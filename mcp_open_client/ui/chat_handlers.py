"""
Chat handlers refactorizado - versión modular y limpia.
Utiliza los módulos especializados para mejor mantenibilidad.
"""
import asyncio
from typing import Optional, List, Dict, Any

from nicegui import ui

# Import módulos refactorizados
from .generation_control import (
    set_generation_active, reset_generation_state, is_generation_stopped,
    safe_delete_spinner, trigger_stats_update
)
from .conversation_manager_new import (
    get_current_conversation_id, create_new_conversation, add_message, get_messages
)
from .message_processing import (
    convert_storage_to_api_format, find_tool_response
)
from .tool_call_processor import (
    process_meta_tools, process_respond_to_user, process_notify_user_calls,
    process_tool_calls_parallel, filter_meta_tools_for_ui
)


def _get_tool_choice_required():
    """Get tool_choice_required setting from user configuration"""
    from nicegui import app
    user_settings = app.storage.user.get('user-settings', {})
    return user_settings.get('tool_choice_required', False)


async def safe_scroll_to_bottom(scroll_area, delay=0.2):
    """Safely scroll to bottom with error handling and improved timing"""
    try:
        # Try to use ui.timer first (when in UI context)
        try:
            def do_scroll():
                try:
                    scroll_area.scroll_to(percent=1.0)
                except Exception:
                    pass

            ui.timer(delay, do_scroll, once=True)

        except Exception:
            # Fallback: Use asyncio.sleep when ui.timer fails
            async def async_scroll():
                try:
                    await asyncio.sleep(delay)
                    scroll_area.scroll_to(percent=1.0)
                except Exception:
                    pass

            asyncio.create_task(async_scroll())

    except Exception:
        pass


def render_message_to_ui(message: dict, message_container) -> None:
    """Render a single message to the UI"""
    role = message.get('role', 'user')
    content = message.get('content', '')
    # Usar _ui_tool_calls para la visualización (tool calls filtrados)
    tool_calls = message.get('_ui_tool_calls', message.get('tool_calls', []))
    tool_call_id = message.get('tool_call_id')
    was_truncated = message.get('_truncated', False)
    original_length = message.get('_original_length', 0)

    with message_container:
        if role == 'user':
            with ui.card().classes('user-message message-bubble mb-2 max-w-4xl').style('border-left: 4px solid #fbbf24; background: #1e293b; padding: 8px;'):
                from .message_parser import parse_and_render_message
                parse_and_render_message(content, message_container)

                if was_truncated:
                    ui.label(f'Message truncated (original: {original_length:,} chars)').classes('text-xs mt-2 italic').style('color: #fbbf24;')

        elif role == 'assistant':
            if content or tool_calls or was_truncated:
                with ui.card().classes('assistant-message message-bubble mb-2 max-w-5xl').style('border-left: 4px solid #f87171; background: #374151; padding: 8px;') as bot_card:
                    if content:
                        from .message_parser import parse_and_render_message
                        parse_and_render_message(content, bot_card)

                    if was_truncated:
                        ui.label(f'Message truncated (original: {original_length:,} chars)').classes('text-xs mt-2 italic').style('color: #fbbf24;')

                    # Show tool calls if present
                    if tool_calls:
                        ui.separator().style('margin: 0;')
                        from .message_parser import render_tool_call_with_metadata

                        for tool_call in tool_calls:
                            tool_call_id = tool_call.get('id')
                            tool_response = find_tool_response(tool_call_id, get_messages()) if tool_call_id else None
                            render_tool_call_with_metadata(tool_call, tool_response, bot_card)


