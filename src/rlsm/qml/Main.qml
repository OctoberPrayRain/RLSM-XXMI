import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: window

    width: 1240
    height: 820
    minimumWidth: 940
    minimumHeight: 680
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
        id: moduleFolderDialog
        title: qsTr("选择 XXMI 根目录或 %1 目录").arg(appController.importerName)
        onAccepted: appController.setModuleUrl(selectedFolder)
    }

    FolderDialog {
        id: prefixFolderDialog
        title: qsTr("选择 %1 使用的 Wine 前缀").arg(appController.gameName)
        onAccepted: appController.setWinePrefixUrl(selectedFolder)
    }

    FileDialog {
        id: importFileDialog
        title: qsTr("选择 Mod 压缩包")
        fileMode: FileDialog.OpenFile
        nameFilters: [qsTr("Mod 压缩包 (*.zip *.7z *.rar)"), qsTr("所有文件 (*)")]
        onAccepted: appController.importModUrl(selectedFile)
    }

    FolderDialog {
        id: importFolderDialog
        title: qsTr("选择需要导入的 Mod 目录")
        onAccepted: appController.importModFolderUrl(selectedFolder)
    }

    Connections {
        target: appController

        function onStateChanged() {
            if (!modulePathField.activeFocus)
                modulePathField.text = appController.modulePath
            gameSelector.currentIndex = appController.currentGameIndex
            lutrisSelector.currentIndex = appController.currentLutrisProfileIndex
        }
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
                    text: qsTr("游戏环境")
                }

                NavigationButton {
                    pageIndex: 1
                    text: qsTr("Mod 资料库")
                }

                NavigationButton {
                    pageIndex: 2
                    text: qsTr("导入与分类")
                }

                Item { Layout.fillHeight: true }

                Label {
                    Layout.fillWidth: true
                    text: appController.gameName + " · " + appController.importerName
                    color: window.mutedTextColor
                    font.pixelSize: 12
                    elide: Text.ElideRight
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
                    anchors.margins: 28
                    spacing: 11

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            text: qsTr("游戏环境")
                            color: window.textColor
                            font.pixelSize: 30
                            font.bold: true
                        }

                        Item { Layout.fillWidth: true }

                        ComboBox {
                            id: gameSelector
                            Layout.preferredWidth: 390
                            model: appController.gameOptions
                            currentIndex: appController.currentGameIndex
                            onActivated: appController.selectGame(currentIndex)
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("每个游戏分别绑定 XXMI 模块、Lutris 启动项和 Wine 前缀。")
                        color: window.mutedTextColor
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: modulePathField
                            Layout.fillWidth: true
                            text: appController.modulePath
                            placeholderText: qsTr("XXMI 根目录或 %1 目录").arg(appController.importerName)
                            selectByMouse: true
                            onAccepted: appController.setModulePath(text)
                        }

                        Button {
                            text: qsTr("浏览")
                            onClicked: moduleFolderDialog.open()
                        }

                        Button {
                            text: qsTr("检查模块")
                            onClicked: appController.setModulePath(modulePathField.text)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 145
                        radius: 12
                        color: window.raisedColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 16

                            Rectangle {
                                Layout.preferredWidth: 10
                                Layout.fillHeight: true
                                radius: 5
                                color: appController.environmentReady ? window.successColor : window.warningColor
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 8

                                Label {
                                    text: appController.environmentTitle
                                    color: window.textColor
                                    font.pixelSize: 18
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

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            text: qsTr("Lutris 与 Wine")
                            color: window.textColor
                            font.pixelSize: 20
                            font.bold: true
                        }

                        Item { Layout.fillWidth: true }

                        Button {
                            text: qsTr("重新读取 Lutris")
                            onClicked: appController.refreshLutris()
                        }
                    }

                    ComboBox {
                        id: lutrisSelector
                        Layout.fillWidth: true
                        model: appController.lutrisProfileOptions
                        currentIndex: appController.currentLutrisProfileIndex
                        onActivated: appController.selectLutrisProfile(currentIndex)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            Layout.fillWidth: true
                            text: appController.winePrefix
                            placeholderText: qsTr("Lutris 启动项没有前缀时，在这里单独指定")
                            readOnly: true
                            selectByMouse: true
                        }

                        Button {
                            text: qsTr("选择前缀")
                            onClicked: prefixFolderDialog.open()
                        }

                        Button {
                            visible: appController.hasWinePrefixOverride
                            text: qsTr("恢复 Lutris 配置")
                            onClicked: appController.clearWinePrefixOverride()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        radius: 12
                        color: window.raisedColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 16

                            Rectangle {
                                Layout.preferredWidth: 10
                                Layout.fillHeight: true
                                radius: 5
                                color: appController.wineReady ? window.successColor : window.warningColor
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 8

                                Label {
                                    text: appController.wineTitle
                                    color: window.textColor
                                    font.pixelSize: 18
                                    font.bold: true
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: appController.wineDetails
                                    color: window.mutedTextColor
                                    wrapMode: Text.Wrap
                                }

                                Item { Layout.fillHeight: true }
                            }

                            Button {
                                text: qsTr("由 Lutris 启动")
                                enabled: appController.canLaunch
                                onClicked: appController.launchSelectedProfile()
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        CheckBox {
                            text: qsTr("切换 Mod 后自动发送 F10")
                            checked: appController.reloadAfterToggle
                            palette.windowText: window.textColor
                            onToggled: {
                                if (checked !== appController.reloadAfterToggle)
                                    appController.setReloadAfterToggle(checked)
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: appController.hyprlandAvailable ? qsTr("Hyprland 可以使用") : qsTr("当前会话无法控制 Hyprland")
                            color: appController.hyprlandAvailable ? window.successColor : window.warningColor
                        }

                        Button {
                            text: qsTr("向游戏发送 F10")
                            enabled: appController.hyprlandAvailable
                            onClicked: appController.reloadGame()
                        }
                    }

                    Label {
                        visible: appController.lastMessage.length > 0
                        Layout.fillWidth: true
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
                                text: appController.gameName + " · " + qsTr("Mod 资料库")
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
                            palette.windowText: window.textColor
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

            Rectangle {
                color: window.color

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 18

                    Label {
                        text: appController.gameName + " · " + qsTr("导入与分类")
                        color: window.textColor
                        font.pixelSize: 28
                        font.bold: true
                    }

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("导入器会识别一个或多个 Mod，自动放入角色、武器、界面或未分类目录。新导入的 Mod 默认停用。")
                        color: window.mutedTextColor
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 190
                        radius: 12
                        color: window.raisedColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12

                            Label {
                                text: qsTr("导入 Mod")
                                color: window.textColor
                                font.pixelSize: 20
                                font.bold: true
                            }

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("支持普通目录、ZIP、7z 和 RAR。压缩包外层目录会自动跳过；同名 Mod 会保留两份。")
                                color: window.mutedTextColor
                                wrapMode: Text.WordWrap
                            }

                            Item { Layout.fillHeight: true }

                            RowLayout {
                                Button {
                                    text: qsTr("选择压缩包")
                                    onClicked: importFileDialog.open()
                                }

                                Button {
                                    text: qsTr("选择目录")
                                    onClicked: importFolderDialog.open()
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 190
                        radius: 12
                        color: window.raisedColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12

                            Label {
                                text: qsTr("自动分类现有 Mod")
                                color: window.textColor
                                font.pixelSize: 20
                                font.bold: true
                            }

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("检查根目录和“未分类”目录中的 Mod。识别依据包括 .rlsm.json、模型文件名称前缀和目录名称；已有分类不会移动。")
                                color: window.mutedTextColor
                                wrapMode: Text.WordWrap
                            }

                            Item { Layout.fillHeight: true }

                            Button {
                                text: qsTr("开始自动分类")
                                onClicked: appController.autoCategorize()
                            }
                        }
                    }

                    Rectangle {
                        visible: appController.lastMessage.length > 0
                        Layout.fillWidth: true
                        Layout.preferredHeight: importMessage.implicitHeight + 24
                        radius: 8
                        color: window.raisedColor

                        Label {
                            id: importMessage
                            anchors.fill: parent
                            anchors.margins: 12
                            text: appController.lastMessage
                            color: window.mutedTextColor
                            wrapMode: Text.Wrap
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
    }
}
