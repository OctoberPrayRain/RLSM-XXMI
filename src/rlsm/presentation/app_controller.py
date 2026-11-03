from __future__ import annotations

from enum import IntEnum
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Property,
    QSettings,
    QUrl,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QImageReader

from rlsm.application.importer import ModImportError, ModImporter
from rlsm.application.library import LibrarySnapshot, ModLibrary
from rlsm.application.mod_files import ModFileError, ModFileManager
from rlsm.application.toggle import ModToggleEngine, ToggleOperationError
from rlsm.domain.game import ImporterDefinition
from rlsm.domain.mod import ModEntry
from rlsm.domain.runtime import GameBinding, LaunchProfile
from rlsm.infrastructure.hyprland import HyprlandIntegration
from rlsm.infrastructure.lutris import LutrisIntegration, LutrisSnapshot
from rlsm.infrastructure.xxmi import (
    IMPORTER_DEFINITIONS,
    EnvironmentInspection,
    discover_module_path,
    inspect_environment,
)
from rlsm.presentation.library_folders import LibraryFolderError, LibraryFolders


ALL_FOLDERS = "__all__"
UNSORTED_FOLDER = "__unsorted__"


class ModRoles(IntEnum):
    DISPLAY_NAME = Qt.ItemDataRole.UserRole + 1
    DIRECTORY_NAME = Qt.ItemDataRole.UserRole + 2
    GROUP_PATH = Qt.ItemDataRole.UserRole + 3
    MOD_ENABLED = Qt.ItemDataRole.UserRole + 4
    PREVIEW_URL = Qt.ItemDataRole.UserRole + 5
    FULL_PATH = Qt.ItemDataRole.UserRole + 6
    LIBRARY_FOLDER = Qt.ItemDataRole.UserRole + 7


class ModListModel(QAbstractListModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: tuple[ModEntry, ...] = ()
        self._visible_entries: tuple[ModEntry, ...] = ()
        self._query = ""
        self._group = ""
        self._state = 0
        self._library_folder = ALL_FOLDERS
        self._folder_by_path: dict[Path, str] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible_entries)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._visible_entries):
            return None

        entry = self._visible_entries[index.row()]
        values: dict[int, object] = {
            ModRoles.DISPLAY_NAME: entry.display_name,
            ModRoles.DIRECTORY_NAME: entry.directory_name,
            ModRoles.GROUP_PATH: "未分类" if entry.group_path == Path(".") else entry.group_path.as_posix(),
            ModRoles.MOD_ENABLED: entry.is_enabled,
            ModRoles.PREVIEW_URL: (
                QUrl.fromLocalFile(str(entry.preview_path)).toString() if entry.preview_path is not None else ""
            ),
            ModRoles.FULL_PATH: str(entry.path),
            ModRoles.LIBRARY_FOLDER: self._folder_by_path.get(entry.path, ""),
        }
        return values.get(role)

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            ModRoles.DISPLAY_NAME: QByteArray(b"displayName"),
            ModRoles.DIRECTORY_NAME: QByteArray(b"directoryName"),
            ModRoles.GROUP_PATH: QByteArray(b"groupPath"),
            ModRoles.MOD_ENABLED: QByteArray(b"modEnabled"),
            ModRoles.PREVIEW_URL: QByteArray(b"previewUrl"),
            ModRoles.FULL_PATH: QByteArray(b"fullPath"),
            ModRoles.LIBRARY_FOLDER: QByteArray(b"libraryFolder"),
        }

    def replace(
        self,
        entries: tuple[ModEntry, ...],
        folder_by_path: dict[Path, str] | None = None,
    ) -> None:
        self._entries = entries
        self._folder_by_path = folder_by_path or {}
        self._apply_filter()

    def set_filter(self, query: str, group: str, state: int, library_folder: str) -> None:
        self._query = query.casefold().strip()
        self._group = group
        self._state = state
        self._library_folder = library_folder
        self._apply_filter()

    def set_folders(self, folder_by_path: dict[Path, str]) -> None:
        self._folder_by_path = folder_by_path
        self._apply_filter()

    def _apply_filter(self) -> None:
        self.beginResetModel()
        self._visible_entries = tuple(
            entry for entry in self._entries
            if (not self._query or self._query in f"{entry.display_name} {entry.group_path}".casefold())
            and (not self._group or self.group_name(entry) == self._group)
            and (self._state == 0 or entry.is_enabled == (self._state == 1))
            and self._matches_library_folder(entry)
        )
        self.endResetModel()

    def _matches_library_folder(self, entry: ModEntry) -> bool:
        if self._library_folder == ALL_FOLDERS:
            return True
        folder = self._folder_by_path.get(entry.path, "")
        if self._library_folder == UNSORTED_FOLDER:
            return not folder
        return folder == self._library_folder

    def entry(self, row: int) -> ModEntry | None:
        if not 0 <= row < len(self._visible_entries):
            return None
        return self._visible_entries[row]

    @staticmethod
    def group_name(entry: ModEntry) -> str:
        return "未分类" if entry.group_path == Path(".") else entry.group_path.as_posix()

    @property
    def entries(self) -> tuple[ModEntry, ...]:
        return self._entries


