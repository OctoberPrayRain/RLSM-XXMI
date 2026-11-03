from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from rlsm.presentation import AppController
from rlsm.presentation.appearance import AppearanceSettings


def main() -> int:
    QCoreApplication.setOrganizationName("Rainy")
    QCoreApplication.setOrganizationDomain("octoberprayrain.github.io")
    QCoreApplication.setApplicationName("RLSM")

    QQuickStyle.setStyle("Basic")
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

