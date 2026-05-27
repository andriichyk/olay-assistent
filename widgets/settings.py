from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QComboBox, QLineEdit,
    QTextEdit, QPushButton,
)

from styles import LIGHT_CSS


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self.setStyleSheet(LIGHT_CSS)

        form = QFormLayout(self)
        form.setSpacing(10)
        form.setContentsMargins(20, 18, 20, 18)

        self.provider = QComboBox()
        self.provider.addItems(["anthropic", "openai", "custom"])
        self.provider.setCurrentText(config.get("provider", "anthropic"))
        self.provider.currentTextChanged.connect(self._sync)

        self.api_key = QLineEdit(config.get("api_key", ""))
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("sk-...")

        self.base_url = QLineEdit(config.get("base_url", ""))
        self.base_url.setPlaceholderText("https://your-api/v1")

        self.model = QLineEdit(config.get("model", ""))
        self.model.setPlaceholderText("gpt-4o / claude-sonnet-4-20250514")

        self.hotkey = QLineEdit(config.get("hotkey", "ctrl+space"))
        self.hotkey.setPlaceholderText("ctrl+space  or  alt+a")

        self.instructions = QTextEdit()
        self.instructions.setPlaceholderText(
            "System instructions for AI — e.g.:\n"
            "«You are a helpful assistant. Answer in Russian, be concise.»"
        )
        self.instructions.setFixedHeight(80)
        try:
            self.instructions.setPlainText(config.get("instructions", ""))
        except Exception:
            self.instructions.setPlainText("")

        form.addRow("Provider",     self.provider)
        form.addRow("API Key",      self.api_key)
        form.addRow("Base URL",     self.base_url)
        form.addRow("Model",        self.model)
        form.addRow("Hotkey",       self.hotkey)
        form.addRow("Instructions", self.instructions)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        ok = QPushButton("Save")
        ok.setObjectName("send_btn")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        form.addRow(btns)

        self._sync(self.provider.currentText())

    def _sync(self, provider: str):
        self.base_url.setEnabled(provider == "custom")
        if provider == "openai" and not self.base_url.text():
            self.base_url.setText("https://api.openai.com/v1")

    def collect(self, base: dict) -> dict:
        return {
            **base,
            "provider":     self.provider.currentText(),
            "api_key":      self.api_key.text().strip(),
            "base_url":     self.base_url.text().strip(),
            "model":        self.model.text().strip(),
            "hotkey":       self.hotkey.text().strip(),
            "instructions": self.instructions.toPlainText().strip(),
        }
