
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
load_dotenv()
import os
import time
import json
import re
import datetime
from subprocess import run
import threading
import tkinter as tk
from tkinter import messagebox
from buddies.chatbot_buddy import ChatbotBuddy
from buddies.focus_automation import FocusAutomation
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

from activity_analyzer import analyze_latest_activity


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7
)



def build_pa_prompt(activity, text, window, ocrtxt, clipboard):
    common_context = (
        f"📝 Main text:\n{text}\n\n"
        f"🪟 Active window:\n{window}\n\n"
        f"🔍 OCR:\n{ocrtxt}\n\n"
        #f"📋 Clipboard:\n{clipboard}\n\n"
    )

    if activity == "researching":
        task = "Read the content and highlight the key points the user is likely reading or focusing on. Speak in first person, like you're talking *to the user*. Avoid saying 'The user'."
    elif activity == "messaging":
        task = "Suggest how the user can rephrase their message better. Speak in a casual tone and talk to the user directly."
    elif activity == "emailing":
        task = "Help the user improve their email's clarity and tone. Speak in first person, addressing the user."
    elif activity == "writing":
        task = "Suggest better ways to express the current content. Be friendly and direct."
    elif activity == "designing":
        task = "Extract creative ideas from the screen and offer suggestions. Keep it casual and creative."
    elif activity == "browsing":
        task = "If any content is meaningful, summarize it. Speak in a buddy tone directly to the user."
    elif activity == "watching":
        task = "Try to figure out what the user is watching and mention anything interesting or relevant."
    elif activity == "working":
        task = "Offer insights into what the user might be doing and suggest the next step casually."
    else:
        task = "Summarize what the user seems to be reading or writing. Be brief and speak in first person to the user."

    prompt = (
        "You're a helpful personal assistant buddy. Based on the following context, respond as if you're directly talking to the user.\n\n"
        + common_context +
        "🎯 Task:\n" + task + "\n\n"
        "Keep your response short — just 3–5 lines. Be clear, casual, and avoid repeating the context."
    )

    return prompt

