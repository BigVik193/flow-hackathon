"""
Main Window Module
==================

Main application window with GUI layout and event handling.

Author: AI Assistant
"""

import threading
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFrame, QMessageBox, QScrollArea
)
from PySide6.QtCore import QTimer, Qt, Signal, QObject, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QFont, QColor, QLinearGradient, QPalette, QPainter, QBrush, QPen, QPixmap

from gui_components import StatusIndicator, ModernCard, ActivityIndicator, ChatBubbleWidget, ResponseWidget
from voice_recognition import SpeechRecognitionThread
from backend_service import BackendService
from macos_integration import MacOSIntegration
import requests
import tempfile
import threading
import pygame
import os


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signal for backend response
    backend_response_received = Signal(dict)
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.backend_service = BackendService(backend_url)
        self.macos_integration = MacOSIntegration(self)
        self.speech_thread = None
        self.session_id = None
        self.pulse_animation = None
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            self.audio_available = True
            print("✅ Pygame mixer initialized for audio playback")
        except Exception as e:
            print(f"⚠️ Audio playback not available: {e}")
            self.audio_available = False
        
        # Setup UI
        self.setup_ui()
        self.setup_speech_recognition()
        
        # Connect backend response signal
        self.backend_response_received.connect(self.handle_backend_response)
        
        # Check backend connection
        self.check_backend_connection()
        
        # Start speech recognition
        self.start_speech_recognition()
    
    def setup_ui(self):
        """Setup sleek modern UI matching the reference screenshots"""
        self.setWindowTitle("Flow")
        
        # Set initial compact window size
        self.compact_height = 165
        self.expanded_height = 400
        self.window_width = 580
        
        self.resize(self.window_width, self.compact_height)
        self.setMinimumSize(self.window_width, self.compact_height)
        self.setMaximumSize(self.window_width, self.expanded_height)
        
        # Window resize animation
        self.resize_animation = QPropertyAnimation(self, b"size")
        self.resize_animation.setDuration(300)
        self.resize_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Apply modern gradient background
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E8F4FD, stop:1 #F0F8FF);
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with precise spacing like reference
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 30, 20, 30)
        
        # Keep minimal status indicators (hidden but functional)
        self.wake_word_indicator = StatusIndicator(QColor(128, 128, 128))
        self.voice_indicator = StatusIndicator(QColor(100, 149, 237))
        self.backend_indicator = StatusIndicator(QColor(128, 128, 128))
        self.status_label = QLabel()
        
        # Chat bubble container - this is the main UI element
        self.chat_bubble = ChatBubbleWidget()
        layout.addWidget(self.chat_bubble)
        
        # Spacing between chat bubble and response
        layout.addSpacing(20)
        
        # Response area with copy functionality (initially hidden)
        self.response_container = ResponseWidget()
        self.response_container.setVisible(False)
        layout.addWidget(self.response_container)
        
        # Stretch to push everything up
        layout.addStretch()
        
        # Store references for compatibility
        self.activity_indicator = self.chat_bubble.activity_indicator
        self.command_input = self.chat_bubble.command_input
        self.response_display = self.response_container.response_display
    
    def setup_input_styling(self):
        """Setup input field styling - now handled by ChatBubbleWidget"""
        # Input styling is now handled by the ChatBubbleWidget
        pass
    
    def start_processing_animation(self):
        """Start processing animation on the Whisper icon"""
        self.activity_indicator.set_state("processing")
    
    def stop_processing_animation(self):
        """Stop processing animation"""
        # Animation state will be updated by activity indicator methods
        pass
    
    def setup_speech_recognition(self):
        """Setup speech recognition thread"""
        self.speech_thread = SpeechRecognitionThread()
        
        # Connect signals
        self.speech_thread.wake_word_detected.connect(self.handle_wake_word_command)
        self.speech_thread.dictation_detected.connect(self.handle_dictation)
        self.speech_thread.status_changed.connect(self.update_status)
        self.speech_thread.error_occurred.connect(self.handle_error)
        self.speech_thread.user_speaking.connect(self.handle_user_speaking)
    
    def start_speech_recognition(self):
        """Start the speech recognition thread"""
        if self.speech_thread and not self.speech_thread.isRunning():
            print("🎤 Starting speech recognition...")
            self.speech_thread.start()
            
            # Update indicators
            self.wake_word_indicator.set_color(QColor(34, 139, 34))  # Green
            self.voice_indicator.set_color(QColor(100, 149, 237))   # Blue
            
            # Set activity indicator to listening state
            self.activity_indicator.set_state("listening")
    
    def stop_speech_recognition(self):
        """Stop the speech recognition thread"""
        if self.speech_thread and self.speech_thread.isRunning():
            print("🛑 Stopping speech recognition...")
            self.speech_thread.stop()
            self.speech_thread.wait(3000)  # Wait up to 3 seconds
            
            # Update indicators
            self.wake_word_indicator.set_color(QColor(128, 128, 128))  # Gray
            self.voice_indicator.set_color(QColor(128, 128, 128))     # Gray
            
            # Set activity indicator to idle state
            self.activity_indicator.set_state("idle")
    
    def check_backend_connection(self):
        """Check backend connection and update indicator"""
        if self.backend_service.check_health():
            self.backend_indicator.set_color(QColor(34, 139, 34))  # Green
            print("✅ Backend connection healthy")
        else:
            self.backend_indicator.set_color(QColor(220, 20, 60))   # Crimson
            print("❌ Backend connection failed")
    
    def handle_wake_word_command(self, command: str):
        """Handle command from wake word detection"""
        print(f"🎯 Processing wake word command: {command}")
        
        # Bring app to front and focus
        self.macos_integration.bring_to_front()
        
        # Set command in input field
        self.command_input.setPlainText(command)
        
        # Execute command
        self.execute_command_with_backend(command)
    
    def handle_dictation(self, text: str):
        """Handle dictation from Orange wake word"""
        print(f"🍊 Processing orange dictation: {text}")
        
        # Insert text at current cursor position using macOS APIs
        self.macos_integration.insert_text_at_cursor(text + " ")
    
    def handle_user_speaking(self, is_speaking: bool):
        """Handle user speaking state for animation"""
        if is_speaking:
            print("🎤 User is speaking")
            self.activity_indicator.set_state("user_speaking")
        else:
            print("🔇 User stopped speaking")
            self.activity_indicator.set_state("listening")
    
    def execute_current_command(self):
        """Execute the command in the input field (removed button, keeping for compatibility)"""
        pass
    
    def execute_command_with_backend(self, command: str):
        """Execute command with backend API"""
        if not command.strip():
            return
            
        print(f"🚀 Executing command: {command}")
        
        # Start processing animation
        self.start_processing_animation()
        
        # Notify speech thread we're processing
        if self.speech_thread:
            self.speech_thread.set_backend_processing(True)
        
        # Execute in background thread to avoid blocking UI
        def execute():
            try:
                response = self.backend_service.execute_command(command, self.session_id)
                print(f"🔄 Thread received response: {response}")
                
                # Emit signal to update UI on main thread
                print(f"🔄 Emitting backend_response_received signal")
                self.backend_response_received.emit(response)
                
            except Exception as e:
                print(f"❌ Exception in background thread: {e}")
                error_response = {
                    "status": "error",
                    "message": f"Execution error: {e}",
                    "agent_type": "error"
                }
                
                print(f"🔄 Emitting error response signal")
                self.activity_indicator.set_state("error")
                QTimer.singleShot(2000, lambda: self.activity_indicator.set_state("listening"))
                self.backend_response_received.emit(error_response)
        
        # Run in thread
        threading.Thread(target=execute, daemon=True).start()
    
    def handle_backend_response(self, response: Dict[str, Any]):
        """Handle response from backend"""
        try:
            print(f"🔍 Handling backend response: {response}")
            
            message = response.get("message", "No response")
            agent_type = response.get("agent_type", "unknown")
            status = response.get("status", "unknown")
            
            print(f"📝 Extracted message: '{message}'")
            print(f"📝 Status: '{status}', Agent type: '{agent_type}'")
            
            # Update response display and expand window
            self.response_container.show_response(message)
            self.expand_window()
            print(f"🖥️ Updated response display with: {message}")
            
            # Play audio from backend if available
            audio_url = response.get("audio_url")
            if audio_url:
                print(f"🔊 Playing audio from backend: {audio_url}")
                self._play_audio_from_url(audio_url)
            else:
                print("⚠️ No audio URL provided by backend")
                # If no audio, return to listening state immediately
                QTimer.singleShot(1000, lambda: self.activity_indicator.set_state("listening"))
            
            # Stop processing animation and return to listening (audio will handle green state)
            self.stop_processing_animation()
            self.activity_indicator.set_state("listening")
            
            # Clear command input
            self.command_input.clear()
            
            # Return to listening state will be handled by audio playback completion
            # or immediately if no audio is played
            
            # Restore original app focus after delay (wait longer for TTS to finish)
            QTimer.singleShot(3000, self.macos_integration.restore_original_app)
            
            # Window collapse will be handled after audio completion
            # or immediately if no audio is played
            if not audio_url:
                QTimer.singleShot(8000, self.collapse_window)
            
            print(f"✅ Command completed: {message}")
            
        except Exception as e:
            print(f"❌ Error in handle_backend_response: {e}")
            print(f"❌ Response data: {response}")
        finally:
            # Re-enable speech recognition
            if self.speech_thread:
                self.speech_thread.set_backend_processing(False)
    
    def _play_audio_from_url(self, audio_url: str):
        """Download and play audio from URL"""
        if not self.audio_available:
            print("⚠️ Audio playback not available")
            return
            
        if not audio_url or not audio_url.strip():
            print("⚠️ Empty or invalid audio URL")
            return
            
        def play_audio():
            temp_file_path = None
            try:
                print(f"🎵 Downloading audio from: {audio_url}")
                
                # Add headers for better compatibility with MiniMax URLs
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                # Download audio file
                response = requests.get(audio_url, timeout=30, headers=headers)
                if response.status_code == 200:
                    # Determine file extension based on content type or URL
                    content_type = response.headers.get('content-type', '').lower()
                    if 'audio/mpeg' in content_type or audio_url.endswith('.mp3'):
                        suffix = '.mp3'
                    elif 'audio/wav' in content_type or audio_url.endswith('.wav'):
                        suffix = '.wav'
                    else:
                        suffix = '.mp3'  # Default to mp3
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_file.write(response.content)
                        temp_file_path = temp_file.name
                    
                    print(f"🎵 Playing audio file: {temp_file_path}")
                    
                    # Play audio using pygame
                    pygame.mixer.music.load(temp_file_path)
                    pygame.mixer.music.play()
                    
                    print("🎵 Audio playback started - setting green animation and disabling speech recognition")
                    # Set agent speaking animation when audio starts
                    self.activity_indicator.set_state("agent_speaking")
                    
                    # Disable speech recognition while agent is speaking
                    if self.speech_thread:
                        self.speech_thread.set_backend_processing(True)
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    
                    print("🎵 Audio playback completed - returning to blue animation and re-enabling speech recognition")
                    # Return to listening state when audio actually completes
                    self.activity_indicator.set_state("listening")
                    
                    # Re-enable speech recognition after agent finishes speaking
                    if self.speech_thread:
                        self.speech_thread.set_backend_processing(False)
                    
                    # Schedule window collapse 10 seconds after audio completes
                    QTimer.singleShot(10000, self.collapse_window)
                    print("✅ Audio playback completed")
                    
                else:
                    print(f"❌ Failed to download audio: HTTP {response.status_code}")
                    print(f"Response headers: {dict(response.headers)}")
                    
            except requests.exceptions.Timeout:
                print("❌ Timeout downloading audio file")
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error downloading audio: {e}")
            except Exception as e:
                print(f"❌ Error playing audio: {e}")
            finally:
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        print("🗑️ Cleaned up temporary audio file")
                    except Exception as e:
                        print(f"⚠️ Failed to clean up temp file: {e}")
        
        # Play audio in background thread
        threading.Thread(target=play_audio, daemon=True).start()
    
    def update_status(self, status: str):
        """Update status label with modern styling"""
        self.status_label.setText(status)
        
        # Add different styling based on status type
        if "error" in status.lower() or "failed" in status.lower():
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #DC2626;
                    padding: 8px 16px;
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 12px;
                }
            """)
        elif "completed" in status.lower() or "✅" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #059669;
                    padding: 8px 16px;
                    background-color: #ECFDF5;
                    border: 1px solid #A7F3D0;
                    border-radius: 12px;
                }
            """)
        elif "processing" in status.lower() or "listening" in status.lower():
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #2563EB;
                    padding: 8px 16px;
                    background-color: #EFF6FF;
                    border: 1px solid #BFDBFE;
                    border-radius: 12px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #374151;
                    padding: 8px 16px;
                    background-color: #F3F4F6;
                    border-radius: 12px;
                }
            """)
    
    def expand_window(self):
        """Expand window to show response area"""
        if self.height() == self.compact_height:
            self.resize_animation.setStartValue(self.size())
            self.resize_animation.setEndValue(QSize(self.window_width, self.expanded_height))
            self.resize_animation.start()
    
    def collapse_window(self):
        """Collapse window back to compact size"""
        if self.height() == self.expanded_height:
            self.response_container.hide_response()
            self.resize_animation.setStartValue(self.size())
            self.resize_animation.setEndValue(QSize(self.window_width, self.compact_height))
            self.resize_animation.start()
    
    def handle_error(self, error: str):
        """Handle errors from speech recognition"""
        print(f"❌ Speech recognition error: {error}")
        self.update_status(f"Error: {error}")
        
        # Show error state on activity indicator
        self.activity_indicator.set_state("error")
        
        # Return to listening state after error display
        QTimer.singleShot(3000, lambda: self.activity_indicator.set_state("listening"))
        
        # Show error dialog
        QMessageBox.warning(self, "Error", f"Speech recognition error:\n{error}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        print("🔄 Shutting down...")
        
        # Stop speech recognition
        self.stop_speech_recognition()
        
        # Stop any ongoing audio playback
        if self.audio_available:
            try:
                pygame.mixer.music.stop()
                print("🔇 Audio playback stopped")
            except Exception as e:
                print(f"❌ Error stopping audio: {e}")
        
        # Force cleanup
        if hasattr(self, 'speech_thread') and self.speech_thread:
            self.speech_thread.terminate()
            self.speech_thread.wait(2000)
        
        event.accept()