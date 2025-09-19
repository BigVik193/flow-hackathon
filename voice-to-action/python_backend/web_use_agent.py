#!/usr/bin/env python3
"""
Web Use Agent for A2A Flow
==========================

Specialized agent for web browsing tasks using ChatAnthropic with Bright Data MCP connector via SSE.
Handles web navigation, information extraction, form filling, and other web-based actions.
"""

import asyncio
import logging
import os
import time
import traceback
from typing import Optional, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from a2a_models import WebUseRequest, WebUseResponse

# Configure logging for WebUseAgent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebUseAgent:
    """Agent specialized for web browsing and interaction tasks via Bright Data MCP"""
    
    def __init__(self, api_key: Optional[str] = None, bright_data_token: Optional[str] = None):
        logger.info("🔧 Initializing WebUseAgent...")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.bright_data_token = "035eba8ed91687819a3b91273f6e2f2646c5cb2b9f94c2ce38d9ef318531dfcc"
        
        logger.info(f"   API Key present: {bool(self.api_key)}")
        logger.info(f"   Bright Data token present: {bool(self.bright_data_token)}")
        
        self.chat_model = None
        self.mcp_client = None
        self.mcp_tools = []
        self._mcp_initialized = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the ChatAnthropic model"""
        logger.info("🔧 Initializing ChatAnthropic model...")
        
        if not self.api_key:
            logger.error("❌ ANTHROPIC_API_KEY is required for WebUseAgent")
            raise ValueError("ANTHROPIC_API_KEY is required for WebUseAgent")
        
        try:
            logger.info("   Creating ChatAnthropic instance with model: claude-sonnet-4-20250514")
            self.chat_model = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.2,
                max_tokens=4096
            )
            logger.info("✅ Web Use Agent ChatAnthropic initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Web Use Agent: {e}")
            logger.error(f"   Full traceback: {traceback.format_exc()}")
            raise
    
    async def _initialize_mcp(self):
        """Initialize Bright Data MCP connection via SSE"""
        logger.info("🔌 Initializing Bright Data MCP connection...")
        
        if not self.bright_data_token:
            logger.warning("⚠️ BRIGHT_DATA_MCP_TOKEN not found - web browsing will use fallback mode")
            self._mcp_initialized = True
            return
        
        try:
            logger.info("   Importing MultiServerMCPClient...")
            # Import MCP client here to avoid dependency issues if not installed
            from langchain_mcp_adapters.client import MultiServerMCPClient
            logger.info("   ✅ MultiServerMCPClient imported successfully")
            
            # Configure Bright Data MCP with SSE connection
            mcp_config = {
                "bright_data": {
                    "transport": "sse",
                    "url": f"https://mcp.brightdata.com/sse?token={self.bright_data_token}"
                }
            }
            logger.info(f"   MCP Config: {mcp_config}")
            
            logger.info("   Creating MultiServerMCPClient instance...")
            self.mcp_client = MultiServerMCPClient(mcp_config)
            logger.info("   ✅ MultiServerMCPClient created")
            
            # Get available tools from Bright Data MCP
            logger.info("   Fetching available tools from MCP...")
            try:
                self.mcp_tools = await self.mcp_client.get_tools()
                logger.info(f"   ✅ Retrieved {len(self.mcp_tools)} tools from MCP")
                
                # Test the connection by checking if tools are valid
                if not self.mcp_tools:
                    logger.warning("   ⚠️ No tools returned from MCP - may indicate auth issues")
                    
            except Exception as tool_error:
                logger.error(f"   ❌ Failed to get tools from MCP: {tool_error}")
                if "401" in str(tool_error) or "Invalid token" in str(tool_error):
                    logger.error("   🔑 Authentication failed - check BRIGHT_DATA_MCP_TOKEN")
                    logger.error("   🔄 Falling back to ChatAnthropic without web tools")
                    self.mcp_tools = []
                    self._mcp_initialized = True
                    return
                else:
                    raise tool_error
            
            logger.info(f"✅ Bright Data MCP connected via SSE with {len(self.mcp_tools)} tools")
            for tool in self.mcp_tools:
                logger.info(f"   📲 Available tool: {tool.name} - {getattr(tool, 'description', 'No description')}")
            
            self._mcp_initialized = True
                
        except ImportError as e:
            logger.error(f"❌ langchain-mcp-adapters not installed: {e}")
            logger.error("   Install with: pip install langchain-mcp-adapters")
            logger.error(f"   Full traceback: {traceback.format_exc()}")
            self._mcp_initialized = True  # Don't retry
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bright Data MCP: {e}")
            logger.error(f"   Full traceback: {traceback.format_exc()}")
            logger.info("🔄 Will fall back to ChatAnthropic without web browsing tools")
            self._mcp_initialized = True  # Don't retry
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the web use agent"""
        mcp_tools_desc = ""
        if self.mcp_tools:
            tool_names = [tool.name for tool in self.mcp_tools]
            mcp_tools_desc = f"\n\nAvailable Bright Data MCP tools: {', '.join(tool_names)}"
        else:
            mcp_tools_desc = "\n\nNote: No web browsing tools available. Provide best available information from training data."
        
        return f"""You are a Web Use Agent. Your job is to extract and return the specific information the user requested.{mcp_tools_desc}

IMPORTANT: Return the actual information found, not explanations of what you did.

Examples:
- Weather request → Return: "Currently 72°F and sunny in San Francisco with light winds"
- Price request → Return: "iPhone 15 Pro starts at $999 on Apple.com"
- News request → Return: "Breaking: [actual headline and details]"

Focus on the data, not the process. If web tools are unavailable, provide the most current information you have from your training data and note that real-time data may differ."""

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
            logger.info(f"🌐 Web Use Agent executing: '{request.instructions[:100]}{'...' if len(request.instructions) > 100 else ''}'")
            
            # Prepare the prompt for web browsing
            user_prompt = f"Web Task Instructions: {request.instructions}"
            
            if request.url:
                user_prompt += f"\nStarting URL: {request.url}"
                logger.info(f"   Starting URL provided: {request.url}")
            
            user_prompt += "\n\nFind and return the specific information requested. Provide the actual data, not descriptions of your process."
            
            logger.info(f"📤 Web Use Agent INPUT: {request.instructions}")
            logger.debug(f"   Full user prompt: {user_prompt}")
            
            # Initialize MCP if not already done
            if not self._mcp_initialized:
                logger.info("🔄 MCP not initialized yet, initializing now...")
                await self._initialize_mcp()
            else:
                logger.info(f"🔗 MCP already initialized with {len(self.mcp_tools)} tools")
            
            if self.mcp_tools:
                # Use proper LangChain agent pattern with MCP tools
                logger.info(f"🔧 Using MCP tools mode with {len(self.mcp_tools)} tools")
                
                try:
                    logger.info("   Importing LangChain agent components...")
                    from langchain.agents import create_tool_calling_agent, AgentExecutor
                    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
                    logger.info("   ✅ Agent components imported successfully")
                except ImportError as e:
                    logger.error(f"❌ Failed to import agent components: {e}")
                    raise
                
                logger.info(f"🔧 Creating agent with {len(self.mcp_tools)} MCP tools...")
                
                # Create a prompt template for the agent
                logger.info("   Creating prompt template...")
                system_prompt = self._create_system_prompt()
                logger.debug(f"   System prompt: {system_prompt[:200]}...")
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
                logger.info("   ✅ Prompt template created")
                
                # Create agent with MCP tools
                logger.info("   Creating tool-calling agent...")
                try:
                    agent = create_tool_calling_agent(self.chat_model, self.mcp_tools, prompt)
                    logger.info("   ✅ Tool-calling agent created")
                except Exception as e:
                    logger.error(f"❌ Failed to create tool-calling agent: {e}")
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    raise
                
                logger.info("   Creating AgentExecutor...")
                agent_executor = AgentExecutor(
                    agent=agent, 
                    tools=self.mcp_tools, 
                    verbose=True,  # Enable verbose for debugging
                    max_iterations=5,  # Reasonable limit for tool iterations
                    handle_parsing_errors=True,  # Handle parsing errors gracefully
                    return_intermediate_steps=True  # Get intermediate steps for debugging
                )
                logger.info("   ✅ AgentExecutor created with enhanced error handling")
                
                # Execute with the agent
                logger.info("   🚀 Executing agent with user prompt...")
                try:
                    # Use ainvoke with timeout to prevent hanging
                    timeout_seconds = 120  # 2 minute timeout
                    logger.info(f"   Setting execution timeout to {timeout_seconds} seconds")
                    
                    result = await asyncio.wait_for(
                        agent_executor.ainvoke({"input": user_prompt}),
                        timeout=timeout_seconds
                    )
                    logger.info("   ✅ Agent execution completed successfully")
                    
                    # Better result processing with proper content extraction
                    if isinstance(result, dict) and "output" in result:
                        raw_output = result["output"]
                        logger.info(f"   Raw output type: {type(raw_output)}")
                        logger.debug(f"   Raw output: {raw_output}")
                        
                        # Handle different output formats
                        if isinstance(raw_output, list) and len(raw_output) > 0:
                            # Extract text from structured response format
                            first_item = raw_output[0]
                            if isinstance(first_item, dict) and "text" in first_item:
                                result_content = first_item["text"]
                                logger.info("   ✅ Extracted text content from structured response")
                            else:
                                result_content = str(first_item)
                                logger.info("   ⚠️ Using string conversion of first list item")
                        elif isinstance(raw_output, str):
                            result_content = raw_output
                            logger.info("   ✅ Using direct string output")
                        else:
                            result_content = str(raw_output)
                            logger.warning(f"   ⚠️ Converting unexpected output type to string: {type(raw_output)}")
                        
                        logger.info(f"   Result type: {type(result)}")
                        logger.info(f"   Result keys: {result.keys()}")
                        logger.info(f"   Final content type: {type(result_content)}")
                    else:
                        logger.warning(f"   Unexpected result format: {type(result)}")
                        result_content = str(result)
                        
                except asyncio.TimeoutError:
                    logger.error(f"❌ Agent execution timed out after {timeout_seconds} seconds")
                    logger.info("   🔄 Falling back to ChatAnthropic due to timeout...")
                    
                    # Fall back to regular ChatAnthropic
                    system_prompt = self._create_system_prompt()
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt)
                    ]
                    
                    logger.info("   🚀 Executing timeout fallback mode...")
                    response = await self.chat_model.ainvoke(messages)
                    # Ensure result_content is always a string for timeout fallback
                    if hasattr(response, 'content'):
                        result_content = str(response.content)
                    else:
                        result_content = str(response)
                    logger.info("   ✅ Timeout fallback execution completed")
                    
                except Exception as e:
                    logger.error(f"❌ Agent execution failed: {e}")
                    
                    # Check different types of errors and handle appropriately
                    error_str = str(e)
                    
                    if "401" in error_str or "Invalid token" in error_str or "ToolException" in error_str:
                        logger.error("   🔑 MCP tool authentication failed during execution")
                        fallback_reason = "authentication failure"
                    elif "timeout" in error_str.lower() or "TimeoutError" in error_str:
                        logger.error("   ⏰ Execution timeout detected")
                        fallback_reason = "timeout"
                    elif "ConnectionError" in error_str or "SSLError" in error_str:
                        logger.error("   🔌 Network connection issue detected")
                        fallback_reason = "network error"
                    else:
                        logger.error(f"   ❌ Unknown error type: {type(e).__name__}")
                        logger.error(f"   Full traceback: {traceback.format_exc()}")
                        fallback_reason = "unknown error"
                    
                    logger.info(f"   🔄 Falling back to ChatAnthropic due to {fallback_reason}...")
                    
                    # Fall back to regular ChatAnthropic
                    try:
                        system_prompt = self._create_system_prompt()
                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=user_prompt)
                        ]
                        
                        logger.info("   🚀 Executing error fallback mode...")
                        response = await asyncio.wait_for(
                            self.chat_model.ainvoke(messages),
                            timeout=30  # Shorter timeout for fallback
                        )
                        # Ensure result_content is always a string for error fallback
                        if hasattr(response, 'content'):
                            result_content = str(response.content)
                        else:
                            result_content = str(response)
                        logger.info("   ✅ Error fallback execution completed")
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback also failed: {fallback_error}")
                        raise Exception(f"Both agent and fallback failed. Agent error: {e}, Fallback error: {fallback_error}")
                
            else:
                # Fallback to regular ChatAnthropic without tools
                logger.info("🔄 Using fallback mode without MCP tools")
                
                try:
                    system_prompt = self._create_system_prompt()
                    logger.debug(f"   Fallback system prompt: {system_prompt[:200]}...")
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt)
                    ]
                    logger.info(f"   Created {len(messages)} messages for fallback mode")
                    
                    logger.info("   🚀 Invoking ChatAnthropic in fallback mode...")
                    # Use ainvoke with timeout for proper async execution
                    response = await asyncio.wait_for(
                        self.chat_model.ainvoke(messages),
                        timeout=60  # 1 minute timeout for fallback
                    )
                    logger.info("   ✅ ChatAnthropic fallback execution completed")
                    
                    # Ensure result_content is always a string for main fallback
                    if hasattr(response, 'content'):
                        result_content = str(response.content)
                    else:
                        result_content = str(response)
                    logger.info(f"   Response type: {type(response)}")
                    logger.info(f"   Result content type: {type(result_content)}")
                    logger.debug(f"   Response content preview: {str(result_content)[:200]}...")
                    
                except asyncio.TimeoutError:
                    logger.error("❌ Fallback mode also timed out")
                    result_content = "I'm sorry, but I'm currently experiencing technical difficulties accessing current information. Please try again later or check Apple's official website directly for the latest iPhone pricing."
                    
                except Exception as e:
                    logger.error(f"❌ Fallback execution failed: {e}")
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    result_content = "I apologize, but I'm unable to retrieve current iPhone pricing information due to technical issues. Please visit Apple's official website or check with authorized retailers for the most up-to-date pricing."
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Web task completed in {execution_time:.2f} seconds")
            
            # Better result content validation and logging
            # Ensure result_content is always a string before validation
            if not isinstance(result_content, str):
                logger.warning(f"⚠️ Converting non-string result_content to string: {type(result_content)}")
                result_content = str(result_content)
            
            if result_content and len(result_content.strip()) > 0:
                logger.info(f"📥 Web Use Agent OUTPUT: {result_content[:300]}{'...' if len(result_content) > 300 else ''}")
                logger.debug(f"   Full result content: {result_content}")
                logger.info(f"   Result content length: {len(result_content)} characters")
                logger.info(f"   Final result_content type: {type(result_content)}")
            else:
                logger.warning("⚠️ Result content is empty or None")
                result_content = "I was unable to retrieve the requested information. Please try again later."
            
            # Final validation before creating WebUseResponse
            if not isinstance(result_content, str):
                logger.error(f"❌ result_content is not a string: {type(result_content)}")
                result_content = str(result_content)
            
            logger.info(f"✅ Creating WebUseResponse with result_content type: {type(result_content)}")
            return WebUseResponse(
                success=True,
                result=result_content,
                final_url=None,
                error_message=None
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Web task failed: {str(e)}"
            logger.error(f"❌ {error_msg} (after {execution_time:.2f} seconds)")
            logger.error(f"   Full error traceback: {traceback.format_exc()}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error args: {e.args}")
            
            # Provide helpful error message to user
            if "timeout" in str(e).lower():
                error_description = "The web search request timed out. This may be due to high server load or network issues."
            elif "401" in str(e) or "Invalid token" in str(e):
                error_description = "Authentication failed with the web search service."
            elif "connection" in str(e).lower():
                error_description = "Unable to connect to the web search service."
            else:
                error_description = "An unexpected error occurred while processing your request."
            
            logger.error(f"   User-friendly error: {error_description}")
            
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
        logger.info("🔄 Executing web task synchronously...")
        try:
            # Check if we're already in an async context
            try:
                logger.info("   Checking for existing event loop...")
                loop = asyncio.get_running_loop()
                logger.warning("   ⚠️ Already in async context - this may cause issues")
                logger.warning("   Consider using execute_web_task() directly for async contexts")
                # If we're in an async context, we need to run in a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.execute_web_task(request))
                    result = future.result()
                    logger.info("   ✅ Completed with thread pool executor")
                    return result
            except RuntimeError:
                # No event loop running, safe to create new one
                logger.info("   No event loop running, creating new one...")
                result = asyncio.run(self.execute_web_task(request))
                logger.info("   ✅ Completed with new event loop")
                return result
        except Exception as e:
            logger.error(f"❌ Sync execution failed: {e}")
            logger.error(f"   Traceback: {traceback.format_exc()}")
            raise
    
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