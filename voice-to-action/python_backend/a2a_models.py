#!/usr/bin/env python3
"""
A2A (Agent-to-Agent) Flow Data Models
=====================================

Defines Pydantic models for structured communication between agents in the
multi-agent conversational system.
"""

from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    """Available task types for the A2A system"""
    GOOGLE_ASSISTANT = "google_assistant"
    WEB_USE = "web_use"


class Task(BaseModel):
    """Individual task to be executed by a specialized agent"""
    task_type: TaskType = Field(description="Type of task (google_assistant or web_use)")
    instructions: str = Field(description="Natural language instructions for the specialized agent")
    task_id: Optional[str] = Field(default=None, description="Unique identifier for this task")


class TaskList(BaseModel):
    """Collection of tasks to be executed"""
    tasks: List[Task] = Field(description="List of tasks to execute in order")
    reasoning: str = Field(description="Explanation of why these tasks are needed")


class FinalResponse(BaseModel):
    """Direct response without needing task execution"""
    response: str = Field(description="The final answer to the user's question")
    reasoning: str = Field(description="Explanation of why no tasks were needed")


class RouterDecision(BaseModel):
    """Router agent's decision on how to handle the user's request"""
    decision_type: Literal["final_response", "task_list"] = Field(
        description="Whether to provide a final response or execute tasks"
    )
    content: Union[FinalResponse, TaskList] = Field(
        description="Either a final response or a list of tasks to execute"
    )


class TaskResult(BaseModel):
    """Result from executing a single task"""
    task_id: str = Field(description="ID of the executed task")
    task_type: TaskType = Field(description="Type of task that was executed")
    success: bool = Field(description="Whether the task completed successfully")
    result: str = Field(description="The output/result from the task execution")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")
    execution_time: float = Field(description="Time taken to execute the task in seconds")


class TaskExecutionSummary(BaseModel):
    """Summary of all executed tasks"""
    total_tasks: int = Field(description="Total number of tasks executed")
    successful_tasks: int = Field(description="Number of successfully completed tasks")
    failed_tasks: int = Field(description="Number of failed tasks")
    results: List[TaskResult] = Field(description="Results from all executed tasks")
    total_execution_time: float = Field(description="Total time for all tasks in seconds")


class FinalAgentResponse(BaseModel):
    """Final response from the synthesis agent"""
    response: str = Field(description="The final synthesized response to the user")
    summary: str = Field(description="Summary of what was accomplished")
    tasks_performed: Optional[List[str]] = Field(
        default=None, 
        description="List of tasks that were performed"
    )


class A2AFlowResult(BaseModel):
    """Complete result of the A2A flow execution"""
    flow_type: Literal["direct_response", "task_execution"] = Field(
        description="Whether this was a direct response or involved task execution"
    )
    final_response: str = Field(description="The final response to return to the user")
    execution_summary: Optional[TaskExecutionSummary] = Field(
        default=None, 
        description="Summary of task execution if tasks were performed"
    )
    total_time: float = Field(description="Total time for the entire A2A flow")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the flow completed")


# Google Assistant API Models
class AiriaRequest(BaseModel):
    """Request model for Airia API calls"""
    userId: str = Field(description="User ID for the Airia API")
    userInput: str = Field(description="User input/instructions for the Google Assistant")
    asyncOutput: bool = Field(default=False, description="Whether to use async output")


class AiriaResponse(BaseModel):
    """Response model from Airia API"""
    success: bool = Field(description="Whether the API call was successful")
    response: str = Field(description="The response from the Google Assistant")
    error_message: Optional[str] = Field(default=None, description="Error message if call failed")


# Web Use Agent Models
class WebUseRequest(BaseModel):
    """Request model for web use agent"""
    instructions: str = Field(description="Natural language instructions for web browsing")
    url: Optional[str] = Field(default=None, description="Starting URL if specified")


class WebUseResponse(BaseModel):
    """Response model from web use agent"""
    success: bool = Field(description="Whether the web task was completed successfully")
    result: str = Field(description="Description of what was accomplished")
    final_url: Optional[str] = Field(default=None, description="Final URL after task completion")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")