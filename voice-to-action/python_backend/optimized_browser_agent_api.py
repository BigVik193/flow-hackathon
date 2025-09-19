#!/usr/bin/env python3
"""
Voice Agent API - A2A Flow Enabled Conversational Interface

A FastAPI service with Agent-to-Agent (A2A) flow capability.
Routes requests through specialized agents for complex task execution.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain imports
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

# Import TTS service
from minimax_tts_service import default_tts_service

# Import A2A Flow components
from a2a_orchestrator import get_a2a_orchestrator

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Global conversation state - single conversation for now
conversation_history = InMemoryChatMessageHistory()
chat_model = None
a2a_orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Voice Agent API with A2A Flow...")
    await initialize_chat_model()
    await initialize_a2a_flow()
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Voice Agent API...")


async def initialize_chat_model():
    """Initialize the ChatAnthropic model"""
    global chat_model
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not found")
        print("Please set: export ANTHROPIC_API_KEY='your-key'")
        return False
    
    try:
        chat_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.7,
            max_tokens=1024
        )
        print("✅ ChatAnthropic initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize ChatAnthropic: {e}")
        return False


async def initialize_a2a_flow():
    """Initialize the A2A flow orchestrator"""
    global a2a_orchestrator
    
    try:
        a2a_orchestrator = get_a2a_orchestrator()
        print("✅ A2A Flow orchestrator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize A2A Flow: {e}")
        return False


# FastAPI app
app = FastAPI(
    title="Voice Agent API",
    description="Simple conversational interface with ChatAnthropic",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    status: str
    response: str
    execution_time: float
    timestamp: str
    audio_url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_initialized: bool
    api_key_present: bool
    conversation_length: int
    a2a_flow_enabled: bool
    a2a_components: Optional[dict] = None


class ConversationResponse(BaseModel):
    messages: list
    total_messages: int


async def process_message(user_message: str) -> str:
    """Process a user message using A2A flow or fallback to simple chat"""
    global a2a_orchestrator, chat_model
    
    # Add user message to history regardless of processing method
    conversation_history.add_message(HumanMessage(content=user_message))
    
    try:
        # Try A2A flow first if orchestrator is available
        if a2a_orchestrator:
            print("🎯 Processing with A2A Flow...")
            a2a_result = await a2a_orchestrator.process_message(user_message)
            response_content = a2a_result.final_response
            
            # Add A2A response to conversation history
            conversation_history.add_message(AIMessage(content=response_content))
            
            return response_content
        
        # Fallback to original chat model if A2A not available
        elif chat_model:
            print("💬 Fallback to simple chat model...")
            
            # Get all messages for context
            all_messages = conversation_history.messages
            
            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: chat_model.invoke(all_messages)
            )
            
            # Add AI response to history
            conversation_history.add_message(response)
            
            return response.content
        
        else:
            raise HTTPException(status_code=500, detail="Neither A2A flow nor chat model initialized")
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        
        # Try fallback if A2A fails
        if a2a_orchestrator and chat_model:
            try:
                print("🔄 A2A failed, trying fallback to simple chat...")
                all_messages = conversation_history.messages
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: chat_model.invoke(all_messages)
                )
                conversation_history.add_message(response)
                return response.content
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
        
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


async def generate_tts_audio(text: str) -> Optional[str]:
    """Generate TTS audio for the response"""
    try:
        audio_url = await default_tts_service.text_to_speech_async(text)
        if audio_url:
            print("✅ TTS audio generated")
        else:
            print("⚠️ Failed to generate TTS audio")
        return audio_url
    except Exception as e:
        print(f"❌ TTS error: {e}")
        return None


@app.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """Send a message and get AI response"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        print(f"💬 Processing: '{request.message}'")
        
        # Process the message
        ai_response = await process_message(request.message)
        
        # Generate TTS audio
        audio_url = await generate_tts_audio(ai_response)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        print(f"✅ Response generated in {execution_time:.3f} seconds")
        
        return MessageResponse(
            status="success",
            response=ai_response,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            audio_url=audio_url
        )
        
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        print(f"❌ Error: {e}")
        
        return MessageResponse(
            status="error",
            response=f"Error: {str(e)}",
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            audio_url=None
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    a2a_enabled = a2a_orchestrator is not None
    a2a_health = None
    
    if a2a_enabled:
        try:
            a2a_health = await a2a_orchestrator.health_check()
        except:
            a2a_health = {"error": "Failed to check A2A health"}
    
    overall_status = "healthy"
    if chat_model is None:
        overall_status = "degraded"
    elif a2a_enabled and a2a_health and any(status == "unhealthy" for status in a2a_health.values()):
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        model_initialized=chat_model is not None,
        api_key_present=bool(os.getenv("ANTHROPIC_API_KEY")),
        conversation_length=len(conversation_history.messages),
        a2a_flow_enabled=a2a_enabled,
        a2a_components=a2a_health
    )


@app.get("/conversation", response_model=ConversationResponse)
async def get_conversation():
    """Get the current conversation history"""
    messages = []
    for msg in conversation_history.messages:
        messages.append({
            "type": msg.type,
            "content": msg.content,
            "timestamp": getattr(msg, 'timestamp', None)
        })
    
    return ConversationResponse(
        messages=messages,
        total_messages=len(messages)
    )


@app.delete("/conversation")
async def clear_conversation():
    """Clear the conversation history"""
    conversation_history.clear()
    return {"message": "Conversation history cleared", "status": "success"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voice Agent API",
        "version": "2.0.0",
        "description": "A2A Flow enabled conversational interface with multi-agent capabilities",
        "features": [
            "Agent-to-Agent (A2A) Flow orchestration",
            "Google Assistant integration via Airia API",
            "Web browsing via Bright Data MCP connector",
            "ChatAnthropic integration with structured output",
            "Conversation history",
            "TTS audio generation",
            "Task routing and execution",
            "Fallback to simple chat mode"
        ],
        "a2a_capabilities": [
            "Intelligent request routing",
            "Google Assistant tasks (reminders, calendar, weather, etc.)",
            "Web browsing and information extraction",
            "Multi-step task execution",
            "Result synthesis and natural responses"
        ],
        "endpoints": {
            "send_message": "/message",
            "health": "/health",
            "conversation": "/conversation",
            "clear_conversation": "/conversation (DELETE)",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("💬 Voice Agent API")
    print("🤖 ChatAnthropic + Conversation History")
    print("📡 Starting server on http://localhost:8000")
    print("📚 API docs at http://localhost:8000/docs")
    
    # Check environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Missing: ANTHROPIC_API_KEY")
        print("Set with: export ANTHROPIC_API_KEY='your-key'")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")