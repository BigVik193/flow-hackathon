"""
Speech Recognition Module
========================

Handles real-time wake word detection and speech recognition using:
- Gladia for continuous real-time speech transcription and wake word detection
- Wake words: "Hey Flow" (commands) and "Scribe Write" (dictation)

Author: AI Assistant
"""

import time
import threading
import re
from typing import Optional
from PySide6.QtCore import QThread, Signal, QObject

# Gladia transcription imports
try:
    from gladia_transcription import GladiaTranscription
    import os
    GLADIA_AVAILABLE = bool(os.getenv('GLADIA_API_KEY'))
    if GLADIA_AVAILABLE:
        print("✅ Gladia transcription loaded successfully")
    else:
        print("⚠️ Gladia API key not found in environment variables")
        GLADIA_AVAILABLE = False
except ImportError as e:
    print(f"❌ Gladia transcription not available: {e}")
    GLADIA_AVAILABLE = False


class SpeechRecognitionThread(QThread):
    """Simplified background thread using only Gladia for continuous speech recognition"""
    
    # Signals to communicate with main thread
    wake_word_detected = Signal(str)  # Command after "Hey Flow"
    dictation_detected = Signal(str)  # Text after "Scribe Write"
    status_changed = Signal(str)  # Status updates
    error_occurred = Signal(str)  # Error messages
    user_speaking = Signal(bool)  # True when user is speaking, False when silent
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.is_processing_backend = False
        self.gladia_transcriber = None
        self.current_text_buffer = ""
        self.waiting_for_command = False
        self.waiting_for_dictation = False
        self.wake_word_detected_time = None
        
        # Wake word patterns - more flexible with punctuation
        self.flow_patterns = [
            r'\bhey[,!]?\s+flow\b',
            r'\bhey[,!]?\s+flo\b', 
            r'\bhay[,!]?\s+flow\b',
            r'\bhay[,!]?\s+flo\b',
            r'\bheyflow\b',
            r'\bhayflo\b'
        ]
        
        self.scribe_patterns = [
            r'\bscribe[,!]?\s+write\b',
            r'\bscribe[,!]?\s+right\b',  # Common mishearing
            r'\bscribe[,!]?\s+type\b',
            r'\bscribewrite\b',
            r'\bscribetype\b'
        ]
        
    def setup_gladia_transcription(self):
        """Initialize Gladia transcription for continuous listening"""
        if not GLADIA_AVAILABLE:
            print("❌ Gladia not available")
            return False
            
        try:
            self.gladia_transcriber = GladiaTranscription(os.getenv('GLADIA_API_KEY'))
            
            # Connect signals for handling transcription results
            self.gladia_transcriber.transcription_result.connect(self.on_final_transcription)
            self.gladia_transcriber.transcription_partial.connect(self.on_partial_transcription)
            self.gladia_transcriber.error_occurred.connect(self.on_transcription_error)
            
            print("✅ Gladia transcriber initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Gladia transcription: {e}")
            self.error_occurred.emit(f"Gladia setup failed: {e}")
            return False
    
    def on_partial_transcription(self, text: str):
        """Handle partial transcription results from Gladia"""
        if self.is_processing_backend:
            return
            
        print(f"🎤 PARTIAL: '{text}'")
        
        # Add to buffer for wake word detection
        self.current_text_buffer = text.lower()
        
        # Check for wake words in partial results
        self.check_for_wake_words(text, is_final=False)
    
    def on_final_transcription(self, text: str):
        """Handle final transcription results from Gladia"""
        if self.is_processing_backend:
            return
            
        print(f"🎤 FINAL: '{text}'")
        
        # Check for wake words and commands in final results
        self.check_for_wake_words(text, is_final=True)
        
        # Clear buffer after processing final result
        self.current_text_buffer = ""
    
    def on_transcription_error(self, error: str):
        """Handle transcription errors"""
        print(f"❌ Transcription error: {error}")
        self.error_occurred.emit(error)
    
    def check_for_wake_words(self, text: str, is_final: bool = False):
        """Check text for wake words and extract commands/dictation"""
        text_lower = text.lower()
        
        # Only process wake words on final transcriptions to avoid false positives
        if not is_final:
            return
        
        # Check for Hey Flow wake words
        for pattern in self.flow_patterns:
            match = re.search(pattern, text_lower)
            if match:
                print(f"🎯 Hey Flow wake word detected: {match.group()}")
                
                # Extract command after wake word, cleaning up punctuation
                command_start = match.end()
                command = text[command_start:].strip()
                # Remove leading punctuation and whitespace
                command = re.sub(r'^[,!.\s]+', '', command).strip()
                
                if command:
                    print(f"🚀 Command: '{command}'")
                    self.wake_word_detected.emit(command)
                else:
                    print("⚠️ No command found after Hey Flow")
                    # Set flag to capture next transcription as command
                    self.waiting_for_command = True
                    self.wake_word_detected_time = time.time()
                    self.status_changed.emit("Listening for command...")
                return
        
        # Check for Scribe Write wake words
        for pattern in self.scribe_patterns:
            match = re.search(pattern, text_lower)
            if match:
                print(f"📝 Scribe Write wake word detected: {match.group()}")
                
                # Extract dictation after wake word, cleaning up punctuation
                dictation_start = match.end()
                dictation = text[dictation_start:].strip()
                # Remove leading punctuation and whitespace
                dictation = re.sub(r'^[,!.\s]+', '', dictation).strip()
                
                if dictation:
                    print(f"📝 Dictation: '{dictation}'")
                    self.dictation_detected.emit(dictation)
                else:
                    print("⚠️ No dictation found after Scribe Write")
                    # Set flag to capture next transcription as dictation
                    self.waiting_for_dictation = True
                    self.wake_word_detected_time = time.time()
                    self.status_changed.emit("Dictation mode - speak your text...")
                return
        
        # If waiting for command/dictation, treat this as the response
        if self.waiting_for_command and text.strip():
            print(f"🚀 Command after wake word: '{text}'")
            self.wake_word_detected.emit(text.strip())
            self.waiting_for_command = False
            self.status_changed.emit("Listening for wake words...")
            return
            
        if self.waiting_for_dictation and text.strip():
            print(f"📝 Dictation after wake word: '{text}'")
            self.dictation_detected.emit(text.strip())
            self.waiting_for_dictation = False
            self.status_changed.emit("Listening for wake words...")
            return
        
        # Reset waiting flags after timeout (10 seconds)
        if (self.waiting_for_command or self.waiting_for_dictation) and self.wake_word_detected_time:
            if time.time() - self.wake_word_detected_time > 10:
                self.waiting_for_command = False
                self.waiting_for_dictation = False
                self.status_changed.emit("Listening for wake words...")
    
    def set_backend_processing(self, processing: bool):
        """Set whether we're currently processing a backend request"""
        self.is_processing_backend = processing
        print(f"🔄 Backend processing: {processing}")
    
    def run(self):
        """Main thread loop - start continuous Gladia transcription"""
        self.running = True
        self.status_changed.emit("Initializing...")
        
        # Setup Gladia transcription
        if not self.setup_gladia_transcription():
            self.error_occurred.emit("Failed to initialize Gladia transcription")
            return
        
        self.status_changed.emit("Starting continuous listening...")
        
        try:
            # Start continuous transcription in separate thread
            threading.Thread(target=self._run_continuous_transcription, daemon=True).start()
            
            # Keep main thread alive
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error in main run loop: {e}")
            self.error_occurred.emit(f"Main loop error: {e}")
        
        print("🛑 Speech recognition thread stopped")
    
    def _run_continuous_transcription(self):
        """Run continuous Gladia transcription in background"""
        try:
            print("🎤 Starting continuous Gladia transcription...")
            self.status_changed.emit("Listening for wake words...")
            
            # Start continuous transcription
            self.gladia_transcriber.start_continuous_transcription()
            
            # Keep this thread alive while transcription runs
            while self.running:
                time.sleep(1)
            
        except Exception as e:
            print(f"❌ Continuous transcription error: {e}")
            self.error_occurred.emit(f"Continuous transcription error: {e}")
    
    def stop(self):
        """Stop the speech recognition"""
        self.running = False
        
        # Stop Gladia transcription
        if self.gladia_transcriber:
            self.gladia_transcriber.stop_transcription()
            
        # Give thread time to clean up
        self.wait(2000)  # Wait up to 2 seconds