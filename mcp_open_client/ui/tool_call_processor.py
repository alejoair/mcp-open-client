"""
Módulo para el procesamiento específico de tool calls y meta tools.
Extraído de chat_handlers.py para mejorar modularidad.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple


async def process_meta_tools(tool_calls: List[Dict[str, Any]], handle_tool_call_func) -> Tuple[Optional[Dict], List[Dict], List[Dict]]:
    """
    Procesa todas las meta tools automáticamente.

    Args:
        tool_calls: Lista de tool calls a procesar
        handle_tool_call_func: Función para manejar tool calls

    Returns:
        Tupla con (respond_to_user_call, notify_user_calls, remaining_tool_calls)
    """
    respond_to_user_call = None
    notify_user_calls = []
    remaining_tool_calls = []
    other_meta_tools = []

    for tool_call in tool_calls:
        tool_name = tool_call.get('function', {}).get('name')

        if tool_name == 'meta-respond_to_user':
            respond_to_user_call = tool_call
            break  # Solo puede haber uno de estos y termina la ejecución
        elif tool_name == 'meta-notify_user':
            notify_user_calls.append(tool_call)  # Puede haber múltiples
        elif tool_name and tool_name.startswith('meta-'):
            # Cualquier otra meta tool se procesa automáticamente
            other_meta_tools.append(tool_call)
        else:
            remaining_tool_calls.append(tool_call)

    # Procesar otras meta tools automáticamente
    for meta_tool_call in other_meta_tools:
        try:
            await handle_tool_call_func(meta_tool_call)
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing meta tool {meta_tool_call.get('function', {}).get('name')}: {e}")

    return respond_to_user_call, notify_user_calls, remaining_tool_calls


async def process_respond_to_user(respond_to_user_call: Dict[str, Any], handle_tool_call_func, add_message_func) -> bool:
    """
    Procesa una llamada respond_to_user.

    Args:
        respond_to_user_call: El tool call de respond_to_user
        handle_tool_call_func: Función para manejar tool calls
        add_message_func: Función para agregar mensajes

    Returns:
        True si se procesó exitosamente, False en caso de error
    """
    try:
        tool_result = await handle_tool_call_func(respond_to_user_call)
        # Agregar directamente como mensaje del asistente (sin tool call en historial)
        add_message_func('assistant', tool_result['content'])
        return True
    except Exception as e:
        print(f"Error processing respond_to_user: {e}")
        # Fallback: agregar mensaje de error
        add_message_func('assistant', f"Error generating response: {str(e)}")
        return False


async def process_notify_user_calls(notify_user_calls: List[Dict[str, Any]], handle_tool_call_func, add_message_func) -> List[Dict[str, Any]]:
    """
    Procesa múltiples llamadas notify_user.

    Args:
        notify_user_calls: Lista de tool calls de notify_user
        handle_tool_call_func: Función para manejar tool calls
        add_message_func: Función para agregar mensajes

    Returns:
        Lista de tool calls restantes después del procesamiento
    """
    try:
        # Procesar cada notify_user secuencialmente
        for notify_call in notify_user_calls:
            tool_result = await handle_tool_call_func(notify_call)

            # Agregar mensaje del asistente con formato visual para el usuario
            notification_content = tool_result.get('_notification_content', tool_result['content'])
            add_message_func('assistant', notification_content)

            # Agregar confirmación del sistema para que el LLM sepa que la notificación fue exitosa
            add_message_func('system', 'Has notificado exitosamente al usuario. No necesitas volver a notificar lo mismo. Puedes usar respond_to_user para finalizar o continuar con otras tareas.')

        return []  # Se han procesado todas las notificaciones
    except Exception as e:
        print(f"Error processing notify_user: {e}")
        # En caso de error, continuar con otros tool calls
        return []


async def process_tool_calls_parallel(tool_calls: List[Dict[str, Any]], handle_tool_call_func) -> List[Dict[str, Any]]:
    """
    Procesa tool calls en paralelo para mejor rendimiento.

    Args:
        tool_calls: Lista de tool calls a procesar
        handle_tool_call_func: Función para manejar tool calls

    Returns:
        Lista de resultados de tool calls
    """
    async def process_single_tool_call(tool_call):
        try:
            return await handle_tool_call_func(tool_call)
        except Exception as e:
            # Return error result in consistent format
            return {
                'tool_call_id': tool_call['id'],
                'content': f"Error executing tool '{tool_call.get('function', {}).get('name', 'unknown')}': {str(e)}",
                '_is_error': True
            }

    # Execute all tool calls in parallel
    tool_results = await asyncio.gather(*[process_single_tool_call(tc) for tc in tool_calls])
    return tool_results


def filter_meta_tools_for_ui(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtra meta tools para la visualización en UI.

    Args:
        tool_calls: Lista de tool calls originales

    Returns:
        Lista de tool calls filtrada para UI (sin meta tools)
    """
    filtered_tool_calls = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('function', {}).get('name', '')
        if not tool_name.startswith('meta-'):
            filtered_tool_calls.append(tool_call)
    return filtered_tool_calls


def validate_tool_call_sequence(messages: List[Dict[str, Any]], force_cleanup: bool = False) -> List[Dict[str, Any]]:
    """
    Valida y limpia secuencias de tool calls.

    Args:
        messages: Lista de mensajes a validar
        force_cleanup: Si True, fuerza la limpieza de tool calls huérfanos

    Returns:
        Lista de mensajes validada y limpiada
    """
    # Para ahora, retorna los mensajes tal como están
    # Esta función se puede expandir con lógica de validación más compleja
    return messages