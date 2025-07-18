#  AI Buddies System

##  Overview

AI Buddies is a privacy-first, real-time desktop assistant system powered entirely by **Google Gemini** LLMs. It senses user activity from various sources like the active window, clipboard, screen content (via OCR), and live code editor data to determine what the user is doing—and launches a corresponding assistant.

Only one UI panel is used for interacting with the system: the **Personal Assistant Buddy UI**, which consolidates chat, focus controls, and contextual productivity tools into a single PyQt5 interface.

---

##  Core Features

- **Live Context Capture**: Polls active window, clipboard, screenshots (OCR), and code editor contents every 10–20s.
- **Activity Analysis**: Uses Gemini LLM to classify user activity like `coding`, `researching`, `watching`, etc.
- **Personal Assistant Buddy**:
  - Context summarization
  - Adaptive nudges and motivation
  - Meeting scheduling
  - Focus Mode and wellness suggestions
- **Focus Automation**:
  - Auto-blocks distractions
  - Triggers based on activity intensity or time of day
- **Modular UI**: One single, tab-based floating window for interaction with chat, focus controls, and summaries.

---

##  File Structure

```
├── gatheruserdata.py          # Collects window, clipboard, OCR, and editor data
├── activity_analyzer.py       # Starts gatherer + LLM-based activity analysis
├── pa_buddy_ui.py             # PyQt5 interface for interaction with the assistant
├── run_chatbot.py             # (Optional) CLI version of the PA Buddy
├── focus_control_ui.py        # Focus logic backend (integrated with UI)
├── test_focus_automation.py   # Testing script for focus control + analysis
├── block_sites.sh             # Blocks distracting sites (e.g., YouTube, Reddit)
├── output/                    # Contains all live & historical context JSON
└── start_pa_buddy.sh          # Launches the entire system
```

---

##  Setup Instructions

### Step 1: Clone & Setup Environment
```bash
git clone <repo-url>
cd AI-Buddies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt install tesseract-ocr

# Windows: download from https://github.com/tesseract-ocr/tesseract
```

### Step 3: Add Gemini Key
Create a `.env` file with:
```
GOOGLE_API_KEY=your_key_here
```

---

##  Running the System

You can run the entire system using:
```bash
./start_pa_buddy.sh
```

Or manually:

1. Start context + activity analyzer:
```bash
python activity_analyzer.py
```

2. Start the PA Buddy UI:
```bash
python pa_buddy_ui.py
```

---

##  Activity Classification

The LLM classifies user activity into:
- `coding`
- `browsing`
- `researching`
- `emailing`
- `messaging`
- `watching`
- `writing`
- `designing`
- `gaming`
- `working`
- `idle`
- `unknown`

The result is stored in `output/prediction_output.json` and updated every 20s.

---

##  Personal Assistant Buddy UI

The PyQt5-based interface supports:
- Activity display (scrollable and styled)
- Contextual chatbot using Gemini
- Focus control toggle and break reminders
- Meeting scheduler (natural language → calendar)

---

##  Testing Focus Features

To simulate and test:
```bash
python test_focus_automation.py
```

This tests:
- Break reminders
- Night mode
- Auto-save buffer
- Focus mode toggle
- Mock coding session

---

##  Privacy and Local-Only Policy

- No data is sent to the cloud (except Gemini API calls).
- VS Code plugin writes code locally to a text file.
- Screenshot OCR, clipboard capture, and prediction are fully offline.

---

##  Future Work

- Add emotional tone detection for replies
- Long-term personalization using vector memory
- Micro-model fallback mode for edge devices
- Third-party buddy agent marketplace

---

##  References

- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/)
- [LangChain](https://python.langchain.com/)
- [PyQt](https://riverbankcomputing.com/software/pyqt/)

