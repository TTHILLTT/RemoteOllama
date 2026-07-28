import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    width: Theme.sidebarWidth
    color: Theme.bgSecondary

    // ── Header: New Chat Button ─────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // New chat button
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 56

            Button {
                anchors.centerIn: parent
                text: "+ New Chat"
                flat: false
                font.pixelSize: Theme.fontSizeMd
                contentItem: Text {
                    text: parent.text
                    color: "#FFFFFF"
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: parent.hovered ? Theme.primaryHover : Theme.primary
                    radius: Theme.borderRadius
                }
                onClicked: sessionListVM.create_session("", "New Chat")
                Layout.fillWidth: true
                Layout.margins: Theme.spacingMd
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.borderColor
        }

        // ── Session List ────────────────────────────────────────
        ListView {
            id: sessionList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: sessionListVM.sessions
            spacing: 2

            delegate: Rectangle {
                width: ListView.view.width
                height: 64
                color: sessionListVM.current_session_id === modelData.id
                       ? Theme.bgHover : "transparent"
                radius: Theme.borderRadius

                MouseArea {
                    anchors.fill: parent
                    onClicked: sessionListVM.select_session(modelData.id)
                    onPressAndHold: contextMenu.popup()
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: 2

                    Text {
                        Layout.fillWidth: true
                        text: modelData.title || "New Chat"
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSizeMd
                        font.bold: sessionListVM.current_session_id === modelData.id
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }

                    RowLayout {
                        spacing: Theme.spacingSm
                        Text {
                            text: modelData.model || "No model"
                            color: Theme.textSecondary
                            font.pixelSize: Theme.fontSizeSm
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.updated_at ? modelData.updated_at.substring(11, 16) : ""
                            color: Theme.textMuted
                            font.pixelSize: Theme.fontSizeXs
                        }
                    }
                }

                // Context menu
                Menu {
                    id: contextMenu
                    MenuItem {
                        text: "Rename"
                        onTriggered: {
                            // Simple prompt-based rename
                            sessionListVM.rename_session(modelData.id, "Renamed Chat")
                        }
                    }
                    MenuItem {
                        text: "Duplicate"
                        onTriggered: sessionListVM.duplicate_session(modelData.id, modelData.model)
                    }
                    MenuSeparator {}
                    MenuItem {
                        text: "Delete"
                        onTriggered: sessionListVM.delete_session(modelData.id)
                    }
                }
            }
        }

        // ── Bottom: Settings Button ─────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.borderColor
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 48

            Button {
                anchors.centerIn: parent
                text: "⚙  Settings"
                flat: true
                font.pixelSize: Theme.fontSizeMd
                contentItem: Text {
                    text: parent.text
                    color: parent.hovered ? Theme.textPrimary : Theme.textSecondary
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: root.StackView.view.push(settingsPage)
            }
        }
    }
}
