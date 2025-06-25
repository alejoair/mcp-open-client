import uuid
import json
from typing import Optional, List, Dict, Any
from nicegui import ui, app
from .message_parser import parse_and_render_message
from .history_manager import history_manager
import asyncio
import json

# Global variables
current_conversation_id: Optional[str] = None
stats_update_callback: Optional[callable] = None

# Generation control variables
generation_active = False
stop_generation = False

def set_stop_generation():
    """Set the stop generation flag"""
    global stop_generation
    stop_generation = True

def is_generation_stopped():
    """Check if generation should be stopped"""
    return stop_generation

def reset_generation_state():
    """Reset generation state"""
    global generation_active, stop_generation
    generation_active = False
    stop_generation = False

def get_conversation_storage() -> Dict[str, Any]:
    """Get or initialize conversation storage"""
    if 'conversations' not in app.storage.user:
        app.storage.user['conversations'] = {}
    return app.storage.user['conversations']

def create_new_conversation() -> str:
    """Create a new conversation and return its ID"""
    global current_conversation_id
    conversation_id = str(uuid.uuid4())
    conversations = get_conversation_storage()
    conversations[conversation_id] = {
        'id': conversation_id,
        'title': f'Conversation {len(conversations) + 1}',
        'messages': [],
        'created_at': str(uuid.uuid1().time),
        'updated_at': str(uuid.uuid1().time)
    }
    current_conversation_id = conversation_id
    app.storage.user['conversations'] = conversations
    return conversation_id

def load_conversation(conversation_id: str) -> None:
    """Load a specific conversation"""
    global current_conversation_id
    conversations = get_conversation_storage()
    if conversation_id in conversations:
        current_conversation_id = conversation_id
        # Update stats when conversation changes
        if stats_update_callback:
            stats_update_callback()

def get_current_conversation_id() -> Optional[str]:
    """Get the current conversation ID"""
    return current_conversation_id

def set_stats_update_callback(callback: callable) -> None:
    """Set the callback function to update stats"""
    global stats_update_callback
    stats_update_callback = callback

def get_messages() -> List[Dict[str, Any]]:
    """Get messages from current conversation"""
    if not current_conversation_id:
        return []
    
    conversations = get_conversation_storage()
    if current_conversation_id in conversations:
        return conversations[current_conversation_id]['messages'].copy()
    return []

def add_message(role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None, tool_call_id: Optional[str] = None) -> None:
    """Add a message to the current conversation"""
    if not current_conversation_id:
        create_new_conversation()
    
    conversations = get_conversation_storage()
    if current_conversation_id in conversations:
        message = {
            'role': role,
            'content': content,
            'timestamp': str(uuid.uuid1().time)
        }
        
        # Add tool calls if present (for assistant messages)
        if tool_calls:
            message['tool_calls'] = tool_calls
            
        # Add tool call ID if present (for tool messages)
        if tool_call_id:
            message['tool_call_id'] = tool_call_id
        
        # Process message through history manager for size limits
        processed_message = history_manager.process_message_for_storage(message)
        
        # Only add message if it passed validation (not None)
        if processed_message is not None:
            print(f"Message processed: original size: {len(json.dumps(message))}, processed size: {len(json.dumps(processed_message))}")
            conversations[current_conversation_id]['messages'].append(processed_message)
        else:
            print(f"Warning: Message was rejected during validation and not stored: {role} - {content[:50]}...")
            return  # Exit early if message was rejected
        conversations[current_conversation_id]['updated_at'] = str(uuid.uuid1().time)
        app.storage.user['conversations'] = conversations
        
        # Log conversation size
        conv_size = history_manager.get_conversation_size(current_conversation_id)
        print(f"Conversation {current_conversation_id} size: {conv_size['total_tokens']} tokens ({conv_size['total_chars']} chars), {conv_size['message_count']} messages")
        
        # Check if conversation or total history needs cleanup
        if history_manager.settings['auto_cleanup']:
            # Cleanup conversation if needed
            conv_cleanup = history_manager.cleanup_conversation_if_needed(current_conversation_id)
            if conv_cleanup:
                print(f"Conversation cleanup performed for {current_conversation_id}")
            
            # Note: Global history cleanup disabled - only per-conversation limits apply
        
        # Update stats in UI if callback is set
        if stats_update_callback:
            stats_update_callback()

def find_tool_response(tool_call_id: str) -> Optional[str]:
    """Find the tool response for a given tool call ID"""
    messages = get_messages()
    for msg in messages:
        if (msg.get('role') == 'tool' and 
            msg.get('tool_call_id') == tool_call_id):
            return msg.get('content', '')
    return None

