import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "." as App
import "components" as C
import "pages" as Pages

ApplicationWindow {
    id: window
    objectName: "mainWindow"
    width: 1320
    height: 880
    minimumWidth: 1020
    minimumHeight: 700
    visible: true
    title: "RLSM · Rainy Linux Skin Manager"
    color: "#0e1723"
    font.family: "Noto Sans"
    font.pixelSize: 14
    palette.window: "#14202d"
    palette.windowText: App.Theme.text
    palette.text: App.Theme.text
    palette.buttonText: App.Theme.text
    palette.base: "#101a26"
    palette.highlight: App.Theme.accent
    palette.highlightedText: App.Theme.accentInk

    property int currentPage: 0
    property string lastShownMessage: ""
    property bool initialized: false
    Component.onCompleted: { lastShownMessage = appController.lastMessage; initialized = true }
    Binding { target: App.Theme; property: "accent"; value: appearance.accentColor }

    background: Rectangle {
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: App.Theme.gradientStart }
            GradientStop { position: 0.5; color: App.Theme.gradientMiddle }
            GradientStop { position: 1; color: App.Theme.gradientEnd }
        }
        Image {
            anchors.fill: parent
            source: appearance.backgroundUrl
            fillMode: appearance.backgroundFit === 0 ? Image.PreserveAspectCrop : Image.PreserveAspectFit
            asynchronous: true
            sourceSize.width: Math.max(window.width, 1920)
        }
        Rectangle {
            anchors.fill: parent
            color: "#0c1420"
            opacity: appearance.backgroundUrl.length > 0 ? appearance.backgroundDim : 0.18
        }
    }

    FolderDialog { id: moduleDialog; title: qsTr("选择 XXMI 模块目录"); onAccepted: appController.setModuleUrl(selectedFolder) }
    FolderDialog { id: prefixDialog; title: qsTr("选择 Wine 前缀"); onAccepted: appController.setWinePrefixUrl(selectedFolder) }
    FileDialog {
        id: archiveDialog
        title: qsTr("导入 Mod 压缩包")
        nameFilters: [qsTr("Mod 压缩包 (*.zip *.7z *.rar)"), qsTr("所有文件 (*)")]
        onAccepted: { appController.importModUrl(selectedFile); importDialog.close() }
    }
    FolderDialog {
        id: modFolderDialog
        title: qsTr("导入 Mod 目录")
        onAccepted: { appController.importModFolderUrl(selectedFolder); importDialog.close() }
    }
    FileDialog {
        id: backgroundDialog
        title: qsTr("选择背景图片")
        nameFilters: [qsTr("图片 (*.png *.jpg *.jpeg *.webp *.bmp)"), qsTr("所有文件 (*)")]
        onAccepted: appearance.setBackground(selectedFile)
    }

    Connections {
        target: appController
        function onStateChanged() {
            if (window.initialized && appController.lastMessage.length > 0 && appController.lastMessage !== window.lastShownMessage) {
                window.lastShownMessage = appController.lastMessage
                messageText.text = appController.lastMessage
                notice.open()
                noticeTimer.restart()
            }
        }
    }
    Connections {
        target: appearance
        function onErrorOccurred(message) { messageText.text = message; notice.open(); noticeTimer.restart() }
    }

    component NavButton: Button {
        id: nav
        required property int pageIndex
        required property string symbol
        Layout.fillWidth: true
        implicitHeight: 46
        checkable: true
        checked: window.currentPage === pageIndex
        hoverEnabled: true
        leftPadding: 14
        contentItem: RowLayout {
            spacing: 13
            C.Icon { name: nav.symbol; color: nav.checked ? App.Theme.accent : App.Theme.muted; width: 18; height: 18 }
            Label { text: nav.text; color: nav.checked ? App.Theme.text : App.Theme.muted; font.pixelSize: 14; font.weight: nav.checked ? Font.DemiBold : Font.Normal; Layout.fillWidth: true }
            Rectangle { visible: nav.checked; width: 4; height: 16; radius: 2; color: App.Theme.accent }
        }
        background: Rectangle { radius: 9; color: nav.checked ? App.Theme.accentSoft : nav.hovered ? "#aa243440" : "transparent" }
        onClicked: window.currentPage = pageIndex
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.preferredWidth: 210
            Layout.fillHeight: true
            color: "#e6101a26"
            Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#34334252" }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 7
                RowLayout {
                    Layout.topMargin: 14
                    Layout.leftMargin: 8
                    spacing: 11
                    Rectangle {
                        width: 36; height: 36; radius: 11; color: App.Theme.accent
                        Text { anchors.centerIn: parent; text: "R"; font.pixelSize: 24; font.weight: Font.Black; color: App.Theme.accentInk }
                    }
                    Column {
                        spacing: 2
                        Label { text: "RLSM"; color: App.Theme.text; font.pixelSize: 20; font.weight: Font.Bold; font.letterSpacing: 1 }
                        Label { text: "Rainy Skin Manager"; color: App.Theme.subtle; font.pixelSize: 10 }
                    }
                }
                NavButton { Layout.topMargin: 34; pageIndex: 0; symbol: "grid"; text: qsTr("Mod 资料库") }
                NavButton { pageIndex: 1; symbol: "game"; text: qsTr("游戏环境") }
                Item { Layout.fillHeight: true }
                NavButton { pageIndex: 2; symbol: "image"; text: qsTr("外观") }
                Rectangle { Layout.fillWidth: true; Layout.topMargin: 14; Layout.bottomMargin: 14; height: 1; color: App.Theme.border }
                RowLayout {
                    Layout.leftMargin: 12
                    Layout.bottomMargin: 10
                    spacing: 8
                    Rectangle { width: 6; height: 6; radius: 3; color: appController.environmentReady ? App.Theme.accent : App.Theme.warning }
                    Label { text: appController.importerName + (appController.environmentReady ? qsTr(" · 已连接") : qsTr(" · 待配置")); color: App.Theme.muted; font.pixelSize: 12 }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 86
                color: "#77101a26"
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#44344454" }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 30
                    anchors.rightMargin: 30
                    spacing: 14
                    C.SelectField {
                        objectName: "gameSelector"
                        Layout.preferredWidth: Math.min(360, window.width * 0.29)
                        model: appController.gameOptions
                        currentIndex: appController.currentGameIndex
                        onActivated: appController.selectGame(currentIndex)
                    }
                    Item { Layout.fillWidth: true }
                    C.ActionButton {
                        text: "F10"
                        symbol: "keyboard"
                        kind: "quiet"
                        enabled: appController.hyprlandAvailable
                        onClicked: appController.reloadGame()
                    }
                    C.ActionButton {
                        text: qsTr("启动游戏")
                        symbol: "play"
                        kind: "primary"
                        enabled: appController.canLaunch
                        onClicked: appController.launchSelectedProfile()
                        ToolTip.visible: hovered && !appController.canLaunch
                        ToolTip.text: qsTr("请在游戏环境中绑定 Lutris 启动项")
                    }
                }
            }

            StackLayout {
                id: pages
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 30
                Layout.bottomMargin: 14
                currentIndex: window.currentPage
                Pages.LibraryPage {
                    objectName: "libraryPage"
                    onImportRequested: importDialog.open()
                    onEnvironmentRequested: window.currentPage = 1
                    onClassificationRequested: classifyDialog.open()
                }
                Pages.EnvironmentPage {
                    objectName: "environmentPage"
                    onModuleBrowseRequested: moduleDialog.open()
                    onPrefixBrowseRequested: prefixDialog.open()
                }
                Pages.AppearancePage { objectName: "appearancePage"; onBackgroundBrowseRequested: backgroundDialog.open() }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 30
                Layout.rightMargin: 30
                Layout.bottomMargin: 18
                Label { text: appController.gameName; color: App.Theme.subtle; font.pixelSize: 11 }
                Label { text: "/"; color: App.Theme.subtle; font.pixelSize: 11 }
                Label { Layout.fillWidth: true; text: appController.modsPath || qsTr("尚未连接 Mod 目录"); color: App.Theme.subtle; font.pixelSize: 11; elide: Text.ElideMiddle }
                Label { text: "RLSM 0.1"; color: App.Theme.subtle; font.pixelSize: 11 }
            }
        }
    }

    Dialog {
        id: importDialog
        objectName: "importDialog"
        anchors.centerIn: parent
        width: 540
        modal: true
        padding: 28
        background: C.Panel { color: "#172330"; border.color: "#3e5262" }
        contentItem: ColumnLayout {
            spacing: 18
            RowLayout {
                Label { text: qsTr("导入 Mod"); color: App.Theme.text; font.pixelSize: 24; font.weight: Font.DemiBold }
                Item { Layout.fillWidth: true }
                C.ActionButton { symbol: "close"; kind: "quiet"; implicitWidth: 34; implicitHeight: 34; onClicked: importDialog.close() }
            }
            C.ActionButton { Layout.fillWidth: true; text: qsTr("压缩包（ZIP / 7z / RAR）"); symbol: "upload"; kind: "primary"; implicitHeight: 52; onClicked: archiveDialog.open() }
            C.ActionButton { Layout.fillWidth: true; text: qsTr("文件夹"); symbol: "folder"; implicitHeight: 52; onClicked: modFolderDialog.open() }
            Label { Layout.fillWidth: true; text: qsTr("导入后保持停用；同名 Mod 不会被覆盖。"); color: App.Theme.subtle; font.pixelSize: 12; wrapMode: Text.WordWrap }
        }
    }

    Dialog {
        id: classifyDialog
        anchors.centerIn: parent
        width: 500
        modal: true
        padding: 26
        background: C.Panel { color: "#172330" }
        contentItem: ColumnLayout {
            spacing: 20
            Label { text: qsTr("整理分类"); color: App.Theme.text; font.pixelSize: 22; font.weight: Font.DemiBold }
            Label { Layout.fillWidth: true; text: qsTr("只整理根目录和“未分类”中的 Mod。无法识别的内容保留原位。"); color: App.Theme.muted; wrapMode: Text.WordWrap; lineHeight: 1.4 }
            RowLayout {
                Item { Layout.fillWidth: true }
                C.ActionButton { text: qsTr("取消"); onClicked: classifyDialog.close() }
                C.ActionButton { text: qsTr("整理"); kind: "primary"; onClicked: { classifyDialog.close(); appController.autoCategorize() } }
            }
        }
    }

    Popup {
        id: notice
        parent: Overlay.overlay
        x: Math.max(230, (window.width - width) / 2)
        y: window.height - height - 44
        width: Math.min(680, window.width - 270)
        padding: 16
        closePolicy: Popup.CloseOnEscape
        background: C.Panel { color: "#f2223442"; border.color: App.Theme.accentBorder }
        contentItem: RowLayout {
            spacing: 12
            C.Icon { name: "info"; color: App.Theme.accent }
            Label { id: messageText; Layout.fillWidth: true; color: App.Theme.text; wrapMode: Text.Wrap; font.pixelSize: 13 }
            C.ActionButton { symbol: "close"; kind: "quiet"; implicitWidth: 28; implicitHeight: 28; onClicked: notice.close() }
        }
    }
    Timer { id: noticeTimer; interval: 8500; onTriggered: notice.close() }
}
