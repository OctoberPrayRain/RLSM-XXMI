pragma Singleton
import QtQuick

QtObject {
    readonly property color text: "#edf2f7"
    readonly property color muted: "#9caabd"
    readonly property color subtle: "#65768d"
    property color accent: "#91e4ce"
    readonly property color accentInk: accent.r * 0.299 + accent.g * 0.587 + accent.b * 0.114 > 0.62 ? "#102026" : "#f7f9fb"
    readonly property color accentHover: Qt.lighter(accent, 1.12)
    readonly property color accentPressed: Qt.darker(accent, 1.12)
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, 0.16)
    readonly property color accentBorder: Qt.rgba(accent.r, accent.g, accent.b, 0.52)
    readonly property color warning: "#efc58d"
    readonly property color border: "#283646"
    readonly property color surface: "#ed14202d"
    readonly property color field: "#eb101a26"
    readonly property color hover: "#293d4b"
    readonly property color selected: accentSoft
    readonly property color gradientStart: Qt.tint("#111b27", Qt.rgba(accent.r, accent.g, accent.b, 0.17))
    readonly property color gradientMiddle: Qt.tint("#101925", Qt.rgba(accent.r, accent.g, accent.b, 0.06))
    readonly property color gradientEnd: Qt.tint("#1b1d2c", Qt.rgba(accent.r, accent.g, accent.b, 0.09))
}
