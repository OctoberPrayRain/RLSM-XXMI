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

from rlsm.application.library import LibrarySnapshot, ModLibrary
from rlsm.application.toggle import ModToggleEngine, ToggleOperationError
from rlsm.domain.game import ImporterDefinition
from rlsm.domain.mod import ModEntry
from rlsm.domain.runtime import GameBinding, LaunchProfile
from rlsm.infrastructure.lutris import LutrisIntegration, LutrisSnapshot
from rlsm.infrastructure.xxmi import (
    IMPORTER_DEFINITIONS,
    EnvironmentInspection,
    discover_module_path,
    inspect_environment,
)


class ModRoles(IntEnum):
    DISPLAY_NAME = Qt.ItemDataRole.UserRole + 1
    DIRECTORY_NAME = Qt.ItemDataRole.UserRole + 2
    GROUP_PATH = Qt.ItemDataRole.UserRole + 3
    MOD_ENABLED = Qt.ItemDataRole.UserRole + 4
    PREVIEW_URL = Qt.ItemDataRole.UserRole + 5
    FULL_PATH = Qt.ItemDataRole.UserRole + 6


class ModListModel(QAbstractListModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: tuple[ModEntry, ...] = ()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None

        entry = self._entries[index.row()]
        values: dict[int, object] = {
            ModRoles.DISPLAY_NAME: entry.display_name,
            ModRoles.DIRECTORY_NAME: entry.directory_name,
            ModRoles.GROUP_PATH: "未分类" if entry.group_path == Path(".") else entry.group_path.as_posix(),
            ModRoles.MOD_ENABLED: entry.is_enabled,
            ModRoles.PREVIEW_URL: (
                QUrl.fromLocalFile(str(entry.preview_path)).toString() if entry.preview_path is not None else ""
            ),
            ModRoles.FULL_PATH: str(entry.path),
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
        }

    def replace(self, entries: tuple[ModEntry, ...]) -> None:
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def entry(self, row: int) -> ModEntry | None:
        if not 0 <= row < len(self._entries):
            return None
        return self._entries[row]

    @property
    def entries(self) -> tuple[ModEntry, ...]:
        return self._entries


class AppController(QObject):
    stateChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self._library = ModLibrary()
        self._toggle_engine = ModToggleEngine()
        self._lutris = LutrisIntegration()
        self._mods_model = ModListModel(self)
        self._importers = IMPORTER_DEFINITIONS
        self._inspection: EnvironmentInspection | None = None
        self._snapshot: LibrarySnapshot | None = None
        self._lutris_snapshot = LutrisSnapshot((), ())
        self._selected_profile: LaunchProfile | None = None
        self._last_message = ""

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
            return f"{importer.importer_name} 尚未安装或尚未选择"
        if self._inspection.ready:
            return f"{importer.importer_name} 可以使用"
        return f"{importer.importer_name} 环境需要处理"

    @Property(str, notify=stateChanged)
    def environmentDetails(self) -> str:
        importer = self._current_importer
        if self._inspection is None:
            return f"请选择 XXMI 根目录或者 {importer.importer_name} 目录。"
        if self._inspection.ready:
            arguments = " ".join(importer.d3d11_arguments) or "无"
            return (
                f"Mods 目录：{self._inspection.mods_path}\n"
                f"注入方式：{importer.injection_mode} · DirectX 参数：{arguments}"
            )
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
            return "尚未绑定 Lutris 启动项"
        if self._wine_is_ready():
            return "Wine 环境可以使用"
        return "Wine 环境需要补充配置"

    @Property(str, notify=stateChanged)
    def wineDetails(self) -> str:
        profile = self._selected_profile
        if profile is None:
            issues = "\n".join(self._lutris_snapshot.issues)
            return issues or "请选择这个游戏对应的 Lutris 启动项。"

        prefix = self._effective_wine_prefix()
        runner_name = profile.wine.runner_name or "未指定"
        prefix_text = str(prefix) if prefix is not None else "未指定"
        architecture = profile.wine.architecture or "未指定"
        details = [
            f"启动项：{profile.name}（ID {profile.profile_id}）",
            f"运行器：{runner_name} · 架构：{architecture}",
            f"Wine 前缀：{prefix_text}",
        ]
        if profile.runner != "wine":
            details.append(f"该启动项的 Lutris 运行器类型为 {profile.runner or '未知'}")
        elif prefix is None:
            details.append("需要选择该游戏使用的 Wine 前缀")
        elif not prefix.is_dir():
            details.append("Wine 前缀当前不可访问")
        if profile.wine.runner_name is None:
            details.append("Lutris 没有提供 Wine 运行器版本")
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

    @Property(int, notify=stateChanged)
    def modCount(self) -> int:
        return len(self._snapshot.entries) if self._snapshot is not None else 0

    @Property(int, notify=stateChanged)
    def enabledCount(self) -> int:
        return self._snapshot.enabled_count if self._snapshot is not None else 0

    @Property(str, notify=stateChanged)
    def lastMessage(self) -> str:
        return self._last_message

    @Slot(int)
    def selectGame(self, index: int) -> None:
        if not 0 <= index < len(self._importers) or index == self._current_game_index:
            return
        self._current_game_index = index
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
        self._set_message("已恢复使用 Lutris 启动项中的 Wine 前缀")

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
        self._set_message("已重新读取 Lutris 启动项")

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
        self._set_message(f"已请求 Lutris 启动 {self._selected_profile.name}")

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
        self._set_message(f"已{action} {target.display_name}，完成 {len(result.completed_steps)} 项目录修改")

    def _load_current_importer(self) -> None:
        self._inspection = None
        self._snapshot = None
        self._mods_model.replace(())
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
            self._mods_model.replace(())
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
            self._mods_model.replace(())
            self._last_message = "环境检查未通过"
        self.stateChanged.emit()

    def _scan_library(self) -> None:
        if self._inspection is None or self._inspection.mods_path is None:
            return
        self._snapshot = self._library.scan(self._inspection.mods_path)
        self._mods_model.replace(self._snapshot.entries)
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
