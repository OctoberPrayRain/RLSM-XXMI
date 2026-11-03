import QtQuick
import QtQuick.Shapes
import ".." as App

Item {
    id: icon
    property string name: "grid"
    property color color: App.Theme.text
    implicitWidth: 20
    implicitHeight: 20
    readonly property var paths: ({
        grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
        settings: "M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6",
        image: "M4 3h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z M3 17l6-6 4 4 3-3 5 5 M15 7h.01",
        plus: "M12 5v14 M5 12h14",
        refresh: "M20 10a8 8 0 0 0-14-5L3 8 M3 3v5h5 M4 14a8 8 0 0 0 14 5l3-3 M21 21v-5h-5",
        folder: "M3 7V5a1 1 0 0 1 1-1h5l3 3h8a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7z",
        search: "M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0 M15 15l6 6",
        down: "M6 9l6 6 6-6",
        play: "M8 4l12 8-12 8z",
        check: "M5 12l4 4L19 6",
        close: "M6 6l12 12 M18 6L6 18",
        trash: "M4 7h16 M9 7V4h6v3 M7 7l1 14h8l1-14 M10 11v6 M14 11v6",
        upload: "M12 16V3 M7 8l5-5 5 5 M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5",
        keyboard: "M3 5h18v14H3z M6 9h1 M11 9h1 M16 9h1 M6 12h1 M11 12h1 M16 12h1 M8 16h8",
        arrow: "M5 12h14 M13 6l6 6-6 6",
        sort: "M4 6h16 M4 12h11 M4 18h6",
        game: "M7 7h10c2 0 3 2 4 7l1 4c0 2-2 3-4 1l-3-3H9l-3 3c-2 2-4 1-4-1l1-4c1-5 2-7 4-7z M6 10v5 M3.5 12.5h5 M16 11h.01 M19 14h.01",
        info: "M12 16v-5 M12 7h.01 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0"
    })
    Shape {
        width: 24
        height: 24
        scale: Math.min(icon.width, icon.height) / 24
        transformOrigin: Item.TopLeft
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: 1.7
            strokeColor: icon.color
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: icon.paths[icon.name] || icon.paths.info }
        }
    }
}
