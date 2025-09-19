#!/usr/bin/env python3
"""
Router Agent for A2A Flow
=========================

The first agent in the A2A flow that analyzes user requests and decides whether to:
1. Provide a direct final response
2. Create a task list for specialized agents to execute

Uses ChatAnthropic with structured output to ensure consistent routing decisions.
"""

import asyncio
import os
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from a2a_models import RouterDecision, FinalResponse, TaskList, Task, TaskType


class RouterAgent:
    """Router agent that determines the flow path for user requests"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.chat_model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the ChatAnthropic model with structured output"""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for RouterAgent")
        
        try:
            self.chat_model = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.1,  # Low temperature for consistent routing decisions
                max_tokens=2048
            ).with_structured_output(RouterDecision)
            
            print("✅ Router Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Router Agent: {e}")
            raise
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the router agent"""
        return """You are a Router Agent. Decide between:

1. **final_response**: For questions you can answer directly (knowledge, explanations, conversations)
2. **task_list**: For actions requiring external agents:
   - **google_assistant**: ONLY for Gmail, Google Drive, Google Calendar actions
   - **web_use**: For web searches, browsing websites, finding information online, weather, shopping

**IMPORTANT DISTINCTIONS:**
- Weather/web searches → web_use (not Google Assistant)
- Gmail/Calendar/Drive → google_assistant
- Shopping/prices → web_use

Examples:
- "What's the weather in NYC?" → web_use task
- "Check my calendar" → google_assistant task
- "Find iPhone prices" → web_use task
- "Send email to John" → google_assistant task

Be specific in task instructions."""

    async def route_request(self, user_message: str, conversation_history: Optional[list] = None) -> RouterDecision:
        """
        Analyze user request and return routing decision
        
        Args:
            user_message: The user's input message
            conversation_history: Optional list of previous messages for context
            
        Returns:
            RouterDecision: Decision on how to handle the request
        """
        if not self.chat_model:
            raise RuntimeError("Router Agent not properly initialized")
        
        try:
            print(f"🤔 Router Agent analyzing: '{user_message[:100]}{'...' if len(user_message) > 100 else ''}'")
            
            # Create messages for the router
            messages = [
                SystemMessage(content=self._create_system_prompt())
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append(HumanMessage(content=f"User request: {user_message}"))
            
            print(f"📤 Router Agent INPUT: {user_message}")
            
            # Get structured decision from the model
            decision = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.chat_model.invoke(messages)
            )
            
            # Log the decision with full details
            if decision.decision_type == "final_response":
                print(f"📝 Router decided: Direct response")
                print(f"📥 Router Agent OUTPUT (final_response): {decision.content.response[:200]}{'...' if len(decision.content.response) > 200 else ''}")
                print(f"   Reasoning: {decision.content.reasoning}")
            else:
                task_count = len(decision.content.tasks) if hasattr(decision.content, 'tasks') else 0
                print(f"🎯 Router decided: Execute {task_count} tasks")
                print(f"📥 Router Agent OUTPUT (task_list):")
                print(f"   Reasoning: {decision.content.reasoning}")
                for i, task in enumerate(decision.content.tasks, 1):
                    print(f"   Task {i}: {task.task_type.value} - {task.instructions[:150]}{'...' if len(task.instructions) > 150 else ''}")
            
            return decision
            
        except Exception as e:
            print(f"❌ Error in router agent: {e}")
            # Fallback to a simple conversational response
            fallback_response = RouterDecision(
                decision_type="final_response",
                content=FinalResponse(
                    response=f"I apologize, but I encountered an error processing your request: {str(e)}",
                    reasoning="Fallback response due to router agent error"
                )
            )
            return fallback_response
    
    def route_request_sync(self, user_message: str, conversation_history: Optional[list] = None) -> RouterDecision:
        """
        Synchronous wrapper for route_request
        
        Args:
            user_message: The user's input message
            conversation_history: Optional list of previous messages for context
            
        Returns:
            RouterDecision: Decision on how to handle the request
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.route_request(user_message, conversation_history))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.route_request(user_message, conversation_history))


# Test the router agent
async def test_router_agent():
    """Test function for the router agent"""
    router = RouterAgent()
    
    test_cases = [
        "What is the capital of France?",
        "Set a reminder for my meeting tomorrow at 2 PM",
        "Find the latest iPhone price on Apple's website",
        "Check my calendar and book a table at a restaurant",
        "How does photosynthesis work?",
        "Turn on the living room lights and play some music"
    ]
    
    for test_message in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing: {test_message}")
        print(f"{'='*50}")
        
        decision = await router.route_request(test_message)
        
        print(f"Decision type: {decision.decision_type}")
        if decision.decision_type == "final_response":
            print(f"Response: {decision.content.response[:100]}...")
        else:
            print(f"Tasks: {len(decision.content.tasks)}")
            for i, task in enumerate(decision.content.tasks, 1):
                print(f"  {i}. {task.task_type}: {task.instructions[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_router_agent())