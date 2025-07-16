import datetime
import pytesseract
from PIL import ImageGrab
import subprocess
import os
import json
import time
import pyperclip
import platform

# On Windows, import win32gui for window title
try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

def is_windows():
    return platform.system() == "Windows"

# Get active window title (cross-platform)
def get_active_window_title():
    if is_windows():
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
        except Exception as e:
            return f"Error (Win): {e}"
    else:
        try:
            script = 'tell application "System Events" to get name of (processes where frontmost is true)'
            output = subprocess.check_output(['osascript', '-e', script]).decode().strip()
            return output
        except Exception as e:
            return f"Error (Mac): {e}"

# Improved function: get_focused_text() returns the AXValue string or error message, not printing anything
def get_focused_text():
    if is_windows():
        # Just return clipboard text on Windows
        try:
            return pyperclip.paste()
        except Exception as e:
            return f"Clipboard error (Win): {e}"
    else:
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                if frontApp is "Visual Studio Code" then
                    keystroke "a" using command down
                    delay 0.2
                    keystroke "c" using command down
                    delay 0.2
                    return "CLIPBOARD"
                else
                    tell application process frontApp
                        try
                            set focusedElement to value of attribute "AXFocusedUIElement"
                            set focusedValue to value of attribute "AXValue" of focusedElement
                            return focusedValue
                        on error
                            return "Could not extract AXValue from focused element"
                        end try
                    end tell
                end if
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            output = result.stdout.strip()
            if output == "CLIPBOARD":
                time.sleep(0.3)
                clipboard_content = pyperclip.paste()
                return clipboard_content
            elif output == "":
                return "Could not extract AXValue from focused element"
            else:
                return output
        except Exception as e:
            return f"Error (Mac): {e}"

# Take screenshot
def capture_screenshot(filename):
    img = ImageGrab.grab()
    img.save(f"output/{filename}")
    return img

# Run OCR on image
def run_ocr(image):
    text = pytesseract.image_to_string(image)
    return text.strip()

## Main capture logic (unchanged)

if __name__ == "__main__":
    import json
    import time
    import pyperclip
    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            screenshot_path = f"screenshot_{timestamp}.png"
            active_window = get_active_window_title()
            # Use get_focused_text() for textbox_text
            textbox_text = get_focused_text()
            # Clipboard logic: On Windows, clipboard and focused_text are the same; on Mac, they may differ
            if is_windows():
                clipboard_content = textbox_text
            else:
                clipboard_content = pyperclip.paste()
            image = capture_screenshot(screenshot_path)
            ocr_text = run_ocr(image)
            # Delete the screenshot after OCR
            try:
                os.remove(f"output/{screenshot_path}")
            except Exception as e:
                print(f"[Warning] Failed to delete screenshot: {e}")
            import os
            # Read the VS Code live text file (cross-platform)
            vscode_text = ""
            if platform.system() == "Darwin":
                path = os.path.expanduser("~/Desktop/vscode_live_text.txt")
            elif platform.system() == "Windows":
                path = os.path.expanduser("~/Desktop/vscode_live_text.txt")
            else:
                path = "/tmp/vscode_live_text.txt"

            try:
                with open(path, "r", encoding="utf-8") as f:
                    vscode_text = f.read().strip()
            except FileNotFoundError:
                vscode_text = "VS Code text not found."

            data = {
                "timestamp": timestamp,
                "active_window": active_window,
                "focused_text": textbox_text,
                "clipboard": clipboard_content,
                "vscode_text": vscode_text,
                "ocr_text": ocr_text
            }
            with open(f"output/user_data_{timestamp}.json", "w") as f:
                json.dump(data, f, indent=2)
            with open("output/live_output.json", "w") as f:
                json.dump(data, f, indent=4)
            time.sleep(20)
    except KeyboardInterrupt:
        print("Program interrupted by user.")