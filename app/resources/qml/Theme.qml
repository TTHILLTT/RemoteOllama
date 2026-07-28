pragma Singleton

import QtQuick

QtObject {
    // Theme mode — toggled by settings
    property bool isDark: true

    // ── Color Palette ───────────────────────────────────────────

    // Primary accent (ChatGPT-style green)
    readonly property color primary: "#10A37F"
    readonly property color primaryHover: "#0E8C6B"
    readonly property color primaryLight: "#1AB88E"

    // Backgrounds
    property color bgPrimary: isDark ? "#1E1E2E" : "#FFFFFF"
    property color bgSecondary: isDark ? "#2D2D3F" : "#F7F7F8"
    property color bgTertiary: isDark ? "#252538" : "#ECECF1"
    property color bgHover: isDark ? "#35354A" : "#E5E5EA"

    // Chat bubbles
    property color bgBubbleUser: isDark ? "#2D2D3F" : "#F0F0F0"
    property color bgBubbleAI: isDark ? "#1E1E2E" : "#FFFFFF"

    // Text
    property color textPrimary: isDark ? "#ECECF1" : "#1A1A2E"
    property color textSecondary: isDark ? "#9B9BB3" : "#6E6E80"
    property color textMuted: isDark ? "#6E6E80" : "#A0A0B0"

    // Borders
    property color borderColor: isDark ? "#3E3E55" : "#E5E5E5"
    property color borderFocus: primary

    // Status
    readonly property color errorColor: "#EF4444"
    readonly property color successColor: "#10B981"
    readonly property color warningColor: "#F59E0B"

    // ── Typography ──────────────────────────────────────────────

    property int fontSizeXs: 11
    property int fontSizeSm: 12
    property int fontSizeMd: 14
    property int fontSizeLg: 16
    property int fontSizeXl: 18
    property int fontSizeTitle: 20

    // ── Spacing ─────────────────────────────────────────────────

    readonly property int spacingXs: 4
    readonly property int spacingSm: 8
    readonly property int spacingMd: 12
    readonly property int spacingLg: 16
    readonly property int spacingXl: 24

    // ── Dimensions ──────────────────────────────────────────────

    readonly property int sidebarWidth: 260
    readonly property int topBarHeight: 48
    readonly property int inputAreaMinHeight: 56
    readonly property int inputAreaMaxHeight: 200
    readonly property int messageAvatarSize: 32
    readonly property int borderRadius: 8
    readonly property int borderRadiusLg: 12

    // ── DPI Scaling ─────────────────────────────────────────────

    readonly property real dpiScale: Math.max(1.0, Screen.devicePixelRatio)
}
