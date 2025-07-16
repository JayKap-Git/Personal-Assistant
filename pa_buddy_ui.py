import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QMessageBox,
    QGroupBox, QScrollArea, QFrame, QSplitter, QSizePolicy, QSpacerItem, QTabWidget
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QTextCursor, QPalette, QColor, QPixmap, QIcon
import json
import os
import re
import threading
import time
from subprocess import run
from buddies.personal_assistant import PersonalAssistantBuddy
from focus_control_ui import FocusControlWidget

OUTPUT_FILE = "output/prediction_output.json"
REFRESH_INTERVAL = 3000  # ms

# Modern color scheme
COLORS = {
    'primary': '#2196F3',
    'secondary': '#FF9800',
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336',
    'dark_bg': '#2C3E50',
    'light_bg': '#ECF0F1',
    'text_primary': '#2C3E50',
    'text_secondary': '#7F8C8D',
    'border': '#BDC3C7'
}

class ChatbotThread(QThread):
    """Thread for chatbot monitoring"""
    message_received = pyqtSignal(str, str)  # speaker, message
    
    def __init__(self, pa_buddy):
        super().__init__()
        self.pa_buddy = pa_buddy
        self.running = False
    
    def run(self):
        self.running = True
        self.pa_buddy.start_chatbot()
        
        # Monitor for chatbot messages
        while self.running:
            time.sleep(1)
    
    def stop(self):
        self.running = False
        self.pa_buddy.stop_chatbot()

class ModernButton(QPushButton):
    """Custom styled button"""
    def __init__(self, text, color=COLORS['primary'], icon=None):
        super().__init__(text)
        self.setMinimumWidth(180)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 16px 32px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {self._adjust_color(color, -20)};
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color(color, -40)};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['text_secondary']};
                color: {COLORS['light_bg']};
            }}
        """)
        if icon:
            self.setIcon(icon)
    
    def _adjust_color(self, color, amount):
        """Adjust color brightness"""
        # Simple color adjustment - in production you'd want a proper color library
        return color

class ModernLineEdit(QLineEdit):
    """Custom styled line edit"""
    def __init__(self, placeholder="", color=COLORS['primary']):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 16px;
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {color};
                background-color: #FAFAFA;
            }}
        """)

class ModernTextEdit(QTextEdit):
    """Custom styled text edit"""
    def __init__(self, read_only=True):
        super().__init__()
        self.setReadOnly(read_only)
        self.setStyleSheet(f"""
            QTextEdit {{
                padding: 12px;
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: white;
                color: {COLORS['text_primary']};
                line-height: 1.4;
            }}
        """)

