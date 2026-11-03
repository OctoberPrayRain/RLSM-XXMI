import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import ".." as App
import "../components" as C

ScrollView {
    id: page
    signal backgroundBrowseRequested()
    clip: true
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ColorDialog {
        id: accentDialog
        title: qsTr("选择主题色")
        onAccepted: appearance.setAccentColor(selectedColor.toString())
    }

    ColumnLayout {
        width: page.availableWidth
        spacing: 20

        Label {
            text: qsTr("外观")
            color: App.Theme.text
            font.pixelSize: 29
            font.weight: Font.DemiBold
        }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: themeColumn.implicitHeight + 44

            ColumnLayout {
                id: themeColumn
                anchors.fill: parent
                anchors.margins: 22
                spacing: 18

                RowLayout {
                    C.Icon { name: "settings"; color: App.Theme.accent }
                    Label {
                        text: qsTr("主题色")
                        color: App.Theme.text
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: appearance.accentColor.toUpperCase()
                        color: App.Theme.muted
                        font.pixelSize: 12
                    }
                }

                RowLayout {
                    spacing: 12

                    Repeater {
                        model: ["#91e4ce", "#72b7ff", "#b79cff", "#f08bb9", "#f0b66e", "#f17777"]

                        delegate: Button {
                            id: swatch
                            required property string modelData
                            implicitWidth: 38
                            implicitHeight: 38
                            hoverEnabled: true
                            onClicked: appearance.setAccentColor(modelData)
                            contentItem: Item { }
                            background: Rectangle {
                                radius: 11
                                color: swatch.modelData
                                border.width: appearance.accentColor.toLowerCase() === swatch.modelData ? 3 : 1
                                border.color: appearance.accentColor.toLowerCase() === swatch.modelData ? App.Theme.text : "#55ffffff"
                            }
                        }
                    }

                    C.ActionButton {
                        text: qsTr("自定义")
                        onClicked: {
                            accentDialog.selectedColor = App.Theme.accent
                            accentDialog.open()
                        }
                    }
                    C.ActionButton {
                        text: qsTr("恢复默认")
                        kind: "quiet"
                        enabled: appearance.accentColor.toLowerCase() !== "#91e4ce"
                        onClicked: appearance.resetAccentColor()
                    }
                    Item { Layout.fillWidth: true }
                }
            }
        }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: previewColumn.implicitHeight + 44

            ColumnLayout {
                id: previewColumn
                anchors.fill: parent
                anchors.margins: 22
                spacing: 18

                RowLayout {
                    C.Icon { name: "image"; color: App.Theme.accent }
                    Label {
                        text: qsTr("窗口背景")
                        color: App.Theme.text
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: appearance.backgroundUrl.length > 0 ? appearance.backgroundName : qsTr("默认渐变")
                        color: App.Theme.muted
                        font.pixelSize: 12
                        elide: Text.ElideMiddle
                        Layout.maximumWidth: 260
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 210
                    radius: 10
                    clip: true
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: App.Theme.gradientStart }
                        GradientStop { position: 0.55; color: App.Theme.gradientMiddle }
                        GradientStop { position: 1; color: App.Theme.gradientEnd }
                    }

                    Image {
                        anchors.fill: parent
                        source: appearance.backgroundUrl
                        fillMode: appearance.backgroundFit === 0 ? Image.PreserveAspectCrop : Image.PreserveAspectFit
                        asynchronous: true
                    }
                    Rectangle {
                        anchors.fill: parent
                        color: "#0c1420"
                        opacity: appearance.backgroundUrl.length > 0 ? appearance.backgroundDim : 0.12
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 18

                        Rectangle {
                            width: 70
                            Layout.fillHeight: true
                            radius: 8
                            color: "#c5101b27"

                            Column {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12
                                Rectangle { width: 22; height: 22; radius: 6; color: App.Theme.accent }
                                Rectangle { width: 46; height: 8; radius: 4; color: App.Theme.accentSoft }
                                Rectangle { width: 36; height: 8; radius: 4; color: "#30404c" }
                                Rectangle { width: 36; height: 8; radius: 4; color: "#30404c" }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Label {
                                text: qsTr("Mod 资料库")
                                color: "#f1f6fa"
                                font.pixelSize: 22
                                font.weight: Font.DemiBold
                            }
                            RowLayout {
                                Layout.fillHeight: true
                                spacing: 12

                                Repeater {
                                    model: 3
                                    delegate: Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        radius: 8
                                        color: "#bb1b2b38"
                                        border.color: index === 0 ? App.Theme.accentBorder : "#404f60"
                                        C.Icon {
                                            anchors.centerIn: parent
                                            name: "image"
                                            color: index === 0 ? App.Theme.accent : "#77959d"
                                            width: 27
                                            height: 27
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    C.ActionButton {
                        text: appearance.backgroundUrl.length > 0 ? qsTr("更换图片") : qsTr("选择图片")
                        symbol: "image"
                        kind: "primary"
                        onClicked: page.backgroundBrowseRequested()
                    }
                    C.ActionButton {
                        text: qsTr("清除背景")
                        enabled: appearance.backgroundUrl.length > 0
                        onClicked: appearance.resetBackground()
                    }
                    Item { Layout.fillWidth: true }
                    Label { text: "PNG / JPEG / WebP"; color: App.Theme.subtle; font.pixelSize: 12 }
                }

                Label {
                    Layout.fillWidth: true
                    text: qsTr("图片会复制到 RLSM 数据目录。")
                    color: App.Theme.muted
                    font.pixelSize: 13
                }
            }
        }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: settingsColumn.implicitHeight + 44

            ColumnLayout {
                id: settingsColumn
                anchors.fill: parent
                anchors.margins: 22
                spacing: 18

                Label {
                    text: qsTr("背景设置")
                    color: App.Theme.text
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("遮罩"); color: App.Theme.text; font.pixelSize: 14 }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: Math.round(appearance.backgroundDim * 100) + "%"
                        color: App.Theme.accent
                        font.pixelSize: 14
                    }
                }

                Slider {
                    id: dimSlider
                    objectName: "backgroundDimSlider"
                    Layout.fillWidth: true
                    from: 0
                    to: 0.9
                    stepSize: 0.01
                    value: appearance.backgroundDim
                    enabled: appearance.backgroundUrl.length > 0
                    opacity: enabled ? 1 : 0.4
                    onMoved: appearance.setBackgroundDim(value)
                    background: Rectangle {
                        x: dimSlider.leftPadding
                        y: (dimSlider.height - height) / 2
                        width: dimSlider.availableWidth
                        height: 5
                        radius: 3
                        color: "#354455"
                        Rectangle {
                            width: dimSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: App.Theme.accent
                        }
                    }
                    handle: Rectangle {
                        x: dimSlider.leftPadding + dimSlider.visualPosition * (dimSlider.availableWidth - width)
                        y: (dimSlider.height - height) / 2
                        width: 18
                        height: 18
                        radius: 9
                        color: dimSlider.pressed ? App.Theme.accentHover : App.Theme.accent
                        border.color: App.Theme.accentInk
                        border.width: 2
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: App.Theme.border }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("显示方式"); color: App.Theme.text; font.pixelSize: 14 }
                    Item { Layout.fillWidth: true }
                    C.SelectField {
                        Layout.preferredWidth: 160
                        model: [qsTr("填满窗口"), qsTr("完整显示")]
                        currentIndex: appearance.backgroundFit
                        enabled: appearance.backgroundUrl.length > 0
                        onActivated: appearance.setBackgroundFit(currentIndex)
                    }
                }
            }
        }

        Item { Layout.preferredHeight: 12 }
    }
}
