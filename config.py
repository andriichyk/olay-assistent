import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".ai_overlay_config.json"
DEFAULTS: dict = {
    "provider":     "anthropic",
    "api_key":      "",
    "base_url":     "https://api.openai.com/v1",
    "model":        "claude-sonnet-4-20250514",
    "hotkey":       "ctrl+space",
    "instructions": "",
}


def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            return {**DEFAULTS, **json.loads(CONFIG_PATH.read_text())}
    except Exception:
        pass
    return DEFAULTS.copy()


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
