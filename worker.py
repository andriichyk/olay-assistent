import json
import base64

import httpx

from PyQt6.QtCore import QThread, pyqtSignal


class APIWorker(QThread):
    token_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, messages: list, screenshot: bytes | None, config: dict):
        super().__init__()
        self.messages = messages
        self.screenshot = screenshot
        self.config = config

    def run(self):
        try:
            instructions = self.config.get("instructions", "").strip()
            if self.config["provider"] == "anthropic":
                self._call_anthropic(instructions)
            else:
                self._call_openai_compat(instructions)
            self.finished.emit()
        except Exception as exc:
            self.error.emit(str(exc))

    def _call_anthropic(self, instructions: str):
        messages = list(self.messages)
        if self.screenshot:
            b64 = base64.standard_b64encode(self.screenshot).decode()
            last = messages[-1]
            messages[-1] = {
                "role": last["role"],
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                    {"type": "text", "text": last["content"]},
                ],
            }

        body = {
            "model":      self.config["model"],
            "max_tokens": 2048,
            "messages":   messages,
            "stream":     True,
        }
        if instructions:
            body["system"] = instructions

        with httpx.Client(timeout=90) as client:
            with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":         self.config["api_key"],
                    "anthropic-version": "2023-06-01",
                    "content-type":      "application/json",
                },
                json=body,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        try:
                            obj = json.loads(line[6:])
                            if obj.get("type") == "content_block_delta":
                                text = obj["delta"].get("text", "")
                                if text:
                                    self.token_received.emit(text)
                        except Exception:
                            pass

    def _call_openai_compat(self, instructions: str):
        messages = list(self.messages)
        if instructions:
            messages.insert(0, {"role": "system", "content": instructions})

        if self.screenshot:
            b64 = base64.standard_b64encode(self.screenshot).decode()
            last = messages[-1]
            messages[-1] = {
                "role": last["role"],
                "content": [
                    {"type": "text", "text": last["content"]},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }

        url = self.config["base_url"].rstrip("/") + "/chat/completions"
        with httpx.Client(timeout=90) as client:
            with client.stream(
                "POST", url,
                headers={
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":      self.config["model"],
                    "messages":   messages,
                    "stream":     True,
                    "max_tokens": 2048,
                },
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            text = obj["choices"][0]["delta"].get("content", "")
                            if text:
                                self.token_received.emit(text)
                        except Exception:
                            pass
