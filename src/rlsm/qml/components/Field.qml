import QtQuick
import QtQuick.Controls
import ".." as App

TextField {
    id: control
    implicitHeight: 44
    leftPadding: 14
    rightPadding: 14
    color: App.Theme.text
    placeholderTextColor: App.Theme.subtle
    selectionColor: App.Theme.selected
    selectedTextColor: App.Theme.text
    font.pixelSize: 14
    selectByMouse: true
    background: Rectangle {
        radius: 9
        color: App.Theme.field
        border.color: control.activeFocus ? App.Theme.accent : App.Theme.border
        border.width: 1
    }
}
