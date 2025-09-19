#!/usr/bin/env python3
"""
Task Executor for A2A Flow
==========================

Orchestrates the execution of tasks created by the router agent.
Manages the sequential execution of Google Assistant and Web Use tasks,
collecting results and handling errors gracefully.
"""

import asyncio
import time
import uuid
from typing import List, Optional

from a2a_models import (
    Task, TaskType, TaskResult, TaskExecutionSummary,
    WebUseRequest, AiriaResponse
)
from web_use_agent import WebUseAgent
from google_assistant_agent import GoogleAssistantAgent


class TaskExecutor:
    """Executes tasks in sequence and collects results"""
    
    def __init__(self):
        self.web_agent = WebUseAgent()
        self.assistant_agent = GoogleAssistantAgent()
        print("✅ Task Executor initialized with all agents")
    
    async def execute_tasks(self, tasks: List[Task]) -> TaskExecutionSummary:
        """
        Execute a list of tasks sequentially
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            TaskExecutionSummary: Summary of all task executions
        """
        if not tasks:
            return TaskExecutionSummary(
                total_tasks=0,
                successful_tasks=0,
                failed_tasks=0,
                results=[],
                total_execution_time=0.0
            )
        
        print(f"🚀 Task Executor starting execution of {len(tasks)} tasks")
        start_time = time.time()
        
        results: List[TaskResult] = []
        successful_tasks = 0
        failed_tasks = 0
        
        for i, task in enumerate(tasks, 1):
            # Generate a unique task ID if not provided
            task_id = task.task_id or f"task_{i}_{str(uuid.uuid4())[:8]}"
            task.task_id = task_id
            
            print(f"\n📋 Executing Task {i}/{len(tasks)}: {task.task_type.value}")
            print(f"   Task ID: {task_id}")
            print(f"   Instructions: {task.instructions[:100]}{'...' if len(task.instructions) > 100 else ''}")
            print(f"📤 Task Executor INPUT to {task.task_type.value}: {task.instructions}")
            
            task_start_time = time.time()
            
            try:
                if task.task_type == TaskType.WEB_USE:
                    result = await self._execute_web_task(task)
                elif task.task_type == TaskType.GOOGLE_ASSISTANT:
                    result = await self._execute_assistant_task(task)
                else:
                    # Unknown task type
                    result = TaskResult(
                        task_id=task_id,
                        task_type=task.task_type,
                        success=False,
                        result="",
                        error_message=f"Unknown task type: {task.task_type}",
                        execution_time=0.0
                    )
                
                result.execution_time = time.time() - task_start_time
                results.append(result)
                
                if result.success:
                    successful_tasks += 1
                    print(f"   ✅ Task {i} completed successfully")
                    print(f"📥 Task Executor OUTPUT from {task.task_type.value}: {result.result[:200]}{'...' if len(result.result) > 200 else ''}")
                else:
                    failed_tasks += 1
                    print(f"   ❌ Task {i} failed: {result.error_message}")
                    print(f"📥 Task Executor OUTPUT from {task.task_type.value}: ERROR - {result.error_message}")
                
            except Exception as e:
                execution_time = time.time() - task_start_time
                error_result = TaskResult(
                    task_id=task_id,
                    task_type=task.task_type,
                    success=False,
                    result="",
                    error_message=f"Unexpected error: {str(e)}",
                    execution_time=execution_time
                )
                results.append(error_result)
                failed_tasks += 1
                print(f"   ❌ Task {i} failed with exception: {str(e)}")
        
        total_execution_time = time.time() - start_time
        
        print(f"\n🏁 Task execution completed:")
        print(f"   Total tasks: {len(tasks)}")
        print(f"   Successful: {successful_tasks}")
        print(f"   Failed: {failed_tasks}")
        print(f"   Total time: {total_execution_time:.2f} seconds")
        
        return TaskExecutionSummary(
            total_tasks=len(tasks),
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            results=results,
            total_execution_time=total_execution_time
        )
    
    async def _execute_web_task(self, task: Task) -> TaskResult:
        """
        Execute a web use task
        
        Args:
            task: The web use task to execute
            
        Returns:
            TaskResult: Result of the task execution
        """
        try:
            web_request = WebUseRequest(instructions=task.instructions)
            web_response = await self.web_agent.execute_web_task(web_request)
            
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=web_response.success,
                result=web_response.result,
                error_message=web_response.error_message,
                execution_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                result="",
                error_message=f"Web task execution error: {str(e)}",
                execution_time=0.0  # Will be set by caller
            )
    
    async def _execute_assistant_task(self, task: Task) -> TaskResult:
        """
        Execute a Google Assistant task
        
        Args:
            task: The Google Assistant task to execute
            
        Returns:
            TaskResult: Result of the task execution
        """
        try:
            assistant_response = await self.assistant_agent.execute_assistant_task(task.instructions)
            
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=assistant_response.success,
                result=assistant_response.response,
                error_message=assistant_response.error_message,
                execution_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                result="",
                error_message=f"Assistant task execution error: {str(e)}",
                execution_time=0.0  # Will be set by caller
            )
    
    def execute_tasks_sync(self, tasks: List[Task]) -> TaskExecutionSummary:
        """
        Synchronous wrapper for execute_tasks
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            TaskExecutionSummary: Summary of all task executions
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.execute_tasks(tasks))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.execute_tasks(tasks))
    
    async def execute_single_task(self, task: Task) -> TaskResult:
        """
        Execute a single task (convenience method)
        
        Args:
            task: The task to execute
            
        Returns:
            TaskResult: Result of the task execution
        """
        summary = await self.execute_tasks([task])
        return summary.results[0] if summary.results else TaskResult(
            task_id=task.task_id or "unknown",
            task_type=task.task_type,
            success=False,
            result="",
            error_message="No result returned from task execution",
            execution_time=0.0
        )


# Test the task executor
async def test_task_executor():
    """Test function for the task executor"""
    executor = TaskExecutor()
    
    # Create test tasks
    test_tasks = [
        Task(
            task_type=TaskType.WEB_USE,
            instructions="Find the current weather in San Francisco",
            task_id="web_weather_test"
        ),
        Task(
            task_type=TaskType.GOOGLE_ASSISTANT,
            instructions="What's the weather like today?",
            task_id="assistant_weather_test"
        ),
        Task(
            task_type=TaskType.WEB_USE,
            instructions="Search for the latest news about artificial intelligence",
            task_id="web_news_test"
        )
    ]
    
    print("🧪 Testing Task Executor with sample tasks")
    print(f"Tasks to execute: {len(test_tasks)}")
    
    # Execute the tasks
    summary = await executor.execute_tasks(test_tasks)
    
    print(f"\n📊 Execution Summary:")
    print(f"Total Tasks: {summary.total_tasks}")
    print(f"Successful: {summary.successful_tasks}")
    print(f"Failed: {summary.failed_tasks}")
    print(f"Total Time: {summary.total_execution_time:.2f} seconds")
    
    print(f"\n📋 Individual Results:")
    for result in summary.results:
        print(f"\nTask ID: {result.task_id}")
        print(f"Type: {result.task_type}")
        print(f"Success: {result.success}")
        print(f"Time: {result.execution_time:.2f}s")
        if result.success:
            print(f"Result: {result.result[:150]}{'...' if len(result.result) > 150 else ''}")
        else:
            print(f"Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(test_task_executor())