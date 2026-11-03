import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window

    width: 1180
    height: 760
    minimumWidth: 900
    minimumHeight: 600
    visible: true
    title: qsTr("RLSM · Rainy Linux Skin Manager")
    color: "#111318"

    property color panelColor: "#191c23"
    property color raisedColor: "#222630"
    property color primaryColor: "#7aa2f7"
    property color textColor: "#eceff4"
    property color mutedTextColor: "#9da5b4"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 230
            color: window.panelColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                Label {
                    text: "RLSM"
                    color: window.textColor
                    font.pixelSize: 26
                    font.bold: true
                }

                Label {
                    text: qsTr("Rainy Linux Skin Manager")
                    color: window.mutedTextColor
                    font.pixelSize: 12
                }

                Item { Layout.preferredHeight: 16 }

                Repeater {
                    model: [qsTr("环境设置"), qsTr("Mod 资料库"), qsTr("预设"), qsTr("导入"), qsTr("设置")]

                    delegate: Button {
                        required property string modelData

                        Layout.fillWidth: true
                        text: modelData
                        enabled: index === 0
                        flat: true
                    }
                }

                Item { Layout.fillHeight: true }

                Label {
                    text: qsTr("首批适配器：ZZMI")
                    color: window.mutedTextColor
                    font.pixelSize: 12
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: window.color

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 36
                spacing: 18

                Label {
                    text: qsTr("连接 XXMI")
                    color: window.textColor
                    font.pixelSize: 30
                    font.bold: true
                }

                Label {
                    Layout.maximumWidth: 650
                    text: qsTr("选择 XXMI 或游戏模块目录。RLSM 将检查 Mods 目录和 d3dx.ini，再建立 Mod 资料库。")
                    color: window.mutedTextColor
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 170
                    radius: 12
                    color: window.raisedColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 22
                        spacing: 10

                        Label {
                            text: qsTr("当前状态")
                            color: window.textColor
                            font.pixelSize: 18
                            font.bold: true
                        }

                        Label {
                            text: qsTr("尚未选择游戏模块目录")
                            color: window.mutedTextColor
                        }

                        Item { Layout.fillHeight: true }

                        Button {
                            text: qsTr("选择目录")
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
