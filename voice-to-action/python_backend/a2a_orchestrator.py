#!/usr/bin/env python3
"""
A2A Flow Orchestrator
====================

Main orchestrator for the Agent-to-Agent flow system.
Coordinates the entire flow from initial routing through task execution to final response.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

from a2a_models import A2AFlowResult, RouterDecision, TaskExecutionSummary
from router_agent import RouterAgent
from task_executor import TaskExecutor
from final_answer_agent import FinalAnswerAgent


class A2AOrchestrator:
    """Main orchestrator for the A2A flow system"""
    
    def __init__(self):
        print("🚀 Initializing A2A Orchestrator...")
        
        # Initialize all agents
        self.router_agent = RouterAgent()
        self.task_executor = TaskExecutor()
        self.final_answer_agent = FinalAnswerAgent()
        
        print("✅ A2A Orchestrator initialized with all agents")
    
    async def process_message(self, user_message: str) -> A2AFlowResult:
        """
        Process a user message through the complete A2A flow
        
        Args:
            user_message: The user's input message
            
        Returns:
            A2AFlowResult: Complete result of the A2A flow
        """
        print(f"\n{'='*80}")
        print(f"🎯 A2A FLOW STARTING")
        print(f"📤 USER INPUT: {user_message}")
        print(f"{'='*80}")
        
        flow_start_time = time.time()
        
        try:
            # Step 1: Route the request
            print("\n📍 Step 1: Routing request...")
            routing_decision = await self.router_agent.route_request(user_message)
            
            if routing_decision.decision_type == "final_response":
                # Direct response - no task execution needed
                print("📝 Router decided: Direct response")
                
                total_time = time.time() - flow_start_time
                print(f"\n🏁 A2A Flow completed (direct response) in {total_time:.2f} seconds")
                print(f"📥 FINAL A2A OUTPUT: {routing_decision.content.response[:300]}{'...' if len(routing_decision.content.response) > 300 else ''}")
                print(f"{'='*80}")
                
                return A2AFlowResult(
                    flow_type="direct_response",
                    final_response=routing_decision.content.response,
                    execution_summary=None,
                    total_time=total_time,
                    timestamp=datetime.now()
                )
            
            else:
                # Task execution needed
                print(f"🎯 Router decided: Execute {len(routing_decision.content.tasks)} tasks")
                
                # Step 2: Execute tasks
                print("\n⚙️ Step 2: Executing tasks...")
                task_summary = await self.task_executor.execute_tasks(routing_decision.content.tasks)
                
                # Step 3: Synthesize final response
                print("\n🎯 Step 3: Synthesizing final response...")
                final_response = await self.final_answer_agent.create_final_response(
                    user_message, task_summary
                )
                
                total_time = time.time() - flow_start_time
                
                print(f"\n🏁 A2A Flow completed in {total_time:.2f} seconds")
                print(f"   Tasks executed: {task_summary.total_tasks}")
                print(f"   Successful tasks: {task_summary.successful_tasks}")
                print(f"   Failed tasks: {task_summary.failed_tasks}")
                print(f"📥 FINAL A2A OUTPUT: {final_response.response[:300]}{'...' if len(final_response.response) > 300 else ''}")
                print(f"{'='*80}")
                
                return A2AFlowResult(
                    flow_type="task_execution",
                    final_response=final_response.response,
                    execution_summary=task_summary,
                    total_time=total_time,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            total_time = time.time() - flow_start_time
            error_msg = f"A2A Flow failed: {str(e)}"
            print(f"❌ {error_msg} (after {total_time:.2f} seconds)")
            
            return A2AFlowResult(
                flow_type="direct_response",
                final_response=f"I apologize, but I encountered an error processing your request: {str(e)}",
                execution_summary=None,
                total_time=total_time,
                timestamp=datetime.now()
            )
    
    def process_message_sync(self, user_message: str) -> A2AFlowResult:
        """
        Synchronous wrapper for process_message
        
        Args:
            user_message: The user's input message
            
        Returns:
            A2AFlowResult: Complete result of the A2A flow
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.process_message(user_message))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.process_message(user_message))
    
    async def health_check(self) -> dict:
        """
        Check the health of all agents in the A2A system
        
        Returns:
            dict: Health status of all components
        """
        health_status = {
            "a2a_orchestrator": "healthy",
            "router_agent": "unknown",
            "task_executor": "unknown", 
            "final_answer_agent": "unknown",
            "web_use_agent": "unknown",
            "google_assistant_agent": "unknown"
        }
        
        try:
            # Test router agent
            test_routing = await self.router_agent.route_request("Hello")
            health_status["router_agent"] = "healthy" if test_routing else "unhealthy"
        except:
            health_status["router_agent"] = "unhealthy"
        
        try:
            # Test final answer agent with minimal data
            from a2a_models import TaskExecutionSummary
            test_summary = TaskExecutionSummary(
                total_tasks=0, successful_tasks=0, failed_tasks=0, 
                results=[], total_execution_time=0.0
            )
            test_final = await self.final_answer_agent.create_final_response("test", test_summary)
            health_status["final_answer_agent"] = "healthy" if test_final else "unhealthy"
        except:
            health_status["final_answer_agent"] = "unhealthy"
        
        # Task executor and sub-agents
        try:
            # Check if agents are initialized
            health_status["task_executor"] = "healthy" if self.task_executor else "unhealthy"
            health_status["web_use_agent"] = "healthy" if self.task_executor.web_agent else "unhealthy"
            health_status["google_assistant_agent"] = "healthy" if self.task_executor.assistant_agent else "unhealthy"
        except:
            health_status["task_executor"] = "unhealthy"
            health_status["web_use_agent"] = "unhealthy"
            health_status["google_assistant_agent"] = "unhealthy"
        
        return health_status


# Global A2A orchestrator instance
_a2a_orchestrator = None

def get_a2a_orchestrator() -> A2AOrchestrator:
    """Get the global A2A orchestrator instance"""
    global _a2a_orchestrator
    if _a2a_orchestrator is None:
        _a2a_orchestrator = A2AOrchestrator()
    return _a2a_orchestrator


# Test the A2A orchestrator
async def test_a2a_orchestrator():
    """Test function for the complete A2A orchestrator"""
    orchestrator = A2AOrchestrator()
    
    test_cases = [
        "What is the capital of France?",  # Should be direct response
        "Check the weather and set a reminder for my meeting",  # Should execute tasks
        "Find the latest iPhone price on Apple's website",  # Should execute web task
        "Turn on the lights and play music",  # Should execute assistant tasks
        "How does photosynthesis work?"  # Should be direct response
    ]
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test_message}")
        print(f"{'='*80}")
        
        result = await orchestrator.process_message(test_message)
        
        print(f"\nFlow Type: {result.flow_type}")
        print(f"Total Time: {result.total_time:.2f} seconds")
        print(f"Final Response: {result.final_response[:200]}{'...' if len(result.final_response) > 200 else ''}")
        
        if result.execution_summary:
            print(f"Tasks Summary:")
            print(f"  Total: {result.execution_summary.total_tasks}")
            print(f"  Successful: {result.execution_summary.successful_tasks}")
            print(f"  Failed: {result.execution_summary.failed_tasks}")


if __name__ == "__main__":
    asyncio.run(test_a2a_orchestrator())