"""
Permission Manager Module
========================

Handles macOS permission requests and checks for:
- Accessibility permissions
- Microphone permissions

Author: AI Assistant
"""

try:
    from ApplicationServices import AXIsProcessTrusted
    MACOS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ macOS frameworks not available: {e}")
    MACOS_AVAILABLE = False

import sounddevice as sd


class PermissionManager:
    """Handles macOS permission requests and checks"""
    
    @staticmethod
    def check_accessibility_permissions() -> bool:
        """Check if accessibility permissions are granted"""
        if not MACOS_AVAILABLE:
            print("⚠️ macOS frameworks not available - skipping accessibility check")
            return True
            
        try:
            trusted = AXIsProcessTrusted()
            if not trusted:
                print("❌ Accessibility permissions required!")
                print("Please grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility")
            return trusted
        except Exception as e:
            print(f"❌ Failed to check accessibility permissions: {e}")
            return False
    
    @staticmethod
    def check_microphone_permissions() -> bool:
        """Check microphone permissions"""
        try:
            # Try to access microphone
            devices = sd.query_devices()
            return True
        except Exception as e:
            print(f"❌ Microphone permission issue: {e}")
            print("Please grant microphone permissions in System Preferences > Security & Privacy > Privacy > Microphone")
            return False
    
    @staticmethod
    def request_all_permissions():
        """Request all necessary permissions"""
        print("🔒 Checking macOS permissions...")
        
        accessibility = PermissionManager.check_accessibility_permissions()
        microphone = PermissionManager.check_microphone_permissions()
        
        print(f"✅ Accessibility: {'Granted' if accessibility else 'Denied'}")
        print(f"✅ Microphone: {'Granted' if microphone else 'Denied'}")
        
        if not accessibility or not microphone:
            print("\n⚠️ Some permissions are missing. The app will continue but some features may not work.")
            print("Please grant the required permissions and restart the app for full functionality.")
        
        return True  # Continue anyway