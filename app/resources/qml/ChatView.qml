import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: Theme.bgPrimary

    // Empty state when no session selected
    Rectangle {
        visible: sessionListVM.current_session_id <= 0
        anchors.fill: parent
        color: Theme.bgPrimary

        ColumnLayout {
            anchors.centerIn: parent
            spacing: Theme.spacingLg

            Text {
                text: "RemoteOllama"
                font.pixelSize: Theme.fontSizeXl * 1.5
                font.bold: true
                color: Theme.textPrimary
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Select a conversation from the sidebar\nor create a new one to get started."
                font.pixelSize: Theme.fontSizeMd
                color: Theme.textSecondary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }

            Button {
                text: "+ New Chat"
                Layout.alignment: Qt.AlignHCenter
                background: Rectangle {
                    color: parent.hovered ? Theme.primaryHover : Theme.primary
                    radius: Theme.borderRadius
                }
                contentItem: Text {
                    text: parent.text
                    color: "#FFFFFF"
                    font.pixelSize: Theme.fontSizeMd
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: sessionListVM.create_session("", "New Chat")
            }
        }
    }

    // Chat area (visible when session is selected)
    ColumnLayout {
        visible: sessionListVM.current_session_id > 0
        anchors.fill: parent
        spacing: 0

        // ── Top Bar ─────────────────────────────────────────────
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

                Text {
                    text: {
                        var sessions = sessionListVM.sessions
                        for (var i = 0; i < sessions.length; i++) {
                            if (sessions[i].id === sessionListVM.current_session_id) {
                                return sessions[i].title || "New Chat"
                            }
                        }
                        return "Chat"
                    }
                    font.pixelSize: Theme.fontSizeLg
                    font.bold: true
                    color: Theme.textPrimary
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                // Model badge
                Rectangle {
                    Layout.preferredHeight: 26
                    implicitWidth: modelLabel.implicitWidth + Theme.spacingMd * 2
                    radius: 13
                    color: Theme.bgTertiary

                    Text {
                        id: modelLabel
                        anchors.centerIn: parent
                        text: {
                            var sessions = sessionListVM.sessions
                            for (var i = 0; i < sessions.length; i++) {
                                if (sessions[i].id === sessionListVM.current_session_id) {
                                    return sessions[i].model || "No model"
                                }
                            }
                            return ""
                        }
                        font.pixelSize: Theme.fontSizeSm
                        color: Theme.textSecondary
                    }
                }
            }
        }

        // ── Message List ────────────────────────────────────────
        ListView {
            id: messageList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 2
            model: chatVM.messages
            boundsBehavior: Flickable.StopAtBounds

            // Auto-scroll to bottom on new messages
            property bool autoScroll: true

            onContentYChanged: {
                if (contentHeight - contentY - height > 100) {
                    autoScroll = false
                }
            }

            Connections {
                function onScroll_to_bottom() {
                    messageList.autoScroll = true
                    messageList.positionViewAtEnd()
                }
            }

            delegate: MessageBubble {
                width: ListView.view.width
                role: modelData.role
                content: modelData.content
                timestamp: modelData.created_at || ""
                isStreaming: modelData.streaming || false
                messageId: modelData.id || 0
            }

            // Scroll indicator
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }
        }

        // ── Input Area ──────────────────────────────────────────
        InputArea {
            id: inputArea
            Layout.fillWidth: true
            onSendMessage: function(content) {
                chatVM.send_message(content)
            }
        }
    }
}
