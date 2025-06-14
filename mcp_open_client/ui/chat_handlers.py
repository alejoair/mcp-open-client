import uuid
import json
from typing import Optional, List, Dict, Any
from nicegui import ui, app
from .message_parser import parse_and_render_message
import asyncio

# Global variable to track current conversation
current_conversation_id: Optional[str] = None

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

def get_current_conversation_id() -> Optional[str]:
    """Get the current conversation ID"""
    return current_conversation_id

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
        
        conversations[current_conversation_id]['messages'].append(message)
        conversations[current_conversation_id]['updated_at'] = str(uuid.uuid1().time)
        app.storage.user['conversations'] = conversations

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
        with ui.card().classes('w-full mb-2 bg-yellow-100'):
            ui.label('Tool Call:').classes('font-bold')
            ui.markdown(f"**Name:** {tool_call['function']['name']}")
            ui.markdown(f"**Arguments:**\n```json\n{tool_call['function']['arguments']}\n```")
        
        with ui.card().classes('w-full mb-2 bg-green-100'):
            ui.label('Tool Result:').classes('font-bold')
            ui.markdown(f"```json\n{json.dumps(tool_result, indent=2)}\n```")

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
                        ui.markdown(f"**AI:** {llm_response['content']}").classes('bg-blue-100 p-2 rounded-lg mb-2')
            else:
                # Add assistant response to conversation
                add_message('assistant', llm_response)
                with chat_container:
                    ui.markdown(f"**AI:** {llm_response}").classes('bg-blue-100 p-2 rounded-lg mb-2')
        except Exception as llm_error:
            error_message = f'Error generating LLM response: {str(llm_error)}'
            add_message('assistant', error_message)
            with chat_container:
                ui.markdown(f"**Error:** {error_message}").classes('bg-red-100 p-2 rounded-lg mb-2')
        
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

async def handle_send(input_field, message_container, api_client, scroll_area):
    """Handle sending a message asynchronously"""
    if input_field.value and input_field.value.strip():
        message = input_field.value.strip()
        
        # Ensure we have a current conversation
        if not get_current_conversation_id():
            create_new_conversation()
        
        # Add user message to conversation storage
        add_message('user', message)
        
        # Add user message to UI
        with message_container:
            with ui.card().classes('ml-auto mr-4 max-w-md') as user_card:
                ui.label('You:').classes('font-bold mb-2')
                parse_and_render_message(message, user_card)
        
        # Clear input
        input_field.value = ''
        
        # Auto-scroll to bottom after adding user message
        await safe_scroll_to_bottom(scroll_area, delay=0.15)
        
        # Send message to API and get response
        try:
            # Show spinner while waiting for response
            with message_container:
                spinner = ui.spinner('dots', size='lg')
            # No need to scroll here, spinner is small
            
            # Get full conversation history for context
            conversation_messages = get_messages()
            
            # Convert to API format
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
            
            # Get available MCP tools for tool calling
            from .handle_tool_call import get_available_tools, is_tool_call_response, extract_tool_calls, handle_tool_call
            available_tools = await get_available_tools()
            
            # Call LLM with tools if available
            if available_tools:
                response = await api_client.chat_completion(api_messages, tools=available_tools)
            else:
                response = await api_client.chat_completion(api_messages)
            
            # Check if response contains tool calls
            if is_tool_call_response(response):
                # Handle tool calls
                tool_calls = extract_tool_calls(response)
                
                # Add the assistant message with tool calls to conversation
                assistant_message = response['choices'][0]['message']
                add_message('assistant', assistant_message.get('content', ''), tool_calls=assistant_message.get('tool_calls'))
                
                # Process each tool call
                tool_results = []
                for tool_call in tool_calls:
                    tool_result = await handle_tool_call(tool_call)
                    tool_results.append(tool_result)
                    
                    # Add tool result to conversation UI
                    add_message('tool', tool_result['content'], tool_call_id=tool_result['tool_call_id'])
                
                # Update API messages with assistant message including tool calls
                api_messages.append({
                    "role": "assistant",
                    "content": assistant_message.get('content'),
                    "tool_calls": assistant_message.get('tool_calls')
                })
                
                # Add tool results to API messages
                for tool_result in tool_results:
                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_result['tool_call_id'],
                        "content": tool_result['content']
                    })
                
                # Get final response from LLM after tool execution
                final_response = await api_client.chat_completion(api_messages, tools=available_tools)
                bot_response = final_response['choices'][0]['message']['content']
            else:
                # Regular response without tool calls
                bot_response = response['choices'][0]['message']['content']
            
            # Remove spinner
            spinner.delete()
            
            # Add assistant response to conversation storage
            add_message('assistant', bot_response)
            
            # Add bot response to UI
            with message_container:
                with ui.card().classes('mr-auto ml-4') as bot_card:
                    ui.label('Bot:').classes('font-bold mb-2')
                    parse_and_render_message(bot_response, bot_card)
            
            # Refresh conversation manager to update sidebar
            from .conversation_manager import conversation_manager
            conversation_manager.refresh_conversations_list()
            
            # Auto-scroll to bottom after adding bot response (longer delay for complex rendering)
            await safe_scroll_to_bottom(scroll_area, delay=0.25)
            
        except Exception as e:
            # Remove spinner if error occurs
            if 'spinner' in locals():
                spinner.delete()
            
            # Add error message to conversation storage
            error_message = f'Error: {str(e)}'
            add_message('assistant', error_message)
            
            # Add error message to UI
            with message_container:
                with ui.card().classes('mr-auto ml-4 max-w-md') as error_card:
                    ui.label('System:').classes('font-bold mb-2 text-red-600')
                    parse_and_render_message(error_message, error_card)
            
            # Refresh conversation manager to update sidebar
            from .conversation_manager import conversation_manager
            conversation_manager.refresh_conversations_list()
            
            # Auto-scroll to bottom after error message
            await safe_scroll_to_bottom(scroll_area, delay=0.2)
    else:
        # we'll just ignore
        pass