async def handle_send(input_field, message_container, api_client, scroll_area, send_button=None):
    """Handle sending a message asynchronously with stop generation support"""

    if not (input_field.value and input_field.value.strip()):
        return

    message = input_field.value.strip()
    set_generation_active(True)

    # Ensure we have a current conversation
    if not get_current_conversation_id():
        create_new_conversation()

    # Add user message
    add_message('user', message)

    # Clear input and re-render
    input_field.value = ''
    message_container.clear()
    from .chat_interface import render_messages
    render_messages(message_container)
    await safe_scroll_to_bottom(scroll_area, delay=0.15)

    spinner = None

    try:
        # Show spinner
        with message_container:
            spinner = ui.spinner('dots', size='lg')

        # Get conversation messages and convert to API format
        conversation_messages = get_messages()
        api_messages = convert_storage_to_api_format(conversation_messages)

        # Get available tools
        from .handle_tool_call import get_available_tools, is_tool_call_response, extract_tool_calls, handle_tool_call
        available_tools = await get_available_tools()

        # Make initial API call
        try:
            if available_tools:
                tool_choice_required = _get_tool_choice_required()
                if tool_choice_required:
                    response = await api_client.chat_completion(api_messages, tools=available_tools, tool_choice="required")
                else:
                    response = await api_client.chat_completion(api_messages, tools=available_tools)
            else:
                response = await api_client.chat_completion(api_messages)

        except Exception as api_error:
            spinner = safe_delete_spinner(spinner)
            error_message = f'Error sending message: {str(api_error)}'
            add_message('assistant', error_message)
            message_container.clear()
            render_messages(message_container)
            return

        # Remove spinner after first API call
        spinner = safe_delete_spinner(spinner)

        # Check if generation was stopped
        if is_generation_stopped():
            return

        # Process response
        if is_tool_call_response(response):
            await _process_tool_call_response(response, message_container, scroll_area, api_client, available_tools, handle_tool_call)
        else:
            await _process_text_response(response, message_container, scroll_area)

    except Exception as e:
        spinner = safe_delete_spinner(spinner)
        error_message = f'Error sending message: {str(e)}'
        add_message('assistant', error_message)
        message_container.clear()
        from .chat_interface import render_messages
        render_messages(message_container)

    finally:
        reset_generation_state()
        spinner = safe_delete_spinner(spinner)
        trigger_stats_update()


async def _process_tool_call_response(response, message_container, scroll_area, api_client, available_tools, handle_tool_call):
    """Process response that contains tool calls"""
    from .handle_tool_call import extract_tool_calls

    tool_calls = extract_tool_calls(response)

    # Process meta tools first
    respond_to_user_call, notify_user_calls, remaining_tool_calls = await process_meta_tools(tool_calls, handle_tool_call)

    if respond_to_user_call:
        # Terminal response - process and exit
        success = await process_respond_to_user(respond_to_user_call, handle_tool_call, add_message)
        if success:
            message_container.clear()
            from .chat_interface import render_messages
            render_messages(message_container)
            await safe_scroll_to_bottom(scroll_area, delay=0.1)
        return

    if notify_user_calls:
        # Process notifications
        await process_notify_user_calls(notify_user_calls, handle_tool_call, add_message)
        remaining_tool_calls = []  # Notifications consume all tool calls

    # Add assistant message with proper tool call filtering
    assistant_message = response['choices'][0]['message']
    original_tool_calls = assistant_message.get('tool_calls', [])
    filtered_tool_calls_for_ui = filter_meta_tools_for_ui(original_tool_calls)

    # For OpenAI API: only store tool calls that will have corresponding tool response messages
    # Meta tools (respond_to_user, notify_user) don't create tool responses, they create assistant/system messages
    # So we only store remaining_tool_calls which are non-meta tools that will have proper tool responses
    tool_calls_for_api = remaining_tool_calls[:]  # Only non-meta tool calls

    add_message('assistant', assistant_message.get('content', ''),
                tool_calls=tool_calls_for_api,  # Only tool calls that will have responses
                _ui_tool_calls=filtered_tool_calls_for_ui)  # Filtered for UI

    # Update UI
    message_container.clear()
    from .chat_interface import render_messages
    render_messages(message_container)
    await safe_scroll_to_bottom(scroll_area, delay=0.1)

    # Process remaining tool calls
    if remaining_tool_calls:
        await _process_remaining_tool_calls(remaining_tool_calls, message_container, scroll_area, api_client, available_tools, handle_tool_call)


