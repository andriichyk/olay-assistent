# AI Assistant Overlay

A lightweight desktop AI assistant that lives in a hotkey-triggered overlay window. Press a shortcut, ask a question, get a streaming response — without leaving your current workflow.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- **Hotkey toggle** — show/hide the window instantly (default: `Ctrl+Space`)
- **Streaming responses** — tokens appear in real time as the model generates them
- **Screenshot attachment** — capture your screen and send it with your message (vision models)
- **Multi-provider support** — works with Anthropic, OpenAI, or any OpenAI-compatible API (Gemini, Groq, Ollama, etc.)
- **System instructions** — set a persistent personality or behavior for the assistant
- **Collapse/expand** — long responses are folded automatically with a "Show more" button
- **Copy button** — one click to copy any assistant response
- **System tray** — runs in the background, accessible from the tray icon
- **Frameless & always-on-top** — stays out of the way until you need it

---

## Installation

**Requirements:** Python 3.11+

```bash
git clone https://github.com/your-username/olay-assistent
cd olay-assistent
pip install -r requirements.txt
python main.py
```

### Dependencies

```
PyQt6
httpx
Pillow
pynput
```

---

## Configuration

On first launch, open **Settings (⚙)** and fill in:

| Field | Description |
|---|---|
| Provider | `anthropic`, `openai`, or `custom` |
| API Key | Your key from the provider's dashboard |
| Base URL | Only for `custom` — e.g. `http://localhost:11434/v1` for Ollama |
| Model | e.g. `claude-sonnet-4-20250514`, `gpt-4o`, `gemini-2.5-flash` |
| Hotkey | Key combo to toggle the window, e.g. `ctrl+space` |
| Instructions | Optional system prompt for the assistant |

Settings are saved to `~/.ai_overlay_config.json` — never committed to the repo.

### Provider quick-start

**Anthropic**
- Get key at [console.anthropic.com](https://console.anthropic.com)
- Provider: `anthropic`, Model: `claude-sonnet-4-20250514`

**Google Gemini (AI Studio)**
- Get key at [aistudio.google.com](https://aistudio.google.com)
- Provider: `custom`, Base URL: `https://generativelanguage.googleapis.com/v1beta/openai`
- Model: `gemini-2.5-flash`

**Ollama (local)**
- Provider: `custom`, Base URL: `http://localhost:11434/v1`, API Key: `ollama`
- Model: any model you have pulled, e.g. `llama3.2`

---

## Usage

| Action | How |
|---|---|
| Show / hide window | `Ctrl+Space` (or your custom hotkey) |
| Send message | `Enter` |
| New line in input | `Shift+Enter` |
| Attach screenshot | Click 📷 — window hides, screen is captured, then re-appears |
| Copy response | Click the copy icon on any assistant message |
| Clear chat | Click 🗑 in the title bar |
| Move window | Drag the title bar |

---

## Project Structure

```
├── main.py              # Entry point, system tray
├── config.py            # Load/save ~/.ai_overlay_config.json
├── worker.py            # API calls in a background QThread (Anthropic + OpenAI)
├── styles.py            # Qt stylesheet
├── icons.py             # Icon loader
└── widgets/
    ├── overlay.py       # Main window
    ├── message.py       # Chat bubble widget (streaming, collapse, copy)
    ├── settings.py      # Settings dialog
    ├── buttons.py       # Icon button component
    └── typing.py        # Animated typing indicator
```

---

## Notes

- **Linux / Wayland:** `ImageGrab` (screenshots) requires X11. On Wayland, install `scrot` and adjust `_do_grab()` in `overlay.py` to use `subprocess.run(["scrot", "/tmp/ss.png"])`.
- **Hotkey on Linux:** `pynput` may require your user to be in the `input` group: `sudo usermod -aG input $USER` (then log out and back in).
