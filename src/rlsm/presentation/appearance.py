from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, Property, QSettings, QStandardPaths, QUrl, Signal, Slot
from PySide6.QtGui import QImageReader


class AppearanceSettings(QObject):
    changed = Signal()
    errorOccurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self._directory = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)) / "appearance"
        self._background = str(self._settings.value("appearance/background", "") or "")
        self._dim = min(0.9, max(0.0, float(self._settings.value("appearance/dim", 0.55))))
        self._fit = int(self._settings.value("appearance/fit", 0))

    @Property(str, notify=changed)
    def backgroundUrl(self) -> str:
        path = Path(self._background)
        return QUrl.fromLocalFile(str(path)).toString() if self._background and path.is_file() else ""

    @Property(str, notify=changed)
    def backgroundName(self) -> str:
        return str(self._settings.value("appearance/name", "自定义背景") or "自定义背景")

    @Property(float, notify=changed)
    def backgroundDim(self) -> float:
        return self._dim

    @Property(int, notify=changed)
    def backgroundFit(self) -> int:
        return self._fit

    @Slot(QUrl)
    def setBackground(self, url: QUrl) -> None:
        source = Path(url.toLocalFile())
        if not url.isLocalFile() or not source.is_file() or not QImageReader(str(source)).canRead():
            self.errorOccurred.emit("请选择可以读取的图片，例如 PNG、JPEG 或 WebP。")
            return
        target = self._directory / f"background-{uuid.uuid4().hex}{source.suffix.lower()}"
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        except OSError as error:
            self.errorOccurred.emit(f"保存背景图片失败：{error}")
            return
        previous = self._background
        self._background = str(target)
        self._settings.setValue("appearance/background", self._background)
        self._settings.setValue("appearance/name", source.name)
        self.changed.emit()
        self._remove_managed_background(previous)

    @Slot(float)
    def setBackgroundDim(self, value: float) -> None:
        self._dim = min(0.9, max(0.0, value))
        self._settings.setValue("appearance/dim", self._dim)
        self.changed.emit()

    @Slot(int)
    def setBackgroundFit(self, value: int) -> None:
        if value not in (0, 1):
            return
        self._fit = value
        self._settings.setValue("appearance/fit", value)
        self.changed.emit()

    @Slot()
    def resetBackground(self) -> None:
        previous = self._background
        self._background, self._dim, self._fit = "", 0.55, 0
        for key in ("background", "name", "dim", "fit"):
            self._settings.remove(f"appearance/{key}")
        self.changed.emit()
        self._remove_managed_background(previous)

    def _remove_managed_background(self, value: str) -> None:
        path = Path(value)
        if value and path.parent == self._directory and path.name.startswith("background-"):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
