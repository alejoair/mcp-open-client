"""
Módulo para procesamiento y conversión de mensajes entre diferentes formatos.
Extraído de chat_handlers.py para mejorar modularidad.
"""
import uuid
from typing import List, Dict, Any, Optional


def convert_storage_to_api_format(storage_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convierte mensajes de storage a formato API de OpenAI.

    Args:
        storage_messages: Lista de mensajes en formato storage

    Returns:
        Lista de mensajes en formato API
    """
    api_messages = []
    for msg in storage_messages:
        api_msg = {
            "role": msg["role"],
            "content": msg.get("content", "")
        }

        # Include tool_calls for assistant messages
        if msg["role"] == "assistant" and "tool_calls" in msg:
            api_msg["tool_calls"] = msg["tool_calls"]

        # Include tool_call_id for tool messages
        if msg["role"] == "tool" and "tool_call_id" in msg:
            api_msg["tool_call_id"] = msg["tool_call_id"]

        api_messages.append(api_msg)
    return api_messages


def clean_orphaned_tools(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Limpia tool call sequences rotos mientras preserva las llamadas válidas pendientes.
    Enfoque conservador para evitar romper secuencias válidas.
    """
    if not messages:
        return []

    # Convert to API format first
    api_messages = []
    for msg in messages:
        # Keep all messages with valid roles
        if msg.get("role") not in ["user", "assistant", "tool", "system"]:
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

    # Build tool call tracking
    tool_call_ids = set()
    tool_response_ids = set()
    tool_call_positions = {}  # track position of each tool call

    for i, msg in enumerate(api_messages):
        if msg["role"] == "assistant" and "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                tool_call_ids.add(tc["id"])
                tool_call_positions[tc["id"]] = i
        elif msg["role"] == "tool" and "tool_call_id" in msg:
            tool_response_ids.add(msg["tool_call_id"])

    # CONSERVATIVE CLEANUP: Only remove clearly orphaned calls
    cleaned = []
    for i, msg in enumerate(api_messages):
        if msg["role"] == "assistant" and "tool_calls" in msg:
            is_last_assistant = (i == len(api_messages) - 1) or all(
                m["role"] != "assistant" for m in api_messages[i+1:]
            )

            # Keep the last assistant message even if tool calls are pending
            if is_last_assistant:
                cleaned.append(msg)
            else:
                # Check if this is truly orphaned (not just pending)
                has_all_responses = all(
                    tc["id"] in tool_response_ids
                    for tc in msg["tool_calls"]
                )

                if has_all_responses:
                    # Complete sequence - keep it
                    cleaned.append(msg)
                else:
                    # Only remove if there are later assistant messages
                    # (indicating this sequence was abandoned)
                    has_later_assistant = any(
                        m["role"] == "assistant"
                        for m in api_messages[i+1:]
                    )

                    if has_later_assistant:
                        # Convert to regular assistant message
                        cleaned_msg = {
                            "role": msg["role"],
                            "content": msg["content"] or "[Tool calls removed due to incomplete sequence]"
                        }
                        cleaned.append(cleaned_msg)
                    else:
                        # Keep as-is (might be pending)
                        cleaned.append(msg)
        elif msg["role"] == "tool":
            # Only keep tool responses that have corresponding calls
            if msg["tool_call_id"] in tool_call_ids:
                cleaned.append(msg)
            # Silently drop orphaned tool responses
        else:
            # Keep all other messages (user, system)
            cleaned.append(msg)

    return cleaned


def rebuild_conversation_from_cleaned_messages(cleaned_messages: List[Dict[str, Any]], current_conversation_id: str) -> None:
    """
    Reconstruye el almacenamiento de conversación desde mensajes limpiados.

    Args:
        cleaned_messages: Mensajes limpiados en formato API
        current_conversation_id: ID de la conversación actual
    """
    from nicegui import app

    if not current_conversation_id:
        return

    def get_conversation_storage():
        if 'conversations' not in app.storage.user:
            app.storage.user['conversations'] = {}
        return app.storage.user['conversations']

    conversations = get_conversation_storage()
    if current_conversation_id in conversations:
        # Convert cleaned API messages back to storage format
        storage_messages = []
        for msg in cleaned_messages:
            storage_msg = {
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': str(uuid.uuid1().time)
            }

            if 'tool_calls' in msg:
                storage_msg['tool_calls'] = msg['tool_calls']
            if 'tool_call_id' in msg:
                storage_msg['tool_call_id'] = msg['tool_call_id']

            storage_messages.append(storage_msg)

        conversations[current_conversation_id]['messages'] = storage_messages
        conversations[current_conversation_id]['updated_at'] = str(uuid.uuid1().time)
        app.storage.user['conversations'] = conversations


def find_tool_response(tool_call_id: str, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Encuentra la respuesta de tool para un tool call ID dado.

    Args:
        tool_call_id: ID del tool call
        messages: Lista de mensajes donde buscar

    Returns:
        Objeto de respuesta del tool o None si no se encuentra
    """
    for msg in messages:
        if (msg.get('role') == 'tool' and
            msg.get('tool_call_id') == tool_call_id):
            # Check if this is a respond_to_user or notify_user tool call
            # If so, don't show the tool response since it's already shown as assistant message
            if msg.get('_is_respond_to_user') or msg.get('_is_notify_user'):
                return None
            return msg  # Return the complete tool result object
    return None