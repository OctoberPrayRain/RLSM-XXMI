import QtQuick
import Qt5Compat.GraphicalEffects
import ".." as App

Item {
    id: panel
    clip: true

    property color glassColor: App.Theme.surface
    property color borderColor: App.Theme.border
    property real borderWidth: 1
    property real radius: 14
    property bool blurEnabled: true
    readonly property point backdropPosition: App.Theme.backdropSource
        ? panel.mapToItem(App.Theme.backdropSource, 0, 0)
        : Qt.point(0, 0)

    ShaderEffectSource {
        id: backdropSample
        anchors.fill: parent
        sourceItem: App.Theme.backdropSource
        sourceRect: Qt.rect(
            panel.backdropPosition.x,
            panel.backdropPosition.y,
            panel.width,
            panel.height
        )
        live: true
        hideSource: false
        visible: App.Theme.backdropSource !== null && panel.blurEnabled
    }

    FastBlur {
        anchors.fill: parent
        source: backdropSample
        visible: App.Theme.backdropSource !== null && panel.blurEnabled
        radius: 32
        transparentBorder: false
    }

    Rectangle {
        anchors.fill: parent
        radius: panel.radius
        color: panel.glassColor
        border.color: panel.borderColor
        border.width: panel.borderWidth
    }

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: panel.radius
        anchors.rightMargin: panel.radius
        height: 1
        color: App.Theme.glassHighlight
    }
}
