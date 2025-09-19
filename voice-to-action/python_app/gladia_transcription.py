"""
Gladia Speech Recognition Module
===============================

Handles real-time speech recognition using Gladia's WebSocket API.
Provides a replacement for the Google Speech Recognition used in the current implementation.

Author: AI Assistant
"""

import json
import asyncio
import threading
import time
from typing import Optional, Callable
import websockets
import requests
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

# Global configuration
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80ms chunks at 16kHz


class GladiaTranscription(QObject):
    """Real-time speech transcription using Gladia's WebSocket API"""
    
    # Signals for communication with main thread
    transcription_result = Signal(str)  # Final transcription result
    transcription_partial = Signal(str)  # Partial transcription result
    error_occurred = Signal(str)  # Error messages
    status_changed = Signal(str)  # Status updates
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.session_url = None
        self.websocket = None
        self.is_recording = False
        self.audio_stream = None
        self.loop = None
        self.transcription_thread = None
        
        # Speech pause detection
        self.final_buffer = ""
        self.final_timer = None
        self.speech_pause_delay = 1.0  # Wait 1 second after final transcription before processing
        
    async def create_session(self) -> bool:
        """Create a new Gladia transcription session"""
        try:
            # Log API key info (without exposing the key)
            api_key_preview = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "SHORT_KEY"
            print(f"🔑 Using Gladia API key: {api_key_preview}")
            
            headers = {
                'Content-Type': 'application/json',
                'X-Gladia-Key': self.api_key,
            }
            
            # Configuration for real-time transcription
            config = {
                "encoding": "wav/pcm",
                "sample_rate": SAMPLE_RATE,
                "bit_depth": 16,
                "channels": 1,
                "realtime_processing": {
                    "words_accurate_timestamps": True
                }
            }
            
            print(f"🌐 Making request to Gladia API: https://api.gladia.io/v2/live")
            print(f"📋 Request config: {config}")
            
            response = requests.post(
                'https://api.gladia.io/v2/live',
                headers=headers,
                json=config,
                timeout=10
            )
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📋 Response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.session_url = result.get('url')
                print(f"✅ Gladia session created: {result.get('id')}")
                print(f"🔗 WebSocket URL: {self.session_url}")
                return True
            else:
                # Log detailed error information
                try:
                    error_details = response.json()
                    print(f"❌ Gladia API error details: {error_details}")
                except:
                    print(f"❌ Gladia API error (no JSON): {response.text}")
                
                error_msg = f"Failed to create Gladia session: HTTP {response.status_code}"
                print(f"❌ {error_msg}")
                
                # Log specific 429 rate limit details
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', 'Unknown')
                    rate_limit_reset = response.headers.get('X-RateLimit-Reset', 'Unknown')
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                    print(f"🚫 RATE LIMIT EXCEEDED:")
                    print(f"   - Retry-After: {retry_after}")
                    print(f"   - Rate Limit Reset: {rate_limit_reset}")
                    print(f"   - Rate Limit Remaining: {rate_limit_remaining}")
                    print(f"   - This could be due to:")
                    print(f"     • Too many requests from this API key")
                    print(f"     • API key quota exceeded")
                    print(f"     • Different rate limits on different machines")
                
                self.error_occurred.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error creating Gladia session: {e}"
            print(f"❌ {error_msg}")
            print(f"🔍 Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
            return False
    
    async def connect_websocket(self):
        """Connect to the Gladia WebSocket"""
        try:
            self.websocket = await websockets.connect(self.session_url)
            print("✅ Connected to Gladia WebSocket")
            return True
        except Exception as e:
            error_msg = f"Failed to connect to Gladia WebSocket: {e}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    async def listen_for_messages(self):
        """Listen for messages from Gladia WebSocket"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                
                if data.get('type') == 'transcript':
                    transcript_data = data.get('data', {})
                    utterance = transcript_data.get('utterance', {})
                    text = utterance.get('text', '')
                    
                    if text:
                        if transcript_data.get('is_final', False):
                            # Final transcription - buffer it and wait for speech pause
                            print(f"🎤 GLADIA FINAL (buffered): '{text}'")
                            self.final_buffer = text
                            self._reset_final_timer()
                        else:
                            # Partial transcription
                            print(f"🎤 GLADIA PARTIAL: '{text}'")
                            self.transcription_partial.emit(text)
                
                elif data.get('type') == 'error':
                    error_msg = data.get('message', 'Unknown Gladia error')
                    print(f"❌ Gladia error: {error_msg}")
                    self.error_occurred.emit(error_msg)
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Gladia WebSocket connection closed")
        except Exception as e:
            error_msg = f"Error listening to Gladia messages: {e}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def audio_callback(self, indata, frames, time, status):
        """Audio callback for sending data to Gladia"""
        if status:
            print(f"⚠️ Audio callback status: {status}")
        
        if self.websocket and self.is_recording:
            try:
                # Convert to the format expected by Gladia (16-bit PCM)
                audio_data = (indata.flatten() * 32767).astype(np.int16)
                
                # Send audio data to Gladia WebSocket (run in event loop)
                if self.loop and not self.loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self.send_audio_chunk(audio_data.tobytes()),
                        self.loop
                    )
            except Exception as e:
                print(f"⚠️ Error in audio callback: {e}")
    
    async def send_audio_chunk(self, audio_bytes: bytes):
        """Send audio chunk to Gladia WebSocket"""
        try:
            if self.websocket:
                await self.websocket.send(audio_bytes)
        except Exception as e:
            print(f"⚠️ Error sending audio chunk: {e}")
    
    def start_transcription(self, timeout: float = 30.0) -> str:
        """Start real-time transcription and return the result"""
        self.final_result = ""
        self.transcription_complete = threading.Event()
        
        # Connect the signal to capture the final result
        def on_final_result(text):
            self.final_result = text
            self.transcription_complete.set()
        
        self.transcription_result.connect(on_final_result)
        
        # Start the transcription in a separate thread
        self.transcription_thread = threading.Thread(
            target=self._run_transcription_session,
            daemon=True
        )
        self.transcription_thread.start()
        
        # Wait for transcription result or timeout
        if self.transcription_complete.wait(timeout):
            return self.final_result
        else:
            self.stop_transcription()
            return ""
    
    def start_continuous_transcription(self):
        """Start continuous transcription (for wake word detection)"""
        if self.transcription_thread and self.transcription_thread.is_alive():
            print("⚠️ Transcription already running")
            return
            
        # Start the transcription in a separate thread
        self.transcription_thread = threading.Thread(
            target=self._run_transcription_session,
            daemon=True
        )
        self.transcription_thread.start()
        print("🎤 Continuous transcription started")
    
    def _run_transcription_session(self):
        """Run the transcription session in an event loop"""
        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._async_transcription_session())
        except Exception as e:
            print(f"❌ Error in transcription session: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.loop.close()
    
    async def _async_transcription_session(self):
        """Async transcription session"""
        try:
            # Create session
            if not await self.create_session():
                return
            
            # Connect WebSocket
            if not await self.connect_websocket():
                return
            
            # Start listening for messages
            message_task = asyncio.create_task(self.listen_for_messages())
            
            # Start audio recording
            self.is_recording = True
            self.status_changed.emit("Recording...")
            
            self.audio_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype=np.float32,
                blocksize=CHUNK_SIZE,
                callback=self.audio_callback
            )
            
            with self.audio_stream:
                print("🎤 Gladia transcription started...")
                await message_task
                
        except Exception as e:
            error_msg = f"Error in async transcription session: {e}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
        finally:
            await self.cleanup()
    
    def stop_transcription(self):
        """Stop the transcription session"""
        self.is_recording = False
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.cleanup(), self.loop)
    
    def _reset_final_timer(self):
        """Reset the timer for processing final transcription after speech pause"""
        # Cancel existing timer if any
        if self.final_timer:
            self.final_timer.cancel()
        
        # Start new timer
        self.final_timer = threading.Timer(self.speech_pause_delay, self._process_final_transcription)
        self.final_timer.start()
        print(f"🕰️ Speech pause timer reset - waiting {self.speech_pause_delay}s for processing")
    
    def _process_final_transcription(self):
        """Process the buffered final transcription after speech pause"""
        if self.final_buffer:
            print(f"🎤 GLADIA FINAL (processed after pause): '{self.final_buffer}'")
            self.transcription_result.emit(self.final_buffer)
            self.final_buffer = ""
        self.final_timer = None
    
    async def cleanup(self):
        """Clean up resources"""
        self.is_recording = False
        
        # Cancel any pending timer
        if self.final_timer:
            self.final_timer.cancel()
            self.final_timer = None
        
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        print("🧹 Gladia transcription cleanup complete")


class GladiaTranscriptionService:
    """Service wrapper for Gladia transcription"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.transcriber = None
    
    def transcribe_audio(self, timeout: float = 15.0) -> str:
        """Transcribe audio and return the result"""
        try:
            self.transcriber = GladiaTranscription(self.api_key)
            result = self.transcriber.start_transcription(timeout)
            return result.strip() if result else ""
        except Exception as e:
            print(f"❌ Gladia transcription error: {e}")
            return ""
        finally:
            if self.transcriber:
                self.transcriber.stop_transcription()
                self.transcriber = None