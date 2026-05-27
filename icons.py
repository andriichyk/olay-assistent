import math

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QIcon, QPainterPath


def _mk_icon(draw_fn, size: int = 24, color: str = "#4e5168") -> QIcon:
    """Create a QIcon from a painter function."""
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_fn(p, QRectF(2, 2, size - 4, size - 4), QColor(color))
    p.end()
    return QIcon(px)


def _pen(p: QPainter, color: QColor, w: float = 1.8):
    pen = QPen(color, w)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)


# ── Individual icon drawing functions ─────────────────────────────────────────

def _draw_x(p: QPainter, r: QRectF, c: QColor):
    _pen(p, c, 2.0)
    m = 3
    p.drawLine(QPointF(r.x() + m, r.y() + m), QPointF(r.right() - m, r.bottom() - m))
    p.drawLine(QPointF(r.right() - m, r.y() + m), QPointF(r.x() + m, r.bottom() - m))


def _draw_gear(p: QPainter, r: QRectF, c: QColor):
    _pen(p, c, 1.7)
    cx, cy = r.center().x(), r.center().y()
    outer = min(r.width(), r.height()) / 2 - 1
    inner = outer * 0.5
    p.drawEllipse(QPointF(cx, cy), outer, outer)
    p.drawEllipse(QPointF(cx, cy), inner + 1, inner + 1)
    for i in range(8):
        a = math.radians(i * 45 - 90)
        p.drawLine(
            QPointF(cx + (outer - 0.5) * math.cos(a), cy + (outer - 0.5) * math.sin(a)),
            QPointF(cx + (inner + 1.5) * math.cos(a), cy + (inner + 1.5) * math.sin(a)),
        )


def _draw_trash(p: QPainter, r: QRectF, c: QColor):
    _pen(p, c, 1.7)
    m = 3
    p.drawLine(QPointF(r.x() + m, r.y() + m + 2), QPointF(r.right() - m, r.y() + m + 2))
    p.drawLine(QPointF(r.center().x(), r.y() + m), QPointF(r.center().x(), r.y() + m + 6))
    bx = r.x() + m + 3
    bw = r.width() - 2 * (m + 3)
    body = QRectF(bx, r.y() + m + 7, bw, r.height() - (m + 7) - m)
    path = QPainterPath()
    path.addRoundedRect(body, 3, 3)
    p.drawPath(path)
    inner_l = bx + bw * 0.32
    inner_r = bx + bw * 0.68
    top_y = body.y() + 3
    bot_y = body.bottom() - 4
    p.drawLine(QPointF(inner_l, top_y), QPointF(inner_l, bot_y))
    p.drawLine(QPointF(inner_r, top_y), QPointF(inner_r, bot_y))


def _draw_arrow_right(p: QPainter, r: QRectF, c: QColor):
    _pen(p, c, 2.0)
    mid_y = r.center().y()
    lx, rx = r.x() + 3, r.right() - 3
    p.drawLine(QPointF(lx, mid_y), QPointF(rx - 4, mid_y))
    path = QPainterPath()
    path.moveTo(rx - 2, mid_y - 5)
    path.lineTo(rx, mid_y)
    path.lineTo(rx - 2, mid_y + 5)
    p.drawPath(path)


def _draw_camera(p: QPainter, r: QRectF, c: QColor):
    _pen(p, c, 1.7)
    body = QRectF(r.x() + 2, r.y() + 5, r.width() - 4, r.height() - 8)
    path = QPainterPath()
    path.addRoundedRect(body, 4, 4)
    p.drawPath(path)
    cx, cy = body.center().x(), body.center().y()
    p.drawEllipse(QPointF(cx, cy), 5, 5)
    p.drawEllipse(QPointF(cx, cy), 2, 2)
    p.drawLine(QPointF(body.right() - 10, body.top()), QPointF(body.right() - 10, r.y() + 2))
    p.drawLine(QPointF(body.right() - 14, r.y() + 2), QPointF(body.right() - 6, r.y() + 2))


def _draw_copy(p: QPainter, r: QRectF, c: QColor):
    _pen(p, c, 1.7)
    offset = 3
    back = QRectF(r.x() + 2 + offset, r.y() + 2 + offset, r.width() - 6, r.height() - 6)
    path = QPainterPath()
    path.addRoundedRect(back, 3, 3)
    p.drawPath(path)
    front = QRectF(r.x() + 2, r.y() + 2, r.width() - 6, r.height() - 6)
    path2 = QPainterPath()
    path2.addRoundedRect(front, 3, 3)
    p.drawPath(path2)


# Lazy icon cache — QPainter/QPixmap require QApplication, so defer creation
_icon_cache: dict = {}

_ICON_REGISTRY = {
    "x":       (_draw_x, 22, "#4e5168"),
    "gear":    (_draw_gear, 22, "#4e5168"),
    "trash":   (_draw_trash, 22, "#4e5168"),
    "send":    (_draw_arrow_right, 24, "#4e63d4"),
    "camera":  (_draw_camera, 22, "#4e5168"),
    "copy":    (_draw_copy, 20, "#6b6e82"),
}


def get_icon(name: str) -> QIcon:
    if name not in _icon_cache:
        fn, size, color = _ICON_REGISTRY[name]
        _icon_cache[name] = _mk_icon(fn, size, color)
    return _icon_cache[name]
