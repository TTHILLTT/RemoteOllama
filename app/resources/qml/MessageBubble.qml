import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    width: ListView.view ? ListView.view.width : 400
    height: contentLayout.implicitHeight + Theme.spacingLg * 2

    property string role: "user"
    property string content: ""
    property string timestamp: ""
    property bool isStreaming: false
    property int messageId: 0

    color: "transparent"

    RowLayout {
        id: contentLayout
        anchors.fill: parent
        anchors.margins: Theme.spacingLg
        spacing: Theme.spacingMd
        // Align user messages to right, AI to left
        layoutDirection: role === "user" ? Qt.RightToLeft : Qt.LeftToRight

        // Avatar
        Rectangle {
            Layout.preferredWidth: Theme.messageAvatarSize
            Layout.preferredHeight: Theme.messageAvatarSize
            Layout.alignment: Qt.AlignTop
            radius: Theme.messageAvatarSize / 2
            color: role === "user" ? Theme.primary : Theme.bgHover

            Text {
                anchors.centerIn: parent
                text: role === "user" ? "U" : "AI"
                color: role === "user" ? "#FFFFFF" : Theme.textSecondary
                font.pixelSize: Theme.fontSizeSm
                font.bold: true
            }
        }

        // Message content container
        ColumnLayout {
            Layout.maximumWidth: parent.width * 0.75
            spacing: Theme.spacingXs

            // Role label
            Text {
                text: role === "user" ? "You" : "Assistant"
                color: Theme.textSecondary
                font.pixelSize: Theme.fontSizeSm
                font.bold: true
            }

            // Message bubble
            Rectangle {
                Layout.fillWidth: true
                implicitWidth: Math.min(messageText.implicitWidth + Theme.spacingLg * 2,
                                        root.width * 0.72)
                implicitHeight: messageText.implicitHeight + Theme.spacingLg * 2
                color: role === "user" ? Theme.bgBubbleUser : Theme.bgBubbleAI
                border.color: role === "user" ? "transparent" : Theme.borderColor
                border.width: role === "user" ? 0 : 1
                radius: Theme.borderRadiusLg

                // Markdown content
                Text {
                    id: messageText
                    anchors.fill: parent
                    anchors.margins: Theme.spacingLg
                    text: content + (isStreaming ? " ▌" : "")
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSizeMd
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                    textFormat: TextEdit.RichText  // For basic HTML rendering
                    renderType: Text.NativeRendering
                    lineHeight: 1.5

                    // Enable text selection
                    onLinkActivated: Qt.openUrlExternally(link)
                }
            }

            // Action buttons row (shown on hover)
            RowLayout {
                spacing: Theme.spacingSm
                visible: actionButtonsHover.hovered || isStreaming

                Item {
                    id: actionButtonsHover
                    Layout.fillWidth: true
                    height: visible ? 20 : 0
                }

                // Action buttons
                Button {
                    text: "📋"
                    flat: true
                    font.pixelSize: Theme.fontSizeXs
                    hoverEnabled: true
                    ToolTip.text: "Copy"
                    ToolTip.visible: hovered
                    onClicked: chatVM.copy_message(content)
                }

                Button {
                    text: "🔄"
                    flat: true
                    font.pixelSize: Theme.fontSizeXs
                    visible: role === "assistant" && !isStreaming
                    hoverEnabled: true
                    ToolTip.text: "Regenerate"
                    ToolTip.visible: hovered
                    onClicked: chatVM.regenerate()
                }

                Button {
                    text: "🗑"
                    flat: true
                    font.pixelSize: Theme.fontSizeXs
                    visible: !isStreaming
                    hoverEnabled: true
                    ToolTip.text: "Delete"
                    ToolTip.visible: hovered
                    onClicked: chatVM.delete_message(messageId)
                }
            }
        }
    }

    // Streaming cursor animation
    Timer {
        running: isStreaming
        interval: 500
        repeat: true
        onTriggered: {
            // The cursor flicker is handled by the Text animation
        }
    }
}
