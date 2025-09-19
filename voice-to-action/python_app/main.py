#!/usr/bin/env python3
"""
Control Flow - Python Voice Agent
=================================

A modern Python replacement for the Swift app with:
1. Real-time speech recognition using Gladia API
2. Wake word detection for "Hey Flow" and "Scribe Write"
3. PySide6 GUI that matches the Swift app functionality
4. Integration with the existing backend API
5. macOS permissions handling

Features:
- Always listening for wake words "Hey Flow" and "Scribe Write"
- "Hey Flow" + command sends to backend for execution
- "Scribe Write" + text for dictation/text insertion
- Professional GUI with status indicators
- MiniMax AI text-to-speech for agent responses
- Handles macOS accessibility and microphone permissions

Author: AI Assistant
Version: 1.0.0 (Refactored)
"""

import sys
from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

# Import our modules
from permissions import PermissionManager
from main_window import MainWindow

# Load environment variables
load_dotenv()

# Global configuration
BACKEND_URL = "http://127.0.0.1:8000"


def main():
    """Main application entry point"""
    print("🚀 Control Flow - Python Voice Agent v1.0 (Refactored)")
    print("=" * 60)
    
    # Check permissions first
    if not PermissionManager.request_all_permissions():
        print("❌ Some permissions not granted - continuing with limited functionality")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Control Flow")
    app.setApplicationVersion("1.0.0")
    
    # Set app icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Create and show main window
    window = MainWindow(BACKEND_URL)
    window.show()
    
    print("✅ Application started successfully")
    print("🎤 Listening for wake words...")
    print("💡 Say 'Hey Flow' + command for voice commands")
    print("📝 Say 'Scribe Write' + text for dictation")
    
    # Run application
    result = app.exec()
    
    print("👋 Application shutdown complete")
    return result


if __name__ == "__main__":
    # Multiprocessing protection for audio processing
    import multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())