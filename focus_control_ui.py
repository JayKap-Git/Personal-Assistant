#!/usr/bin/env python3
"""
Focus Control UI - Simple interface to control focus automation features
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from datetime import datetime
from buddies.personal_assistant import PersonalAssistantBuddy

# --- PyQt5 version for integration ---
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGroupBox, QGridLayout, QMessageBox, QTextEdit
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.Qt import Qt

class FocusControlUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Focus Automation Control")
        self.root.geometry("600x500")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize personal assistant
        self.pa = PersonalAssistantBuddy()
        
        # Status update thread
        self.status_thread = None
        self.is_running = True
        
        self._create_ui()
        self._start_status_updates()
        
    def _create_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Focus & Productivity Automation", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Current Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Status labels
        self.focus_status_label = ttk.Label(status_frame, text="Focus Mode: Inactive", 
                                          font=("Arial", 12))
        self.focus_status_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.night_status_label = ttk.Label(status_frame, text="Night Mode: Inactive", 
                                          font=("Arial", 12))
        self.night_status_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.intensity_label = ttk.Label(status_frame, text="Work Intensity: 0%", 
                                       font=("Arial", 12))
        self.intensity_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.duration_label = ttk.Label(status_frame, text="Focus Duration: 0 minutes", 
                                       font=("Arial", 12))
        self.duration_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        self.sites_label = ttk.Label(status_frame, text="Sites Blocked: 0", 
                                    font=("Arial", 12))
        self.sites_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        # Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Manual Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Control buttons
        self.focus_button = ttk.Button(control_frame, text="Toggle Focus Mode", 
                                      command=self._toggle_focus_mode)
        self.focus_button.grid(row=0, column=0, padx=(0, 10), pady=5)
        
        self.break_button = ttk.Button(control_frame, text="Trigger Break Reminder", 
                                      command=self._trigger_break)
        self.break_button.grid(row=0, column=1, padx=(0, 10), pady=5)
        
        self.night_button = ttk.Button(control_frame, text="Toggle Night Mode", 
                                      command=self._toggle_night_mode)
        self.night_button.grid(row=0, column=2, pady=5)
        
        # Auto-save Section
        autosave_frame = ttk.LabelFrame(main_frame, text="Auto-Save Work", padding="10")
        autosave_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.autosave_button = ttk.Button(autosave_frame, text="View Auto-Saved Work", 
                                         command=self._view_autosaved_work)
        self.autosave_button.grid(row=0, column=0, padx=(0, 10), pady=5)
        
        self.clear_button = ttk.Button(autosave_frame, text="Clear Auto-Save History", 
                                      command=self._clear_autosaved_work)
        self.clear_button.grid(row=0, column=1, pady=5)
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Configuration labels
        ttk.Label(config_frame, text="Focus Threshold: 30 minutes").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(config_frame, text="Break Interval: 25 minutes").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(config_frame, text="Night Mode: 8 PM - 7 AM").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(config_frame, text="Auto-Save: Every 5 minutes").grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # Info Section
        info_frame = ttk.LabelFrame(main_frame, text="How It Works", padding="10")
        info_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        info_text = """
