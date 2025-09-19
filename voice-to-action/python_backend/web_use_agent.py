#!/usr/bin/env python3
"""
Web Use Agent for A2A Flow
==========================

Specialized agent for web browsing tasks using ChatAnthropic with Bright Data MCP connector via SSE.
Handles web navigation, information extraction, form filling, and other web-based actions.
"""

import asyncio
import os
import time
from typing import Optional, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from a2a_models import WebUseRequest, WebUseResponse


class WebUseAgent:
    """Agent specialized for web browsing and interaction tasks via Bright Data MCP"""
    
    def __init__(self, api_key: Optional[str] = None, bright_data_token: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.bright_data_token = bright_data_token or os.getenv("BRIGHT_DATA_MCP_TOKEN")
        self.chat_model = None
        self.mcp_client = None
        self.mcp_tools = []
        self._mcp_initialized = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the ChatAnthropic model"""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for WebUseAgent")
        
        try:
            self.chat_model = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.2,
                max_tokens=4096
            )
            print("✅ Web Use Agent ChatAnthropic initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Web Use Agent: {e}")
            raise
    
    async def _initialize_mcp(self):
        """Initialize Bright Data MCP connection via SSE"""
        if not self.bright_data_token:
            print("⚠️ BRIGHT_DATA_MCP_TOKEN not found - web browsing will use fallback mode")
            return
        
        try:
            # Import MCP client here to avoid dependency issues if not installed
            from langchain_mcp_adapters.client import MultiServerMCPClient
            
            # Configure Bright Data MCP with SSE connection
            mcp_config = {
                "bright_data": {
                    "transport": "sse",
                    "url": f"https://mcp.brightdata.com/sse?token={self.bright_data_token}"
                }
            }
            
            self.mcp_client = MultiServerMCPClient(mcp_config)
            
            # Get available tools from Bright Data MCP
            self.mcp_tools = await self.mcp_client.get_tools()
            
            print(f"✅ Bright Data MCP connected via SSE with {len(self.mcp_tools)} tools")
            for tool in self.mcp_tools:
                print(f"   📲 Available tool: {tool.name}")
            
            self._mcp_initialized = True
                
        except ImportError:
            print("❌ langchain-mcp-adapters not installed. Install with: pip install langchain-mcp-adapters")
            self._mcp_initialized = True  # Don't retry
        except Exception as e:
            print(f"❌ Failed to initialize Bright Data MCP: {e}")
            print("🔄 Will fall back to ChatAnthropic without web browsing tools")
            self._mcp_initialized = True  # Don't retry
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the web use agent"""
        mcp_tools_desc = ""
        if self.mcp_tools:
            tool_names = [tool.name for tool in self.mcp_tools]
            mcp_tools_desc = f"\n\nAvailable Bright Data MCP tools: {', '.join(tool_names)}"
        
        return f"""You are a Web Use Agent. Your job is to extract and return the specific information the user requested.{mcp_tools_desc}

IMPORTANT: Return the actual information found, not explanations of what you did.

Examples:
- Weather request → Return: "Currently 72°F and sunny in San Francisco with light winds"
- Price request → Return: "iPhone 15 Pro starts at $999 on Apple.com"
- News request → Return: "Breaking: [actual headline and details]"

Focus on the data, not the process."""

    async def execute_web_task(self, request: WebUseRequest) -> WebUseResponse:
        """
        Execute a web browsing task using Bright Data MCP tools
        
        Args:
            request: WebUseRequest containing task instructions
            
        Returns:
            WebUseResponse: Result of the web task execution
        """
        if not self.chat_model:
            raise RuntimeError("Web Use Agent not properly initialized")
        
        start_time = time.time()
        
        try:
            print(f"🌐 Web Use Agent executing: '{request.instructions[:100]}{'...' if len(request.instructions) > 100 else ''}'")
            
            # Prepare the prompt for web browsing
            user_prompt = f"Web Task Instructions: {request.instructions}"
            
            if request.url:
                user_prompt += f"\nStarting URL: {request.url}"
            
            user_prompt += "\n\nFind and return the specific information requested. Provide the actual data, not descriptions of your process."
            
            print(f"📤 Web Use Agent INPUT: {request.instructions}")
            if request.url:
                print(f"   Starting URL: {request.url}")
            
            # Initialize MCP if not already done
            if not self._mcp_initialized:
                await self._initialize_mcp()
            
            if self.mcp_tools:
                # Use proper LangChain agent pattern with MCP tools
                from langchain.agents import create_tool_calling_agent, AgentExecutor
                from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
                
                print(f"🔧 Creating agent with {len(self.mcp_tools)} MCP tools...")
                
                # Create a prompt template for the agent
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self._create_system_prompt()),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
                
                # Create agent with MCP tools
                agent = create_tool_calling_agent(self.chat_model, self.mcp_tools, prompt)
                agent_executor = AgentExecutor(
                    agent=agent, 
                    tools=self.mcp_tools, 
                    verbose=False,  # Set to True for debugging
                    max_iterations=3,
                    early_stopping_method="generate"
                )
                
                # Execute with the agent
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: agent_executor.invoke({"input": user_prompt})
                )
                
                result_content = result["output"]
                print(f"   🤖 Agent execution completed")
                
            else:
                # Fallback to regular ChatAnthropic without tools
                print("🔄 Using fallback mode without MCP tools")
                
                messages = [
                    SystemMessage(content=self._create_system_prompt()),
                    HumanMessage(content=user_prompt)
                ]
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.chat_model.invoke(messages)
                )
                
                result_content = response.content
            
            execution_time = time.time() - start_time
            print(f"✅ Web task completed in {execution_time:.2f} seconds")
            print(f"📥 Web Use Agent OUTPUT: {result_content[:300]}{'...' if len(result_content) > 300 else ''}")
            
            return WebUseResponse(
                success=True,
                result=result_content,
                final_url=None,
                error_message=None
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Web task failed: {str(e)}"
            print(f"❌ {error_msg} (after {execution_time:.2f} seconds)")
            
            return WebUseResponse(
                success=False,
                result="",
                final_url=None,
                error_message=error_msg
            )
    
    def execute_web_task_sync(self, request: WebUseRequest) -> WebUseResponse:
        """
        Synchronous wrapper for execute_web_task
        
        Args:
            request: WebUseRequest containing task instructions
            
        Returns:
            WebUseResponse: Result of the web task execution
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.execute_web_task(request))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.execute_web_task(request))
    
    async def execute_web_task_from_string(self, instructions: str, url: Optional[str] = None) -> WebUseResponse:
        """
        Execute a web task from string instructions (convenience method)
        
        Args:
            instructions: Natural language instructions for the web task
            url: Optional starting URL
            
        Returns:
            WebUseResponse: Result of the web task execution
        """
        request = WebUseRequest(instructions=instructions, url=url)
        return await self.execute_web_task(request)


# Test the web use agent
async def test_web_use_agent():
    """Test function for the web use agent"""
    agent = WebUseAgent()
    
    test_cases = [
        WebUseRequest(
            instructions="Find the current price of Bitcoin",
            url=None
        ),
        WebUseRequest(
            instructions="Look up the weather forecast for San Francisco today",
            url=None
        ),
        WebUseRequest(
            instructions="Find information about the latest iPhone model and its price",
            url="https://apple.com"
        ),
        WebUseRequest(
            instructions="Search for the top 3 Python learning resources online",
            url=None
        )
    ]
    
    for i, test_request in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test_request.instructions}")
        print(f"{'='*60}")
        
        response = await agent.execute_web_task(test_request)
        
        print(f"Success: {response.success}")
        if response.success:
            print(f"Result: {response.result[:200]}{'...' if len(response.result) > 200 else ''}")
        else:
            print(f"Error: {response.error_message}")


if __name__ == "__main__":
    asyncio.run(test_web_use_agent())