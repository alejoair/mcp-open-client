import json
import logging
from typing import Dict, Any, List
from mcp_open_client.mcp_client import mcp_client_manager

logger = logging.getLogger(__name__)

async def handle_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a tool call from the LLM by routing it to the appropriate MCP server.
    
    Args:
        tool_call: Tool call object from LLM response containing:
            - id: Tool call ID
            - type: Should be "function"
            - function: Object with name and arguments
    
    Returns:
        Tool call result in OpenAI format
    """
    try:
        logger.info(f"Handling tool call: {tool_call}")
        
        # Extract tool information
        tool_call_id = tool_call.get("id")
        function_info = tool_call.get("function", {})
        tool_name = function_info.get("name")
        arguments_str = function_info.get("arguments", "{}")
        
        if not tool_name:
            error_msg = "Tool name not found in tool call"
            logger.error(error_msg)
            return {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": f"Error: {error_msg}"
            }
        
        # Parse arguments
        try:
            arguments = json.loads(arguments_str) if arguments_str else {}
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in tool arguments: {e}"
            logger.error(error_msg)
            return {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": f"Error: {error_msg}"
            }
        
        logger.info(f"Calling MCP tool: {tool_name} with arguments: {arguments}")
        
        # Call the MCP tool
        try:
            result = await mcp_client_manager.call_tool(tool_name, arguments)
            
            # Check if the result contains an error (from MCP client error handling)
            if result and isinstance(result, dict) and 'error' in result:
                # This is an error returned by the MCP client
                error_msg = result['error']
                operation_info = result.get('operation', {})
                
                # Create detailed error message for the LLM
                detailed_error = f"MCP Tool Error: {error_msg}"
                if operation_info:
                    detailed_error += f"\nTool: {operation_info.get('name', tool_name)}"
                    detailed_error += f"\nArguments: {operation_info.get('params', arguments)}"
                
                logger.error(f"MCP tool call failed: {tool_name} - {error_msg}")
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": detailed_error
                }
            
            # Format the successful result for the LLM
            if result:
                # MCP returns a list of content items, we'll join them
                content_parts = []
                for item in result:
                    if hasattr(item, 'text'):
                        content_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        content_parts.append(item['text'])
                    else:
                        content_parts.append(str(item))
                
                content = "\n".join(content_parts) if content_parts else "Tool executed successfully"
            else:
                content = "Tool executed successfully (no output)"
            
            logger.info(f"Tool call successful: {tool_name}")
            return {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": content
            }
            
        except Exception as e:
            error_msg = f"Error executing MCP tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            return {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": f"Error: {error_msg}\nTool: {tool_name}\nArguments: {arguments}"
            }
            
    except Exception as e:
        error_msg = f"Unexpected error in handle_tool_call: {str(e)}"
        logger.error(error_msg)
        return {
            "tool_call_id": tool_call.get("id", "unknown"),
            "role": "tool",
            "content": f"Error: {error_msg}"
        }

async def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get all available MCP tools formatted for OpenAI tool calling.
    
    Returns:
        List of tool definitions in OpenAI format
    """
    try:
        logger.info("Getting available MCP tools")
        print("DEBUG: Getting available MCP tools")
        
        # Check if MCP client is connected
        if not mcp_client_manager.is_connected():
            print("DEBUG: MCP client is not connected")
            logger.warning("MCP client is not connected")
            return []
        
        print("DEBUG: MCP client is connected")
        
        # Get tools from MCP client manager
        mcp_tools = await mcp_client_manager.list_tools()
        print(f"DEBUG: Retrieved {len(mcp_tools) if mcp_tools else 0} MCP tools")
        
        if not mcp_tools:
            logger.info("No MCP tools available")
            print("DEBUG: No MCP tools available")
            return []
        
        # Convert MCP tools to OpenAI format
        openai_tools = []
        for tool in mcp_tools:
            try:
                # MCP tool format to OpenAI tool format
                # Handle both dict and object formats
                if hasattr(tool, 'name'):
                    # FastMCP Tool object
                    name = tool.name
                    description = tool.description
                    input_schema = tool.inputSchema
                else:
                    # Dict format
                    name = tool.get("name", "")
                    description = tool.get("description", "")
                    input_schema = tool.get("inputSchema")
                
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                    }
                }
                
                # Add parameters if available
                if input_schema:
                    openai_tool["function"]["parameters"] = input_schema
                openai_tools.append(openai_tool)
                logger.debug(f"Converted tool: {name}")
                
                
            except Exception as e:
                logger.warning(f"Error converting tool {tool}: {e}")
                continue
        
        logger.info(f"Available tools: {len(openai_tools)}")
        return openai_tools
        
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        return []

def is_tool_call_response(response: Dict[str, Any]) -> bool:
    """
    Check if the LLM response contains tool calls.
    
    Args:
        response: LLM response object
        
    Returns:
        True if response contains tool calls
    """
    try:
        choices = response.get("choices", [])
        if not choices:
            return False
            
        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls")
        
        return tool_calls is not None and len(tool_calls) > 0
        
    except Exception as e:
        logger.error(f"Error checking for tool calls: {e}")
        return False

def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract tool calls from LLM response.
    
    Args:
        response: LLM response object
        
    Returns:
        List of tool call objects
    """
    try:
        choices = response.get("choices", [])
        if not choices:
            return []
            
        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        return tool_calls
        
    except Exception as e:
        logger.error(f"Error extracting tool calls: {e}")
        return []