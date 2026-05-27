import math

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget


class TypingIndicator(QWidget):
    """Three bouncing dots that indicate the AI is thinking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(120)

    def start(self):
        self._phase = 0
        self._timer.start()
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._phase = (self._phase + 1) % 24
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dot_r = 3.5
        spacing = 10
        total_w = 3 * (dot_r * 2) + 2 * spacing
        start_x = (self.width() - total_w) / 2
        cy = self.height() / 2

        for i in range(3):
            offset = (self._phase - i * 8) % 24
            if offset < 12:
                dy = -6 * math.sin(offset / 12 * math.pi)
                scale = 1.0
            else:
                dy = 0
                scale = 0.6 + 0.4 * abs(math.cos((offset - 12) / 12 * math.pi))

            alpha = 80 + int(175 * (1 - abs(offset - 8) / 12))
            alpha = max(60, min(255, alpha))

            x = start_x + i * (dot_r * 2 + spacing) + dot_r
            y = cy + dy
            color = QColor(78, 99, 212, alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(x, y), dot_r * scale, dot_r * scale)
        p.end()
