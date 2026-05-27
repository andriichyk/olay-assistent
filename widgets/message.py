from PyQt6.QtCore import Qt, QEvent, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QApplication,
    QGraphicsOpacityEffect, QAbstractScrollArea, QSizePolicy, QPushButton,
)

from widgets.buttons import IconButton

COLLAPSE_THRESHOLD = 180   # px — messages taller than this get a Show more button


class MessageWidget(QFrame):
    """Chat message bubble with streaming, collapse/expand & copy support."""

    def __init__(self, role: str, text: str = ""):
        super().__init__()
        self.role = role
        self._full_text = text
        self._effect = None
        self._content_height = 0      # real document height in px
        self._is_collapsed = False    # collapse state (only after finalize)
        self._collapsible = False     # becomes True if content exceeds threshold

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        author = QLabel("You" if role == "user" else "Assistant")
        author.setStyleSheet(
            "color:#4a6cf7;font-weight:600;font-size:11px;"
            if role == "user"
            else "color:#2f8b3a;font-weight:600;font-size:11px;"
        )
        author.setSizePolicy(
            author.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        header.addWidget(author)
        header.addStretch()

        if role == "assistant":
            self._btn_copy = IconButton("copy", "Copy response", 28)
            self._btn_copy.clicked.connect(self._copy)
            header.addWidget(self._btn_copy)
        else:
            self._btn_copy = None

        # ── Display ─────────────────────────────────────────────────────────
        self.display = QTextBrowser()
        self.display.setReadOnly(True)
        self.display.setOpenExternalLinks(True)
        self.display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.display.setMinimumHeight(0)
        self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.display.setStyleSheet(
            "QTextBrowser{background:transparent;border:none;color:#1d1d2c;font-size:13px;}"
        )
        self.display.installEventFilter(self)
        self.display.viewport().installEventFilter(self)
        self.display.document().contentsChanged.connect(self._update_height)

        # ── Expand / Collapse button ─────────────────────────────────────────
        self._btn_expand = QPushButton("Show more ▾")
        self._btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_expand.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #4a6cf7;
                font-size: 11px;
                font-weight: 600;
                padding: 0;
                text-align: left;
            }
            QPushButton:hover { color: #2f4fc0; }
        """)
        self._btn_expand.hide()
        self._btn_expand.clicked.connect(self._toggle_expand)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        bg = "#dbe4ff" if role == "user" else "#e9eaf1"
        border = "#c4d0ff" if role == "user" else "#d8dae3"
        self.setStyleSheet(
            f"QFrame{{background:{bg};border-radius:10px;border:1px solid {border};}}"
        )

        if text:
            self.display.setMarkdown(text)

        layout.addLayout(header)
        layout.addWidget(self.display)
        layout.addWidget(self._btn_expand)

    # ── Events ───────────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self.display.viewport() and event.type() == QEvent.Type.Wheel:
            self._forward_wheel(event)
            return True
        if obj is self.display and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._update_height)
            return False
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_height()

    def _forward_wheel(self, event):
        p = self.parent()
        while p:
            if isinstance(p, QAbstractScrollArea):
                p.verticalScrollBar().wheelEvent(event)
                return
            p = p.parent()

    # ── Height logic ─────────────────────────────────────────────────────────

    def _calc_doc_height(self) -> int:
        """Return true document height in pixels for current width."""
        w = self.display.viewport().width()
        if w < 20:
            p = self.parent()
            w = (p.width() - 40) if p and p.width() > 40 else 0
        if w < 20:
            return 0
        doc = self.display.document()
        doc.setTextWidth(w)
        # documentMargin is added top+bottom by Qt — include it to avoid clipping
        margin = int(doc.documentMargin())
        return int(doc.size().height()) + margin

    def _update_height(self, *_):
        h = self._calc_doc_height()
        if h == 0:
            return
        self._content_height = h

        if self._collapsible and self._is_collapsed:
            self.display.setFixedHeight(COLLAPSE_THRESHOLD)
        else:
            self.display.setFixedHeight(h)

        self.updateGeometry()

    # ── Streaming ────────────────────────────────────────────────────────────

    def stream_token(self, token: str):
        self._full_text += token
        cursor = self.display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)

    def finalize(self):
        """Called once streaming is done — render markdown & maybe collapse."""
        self.display.setMarkdown(self._full_text)
        # give Qt one event loop cycle to compute the layout
        QTimer.singleShot(0, self._apply_collapse)

    def _apply_collapse(self):
        h = self._calc_doc_height()
        if h == 0:
            return
        self._content_height = h
        if h > COLLAPSE_THRESHOLD:
            self._collapsible = True
            self._is_collapsed = True
            self.display.setFixedHeight(COLLAPSE_THRESHOLD)
            self._btn_expand.setText("Show more ▾")
            self._btn_expand.show()
        else:
            self.display.setFixedHeight(h)
        self.updateGeometry()

    def _toggle_expand(self):
        self._is_collapsed = not self._is_collapsed
        if self._is_collapsed:
            self.display.setFixedHeight(COLLAPSE_THRESHOLD)
            self._btn_expand.setText("Show more ▾")
        else:
            self.display.setFixedHeight(self._content_height)
            self._btn_expand.setText("Show less ▴")
        self.updateGeometry()

    # ── Animations ───────────────────────────────────────────────────────────

    def start_fade_in(self):
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

    # ── Copy ─────────────────────────────────────────────────────────────────

    def _copy(self):
        QApplication.clipboard().setText(self._full_text)
        if self._btn_copy:
            self._btn_copy.setStyleSheet("""
                QPushButton {
                    background: rgba(47,139,58,0.12);
                    border: none;
                    border-radius: 4px;
                }
            """)
            QTimer.singleShot(800, self._reset_copy_style)

    def _reset_copy_style(self):
        if self._btn_copy:
            self._btn_copy.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover { background: rgba(0,0,0,0.05); }
            """)