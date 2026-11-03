import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as App
import "../components" as C

ScrollView {
    id: page
    signal moduleBrowseRequested()
    signal prefixBrowseRequested()
    clip: true
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ColumnLayout {
        width: page.availableWidth
        spacing: 20
        Label { text: qsTr("游戏环境"); color: App.Theme.text; font.pixelSize: 29; font.weight: Font.DemiBold }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: moduleContent.implicitHeight + 44
            ColumnLayout {
                id: moduleContent
                anchors.fill: parent
                anchors.margins: 22
                spacing: 16
                RowLayout {
                    C.Icon { name: "folder"; color: App.Theme.accent }
                    Label { text: qsTr("XXMI 模块"); color: App.Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Item { Layout.fillWidth: true }
                    C.StatusPill { text: appController.environmentReady ? qsTr("已连接") : qsTr("待配置"); ready: appController.environmentReady }
                }
                Label { text: qsTr("模块目录"); color: App.Theme.muted; font.pixelSize: 13 }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    C.Field {
                        id: modulePath
                        Layout.fillWidth: true
                        text: appController.modulePath
                        placeholderText: qsTr("XXMI 模块路径")
                        onAccepted: appController.setModulePath(text)
                        Connections {
                            target: appController
                            function onStateChanged() { if (!modulePath.activeFocus) modulePath.text = appController.modulePath }
                        }
                    }
                    C.ActionButton { text: qsTr("浏览"); symbol: "folder"; onClicked: page.moduleBrowseRequested() }
                    C.ActionButton { text: qsTr("连接"); kind: "primary"; onClicked: appController.setModulePath(modulePath.text) }
                }
                Label {
                    Layout.fillWidth: true
                    text: appController.environmentDetails
                    color: appController.environmentReady ? App.Theme.muted : App.Theme.warning
                    wrapMode: Text.WrapAnywhere
                    font.pixelSize: 13
                    lineHeight: 1.4
                }
            }
        }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: wineContent.implicitHeight + 44
            ColumnLayout {
                id: wineContent
                anchors.fill: parent
                anchors.margins: 22
                spacing: 16
                RowLayout {
                    C.Icon { name: "game"; color: App.Theme.accent }
                    Label { text: qsTr("Lutris 与 Wine"); color: App.Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Item { Layout.fillWidth: true }
                    C.ActionButton { text: qsTr("刷新"); symbol: "refresh"; kind: "quiet"; implicitHeight: 32; onClicked: appController.refreshLutris() }
                }
                Label { text: qsTr("游戏启动项"); color: App.Theme.muted; font.pixelSize: 13 }
                C.SelectField {
                    Layout.fillWidth: true
                    model: appController.lutrisProfileOptions
                    currentIndex: appController.currentLutrisProfileIndex
                    onActivated: appController.selectLutrisProfile(currentIndex)
                }
                Label { text: qsTr("Wine 前缀"); color: App.Theme.muted; font.pixelSize: 13 }
                RowLayout {
                    Layout.fillWidth: true
                    C.Field { Layout.fillWidth: true; text: appController.winePrefix; readOnly: true; placeholderText: qsTr("未选择 Wine 前缀") }
                    C.ActionButton { text: qsTr("选择前缀"); onClicked: page.prefixBrowseRequested() }
                }
                C.ActionButton { visible: appController.hasWinePrefixOverride; text: qsTr("恢复 Lutris 前缀"); kind: "quiet"; onClicked: appController.clearWinePrefixOverride() }
                Label { Layout.fillWidth: true; text: appController.wineDetails; color: App.Theme.muted; font.pixelSize: 13; wrapMode: Text.WrapAnywhere; lineHeight: 1.4 }
            }
        }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: reloadContent.implicitHeight + 44
            ColumnLayout {
                id: reloadContent
                anchors.fill: parent
                anchors.margins: 22
                spacing: 14
                RowLayout {
                    C.Icon { name: "keyboard"; color: App.Theme.accent }
                    Label { text: qsTr("游戏内刷新"); color: App.Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Item { Layout.fillWidth: true }
                    C.StatusPill { text: appController.hyprlandAvailable ? qsTr("可用") : qsTr("不可用"); ready: appController.hyprlandAvailable }
                }
                RowLayout {
                    Layout.fillWidth: true
                    C.Toggle {
                        text: qsTr("切换 Mod 后自动发送 F10")
                        checked: appController.reloadAfterToggle
                        onToggled: appController.setReloadAfterToggle(checked)
                    }
                    Item { Layout.fillWidth: true }
                    C.ActionButton { text: qsTr("发送 F10"); enabled: appController.hyprlandAvailable; onClicked: appController.reloadGame() }
                }
            }
        }
        Item { Layout.preferredHeight: 12 }
    }
}