🎯 Focus Mode: Automatically enabled after 30 minutes of coding
⚡ Break Reminders: Smart breaks based on work intensity
🌙 Night Mode: Auto-enabled after 8 PM, adjusts screen brightness
🚫 Distraction Blocking: Blocks social media during focus mode
💾 Auto-Save: Saves work when switching applications
        """
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.grid(row=0, column=0, sticky=tk.W)
        
    def _start_status_updates(self):
        """Start status update thread"""
        self.status_thread = threading.Thread(target=self._update_status_loop, daemon=True)
        self.status_thread.start()
    
    def _update_status_loop(self):
        """Update status labels continuously"""
        while self.is_running:
            try:
                status = self.pa.get_focus_status()
                
                # Update focus status
                focus_text = "Active" if status.get("focus_mode_active", False) else "Inactive"
                self.focus_status_label.config(text=f"Focus Mode: {focus_text}")
                
                # Update night mode status
                night_text = "Active" if status.get("night_mode_active", False) else "Inactive"
                self.night_status_label.config(text=f"Night Mode: {night_text}")
                
                # Update work intensity
                intensity = status.get("work_intensity_score", 0)
                intensity_percent = int(intensity * 100)
                self.intensity_label.config(text=f"Work Intensity: {intensity_percent}%")
                
                # Update focus duration
                duration = status.get("focus_duration_minutes", 0)
                self.duration_label.config(text=f"Focus Duration: {duration} minutes")
                
                # Update blocked sites
                sites = status.get("sites_blocked", 0)
                self.sites_label.config(text=f"Sites Blocked: {sites}")
                
                # Update button states
                if status.get("focus_mode_active", False):
                    self.focus_button.config(text="Disable Focus Mode")
                else:
                    self.focus_button.config(text="Enable Focus Mode")
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Status update error: {e}")
                time.sleep(5)
    
    def _toggle_focus_mode(self):
        """Toggle focus mode manually"""
        try:
            self.pa.toggle_focus_mode()
            messagebox.showinfo("Focus Mode", "Focus mode toggled!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle focus mode: {e}")
    
    def _trigger_break(self):
        """Trigger a break reminder manually"""
        try:
            self.pa.trigger_break_reminder()
            messagebox.showinfo("Break Reminder", "Break reminder triggered!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to trigger break: {e}")
    
    def _toggle_night_mode(self):
        """Toggle night mode manually"""
        try:
            if self.pa.is_night_mode_active():
                # Disable night mode
                self.pa.focus_automation._disable_night_mode()
            else:
                # Enable night mode
                self.pa.focus_automation._enable_night_mode()
            messagebox.showinfo("Night Mode", "Night mode toggled!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle night mode: {e}")
    
    def _view_autosaved_work(self):
        """View auto-saved work in a new window"""
        try:
            auto_saved = self.pa.get_auto_saved_work()
            
            if not auto_saved:
                messagebox.showinfo("Auto-Saved Work", "No auto-saved work found.")
                return
            
            # Create new window
            work_window = tk.Toplevel(self.root)
            work_window.title("Auto-Saved Work")
            work_window.geometry("800x600")
            
            # Create text widget
            text_widget = tk.Text(work_window, wrap=tk.WORD, padx=10, pady=10)
            scrollbar = ttk.Scrollbar(work_window, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            
            # Configure grid weights
            work_window.grid_rowconfigure(0, weight=1)
            work_window.grid_columnconfigure(0, weight=1)
            
            # Display auto-saved work
            for i, work in enumerate(auto_saved[-20:], 1):  # Show last 20 entries
                timestamp = work.get("timestamp", "")
                from_window = work.get("from_window", "")
                to_window = work.get("to_window", "")
                content = work.get("clipboard_content", "")
                
                text_widget.insert(tk.END, f"=== Entry {i} ===\n")
                text_widget.insert(tk.END, f"Time: {timestamp}\n")
                text_widget.insert(tk.END, f"From: {from_window}\n")
                text_widget.insert(tk.END, f"To: {to_window}\n")
                text_widget.insert(tk.END, f"Content:\n{content[:200]}...\n\n")
                text_widget.insert(tk.END, "-" * 50 + "\n\n")
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view auto-saved work: {e}")
    
    def _clear_autosaved_work(self):
        """Clear auto-saved work history"""
        try:
            result = messagebox.askyesno("Clear Auto-Save", 
                                       "Are you sure you want to clear all auto-saved work?")
            if result:
                self.pa.clear_auto_saved_work()
                messagebox.showinfo("Success", "Auto-saved work history cleared!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear auto-saved work: {e}")

class FocusControlWidget(QWidget):
    def __init__(self, pa_buddy):
        super().__init__()
        self.pa = pa_buddy
        self.init_ui()
        self.start_status_timer()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🎯 Focus & Productivity Automation")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Status group
        status_group = QGroupBox("Current Status")
        status_layout = QGridLayout()
        self.focus_status_label = QLabel("Focus Mode: Inactive")
        self.night_status_label = QLabel("Night Mode: Inactive")
        self.intensity_label = QLabel("Work Intensity: 0%")
        self.duration_label = QLabel("Focus Duration: 0 minutes")
        self.sites_label = QLabel("Sites Blocked: 0")
        status_layout.addWidget(self.focus_status_label, 0, 0)
        status_layout.addWidget(self.night_status_label, 1, 0)
        status_layout.addWidget(self.intensity_label, 2, 0)
        status_layout.addWidget(self.duration_label, 3, 0)
        status_layout.addWidget(self.sites_label, 4, 0)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Controls group
        controls_group = QGroupBox("Manual Controls")
        controls_layout = QHBoxLayout()
        self.focus_button = QPushButton("Toggle Focus Mode")
        self.focus_button.clicked.connect(self.toggle_focus_mode)
        self.break_button = QPushButton("Trigger Break Reminder")
        self.break_button.clicked.connect(self.trigger_break)
        self.night_button = QPushButton("Toggle Night Mode")
        self.night_button.clicked.connect(self.toggle_night_mode)
        controls_layout.addWidget(self.focus_button)
        controls_layout.addWidget(self.break_button)
        controls_layout.addWidget(self.night_button)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Auto-save group
        autosave_group = QGroupBox("Auto-Save Work")
        autosave_layout = QHBoxLayout()
        self.autosave_button = QPushButton("View Auto-Saved Work")
        self.autosave_button.clicked.connect(self.view_autosaved_work)
        self.clear_button = QPushButton("Clear Auto-Save History")
        self.clear_button.clicked.connect(self.clear_autosaved_work)
        autosave_layout.addWidget(self.autosave_button)
        autosave_layout.addWidget(self.clear_button)
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)

        # Info group
        info_group = QGroupBox("How It Works")
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setPlainText(
            """
