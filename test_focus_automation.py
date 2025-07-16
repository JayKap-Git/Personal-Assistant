#!/usr/bin/env python3
"""
Test Focus Automation Features
Demonstrates the focus automation capabilities
"""

import time
import json
from datetime import datetime
from buddies.personal_assistant import PersonalAssistantBuddy

def test_focus_automation():
    """Test the focus automation features"""
    print("🎯 Testing Focus & Productivity Automation Features")
    print("=" * 60)
    
    # Initialize personal assistant
    pa = PersonalAssistantBuddy()
    
    print("\n1. 📊 Current Focus Status:")
    status = pa.get_focus_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n2. 🎯 Testing Focus Mode Toggle:")
    print("   Toggling focus mode...")
    pa.toggle_focus_mode()
    time.sleep(2)
    
    status = pa.get_focus_status()
    print(f"   Focus mode active: {status.get('focus_mode_active', False)}")
    
    print("\n3. ⚡ Testing Break Reminder:")
    print("   Triggering break reminder...")
    pa.trigger_break_reminder()
    
    print("\n4. 🌙 Testing Night Mode:")
    current_hour = datetime.now().hour
    print(f"   Current hour: {current_hour}")
    print(f"   Night mode should be active: {current_hour >= 20 or current_hour < 7}")
    
    print("\n5. 💾 Testing Auto-Save:")
    auto_saved = pa.get_auto_saved_work()
    print(f"   Auto-saved entries: {len(auto_saved)}")
    
    if auto_saved:
        print("   Recent auto-saved work:")
        for i, work in enumerate(auto_saved[-3:], 1):  # Show last 3
            timestamp = work.get("timestamp", "")
            from_window = work.get("from_window", "")
            content = work.get("clipboard_content", "")[:50]
            print(f"     {i}. {timestamp} - {from_window}: {content}...")
    
    print("\n6. 📈 Work Intensity Analysis:")
    intensity = pa.get_work_intensity()
    print(f"   Current work intensity: {intensity:.2f} ({int(intensity * 100)}%)")
    
    print("\n7. 🔧 Manual Controls Available:")
    print("   - pa.toggle_focus_mode() - Toggle focus mode")
    print("   - pa.trigger_break_reminder() - Trigger break")
    print("   - pa.get_auto_saved_work() - Get auto-saved work")
    print("   - pa.clear_auto_saved_work() - Clear auto-save history")
    print("   - pa.get_focus_status() - Get current status")
    
    print("\n8. 🎛️ Configuration:")
    config = pa.focus_automation.config
    print(f"   Focus threshold: {config['focus_threshold_minutes']} minutes")
    print(f"   Break interval: {config['break_interval_minutes']} minutes")
    print(f"   Night mode hours: {config['night_mode_start_hour']} - {config['night_mode_end_hour']}")
    print(f"   Distraction sites: {len(config['distraction_sites'])} sites")
    
    print("\n✅ Focus automation test completed!")
    print("\n💡 To use the GUI control panel, run: python focus_control_ui.py")

def simulate_coding_session():
    """Simulate a coding session to test automation"""
    print("\n🎮 Simulating Coding Session...")
    print("This will simulate 35 minutes of coding to trigger focus mode")
    
    # Create mock activity data
    mock_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "active_window": "Cursor",
        "focused_text": "def test_function():",
        "clipboard": "import numpy as np",
        "vscode_text": "class TestClass:",
        "ocr_text": "Python code editor"
    }
    
    # Save mock data
    with open("output/live_output.json", "w") as f:
        json.dump(mock_data, f, indent=2)
    
    # Create mock analyzed activity
    mock_analyzed = {
        "activity": "coding",
        "confidence": 0.85,
        "description": "User is writing Python code",
        "details": "Detected Python syntax and IDE interface",
        "timestamp": time.time()
    }
    
    with open("output/prediction_output.json", "w") as f:
        json.dump(mock_analyzed, f, indent=2)
    
    print("✅ Mock coding session data created!")
    print("   The focus automation should detect this as coding activity")
    print("   Focus mode will be enabled after 30 minutes of detected coding")

def show_automation_features():
    """Show what automation features are available"""
    print("\n🎯 Focus & Productivity Automation Features:")
    print("=" * 50)
    
    features = [
        {
            "name": "Auto Focus Mode",
            "description": "Automatically enables focus mode after 30 minutes of coding",
            "trigger": "Extended coding sessions",
            "action": "Blocks distractions, shows notifications"
        },
        {
            "name": "Smart Break Reminders",
            "description": "Suggests breaks based on work intensity",
            "trigger": "High/medium/low work intensity",
            "action": "Shows break notifications with different messages"
        },
        {
            "name": "Auto Night Mode",
            "description": "Automatically enables night mode after 8 PM",
            "trigger": "Time-based (8 PM - 7 AM)",
            "action": "Adjusts screen brightness, shows notifications"
        },
        {
            "name": "Distraction Blocking",
            "description": "Blocks social media sites during focus mode",
            "trigger": "Focus mode activation",
            "action": "Modifies hosts file to block sites"
        },
        {
            "name": "Auto-Save Work",
            "description": "Saves work when switching applications",
            "trigger": "Application switching with work content",
            "action": "Saves clipboard content to JSON file"
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. {feature['name']}")
        print(f"   Description: {feature['description']}")
        print(f"   Trigger: {feature['trigger']}")
        print(f"   Action: {feature['action']}")

if __name__ == "__main__":
    print("🎯 Focus Automation Test Suite")
    print("=" * 40)
    
    # Show available features
    show_automation_features()
    
    # Run tests
    test_focus_automation()
    
    # Simulate coding session
    simulate_coding_session()
    
    print("\n🚀 To start using focus automation:")
    print("1. Run: python focus_control_ui.py (for GUI)")
    print("2. Or integrate with your existing personal assistant")
    print("3. The automation runs in the background automatically") 