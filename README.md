# Helper AI

A sleek desktop overlay tool for quick AI queries with screenshot context, voice input, and multi-monitor support.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **🎯 Quick Access Overlay** - Press `F2` (configurable) to summon a floating overlay anywhere
- **📸 Multi-Monitor Screenshot** - Capture any screen with visual selection and hover highlighting
- **🎤 Voice Input** - Push-to-talk or toggle mode with OpenAI Whisper transcription
- **💬 Session Memory** - Conversations are grouped into sessions with full history
- **⚡ Complexity Levels** - Route queries to different AI models (Low/Mid/High)
- **🔧 n8n Integration** - Connect to your own AI workflow via webhook

## 🖥️ UI Overview

<img width="621" height="195" alt="image" src="https://github.com/user-attachments/assets/14c0c3ab-2a3f-45d8-85dd-dccd94e4ca50" />

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/helper-ai.git
cd helper-ai
pip install -r requirements.txt
```

### 2. Install FFmpeg (for voice input)

- **Windows**: `winget install ffmpeg`
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 3. Configure

Edit `config.py` and set your n8n webhook URL:

```python
WEBHOOK_URL = "https://your-n8n-instance.com/webhook/your-endpoint"
```

### 4. Run

```bash
python main.py
```

Press `F2` to toggle the overlay!

## ⚙️ Settings

Click the ⚙ button to configure:

| Setting | Description |
|---------|-------------|
| Overlay Hotkey | Key to toggle overlay (default: `F2`) |
| Webhook URL | Your n8n webhook endpoint |
| Voice Mode | `toggle` or `push_to_talk` |
| Voice Hotkey | Key for voice input (default: `ctrl+shift+v`) |

## 🔗 n8n Workflow

An example workflow is included in `n8n-workflow.json`:

1. Open n8n → **Workflows** → **Import from File**
2. Select `n8n-workflow.json`
3. Configure your Google Gemini API credentials
4. Activate the workflow

### Payload Fields

| Field | Description |
|-------|-------------|
| `query` | The user's question |
| `complexity` | Low, Mid, or High |
| `sessionId` | UUID for conversation memory |
| `screenshot` | Base64 PNG (optional) |

## 📁 Project Structure

```
helper-ai/
├── main.py              # Entry point
├── overlay_app.py       # Main UI
├── config.py            # Configuration
├── settings_manager.py  # Persistent settings
├── screenshot_utils.py  # Multi-monitor capture
├── voice_utils.py       # Whisper transcription
├── n8n_client.py        # Webhook integration
└── n8n-workflow.json    # Example n8n workflow
```

## 🛠️ Requirements

- Python 3.8+
- customtkinter, Pillow, requests, keyboard, mss
- openai-whisper, sounddevice, scipy (for voice)
- FFmpeg (for voice)

## 📝 License

MIT License - feel free to use and modify!

---

**Made with ❤️ for quick AI assistance**
