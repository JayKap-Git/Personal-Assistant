import json
import time

import os

from typing import Dict, Any, List
import subprocess
import signal

# Import Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage

from dotenv import load_dotenv

load_dotenv()

# Google Gemini API key setup
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")



# Initialize Google Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    convert_system_message_to_human=True
)


def read_latest_user_data() -> Dict[str, Any]:
    """Read the latest user data from live_output.json"""
    try:
        with open("output/live_output.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def read_user_data_file(filename: str) -> Dict[str, Any]:
    """Read a specific user data file"""
    try:
        with open(f"output/{filename}", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_all_user_data_files() -> List[str]:
    """Get list of all user data files in output directory"""
    try:
        files = [f for f in os.listdir("output") if f.startswith("user_data_") and f.endswith(".json")]
        return sorted(files)
    except FileNotFoundError:
        return []


def analyze_user_activity_from_json(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze user data from JSON to determine what the user is doing
    Returns JSON format with activity classification
    """
    if not user_data:
        return {
            "activity": "unknown",
            "confidence": 0.0,
            "description": "No user data available",
            "timestamp": time.time()
        }

    # Extract relevant information from user data
    active_window = user_data.get("active_window", "")
    focused_text = user_data.get("focused_text", "")
    clipboard_content = user_data.get("clipboard", "")
    # vscode_text = user_data.get("vscode_text", "")
    ocr_text = user_data.get("ocr_text", "")
    timestamp = user_data.get("timestamp", "")

    # Combine all text sources for analysis
    #     combined_text = f"""
    # Active Window: {active_window}
    # Focused Text: {focused_text}
    # Clipboard: {clipboard_content}
    # VS Code Text: {vscode_text}
    # Screen OCR: {ocr_text}
    #     """.strip()
    combined_text = f"""
Active Window: {active_window}
Focused Text: {focused_text}
Clipboard: {clipboard_content}
Screen OCR: {ocr_text}
    """.strip()

    if not combined_text or combined_text.strip() == "":
        return {
            "activity": "unknown",
            "confidence": 0.0,
            "description": "No meaningful text data available",
            "timestamp": time.time()
        }

    system_prompt = """You are an AI assistant that analyzes user activity data to determine what the user is currently doing. 

    You have access to multiple data sources:
    - Active Window: The currently active application
    - Focused Text: Text from the focused element
    - Clipboard: Content in the clipboard
    - VS Code Text: Text from VS Code editor (if available)
    - Screen OCR: Text extracted from screen capture

    Analyze this data and classify the user's activity into one of these categories:
    - coding: Writing, editing, or reviewing code (Python, JavaScript, etc.)
    - researching: Reading articles, papers, documentation, or searching for information
    - browsing: General web browsing, social media, or casual internet use
    - emailing: Composing, reading, or managing emails
    - messaging: Using chat applications, messaging apps, or communication tools
    - gaming: Playing video games or game-related activities
    - watching: Watching videos, streams, or multimedia content
    - writing: Writing documents, notes, or creative content
    - designing: Working on design, graphics, or creative projects
    - working: General work activities not covered by other categories
    - unknown: Unable to determine the activity

    Consider the following patterns:
    - Coding: Look for code syntax, function definitions, imports, IDE elements
    - Messaging: Look for chat interfaces, message bubbles, contact names
    - Researching: Look for articles, documentation, search results
    - Browsing: Look for web browser elements, URLs, navigation

    Return your response in valid JSON format with these fields:
    - activity: The classified activity (string)
    - confidence: Confidence level 0.0-1.0 (float)
    - description: Brief description of what you observed (string)
    - details: Additional context or specific tools/applications detected (string)
    - data_sources: Which data sources were most useful for classification (string)
    - timestamp: Current timestamp (float)

    Example response:
    {
        "activity": "coding",
        "confidence": 0.85,
        "description": "User appears to be writing Python code in Cursor IDE",
        "details": "Detected Python imports, function definitions, and Cursor IDE interface",
        "data_sources": "VS Code text and active window",
        "timestamp": 1234567890.123
    }

    Only return valid JSON, no additional text."""

    human_prompt = f"Here's the user activity data to analyze:\n\n{combined_text}\n\nPlease analyze this data and determine what the user is doing."

    try:
        time.sleep(10)  # Add 10-second delay before LLM call
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = llm(messages)
        response_text = response.content.strip()

        # Try to parse the JSON response
        try:
            # Handle markdown-wrapped JSON responses
            if response_text.startswith("```json") and response_text.endswith("```"):
                # Extract JSON from markdown code blocks
                json_start = response_text.find("```json") + 7
                json_end = response_text.rfind("```")
                if json_start < json_end:
                    response_text = response_text[json_start:json_end].strip()
            elif response_text.startswith("```") and response_text.endswith("```"):
                # Extract JSON from generic code blocks
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                if json_start < json_end:
                    response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            # Ensure timestamp is current
            result["timestamp"] = time.time()
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "activity": "unknown",
                "confidence": 0.0,
                "description": "Failed to parse LLM response",
                "details": response_text,
                "data_sources": "LLM response parsing failed",
                "timestamp": time.time()
            }

    except Exception as e:
        return {
            "activity": "unknown",
            "confidence": 0.0,
            "description": f"Error analyzing user data: {str(e)}",
            "details": "",
            "data_sources": "Error occurred during analysis",
            "timestamp": time.time()
        }


def analyze_historical_data(num_files: int = 5) -> List[Dict[str, Any]]:
    """Analyze the most recent user data files"""
    files = get_all_user_data_files()
    if not files:
        return []

    # Get the most recent files
    recent_files = files[-num_files:] if len(files) > num_files else files
    results = []

    for filename in recent_files:
        user_data = read_user_data_file(filename)
        if user_data:
            analysis = analyze_user_activity_from_json(user_data)
            analysis["source_file"] = filename
            results.append(analysis)

    return results


def analyze_latest_activity() -> dict:
    user_data = read_latest_user_data()
    return analyze_user_activity_from_json(user_data)


def main():
    """Main function to continuously monitor and analyze user activity"""
    print("🔍 User Activity Monitor Started")
    print("Using Google Gemini LLM for activity analysis")
    print("Analyzing data from gatheruserdata.py JSON files")
    print("Press Ctrl+C to stop\n")

    # Start gatheruserdata.py as a subprocess
    gather_proc = subprocess.Popen([
        sys.executable, "gatheruserdata.py"
    ])
    print("🚀 Started gatheruserdata.py in the background (PID: {}), collecting user data...".format(gather_proc.pid))

    try:
        last_timestamp = None
        while True:
            print("📊 Reading latest user data...")
            user_data = read_latest_user_data()

            # Only analyze if new data is available
            if user_data and user_data.get("timestamp") != last_timestamp:
                last_timestamp = user_data.get("timestamp")
                print("🤖 Analyzing user activity from JSON data...")
                result = analyze_user_activity_from_json(user_data)
                # Pretty print the JSON result
                print("📊 Activity Analysis:")
                print(json.dumps(result, indent=2))
                try:
                    with open("output/prediction_output.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                except Exception as e:
                    print(f"❌ Failed to save prediction output: {e}")
                print("=" * 60)
            else:
                print("⏳ Waiting for new user data...")

            # Wait before next check
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n👋 Activity monitor stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🛑 Terminating gatheruserdata.py subprocess...")
        gather_proc.terminate()
        try:
            gather_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            gather_proc.kill()
        print("✅ gatheruserdata.py stopped.")


def analyze_single_file(filename: str):
    """Analyze a specific user data file"""
    print(f"🔍 Analyzing file: {filename}")
    user_data = read_user_data_file(filename)

    if user_data:
        result = analyze_user_activity_from_json(user_data)
        print("📊 Activity Analysis:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Could not read file: {filename}")


def analyze_recent_files(num_files: int = 5):
    """Analyze the most recent user data files"""
    print(f"🔍 Analyzing {num_files} most recent files...")
    results = analyze_historical_data(num_files)

    for result in results:
        print(f"\n📁 File: {result.get('source_file', 'Unknown')}")
        print(f"🎯 Activity: {result.get('activity', 'Unknown')}")
        print(f"📈 Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"📝 Description: {result.get('description', 'No description')}")
        print("-" * 40)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            analyze_single_file(sys.argv[2])
        elif sys.argv[1] == "--recent" and len(sys.argv) > 2:
            analyze_recent_files(int(sys.argv[2]))
        elif sys.argv[1] == "--recent":
            analyze_recent_files()
        else:
            print("Usage:")
            print("  python activity_analyzer.py                    # Monitor live data")
            print("  python activity_analyzer.py --file <filename>  # Analyze specific file")
            print("  python activity_analyzer.py --recent [num]     # Analyze recent files")
    else:
        main() 