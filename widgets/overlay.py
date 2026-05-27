from io import BytesIO

from PyQt6.QtCore import (
    Qt, QPoint, QTimer, QEvent, QPropertyAnimation, QEasingCurve, QSize,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QScrollArea, QPushButton, QApplication, QDialog,
)

from PIL import ImageGrab

from config import load_config, save_config
from icons import get_icon
from styles import LIGHT_CSS
from worker import APIWorker
from widgets.buttons import IconButton
from widgets.message import MessageWidget
from widgets.typing import TypingIndicator
from widgets.settings import SettingsDialog


class Overlay(QMainWindow):
    _toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config: dict = load_config()
        self.history: list = []
        self.screenshot: bytes | None = None
        self.worker: APIWorker | None = None
        self._ai_msg: MessageWidget | None = None
        self._drag_pos: QPoint | None = None
        self._listener = None
        self._fading = False

        self._toggle_signal.connect(self.toggle)

        self._build_ui()
        self._register_hotkey()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(LIGHT_CSS)
        self.resize(480, 660)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 500, 30)

        root = QWidget()
        root.setObjectName("root")
        root.setStyleSheet(
            "#root{background:#f4f5fa;border-radius:14px;border:1px solid #d8dae3;}"
        )
        self.setCentralWidget(root)

        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._build_titlebar())
        vbox.addWidget(self._build_chat(), stretch=1)
        vbox.addWidget(self._build_input())

    def _build_titlebar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(
            "background:#eaebf2;border-radius:14px 14px 0 0;border-bottom:1px solid #d8dae3;"
        )
        bar.mousePressEvent = self._drag_start
        bar.mouseMoveEvent = self._drag_move

        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 8, 0)

        title = QLabel("AI Assistant")
        title.setStyleSheet(
            "color:#4e63d4;font-weight:700;font-size:13px;background:transparent;"
        )

        btn_cfg = IconButton("gear", "Settings", 32)
        btn_clear = IconButton("trash", "Clear chat", 32)
        btn_close = IconButton("x", "Hide (hotkey to reopen)", 32)
        btn_close.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:6px;}"
            "QPushButton:hover{background:rgba(220,60,60,0.15);}"
            "QPushButton:pressed{background:rgba(220,60,60,0.25);}"
        )

        btn_cfg.clicked.connect(self._open_settings)
        btn_clear.clicked.connect(self._clear_chat)
        btn_close.clicked.connect(self._fade_out)

        h.addWidget(title)
        h.addStretch()
        for b in (btn_cfg, btn_clear, btn_close):
            h.addWidget(b)
        return bar

    def _build_chat(self) -> QScrollArea:
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")

        self.chat_box = QWidget()
        self.chat_box.setStyleSheet("background:transparent;")
        self.chat_vbox = QVBoxLayout(self.chat_box)
        self.chat_vbox.setContentsMargins(8, 10, 8, 10)
        self.chat_vbox.setSpacing(6)
        self.chat_vbox.addStretch()

        self.scroll.setWidget(self.chat_box)
        return self.scroll

    def _build_input(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet(
            "background:#eaebf2;border-radius:0 0 14px 14px;border-top:1px solid #d8dae3;"
        )
        vbox = QVBoxLayout(area)
        vbox.setContentsMargins(10, 8, 10, 10)
        vbox.setSpacing(5)

        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()

        self.ss_label = QLabel()
        self.ss_label.setStyleSheet(
            "background:rgba(47,139,58,0.08);color:#2f8b3a;font-size:11px;"
            "padding:4px 8px;border-radius:6px;"
        )
        self.ss_label.hide()

        row = QHBoxLayout()
        row.setSpacing(6)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Ask anything…  (Enter to send, Shift+Enter for newline)")
        self.input_box.setFixedHeight(68)
        self.input_box.installEventFilter(self)

        col = QVBoxLayout()
        col.setSpacing(4)

        self.btn_ss = IconButton("camera", "Capture screenshot", 36)
        self.btn_ss.clicked.connect(self._grab_screenshot)

        self.btn_send = QPushButton()
        self.btn_send.setIcon(get_icon("send"))
        self.btn_send.setIconSize(QSize(20, 20))
        self.btn_send.setObjectName("send_btn")
        self.btn_send.setFixedSize(36, 36)
        self.btn_send.setToolTip("Send (Enter)")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._send)

        col.addWidget(self.btn_ss)
        col.addWidget(self.btn_send)

        row.addWidget(self.input_box)
        row.addLayout(col)

        self.status_lbl = QLabel(f"model: {self.config.get('model', '—')}")
        self.status_lbl.setStyleSheet(
            "color:#9a9eb0;font-size:10px;padding:2px 2px 0 2px;background:transparent;"
        )

        vbox.addWidget(self.typing_indicator)
        vbox.addWidget(self.ss_label)
        vbox.addLayout(row)
        vbox.addWidget(self.status_lbl)
        return area

    # ── Hotkey ───────────────────────────────────────────────────────────────

    def _register_hotkey(self):
        hotkey_str = self.config.get("hotkey", "ctrl+space")
        try:
            from pynput import keyboard as kb

            combo = kb.HotKey.parse(self._to_pynput(hotkey_str))
            hotkey = kb.HotKey(combo, lambda: self._toggle_signal.emit())

            def _canonical(fn):
                return lambda k: fn(listener.canonical(k))

            listener = kb.Listener(
                on_press=_canonical(hotkey.press),
                on_release=_canonical(hotkey.release),
            )
            listener.start()
            self._listener = listener
            print(f"[hotkey] registered: {hotkey_str}")
        except Exception as exc:
            print(f"[hotkey] failed ({exc})")

    @staticmethod
    def _to_pynput(hk: str) -> str:
        SPECIAL = {
            "ctrl", "alt", "shift", "cmd", "super",
            "space", "tab", "esc", "enter", "backspace", "delete",
            *(f"f{i}" for i in range(1, 13)),
        }
        return "+".join(f"<{p}>" if p.lower() in SPECIAL else p for p in hk.split("+"))

    # ── Window drag ──────────────────────────────────────────────────────────

    def _drag_start(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _drag_move(self, e):
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    # ── Toggle with fade animation ───────────────────────────────────────────

    def toggle(self):
        if self._fading:
            return
        if self.isVisible():
            self._fade_out()
        else:
            self._fade_in()

    def _fade_in(self):
        if self._fading or (self.isVisible() and self.windowOpacity() > 0.9):
            return
        self._fading = True
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_box.setFocus()

        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: setattr(self, '_fading', False))
        anim.start()

    def _fade_out(self):
        self._fading = True
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(180)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._on_faded_out)
        anim.start()

    def _on_faded_out(self):
        self.hide()
        self._fading = False

    # ── Screenshot ───────────────────────────────────────────────────────────

    def _grab_screenshot(self):
        self._fade_out()
        QTimer.singleShot(300, self._do_grab)

    def _do_grab(self):
        try:
            img = ImageGrab.grab()
            buf = BytesIO()
            img.save(buf, "PNG")
            self.screenshot = buf.getvalue()
            kb_size = len(self.screenshot) // 1024
            self.ss_label.setText(f"Screenshot attached  ({kb_size} KB)")
            self.ss_label.show()
        except Exception as exc:
            self.ss_label.setText(f"Screenshot failed: {exc}")
            self.ss_label.show()
        finally:
            if not self.isVisible():
                self._fade_in()

    # ── Send ─────────────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self.input_box and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if (key_event.key() == Qt.Key.Key_Return and
                    not (key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
                self._send()
                return True
        return super().eventFilter(obj, event)

    def _send(self):
        text = self.input_box.toPlainText().strip()
        if not text or self.worker is not None:
            return
        if not self.config.get("api_key"):
            self._sys_msg("Set your API key in Settings first.")
            return

        self.input_box.clear()

        # User bubble
        bubble = self._add_bubble("user", text)
        QTimer.singleShot(5, bubble.start_fade_in)
        self.history.append({"role": "user", "content": text})

        # Grab & clear screenshot
        ss, self.screenshot = self.screenshot, None
        self.ss_label.hide()

        # AI bubble placeholder for streaming
        ai_bubble = MessageWidget("assistant")
        self.chat_vbox.insertWidget(self.chat_vbox.count() - 1, ai_bubble)
        QTimer.singleShot(5, ai_bubble.start_fade_in)
        self._ai_msg = ai_bubble
        self._scroll_bottom()

        # Typing indicator
        self.typing_indicator.start()

        # Start worker
        self.worker = APIWorker(list(self.history), ss, self.config)
        self.worker.token_received.connect(ai_bubble.stream_token)
        self.worker.token_received.connect(lambda _: self._scroll_bottom())
        self.worker.finished.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.btn_send.setEnabled(False)
        self.status_lbl.setText("thinking…")
        self.worker.start()

    def _on_done(self):
        if self._ai_msg:
            self._ai_msg.finalize()
            self.history.append({"role": "assistant", "content": self._ai_msg._full_text})
        self.typing_indicator.stop()
        self.worker = None
        self._ai_msg = None
        self.btn_send.setEnabled(True)
        self.status_lbl.setText(f"model: {self.config.get('model', '—')}")

    def _on_error(self, msg: str):
        if self._ai_msg:
            self._ai_msg.deleteLater()
        self.typing_indicator.stop()
        self._sys_msg(f"Error: {msg}")
        self.worker = None
        self._ai_msg = None
        self.btn_send.setEnabled(True)
        self.status_lbl.setText("error")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _add_bubble(self, role: str, text: str) -> MessageWidget:
        w = MessageWidget(role, text)
        self.chat_vbox.insertWidget(self.chat_vbox.count() - 1, w)
        self._scroll_bottom()
        return w

    def _sys_msg(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color:#c8821e;font-size:12px;padding:4px 12px;"
            "background:rgba(200,130,30,0.08);border-radius:8px;"
        )
        lbl.setWordWrap(True)
        self.chat_vbox.insertWidget(self.chat_vbox.count() - 1, lbl)
        self._scroll_bottom()

    def _scroll_bottom(self, *_):
        QTimer.singleShot(40, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _clear_chat(self):
        self.history.clear()
        while self.chat_vbox.count() > 1:
            item = self.chat_vbox.takeAt(0)
            if w := item.widget():
                w.deleteLater()

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                old_hk = self.config.get("hotkey")
                self.config = dlg.collect(self.config)
                save_config(self.config)
                self.status_lbl.setText(f"model: {self.config.get('model', '—')}")
                if old_hk != self.config.get("hotkey"):
                    try:
                        if self._listener:
                            self._listener.stop()
                    except Exception:
                        pass
                    self._register_hotkey()
            except Exception as exc:
                print(f"[settings] save error: {exc}")
                import traceback
                traceback.print_exc()