class ModernGroupBox(QGroupBox):
    """Custom styled group box"""
    def __init__(self, title, color=COLORS['primary']):
        super().__init__(title)
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 16px;
                color: {color};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: white;
            }}
        """)

class PABuddyUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 Personal Assistant Buddy - Activity Monitor & Chatbot")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['light_bg']};
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        
        # Initialize PA Buddy
        self.pa_buddy = PersonalAssistantBuddy()
        
        # Chatbot thread
        self.chatbot_thread = ChatbotThread(self.pa_buddy)
        self.chatbot_thread.message_received.connect(self.add_chat_message)
        
        # UI Elements
        self.setup_ui_elements()
        self.init_ui()
        
        # Timer for activity refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_activity)
        self.timer.start(REFRESH_INTERVAL)
        self.refresh_activity()
        
        # Start chatbot
        self.start_chatbot()

    def setup_ui_elements(self):
        """Setup all UI elements with modern styling"""
        # Activity monitoring
        self.activity_label = QTextEdit()
        self.activity_label.setReadOnly(True)
        self.activity_label.setMinimumHeight(300)
        self.activity_label.setMaximumHeight(400)
        self.activity_label.setStyleSheet(f"""
            QTextEdit {{
                padding: 16px;
                background-color: white;
                border-radius: 8px;
                border: 1px solid {COLORS['border']};
                font-size: 14px;
                line-height: 1.5;
            }}
        """)
        
        # Meeting scheduling
        self.meeting_input = ModernLineEdit("Enter meeting details (e.g., 'Team meeting tomorrow at 2pm')", COLORS['success'])
        self.schedule_meeting_btn = ModernButton("📅 Schedule Meeting", COLORS['success'])
        self.schedule_meeting_btn.clicked.connect(self.handle_meeting_schedule)
        
        # Chatbot elements
        self.chat_display = ModernTextEdit()
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setMaximumHeight(400)
        
        self.chat_input = ModernLineEdit("💬 Chat with Chatbot Buddy...", COLORS['primary'])
        self.chat_input.returnPressed.connect(self.send_chat_message)
        
        self.chat_send_btn = ModernButton("Send", COLORS['primary'])
        self.chat_send_btn.clicked.connect(self.send_chat_message)
        
        # Control buttons
        self.joke_btn = ModernButton("😄 Tell Joke", COLORS['secondary'])
        self.joke_btn.clicked.connect(self.tell_joke)
        
        self.chatbot_status_btn = ModernButton("📊 Status", COLORS['warning'])
        self.chatbot_status_btn.clicked.connect(self.show_chatbot_status)
        
        self.reset_session_btn = ModernButton("🔄 Reset Session", COLORS['error'])
        self.reset_session_btn.clicked.connect(self.reset_work_session)

    def init_ui(self):
        """Initialize the main UI layout with tabs"""
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.North)
        tab_widget.setMovable(False)
        tab_widget.setDocumentMode(True)
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLORS['border']}; border-radius: 8px; }}
            QTabBar::tab {{ background: {COLORS['light_bg']}; color: {COLORS['primary']}; font-weight: bold; padding: 16px 36px; min-width: 160px; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
            QTabBar::tab:selected {{ background: {COLORS['primary']}; color: white; }}
        """)

        # PA Buddy tab (existing UI)
        pa_buddy_tab = QWidget()
        pa_buddy_layout = QHBoxLayout()
        # Left panel - Activity and Meeting
        left_panel = QVBoxLayout()
        activity_group = ModernGroupBox("📊 Activity Monitor", COLORS['primary'])
        activity_layout = QVBoxLayout()
        activity_layout.addWidget(self.activity_label)
        activity_group.setLayout(activity_layout)
        left_panel.addWidget(activity_group)
        meeting_group = ModernGroupBox("📅 Meeting Scheduler", COLORS['success'])
        meeting_layout = QVBoxLayout()
        meeting_info = QLabel("Schedule meetings by entering natural language details below:")
        meeting_info.setStyleSheet(f"QLabel {{ color: {COLORS['text_secondary']}; font-size: 13px; margin-bottom: 8px; }}")
        meeting_info.setWordWrap(True)
        meeting_layout.addWidget(meeting_info)
        meeting_layout.addWidget(self.meeting_input)
        meeting_layout.addWidget(self.schedule_meeting_btn)
        meeting_group.setLayout(meeting_layout)
        left_panel.addWidget(meeting_group)
        left_panel.addStretch()
        # Right panel - Chatbot
        right_panel = QVBoxLayout()
        chatbot_group = ModernGroupBox("🤖 Chatbot Buddy (Activity Aware)", COLORS['primary'])
        chatbot_layout = QVBoxLayout()
        activity_info = QLabel("💡 Chatbot Buddy has access to your current activity data and can provide contextual responses!")
        activity_info.setStyleSheet(f"""
            QLabel {{ 
                color: {COLORS['primary']}; 
                font-weight: bold; 
                font-size: 13px;
                padding: 8px;
                background-color: rgba(33, 150, 243, 0.1);
                border-radius: 6px;
                margin-bottom: 8px;
            }}
        """)
        activity_info.setWordWrap(True)
        chatbot_layout.addWidget(activity_info)
        chat_label = QLabel("💬 Conversation:")
        chat_label.setStyleSheet(f"QLabel {{ font-weight: bold; font-size: 14px; margin-bottom: 4px; }}")
        chatbot_layout.addWidget(chat_label)
        chatbot_layout.addWidget(self.chat_display)
        chat_input_layout = QHBoxLayout()
        chat_input_layout.addWidget(self.chat_input, 4)
        chat_input_layout.addWidget(self.chat_send_btn, 1)
        chatbot_layout.addLayout(chat_input_layout)
        chatbot_controls_layout = QHBoxLayout()
        chatbot_controls_layout.addWidget(self.joke_btn)
        chatbot_controls_layout.addWidget(self.chatbot_status_btn)
        chatbot_controls_layout.addWidget(self.reset_session_btn)
        chatbot_layout.addLayout(chatbot_controls_layout)
        chatbot_group.setLayout(chatbot_layout)
        right_panel.addWidget(chatbot_group)
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(500)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 550])
        main_layout = QHBoxLayout()
        main_layout.addSpacing(24)  # Add space below nav bar
        main_layout.addWidget(splitter)
        pa_buddy_tab.setLayout(main_layout)

        # Focus Control tab
        focus_control_tab = FocusControlWidget(self.pa_buddy)

        # Add tabs
        tab_widget.addTab(pa_buddy_tab, "PA Buddy")
        tab_widget.addTab(focus_control_tab, "Focus Control")

        # Set main layout
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(tab_widget)
        self.setLayout(outer_layout)

    def start_chatbot(self):
        """Start the chatbot thread"""
        if not self.chatbot_thread.isRunning():
            self.chatbot_thread.start()
            self.add_chat_message("system", "🤖 Chatbot Buddy is now active and monitoring your work sessions!")

    def stop_chatbot(self):
        """Stop the chatbot thread"""
        if self.chatbot_thread.isRunning():
            self.chatbot_thread.stop()
            self.chatbot_thread.wait()

    def add_chat_message(self, speaker, message):
        """Add a message to the chat display with enhanced formatting"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Add a line break before new message if not at the beginning
        if self.chat_display.toPlainText():
            cursor.insertHtml('<br>')
        
        # Enhanced message formatting
        timestamp = time.strftime("%H:%M")
        
        if speaker == "user":
            formatted_message = f'<div style="margin: 12px 0; padding: 12px 16px; background-color: #E3F2FD; border-radius: 8px; border-left: 4px solid #2196F3; margin-left: 20px;">'
            formatted_message += f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            formatted_message += f'<span style="font-weight: bold; color: #1976D2; font-size: 14px;">👤 You</span>'
            formatted_message += f'<span style="color: #666; font-size: 11px;">{timestamp}</span>'
            formatted_message += f'</div>'
            formatted_message += f'<div style="color: #2C3E50; font-size: 14px; line-height: 1.4;">{message}</div></div>'
        elif speaker == "bot":
            formatted_message = f'<div style="margin: 12px 0; padding: 12px 16px; background-color: #F3E5F5; border-radius: 8px; border-left: 4px solid #9C27B0; margin-right: 20px;">'
            formatted_message += f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            formatted_message += f'<span style="font-weight: bold; color: #7B1FA2; font-size: 14px;">🤖 Chatbot Buddy</span>'
            formatted_message += f'<span style="font-size: 11px; color: #666;">{timestamp}</span>'
            formatted_message += f'</div>'
            formatted_message += f'<div style="color: #2C3E50; font-size: 14px; line-height: 1.4;">{message}</div></div>'
        else:
            formatted_message = f'<div style="margin: 12px 0; padding: 12px 16px; background-color: #FFF3E0; border-radius: 8px; border-left: 4px solid #FF9800; text-align: center;">'
            formatted_message += f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            formatted_message += f'<span style="font-weight: bold; color: #E65100; font-size: 14px;">💬 System</span>'
            formatted_message += f'<span style="color: #666; font-size: 11px;">{timestamp}</span>'
            formatted_message += f'</div>'
            formatted_message += f'<div style="color: #2C3E50; font-size: 14px; line-height: 1.4;">{message}</div></div>'
        
        cursor.insertHtml(formatted_message)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def send_chat_message(self):
        """Send a message to the chatbot"""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Add user message to display
        self.add_chat_message("user", message)
        self.chat_input.clear()
        
        # Disable send button temporarily
        self.chat_send_btn.setEnabled(False)
        self.chat_send_btn.setText("Sending...")
        
        # Send to chatbot in a separate thread
        threading.Thread(target=self._send_chat_message_thread, args=(message,)).start()

    def _send_chat_message_thread(self, message):
        """Thread for sending chat message"""
        try:
            response = self.pa_buddy.chat_with_user(message)
            # Emit signal to update UI from main thread
            self.chatbot_thread.message_received.emit("bot", response)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.chatbot_thread.message_received.emit("system", error_msg)
        finally:
            # Re-enable send button
            self.chat_send_btn.setEnabled(True)
            self.chat_send_btn.setText("Send")

    def tell_joke(self):
        """Tell a joke via chatbot"""
        self.joke_btn.setEnabled(False)
        self.joke_btn.setText("Loading...")
        threading.Thread(target=self._tell_joke_thread).start()

    def _tell_joke_thread(self):
        """Thread for telling joke"""
        try:
            joke = self.pa_buddy.tell_joke()
            self.chatbot_thread.message_received.emit("bot", joke)
        except Exception as e:
            error_msg = f"Error telling joke: {str(e)}"
            self.chatbot_thread.message_received.emit("system", error_msg)
        finally:
            self.joke_btn.setEnabled(True)
            self.joke_btn.setText("😄 Tell Joke")

    def show_chatbot_status(self):
        """Show chatbot status"""
        try:
            status = self.pa_buddy.get_chatbot_status()
            status_text = f"""
