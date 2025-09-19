#!/usr/bin/env python3
"""
Final Answer Agent for A2A Flow
===============================

Synthesizes task execution results into a coherent final response.
Takes the user's original question and all task results, then creates
a comprehensive answer that addresses what was accomplished.
"""

import asyncio
import os
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from a2a_models import TaskExecutionSummary, FinalAgentResponse


class FinalAnswerAgent:
    """Agent that synthesizes task results into a final response"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.chat_model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the ChatAnthropic model for response synthesis"""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for FinalAnswerAgent")
        
        try:
            self.chat_model = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.3,  # Balanced for coherent but natural responses
                max_tokens=2048
            ).with_structured_output(FinalAgentResponse)
            
            print("✅ Final Answer Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Final Answer Agent: {e}")
            raise
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the final answer agent"""
        return """You synthesize task results into natural responses. Present the actual information found, not process descriptions.

You receive: user's request, task results (success/failure), execution summary.

IMPORTANT: Extract and present the actual data from task results.

Examples:
- Weather task result: "Currently 72°F and sunny" → "The weather in San Francisco is currently 72°F and sunny."
- Price task result: "iPhone 15 Pro starts at $999" → "The iPhone 15 Pro starts at $999."
- Failed task → "I wasn't able to [specific task] due to [brief reason]."

Don't say "I checked" or "I found" - just present the information directly."""

    async def create_final_response(
        self, 
        user_request: str, 
        task_summary: TaskExecutionSummary
    ) -> FinalAgentResponse:
        """
        Create a final synthesized response from task execution results
        
        Args:
            user_request: The original user request
            task_summary: Summary of all executed tasks and their results
            
        Returns:
            FinalAgentResponse: Synthesized final response
        """
        if not self.chat_model:
            raise RuntimeError("Final Answer Agent not properly initialized")
        
        try:
            print(f"🎯 Final Answer Agent synthesizing response for: '{user_request[:100]}{'...' if len(user_request) > 100 else ''}'")
            
            # Create a detailed prompt with task results
            task_results_text = self._format_task_results(task_summary)
            
            print(f"📤 Final Answer Agent INPUT:")
            print(f"   User Request: {user_request}")
            print(f"   Task Summary: {task_summary.successful_tasks}/{task_summary.total_tasks} successful")
            for i, result in enumerate(task_summary.results, 1):
                status = "✅" if result.success else "❌"
                print(f"   Task {i} {status}: {result.result[:100]}{'...' if len(result.result) > 100 else ''}")
            
            user_prompt = f"""
User asked: {user_request}

Task Results:
{task_results_text}

Extract the actual information from the successful task results and present it naturally to answer the user's question. If tasks failed, briefly mention what couldn't be completed.
"""
            
            # Create messages for the final answer agent
            messages = [
                SystemMessage(content=self._create_system_prompt()),
                HumanMessage(content=user_prompt)
            ]
            
            # Generate the final response
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.chat_model.invoke(messages)
            )
            
            print(f"✅ Final response synthesized successfully")
            print(f"📥 Final Answer Agent OUTPUT: {response.response[:300]}{'...' if len(response.response) > 300 else ''}")
            print(f"   Summary: {response.summary}")
            if response.tasks_performed:
                print(f"   Tasks Performed: {', '.join(response.tasks_performed)}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error in final answer agent: {e}")
            # Fallback response
            fallback_response = FinalAgentResponse(
                response=f"I apologize, but I encountered an error while processing your request: {str(e)}",
                summary="Error occurred during response synthesis",
                tasks_performed=None
            )
            return fallback_response
    
    def _format_task_results(self, task_summary: TaskExecutionSummary) -> str:
        """
        Format task results into a readable text summary
        
        Args:
            task_summary: Summary of task execution
            
        Returns:
            str: Formatted task results text
        """
        if not task_summary.results:
            return "No tasks were executed."
        
        results_text = []
        
        for i, result in enumerate(task_summary.results, 1):
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            
            task_text = f"""
Task {i} ({result.task_type.value}): {status}
- Execution Time: {result.execution_time:.2f} seconds
"""
            
            if result.success:
                task_text += f"- Result: {result.result[:300]}{'...' if len(result.result) > 300 else ''}"
            else:
                task_text += f"- Error: {result.error_message}"
            
            results_text.append(task_text)
        
        return "\n".join(results_text)
    
    def create_final_response_sync(
        self, 
        user_request: str, 
        task_summary: TaskExecutionSummary
    ) -> FinalAgentResponse:
        """
        Synchronous wrapper for create_final_response
        
        Args:
            user_request: The original user request
            task_summary: Summary of all executed tasks and their results
            
        Returns:
            FinalAgentResponse: Synthesized final response
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.create_final_response(user_request, task_summary))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.create_final_response(user_request, task_summary))


# Test the final answer agent
async def test_final_answer_agent():
    """Test function for the final answer agent"""
    agent = FinalAnswerAgent()
    
    # Create mock task summary for testing
    from a2a_models import TaskResult, TaskType
    
    mock_results = [
        TaskResult(
            task_id="weather_task",
            task_type=TaskType.WEB_USE,
            success=True,
            result="The current weather in San Francisco is sunny with a temperature of 72°F. Light winds from the west at 5 mph. No precipitation expected today.",
            error_message=None,
            execution_time=2.3
        ),
        TaskResult(
            task_id="reminder_task", 
            task_type=TaskType.GOOGLE_ASSISTANT,
            success=True,
            result="Reminder set successfully for 'Team meeting' tomorrow at 2:00 PM.",
            error_message=None,
            execution_time=1.8
        ),
        TaskResult(
            task_id="lights_task",
            task_type=TaskType.GOOGLE_ASSISTANT,
            success=False,
            result="",
            error_message="Unable to connect to smart home system",
            execution_time=1.2
        )
    ]
    
    mock_summary = TaskExecutionSummary(
        total_tasks=3,
        successful_tasks=2,
        failed_tasks=1,
        results=mock_results,
        total_execution_time=5.3
    )
    
    test_cases = [
        "Check the weather in San Francisco and set a reminder for my team meeting tomorrow at 2 PM",
        "Turn on the living room lights, check the weather, and set a reminder",
        "What's the weather like and can you help me with my smart home?"
    ]
    
    for i, user_request in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {user_request}")
        print(f"{'='*70}")
        
        response = await agent.create_final_response(user_request, mock_summary)
        
        print(f"Response: {response.response}")
        print(f"Summary: {response.summary}")
        if response.tasks_performed:
            print(f"Tasks Performed: {', '.join(response.tasks_performed)}")


if __name__ == "__main__":
    asyncio.run(test_final_answer_agent())