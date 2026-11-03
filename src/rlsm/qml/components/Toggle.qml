import QtQuick
import QtQuick.Controls
import ".." as App

Switch {
    id: control
    implicitHeight: 32
    spacing: 12
    leftPadding: 0
    rightPadding: 0
    indicator: Rectangle {
        implicitWidth: 38
        implicitHeight: 22
        x: 0
        y: (control.height - height) / 2
        radius: 11
        color: control.checked ? App.Theme.accent : "#354556"
        border.color: control.activeFocus ? App.Theme.text : "transparent"
        Rectangle {
            width: 16
            height: 16
            x: control.checked ? parent.width - width - 3 : 3
            y: 3
            radius: 8
            color: control.checked ? App.Theme.accentInk : "#b4c0cf"
            Behavior on x { NumberAnimation { duration: 120 } }
        }
    }
    contentItem: Text {
        text: control.text
        leftPadding: control.indicator.width + control.spacing
        font.pixelSize: 14
        verticalAlignment: Text.AlignVCenter
        color: App.Theme.text
    }
}
