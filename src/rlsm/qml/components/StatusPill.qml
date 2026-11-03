import QtQuick
import QtQuick.Layouts
import ".." as App

Rectangle {
    id: pill
    property string text: ""
    property bool ready: true
    implicitWidth: row.implicitWidth + 20
    implicitHeight: 28
    radius: 14
    color: ready ? "#253e3b" : "#403a30"
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 7
        Rectangle { width: 5; height: 5; radius: 3; color: pill.ready ? App.Theme.accent : App.Theme.warning }
        Text { text: pill.text; color: pill.ready ? App.Theme.accent : App.Theme.warning; font.pixelSize: 12 }
    }
}
