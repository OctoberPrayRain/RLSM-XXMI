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
from rlsm.domain.mod import ModEntry
from rlsm.infrastructure.xxmi import (
    ZZMI,
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
        self._mods_model = ModListModel(self)
        self._inspection: EnvironmentInspection | None = None
        self._snapshot: LibrarySnapshot | None = None
        self._last_message = ""

        saved_path = str(self._settings.value("games/zzmi/modulePath", "") or "")
        initial_path = Path(saved_path).expanduser() if saved_path else discover_module_path(ZZMI)
        if initial_path is not None:
            self._inspect(initial_path)

    @Property(QObject, constant=True)
    def modsModel(self) -> QObject:
        return self._mods_model

    @Property(str, notify=stateChanged)
    def gameName(self) -> str:
        return ZZMI.display_name

    @Property(str, notify=stateChanged)
    def importerName(self) -> str:
        return ZZMI.importer_name

    @Property(str, notify=stateChanged)
    def modulePath(self) -> str:
        if self._inspection is None:
            return ""
        return str(self._inspection.module_path or self._inspection.selected_path)

    @Property(bool, notify=stateChanged)
    def environmentReady(self) -> bool:
        return self._inspection is not None and self._inspection.ready

    @Property(str, notify=stateChanged)
    def environmentTitle(self) -> str:
        if self._inspection is None:
            return "尚未连接游戏模块"
        if self._inspection.ready:
            return f"{ZZMI.importer_name} 可以使用"
        return f"{ZZMI.importer_name} 环境需要处理"

    @Property(str, notify=stateChanged)
    def environmentDetails(self) -> str:
        if self._inspection is None:
            return "请选择 XXMI 根目录或者 ZZMI 目录。"
        if self._inspection.ready:
            return f"Mods 目录：{self._inspection.mods_path}"
        return "\n".join(self._inspection.issues)

    @Property(int, notify=stateChanged)
    def modCount(self) -> int:
        return len(self._snapshot.entries) if self._snapshot is not None else 0

    @Property(int, notify=stateChanged)
    def enabledCount(self) -> int:
        return self._snapshot.enabled_count if self._snapshot is not None else 0

    @Property(str, notify=stateChanged)
    def lastMessage(self) -> str:
        return self._last_message

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

    def _inspect(self, path: Path) -> None:
        try:
            self._inspection = inspect_environment(path, ZZMI)
        except OSError as error:
            self._inspection = None
            self._snapshot = None
            self._mods_model.replace(())
            self._set_message(f"读取 XXMI 环境失败：{error}")
            return

        if self._inspection.module_path is not None:
            self._settings.setValue("games/zzmi/modulePath", str(self._inspection.module_path))

        if self._inspection.ready:
            self._scan_library()
            self._last_message = f"已连接 {ZZMI.importer_name}"
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

    def _set_message(self, message: str) -> None:
        self._last_message = message
        self.stateChanged.emit()