async def _process_remaining_tool_calls(tool_calls, message_container, scroll_area, api_client, available_tools, handle_tool_call):
    """Process normal (non-meta) tool calls"""

    # Execute tool calls in parallel
    tool_results = await process_tool_calls_parallel(tool_calls, handle_tool_call)

    # Add tool results to conversation
    for tool_result in tool_results:
        tool_metadata = tool_result.get('_tool_metadata', {})
        add_message('tool', tool_result['content'],
                   tool_call_id=tool_result['tool_call_id'],
                   **tool_metadata)

        # Update UI after each tool result
        message_container.clear()
        from .chat_interface import render_messages
        render_messages(message_container)
        await safe_scroll_to_bottom(scroll_area, delay=0.1)

    # Continue processing loop
    await _continue_tool_processing_loop(message_container, scroll_area, api_client, available_tools, handle_tool_call)


async def _continue_tool_processing_loop(message_container, scroll_area, api_client, available_tools, handle_tool_call):
    """Continue processing loop for tool calls"""

    while True:
        if is_generation_stopped():
            break

        # Get updated messages and convert to API format
        conversation_messages = get_messages()
        api_messages = convert_storage_to_api_format(conversation_messages)

        # Show spinner for subsequent calls
        with message_container:
            spinner = ui.spinner('dots', size='lg')

        try:
            # Make API call
            if available_tools:
                tool_choice_required = _get_tool_choice_required()
                if tool_choice_required:
                    response = await api_client.chat_completion(api_messages, tools=available_tools, tool_choice="required")
                else:
                    response = await api_client.chat_completion(api_messages, tools=available_tools)
            else:
                response = await api_client.chat_completion(api_messages)

            spinner = safe_delete_spinner(spinner)

            if is_generation_stopped():
                break

            # Process response
            if response and 'choices' in response and response['choices']:
                assistant_message = response['choices'][0]['message']
                content = assistant_message.get('content', '')
                tool_calls = assistant_message.get('tool_calls', [])

                if not tool_calls:
                    # No more tool calls - add final response and exit
                    add_message('assistant', content)
                    message_container.clear()
                    from .chat_interface import render_messages
                    render_messages(message_container)
                    await safe_scroll_to_bottom(scroll_area, delay=0.1)
                    break

                # Process new tool calls
                await _process_tool_call_response(response, message_container, scroll_area, api_client, available_tools, handle_tool_call)
                break  # _process_tool_call_response handles the continuation
            else:
                break

        except Exception as e:
            spinner = safe_delete_spinner(spinner)
            add_message('assistant', f'Error: {str(e)}')
            message_container.clear()
            from .chat_interface import render_messages
            render_messages(message_container)
            break


async def _process_text_response(response, message_container, scroll_area):
    """Process response that contains only text (no tool calls)"""

    if response and 'choices' in response and response['choices']:
        assistant_message = response['choices'][0]['message']
        content = assistant_message.get('content', '')

        add_message('assistant', content)

        message_container.clear()
        from .chat_interface import render_messages
        render_messages(message_container)
        await safe_scroll_to_bottom(scroll_area, delay=0.1)


# Re-export important functions for compatibility
from .conversation_manager_new import (
    current_conversation_id, get_conversation_storage, create_new_conversation,
    load_conversation, get_current_conversation_id, get_messages, add_message,
    clear_messages, get_all_conversations, delete_conversation,
    save_current_conversation, rename_conversation
)

from .generation_control import (
    set_stop_generation, is_generation_stopped, reset_generation_state,
    set_stats_update_callback, set_conversations_refresh_callback
)