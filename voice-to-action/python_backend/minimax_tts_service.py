"""
MiniMax Text-to-Speech Service for Backend
==========================================

Handles text-to-speech conversion using MiniMax AI's TTS API.
Used by the backend to generate audio URLs for frontend consumption.

Author: AI Assistant
"""

import requests
import os
import asyncio
import aiohttp
from typing import Optional
from datetime import datetime


class MinimaxTTSService:
    """Backend service for MiniMax text-to-speech conversion"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('MINIMAX_API_KEY')
        self.base_url = "https://api.minimax.io/v1"
        
        if not self.api_key:
            print("⚠️ MINIMAX_API_KEY not found in environment variables")
    
    async def text_to_speech_async(self, text: str, voice_id: str = "English_AttractiveGirl", model: str = "speech-02-turbo") -> Optional[str]:
        """
        Convert text to speech using MiniMax API (async version)
        
        Args:
            text: Text to convert to speech (1-10000 characters)
            voice_id: Voice ID to use (default: "English_AttractiveGirl")
            model: TTS model to use (default: "speech-02-turbo", options: "speech-01-turbo", "speech-01-hd", "speech-02-turbo", "speech-02-hd")
            
        Returns:
            str: Audio URL if successful, None otherwise
        """
        if not self.api_key:
            print("❌ MiniMax API key not available")
            return None
            
        if not text or len(text.strip()) == 0:
            print("⚠️ Empty text provided for TTS")
            return None
            
        if len(text) > 10000:
            print(f"⚠️ Text too long ({len(text)} chars), truncating to 10000")
            text = text[:10000]
        
        try:
            print(f"🔊 Backend: Converting text to speech using model {model}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Prepare request with correct format based on 2025 API docs
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "text": text,
                "stream": False,  # Non-streaming mode for simplicity
                "output_format": "url",  # Request URL format instead of hex data
                "voice_setting": {
                    "voice_id": voice_id,
                    "speed": 1.4,
                    "vol": 1.0,
                    "pitch": 0
                },
                "audio_setting": {
                    "audio_sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3",
                    "channel": 1
                }
            }
            
            # Use the correct endpoint for synchronous TTS
            endpoint = f"{self.base_url}/t2a_v2"
            
            # Make async API request with increased timeout for TTS generation
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status in [200, 201]:  # Accept both 200 and 201
                        result = await response.json()
                        print(f"🔍 Backend: API Response keys: {list(result.keys())}")
                        
                        # Check for different possible response formats based on API docs
                        audio_url = None
                        
                        # Try different possible response structures
                        if 'audio_url' in result:
                            audio_url = result['audio_url']
                        elif 'data' in result and isinstance(result['data'], dict):
                            if 'audio_url' in result['data']:
                                audio_url = result['data']['audio_url']
                            elif 'audio' in result['data']:
                                audio_url = result['data']['audio']
                        elif 'audio' in result:
                            audio_url = result['audio']
                        elif 'url' in result:
                            audio_url = result['url']
                        
                        if audio_url:
                            print(f"✅ Backend: Audio generated successfully: {audio_url}")
                            return audio_url
                        else:
                            print("❌ Backend: No audio URL in response")
                            print(f"🔍 Full response: {result}")
                            return None
                    else:
                        error_text = await response.text()
                        print(f"❌ Backend: MiniMax API error: HTTP {response.status}")
                        print(f"Response: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            print("❌ Backend: MiniMax API request timed out")
            return None
        except Exception as e:
            print(f"❌ Backend: Unexpected error in text_to_speech: {e}")
            return None
    
    def text_to_speech_sync(self, text: str, voice_id: str = "English_AttractiveGirl", model: str = "speech-02-turbo") -> Optional[str]:
        """
        Synchronous wrapper for text_to_speech_async
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            model: TTS model to use
            
        Returns:
            str: Audio URL if successful, None otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.text_to_speech_async(text, voice_id, model))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.text_to_speech_async(text, voice_id, model))
    
    async def check_health(self) -> bool:
        """Check if MiniMax TTS service is available"""
        if not self.api_key:
            return False
            
        try:
            # Try a simple test request
            test_result = await self.text_to_speech_async("Test", "English_AttractiveGirl")
            return test_result is not None
        except:
            return False


# Default instance for easy importing
default_tts_service = MinimaxTTSService()