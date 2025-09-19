"""
Backend Service Module
======================

Handles communication with the FastAPI backend for command execution.

Author: AI Assistant
"""

import requests
from typing import Dict, Any, Optional
from datetime import datetime


class BackendService:
    """Service for communicating with the backend API"""
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        self.backend_url = backend_url
    
    def execute_command(self, command: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send command to backend API"""
        try:
            payload = {
                "message": command
            }
            
            print(f"🚀 Sending to backend: {command}")
            
            response = requests.post(
                f"{self.backend_url}/message",
                json=payload,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Backend response: {result.get('response', '')}")
                # Convert backend response format to frontend expected format
                return {
                    "status": result.get("status", "success"),
                    "message": result.get("response", ""),
                    "agent_type": "conversation",
                    "execution_time": result.get("execution_time", 0.0),
                    "timestamp": result.get("timestamp", datetime.now().isoformat()),
                    "audio_url": result.get("audio_url")
                }
            else:
                error_msg = f"Backend error: HTTP {response.status_code}"
                print(f"❌ {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "agent_type": "error",
                    "execution_time": 0.0,
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {e}"
            print(f"❌ {error_msg}")
            return {
                "status": "error", 
                "message": error_msg,
                "agent_type": "error",
                "execution_time": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def check_health(self) -> bool:
        """Check if backend is healthy"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False