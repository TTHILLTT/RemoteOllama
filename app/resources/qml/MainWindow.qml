import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 1100
    height: 750
    minimumWidth: 800
    minimumHeight: 600
    title: "RemoteOllama"

    // Apply theme
    color: Theme.bgPrimary

    // ── Main Layout: Sidebar + Content ─────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Left sidebar
        Sidebar {
            id: sidebar
            Layout.preferredWidth: Theme.sidebarWidth
            Layout.fillHeight: true
        }

        // Divider
        Rectangle {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            color: Theme.borderColor
        }

        // Right content area with StackView
        StackView {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            initialItem: chatPage
        }
    }

    // ── Pages ──────────────────────────────────────────────────
    Component {
        id: chatPage
        ChatView {}
    }

    Component {
        id: settingsPage
        SettingsPage {}
    }

    // ── Model Selection Dialog ─────────────────────────────────
    Popup {
        id: modelSelectorDialog
        modal: true
        anchors.centerIn: parent
        width: 400
        height: 450
        padding: Theme.spacingLg
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            color: Theme.bgSecondary
            border.color: Theme.borderColor
            border.width: 1
            radius: Theme.borderRadiusLg
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: Theme.spacingMd

            Text {
                text: "Select Model"
                font.pixelSize: Theme.fontSizeXl
                font.bold: true
                color: Theme.textPrimary
            }

            Text {
                text: "Choose a model for this conversation:"
                color: Theme.textSecondary
                font.pixelSize: Theme.fontSizeMd
                wrapMode: Text.Wrap
            }

            ListView {
                id: modelList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: modelSelectorVM.models

                delegate: Rectangle {
                    width: ListView.view.width
                    height: 48
                    color: modelSelectorVM.selected_model === modelData.name
                           ? Theme.bgHover : "transparent"
                    radius: Theme.borderRadius

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: Theme.spacingMd
                        spacing: Theme.spacingMd

                        Text {
                            text: modelData.name || "Unknown"
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontSizeMd
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.size_display || ""
                            color: Theme.textSecondary
                            font.pixelSize: Theme.fontSizeSm
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: modelSelectorVM.selected_model = modelData.name
                    }
                }
            }

            RowLayout {
                spacing: Theme.spacingSm
                Layout.alignment: Qt.AlignRight

                Button {
                    text: "Refresh"
                    flat: true
                    onClicked: modelSelectorVM.fetch_models()
                    enabled: !modelSelectorVM.loading
                }
                Button {
                    text: "OK"
                    enabled: modelSelectorVM.selected_model !== ""
                    background: Rectangle {
                        color: parent.enabled
                               ? (parent.hovered ? Theme.primaryHover : Theme.primary)
                               : Theme.bgTertiary
                        radius: Theme.borderRadius
                    }
                    contentItem: Text {
                        text: parent.text
                        color: parent.enabled ? "#FFFFFF" : Theme.textMuted
                        font.pixelSize: Theme.fontSizeMd
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: modelSelectorDialog.close()
                }
            }
        }
    }

    // ── Toast Notification ─────────────────────────────────────
    Popup {
        id: toast
        width: 400
        height: 48
        x: (mainWindow.width - width) / 2
        y: mainWindow.height - height - 24
        padding: Theme.spacingMd
        closePolicy: Popup.NoAutoClose

        background: Rectangle {
            color: Theme.isDark ? "#2D2D3F" : "#333333"
            radius: Theme.borderRadius
        }

        Text {
            id: toastText
            anchors.centerIn: parent
            color: "#FFFFFF"
            font.pixelSize: Theme.fontSizeMd
        }

        Timer {
            id: toastTimer
            interval: 3000
            onTriggered: toast.close()
        }

        function show(message) {
            toastText.text = message
            toast.open()
            toastTimer.restart()
        }
    }

    // ── Error handler ──────────────────────────────────────────
    Connections {
        function onError_occurred(message) {
            toast.show(message)
        }
    }
}
