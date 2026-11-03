import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as App
import "../components" as C

Item {
    id: page
    signal importRequested()
    signal environmentRequested()
    signal classificationRequested()
    signal previewRequested(int row)
    signal deleteRequested(int row, string displayName)
    property bool singleSelection: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            ColumnLayout {
                spacing: 6
                Label { text: qsTr("Mod 资料库"); color: App.Theme.text; font.pixelSize: 29; font.weight: Font.DemiBold }
            }
            Item { Layout.fillWidth: true }
            C.ActionButton {
                text: qsTr("整理分类")
                symbol: "sort"
                enabled: appController.environmentReady && appController.modCount > 0
                onClicked: page.classificationRequested()
            }
            C.ActionButton {
                text: qsTr("导入 Mod")
                symbol: "plus"
                kind: "primary"
                enabled: appController.environmentReady
                onClicked: page.importRequested()
            }
        }

        C.Panel {
            Layout.fillWidth: true
            implicitHeight: 84
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                spacing: 26
                Repeater {
                    model: [
                        { label: qsTr("全部"), value: appController.modCount, tint: App.Theme.text },
                        { label: qsTr("启用"), value: appController.enabledCount, tint: App.Theme.accent },
                        { label: qsTr("停用"), value: appController.modCount - appController.enabledCount, tint: App.Theme.muted }
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        spacing: 10
                        Label { text: modelData.value; font.pixelSize: 27; font.weight: Font.DemiBold; color: modelData.tint }
                        Label { text: modelData.label; color: App.Theme.muted; font.pixelSize: 13 }
                    }
                }
                Item { Layout.fillWidth: true }
                C.ActionButton {
                    text: qsTr("刷新")
                    symbol: "refresh"
                    kind: "quiet"
                    enabled: appController.environmentReady
                    onClicked: appController.refreshLibrary()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            C.Field {
                id: search
                objectName: "modSearch"
                Layout.fillWidth: true
                placeholderText: qsTr("搜索 Mod 名称或分类…")
                text: appController.searchQuery
                leftPadding: 40
                onTextEdited: appController.setSearchQuery(text)
                C.Icon { name: "search"; color: App.Theme.subtle; width: 17; height: 17; x: 14; anchors.verticalCenter: parent.verticalCenter }
            }
            C.SelectField {
                Layout.preferredWidth: 170
                model: appController.categoryOptions
                currentIndex: Math.max(0, appController.categoryOptions.indexOf(appController.categoryFilter))
                onActivated: appController.setCategoryFilter(currentText)
            }
            C.SelectField {
                Layout.preferredWidth: 130
                model: [qsTr("全部状态"), qsTr("启用"), qsTr("停用")]
                currentIndex: appController.stateFilter
                onActivated: appController.setStateFilter(currentIndex)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Label { text: qsTr("%1 个 Mod").arg(appController.visibleModCount); color: App.Theme.muted; font.pixelSize: 12 }
            C.ActionButton {
                visible: appController.searchQuery.length > 0 || appController.categoryFilter !== "全部分类" || appController.stateFilter !== 0
                text: qsTr("清除筛选")
                kind: "quiet"
                implicitHeight: 30
                onClicked: appController.clearFilters()
            }
            Item { Layout.fillWidth: true }
            C.Toggle {
                text: qsTr("分类内单选")
                checked: page.singleSelection
                onToggled: page.singleSelection = checked
                ToolTip.visible: hovered
                ToolTip.text: qsTr("启用一个 Mod 时，停用同一分类的其他 Mod。")
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            GridView {
                id: grid
                anchors.fill: parent
                anchors.margins: -6
                clip: true
                visible: appController.visibleModCount > 0
                model: appController.modsModel
                cellWidth: width / Math.max(1, Math.floor(width / 240))
                cellHeight: 330
                ScrollBar.vertical: ScrollBar { }
                delegate: Item {
                    id: card
                    required property int index
                    required property string displayName
                    required property string groupPath
                    required property bool modEnabled
                    required property string previewUrl
                    required property string fullPath
                    width: grid.cellWidth
                    height: grid.cellHeight

                    C.Panel {
                        anchors.fill: parent
                        anchors.margins: 6
                        glassColor: hover.hovered ? App.Theme.hover : App.Theme.surface
                        borderColor: card.modEnabled ? App.Theme.accentBorder : App.Theme.border
                        HoverHandler { id: hover }
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: "#152430"
                                radius: 9
                                clip: true
                                Image {
                                    anchors.fill: parent
                                    source: card.previewUrl
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    cache: false
                                }
                                C.Icon {
                                    visible: card.previewUrl.length === 0
                                    anchors.centerIn: parent
                                    name: "image"
                                    width: 38
                                    height: 38
                                    color: "#3e5867"
                                }
                                C.StatusPill {
                                    anchors.top: parent.top
                                    anchors.right: parent.right
                                    anchors.margins: 9
                                    visible: card.modEnabled
                                    text: qsTr("已启用")
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: card.displayName
                                color: App.Theme.text
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                                ToolTip.visible: hover.hovered
                                ToolTip.text: card.fullPath
                            }
                            Label {
                                Layout.fillWidth: true
                                text: card.groupPath
                                color: App.Theme.muted
                                font.pixelSize: 12
                                elide: Text.ElideMiddle
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                C.ActionButton {
                                    text: qsTr("预览图")
                                    symbol: "image"
                                    implicitHeight: 34
                                    onClicked: page.previewRequested(card.index)
                                }
                                C.ActionButton {
                                    text: qsTr("删除")
                                    symbol: "trash"
                                    kind: "danger"
                                    implicitHeight: 34
                                    onClicked: page.deleteRequested(card.index, card.displayName)
                                }
                                Item { Layout.fillWidth: true }
                                C.ActionButton {
                                    text: card.modEnabled ? qsTr("停用") : qsTr("启用")
                                    kind: card.modEnabled ? "secondary" : "primary"
                                    implicitHeight: 34
                                    onClicked: appController.toggleMod(card.index, page.singleSelection)
                                }
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width - 50, 460)
                visible: appController.visibleModCount === 0
                spacing: 16
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 82
                    height: 82
                    radius: 24
                    color: App.Theme.accentSoft
                    C.Icon { anchors.centerIn: parent; name: appController.modCount > 0 ? "search" : "folder"; width: 34; height: 34; color: App.Theme.accent }
                }
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: !appController.environmentReady ? qsTr("未连接游戏环境")
                        : appController.modCount > 0 ? qsTr("没有匹配的 Mod") : qsTr("还没有 Mod")
                    color: App.Theme.text
                    font.pixelSize: 21
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: !appController.environmentReady ? qsTr("请选择 XXMI 模块目录。")
                        : appController.modCount > 0 ? qsTr("请修改搜索或筛选条件。")
                        : qsTr("支持文件夹、ZIP、7z 和 RAR。")
                    color: App.Theme.muted
                    font.pixelSize: 14
                    wrapMode: Text.WordWrap
                    lineHeight: 1.4
                }
                C.ActionButton {
                    Layout.alignment: Qt.AlignHCenter
                    text: !appController.environmentReady ? qsTr("配置游戏") : appController.modCount > 0 ? qsTr("清除筛选") : qsTr("导入 Mod")
                    symbol: appController.modCount > 0 ? "refresh" : "plus"
                    kind: "primary"
                    onClicked: {
                        if (!appController.environmentReady) page.environmentRequested()
                        else if (appController.modCount > 0) appController.clearFilters()
                        else page.importRequested()
                    }
                }
            }
        }
    }
}