🎯 Focus Mode: Automatically enabled after 30 minutes of coding
⚡ Break Reminders: Smart breaks based on work intensity
🌙 Night Mode: Auto-enabled after 8 PM, adjusts screen brightness
🚫 Distraction Blocking: Blocks social media during focus mode
💾 Auto-Save: Saves work when switching applications
            """
        )
        info_group_layout = QVBoxLayout()
        info_group_layout.addWidget(info_text)
        info_group.setLayout(info_group_layout)
        layout.addWidget(info_group)

        self.setLayout(layout)

    def start_status_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(2000)
        self.update_status()

    def update_status(self):
        status = self.pa.get_focus_status()
        focus_text = "Active" if status.get("focus_mode_active", False) else "Inactive"
        self.focus_status_label.setText(f"Focus Mode: {focus_text}")
        night_text = "Active" if status.get("night_mode_active", False) else "Inactive"
        self.night_status_label.setText(f"Night Mode: {night_text}")
        intensity = status.get("work_intensity_score", 0)
        intensity_percent = int(intensity * 100)
        self.intensity_label.setText(f"Work Intensity: {intensity_percent}%")
        duration = status.get("focus_duration_minutes", 0)
        self.duration_label.setText(f"Focus Duration: {duration} minutes")
        sites = status.get("sites_blocked", 0)
        self.sites_label.setText(f"Sites Blocked: {sites}")
        if status.get("focus_mode_active", False):
            self.focus_button.setText("Disable Focus Mode")
        else:
            self.focus_button.setText("Enable Focus Mode")

    def toggle_focus_mode(self):
        try:
            self.pa.toggle_focus_mode()
            QMessageBox.information(self, "Focus Mode", "Focus mode toggled!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle focus mode: {e}")

    def trigger_break(self):
        try:
            self.pa.trigger_break_reminder()
            QMessageBox.information(self, "Break Reminder", "Break reminder triggered!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to trigger break: {e}")

    def toggle_night_mode(self):
        try:
            if self.pa.is_night_mode_active():
                self.pa.focus_automation._disable_night_mode()
            else:
                self.pa.focus_automation._enable_night_mode()
            QMessageBox.information(self, "Night Mode", "Night mode toggled!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle night mode: {e}")

    def view_autosaved_work(self):
        try:
            auto_saved = self.pa.get_auto_saved_work()
            if not auto_saved:
                QMessageBox.information(self, "Auto-Saved Work", "No auto-saved work found.")
                return
            text = "\n\n".join([json.dumps(entry, indent=2) for entry in auto_saved])
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Auto-Saved Work")
            dlg.setTextInteractionFlags(Qt.TextSelectableByMouse)
            dlg.setText(text)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to view auto-saved work: {e}")

    def clear_autosaved_work(self):
        try:
            self.pa.clear_auto_saved_work()
            QMessageBox.information(self, "Auto-Save", "Auto-save history cleared!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear auto-save history: {e}")
    
    def run(self):
        """Run the UI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("UI closed by user")
        finally:
            self.is_running = False

if __name__ == "__main__":
    app = FocusControlUI()
    app.run() 