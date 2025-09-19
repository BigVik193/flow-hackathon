#!/usr/bin/env python3
"""
Google Assistant Agent for A2A Flow
===================================

Specialized agent for Google Assistant tasks using the Airia API.
Handles device control, reminders, calendar events, weather, news, and other
Google Assistant capabilities through the Airia pipeline.
"""

import asyncio
import os
import time
import aiohttp
from typing import Optional
import json

from a2a_models import AiriaRequest, AiriaResponse


class GoogleAssistantAgent:
    """Agent specialized for Google Assistant tasks via Airia API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("AIRIA_API_KEY")
        self.pipeline_id = "efeafd70-2258-4e26-9433-f207f7d11481"
        self.base_url = "https://api.airia.ai/v2/PipelineExecution"
        
        if not self.api_key:
            print("⚠️ AIRIA_API_KEY not found in environment variables")
        
        print("✅ Google Assistant Agent initialized")
    
    async def execute_assistant_task(self, instructions: str) -> AiriaResponse:
        """
        Execute a Google Assistant task through the Airia API
        
        Args:
            instructions: Natural language instructions for Google Assistant
            
        Returns:
            AiriaResponse: Result of the assistant task execution
        """
        if not self.api_key:
            return AiriaResponse(
                success=False,
                response="",
                error_message="Missing AIRIA_API_KEY environment variable"
            )
        
        start_time = time.time()
        
        try:
            print(f"🗣️ Google Assistant executing: '{instructions[:100]}{'...' if len(instructions) > 100 else ''}'")
            print(f"📤 Google Assistant Agent INPUT: {instructions}")
            
            # Prepare the API request
            url = f"{self.base_url}/{self.pipeline_id}"
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "userInput": instructions,
                "asyncOutput": False
            }
            
            # Make the API call
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    
                    execution_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract the response from the Airia API result
                        # The exact structure may vary based on Airia's response format
                        response_text = self._extract_response_from_airia_result(result)
                        
                        print(f"✅ Google Assistant task completed in {execution_time:.2f} seconds")
                        print(f"📥 Google Assistant Agent OUTPUT: {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
                        
                        return AiriaResponse(
                            success=True,
                            response=response_text,
                            error_message=None
                        )
                    else:
                        error_text = await response.text()
                        error_msg = f"Airia API error: HTTP {response.status} - {error_text}"
                        print(f"❌ {error_msg}")
                        
                        return AiriaResponse(
                            success=False,
                            response="",
                            error_message=error_msg
                        )
                        
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Airia API request timed out after {execution_time:.2f} seconds"
            print(f"❌ {error_msg}")
            
            return AiriaResponse(
                success=False,
                response="",
                error_message=error_msg
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Google Assistant task failed: {str(e)}"
            print(f"❌ {error_msg} (after {execution_time:.2f} seconds)")
            
            return AiriaResponse(
                success=False,
                response="",
                error_message=error_msg
            )
    
    def _extract_response_from_airia_result(self, result: dict) -> str:
        """
        Extract the meaningful response from Airia API result
        
        Args:
            result: Raw JSON response from Airia API
            
        Returns:
            str: Extracted response text
        """
        try:
            # Try different possible response structures
            if isinstance(result, dict):
                # Common response patterns
                if "response" in result:
                    return str(result["response"])
                elif "output" in result:
                    return str(result["output"])
                elif "result" in result:
                    return str(result["result"])
                elif "data" in result:
                    if isinstance(result["data"], dict) and "response" in result["data"]:
                        return str(result["data"]["response"])
                    else:
                        return str(result["data"])
                elif "message" in result:
                    return str(result["message"])
                else:
                    # If no known structure, return the full result as string
                    return json.dumps(result, indent=2)
            else:
                return str(result)
                
        except Exception as e:
            print(f"⚠️ Error extracting response from Airia result: {e}")
            return str(result)
    
    def execute_assistant_task_sync(self, instructions: str) -> AiriaResponse:
        """
        Synchronous wrapper for execute_assistant_task
        
        Args:
            instructions: Natural language instructions for Google Assistant
            
        Returns:
            AiriaResponse: Result of the assistant task execution
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.execute_assistant_task(instructions))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.execute_assistant_task(instructions))
    
    async def check_health(self) -> bool:
        """
        Check if the Airia API is accessible and working
        
        Returns:
            bool: True if the API is healthy, False otherwise
        """
        try:
            # Simple test request to check API health
            test_response = await self.execute_assistant_task("Hello, can you hear me?")
            return test_response.success
        except:
            return False


# Test the Google Assistant agent
async def test_google_assistant_agent():
    """Test function for the Google Assistant agent"""
    agent = GoogleAssistantAgent()
    
    # Check if we have the required credentials
    if not agent.api_key:
        print("❌ Cannot test Google Assistant agent - missing API credentials")
        print("Please set AIRIA_API_KEY environment variable")
        return
    
    test_cases = [
        "What's the weather like today?",
        "Set a reminder for my meeting tomorrow at 2 PM",
        "What's on my calendar for today?",
        "Turn on the living room lights",
        "Play some relaxing music",
        "What's the latest news?"
    ]
    
    for i, test_instruction in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test_instruction}")
        print(f"{'='*60}")
        
        response = await agent.execute_assistant_task(test_instruction)
        
        print(f"Success: {response.success}")
        if response.success:
            print(f"Response: {response.response[:300]}{'...' if len(response.response) > 300 else ''}")
        else:
            print(f"Error: {response.error_message}")


if __name__ == "__main__":
    asyncio.run(test_google_assistant_agent())