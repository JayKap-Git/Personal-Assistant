#!/usr/bin/env python3
"""
Standalone Chatbot Buddy Runner
Run this to start the chatbot independently
"""

import time
import signal
import sys
from buddies.chatbot_buddy import ChatbotBuddy

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🤖 Chatbot Buddy: Goodbye! Take care! 👋")
    sys.exit(0)

def main():
    """Main chatbot runner"""
    print("🤖 Chatbot Buddy - Your Friendly AI Companion")
    print("=" * 50)
    print("I'll check in on you during long work sessions and keep you company!")
    print("Commands: 'joke', 'stats', 'check', 'reset', 'quit'")
    print("=" * 50)
    
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize and start chatbot
    chatbot = ChatbotBuddy()
    chatbot.start_monitoring()
    
    print("🚀 Chatbot Buddy is now active!")
    print("💬 I'll automatically check in when you've been working too long.")
    print("💡 You can also chat with me anytime!")
    
    try:
        while True:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'joke':
                chatbot.tell_joke()
            elif user_input.lower() == 'stats':
                print(f"📊 {chatbot.get_work_stats()}")
            elif user_input.lower() == 'check':
                chatbot.manual_check_in()
            elif user_input.lower() == 'reset':
                chatbot.reset_work_session()
                print("🔄 Work session reset!")
            elif user_input.lower() == 'status':
                status = chatbot.get_status()
                print(f"📈 Status: {status}")
            elif user_input.lower() == 'history':
                history = chatbot.get_conversation_history()
                print(f"📚 Conversation history ({len(history)} messages):")
                for msg in history[-5:]:  # Show last 5 messages
                    print(f"  {msg['speaker']}: {msg['message']}")
            elif user_input.lower() == 'clear':
                chatbot.clear_conversation_history()
            elif user_input:
                chatbot.respond_to_user(user_input)
                
    except KeyboardInterrupt:
        pass
    finally:
        chatbot.stop_monitoring()
        print("\n🤖 Chatbot Buddy: Thanks for chatting! See you next time! 👋")

if __name__ == "__main__":
    main() 