def render_message_to_ui(message: dict, message_container) -> None:
    """Render a single message to the UI"""
    role = message.get('role', 'user')
    content = message.get('content', '')
    tool_calls = message.get('tool_calls', [])
    tool_call_id = message.get('tool_call_id')
    was_truncated = message.get('_truncated', False)
    original_length = message.get('_original_length', 0)
    
    with message_container:
        if role == 'user':
            with ui.card().classes('user-message message-bubble ml-auto mb-2 mr-0 max-w-4xl bg-blue-900/20 border-l-4 border-blue-400') as user_card:
                parse_and_render_message(content, user_card)
                
                # Show truncation notice if message was truncated
                if was_truncated:
                    ui.label(f'⚠️ Message truncated (original: {original_length:,} chars)').classes('text-xs text-yellow-400 mt-2 italic')
        elif role == 'assistant':
            with ui.card().classes('assistant-message message-bubble mb-2 ml-0 max-w-5xl bg-gray-800/30 border-l-4 border-gray-500') as bot_card:
                if content:
                    parse_and_render_message(content, bot_card)
                
                # Show truncation notice if message was truncated
                if was_truncated:
                    ui.label(f'⚠️ Message truncated (original: {original_length:,} chars)').classes('text-xs text-yellow-400 mt-2 italic')
                
                # Show tool calls if present
                if tool_calls:
                    ui.separator().classes('my-2')
                    for i, tool_call in enumerate(tool_calls):
                        function_info = tool_call.get('function', {})
                        tool_name = function_info.get('name', 'unknown')
                        tool_args = function_info.get('arguments', '{}')
                        
                        # Find corresponding tool response
                        tool_call_id = tool_call.get('id')
                        tool_response = find_tool_response(tool_call_id) if tool_call_id else None
                        
                        with ui.expansion(f"{tool_name}",
                                        icon=None,
                                        value=False).classes('w-full max-w-full border-l-4 border-blue-400 mb-2 overflow-hidden text-sm').props('dense header-class="text-sm font-normal"'):
                            # Tool Call Section
                            ui.label('Call:').classes('font-semibold text-blue-300 mt-1')
                            ui.code(tool_name, language='text').classes('w-full overflow-x-auto')
                            ui.label('Arguments:').classes('font-semibold text-blue-300')
                            try:
                                # Try to format JSON arguments nicely
                                formatted_args = json.dumps(json.loads(tool_args), indent=2)
                                ui.code(formatted_args, language='json').classes('w-full overflow-x-auto')
                            except:
                                ui.code(tool_args, language='json').classes('w-full overflow-x-auto')
                            
                            # Tool Response Section (if available)
                            if tool_response:
                                ui.separator().classes('my-3')
                                ui.label('Response:').classes('font-semibold text-emerald-300')
                                # Use HTML with strict width control to prevent horizontal expansion
                                import html
                                escaped_response = html.escape(tool_response)
                                ui.html(f'''<div style="width: 100%; max-width: 100%; overflow: hidden; box-sizing: border-box;">
                                    <pre style="white-space: pre-wrap; word-wrap: break-word; overflow-wrap: anywhere; width: 100%; max-width: 100%; margin: 0; padding: 0.5rem; background: transparent; font-family: monospace; font-size: 0.875rem; overflow: hidden; box-sizing: border-box;">{escaped_response}</pre>
                                </div>''')
        elif role == 'tool':
            # Skip individual tool messages - they're now grouped with assistant messages
            pass

def save_current_conversation() -> None:
    """Save current conversation to storage"""
    # This is automatically handled by NiceGUI's storage system
    pass

def clear_messages() -> None:
    """Clear messages from current conversation"""
    if not current_conversation_id:
        return
    
    conversations = get_conversation_storage()
    if current_conversation_id in conversations:
        conversations[current_conversation_id]['messages'] = []
        conversations[current_conversation_id]['updated_at'] = str(uuid.uuid1().time)
        app.storage.user['conversations'] = conversations

def get_all_conversations() -> Dict[str, Any]:
    """Get all conversations"""
    return get_conversation_storage()

