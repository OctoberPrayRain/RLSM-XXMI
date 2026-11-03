from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from rlsm.presentation import AppController
from rlsm.presentation.appearance import AppearanceSettings


def _add_fcitx_plugin_path() -> None:
    if not sys.platform.startswith("linux"):
        return
    if os.environ.get("QT_IM_MODULE", "").casefold() not in {"fcitx", "fcitx5"}:
        return

    plugin_relative_path = Path(
        "platforminputcontexts/libfcitx5platforminputcontextplugin.so"
    )
    library_paths = [Path(value) for value in QCoreApplication.libraryPaths()]
    if any((path / plugin_relative_path).is_file() for path in library_paths):
        return

    for path in (
        Path("/usr/lib/qt6/plugins"),
        Path("/usr/lib64/qt6/plugins"),
        Path("/usr/lib/x86_64-linux-gnu/qt6/plugins"),
    ):
        if (path / plugin_relative_path).is_file():
            QCoreApplication.setLibraryPaths(
                [*(str(item) for item in library_paths), str(path)]
            )
            return


def main() -> int:
    QCoreApplication.setOrganizationName("Rainy")
    QCoreApplication.setOrganizationDomain("octoberprayrain.github.io")
    QCoreApplication.setApplicationName("RLSM")

    QQuickStyle.setStyle("Basic")
    _add_fcitx_plugin_path()
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    controller = AppController(engine)
    appearance = AppearanceSettings(engine)
    engine.rootContext().setContextProperty("appController", controller)
    engine.rootContext().setContextProperty("appearance", appearance)

    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

