from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QPushButton

from icons import get_icon


class IconButton(QPushButton):
    """A minimalist icon button."""

    def __init__(self, icon_name: str, tooltip: str = "", size: int = 32, parent=None):
        super().__init__(parent=parent)
        self.setIcon(get_icon(icon_name))
        self.setIconSize(QSize(size - 4, size - 4))
        self.setFixedSize(size, size)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
            }
            QPushButton:pressed {
                background: rgba(0,0,0,0.10);
            }
        """)
