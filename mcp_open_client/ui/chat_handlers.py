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
            with ui.card().classes('user-message message-bubble mb-2 max-w-4xl').style('border-left: 4px solid #1e40af; background: #1e293b; padding: 8px;') as user_card:
                parse_and_render_message(content, user_card)
                
                # Show truncation notice if message was truncated
                if was_truncated:
                    ui.label(f'⚠️ Message truncated (original: {original_length:,} chars)').classes('text-xs text-yellow-400 mt-2 italic')
        elif role == 'assistant':
            with ui.card().classes('assistant-message message-bubble mb-2 max-w-5xl border-l-4 border-red-300').style('background: #374151; padding: 8px;') as bot_card:
                if content:
                    parse_and_render_message(content, bot_card)
                
                # Show truncation notice if message was truncated
                if was_truncated:
                    ui.label(f'⚠️ Message truncated (original: {original_length:,} chars)').classes('text-xs text-yellow-400 mt-2 italic')
                
                # Show tool calls if present
                if tool_calls:
                    ui.separator().style('margin: 0;')
                    for i, tool_call in enumerate(tool_calls):
                        function_info = tool_call.get('function', {})
                        tool_name = function_info.get('name', 'unknown')
                        tool_args = function_info.get('arguments', '{}')
                        
                        # Find corresponding tool response
                        tool_call_id = tool_call.get('id')
                        tool_response = find_tool_response(tool_call_id) if tool_call_id else None
                        
                        with ui.expansion(f"{tool_name}",
                                        icon=None,
                                        value=False).classes('w-full max-w-full border-l-4 border-blue-400 overflow-hidden text-sm').props('dense header-class="text-sm font-normal"').style('max-width: 100%; box-sizing: border-box; margin: 0;'):
                            # Tool Call Section
                            ui.label('Arguments:').classes('font-semibold text-blue-300')
                            try:
                                # Try to format JSON arguments nicely
                                formatted_args = json.dumps(json.loads(tool_args), indent=2)
                                ui.code(formatted_args, language='json').classes('w-full overflow-x-auto')
                            except:
                                ui.code(tool_args, language='json').classes('w-full overflow-x-auto')
                            
                            # Tool Response Section (if available)
                            if tool_response:
                                ui.separator().style('margin: 0;')
                                ui.label('Response:').classes('font-semibold text-emerald-300')
                                # Use HTML with strict width control to prevent horizontal expansion
                                import html
                                escaped_response = html.escape(tool_response)
                                ui.html(f'''<div style="width: 100%; max-width: calc(100vw - 48px); overflow: hidden; box-sizing: border-box;">
                                    <pre style="white-space: pre-wrap; word-wrap: break-word; overflow-wrap: anywhere; width: 100%; max-width: 100%; margin: 0; padding: 0.5rem; background: transparent; font-family: monospace; font-size: 0.875rem; overflow-x: auto; box-sizing: border-box; word-break: break-all;">{escaped_response}</pre>
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
            
            # Simple validation: remove orphaned tool calls
            def clean_orphaned_tools(messages):
                """Remove orphaned tool calls - keep only complete sequences"""
                if not messages:
                    return []
                
                # Convert to API format first
                api_messages = []
                for msg in messages:
                    if not msg.get("content") and msg.get("role") != "assistant":
                        continue
                    
                    api_msg = {
                        "role": msg["role"],
                        "content": msg.get("content") or ""
                    }
                    
                    if msg["role"] == "assistant" and msg.get("tool_calls"):
                        api_msg["tool_calls"] = msg["tool_calls"]
                    elif msg["role"] == "tool" and msg.get("tool_call_id"):
                        api_msg["tool_call_id"] = msg["tool_call_id"]
                    
                    api_messages.append(api_msg)
                
                # Find tool calls that have responses
                tool_call_ids = set()
                tool_response_ids = set()
                
                for msg in api_messages:
                    if msg["role"] == "assistant" and "tool_calls" in msg:
                        for tc in msg["tool_calls"]:
                            tool_call_ids.add(tc["id"])
                    elif msg["role"] == "tool" and "tool_call_id" in msg:
                        tool_response_ids.add(msg["tool_call_id"])
                
                # Remove assistant messages with orphaned tool calls (except the last one)
                cleaned = []
                for i, msg in enumerate(api_messages):
                    if msg["role"] == "assistant" and "tool_calls" in msg:
                        # Check if all tool calls have responses
                        has_orphaned = any(tc["id"] not in tool_response_ids for tc in msg["tool_calls"])
                        is_last_message = i == len(api_messages) - 1
                        
                        if has_orphaned and not is_last_message:
                            # Remove tool_calls from orphaned assistant message
                            cleaned_msg = {"role": msg["role"], "content": msg["content"] or "[Tool call removed]"}
                            cleaned.append(cleaned_msg)
                        else:
                            cleaned.append(msg)
                    elif msg["role"] == "tool":
                        # Only keep tool responses that have corresponding calls
                        if msg["tool_call_id"] in tool_call_ids:
                            cleaned.append(msg)
                    else:
                        cleaned.append(msg)
                
                return cleaned
            
            # Clean conversation messages
            api_messages = clean_orphaned_tools(conversation_messages)
            
            # Get available MCP tools for tool calling
            from .handle_tool_call import get_available_tools, is_tool_call_response, extract_tool_calls, handle_tool_call
            available_tools = await get_available_tools()
            
            # Call LLM with tools if available, with enhanced error handling
            try:
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
                    
                    # Clean orphaned tools before API call
                    api_messages = clean_orphaned_tools(get_messages())
                    
                    print(f"DEBUG: After cleaning: {len(api_messages)} api_messages")
                    
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
                        # Clean orphaned tools before API call
                        api_messages = clean_orphaned_tools(get_messages())
                        
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
            # Reset generation state
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


