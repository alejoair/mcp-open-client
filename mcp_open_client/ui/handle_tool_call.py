import json
import logging
from typing import Dict, Any, List
from mcp_open_client.mcp_client import mcp_client_manager

logger = logging.getLogger(__name__)

def attempt_json_repair(json_str: str) -> tuple[dict, bool]:
    """
    Attempt to repair common JSON formatting issues.
    
    Returns:
        tuple: (parsed_dict, was_repaired)
    """
    if not json_str or json_str.strip() == "":
        return {}, False
    
    original_str = json_str
    repaired = False
    
    try:
        # First try parsing as-is
        return json.loads(json_str), False
    except json.JSONDecodeError:
        pass
    
    # Common repair attempts
    repairs = [
        # Add missing closing quote and brace if string appears unterminated
        lambda s: s + '"' + '}' if s.count('"') % 2 == 1 and not s.rstrip().endswith('}') else s,
        # Add missing closing brace
        lambda s: s + '}' if not s.rstrip().endswith('}') and s.count('{') > s.count('}') else s,
        # Remove trailing comma before closing brace
        lambda s: s.replace(',}', '}').replace(',]', ']'),
        # Fix common escape issues
        lambda s: s.replace('\\"', '"').replace('\\n', '\\\\n'),
    ]
    
    for repair_func in repairs:
        try:
            repaired_str = repair_func(json_str)
            if repaired_str != json_str:
                result = json.loads(repaired_str)
                logger.info(f"Successfully repaired JSON: {original_str[:100]}... -> {repaired_str[:100]}...")
                return result, True
        except (json.JSONDecodeError, Exception):
            continue
    
    # If all repairs failed, return empty dict
    return {}, False

def parse_pydantic_error(error_msg: str, tool_name: str, arguments: dict) -> str:
    """
    Parse Pydantic validation errors and create helpful error messages for the LLM.
    
    Args:
        error_msg: Raw error message from Pydantic
        tool_name: Name of the tool that failed
        arguments: Arguments that were provided
        
    Returns:
        Formatted error message with suggestions
    """
    # Extract missing arguments from Pydantic error
    missing_args = []
    invalid_args = []
    
    if "Missing required argument" in error_msg or "missing_argument" in error_msg:
        # Parse missing argument name from error
        lines = error_msg.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('For further information') and not line.startswith('type=') and not line.startswith('input_value='):
                # This is likely the missing field name
                if not any(keyword in line.lower() for keyword in ['error', 'validation', 'type=', 'input_value=', 'input_type=']):
                    missing_args.append(line)
    
    # Create helpful error message
    if missing_args:
        formatted_error = f"❌ Tool '{tool_name}' validation failed\n\n"
        formatted_error += f"Missing required arguments: {', '.join(missing_args)}\n\n"
        formatted_error += "Arguments provided:\n"
        for key, value in arguments.items():
            formatted_error += f"  ✓ {key}: {repr(value)}\n"
        
        formatted_error += f"\nMissing arguments needed:\n"
        for arg in missing_args:
            formatted_error += f"  ❌ {arg}: REQUIRED\n"
        
        formatted_error += f"\n💡 Please retry the tool call with ALL required parameters included."
        
        # Add specific suggestions for common tools
        if 'file' in tool_name.lower() and 'content' in missing_args:
            formatted_error += f"\n\nExample for {tool_name}:\n"
            formatted_error += f'{{"path": "your_file.py", "content": "your file content here"}}'
        
        return formatted_error
    else:
        # Fallback for other validation errors
        return f"❌ Tool '{tool_name}' validation failed\n\nError: {error_msg}\n\nArguments provided: {arguments}\n\n💡 Please check the tool parameters and try again."

def validate_and_clean_arguments(arguments: dict, tool_name: str) -> dict:
    """
    Validate and clean tool arguments to prevent common issues.
    
    Args:
        arguments: Parsed arguments dictionary
        tool_name: Name of the tool being called
        
    Returns:
        Cleaned arguments dictionary
    """
    if not isinstance(arguments, dict):
        logger.warning(f"Tool '{tool_name}' arguments are not a dictionary: {type(arguments)}")
        return {}
    
    cleaned = {}
    for key, value in arguments.items():
        # Ensure keys are strings
        if not isinstance(key, str):
            logger.warning(f"Tool '{tool_name}' has non-string key: {key} ({type(key)})")
            key = str(key)
        
        # Clean up common value issues
        if isinstance(value, str):
            # Remove null bytes and other problematic characters
            value = value.replace('\x00', '').strip()
        elif value is None:
            # Convert None to empty string for most tools
            value = ""
        
        cleaned[key] = value
    
    return cleaned

async def handle_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a tool call from the LLM by routing it to the appropriate MCP server.
    
    Enhanced with automatic JSON repair and detailed error reporting.
    
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
        logger.debug(f"Tool call structure: {json.dumps(tool_call, indent=2, default=str)}")
        
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
        
        # Parse arguments with automatic repair attempt
        try:
            arguments = json.loads(arguments_str) if arguments_str else {}
        except json.JSONDecodeError as e:
            # Attempt to repair the JSON automatically
            arguments, was_repaired = attempt_json_repair(arguments_str)
            
            if was_repaired:
                logger.warning(f"Successfully repaired malformed JSON for tool '{tool_name}'")
                logger.debug(f"Original: {repr(arguments_str[:200])}...")
            else:
                # Repair failed, return detailed error to LLM
                error_msg = f"Invalid JSON in tool arguments: {e}"
                logger.error(f"JSON parsing failed for tool '{tool_name}': {error_msg}")
                logger.error(f"Raw arguments string: {repr(arguments_str)}")
                
                # Provide more helpful error message to LLM
                detailed_error = f"""JSON parsing error in tool arguments for '{tool_name}': {e}

Please ensure your tool call uses valid JSON format. Common issues:
- Unterminated strings (missing closing quotes)
- Unescaped quotes within strings
- Missing commas between properties
- Trailing commas

Raw arguments received: {repr(arguments_str[:200])}{'...' if len(arguments_str) > 200 else ''}

Please retry with properly formatted JSON."""
                
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": detailed_error
                }
        # Validate and clean arguments
        arguments = validate_and_clean_arguments(arguments, tool_name)
        
        logger.info(f"Calling MCP tool: {tool_name} with arguments: {arguments}")
        
        
        # Call the MCP tool
        try:
            result = await mcp_client_manager.call_tool(tool_name, arguments)
            
            # Check if the result contains an error (from MCP client error handling)
            if result and isinstance(result, dict) and 'error' in result:
                # This is an error returned by the MCP client
                error_msg = result['error']
                operation_info = result.get('operation', {})
                
                # Check if this is a Pydantic validation error and format it nicely
                if "validation error" in error_msg.lower() or "missing required argument" in error_msg.lower():
                    detailed_error = parse_pydantic_error(error_msg, tool_name, arguments)
                else:
                    # Create detailed error message for other types of errors
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
                    print(f"DEBUG: Tool {name} - inputSchema type: {type(input_schema)}, value: {input_schema}")
                else:
                    # Dict format
                    name = tool.get("name", "")
                    description = tool.get("description", "")
                    input_schema = tool.get("inputSchema")
                    print(f"DEBUG: Tool {name} (dict) - inputSchema type: {type(input_schema)}, value: {input_schema}")
                
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                    }
                }
                
                # Add parameters - always provide a valid schema
                if input_schema and isinstance(input_schema, dict):
                    openai_tool["function"]["parameters"] = input_schema
                else:
                    # Provide default empty schema if none available
                    openai_tool["function"]["parameters"] = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                
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