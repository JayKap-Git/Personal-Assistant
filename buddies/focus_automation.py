#!/usr/bin/env python3
"""
Focus & Productivity Automation Module
Handles focus mode, break reminders, night mode, distraction blocking, and auto-save
"""

import json
import time
import threading
import subprocess
import platform
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pyperclip
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv

load_dotenv()

class FocusAutomation:
    def __init__(self, personal_assistant):
        self.pa = personal_assistant
        self.is_focus_mode_active = False
        self.is_night_mode_active = False
        self.focus_start_time = None
        self.last_break_time = None
        self.work_intensity_score = 0
        self.distraction_sites_blocked = []
        self.auto_save_enabled = True
        self.non_coding_start_time = None  # Track when non-coding activity starts
        
        # Configuration
        self.config = {
            "focus_threshold_minutes": 30,  # Enable focus mode after 30 min of coding
            "break_interval_minutes": 25,   # Take breaks every 25 minutes
            "night_mode_start_hour": 20,    # Enable night mode after 8 PM
            "night_mode_end_hour": 7,       # Disable night mode after 7 AM
            "distraction_sites": [
                "facebook.com", "twitter.com", "instagram.com", 
                "youtube.com", "reddit.com", "tiktok.com", "m.youtube.com"
            ],
            "auto_save_interval_seconds": 300  # Auto-save every 5 minutes
        }
        
        # Start monitoring threads
        self._start_monitoring()
        
    def _start_monitoring(self):
        """Start all monitoring threads"""
        # Focus mode monitoring
        focus_thread = threading.Thread(target=self._monitor_focus_mode, daemon=True)
        focus_thread.start()
        
        # Break reminder monitoring
        break_thread = threading.Thread(target=self._monitor_break_reminders, daemon=True)
        break_thread.start()
        
        # Night mode monitoring
        night_thread = threading.Thread(target=self._monitor_night_mode, daemon=True)
        night_thread.start()
        
        # Auto-save monitoring
        if self.auto_save_enabled:
            autosave_thread = threading.Thread(target=self._monitor_auto_save, daemon=True)
            autosave_thread.start()
        
        print("🎯 Focus Automation monitoring started!")
    
    def _monitor_focus_mode(self):
        """Monitor for extended coding sessions to enable focus mode and disable only after 30 min of non-coding"""
        while True:
            try:
                current_activity = self._get_current_activity()
                now = datetime.now()
                if current_activity and current_activity.get("activity") == "coding":
                    self.non_coding_start_time = None  # Reset non-coding timer
                    # Enable focus mode if coding for extended period (manual toggle still works)
                    if not self.focus_start_time:
                        self.focus_start_time = now
                    coding_duration = (now - self.focus_start_time).total_seconds() / 60
                    if coding_duration >= self.config["focus_threshold_minutes"] and not self.is_focus_mode_active:
                        self._enable_focus_mode()
                else:
                    # If not coding, start or update non-coding timer
                    if self.is_focus_mode_active:
                        if not self.non_coding_start_time:
                            self.non_coding_start_time = now
                        non_coding_duration = (now - self.non_coding_start_time).total_seconds() / 60
                        if non_coding_duration >= self.config["focus_threshold_minutes"]:
                            self._disable_focus_mode()
                            self.non_coding_start_time = None
                    self.focus_start_time = None
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"🎯 Focus mode monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_break_reminders(self):
        """Monitor work intensity and suggest breaks"""
        while True:
            try:
                if self.is_focus_mode_active:
                    # Calculate work intensity
                    self._calculate_work_intensity()
                    
                    # Suggest breaks based on intensity
                    if self.work_intensity_score > 0.7:  # High intensity
                        if not self.last_break_time or (datetime.now() - self.last_break_time).total_seconds() > 1200:  # 20 min
                            self._suggest_break("high_intensity")
                    elif self.work_intensity_score > 0.4:  # Medium intensity
                        if not self.last_break_time or (datetime.now() - self.last_break_time).total_seconds() > 1800:  # 30 min
                            self._suggest_break("medium_intensity")
                    else:  # Low intensity
                        if not self.last_break_time or (datetime.now() - self.last_break_time).total_seconds() > 3600:  # 1 hour
                            self._suggest_break("low_intensity")
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"🎯 Break reminder monitoring error: {e}")
                time.sleep(300)
    
    def _monitor_night_mode(self):
        """Monitor time to enable/disable night mode"""
        while True:
            try:
                current_hour = datetime.now().hour
                
                # Check if it's time for night mode
                if (current_hour >= self.config["night_mode_start_hour"] or 
                    current_hour < self.config["night_mode_end_hour"]):
                    if not self.is_night_mode_active:
                        self._enable_night_mode()
                else:
                    if self.is_night_mode_active:
                        self._disable_night_mode()
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"🎯 Night mode monitoring error: {e}")
                time.sleep(300)
    
    def _monitor_auto_save(self):
        """Monitor for application switches and auto-save work"""
        last_active_window = None
        
        while True:
            try:
                current_activity = self._get_current_activity()
                current_window = current_activity.get("active_window", "") if current_activity else ""
                
                # Check if user switched applications
                if last_active_window and last_active_window != current_window:
                    self._auto_save_work(last_active_window, current_window)
                
                last_active_window = current_window
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"🎯 Auto-save monitoring error: {e}")
                time.sleep(10)
    
    def _get_current_activity(self) -> Optional[Dict[str, Any]]:
        """Get current activity data"""
        try:
            with open("output/live_output.json", "r") as f:
                data = json.load(f)
            
            # Also get analyzed activity
            try:
                with open("output/prediction_output.json", "r") as f:
                    analyzed = json.load(f)
                    data["analyzed_activity"] = analyzed
            except:
                pass
            
            return data
        except Exception as e:
            print(f"🎯 Error reading activity data: {e}")
            return None
    
    def _calculate_work_intensity(self):
        """Calculate work intensity based on various factors"""
        try:
            current_activity = self._get_current_activity()
            if not current_activity:
                return
            
            intensity_score = 0.0
            
            # Factor 1: Activity type
            analyzed = current_activity.get("analyzed_activity", {})
            activity_type = analyzed.get("activity", "")
            confidence = analyzed.get("confidence", 0)
            
            if activity_type == "coding" and confidence > 0.7:
                intensity_score += 0.4
            elif activity_type == "researching" and confidence > 0.7:
                intensity_score += 0.3
            elif activity_type == "writing" and confidence > 0.7:
                intensity_score += 0.3
            
            # Factor 2: Time of day (peak productivity hours)
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 11 or 14 <= current_hour <= 16:
                intensity_score += 0.2
            
            # Factor 3: Duration of focus session
            if self.focus_start_time:
                focus_duration = (datetime.now() - self.focus_start_time).total_seconds() / 3600  # hours
                if focus_duration > 2:  # More than 2 hours
                    intensity_score += 0.2
                elif focus_duration > 1:  # More than 1 hour
                    intensity_score += 0.1
            
            # Factor 4: Clipboard activity (copying/pasting indicates active work)
            clipboard = current_activity.get("clipboard", "")
            if clipboard and len(clipboard) > 10:
                intensity_score += 0.1
            
            self.work_intensity_score = min(intensity_score, 1.0)
            
        except Exception as e:
            print(f"🎯 Error calculating work intensity: {e}")
    
    def _enable_focus_mode(self):
        """Enable focus mode with distraction blocking"""
        self.is_focus_mode_active = True
        print("🎯 Focus mode enabled! Blocking distractions...")
        
        # Block distraction sites
        self._block_distraction_sites()
        
        # Show focus mode notification
        self._show_notification(
            "Focus Mode Enabled",
            "Distractions blocked. Stay focused on your work!",
            "info"
        )
    
    def _disable_focus_mode(self):
        """Disable focus mode"""
        self.is_focus_mode_active = False
        print("🎯 Focus mode disabled.")
        
        # Unblock distraction sites
        self._unblock_distraction_sites()
        
        # Show notification
        self._show_notification(
            "Focus Mode Disabled",
            "Distractions unblocked. Take a break if needed!",
            "info"
        )
    
    def _block_distraction_sites(self):
        """Block distraction websites using block_sites.sh script"""
        if platform.system() == "Darwin":  # macOS
            try:
                sites = self.config["distraction_sites"]
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'block_sites.sh'))
                cmd = ["sudo", script_path, "block"] + sites
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
                if result.returncode != 0:
                    print(f"🎯 Error blocking sites: {result.stderr}")
                else:
                    self.distraction_sites_blocked = sites.copy()
            except Exception as e:
                print(f"🎯 Could not block distraction sites: {e}")
        else:
            print("🎯 Site blocking only supported on macOS in this version.")

    def _unblock_distraction_sites(self):
        """Unblock distraction websites using block_sites.sh script"""
        if platform.system() == "Darwin":  # macOS
            try:
                sites = self.config["distraction_sites"]
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'block_sites.sh'))
                cmd = ["sudo", script_path, "unblock"] + sites
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
                if result.returncode != 0:
                    print(f"🎯 Error unblocking sites: {result.stderr}")
                else:
                    self.distraction_sites_blocked = []
            except Exception as e:
                print(f"🎯 Could not unblock distraction sites: {e}")
        else:
            print("🎯 Site unblocking only supported on macOS in this version.")
    
    def _suggest_break(self, intensity_level: str):
        """Suggest a break based on work intensity"""
        break_messages = {
            "high_intensity": "🔥 You've been working intensely! Time for a 5-minute break to recharge.",
            "medium_intensity": "⚡ You've been focused for a while. How about a quick 3-minute break?",
            "low_intensity": "💡 You've been working steadily. Consider a short break to refresh."
        }
        
        message = break_messages.get(intensity_level, "Time for a break!")
        
        # Show break suggestion
        self._show_notification(
            "Break Time!",
            message,
            "warning"
        )
        
        # Update last break time
        self.last_break_time = datetime.now()
        
        print(f"🎯 Break suggested ({intensity_level}): {message}")
    
    def _enable_night_mode(self):
        """Enable night mode"""
        self.is_night_mode_active = True
        print("🌙 Night mode enabled!")
        
        # Set brightness to level 4 for night mode
        self.pa.set_brightness(4)
        
        # Show notification
        self._show_notification(
            "Night Mode Enabled",
            "Screen brightness set to level 4 for evening work.",
            "info"
        )
    
    def _disable_night_mode(self):
        """Disable night mode"""
        self.is_night_mode_active = False
        print("🌙 Night mode disabled!")
        
        # Restore brightness to level 12
        self.pa.set_brightness(12)
        
        # Show notification
        self._show_notification(
            "Night Mode Disabled",
            "Screen brightness restored to level 12.",
            "info"
        )
    
    def _auto_save_work(self, from_window: str, to_window: str):
        """Auto-save work when switching applications"""
        try:
            # Get current clipboard content
            clipboard_content = pyperclip.paste()
            
            # Check if clipboard contains work content
            if (len(clipboard_content) > 20 and 
                any(keyword in clipboard_content.lower() for keyword in ["function", "class", "import", "def", "const", "let", "var"])):
                
                # Create auto-save entry
                save_data = {
                    "timestamp": datetime.now().isoformat(),
                    "from_window": from_window,
                    "to_window": to_window,
                    "clipboard_content": clipboard_content,
                    "activity": "auto_save"
                }
                
                # Save to auto-save file
                auto_save_file = "output/auto_save_work.json"
                try:
                    with open(auto_save_file, "r") as f:
                        auto_saves = json.load(f)
                except:
                    auto_saves = []
                
                auto_saves.append(save_data)
                
                # Keep only last 50 auto-saves
                if len(auto_saves) > 50:
                    auto_saves = auto_saves[-50:]
                
                with open(auto_save_file, "w") as f:
                    json.dump(auto_saves, f, indent=2)
                
                print(f"🎯 Auto-saved work from {from_window} to {to_window}")
                
        except Exception as e:
            print(f"🎯 Auto-save error: {e}")
    
    def _show_notification(self, title: str, message: str, notification_type: str = "info"):
        """Show a system notification"""
        try:
            if platform.system() == "Darwin":  # macOS
                script = f'''
                display notification "{message}" with title "{title}"
                '''
                subprocess.run(["osascript", "-e", script])
            else:
                # Fallback to tkinter message box
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                if notification_type == "warning":
                    messagebox.showwarning(title, message)
                elif notification_type == "error":
                    messagebox.showerror(title, message)
                else:
                    messagebox.showinfo(title, message)
                
                root.destroy()
                
        except Exception as e:
            print(f"🎯 Notification error: {e}")
    
    def get_focus_status(self) -> Dict[str, Any]:
        """Get current focus automation status"""
        return {
            "focus_mode_active": self.is_focus_mode_active,
            "night_mode_active": self.is_night_mode_active,
            "work_intensity_score": self.work_intensity_score,
            "focus_duration_minutes": self._get_focus_duration_minutes(),
            "sites_blocked": len(self.distraction_sites_blocked),
            "auto_save_enabled": self.auto_save_enabled
        }
    
    def _get_focus_duration_minutes(self) -> int:
        """Get current focus session duration in minutes"""
        if self.focus_start_time:
            duration = (datetime.now() - self.focus_start_time).total_seconds() / 60
            return int(duration)
        return 0
    
    def manual_focus_mode_toggle(self):
        """Manually toggle focus mode"""
        if self.is_focus_mode_active:
            self._disable_focus_mode()
        else:
            self._enable_focus_mode()
    
    def manual_break_reminder(self):
        """Manually trigger a break reminder"""
        self._suggest_break("manual")
    
    def get_auto_saved_work(self) -> list:
        """Get list of auto-saved work"""
        try:
            with open("output/auto_save_work.json", "r") as f:
                return json.load(f)
        except:
            return []
    
    def clear_auto_saved_work(self):
        """Clear auto-saved work history"""
        try:
            with open("output/auto_save_work.json", "w") as f:
                json.dump([], f)
            print("🎯 Auto-saved work history cleared")
        except Exception as e:
            print(f"🎯 Error clearing auto-saved work: {e}") 