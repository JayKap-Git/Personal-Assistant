#!/usr/bin/env python3
"""
Chatbot Buddy - An independent conversational AI that engages with the user
"""

import json
import time
import random
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import os

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

class ChatbotBuddy:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.8,
            convert_system_message_to_human=True
        )
        self.last_interaction = None
        self.work_start_time = None
        self.is_active = False
        self.conversation_history = []
        self.current_activity = None
        
        # Jokes database
        self.jokes = [
            "Why don't programmers like nature? It has too many bugs!",
            "Why did the computer go to the doctor? Because it had a virus!",
            "What do you call a computer that sings? A Dell!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a can opener that doesn't work? A can't opener!",
            "Why did the cookie go to the doctor? Because it was feeling crumbly!",
            "What do you call a computer that sings? A Dell!",
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call a fake noodle? An impasta!"
        ]
        
        # Conversation starters
        self.conversation_starters = [
            "Hey there! 👋 How's your day going?",
            "Hi! 😊 Taking a break? I'm here if you want to chat!",
            "Hello! 🌟 You've been working hard. Want to hear a joke?",
            "Hey! 🎉 How about we take a quick mental break?",
            "Hi there! ✨ You've been focused for a while. Everything okay?",
            "Hello! 🚀 Need a quick distraction? I've got some jokes!",
            "Hey! 🎯 How's the work going? Want to chat for a bit?",
            "Hi! 🌈 You've been at it for a while. Time for a breather?"
        ]
        
        # Work check-in messages
        self.work_checkins = [
            "You've been working for quite a while! 🤔 How about a quick break?",
            "Hey, you've been focused for a long time! 💪 Need a breather?",
            "Wow, you're really in the zone! 🎯 But maybe it's time for a short break?",
            "You've been at it for hours! ⏰ How about we take a quick pause?",
            "Impressive focus! 🚀 But even superheroes need breaks. Want to chat?",
            "You've been working hard! 💼 Time for a quick mental refresh?",
            "Long coding session detected! 💻 How about a 5-minute break?",
            "You've been productive! 📈 But don't forget to take care of yourself!"
        ]

    def start_monitoring(self):
        """Start the chatbot monitoring in a separate thread"""
        self.is_active = True
        self.work_start_time = datetime.now()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_work_sessions, daemon=True)
        monitor_thread.start()
        
        print("🤖 Chatbot Buddy is now active and monitoring your work sessions!")
        print("💬 I'll check in on you and keep you company during long work sessions.")

    def stop_monitoring(self):
        """Stop the chatbot monitoring"""
        self.is_active = False
        print("🤖 Chatbot Buddy is going to sleep. Goodbye!")

    def get_current_activity(self):
        """Get the current user activity data"""
        try:
            with open("output/live_output.json", "r") as f:
                activity_data = json.load(f)
            
            # Also get the analyzed activity
            try:
                with open("output/prediction_output.json", "r") as f:
                    analyzed_activity = json.load(f)
            except:
                analyzed_activity = {}
            
            return {
                "raw_data": activity_data,
                "analyzed": analyzed_activity
            }
        except Exception as e:
            print(f"🤖 Error reading activity data: {e}")
            return None

    def _monitor_work_sessions(self):
        """Monitor work sessions and initiate conversations"""
        while self.is_active:
            try:
                current_time = datetime.now()
                
                # Update current activity
                self.current_activity = self.get_current_activity()
                
                # Check if user has been working for more than 2 hours
                if self.work_start_time and (current_time - self.work_start_time).total_seconds() > 7200:  # 2 hours
                    if not self.last_interaction or (current_time - self.last_interaction).total_seconds() > 1800:  # 30 minutes
                        self._initiate_conversation()
                        self.last_interaction = current_time
                
                # Check if user has been working for more than 1 hour
                elif self.work_start_time and (current_time - self.work_start_time).total_seconds() > 3600:  # 1 hour
                    if not self.last_interaction or (current_time - self.last_interaction).total_seconds() > 3600:  # 1 hour
                        self._initiate_conversation()
                        self.last_interaction = current_time
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"🤖 Chatbot Buddy error: {e}")
                time.sleep(60)

    def _initiate_conversation(self):
        """Initiate a conversation with the user"""
        try:
            # Get current activity context
            activity_context = self._get_activity_context()
            
            # Choose a conversation starter
            starter = random.choice(self.conversation_starters)
            work_message = random.choice(self.work_checkins)
            
            # Combine messages with activity context
            if activity_context:
                message = f"{work_message}\n\n{activity_context}\n\n{starter}"
            else:
                message = f"{work_message}\n\n{starter}"
            
            print(f"\n🤖 Chatbot Buddy: {message}")
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "bot",
                "message": message
            })
            
        except Exception as e:
            print(f"🤖 Error initiating conversation: {e}")

    def _get_activity_context(self):
        """Get contextual information about current activity"""
        if not self.current_activity:
            return None
        
        try:
            raw_data = self.current_activity.get("raw_data", {})
            analyzed = self.current_activity.get("analyzed", {})
            
            context_parts = []
            
            # Add analyzed activity if available
            if analyzed:
                activity_type = analyzed.get("description", "")
                details = analyzed.get("details", "")
                confidence = analyzed.get("confidence", 0)
                
                if activity_type and confidence > 0.5:
                    context_parts.append(f"I can see you're {activity_type.lower()}")
                    if details:
                        context_parts.append(f"Specifically: {details}")
            
            # Add active window info
            active_window = raw_data.get("active_window", "")
            if active_window and active_window != "unknown":
                context_parts.append(f"You're currently using {active_window}")
            
            # Add clipboard context if it seems relevant
            clipboard = raw_data.get("clipboard", "")
            if clipboard and len(clipboard) > 10 and len(clipboard) < 200:
                # Check if clipboard contains meeting-related content
                meeting_keywords = ["meet", "meeting", "call", "appointment", "schedule"]
                if any(keyword in clipboard.lower() for keyword in meeting_keywords):
                    context_parts.append(f"I noticed you have meeting details in your clipboard")
            
            if context_parts:
                return " ".join(context_parts)
            else:
                return None
                
        except Exception as e:
            print(f"🤖 Error getting activity context: {e}")
            return None

    def get_activity_insights(self):
        """Get detailed insights about current activity for the chatbot"""
        if not self.current_activity:
            return None
        
        try:
            raw_data = self.current_activity.get("raw_data", {})
            analyzed = self.current_activity.get("analyzed", {})
            
            insights = {
                "active_window": raw_data.get("active_window", ""),
                "focused_text": raw_data.get("focused_text", ""),
                "clipboard": raw_data.get("clipboard", ""),
                "ocr_text": raw_data.get("ocr_text", ""),
                "vscode_text": raw_data.get("vscode_text", ""),
                "analyzed_activity": analyzed.get("activity", ""),
                "activity_description": analyzed.get("description", ""),
                "activity_details": analyzed.get("details", ""),
                "confidence": analyzed.get("confidence", 0)
            }
            
            return insights
            
        except Exception as e:
            print(f"🤖 Error getting activity insights: {e}")
            return None

    def tell_joke(self):
        """Tell a random joke"""
        joke = random.choice(self.jokes)
        print(f"🤖 Chatbot Buddy: {joke} 😄")
        
        # Add to conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "bot",
            "message": joke
        })
        
        return joke

    def respond_to_user(self, user_message):
        """Respond to user input using LLM with activity context"""
        try:
            # Get current activity context
            activity_context = self._get_activity_context()
            
            # Build context from conversation history
            context = ""
            if self.conversation_history:
                recent_messages = self.conversation_history[-5:]  # Last 5 messages
                context = "\n".join([f"{msg['speaker']}: {msg['message']}" for msg in recent_messages])
            
            # Create enhanced system prompt with activity awareness
            system_prompt = """You are Chatbot Buddy, a friendly and supportive AI companion who is aware of the user's current activity. Your role is to:
- Be cheerful, encouraging, and supportive
- Tell jokes and make the user smile
- Check in on their well-being during long work sessions
- Provide positive reinforcement and motivation
- Keep conversations light and engaging
- Ask about their work progress and offer encouragement
- Suggest breaks when appropriate
- Reference their current activity when relevant and helpful

Keep your responses short (2-3 sentences max), friendly, and conversational. Use emojis occasionally to keep things light. If you know what the user is currently doing, you can reference it naturally in your response."""

            # Build user prompt with activity context
            user_prompt = f"User: {user_message}"
            
            if activity_context:
                user_prompt += f"\n\nCurrent Activity Context: {activity_context}"
            
            if context:
                user_prompt += f"\n\nRecent Conversation:\n{context}"
            
            user_prompt += "\n\nRespond as Chatbot Buddy:"

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            if response and response.content:
                bot_response = response.content.strip()
                print(f"🤖 Chatbot Buddy: {bot_response}")
                
                # Add to conversation history
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "speaker": "user",
                    "message": user_message
                })
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "speaker": "bot",
                    "message": bot_response
                })
                
                return bot_response
            else:
                return "Sorry, I didn't catch that. Could you repeat?"
                
        except Exception as e:
            print(f"🤖 Error generating response: {e}")
            return "I'm having trouble thinking right now. How about a joke instead?"

    def get_work_stats(self):
        """Get current work session statistics"""
        if not self.work_start_time:
            return "No work session started yet."
        
        duration = datetime.now() - self.work_start_time
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        
        return f"You've been working for {int(hours)} hours and {int(minutes)} minutes! 💪"

    def reset_work_session(self):
        """Reset the work session timer"""
        self.work_start_time = datetime.now()
        self.last_interaction = None
        print("🤖 Chatbot Buddy: Work session reset! Starting fresh! 🚀")

    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history

    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        print("🤖 Chatbot Buddy: Conversation history cleared! 🗑️")

    def manual_check_in(self):
        """Manually trigger a check-in"""
        self._initiate_conversation()

    def get_status(self):
        """Get the current status of the chatbot"""
        status = {
            "active": self.is_active,
            "work_start_time": self.work_start_time.isoformat() if self.work_start_time else None,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "conversation_count": len(self.conversation_history)
        }
        return status 