class AppController(QObject):
    stateChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self._folders = LibraryFolders(self._settings)
        self._library = ModLibrary()
        self._mod_files = ModFileManager()
        self._toggle_engine = ModToggleEngine()
        self._mod_importer = ModImporter()
        self._hyprland = HyprlandIntegration()
        self._lutris = LutrisIntegration()
        self._mods_model = ModListModel(self)
        self._importers = IMPORTER_DEFINITIONS
        self._inspection: EnvironmentInspection | None = None
        self._snapshot: LibrarySnapshot | None = None
        self._lutris_snapshot = LutrisSnapshot((), ())
        self._selected_profile: LaunchProfile | None = None
        self._last_message = ""
        self._search_query = ""
        self._category_filter = ""
        self._state_filter = 0
        self._folder_filter = ALL_FOLDERS
        self._reload_after_toggle = bool(
            self._settings.value("reloadAfterToggle", True, type=bool)
        )

        saved_importer = str(self._settings.value("currentImporter", "zzmi") or "zzmi")
        self._current_game_index = next(
            (index for index, item in enumerate(self._importers) if item.key == saved_importer),
            0,
        )
        self._module_paths: dict[str, Path] = {}
        for importer in self._importers:
            saved_path = str(self._settings.value(self._module_setting(importer), "") or "")
            module_path = Path(saved_path).expanduser() if saved_path else discover_module_path(importer)
            if module_path is not None:
                self._module_paths[importer.key] = module_path

        self._refresh_lutris_snapshot()
        self._load_current_importer()

    @property
    def _current_importer(self) -> ImporterDefinition:
        return self._importers[self._current_game_index]

    @Property(QObject, constant=True)
    def modsModel(self) -> QObject:
        return self._mods_model

    @Property("QStringList", notify=stateChanged)
    def gameOptions(self) -> list[str]:
        options: list[str] = []
        for importer in self._importers:
            state = "已安装" if importer.key in self._module_paths else "未安装"
            options.append(f"{importer.display_name} · {importer.importer_name} · {state}")
        return options

    @Property(int, notify=stateChanged)
    def currentGameIndex(self) -> int:
        return self._current_game_index

    @Property(str, notify=stateChanged)
    def gameName(self) -> str:
        return self._current_importer.display_name

    @Property(str, notify=stateChanged)
    def importerName(self) -> str:
        return self._current_importer.importer_name

    @Property(str, notify=stateChanged)
    def modulePath(self) -> str:
        if self._inspection is not None:
            return str(self._inspection.module_path or self._inspection.selected_path)
        path = self._module_paths.get(self._current_importer.key)
        return str(path) if path is not None else ""

    @Property(bool, notify=stateChanged)
    def environmentReady(self) -> bool:
        return self._inspection is not None and self._inspection.ready

    @Property(str, notify=stateChanged)
    def environmentTitle(self) -> str:
        importer = self._current_importer
        if self._inspection is None:
            return f"{importer.importer_name} 未选择"
        if self._inspection.ready:
            return f"{importer.importer_name} 已连接"
        return f"{importer.importer_name} 需要配置"

    @Property(str, notify=stateChanged)
    def environmentDetails(self) -> str:
        importer = self._current_importer
        if self._inspection is None:
            return "未选择模块目录"
        if self._inspection.ready:
            details = [
                f"Mods：{self._inspection.mods_path}",
                f"注入：{importer.injection_mode}",
            ]
            arguments = " ".join(importer.d3d11_arguments)
            if arguments:
                details.append(f"DirectX 参数：{arguments}")
            return "\n".join(details)
        return "\n".join(self._inspection.issues)

    @Property("QStringList", notify=stateChanged)
    def lutrisProfileOptions(self) -> list[str]:
        return ["未绑定 Lutris 启动项"] + [
            f"{profile.name} · {profile.runner or '未知运行器'} · ID {profile.profile_id}"
            for profile in self._lutris_snapshot.profiles
        ]

    @Property(int, notify=stateChanged)
    def currentLutrisProfileIndex(self) -> int:
        if self._selected_profile is None:
            return 0
        for index, profile in enumerate(self._lutris_snapshot.profiles, start=1):
            if profile.profile_id == self._selected_profile.profile_id:
                return index
        return 0

    @Property(bool, notify=stateChanged)
    def wineReady(self) -> bool:
        return self._wine_is_ready()

    def _wine_is_ready(self) -> bool:
        profile = self._selected_profile
        prefix = self._effective_wine_prefix()
        return (
            profile is not None
            and profile.runner == "wine"
            and prefix is not None
            and prefix.is_dir()
            and profile.wine.runner_name is not None
        )

    @Property(str, notify=stateChanged)
    def wineTitle(self) -> str:
        if self._selected_profile is None:
            return "未绑定 Lutris 启动项"
        if self._wine_is_ready():
            return "Wine 已连接"
        return "Wine 需要配置"

    @Property(str, notify=stateChanged)
    def wineDetails(self) -> str:
        profile = self._selected_profile
        if profile is None:
            issues = "\n".join(self._lutris_snapshot.issues)
            return issues or "未选择 Lutris 启动项"

        prefix = self._effective_wine_prefix()
        runner_name = profile.wine.runner_name or "未指定"
        architecture = profile.wine.architecture or "未指定"
        details = [f"运行器：{runner_name} · 架构：{architecture}"]
        if profile.runner != "wine":
            details.append(f"Lutris 运行器类型：{profile.runner or '未知'}")
        elif prefix is None:
            details.append("未选择 Wine 前缀")
        elif not prefix.is_dir():
            details.append("Wine 前缀无法访问")
        if profile.wine.runner_name is None:
            details.append("Lutris 未提供 Wine 运行器版本")
        return "\n".join(details)

    @Property(str, notify=stateChanged)
    def winePrefix(self) -> str:
        prefix = self._effective_wine_prefix()
        return str(prefix) if prefix is not None else ""

    @Property(bool, notify=stateChanged)
    def hasWinePrefixOverride(self) -> bool:
        return self._wine_prefix_override() is not None

    @Property(bool, notify=stateChanged)
    def canLaunch(self) -> bool:
        return self._selected_profile is not None

    @Property(bool, notify=stateChanged)
    def hyprlandAvailable(self) -> bool:
        return self._hyprland.available

    @Property(bool, notify=stateChanged)
    def reloadAfterToggle(self) -> bool:
        return self._reload_after_toggle

    @Property(int, notify=stateChanged)
    def modCount(self) -> int:
        return len(self._snapshot.entries) if self._snapshot is not None else 0

    @Property(int, notify=stateChanged)
    def enabledCount(self) -> int:
        return self._snapshot.enabled_count if self._snapshot is not None else 0

    @Property(str, notify=stateChanged)
    def lastMessage(self) -> str:
        return self._last_message

    @Property("QStringList", notify=stateChanged)
    def categoryOptions(self) -> list[str]:
        return ["全部分类"] + sorted(
            {self._mods_model.group_name(entry) for entry in self._mods_model.entries},
            key=str.casefold,
        )

    @Property("QVariantList", notify=stateChanged)
    def libraryFolderItems(self) -> list[dict[str, object]]:
        entries = self._mods_model.entries
        counts = {name: 0 for name in self._folders.names}
        unsorted_count = 0
        for entry in entries:
            folder = self._folders.folder_for(entry)
            if folder:
                counts[folder] = counts.get(folder, 0) + 1
            else:
                unsorted_count += 1
        return [
            {"key": ALL_FOLDERS, "name": "全部 Mod", "count": len(entries), "icon": "grid"},
            {"key": UNSORTED_FOLDER, "name": "未整理", "count": unsorted_count, "icon": "folder"},
            *(
                {"key": name, "name": name, "count": counts.get(name, 0), "icon": "folder"}
                for name in self._folders.names
            ),
        ]

    @Property("QStringList", notify=stateChanged)
    def moveFolderOptions(self) -> list[str]:
        return ["未整理", *self._folders.names]

    @Property(str, notify=stateChanged)
    def currentLibraryFolderKey(self) -> str:
        return self._folder_filter

    @Property(str, notify=stateChanged)
    def currentLibraryFolderName(self) -> str:
        if self._folder_filter == ALL_FOLDERS:
            return "全部 Mod"
        if self._folder_filter == UNSORTED_FOLDER:
            return "未整理"
        return self._folder_filter

    @Property(bool, notify=stateChanged)
    def canManageCurrentLibraryFolder(self) -> bool:
        return self._folder_filter not in {ALL_FOLDERS, UNSORTED_FOLDER}

    @Property(str, notify=stateChanged)
    def searchQuery(self) -> str:
        return self._search_query

    @Property(str, notify=stateChanged)
    def categoryFilter(self) -> str:
        return self._category_filter or "全部分类"

    @Property(int, notify=stateChanged)
    def stateFilter(self) -> int:
        return self._state_filter

    @Property(int, notify=stateChanged)
    def visibleModCount(self) -> int:
        return self._mods_model.rowCount()

    @Property(str, notify=stateChanged)
    def modsPath(self) -> str:
        return str(self._inspection.mods_path) if self._inspection and self._inspection.mods_path else ""

    @Slot(str)
    def setSearchQuery(self, value: str) -> None:
        self._search_query = value
        self._apply_library_filter()

    @Slot(str)
    def setCategoryFilter(self, value: str) -> None:
        self._category_filter = "" if value == "全部分类" else value
        self._apply_library_filter()

    @Slot(int)
    def setStateFilter(self, value: int) -> None:
        if 0 <= value <= 2:
            self._state_filter = value
            self._apply_library_filter()

    @Slot()
    def clearFilters(self) -> None:
        self._search_query, self._category_filter, self._state_filter = "", "", 0
        self._apply_library_filter()

    @Slot(str)
    def setLibraryFolder(self, value: str) -> None:
        valid_keys = {ALL_FOLDERS, UNSORTED_FOLDER, *self._folders.names}
        if value not in valid_keys:
            return
        self._folder_filter = value
        self._apply_library_filter()

    @Slot(str)
    def createLibraryFolder(self, value: str) -> None:
        try:
            name = self._folders.create(value)
        except LibraryFolderError as error:
            self._set_message(str(error))
            return
        self._set_message(f"已创建文件夹：{name}")

    @Slot(str, str)
    def renameLibraryFolder(self, current_name: str, value: str) -> None:
        try:
            name = self._folders.rename(current_name, value)
        except LibraryFolderError as error:
            self._set_message(str(error))
            return
        if self._folder_filter == current_name:
            self._folder_filter = name
        self._sync_library_folders()
        self._set_message(f"已重命名文件夹：{name}")

    @Slot(str)
    def deleteLibraryFolder(self, value: str) -> None:
        try:
            self._folders.delete(value)
        except LibraryFolderError as error:
            self._set_message(str(error))
            return
        if self._folder_filter == value:
            self._folder_filter = UNSORTED_FOLDER
        self._sync_library_folders()
        self._set_message(f"已删除文件夹：{value}")

    @Slot(int, str)
    def moveModToLibraryFolder(self, row: int, value: str) -> None:
        target = self._mods_model.entry(row)
        if target is None:
            self._set_message("找不到需要整理的 Mod")
            return
        folder_name = "" if value == "未整理" else value
        try:
            folder = self._folders.assign(target, folder_name)
        except LibraryFolderError as error:
            self._set_message(str(error))
            return
        self._sync_library_folders()
        destination = folder or "未整理"
        self._set_message(f"已将 {target.display_name} 移到 {destination}")

    def _apply_library_filter(self) -> None:
        self._mods_model.set_filter(
            self._search_query,
            self._category_filter,
            self._state_filter,
            self._folder_filter,
        )
        self.stateChanged.emit()

    @Slot(int)
    def selectGame(self, index: int) -> None:
        if not 0 <= index < len(self._importers) or index == self._current_game_index:
            return
        self._current_game_index = index
        self._folder_filter = ALL_FOLDERS
        self.clearFilters()
        self._settings.setValue("currentImporter", self._current_importer.key)
        self._load_current_importer()
        self._last_message = f"已切换到 {self._current_importer.display_name}"
        self.stateChanged.emit()

    @Slot(str)
    def setModulePath(self, value: str) -> None:
        path_value = value.strip()
        if not path_value:
            self._set_message("目录不能为空")
            return
        if path_value.startswith("file:"):
            path_value = QUrl(path_value).toLocalFile()
        self._inspect(Path(path_value))

    @Slot(QUrl)
    def setModuleUrl(self, value: QUrl) -> None:
        self.setModulePath(value.toLocalFile())

    @Slot(int)
    def selectLutrisProfile(self, index: int) -> None:
        if index == 0:
            self._selected_profile = None
            self._settings.setValue(self._profile_setting(self._current_importer), "__none__")
            self._set_message("已取消 Lutris 启动项绑定")
            return
        profile_index = index - 1
        if not 0 <= profile_index < len(self._lutris_snapshot.profiles):
            return
        self._selected_profile = self._lutris_snapshot.profiles[profile_index]
        self._settings.setValue(
            self._profile_setting(self._current_importer),
            self._selected_profile.profile_id,
        )
        self._set_message(f"已绑定 Lutris 启动项：{self._selected_profile.name}")

    @Slot(QUrl)
    def setWinePrefixUrl(self, value: QUrl) -> None:
        path = Path(value.toLocalFile()).expanduser().resolve(strict=False)
        if not path.is_dir() or not (path / "drive_c").is_dir():
            self._set_message("所选目录不是可识别的 Wine 前缀")
            return
        self._settings.setValue(self._prefix_setting(self._current_importer), str(path))
        self._set_message(f"已为 {self._current_importer.display_name} 指定 Wine 前缀")

    @Slot()
    def clearWinePrefixOverride(self) -> None:
        self._settings.remove(self._prefix_setting(self._current_importer))
        self._set_message("已恢复 Lutris 的 Wine 前缀")

    @Slot()
    def refreshLutris(self) -> None:
        previous_profile_id = self._selected_profile.profile_id if self._selected_profile else None
        saved_profile_id = str(
            self._settings.value(self._profile_setting(self._current_importer), "") or ""
        )
        self._refresh_lutris_snapshot()
        self._select_profile(
            previous_profile_id or (saved_profile_id if saved_profile_id != "__none__" else None),
            allow_auto=saved_profile_id != "__none__",
        )
        self._set_message("已刷新 Lutris 启动项")

    @Slot()
    def launchSelectedProfile(self) -> None:
        if self._selected_profile is None:
            self._set_message("请先绑定 Lutris 启动项")
            return
        try:
            self._lutris.launch(self._selected_profile)
        except OSError as error:
            self._set_message(f"无法启动 Lutris：{error}")
            return
        self._set_message(f"已向 Lutris 发送启动请求：{self._selected_profile.name}")

    @Slot(bool)
    def setReloadAfterToggle(self, enabled: bool) -> None:
        self._reload_after_toggle = enabled
        self._settings.setValue("reloadAfterToggle", enabled)
        state = "开启" if enabled else "关闭"
        self._set_message(f"自动 F10 已{state}")

    @Slot()
    def reloadGame(self) -> None:
        result = self._hyprland.reload_game(self._current_importer.game)
        self._set_message(result.message)

    @Slot(QUrl)
    def importModUrl(self, value: QUrl) -> None:
        self._import_mod_path(Path(value.toLocalFile()))

    @Slot(QUrl)
    def importModFolderUrl(self, value: QUrl) -> None:
        self._import_mod_path(Path(value.toLocalFile()))

    @Slot()
    def autoCategorize(self) -> None:
        if self._inspection is None or self._inspection.mods_path is None:
            self._set_message("请先连接游戏模块")
            return
        if self._snapshot is None:
            self._scan_library()
        entries = self._snapshot.entries if self._snapshot is not None else ()
        result = self._mod_importer.organize_existing(
            self._inspection.mods_path,
            tuple(entry.path for entry in entries),
        )
        self._scan_library()
        message = f"已整理：移动 {result.moved} 个，保留 {result.unchanged} 个"
        if result.warnings:
            message += "\n" + "\n".join(result.warnings)
        self._set_message(message)

    @Slot()
    def refreshLibrary(self) -> None:
        if self._inspection is None:
            self._set_message("请先连接游戏模块")
            return
        self._inspect(self._inspection.module_path or self._inspection.selected_path)

    @Slot(int, bool)
    def toggleMod(self, row: int, exclusive: bool) -> None:
        target = self._mods_model.entry(row)
        if target is None:
            self._set_message("找不到需要切换的 Mod")
            return

        try:
            if exclusive and not target.is_enabled:
                siblings = (entry for entry in self._mods_model.entries if entry.group_path == target.group_path)
                result = self._toggle_engine.enable_exclusively(target, siblings)
            else:
                result = self._toggle_engine.set_enabled(target, not target.is_enabled)
        except ToggleOperationError as error:
            message = str(error)
            if error.rollback_errors:
                message += "\n" + "\n".join(error.rollback_errors)
            self._set_message(message)
            return

        self._scan_library()
        action = "启用" if not target.is_enabled else "停用"
        message = f"已{action} {target.display_name}"
        if result.changed and self._reload_after_toggle:
            reload_result = self._hyprland.reload_game(self._current_importer.game)
            message += f"\n{reload_result.message}"
        self._set_message(message)

    @Slot(int, QUrl)
    def setModPreview(self, row: int, value: QUrl) -> None:
        target = self._mods_model.entry(row)
        if target is None:
            self._set_message("找不到需要设置预览图的 Mod")
            return
        source = Path(value.toLocalFile())
        if not value.isLocalFile() or not source.is_file() or not QImageReader(str(source)).canRead():
            self._set_message("请选择可以读取的图片")
            return
        try:
            self._mod_files.set_preview(target, source)
        except ModFileError as error:
            self._set_message(str(error))
            return
        self._scan_library()
        self._set_message(f"已更新 {target.display_name} 的预览图")

    @Slot(int)
    def deleteMod(self, row: int) -> None:
        target = self._mods_model.entry(row)
        if target is None:
            self._set_message("找不到需要删除的 Mod")
            return
        if self._inspection is None or self._inspection.mods_path is None:
            self._set_message("未连接 Mods 目录")
            return
        folder_key = self._folders.key_for(target)
        try:
            self._mod_files.move_to_trash(target, self._inspection.mods_path)
        except ModFileError as error:
            self._set_message(str(error))
            return
        self._folders.remove_key(folder_key)
        self._scan_library()
        message = f"已将 {target.display_name} 移入回收站"
        if target.is_enabled and self._reload_after_toggle:
            reload_result = self._hyprland.reload_game(self._current_importer.game)
            message += f"\n{reload_result.message}"
        self._set_message(message)

    def _import_mod_path(self, source: Path) -> None:
        if self._inspection is None or self._inspection.mods_path is None:
            self._set_message("请先连接游戏模块")
            return
        try:
            result = self._mod_importer.import_source(source, self._inspection.mods_path)
        except ModImportError as error:
            self._set_message(str(error))
            return
        self._scan_library()
        message = f"已导入 {len(result.imported)} 个 Mod，保持停用"
        if result.warnings:
            message += "\n" + "\n".join(result.warnings)
        self._set_message(message)

    def _load_current_importer(self) -> None:
        self._folders.load(self._current_importer.key)
        self._folder_filter = ALL_FOLDERS
        self._inspection = None
        self._snapshot = None
        self._mods_model.replace((), {})
        module_path = self._module_paths.get(self._current_importer.key)
        if module_path is not None:
            self._inspect(module_path)
        saved_profile_id = str(
            self._settings.value(self._profile_setting(self._current_importer), "") or ""
        )
        self._select_profile(
            saved_profile_id if saved_profile_id != "__none__" else None,
            allow_auto=saved_profile_id != "__none__",
        )

    def _inspect(self, path: Path) -> None:
        importer = self._current_importer
        try:
            self._inspection = inspect_environment(path, importer)
        except OSError as error:
            self._inspection = None
            self._snapshot = None
            self._mods_model.replace((), {})
            self._set_message(f"读取 XXMI 环境失败：{error}")
            return

        if self._inspection.module_path is not None:
            module_path = self._inspection.module_path
            self._module_paths[importer.key] = module_path
            self._settings.setValue(self._module_setting(importer), str(module_path))

        if self._inspection.ready:
            self._scan_library()
            self._last_message = f"已连接 {importer.importer_name}"
        else:
            self._snapshot = None
            self._mods_model.replace((), {})
            self._last_message = "环境检查未通过"
        self.stateChanged.emit()

    def _scan_library(self) -> None:
        if self._inspection is None or self._inspection.mods_path is None:
            return
        self._snapshot = self._library.scan(self._inspection.mods_path)
        groups = {self._mods_model.group_name(entry) for entry in self._snapshot.entries}
        if self._category_filter not in groups:
            self._category_filter = ""
        if self._folder_filter not in {ALL_FOLDERS, UNSORTED_FOLDER, *self._folders.names}:
            self._folder_filter = ALL_FOLDERS
        folder_map = self._folders.folder_map(self._snapshot.entries)
        self._mods_model.set_filter(
            self._search_query,
            self._category_filter,
            self._state_filter,
            self._folder_filter,
        )
        self._mods_model.replace(self._snapshot.entries, folder_map)
        self.stateChanged.emit()

    def _sync_library_folders(self) -> None:
        entries = self._mods_model.entries
        self._mods_model.set_folders(self._folders.folder_map(entries))
        self._mods_model.set_filter(
            self._search_query,
            self._category_filter,
            self._state_filter,
            self._folder_filter,
        )
        self.stateChanged.emit()

    def _refresh_lutris_snapshot(self) -> None:
        self._lutris_snapshot = self._lutris.discover_profiles()

    def _select_profile(self, profile_id: str | None, allow_auto: bool = True) -> None:
        profiles = self._lutris_snapshot.profiles
        self._selected_profile = next(
            (profile for profile in profiles if profile.profile_id == profile_id),
            None,
        )
        if self._selected_profile is not None:
            return
        if allow_auto:
            candidates = self._lutris.profiles_for_importer(self._current_importer, profiles)
            self._selected_profile = candidates[0] if candidates else None

    def _current_binding(self) -> GameBinding:
        return GameBinding(
            importer_key=self._current_importer.key,
            module_path=self._module_paths.get(self._current_importer.key),
            launch_profile_id=(
                self._selected_profile.profile_id if self._selected_profile is not None else None
            ),
            wine_prefix_override=self._wine_prefix_override(),
        )

    def _effective_wine_prefix(self) -> Path | None:
        binding = self._current_binding()
        if binding.wine_prefix_override is not None:
            return binding.wine_prefix_override
        if self._selected_profile is None:
            return None
        return self._selected_profile.wine.prefix_path

    def _wine_prefix_override(self) -> Path | None:
        value = str(self._settings.value(self._prefix_setting(self._current_importer), "") or "")
        return Path(value).expanduser().resolve(strict=False) if value else None

    @staticmethod
    def _module_setting(importer: ImporterDefinition) -> str:
        return f"games/{importer.key}/modulePath"

    @staticmethod
    def _profile_setting(importer: ImporterDefinition) -> str:
        return f"games/{importer.key}/lutrisProfileId"

    @staticmethod
    def _prefix_setting(importer: ImporterDefinition) -> str:
        return f"games/{importer.key}/winePrefixOverride"

    def _set_message(self, message: str) -> None:
        self._last_message = message
        self.stateChanged.emit()
