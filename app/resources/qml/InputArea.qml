import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    height: inputLayout.implicitHeight + Theme.spacingMd * 2
    color: Theme.bgPrimary
    border.color: Theme.borderColor
    border.width: 1

    // Signal for QML-level send
    signal sendMessage(string content)

    RowLayout {
        id: inputLayout
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingSm

        // Text input area
        ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(
                inputField.implicitHeight + Theme.spacingSm,
                Theme.inputAreaMaxHeight
            )

            TextArea {
                id: inputField
                placeholderText: "Type a message..."
                placeholderTextColor: Theme.textMuted
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSizeMd
                wrapMode: TextArea.WrapAtWordBoundaryOrAnywhere
                background: Rectangle {
                    color: "transparent"
                }

                // Send on Enter (Shift+Enter for newline)
                Keys.onPressed: function(event) {
                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                        if (event.modifiers & Qt.ShiftModifier) {
                            // Shift+Enter: newline — default behavior
                        } else {
                            event.accepted = true
                            doSend()
                        }
                    }
                }
            }
        }

        // Stop button (visible only during streaming)
        Button {
            id: stopButton
            visible: chatVM.is_streaming
            Layout.alignment: Qt.AlignBottom
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40

            contentItem: Text {
                text: "■"
                color: "#FFFFFF"
                font.pixelSize: Theme.fontSizeLg
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.hovered ? "#DC2626" : Theme.errorColor
                radius: Theme.borderRadius
            }
            onClicked: chatVM.stop_generation()
        }

        // Send button
        Button {
            id: sendButton
            visible: !chatVM.is_streaming
            Layout.alignment: Qt.AlignBottom
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            enabled: inputField.text.trim().length > 0

            contentItem: Text {
                text: "→"
                color: parent.enabled ? "#FFFFFF" : Theme.textMuted
                font.pixelSize: Theme.fontSizeLg
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.enabled
                       ? (parent.hovered ? Theme.primaryHover : Theme.primary)
                       : Theme.bgTertiary
                radius: Theme.borderRadius
            }
            onClicked: doSend()
        }
    }

    function doSend() {
        var text = inputField.text.trim()
        if (text.length > 0) {
            sendMessage(text)
            inputField.text = ""
        }
    }
}
