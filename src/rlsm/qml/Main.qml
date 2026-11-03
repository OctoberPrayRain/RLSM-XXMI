import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
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

    property int currentPage: 0
    property color panelColor: "#191c23"
    property color raisedColor: "#222630"
    property color raisedHoverColor: "#2a2f3b"
    property color primaryColor: "#7aa2f7"
    property color successColor: "#9ece6a"
    property color warningColor: "#e0af68"
    property color textColor: "#eceff4"
    property color mutedTextColor: "#9da5b4"

    FolderDialog {
        id: folderDialog
        title: qsTr("选择 XXMI 根目录或 ZZMI 目录")
        onAccepted: appController.setModuleUrl(selectedFolder)
    }

    component NavigationButton: Button {
        required property int pageIndex
        Layout.fillWidth: true
        text: ""
        checkable: true
        checked: window.currentPage === pageIndex
        enabled: pageIndex === 0 || appController.environmentReady
        onClicked: window.currentPage = pageIndex
    }

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
                spacing: 10

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

                NavigationButton {
                    pageIndex: 0
                    text: qsTr("环境设置")
                }

                NavigationButton {
                    pageIndex: 1
                    text: qsTr("Mod 资料库")
                }

                Item { Layout.fillHeight: true }

                Label {
                    text: appController.gameName + " · " + appController.importerName
                    color: window.mutedTextColor
                    font.pixelSize: 12
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: window.currentPage

            Rectangle {
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
                        Layout.maximumWidth: 720
                        text: qsTr("选择 XXMI 根目录或者游戏模块目录。RLSM 将检查 Mods 目录和 d3dx.ini。")
                        color: window.mutedTextColor
                        font.pixelSize: 15
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: modulePathField
                            Layout.fillWidth: true
                            text: appController.modulePath
                            placeholderText: qsTr("XXMI 或 ZZMI 目录")
                            selectByMouse: true
                            onAccepted: appController.setModulePath(text)
                        }

                        Button {
                            text: qsTr("浏览")
                            onClicked: folderDialog.open()
                        }

                        Button {
                            text: qsTr("检查并连接")
                            onClicked: appController.setModulePath(modulePathField.text)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 190
                        radius: 12
                        color: window.raisedColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 22
                            spacing: 18

                            Rectangle {
                                Layout.preferredWidth: 12
                                Layout.fillHeight: true
                                radius: 6
                                color: appController.environmentReady ? window.successColor : window.warningColor
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 10

                                Label {
                                    text: appController.environmentTitle
                                    color: window.textColor
                                    font.pixelSize: 19
                                    font.bold: true
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: appController.environmentDetails
                                    color: window.mutedTextColor
                                    wrapMode: Text.Wrap
                                }

                                Item { Layout.fillHeight: true }

                                Label {
                                    visible: appController.environmentReady
                                    text: qsTr("已经发现 %1 个 Mod，其中 %2 个已启用").arg(appController.modCount).arg(appController.enabledCount)
                                    color: window.successColor
                                }
                            }
                        }
                    }

                    Label {
                        visible: appController.lastMessage.length > 0
                        text: appController.lastMessage
                        color: window.mutedTextColor
                        wrapMode: Text.Wrap
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            Rectangle {
                color: window.color

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true

                        ColumnLayout {
                            Label {
                                text: qsTr("Mod 资料库")
                                color: window.textColor
                                font.pixelSize: 28
                                font.bold: true
                            }

                            Label {
                                text: qsTr("%1 个 Mod · %2 个已启用").arg(appController.modCount).arg(appController.enabledCount)
                                color: window.mutedTextColor
                            }
                        }

                        Item { Layout.fillWidth: true }

                        CheckBox {
                            id: singleSelect
                            text: qsTr("同组单选")
                            checked: true
                        }

                        Button {
                            text: qsTr("重新扫描")
                            onClicked: appController.refreshLibrary()
                        }
                    }

                    Rectangle {
                        visible: appController.lastMessage.length > 0
                        Layout.fillWidth: true
                        Layout.preferredHeight: messageLabel.implicitHeight + 24
                        radius: 8
                        color: window.raisedColor

                        Label {
                            id: messageLabel
                            anchors.fill: parent
                            anchors.margins: 12
                            text: appController.lastMessage
                            color: window.mutedTextColor
                            wrapMode: Text.Wrap
                        }
                    }

                    GridView {
                        id: modGrid
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: appController.modsModel
                        cellWidth: 290
                        cellHeight: 250

                        delegate: Item {
                            id: card
                            required property int index
                            required property string displayName
                            required property string directoryName
                            required property string groupPath
                            required property bool modEnabled
                            required property string previewUrl
                            required property string fullPath

                            width: modGrid.cellWidth
                            height: modGrid.cellHeight

                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 7
                                radius: 12
                                color: cardHover.hovered ? window.raisedHoverColor : window.raisedColor

                                HoverHandler {
                                    id: cardHover
                                }

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        radius: 8
                                        color: "#151820"
                                        clip: true

                                        Image {
                                            anchors.fill: parent
                                            source: card.previewUrl
                                            fillMode: Image.PreserveAspectCrop
                                            asynchronous: true
                                            visible: card.previewUrl.length > 0
                                        }

                                        Label {
                                            anchors.centerIn: parent
                                            visible: card.previewUrl.length === 0
                                            text: "RLSM"
                                            color: window.mutedTextColor
                                            font.pixelSize: 20
                                            font.bold: true
                                        }
                                    }

                                    Label {
                                        Layout.fillWidth: true
                                        text: card.displayName
                                        color: window.textColor
                                        font.pixelSize: 16
                                        font.bold: true
                                        elide: Text.ElideRight
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true

                                        Label {
                                            Layout.fillWidth: true
                                            text: card.groupPath
                                            color: window.mutedTextColor
                                            elide: Text.ElideMiddle
                                        }

                                        Button {
                                            text: card.modEnabled ? qsTr("停用") : qsTr("启用")
                                            onClicked: appController.toggleMod(card.index, singleSelect.checked)
                                        }
                                    }
                                }
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            visible: appController.modCount === 0
                            text: qsTr("Mods 目录中还没有识别到 Mod")
                            color: window.mutedTextColor
                            font.pixelSize: 16
                        }
                    }
                }
            }
        }
    }
}