def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation"""
    global current_conversation_id
    conversations = get_conversation_storage()
    if conversation_id in conversations:
        del conversations[conversation_id]
        app.storage.user['conversations'] = conversations
        
        # If we deleted the current conversation, clear the current ID
        if current_conversation_id == conversation_id:
            current_conversation_id = None

# Global variable to track scroll debouncing
_scroll_timer = None

async def safe_scroll_to_bottom(scroll_area, delay=0.2):
    """Safely scroll to bottom with error handling and improved timing"""
    global _scroll_timer
    
    try:
        # Cancel any existing scroll timer to debounce multiple calls
        if _scroll_timer is not None:
            _scroll_timer.cancel()
        
        # Create a new timer with the specified delay
        def do_scroll():
            try:
                scroll_area.scroll_to(percent=1.0)
            except Exception as e:
                print(f"Scroll error (non-critical): {e}")
        
        # Use ui.timer for better DOM synchronization
        _scroll_timer = ui.timer(delay, do_scroll, once=True)
        
    except Exception as e:
        print(f"Scroll setup error (non-critical): {e}")

def render_tool_call_and_result(chat_container, tool_call, tool_result):
    """Render tool call and result in the UI"""
    with chat_container:
        with ui.card().classes('w-full max-w-full mb-2 bg-yellow-100 overflow-hidden'):
            with ui.element('div').classes('w-full max-w-full overflow-hidden p-2'):
                ui.label('Tool Call:').classes('font-bold')
                ui.markdown(f"**Name:** {tool_call['function']['name']}")
                ui.code(tool_call['function']['arguments'], language='json').classes('w-full max-w-full overflow-x-auto')
        
        with ui.card().classes('w-full max-w-full mb-2 bg-green-100 overflow-hidden'):
            with ui.element('div').classes('w-full max-w-full overflow-hidden p-2'):
                ui.label('Tool Result:').classes('font-bold')
                ui.code(json.dumps(tool_result, indent=2), language='json').classes('w-full max-w-full overflow-x-auto')

async def send_message_to_mcp(message: str, server_name: str, chat_container, message_input):
    """Send message to MCP server and handle response"""
    from mcp_open_client.mcp_client import mcp_client_manager
    
    # Add user message to conversation
    add_message('user', message)
    
    # Clear input
    message_input.value = ''
    
    try:
        # Show spinner while waiting for response
        with chat_container:
            with ui.row().classes('w-full justify-start mb-2'):
                spinner_card = ui.card().classes('bg-gray-200 p-2')
                with spinner_card:
                    ui.spinner('dots', size='md')
                    ui.label('Thinking...')
        
        # Get available tools and resources
        tools = await mcp_client_manager.list_tools()
        resources = await mcp_client_manager.list_resources()
        
        # Prepare the context for the LLM
        context = {
            "message": message,
            "tools": tools,
            "resources": resources
        }
        
        # Send the context to the LLM
        try:
            llm_response = await mcp_client_manager.generate_response(context)
            
            # Check if the LLM response contains tool calls
            if isinstance(llm_response, dict) and 'tool_calls' in llm_response:
                for tool_call in llm_response['tool_calls']:
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    
                    # Execute the tool call
                    tool_result = await mcp_client_manager.call_tool(tool_name, tool_args)
                    
                    # Add tool call to conversation
                    add_message('assistant', f"Calling tool: {tool_name}", tool_calls=[tool_call])
                    
                    # Add tool result to conversation
                    add_message('tool', json.dumps(tool_result, indent=2), tool_call_id=tool_call['id'])
                    
                    # Render tool call and result in UI
                    render_tool_call_and_result(chat_container, tool_call, tool_result)
                
                # Add final assistant response to conversation
                if 'content' in llm_response:
                    add_message('assistant', llm_response['content'])
                    with chat_container:
                        ui.markdown(f"**AI:** {llm_response['content']}").classes('bg-blue-100 p-2 rounded-lg mb-2 max-w-full overflow-wrap-anywhere')
            else:
                # Add assistant response to conversation
                add_message('assistant', llm_response)
                with chat_container:
                    ui.markdown(f"**AI:** {llm_response}").classes('bg-blue-100 p-2 rounded-lg mb-2 max-w-full overflow-wrap-anywhere')
        except Exception as llm_error:
            error_message = f'Error generating LLM response: {str(llm_error)}'
            add_message('assistant', error_message)
            with chat_container:
                ui.markdown(f"**Error:** {error_message}").classes('bg-red-100 p-2 rounded-lg mb-2 max-w-full overflow-wrap-anywhere')
        
        # Remove spinner
        spinner_card.delete()
        
        # Scroll to bottom after adding new content
        await safe_scroll_to_bottom(chat_container)
        
    except Exception as e:
        print(f"Error in send_message_to_mcp: {e}")
        # Remove spinner if error occurs
        if 'spinner_card' in locals():
            spinner_card.delete()
        
        error_message = f'Error communicating with MCP server: {str(e)}'
        add_message('assistant', error_message)

async def handle_send(input_field, message_container, api_client, scroll_area, send_button=None):
    """Handle sending a message asynchronously with stop generation support"""
    global generation_active, stop_generation
    
    if input_field.value and input_field.value.strip():
        message = input_field.value.strip()
        generation_active = True
        stop_generation = False
        
        # Ensure we have a current conversation
        if not get_current_conversation_id():
            create_new_conversation()
        
        # Add user message to conversation storage
        add_message('user', message)
        
        # Clear input
        input_field.value = ''
        
        # Re-render all messages to show the new user message
        message_container.clear()
        from .chat_interface import render_messages
        render_messages(message_container)
        
        # Auto-scroll to bottom after adding user message
        await safe_scroll_to_bottom(scroll_area, delay=0.15)
        
        # Send message to API and get response
        try:
            # Check if generation was stopped before starting
            if stop_generation:
                return
                
            # Show spinner while waiting for response
            with message_container:
                spinner = ui.spinner('dots', size='lg')
            # No need to scroll here, spinner is small
            
            # Get full conversation history for context
            conversation_messages = get_messages()
            
            # Enhanced validation and cleaning for tool call sequences
            def validate_and_clean_messages(messages):
                """
                Comprehensive validation and cleaning of message sequences.
                Handles orphaned tool calls, invalid sequences, and ensures API compatibility.
                """
                if not messages:
                    return []
                
                cleaned_messages = []
                i = 0
                
                while i < len(messages):
                    msg = messages[i]
                    
                    # Skip messages with None content to prevent API errors
                    if msg.get("content") is None:
                        print(f"Warning: Skipping message with None content at index {i}")
                        i += 1
                        continue
                    
                    # If this is an assistant message with tool_calls
                    if (msg["role"] == "assistant" and
                        "tool_calls" in msg and
                        msg["tool_calls"]):
                        
                        # Validate tool_calls structure
                        valid_tool_calls = []
                        for tc in msg["tool_calls"]:
                            if (isinstance(tc, dict) and
                                "id" in tc and
                                "function" in tc and
                                isinstance(tc["function"], dict) and
                                "name" in tc["function"]):
                                valid_tool_calls.append(tc)
                            else:
                                print(f"Warning: Invalid tool call structure: {tc}")
                        
                        if not valid_tool_calls:
                            # No valid tool calls, treat as regular assistant message
                            msg_copy = msg.copy()
                            msg_copy.pop("tool_calls", None)
                            cleaned_messages.append(msg_copy)
                            i += 1
                            continue
                        
                        # Check if the next messages contain all corresponding tool results
                        tool_call_ids = {tc["id"] for tc in valid_tool_calls}
                        found_tool_results = set()
                        tool_result_messages = []
                        
                        # Look ahead for tool results
                        j = i + 1
                        while j < len(messages) and messages[j]["role"] == "tool":
                            tool_msg = messages[j]
                            if ("tool_call_id" in tool_msg and
                                tool_msg["tool_call_id"] in tool_call_ids and
                                tool_msg.get("content") is not None):
                                found_tool_results.add(tool_msg["tool_call_id"])
                                tool_result_messages.append(tool_msg)
                            else:
                                print(f"Warning: Invalid or orphaned tool result: {tool_msg}")
                            j += 1
                        
                        # Only include complete tool call sequences
                        if tool_call_ids == found_tool_results and len(found_tool_results) > 0:
                            # Add the assistant message with valid tool calls
                            msg_copy = msg.copy()
                            msg_copy["tool_calls"] = valid_tool_calls
                            cleaned_messages.append(msg_copy)
                            # Add all valid tool result messages
                            cleaned_messages.extend(tool_result_messages)
                            i = j  # Skip to after the tool results
                        else:
                            # Incomplete sequence - convert to regular assistant message
                            print(f"Warning: Incomplete tool call sequence. Expected: {tool_call_ids}, Found: {found_tool_results}")
                            msg_copy = msg.copy()
                            msg_copy.pop("tool_calls", None)
                            # Add explanation about tool calls if content is empty
                            if not msg_copy.get("content"):
                                msg_copy["content"] = f"[Tool calls were attempted but incomplete]"
                            cleaned_messages.append(msg_copy)
                            i = j  # Skip to after any partial tool results
                    
                    elif msg["role"] == "tool":
                        # Orphaned tool result - skip it
                        print(f"Warning: Skipping orphaned tool result: {msg.get('tool_call_id', 'unknown')}")
                        i += 1
                    
                    else:
                        # Regular message (user, assistant without tool_calls)
                        # Ensure content is not None
                        if msg.get("content") is None:
                            msg_copy = msg.copy()
                            msg_copy["content"] = ""
                        else:
                            msg_copy = msg
                        cleaned_messages.append(msg_copy)
                        i += 1
                
                return cleaned_messages
            
            # Clean the conversation messages with enhanced validation
            conversation_messages = validate_and_clean_messages(conversation_messages)
            
            # Convert to API format with additional safety checks
            api_messages = []
            for msg in conversation_messages:
                # Ensure required fields exist
                if "role" not in msg or "content" not in msg:
                    print(f"Warning: Skipping malformed message: {msg}")
                    continue
                
                api_msg = {
                    "role": msg["role"],
                    "content": msg["content"] or ""  # Ensure content is never None
                }
                
                # Include tool_calls for assistant messages (with validation)
                if (msg["role"] == "assistant" and
                    "tool_calls" in msg and
                    isinstance(msg["tool_calls"], list) and
                    len(msg["tool_calls"]) > 0):
                    api_msg["tool_calls"] = msg["tool_calls"]
                
                # Include tool_call_id for tool messages (with validation)
                if (msg["role"] == "tool" and
                    "tool_call_id" in msg and
                    msg["tool_call_id"]):
                    api_msg["tool_call_id"] = msg["tool_call_id"]
                
                api_messages.append(api_msg)
            
            # Final validation: ensure no orphaned tool results made it through (normal execution)
            api_messages = _final_tool_sequence_validation(api_messages, force_cleanup=False)
            
            # Get available MCP tools for tool calling
            from .handle_tool_call import get_available_tools, is_tool_call_response, extract_tool_calls, handle_tool_call
            available_tools = await get_available_tools()
            
            # Call LLM with tools if available, with enhanced error handling
            try:
                # Validate message sequence but preserve pending tool calls during normal execution
                api_messages = _final_tool_sequence_validation(api_messages, force_cleanup=False)
                
                if available_tools:
                    response = await api_client.chat_completion(api_messages, tools=available_tools)
                else:
                    response = await api_client.chat_completion(api_messages)
            except Exception as api_error:
                error_str = str(api_error)
                
                # Check if it's a tool sequence error
                if ("toolresult" in error_str.lower() or
                    "tool_use" in error_str.lower() or
                    "unexpected" in error_str.lower()):
                    
                    print(f"Tool sequence error detected: {error_str}")
                    
                    # Fallback: Remove all tool calls and try again with clean messages
                    fallback_messages = []
                    for msg in api_messages:
                        if msg["role"] == "tool":
                            continue  # Skip all tool messages
                        elif msg["role"] == "assistant" and "tool_calls" in msg:
                            # Convert to regular assistant message
                            fallback_msg = {
                                "role": "assistant",
                                "content": msg.get("content") or "[Previous tool interaction]"
                            }
                            fallback_messages.append(fallback_msg)
                        else:
                            fallback_messages.append(msg)
                    
                    print(f"Retrying with {len(fallback_messages)} cleaned messages (removed tool calls)")
                    
                    try:
                        # Validate fallback messages but preserve any remaining tool calls
                        fallback_messages = _final_tool_sequence_validation(fallback_messages, force_cleanup=False)
                        
                        if available_tools:
                            response = await api_client.chat_completion(fallback_messages, tools=available_tools)
                        else:
                            response = await api_client.chat_completion(fallback_messages)
                    except Exception as fallback_error:
                        print(f"Fallback also failed: {fallback_error}")
                        raise fallback_error
                else:
                    # Different type of error, re-raise
                    raise api_error
            
            # Check if response contains tool calls
            if is_tool_call_response(response):
                # Handle tool calls
                tool_calls = extract_tool_calls(response)
                
                # Add the assistant message with tool calls to conversation
                assistant_message = response['choices'][0]['message']
                add_message('assistant', assistant_message.get('content', ''), tool_calls=assistant_message.get('tool_calls'))
                
                # Update UI immediately after adding assistant message with tool calls
                message_container.clear()
                from .chat_interface import render_messages
                render_messages(message_container)
                await safe_scroll_to_bottom(scroll_area, delay=0.1)
                
                # Process each tool call with error handling
                tool_results = []
                for tool_call in tool_calls:
                    try:
                        tool_result = await handle_tool_call(tool_call)
                        tool_results.append(tool_result)
                        
                        # Add tool result to conversation storage
                        print(f"DEBUG: Adding tool result to conversation - tool_call_id: {tool_result['tool_call_id']}, content length: {len(tool_result['content'])}")
                        add_message('tool', tool_result['content'], tool_call_id=tool_result['tool_call_id'])
                        
                        # Verify the tool result was added correctly
                        messages_after_add = get_messages()
                        tool_msg_found = False
                        for msg in messages_after_add:
                            if msg.get('role') == 'tool' and msg.get('tool_call_id') == tool_result['tool_call_id']:
                                tool_msg_found = True
                                print(f"DEBUG: Tool result verified in conversation - tool_call_id: {msg.get('tool_call_id')}")
                                break
                        if not tool_msg_found:
                            print(f"ERROR: Tool result not found in conversation after add_message - tool_call_id: {tool_result['tool_call_id']}")
                        
                        # Update UI immediately after each tool result
                        message_container.clear()
                        render_messages(message_container)
                        await safe_scroll_to_bottom(scroll_area, delay=0.1)
                        
                    except Exception as e:
                        # Handle tool call failure - add error message as tool result
                        error_message = f"Error executing tool '{tool_call.get('function', {}).get('name', 'unknown')}': {str(e)}"
                        error_result = {
                            'tool_call_id': tool_call['id'],
                            'content': error_message
                        }
                        tool_results.append(error_result)
                        
                        # Add error result to conversation storage
                        print(f"DEBUG: Adding tool error to conversation - tool_call_id: {tool_call['id']}, error: {error_message}")
                        add_message('tool', error_message, tool_call_id=tool_call['id'])
                        
                        # Verify the tool error was added correctly
                        messages_after_error = get_messages()
                        tool_error_found = False
                        for msg in messages_after_error:
                            if msg.get('role') == 'tool' and msg.get('tool_call_id') == tool_call['id']:
                                tool_error_found = True
                                print(f"DEBUG: Tool error verified in conversation - tool_call_id: {msg.get('tool_call_id')}")
                                break
                        if not tool_error_found:
                            print(f"ERROR: Tool error not found in conversation after add_message - tool_call_id: {tool_call['id']}")
                        
                        # Update UI immediately after error
                        message_container.clear()
                        render_messages(message_container)
                        await safe_scroll_to_bottom(scroll_area, delay=0.1)
                        
                        print(f"Tool call error: {error_message}")
                
                # Note: No need to add to api_messages here since they're already
                # added to conversation storage via add_message() calls above.
                # The next API call will rebuild api_messages from the updated conversation.
                
                # Continue processing until no more tool calls
                while True:
                    # Check if generation was stopped
                    if stop_generation:
                        print("Generation stopped by user")
                        # Clean up any orphaned tool calls before breaking
                        conversation_messages = get_messages()
                        api_messages = []
                        for msg in conversation_messages:
                            api_msg = {
                                "role": msg["role"],
                                "content": msg["content"]
                            }
                            
                            # Include tool_calls for assistant messages
                            if msg["role"] == "assistant" and "tool_calls" in msg:
                                api_msg["tool_calls"] = msg["tool_calls"]
                            
                            # Include tool_call_id for tool messages
                            if msg["role"] == "tool" and "tool_call_id" in msg:
                                api_msg["tool_call_id"] = msg["tool_call_id"]
                            
                            api_messages.append(api_msg)
                        
                        # Apply final validation to clean up orphaned tool calls (STOP PRESSED)
                        cleaned_messages = _final_tool_sequence_validation(api_messages, force_cleanup=True)
                        
                        # If orphaned tool calls were found, update the conversation
                        if len(cleaned_messages) != len(api_messages):
                            print(f"Cleaned up orphaned tool calls: {len(api_messages)} -> {len(cleaned_messages)} messages")
                            # Rebuild conversation from cleaned messages
                            _rebuild_conversation_from_cleaned_messages(cleaned_messages)
                        
                        break
                        
                    # Rebuild api_messages from updated conversation for next API call
                    conversation_messages = get_messages()
                    print(f"DEBUG: Rebuilding api_messages from {len(conversation_messages)} conversation messages")
                    
                    api_messages = []
                    for i, msg in enumerate(conversation_messages):
                        api_msg = {
                            "role": msg["role"],
                            "content": msg["content"]
                        }
                        
                        # Include tool_calls for assistant messages
                        if msg["role"] == "assistant" and "tool_calls" in msg:
                            api_msg["tool_calls"] = msg["tool_calls"]
                            print(f"DEBUG: Message {i} - Assistant with {len(msg['tool_calls'])} tool calls")
                        
                        # Include tool_call_id for tool messages
                        if msg["role"] == "tool" and "tool_call_id" in msg:
                            api_msg["tool_call_id"] = msg["tool_call_id"]
                            print(f"DEBUG: Message {i} - Tool result with tool_call_id: {msg['tool_call_id']}")
                        
                        api_messages.append(api_msg)
                    
                    print(f"DEBUG: Built {len(api_messages)} api_messages before validation")
                    
                    # Apply final validation to ensure no orphaned tool results (normal execution)
                    api_messages = _final_tool_sequence_validation(api_messages, force_cleanup=False)
                    
                    print(f"DEBUG: After validation: {len(api_messages)} api_messages")
                    
                    # Check again before making API call
                    if stop_generation:
                        print("Generation stopped by user before API call")
                        # Clean up any orphaned tool calls before breaking (STOP PRESSED)
                        cleaned_messages = _final_tool_sequence_validation(api_messages, force_cleanup=True)
                        if len(cleaned_messages) != len(api_messages):
                            print(f"Cleaned up orphaned tool calls before API call: {len(api_messages)} -> {len(cleaned_messages)} messages")
                            _rebuild_conversation_from_cleaned_messages(cleaned_messages)
                        break
                    
                    # Show spinner for subsequent API calls
                    with message_container:
                        spinner = ui.spinner('dots', size='lg')
                    
                    # Make API call with stop check
                    try:
                        # Validate message sequence but preserve pending tool calls during normal execution
                        api_messages = _final_tool_sequence_validation(api_messages, force_cleanup=False)
                        
                        if available_tools:
                            response = await api_client.chat_completion(api_messages, tools=available_tools)
                        else:
                            response = await api_client.chat_completion(api_messages)
                        
                        # Remove spinner after API call
                        if 'spinner' in locals():
                            spinner.delete()
                            spinner = None  # Mark as deleted
                        
                        # Check if stopped during API call
                        if stop_generation:
                            print("Generation stopped during API call")
                            # Clean up any orphaned tool calls before breaking (STOP PRESSED)
                            cleaned_messages = _final_tool_sequence_validation(api_messages, force_cleanup=True)
                            if len(cleaned_messages) != len(api_messages):
                                print(f"Cleaned up orphaned tool calls after API call: {len(api_messages)} -> {len(cleaned_messages)} messages")
                                _rebuild_conversation_from_cleaned_messages(cleaned_messages)
                            break
                            
                        # Process response normally
                        if response and 'choices' in response and response['choices'] and 'message' in response['choices'][0]:
                            # Extract content and tool_calls from the correct structure
                            assistant_message = response['choices'][0]['message']
                            content = assistant_message.get('content', '')
                            tool_calls = assistant_message.get('tool_calls', [])
                            
                            # Add assistant response
                            add_message('assistant', content, tool_calls)
                            
                            # Re-render messages to show assistant response
                            message_container.clear()
                            from .chat_interface import render_messages
                            render_messages(message_container)
                            await safe_scroll_to_bottom(scroll_area, delay=0.1)
                            
                            # If no tool calls, we're done
                            if not tool_calls:
                                break
                            
                            # Execute tool calls if present
                            print(f"DEBUG: Processing {len(tool_calls)} tool calls in loop")
                            tool_results = []
                            for tool_call in tool_calls:
                                try:
                                    tool_result = await handle_tool_call(tool_call)
                                    tool_results.append(tool_result)
                                    
                                    # Add tool result to conversation storage
                                    print(f"DEBUG: Adding tool result to conversation - tool_call_id: {tool_result['tool_call_id']}, content length: {len(tool_result['content'])}")
                                    add_message('tool', tool_result['content'], tool_call_id=tool_result['tool_call_id'])
                                    
                                    # Update UI immediately after each tool result
                                    message_container.clear()
                                    from .chat_interface import render_messages
                                    render_messages(message_container)
                                    await safe_scroll_to_bottom(scroll_area, delay=0.1)
                                    
                                except Exception as e:
                                    # Handle tool call failure - add error message as tool result
                                    error_message = f"Error executing tool '{tool_call.get('function', {}).get('name', 'unknown')}': {str(e)}"
                                    error_result = {
                                        'tool_call_id': tool_call['id'],
                                        'content': error_message
                                    }
                                    tool_results.append(error_result)
                                    
                                    # Add error result to conversation storage
                                    print(f"DEBUG: Adding tool error to conversation - tool_call_id: {tool_call['id']}, error: {error_message}")
                                    add_message('tool', error_message, tool_call_id=tool_call['id'])
                                    
                                    # Update UI immediately after error
                                    message_container.clear()
                                    from .chat_interface import render_messages
                                    render_messages(message_container)
                                    await safe_scroll_to_bottom(scroll_area, delay=0.1)
                                    
                                    print(f"Tool call error: {error_message}")
                            
                            # Continue to next iteration to process tool results
                            continue
                                
                        else:
                            print("No valid response received")
                            print(f"Response structure: {response}")
                            break
                            
                    except Exception as api_error:
                        print(f"API call error: {api_error}")
                        # Remove spinner on error
                        if 'spinner' in locals() and spinner is not None:
                            spinner.delete()
                        add_message('assistant', f'Error: {str(api_error)}')
                        message_container.clear()
                        from .chat_interface import render_messages
                        render_messages(message_container)
                        break
            else:
               # Handle normal response (no tool calls) from first API call
               if response and 'choices' in response and response['choices'] and 'message' in response['choices'][0]:
                   # Extract content from the correct structure
                   assistant_message = response['choices'][0]['message']
                   content = assistant_message.get('content', '')
                   
                   # Add assistant response
                   add_message('assistant', content)
                   
                   # Re-render messages to show assistant response
                   message_container.clear()
                   from .chat_interface import render_messages
                   render_messages(message_container)
                   await safe_scroll_to_bottom(scroll_area, delay=0.1)
               else:
                   print("No valid response received from first API call")
                   print(f"Response structure: {response}")
       
        except Exception as e:
            # Remove spinner on error
            if 'spinner' in locals() and spinner is not None:
                spinner.delete()
            
            error_message = f'Error sending message: {str(e)}'
            add_message('assistant', error_message)
            
            # Re-render messages to show error
            message_container.clear()
            from .chat_interface import render_messages
            render_messages(message_container)
            
        finally:
            # Clean up any orphaned tool calls before finishing
            try:
                conversation_messages = get_messages()
                api_messages = []
                for msg in conversation_messages:
                    api_msg = {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                    
                    # Include tool_calls for assistant messages
                    if msg["role"] == "assistant" and "tool_calls" in msg:
                        api_msg["tool_calls"] = msg["tool_calls"]
                    
                    # Include tool_call_id for tool messages
                    if msg["role"] == "tool" and "tool_call_id" in msg:
                        api_msg["tool_call_id"] = msg["tool_call_id"]
                    
                    api_messages.append(api_msg)
                
                # Apply final validation to clean up any orphaned tool calls (FINALLY BLOCK - conditional)
                # Only force cleanup if stop was pressed or there was an error
                force_cleanup = stop_generation or 'error' in locals()
                cleaned_messages = _final_tool_sequence_validation(api_messages, force_cleanup=force_cleanup)
                
                # If orphaned tool calls were found, update the conversation
                if len(cleaned_messages) != len(api_messages):
                    print(f"Final cleanup: {len(api_messages)} -> {len(cleaned_messages)} messages")
                    _rebuild_conversation_from_cleaned_messages(cleaned_messages)
                    
                    # Re-render messages to show cleaned conversation
                    message_container.clear()
                    from .chat_interface import render_messages
                    render_messages(message_container)
                    
            except Exception as cleanup_error:
                print(f"Error during final cleanup: {cleanup_error}")
            
            # Always reset generation state when done
            generation_active = False
            stop_generation = False
            
            # Remove spinner if it still exists
            if 'spinner' in locals() and spinner is not None:
                try:
                    spinner.delete()
                except:
                    pass
            
            # Update stats after completion
            if stats_update_callback:
                stats_update_callback()


def _final_tool_sequence_validation(api_messages, force_cleanup=False):
    """
    Final validation to ensure no orphaned tool results.
    Removes any tool messages that don't have corresponding tool calls.
    Only removes unresolved tool calls when force_cleanup=True (stop button pressed).
    
    Args:
        api_messages: List of API-formatted messages
        force_cleanup: If True, removes assistant messages with unresolved tool calls
        
    Returns:
        List of validated messages with orphaned tool results removed
    """
    if not api_messages:
        return []
    
    validated_messages = []
    pending_tool_calls = set()  # Set of tool_call_ids that need responses
    
    for msg in api_messages:
        role = msg.get('role')
        
        if role == 'assistant' and 'tool_calls' in msg:
            # Track tool calls that need responses
            for tc in msg.get('tool_calls', []):
                if tc.get('id'):
                    pending_tool_calls.add(tc['id'])
            validated_messages.append(msg)
            
        elif role == 'tool':
            # Check if this tool result has a corresponding tool call
            tool_call_id = msg.get('tool_call_id')
            if tool_call_id and tool_call_id in pending_tool_calls:
                # Valid tool result
                validated_messages.append(msg)
                pending_tool_calls.remove(tool_call_id)
            else:
                # Orphaned tool result - skip it
                print(f"Final validation: Removing orphaned tool result with ID: {tool_call_id}")
                
        else:
            # Regular user/system/assistant message
            validated_messages.append(msg)
    
    # CRITICAL: Only remove assistant messages with unresolved tool calls when force_cleanup=True
    # This prevents removing valid tool calls that are still in progress during normal execution
    if pending_tool_calls and force_cleanup:
        print(f"Final validation: Found {len(pending_tool_calls)} unresolved tool calls: {pending_tool_calls}")
        print("Removing assistant messages with unresolved tool calls to prevent API errors")
        
        # Remove assistant messages that have unresolved tool calls
        final_validated_messages = []
        for msg in validated_messages:
            if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                # Check if this assistant message has any unresolved tool calls
                has_unresolved = False
                for tc in msg.get('tool_calls', []):
                    if tc.get('id') in pending_tool_calls:
                        has_unresolved = True
                        break
                
                if has_unresolved:
                    print(f"Removing assistant message with unresolved tool calls: {[tc.get('id') for tc in msg.get('tool_calls', [])]}")
                    continue
            
            final_validated_messages.append(msg)
        
        validated_messages = final_validated_messages
        print(f"Final validation: {len(api_messages)} -> {len(validated_messages)} messages")
    elif pending_tool_calls and not force_cleanup:
        # Just log that there are pending tool calls but don't remove them (normal execution)
        print(f"Final validation: Found {len(pending_tool_calls)} pending tool calls (normal execution - not removing)")
    
    return validated_messages


def _rebuild_conversation_from_cleaned_messages(cleaned_api_messages):
    """
    Rebuild the conversation storage from cleaned API messages.
    This removes orphaned tool calls from the stored conversation.
    
    Args:
        cleaned_api_messages: List of validated API messages without orphaned tool calls
    """
    global current_conversation_id
    
    if not current_conversation_id:
        return
    
    conversations = get_conversation_storage()
    if current_conversation_id not in conversations:
        return
    
    # Convert API messages back to conversation format
    new_messages = []
    for api_msg in cleaned_api_messages:
        conv_msg = {
            "role": api_msg["role"],
            "content": api_msg["content"],
            "timestamp": str(uuid.uuid1().time)
        }
        
        # Include tool_calls for assistant messages
        if api_msg["role"] == "assistant" and "tool_calls" in api_msg:
            conv_msg["tool_calls"] = api_msg["tool_calls"]
        
        # Include tool_call_id for tool messages
        if api_msg["role"] == "tool" and "tool_call_id" in api_msg:
            conv_msg["tool_call_id"] = api_msg["tool_call_id"]
        
        new_messages.append(conv_msg)
    
    # Update the conversation with cleaned messages
    conversations[current_conversation_id]["messages"] = new_messages
    conversations[current_conversation_id]["updated_at"] = str(uuid.uuid1().time)
    
    print(f"Rebuilt conversation with {len(new_messages)} cleaned messages")