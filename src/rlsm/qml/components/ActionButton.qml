import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as App

Button {
    id: control
    property string kind: "secondary"
    property string symbol: ""
    implicitHeight: 42
    implicitWidth: contentItem.implicitWidth + 28
    leftPadding: 14
    rightPadding: 14
    hoverEnabled: true
    opacity: enabled ? 1 : 0.4
    font.pixelSize: 14
    activeFocusOnTab: true
    contentItem: RowLayout {
        spacing: 8
        Icon {
            visible: control.symbol.length > 0
            name: control.symbol
            implicitWidth: 17
            implicitHeight: 17
            color: control.kind === "primary" ? App.Theme.accentInk : App.Theme.text
        }
        Text {
            text: control.text
            font: control.font
            color: control.kind === "primary" ? App.Theme.accentInk : App.Theme.text
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }
    }
    background: Rectangle {
        radius: 9
        color: control.kind === "primary" ? (control.down ? App.Theme.accentPressed : control.hovered ? App.Theme.accentHover : App.Theme.accent)
             : control.down ? App.Theme.selected : control.hovered ? App.Theme.hover
             : control.kind === "quiet" ? "transparent" : "#c923303e"
        border.width: control.activeFocus || control.kind === "secondary" ? 1 : 0
        border.color: control.activeFocus ? App.Theme.accent : App.Theme.border
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
