# AI-Buddy Project Index

## Project Overview
AI-Buddy is a comprehensive AI-powered personal assistant system that includes chatbot functionality, focus automation, activity analysis, and GUI interfaces.

## Core Python Files

### Main Application Files
- **`run_chatbot.py`** - Main entry point for running the chatbot buddy
- **`pa_buddy_ui.py`** - PyQt5-based GUI for the personal assistant buddy
- **`focus_control_ui.py`** - PyQt5-based GUI for focus automation controls
- **`activity_analyzer.py`** - AI-powered activity analysis using Google Gemini
- **`gatheruserdata.py`** - Data collection module for user activity monitoring
- **`test_focus_automation.py`** - Test suite for focus automation functionality

### Buddy Modules (`buddies/`)
- **`chatbot_buddy.py`** - Core chatbot implementation with Google Gemini
- **`focus_automation.py`** - Focus automation and productivity tools
- **`personal_assistant.py`** - Main personal assistant orchestrator

### Configuration Files
- **`requirements.txt`** - Python dependencies (updated with all project dependencies)
- **`block_sites.sh`** - Shell script for website blocking functionality

## VS Code Extension (`text/`)
A VS Code extension for text extraction functionality:
- **`package.json`** - Extension manifest and dependencies
- **`package-lock.json`** - Locked dependency versions
- **`tsconfig.json`** - TypeScript configuration
- **`eslint.config.mjs`** - ESLint configuration
- **`src/extension.ts`** - Main extension source code
- **`text-extractor-0.0.1.vsix`** - Compiled VS Code extension
- **`CHANGELOG.md`** - Extension changelog
- **`README.md`** - Extension documentation
- **`vsc-extension-quickstart.md`** - Quick start guide

### VS Code Configuration (`text/.vscode/`)
- **`extensions.json`** - Recommended extensions
- **`launch.json`** - Debug configuration
- **`settings.json`** - Workspace settings
- **`tasks.json`** - Build tasks

## Dependencies

### Core AI/ML Libraries
- `langchain==0.1.0` - LangChain framework for AI applications
- `langchain_google_genai==0.0.6` - Google Gemini integration for LangChain
- `google-generativeai==0.3.2` - Google Generative AI SDK

### Computer Vision and Image Processing
- `opencv-python==4.8.1.78` - OpenCV for computer vision
- `pytesseract==0.3.10` - OCR (Optical Character Recognition)
- `Pillow==10.1.0` - Python Imaging Library
- `numpy>=1.26.0` - Numerical computing library

### System and GUI
- `PyQt5>=5.15.0` - GUI framework for desktop applications
- `pyperclip==1.8.2` - Cross-platform clipboard operations
- `mss==9.0.1` - Screenshot capture library

### Environment and Utilities
- `python-dotenv>=1.0.0` - Environment variable management

### Platform-Specific
- `pywin32==306` - Windows-specific utilities (Windows only)

## Project Structure
```
AI-Buddy/
├── buddies/                    # Core AI modules
│   ├── chatbot_buddy.py       # Chatbot implementation
│   ├── focus_automation.py    # Focus automation tools
│   └── personal_assistant.py  # Main assistant orchestrator
├── text/                      # VS Code extension
│   ├── src/
│   │   └── extension.ts       # Extension source code
│   ├── .vscode/              # VS Code configuration
│   └── *.json, *.md          # Extension metadata
├── output/                    # Data output directory
├── venv/                      # Python virtual environment
├── *.py                       # Main application files
├── requirements.txt           # Python dependencies
└── PROJECT_INDEX.md          # This file
```

## Key Features
1. **AI-Powered Chatbot** - Google Gemini integration for intelligent conversations
2. **Focus Automation** - Productivity tools and website blocking
3. **Activity Analysis** - AI-powered analysis of user activity patterns
4. **GUI Interfaces** - PyQt5-based desktop applications
5. **VS Code Extension** - Text extraction functionality
6. **Data Collection** - Comprehensive user activity monitoring

## Setup Instructions
1. Create virtual environment: `python3 -m venv venv`
2. Activate environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables (Google API key)
5. Run applications as needed

## Development Notes
- All Python files are properly indexed and dependencies are documented
- VS Code extension is self-contained in the `text/` directory
- Cross-platform compatibility (Windows-specific dependencies handled)
- Comprehensive dependency management with version pinning 