🤖 <b>Chatbot Status</b>

✅ Active: {status['active']}
⏰ Work Start: {status['work_start_time']}
💬 Last Interaction: {status['last_interaction']}
📊 Conversation Count: {status['conversation_count']}
            """
            
            msg = QMessageBox()
            msg.setWindowTitle("Chatbot Status")
            msg.setText(status_text)
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {COLORS['light_bg']};
                }}
                QMessageBox QLabel {{
                    color: {COLORS['text_primary']};
                    font-size: 14px;
                }}
            """)
            msg.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error getting status: {str(e)}")

    def reset_work_session(self):
        """Reset the work session"""
        try:
            self.pa_buddy.reset_chatbot_session()
            self.add_chat_message("system", "🔄 Work session reset successfully!")
        except Exception as e:
            self.add_chat_message("system", f"Error resetting session: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event"""
        self.stop_chatbot()
        event.accept()

    def refresh_activity(self):
        """Refresh activity display with enhanced formatting"""
        try:
            with open(OUTPUT_FILE, "r") as f:
                activity = json.load(f)
            
            desc = activity.get("description", "No activity detected")
            details = activity.get("details", "")
            confidence = activity.get("confidence", "")
            
            # Enhanced activity display
            activity_html = f"""
<div style="padding: 16px; background: linear-gradient(135deg, #E3F2FD 0%, #F3E5F5 100%); color: #2C3E50; border-radius: 8px; border: 2px solid #2196F3;">
    <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px; color: #1976D2;">🎯 Current Activity</div>
    <div style="font-size: 16px; margin-bottom: 12px; color: #2C3E50;">{desc}</div>
    <div style="font-size: 13px; color: #34495E;">
        <div><strong>Details:</strong> {details}</div>
        <div><strong>Confidence:</strong> {confidence}</div>
    </div>
</div>
            """
            
            self.activity_label.setHtml(activity_html)
        except Exception as e:
            error_html = f"""
<div style="padding: 16px; background-color: #FFEBEE; border: 1px solid #F44336; border-radius: 8px; color: #C62828;">
    <div style="font-weight: bold;">⚠️ Error Reading Activity</div>
    <div style="font-size: 13px;">{str(e)}</div>
</div>
            """
            self.activity_label.setHtml(error_html)

    def handle_meeting_schedule(self):
        """Handle meeting scheduling from user input"""
        meeting_text = self.meeting_input.text().strip()
        if not meeting_text:
            QMessageBox.warning(self, "Input Required", "Please enter meeting details to schedule.")
            return
        
        # Add to chat display
        self.add_chat_message("user", f"📅 Scheduling: {meeting_text}")
        
        # Show processing message
        self.add_chat_message("system", "🔄 Processing meeting details with AI...")
        
        # Disable button during processing
        self.schedule_meeting_btn.setEnabled(False)
        self.schedule_meeting_btn.setText("Processing...")
        
        # Process in background thread
        threading.Thread(target=self._schedule_meeting_thread, args=(meeting_text,)).start()
        
        # Clear input
        self.meeting_input.clear()

    def _schedule_meeting_thread(self, meeting_text):
        """Thread for scheduling meeting via LLM and CLI with simplified feedback"""
        try:
            # Show processing message
            self.chatbot_thread.message_received.emit("system", "🔄 Generating AppleScript for calendar event...")
            
            # Schedule meeting using simplified approach
            success = self.pa_buddy.schedule_meeting_from_user_input(meeting_text)
            
            if success:
                result_msg = f"✅ Meeting scheduled successfully!\n\n📅 {meeting_text}\n📆 Added to Work calendar"
            else:
                result_msg = f"❌ Failed to schedule meeting: {meeting_text}\n\n💡 Please check your calendar application or try again."
            
            # Update UI from main thread
            self.chatbot_thread.message_received.emit("system", result_msg)
            
        except Exception as e:
            error_msg = f"❌ Error scheduling meeting: {str(e)}"
            self.chatbot_thread.message_received.emit("system", error_msg)
        finally:
            # Re-enable button
            self.schedule_meeting_btn.setEnabled(True)
            self.schedule_meeting_btn.setText("📅 Schedule Meeting")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = PABuddyUI()
    window.show()
    sys.exit(app.exec_()) 