class PersonalAssistantBuddy:
    def __init__(self):
        self.last_event = None
        self.last_user_care = None
        self.chatbot = ChatbotBuddy()
        self.focus_automation = FocusAutomation(self)

    def start_chatbot(self):
        """Start the chatbot buddy"""
        self.chatbot.start_monitoring()
        print("🤖 Chatbot Buddy integrated with Personal Assistant!")

    def stop_chatbot(self):
        """Stop the chatbot buddy"""
        self.chatbot.stop_monitoring()

    def tell_joke(self):
        """Tell a joke via chatbot"""
        return self.chatbot.tell_joke()

    def chat_with_user(self, message):
        """Chat with user via activity-aware chatbot, and create a note in Notes app if requested"""
        # Check for note creation command
        note_match = None
        note_patterns = [
            r"^note[:\s]+(.+)",
            r"^make a note[:\s]+(.+)",
            r"^add note[:\s]+(.+)",
            r"remember this[:\s]+(.+)",
        ]
        for pat in note_patterns:
            m = re.match(pat, message.strip(), re.IGNORECASE)
            if m:
                note_match = m.group(1).strip()
                break
        if note_match:
            # Create note in Notes app using AppleScript
            note_content = note_match.replace('"', "'")  # Avoid breaking AppleScript
            applescript = f'''
tell application "Notes"
    activate
    make new note at folder "Notes" with properties {{name:"Note from PA Buddy", body:"{note_content}"}}
end tell
'''
            try:
                result = run(["osascript", "-e", applescript], capture_output=True, text=True)
                if result.returncode == 0:
                    return f"📝 Noted! I've added this to your Notes app: '{note_content}'"
                else:
                    return f"❌ Sorry, I couldn't create the note. Error: {result.stderr}"
            except Exception as e:
                return f"❌ Sorry, I couldn't create the note. Error: {e}"
        # Otherwise, normal chatbot response
        return self.chatbot.respond_to_user(message)

    def get_chatbot_status(self):
        """Get chatbot status"""
        return self.chatbot.get_status()

    def reset_chatbot_session(self):
        """Reset chatbot work session"""
        self.chatbot.reset_work_session()

    def handle_custom_prompt(self, prompt, sys_info):
        try:
            # Append user prompt
            # pa_messages.append(f"🧑 You: {prompt}")

            # Get message history (last 10)
            # history = "\n".join([msg for msg in list(pa_messages)[-10:]])

            # System context
            code = sys_info.get("focused_text", "")
            window = sys_info.get("active_window", "")
            clipboard = sys_info.get("clipboard", "")
            ocrtxt = sys_info.get("ocr_text", "")

            system_context = (
                f"🧠 System Context:\n"
                f"• Focused Text:\n{code}\n\n"
                f"• Active Window:\n{window}\n\n"
                f"• Clipboard:\n{clipboard}\n\n"
                f"• OCR Text:\n{ocrtxt}\n"
            )

            full_prompt = (
                f"{system_context}\n"
                # f"💬 Recent Conversation:\n{history}\n\n"
                f"🧑 User's New Prompt:\n{prompt}\n\n"
                f"👉 Please respond helpfully like a chill, friendly assistant buddy. Be short, clear, and relevant."
            )

            time.sleep(10)  # Add 10-second delay before LLM call
            response = self.llm.invoke([HumanMessage(content=full_prompt)])
            # pa_messages.append(f"🤖 PA Buddy: {response.content.strip()}")

        except Exception as e:
            print(f"❌ Gemini API error (PA Buddy): {e}")

    def summarize_contextually(self, sys_info, activity):
        print(f"🧠 [PA Buddy] summarize_contextually triggered for activity: {activity}")

        prompt = (
            "Hey buddy! Based on what I'm reading right now, can you help me out?\n\n"
            "👉 Just give me a **quick, chill summary** of the key stuff — like the main ideas, historical events, or cool facts.\n"
            "Skip the obvious stuff I can already see on the screen. Talk to me like a friend helping me revise.\n\n"
            f"📚 Here's what's on my screen:\n\n"
            f"🪟 Active Window: {sys_info.get('active_window')}\n\n"
            f"📋 Clipboard: {sys_info.get('clipboard')}\n\n"
            f"🖥 OCR Snapshot: {sys_info.get('ocr_text')}\n\n"
        )

        try:
            time.sleep(10)  # Add 10-second delay before LLM call
            response = llm.invoke([HumanMessage(content=prompt)])
            # from shared_queue import pa_messages
            if response and response.content:
                print("💬 [PA Buddy] Response generated")
                # pa_messages.append(f"🤖 PA Buddy: {response.content.strip()}")
            else:
                print("⚠️ [PA Buddy] No response content.")
        except Exception as e:
            print(f"❌ [PA Buddy] Gemini API error: {e}")

    def extract_event(self, text):
        """Detect meeting/event info from text with enhanced messaging app detection."""
        # Enhanced patterns for messaging apps and email
        messaging_patterns = [
            # WhatsApp/Telegram style patterns - capture more context
            r"(meet(?:ing)?|call|appointment|catch up|sync|discuss)[^\n]*?(tomorrow|today|\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2}|\d{1,2}/\d{1,2})[^\n]*?(?:to|for|about|discuss)?[^\n]*?(\w+)?",
            # Email style patterns
            r"(schedule|book|arrange|set up|plan)[^\n]*?(meet(?:ing)?|call|appointment)[^\n]*?(tomorrow|today|\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2})",
            # Time-based patterns with context
            r"(\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2})[^\n]*?(meet(?:ing)?|call|discuss|sync)[^\n]*?(?:to|for|about)?[^\n]*?(\w+)?",
            # Date-based patterns with context
            r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)[^\n]*?(meet(?:ing)?|call|discuss)[^\n]*?(?:at|on)?[^\n]*?(\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2})?",
            # Simple patterns for basic detection
            r"(meet(?:ing)?|call|appointment)[^\n]*?(tomorrow|today|\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2})",
        ]
        
        for pattern in messaging_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Return the full matched text for better context
                return match.group(0).strip()
        return None

    def detect_messaging_context(self, sys_info):
        """Detect if user is in a messaging context (WhatsApp, email, etc.)"""
        active_window = sys_info.get("active_window", "").lower()
        clipboard = sys_info.get("clipboard", "").lower()
        ocr_text = sys_info.get("ocr_text", "").lower()
        
        # Check for messaging apps
        messaging_apps = ["whatsapp", "telegram", "slack", "discord", "teams", "zoom", "mail", "outlook", "gmail"]
        is_messaging = any(app in active_window for app in messaging_apps)
        
        # Check for messaging indicators in OCR
        messaging_indicators = ["chat", "message", "conversation", "contact", "group", "channel"]
        has_messaging_ui = any(indicator in ocr_text for indicator in messaging_indicators)
        
        return is_messaging or has_messaging_ui

    def detect_meeting_in_conversation(self, sys_info):
        """Enhanced meeting detection specifically for messaging contexts"""
        if not self.detect_messaging_context(sys_info):
            return None
            
        # Combine all text sources
        text_sources = [
            sys_info.get("clipboard", ""),
            sys_info.get("focused_text", ""),
            sys_info.get("ocr_text", "")
        ]
        
        combined_text = " ".join(text_sources).lower()
        
        # Enhanced meeting keywords
        meeting_keywords = [
            "meet", "meeting", "call", "appointment", "sync", "discuss", "catch up",
            "schedule", "book", "arrange", "set up", "plan", "coordinate"
        ]
        
        # Time/date keywords
        time_keywords = [
            "tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", 
            "friday", "saturday", "sunday", "am", "pm", "morning", "afternoon", "evening"
        ]
        
        # Check if both meeting and time keywords are present
        has_meeting_keyword = any(keyword in combined_text for keyword in meeting_keywords)
        has_time_keyword = any(keyword in combined_text for keyword in time_keywords)
        
        if has_meeting_keyword and has_time_keyword:
            # Extract the meeting context - try to get the full sentence or phrase
            meeting_context = self.extract_full_meeting_context(combined_text)
            if meeting_context:
                return meeting_context
            else:
                # Fallback to the original extraction
                return self.extract_event(combined_text)
        
        return None

    def extract_full_meeting_context(self, text):
        """Extract the full meeting context from text"""
        # Look for complete meeting phrases
        meeting_patterns = [
            # Full meeting phrases
            r"[^.]*(meet(?:ing)?|call|appointment|sync|discuss)[^.]*(tomorrow|today|\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2})[^.]*",
            # Time-based phrases
            r"[^.]*(\d{1,2} ?(?:am|pm)|\d{1,2}:\d{2})[^.]*(meet(?:ing)?|call|discuss|sync)[^.]*",
            # Date-based phrases
            r"[^.]*(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)[^.]*(meet(?:ing)?|call|discuss)[^.]*",
        ]
        
        for pattern in meeting_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None

    def monitor_activity(self):
        """Continuously monitor activity_analyzer output and detect actionable events and user care needs."""
        print("[PA Buddy] Monitoring user activity for actionable events and user care...")
        while True:
            try:
                # Read live output directly
                live_data = self.read_live_output()
                if live_data:
                    # Check for meeting in messaging context
                    meeting_event = self.detect_meeting_in_conversation(live_data)
                    if meeting_event and meeting_event != self.last_event:
                        print(f"[PA Buddy] Detected meeting in messaging context: {meeting_event}")
                        self.last_event = meeting_event
                        self.prompt_schedule(meeting_event)
                
                # Also check activity analyzer output
                activity = analyze_latest_activity()
                description = activity.get("description", "")
                details = activity.get("details", "")
                # Detect meeting/event in description or details
                event = self.extract_event(description + " " + details)
                if event and event != self.last_event:
                    print(f"[PA Buddy] Detected event: {event}")
                    self.last_event = event
                    self.prompt_schedule(event)
                # Proactive user care
                user_care_action = self.detect_user_care()
                if user_care_action and user_care_action != self.last_user_care:
                    print(f"[PA Buddy] Proactive care: {user_care_action}")
                    self.last_user_care = user_care_action
                    self.prompt_user_care(user_care_action)
            except Exception as e:
                print(f"[PA Buddy] Error reading activity: {e}")
            time.sleep(10)

    def prompt_schedule(self, event):
        print(f"[PA Buddy] Would you like to schedule this event? -> {event}")
        # CLI prompt
        answer = input("Type 'yes' to schedule, anything else to skip: ").strip().lower()
        if answer == "yes":
            self.schedule_event_cli(event)
        else:
            print("[PA Buddy] Skipped scheduling.")
        # UI prompt (in parallel)
        self.show_event_ui(event)

    def generate_calendar_script(self, event_text):
        """Use LLM to generate AppleScript for calendar event based on detected text."""
        try:
            # Enhanced prompt for better meeting parsing
            prompt = f"""
You are an AppleScript expert. Generate a working AppleScript to schedule a calendar event.

Event text: "{event_text}"

Requirements:
- Use ONLY the "Home" calendar
- Parse the meeting details intelligently from the text
- Extract date, time, and meeting purpose
- If date is "tomorrow", calculate the actual date
- If time is "8 pm", convert to 24-hour format (20:00)
- Set both start and end date (1 hour duration if not specified)
- Use a descriptive summary based on the meeting purpose
- Return ONLY AppleScript code, no explanations

Example parsing:
- "meet tomorrow at 8 pm to discuss LLMS" → Date: tomorrow, Time: 8 PM, Summary: "LLMS Discussion"
- "call at 10am" → Date: today, Time: 10 AM, Summary: "Call"
- "sync on monday 2pm" → Date: next monday, Time: 2 PM, Summary: "Sync Meeting"

AppleScript format:
tell application "Calendar"
  tell calendar "Home"
    set startDate to date "22 July, 2025 2:00 PM"
    set endDate to date "22 July, 2025 3:00 PM"
    make new event at end with properties {{summary:"Meeting Summary", start date:startDate, end date:endDate}}
  end tell
  activate
end tell

Parse this event text and generate the appropriate AppleScript.
"""
            
            # Get LLM response
            response = llm.invoke([HumanMessage(content=prompt)])
            if response and response.content:
                script = response.content.strip()
                
                # Clean up the script
                script = self.clean_applescript(script)
                
                # Validate the script
                if self.validate_applescript(script):
                    print(f"[PA Buddy] Generated valid AppleScript for: {event_text}")
                    return script
                else:
                    print(f"[PA Buddy] Generated script failed validation, using fallback")
                    return self.simple_event_script(event_text)
            else:
                print("[PA Buddy] LLM failed to generate script, using fallback")
                return self.simple_event_script(event_text)
                
        except Exception as e:
            print(f"[PA Buddy] Error in script generation: {e}, using fallback")
            return self.simple_event_script(event_text)

    def parse_meeting_details(self, event_text):
        """Parse meeting details from text for better calendar creation"""
        
        # Convert to lowercase for easier parsing
        text = event_text.lower()
        
        # Extract time with improved patterns
        time_patterns = [
            r"(\d{1,2}):(\d{2})\s*(am|pm)?",
            r"(\d{1,2})\s*(am|pm)",
            r"(\d{1,2})\s*pm",
            r"(\d{1,2})\s*am"
        ]
        
        time_str = None
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:  # HH:MM AM/PM
                    hour, minute, ampm = match.groups()
                    hour = int(hour)
                    if ampm and ampm.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif ampm and ampm.lower() == 'am' and hour == 12:
                        hour = 0
                    time_str = f"{hour:02d}:{minute}"
                elif len(match.groups()) == 2:  # HH AM/PM
                    hour, ampm = match.groups()
                    hour = int(hour)
                    if ampm.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif ampm.lower() == 'am' and hour == 12:
                        hour = 0
                    time_str = f"{hour:02d}:00"
                break
        
        # If no time found, try to extract from the full text more broadly
        if not time_str:
            # Look for time patterns in the full text
            time_matches = re.findall(r'(\d{1,2})\s*(am|pm)', text, re.IGNORECASE)
            if time_matches:
                hour, ampm = time_matches[0]
                hour = int(hour)
                if ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif ampm.lower() == 'am' and hour == 12:
                    hour = 0
                time_str = f"{hour:02d}:00"
        
        # Extract date
        today = datetime.datetime.now()
        date_str = None
        
        if "tomorrow" in text:
            tomorrow = today + datetime.timedelta(days=1)
            date_str = tomorrow.strftime("%d %B, %Y")
        elif "today" in text:
            date_str = today.strftime("%d %B, %Y")
        else:
            # Check for day names
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for i, day in enumerate(days):
                if day in text:
                    # Calculate next occurrence of this day
                    days_ahead = (i - today.weekday()) % 7
                    if days_ahead == 0:  # Today
                        days_ahead = 7
                    target_date = today + datetime.timedelta(days=days_ahead)
                    date_str = target_date.strftime("%d %B, %Y")
                    break
        
        # Extract meeting purpose with better logic
        purpose_keywords = ["discuss", "sync", "call", "meeting", "catch up", "review"]
        purpose = "Meeting"
        
        # Look for the main action word
        for keyword in purpose_keywords:
            if keyword in text:
                # Extract context around the keyword
                keyword_index = text.find(keyword)
                # Get words after the keyword (up to 5 words)
                after_keyword = text[keyword_index + len(keyword):].strip().split()[:5]
                if after_keyword:
                    # Filter out common words and time/date words
                    filtered_words = []
                    skip_words = ["at", "on", "tomorrow", "today", "am", "pm", "the", "a", "an", "and", "or", "to", "with", "could", "not", "extract", "axvalue", "from", "focused", "element"]
                    for word in after_keyword:
                        if word not in skip_words and not re.match(r'\d+', word) and len(word) > 2:
                            filtered_words.append(word)
                    
                    if filtered_words:
                        purpose = f"{keyword.title()} - {' '.join(filtered_words)}"
                    else:
                        purpose = keyword.title()
                else:
                    purpose = keyword.title()
                break
        
        # If no specific purpose found, try to extract from the full text
        if purpose == "Meeting":
            # Look for topics like "discuss LLMS", "review project", etc.
            topic_patterns = [
                r"discuss\s+(\w+)",
                r"review\s+(\w+)",
                r"sync\s+(\w+)",
                r"call\s+(\w+)"
            ]
            
            for pattern in topic_patterns:
                match = re.search(pattern, text)
                if match:
                    topic = match.group(1)
                    purpose = f"Meeting - {topic}"
                    break
        
        return {
            "date": date_str or today.strftime("%d %B, %Y"),
            "time": time_str or "10:00",
            "purpose": purpose
        }

    def simple_event_script(self, event_text):
        """Create a simple calendar event script with parsed details"""
        details = self.parse_meeting_details(event_text)
        
        # Calculate end time (1 hour later)
        try:
            start_time = datetime.datetime.strptime(details["time"], "%H:%M")
            end_time = start_time + datetime.timedelta(hours=1)
            end_time_str = end_time.strftime("%H:%M")
        except ValueError:
            # Fallback if time parsing fails
            start_time = datetime.datetime.now()
            end_time = start_time + datetime.timedelta(hours=1)
            details["time"] = start_time.strftime("%H:%M")
            end_time_str = end_time.strftime("%H:%M")
        
        # Format time for AppleScript (12-hour format with AM/PM)
        try:
            start_hour = int(details["time"].split(":")[0])
            start_minute = int(details["time"].split(":")[1])
            
            if start_hour >= 12:
                if start_hour > 12:
                    start_hour -= 12
                ampm = "PM"
            else:
                if start_hour == 0:
                    start_hour = 12
                ampm = "AM"
            
            end_hour = int(end_time_str.split(":")[0])
            end_minute = int(end_time_str.split(":")[1])
            
            if end_hour >= 12:
                if end_hour > 12:
                    end_hour -= 12
                end_ampm = "PM"
            else:
                if end_hour == 0:
                    end_hour = 12
                end_ampm = "AM"
            
            start_time_str = f"{start_hour}:{start_minute:02d} {ampm}"
            end_time_str = f"{end_hour}:{end_minute:02d} {end_ampm}"
        except:
            # Fallback to current time
            now = datetime.datetime.now()
            start_time_str = now.strftime("%I:%M %p")
            end_time = now + datetime.timedelta(hours=1)
            end_time_str = end_time.strftime("%I:%M %p")
            details["date"] = now.strftime("%d %B, %Y")
        
        script = f'''tell application "Calendar"
  tell calendar "Home"
    set startDate to date "{details["date"]} {start_time_str}"
    set endDate to date "{details["date"]} {end_time_str}"
    make new event at end with properties {{summary:"{details["purpose"]}", start date:startDate, end date:endDate}}
  end tell
  activate
end tell'''
        return script

    def clean_applescript(self, script):
        """Clean and extract AppleScript from LLM response."""
        # Remove markdown
        if "```" in script:
            parts = script.split("```")
            for part in parts:
                if "tell application" in part:
                    script = part
                    break
        
        # Remove shell wrapper
        lines = script.splitlines()
        applescript_lines = []
        in_applescript = False
        
        for line in lines:
            if 'tell application' in line:
                in_applescript = True
            if in_applescript:
                if 'EOF' in line or 'osascript' in line or line.strip().startswith('"'):
                    break
                applescript_lines.append(line)
        
        if applescript_lines:
            return '\n'.join(applescript_lines).strip()
        return script.strip()

    def validate_applescript(self, script):
        """Validate that the AppleScript is complete and correct."""
        required_elements = [
            'tell application "Calendar"',
            'tell calendar "Home"',
            'make new event',
            'summary:',
            'start date:',
            'end date:'
        ]
        
        # Check for required elements
        for element in required_elements:
            if element not in script:
                return False
        
        # Check for common errors
        error_indicators = [
            'not defined',
            'undefined variable',
            'syntax error',
            'missing',
            'error'
        ]
        
        for error in error_indicators:
            if error in script.lower():
                return False
        
        return True

    def ultra_simple_event_script(self, event_text):
        """Ultra-simple fallback that always works."""
        return f'''tell application "Calendar"
  tell calendar "Home"
    make new event at end with properties {{summary:"{event_text}"}}
  end tell
end tell'''

    def schedule_event_with_llm(self, event_text):
        """Schedule event with multiple fallback levels."""
        try:
            # Level 1: Try LLM-generated script
            script = self.generate_calendar_script(event_text)
            if script:
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[PA Buddy] Event scheduled successfully: {event_text}")
                    return True
                else:
                    print(f"[PA Buddy] LLM script failed: {result.stderr}")
                    print(f"[PA Buddy] Failed script:\n{script}")
            
            # Level 2: Try simple event script
            print("[PA Buddy] Trying simple event script...")
            simple_script = self.simple_event_script(event_text)
            result = run(["osascript", "-e", simple_script], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[PA Buddy] Simple event scheduled successfully: {event_text}")
                return True
            else:
                print(f"[PA Buddy] Simple script failed: {result.stderr}")
                print(f"[PA Buddy] Failed simple script:\n{simple_script}")
            
            # Level 3: Ultra-simple fallback
            print("[PA Buddy] Trying ultra-simple fallback...")
            ultra_script = self.ultra_simple_event_script(event_text)
            result = run(["osascript", "-e", ultra_script], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[PA Buddy] Ultra-simple event scheduled successfully: {event_text}")
                return True
            else:
                print(f"[PA Buddy] Ultra-simple script failed: {result.stderr}")
                print(f"[PA Buddy] Failed ultra-simple script:\n{ultra_script}")
            
            print("[PA Buddy] All calendar methods failed")
            return False
            
        except Exception as e:
            print(f"[PA Buddy] Error in event scheduling: {e}")
            return False

    def schedule_event_cli(self, event):
        """Try calcurse first, then multiple AppleScript fallbacks."""
        print(f"[PA Buddy] Scheduling event via CLI: {event}")
        
        # Try calcurse first
        if self.try_calcurse(event):
            print(f"[PA Buddy] Event scheduled in calcurse: {event}")
            return True
        
        # Try LLM + fallbacks
        if self.schedule_event_with_llm(event):
            return True
        
        print("[PA Buddy] All calendar methods failed")
        return False

    def schedule_meeting_from_user_input(self, meeting_text):
        """Schedule a meeting from user input using simple LLM processing."""
        print(f"[PA Buddy] Processing user meeting input: {meeting_text}")
        
        try:
            # Use LLM to generate AppleScript directly
            apple_script = self._generate_applescript_with_llm(meeting_text)
            
            if apple_script:
                # Execute the AppleScript
                result = run(["osascript", "-e", apple_script], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[PA Buddy] Meeting scheduled successfully: {meeting_text}")
                    return True
                else:
                    print(f"[PA Buddy] AppleScript failed: {result.stderr}")
                    return False
            else:
                print("[PA Buddy] Failed to generate AppleScript")
                return False
                
        except Exception as e:
            print(f"[PA Buddy] Error scheduling meeting: {e}")
            return False

    def _generate_applescript_with_llm(self, meeting_text):
        """Generate AppleScript for calendar event using LLM."""
        try:
            prompt = f"""
You are an AppleScript expert. Generate a working AppleScript to schedule a calendar event.

User input: "{meeting_text}"

Generate an AppleScript that:
1. Uses the "Work" calendar
2. Extracts date, time, and meeting purpose from the input
3. Sets both start and end date (1 hour duration if not specified)
4. Uses a descriptive summary based on the meeting purpose
5. Returns ONLY the AppleScript code, no explanations, no markdown formatting

Example format:
tell application "Calendar"
  tell calendar "Work"
    set startDate to date "July 22, 2025 2:00 PM"
    set endDate to date "July 22, 2025 3:00 PM"
    make new event at end with properties {{summary:"Meeting", start date:startDate, end date:endDate}}
  end tell
  activate
end tell

Parse this event text and generate the appropriate AppleScript. Return ONLY the AppleScript code, no markdown, no explanations.
"""
            
            response = llm.invoke([HumanMessage(content=prompt)])
            if response and response.content:
                script = response.content.strip()
                
                # Clean up any markdown formatting
                script = self._clean_applescript_response(script)
                
                print(f"[PA Buddy] Generated AppleScript: {script}")
                return script
            else:
                print("[PA Buddy] LLM failed to generate AppleScript")
                return None
                
        except Exception as e:
            print(f"[PA Buddy] Error generating AppleScript: {e}")
            return None

    def _clean_applescript_response(self, script):
        """Clean up AppleScript response by removing markdown formatting."""
        # Remove markdown code blocks
        script = re.sub(r'```applescript\s*', '', script)
        script = re.sub(r'```\s*$', '', script)
        script = re.sub(r'```\s*', '', script)
        
        # Remove any leading/trailing whitespace
        script = script.strip()
        
        return script

    def _process_meeting_text_with_llm(self, meeting_text):
        """Process meeting text with LLM to extract and format meeting details."""
        try:
            prompt = f"""
            You are a helpful assistant that processes meeting scheduling requests.
            
            User input: "{meeting_text}"
            
            Please extract and format the meeting details in a clear, structured way that can be used for calendar scheduling.
            
            Rules:
            1. Extract the meeting title, date, time, and any other relevant details
            2. If date/time is not specified, use reasonable defaults (e.g., today, tomorrow)
            3. Format the output as a clear meeting description
            4. Keep it concise but informative
            5. If the input is unclear, make reasonable assumptions
            
            Output format: A clear, structured meeting description that can be used for calendar scheduling.
            
            Example:
            Input: "team meeting tomorrow at 2pm"
            Output: "Team Meeting - Tomorrow at 2:00 PM"
            
            Input: "call with John about project"
            Output: "Call with John about project - Today at 3:00 PM"
            """
            
            response = llm.invoke([HumanMessage(content=prompt)])
            if response and response.content:
                processed_text = response.content.strip()
                print(f"[PA Buddy] LLM processed meeting text: {processed_text}")
                return processed_text
            else:
                print("[PA Buddy] LLM processing failed, using original text")
                return meeting_text
                
        except Exception as e:
            print(f"[PA Buddy] Error in LLM processing: {e}")
            return meeting_text

    def try_calcurse(self, event):
        """Try to add event to calcurse via CLI. Return True if successful."""
        try:
            # Method 1: Try calcurse -a (add appointment) - correct syntax
            result = run(["calcurse", "-a", "-n", event, "-d", "today"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[PA Buddy] Event added to calcurse: {event}")
                return True
            else:
                print(f"[PA Buddy] calcurse -a error: {result.stderr}")
        except FileNotFoundError:
            print("[PA Buddy] calcurse not installed. Trying alternative methods...")
        
        try:
            # Method 2: Try calcurse -n (add note) - correct syntax
            result = run(["calcurse", "-n", event], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[PA Buddy] Event added as note to calcurse: {event}")
                return True
            else:
                print(f"[PA Buddy] calcurse -n error: {result.stderr}")
        except FileNotFoundError:
            pass
        
        try:
            # Method 3: Try calcurse with interactive mode
            result = run(["calcurse", "-a", "-n", event], capture_output=True, text=True, input=b"\n")
            if result.returncode == 0:
                print(f"[PA Buddy] Event added to calcurse interactively: {event}")
                return True
            else:
                print(f"[PA Buddy] calcurse interactive error: {result.stderr}")
        except Exception as e:
            print(f"[PA Buddy] calcurse interactive error: {e}")
        
        print("[PA Buddy] calcurse not available or failed")
        return False

    def detect_user_care(self):
        """Detect if user needs care (e.g., late night, long work, etc.). Return action string or None."""
        # Example: If it's late, suggest reducing brightness or enabling night mode
        hour = time.localtime().tm_hour
        if hour >= 22 or hour < 6:
            return "It's late. Would you like to reduce screen brightness or enable night mode?"
        # TODO: Add more care logic (long work, hydration, etc.)
        return None

    def prompt_user_care(self, action):
        print(f"[PA Buddy] User care suggestion: {action}")
        # CLI prompt
        answer = input(f"{action} Type 'yes' to proceed, anything else to skip: ").strip().lower()
        if answer == "yes":
            self.perform_user_care_action(action)
        else:
            print("[PA Buddy] Skipped user care action.")
        # UI prompt (to be replaced with PyQt)
        self.show_user_care_ui(action)

    def perform_user_care_action(self, action):
        """Perform the user care action via CLI."""
        if "brightness" in action.lower():
            if "night" in action.lower() or "reduce" in action.lower():
                return self.set_night_brightness()
            else:
                return self.set_brightness(0.3)  # Default to 30%
        if "night mode" in action.lower():
            return self.enable_night_mode()
        if "music" in action.lower():
            return self.play_relaxing_music()
        if "block sites" in action.lower():
            return self.block_distracting_sites()
        return False

    def set_brightness(self, level):
        """Set screen brightness via F1/F2 key codes (macOS)."""
        
        try:
            # First, decrease brightness to minimum (F1 pressed 16 times)
            print(f"[PA Buddy] Setting brightness to level {level}")
            
            # Decrease to minimum first
            for i in range(16):
                script = 'tell application "System Events" to key code 145'
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                time.sleep(0.1)
            
            # Now increase to target level
            for i in range(level):
                script = 'tell application "System Events" to key code 144'
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                time.sleep(0.1)
            
            print(f"[PA Buddy] Brightness set to level {level})")
            return True
            
        except Exception as e:
            print(f"[PA Buddy] Brightness control error: {e}")
            return False

    def decrease_brightness(self, steps=1):
        """Decrease brightness by specified number of steps."""
        try:
            for i in range(steps):
                script = 'tell application "System Events" to key code 145'
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                time.sleep(0.1)
                if result.returncode != 0:
                    print(f"[PA Buddy] Error decreasing brightness: {result.stderr}")
                    return False
            print(f"[PA Buddy] Decreased brightness by {steps} step(s)")
            return True
        except Exception as e:
            print(f"[PA Buddy] Decrease brightness error: {e}")
            return False

    def increase_brightness(self, steps=1):
        """Increase brightness by specified number of steps."""
        try:
            for i in range(steps):
                script = 'tell application "System Events" to key code 144'
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                time.sleep(0.1)
                if result.returncode != 0:
                    print(f"[PA Buddy] Error increasing brightness: {result.stderr}")
                    return False
            print(f"[PA Buddy] Increased brightness by {steps} step(s)")
            return True
        except Exception as e:
            print(f"[PA Buddy] Increase brightness error: {e}")
            return False

    def set_night_brightness(self):
        """Set brightness to night mode (level 3-4 out of 16)."""
        try:
            # Decrease to minimum first
            for i in range(16):
                script = 'tell application "System Events" to key code 145'
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                time.sleep(0.1)
                if result.returncode != 0:
                    print(f"[PA Buddy] Error decreasing brightness: {result.stderr}")
                    return False
            
            # Increase to level 5 (night mode)
            for i in range(5):
                script = 'tell application "System Events" to key code 144'
                result = run(["osascript", "-e", script], capture_output=True, text=True)
                time.sleep(0.1)
                if result.returncode != 0:
                    print(f"[PA Buddy] Error increasing brightness: {result.stderr}")
                    return False
            
            print("[PA Buddy] Night brightness set (level 4/16)")
            return True
            
        except Exception as e:
            print(f"[PA Buddy] Night brightness error: {e}")
            return False

    def enable_night_mode(self):
        """Enable dark mode/night mode on macOS."""
        try:
            # Method 1: AppleScript for dark mode (more robust)
            script = '''
            tell application "System Events"
                tell appearance preferences
                    set dark mode to true
                end tell
            end tell
            '''
            result = run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                # Verify the change
                verify_script = '''
                tell application "System Events"
                    tell appearance preferences
                        get dark mode
                    end tell
                end tell
                '''
                verify_result = run(["osascript", "-e", verify_script], capture_output=True, text=True)
                if verify_result.returncode == 0:
                    is_dark = verify_result.stdout.strip().lower() == "true"
                    print(f"[PA Buddy] Night mode enabled via AppleScript (verified: {is_dark})")
                    return True
                else:
                    print(f"[PA Buddy] Night mode verification failed: {verify_result.stderr}")
            else:
                print(f"[PA Buddy] Night mode AppleScript error: {result.stderr}")
        except Exception as e:
            print(f"[PA Buddy] Night mode error: {e}")
        
        # Method 2: Alternative approach
        try:
            script = '''
            tell application "System Events"
                tell process "SystemUIServer"
                    set dark mode to true
                end tell
            end tell
            '''
            result = run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                print("[PA Buddy] Night mode enabled via alternative AppleScript")
                return True
            else:
                print(f"[PA Buddy] Alternative night mode error: {result.stderr}")
        except Exception as e:
            print(f"[PA Buddy] Alternative night mode error: {e}")
        
        print("[PA Buddy] Could not enable night mode")
        return False

    def play_relaxing_music(self):
        """Play relaxing music/sound."""
        try:
            # Method 1: Try system sounds
            system_sounds = [
                "/System/Library/Sounds/Glass.aiff",
                "/System/Library/Sounds/Ping.aiff", 
                "/System/Library/Sounds/Blow.aiff"
            ]
            
            for sound in system_sounds:
                if os.path.exists(sound):
                    result = run(["afplay", sound], capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"[PA Buddy] Playing relaxing sound: {sound}")
                        return True
            
            # Method 2: Try playing a short beep
            result = run(["afplay", "-v", "0.5", "-t", "2", "/System/Library/Sounds/Glass.aiff"], 
                        capture_output=True, text=True)
            if result.returncode == 0:
                print("[PA Buddy] Playing relaxing sound")
                return True
            else:
                print(f"[PA Buddy] afplay error: {result.stderr}")
        except Exception as e:
            print(f"[PA Buddy] Music error: {e}")
        
        print("[PA Buddy] Could not play music")
        return False

    def block_distracting_sites(self):
        """Block distracting sites by editing /etc/hosts (requires sudo)."""
        hosts_path = "/etc/hosts"
        block_entries = [
            "127.0.0.1 facebook.com\n",
            "127.0.0.1 www.facebook.com\n", 
            "127.0.0.1 youtube.com\n",
            "127.0.0.1 www.youtube.com\n",
            "127.0.0.1 twitter.com\n",
            "127.0.0.1 www.twitter.com\n"
        ]
        
        try:
            # Check if we can read the hosts file
            with open(hosts_path, "r") as f:
                lines = f.readlines()
            
            # Only add if not already present
            to_add = [entry for entry in block_entries if entry not in lines]
            
            if to_add:
                # Try to write without sudo first
                try:
                    with open(hosts_path, "a") as f:
                        f.writelines(to_add)
                    print("[PA Buddy] Distracting sites blocked (hosts file updated)")
                    print("[PA Buddy] Note: You may need to flush DNS: sudo dscacheutil -flushcache")
                    return True
                except PermissionError:
                    print("[PA Buddy] Permission denied: hosts file requires sudo access")
                    print("[PA Buddy] To block sites manually, run: sudo nano /etc/hosts")
                    return False
            else:
                print("[PA Buddy] Sites already blocked")
                return True
                
        except FileNotFoundError:
            print("[PA Buddy] hosts file not found")
            return False
        except Exception as e:
            print(f"[PA Buddy] Site blocking error: {e}")
            return False

    def test_cli_utilities(self):
        """Test all CLI utilities to see which ones work on this system."""
        print("[PA Buddy] Testing CLI utilities...")
        
        # Test brightness
        print("\n--- Testing Brightness ---")
        self.set_brightness(0.5)
        
        # Test night mode
        print("\n--- Testing Night Mode ---")
        self.enable_night_mode()
        
        # Test music
        print("\n--- Testing Music ---")
        self.play_relaxing_music()
        
        # Test site blocking
        print("\n--- Testing Site Blocking ---")
        self.block_distracting_sites()
        
        # Test calendar
        print("\n--- Testing Calendar ---")
        self.schedule_event_cli("Test event from PA Buddy")
        
        print("\n[PA Buddy] CLI utility testing complete!")

    # Stub for UI integration
    def show_event_ui(self, event):
        def on_yes():
            root.destroy()
            self.schedule_event_cli(event)
        def on_no():
            root.destroy()
            print("[PA Buddy] Skipped scheduling (UI).")
        def run_ui():
            nonlocal event
            root = tk.Tk()
            root.title("PA Buddy: Schedule Event?")
            root.geometry("400x150")
            label = tk.Label(root, text=f"Detected event:\n{event}", font=("Arial", 12), wraplength=380)
            label.pack(pady=10)
            btn_frame = tk.Frame(root)
            btn_frame.pack(pady=10)
            yes_btn = tk.Button(btn_frame, text="Yes, schedule", command=on_yes, width=15)
            yes_btn.pack(side=tk.LEFT, padx=10)
            no_btn = tk.Button(btn_frame, text="No, skip", command=on_no, width=15)
            no_btn.pack(side=tk.LEFT, padx=10)
            root.mainloop()
        threading.Thread(target=run_ui).start()

    def show_user_care_ui(self, action):
        print(f"[PA Buddy] (Stub) Would show user care suggestion in UI: {action}")
        # TODO: Replace with PyQt UI

    def read_live_output(self):
        """Read the latest live output data"""
        try:
            with open("output/live_output.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PA Buddy] Error reading live output: {e}")
            return None

    # Focus Automation Methods
    def get_focus_status(self):
        """Get current focus automation status"""
        return self.focus_automation.get_focus_status()
    
    def toggle_focus_mode(self):
        """Manually toggle focus mode"""
        return self.focus_automation.manual_focus_mode_toggle()
    
    def trigger_break_reminder(self):
        """Manually trigger a break reminder"""
        return self.focus_automation.manual_break_reminder()
    
    def get_auto_saved_work(self):
        """Get list of auto-saved work"""
        return self.focus_automation.get_auto_saved_work()
    
    def clear_auto_saved_work(self):
        """Clear auto-saved work history"""
        return self.focus_automation.clear_auto_saved_work()
    
    def get_work_intensity(self):
        """Get current work intensity score"""
        status = self.focus_automation.get_focus_status()
        return status.get("work_intensity_score", 0)
    
    def is_focus_mode_active(self):
        """Check if focus mode is currently active"""
        status = self.focus_automation.get_focus_status()
        return status.get("focus_mode_active", False)
    
    def is_night_mode_active(self):
        """Check if night mode is currently active"""
        status = self.focus_automation.get_focus_status()
        return status.get("night_mode_active", False)


