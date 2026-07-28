import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: Theme.bgPrimary

    // Header with back button
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Top bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Theme.topBarHeight
            color: Theme.bgPrimary
            border.color: Theme.borderColor
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: Theme.spacingMd
                spacing: Theme.spacingMd

                Button {
                    text: "← Back"
                    flat: true
                    font.pixelSize: Theme.fontSizeMd
                    contentItem: Text {
                        text: parent.text
                        color: Theme.textSecondary
                        font: parent.font
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: root.StackView.view.pop()
                }

                Text {
                    text: "Settings"
                    font.pixelSize: Theme.fontSizeLg
                    font.bold: true
                    color: Theme.textPrimary
                    Layout.fillWidth: true
                }
            }
        }

        // Settings content
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: Math.min(600, root.width - Theme.spacingXl * 2)
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: Theme.spacingXl

                // ── Section: Server ─────────────────────────────
                GroupBox {
                    title: "Server Connection"
                    Layout.fillWidth: true

                    ColumnLayout {
                        spacing: Theme.spacingMd
                        anchors.fill: parent

                        RowLayout {
                            Text { text: "Server URL:"; color: Theme.textPrimary; Layout.preferredWidth: 120 }
                            TextField {
                                id: serverUrlField
                                text: settingsVM.server_url
                                color: Theme.textPrimary
                                Layout.fillWidth: true
                                placeholderText: "http://localhost:11434"
                                onTextChanged: settingsVM.server_url = text
                                background: Rectangle {
                                    color: Theme.bgSecondary
                                    border.color: parent.activeFocus ? Theme.borderFocus : Theme.borderColor
                                    radius: Theme.borderRadius
                                }
                            }
                        }

                        RowLayout {
                            spacing: Theme.spacingSm
                            Button {
                                text: "Test Connection"
                                onClicked: settingsVM.test_connection()
                                background: Rectangle {
                                    color: parent.hovered ? Theme.primaryHover : Theme.primary
                                    radius: Theme.borderRadius
                                }
                                contentItem: Text {
                                    text: parent.text
                                    color: "#FFFFFF"
                                    font.pixelSize: Theme.fontSizeSm
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            Text {
                                id: connectionStatus
                                text: ""
                                color: Theme.textSecondary
                                font.pixelSize: Theme.fontSizeSm
                            }
                        }

                        // Connection test result handler
                        Connections {
                            function onConnection_test_result(success, message) {
                                connectionStatus.text = message
                                connectionStatus.color = success ? Theme.successColor : Theme.errorColor
                            }
                        }
                    }
                }

                // ── Section: Appearance ─────────────────────────
                GroupBox {
                    title: "Appearance"
                    Layout.fillWidth: true

                    ColumnLayout {
                        spacing: Theme.spacingMd
                        anchors.fill: parent

                        RowLayout {
                            Text { text: "Theme:"; color: Theme.textPrimary; Layout.preferredWidth: 120 }
                            ComboBox {
                                id: themeCombo
                                model: ["dark", "light"]
                                currentIndex: settingsVM.theme === "light" ? 1 : 0
                                onCurrentTextChanged: settingsVM.theme = currentText
                                contentItem: Text {
                                    text: parent.currentText
                                    color: Theme.textPrimary
                                    font.pixelSize: Theme.fontSizeMd
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }

                        RowLayout {
                            Text { text: "Font Size:"; color: Theme.textPrimary; Layout.preferredWidth: 120 }
                            SpinBox {
                                id: fontSizeSpin
                                from: 8
                                to: 48
                                value: settingsVM.font_size
                                onValueChanged: settingsVM.font_size = value
                            }
                        }
                    }
                }

                // ── Section: Chat ───────────────────────────────
                GroupBox {
                    title: "Chat"
                    Layout.fillWidth: true

                    ColumnLayout {
                        spacing: Theme.spacingMd
                        anchors.fill: parent

                        RowLayout {
                            Text { text: "Streaming:"; color: Theme.textPrimary; Layout.preferredWidth: 120 }
                            Switch {
                                id: streamSwitch
                                checked: settingsVM.streaming_enabled
                                onCheckedChanged: settingsVM.streaming_enabled = checked
                            }
                        }

                        RowLayout {
                            Text { text: "Timeout (s):"; color: Theme.textPrimary; Layout.preferredWidth: 120 }
                            SpinBox {
                                id: timeoutSpin
                                from: 1
                                to: 600
                                value: settingsVM.timeout
                                onValueChanged: settingsVM.timeout = value
                            }
                        }

                        RowLayout {
                            Text { text: "Default Model:"; color: Theme.textPrimary; Layout.preferredWidth: 120 }
                            TextField {
                                id: defaultModelField
                                text: settingsVM.default_model
                                color: Theme.textPrimary
                                Layout.fillWidth: true
                                placeholderText: "e.g., qwen3:14b"
                                onTextChanged: settingsVM.default_model = text
                                background: Rectangle {
                                    color: Theme.bgSecondary
                                    border.color: parent.activeFocus ? Theme.borderFocus : Theme.borderColor
                                    radius: Theme.borderRadius
                                }
                            }
                        }
                    }
                }

                // ── Save Button ─────────────────────────────────
                Button {
                    text: "Save Settings"
                    Layout.alignment: Qt.AlignHCenter
                    background: Rectangle {
                        color: parent.hovered ? Theme.primaryHover : Theme.primary
                        radius: Theme.borderRadius
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "#FFFFFF"
                        font.pixelSize: Theme.fontSizeMd
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: settingsVM.save_settings()
                }

                // Bottom spacer
                Item { Layout.preferredHeight: Theme.spacingXl }
            }
        }
    }
}
