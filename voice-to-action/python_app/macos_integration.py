"""
macOS Integration Module
========================

Handles macOS-specific functionality like:
- Window management
- Text insertion at cursor
- App focus management

Author: AI Assistant
"""

from PySide6.QtCore import QTimer

# macOS integration
try:
    from Foundation import NSBundle, NSWorkspace, NSRunningApplication
    from AppKit import NSApp, NSApplication, NSWindow, NSScreen, NSSpeechSynthesizer
    from Cocoa import NSPasteboard, NSStringPboardType, NSEvent
    from Quartz import (
        CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap,
        CGEventSourceCreate, kCGEventSourceStateHIDSystemState,
        CGEventSetFlags, kCGEventFlagMaskCommand
    )
    MACOS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ macOS frameworks not available: {e}")
    MACOS_AVAILABLE = False


class MacOSIntegration:
    """Handles macOS-specific functionality"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.original_app = None
        self.speech_synthesizer = None
        if MACOS_AVAILABLE:
            try:
                self.speech_synthesizer = NSSpeechSynthesizer.alloc().init()
                print("✅ Speech synthesizer initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize speech synthesizer: {e}")
                self.speech_synthesizer = None
    
    def bring_to_front(self):
        """Bring app window to front"""
        if not MACOS_AVAILABLE:
            self.main_window.raise_()
            self.main_window.activateWindow()
            return
            
        try:
            # Store current frontmost app
            workspace = NSWorkspace.sharedWorkspace()
            frontmost = workspace.frontmostApplication()
            
            if frontmost and frontmost.bundleIdentifier() != NSBundle.mainBundle().bundleIdentifier():
                self.original_app = frontmost
            
            # Activate our app
            NSApp.activateIgnoringOtherApps_(True)
            self.main_window.raise_()
            self.main_window.activateWindow()
        except Exception as e:
            print(f"❌ Failed to bring window to front: {e}")
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def restore_original_app(self):
        """Restore focus to original app"""
        if not MACOS_AVAILABLE or not self.original_app:
            return
            
        try:
            self.original_app.activateWithOptions_(0)
            self.original_app = None
        except Exception as e:
            print(f"❌ Failed to restore original app: {e}")
    
    def insert_text_at_cursor(self, text: str):
        """Insert text at current cursor position using macOS pasteboard"""
        if not MACOS_AVAILABLE:
            print(f"⚠️ macOS not available - cannot insert text: {text}")
            return
            
        try:
            # Get current pasteboard content
            pasteboard = NSPasteboard.generalPasteboard()
            original_content = pasteboard.stringForType_(NSStringPboardType)
            
            # Set our text to pasteboard
            pasteboard.clearContents()
            pasteboard.setString_forType_(text, NSStringPboardType)
            
            # Create Cmd+V event
            source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState)
            
            # Cmd key down + V key down
            cmd_v_down = CGEventCreateKeyboardEvent(source, 9, True)  # V key
            CGEventSetFlags(cmd_v_down, kCGEventFlagMaskCommand)
            
            # Cmd key up + V key up  
            cmd_v_up = CGEventCreateKeyboardEvent(source, 9, False)  # V key
            
            # Post events
            CGEventPost(kCGHIDEventTap, cmd_v_down)
            CGEventPost(kCGHIDEventTap, cmd_v_up)
            
            # Restore original pasteboard content after delay
            QTimer.singleShot(100, lambda: self.restore_pasteboard(original_content))
            
            print(f"✅ Text inserted via Cmd+V: {text}")
            
        except Exception as e:
            print(f"❌ Failed to insert text: {e}")
    
    def restore_pasteboard(self, original_content: str):
        """Restore original pasteboard content"""
        if not MACOS_AVAILABLE or not original_content:
            return
            
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(original_content, NSStringPboardType)
        except Exception as e:
            print(f"❌ Failed to restore pasteboard: {e}")
    
    def speak_text(self, text: str):
        """Speak text using macOS built-in text-to-speech"""
        print(f"🔊 speak_text called with: '{text}'")
        print(f"🔊 MACOS_AVAILABLE: {MACOS_AVAILABLE}")
        print(f"🔊 speech_synthesizer exists: {self.speech_synthesizer is not None}")
        
        if not MACOS_AVAILABLE:
            print(f"⚠️ macOS not available - cannot speak: {text}")
            return
            
        if not self.speech_synthesizer:
            print(f"⚠️ Speech synthesizer not initialized - cannot speak: {text}")
            return
            
        try:
            # Check if synthesizer is available
            if not self.speech_synthesizer:
                print("❌ Speech synthesizer is None")
                return
                
            # Stop any current speech
            is_speaking = self.speech_synthesizer.isSpeaking()
            print(f"🔊 Currently speaking: {is_speaking}")
            if is_speaking:
                print("🔇 Stopping current speech")
                self.speech_synthesizer.stopSpeaking()
            
            # Speak the text
            print(f"🔊 About to call startSpeakingString_ with: '{text}'")
            result = self.speech_synthesizer.startSpeakingString_(text)
            print(f"🔊 startSpeakingString_ returned: {result}")
            
            # Check if speaking started
            is_speaking_after = self.speech_synthesizer.isSpeaking()
            print(f"🔊 Speaking after start: {is_speaking_after}")
            
        except Exception as e:
            print(f"❌ Exception in speak_text: {e}")
            print(f"❌ Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
    
    def stop_speaking(self):
        """Stop current speech synthesis"""
        if MACOS_AVAILABLE and self.speech_synthesizer and self.speech_synthesizer.isSpeaking():
            try:
                self.speech_synthesizer.stopSpeaking()
                print("🔇 Speech stopped")
            except Exception as e:
                print(f"❌ Failed to stop speech: {e}")