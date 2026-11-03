import QtQuick
import QtQuick.Controls
import ".." as App

ComboBox {
    id: control
    implicitHeight: 44
    leftPadding: 14
    rightPadding: 38
    font.pixelSize: 14
    hoverEnabled: true
    contentItem: Text {
        text: control.displayText
        color: App.Theme.text
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Icon {
        x: control.width - width - 12
        y: (control.height - height) / 2
        name: "down"
        color: App.Theme.muted
        width: 16
        height: 16
    }
    background: Rectangle {
        radius: 9
        color: control.hovered ? "#263644" : App.Theme.field
        border.color: control.activeFocus ? App.Theme.accent : App.Theme.border
    }
    delegate: ItemDelegate {
        id: option
        required property var modelData
        required property int index
        width: control.width
        height: 44
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: option.modelData
            color: option.index === control.currentIndex ? App.Theme.accent : App.Theme.text
            font.pixelSize: 14
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle { radius: 6; color: option.highlighted ? App.Theme.hover : "transparent" }
    }
    popup: Popup {
        y: control.height + 6
        width: control.width
        padding: 6
        implicitHeight: Math.min(contentItem.implicitHeight + 12, 340)
        background: Rectangle { color: "#172330"; radius: 10; border.color: App.Theme.border }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator { }
        }
    }
}
