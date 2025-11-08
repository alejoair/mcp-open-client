"""
Módulo para manejo de conversaciones y storage.
Extraído de chat_handlers.py para mejorar modularidad.
"""
import uuid
import asyncio
from typing import Optional, Dict, Any, List
from nicegui import ui, app


# Global variables
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


def get_messages(include_stats: bool = False) -> List[Dict[str, Any]] | Dict[str, Any]:
    """
    Get messages from current conversation

    Args:
        include_stats: If True, include conversation stats in the result

    Returns:
        List of messages or a dict with messages and stats
    """
    if not current_conversation_id:
        return [] if not include_stats else {'messages': [], 'stats': {'total_tokens': 0, 'total_chars': 0, 'message_count': 0}}

    conversations = get_conversation_storage()
    if current_conversation_id in conversations:
        messages = conversations[current_conversation_id]['messages'].copy()
        if include_stats:
            # Get conversation stats
            from .history_manager import history_manager
            stats = history_manager.get_conversation_size(current_conversation_id)
            return {
                'messages': messages,
                'stats': stats
            }
        return messages
    return [] if not include_stats else {'messages': [], 'stats': {'total_tokens': 0, 'total_chars': 0, 'message_count': 0}}


def add_message(role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None, tool_call_id: Optional[str] = None, **metadata) -> None:
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

        # Add any additional metadata
        for key, value in metadata.items():
            message[key] = value

        # Process message through history manager for size limits
        from .history_manager import history_manager
        processed_message = history_manager.process_message_for_storage(message)

        # Only add message if it passed validation (not None)
        if processed_message is not None:
            conversations[current_conversation_id]['messages'].append(processed_message)
        else:
            return  # Exit early if message was rejected

        conversations[current_conversation_id]['updated_at'] = str(uuid.uuid1().time)
        app.storage.user['conversations'] = conversations

        # Check if conversation or total history needs cleanup
        if history_manager.settings['auto_cleanup']:
            # Cleanup conversation if needed
            conv_cleanup = history_manager.cleanup_conversation_if_needed(current_conversation_id)
            if conv_cleanup:
                pass

        # Log conversation size with accurate token count from tiktoken
        conv_size = history_manager.get_conversation_size(current_conversation_id)

        # Trigger auto-rename check
        asyncio.create_task(_check_auto_rename_conversation())


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


def save_current_conversation() -> None:
    """Save current conversation to storage"""
    # This is automatically handled by NiceGUI's storage system
    pass


async def _check_auto_rename_conversation():
    """Check if current conversation should be auto-renamed and perform the rename."""
    global current_conversation_id

    if not current_conversation_id:
        return

    try:
        from .conversation_title_manager import get_title_manager

        conversations = get_conversation_storage()
        if current_conversation_id not in conversations:
            return

        conversation = conversations[current_conversation_id]
        messages = conversation.get('messages', [])

        title_manager = get_title_manager()
        should_rename = title_manager.should_auto_rename(messages)

        if should_rename:
            current_title = conversation.get('title', '')

            if current_title.startswith('Conversation'):
                new_title = await title_manager.generate_conversation_title(messages)

                conversations[current_conversation_id]['title'] = new_title
                conversations[current_conversation_id]['updated_at'] = str(uuid.uuid1().time)
                app.storage.user['conversations'] = conversations

                # Refresh conversations list and force UI update
                try:
                    from .generation_control import trigger_conversations_refresh
                    trigger_conversations_refresh()

                    # Force a complete UI update
                    ui.update()

                    print(f"Auto-rename: Successfully updated UI for new title '{new_title}'")
                except Exception as refresh_error:
                    print(f"Warning: Could not refresh conversations list: {refresh_error}")

    except Exception as e:
        print(f"Error in auto-rename: {e}")


def rename_conversation(conversation_id: str, new_title: str) -> bool:
    """
    Manually rename a conversation.

    Args:
        conversation_id: ID of the conversation to rename
        new_title: New title for the conversation

    Returns:
        True if rename was successful, False otherwise
    """
    try:
        from .conversation_title_manager import get_title_manager

        conversations = get_conversation_storage()
        if conversation_id not in conversations:
            return False

        # Validate the new title
        title_manager = get_title_manager()
        validated_title = title_manager.validate_title(new_title)

        # Update conversation title
        conversations[conversation_id]['title'] = validated_title
        conversations[conversation_id]['updated_at'] = str(uuid.uuid1().time)
        app.storage.user['conversations'] = conversations

        # Refresh conversations list in UI
        try:
            from .generation_control import trigger_conversations_refresh
            trigger_conversations_refresh()
        except Exception as e:
            print(f"Error refreshing conversations list: {e}")
            # Don't force reload - just skip the refresh
            pass

        return True

    except Exception as e:
        print(f"Error renaming conversation: {str(e)}")
        return False