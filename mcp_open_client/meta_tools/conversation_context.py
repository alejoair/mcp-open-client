"""
Meta tool para gestionar el contexto de conversación.

Este módulo proporciona herramientas para mantener un contexto persistente
en las conversaciones que siempre se presenta justo antes del mensaje del usuario.
"""

import logging
from typing import Dict, Any, Optional, List
from nicegui import ui, app
from mcp_open_client.meta_tools.meta_tool import meta_tool

logger = logging.getLogger(__name__)

# Clave para almacenar el contexto en el storage de la aplicación
CONTEXT_STORAGE_KEY = 'conversation_context'

def _get_current_context() -> str:
    """Obtiene el contexto actual de la conversación."""
    return app.storage.user.get(CONTEXT_STORAGE_KEY, "")

def _set_context(context: str) -> None:
    """Establece el contexto de la conversación."""
    app.storage.user[CONTEXT_STORAGE_KEY] = context

def _clear_context() -> None:
    """Limpia el contexto de la conversación."""
    app.storage.user[CONTEXT_STORAGE_KEY] = ""

@meta_tool(
    name="conversation_context_add",
    description="Agrega información al contexto de la conversación actual",
    parameters_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Contenido a agregar al contexto de la conversación"
            },
            "replace": {
                "type": "boolean",
                "description": "Si es True, reemplaza el contexto actual en lugar de agregarlo",
                "default": False
            }
        },
        "required": ["content"]
    }
)
def add_to_context(content: str, replace: bool = False) -> Dict[str, Any]:
    """
    Agrega información al contexto de la conversación.
    
    Args:
        content: Texto a agregar al contexto
        replace: Si es True, reemplaza el contexto actual en vez de agregarlo
        
    Returns:
        Diccionario con el resultado de la operación
    """
    try:
        current_context = _get_current_context()
        
        if replace or not current_context:
            new_context = content
        else:
            new_context = f"{current_context}\n\n{content}"
        
        _set_context(new_context)
        
        # Guardar el contexto como un mensaje de sistema en la conversación actual
        context_message = get_context_system_message()
        if context_message:
            from mcp_open_client.ui.chat_handlers import add_message
            add_message('system', context_message['content'])
        
        # Notificar al usuario
        ui.notify(
            "Contexto de conversación actualizado",
            color='positive',
            position='bottom-right'
        )
        
        return {
            "result": "Contexto actualizado correctamente",
            "context_length": len(new_context),
            "operation": "replace" if replace else "append"
        }
    except Exception as e:
        logger.error(f"Error al actualizar el contexto: {str(e)}")
        return {"error": f"Error al actualizar el contexto: {str(e)}"}

@meta_tool(
    name="conversation_context_clear",
    description="Limpia el contexto de la conversación actual",
    parameters_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def clear_context() -> Dict[str, Any]:
    """
    Limpia el contexto de la conversación.
    
    Returns:
        Diccionario con el resultado de la operación
    """
    try:
        _clear_context()
        
        # Notificar al usuario
        ui.notify(
            "Contexto de conversación limpiado",
            color='info',
            position='bottom-right'
        )
        
        return {
            "result": "Contexto limpiado correctamente"
        }
    except Exception as e:
        logger.error(f"Error al limpiar el contexto: {str(e)}")
        return {"error": f"Error al limpiar el contexto: {str(e)}"}


# Función para obtener el mensaje de contexto formateado para el sistema
def get_context_system_message() -> Optional[Dict[str, str]]:
    """
    Obtiene el mensaje de contexto formateado como mensaje del sistema.
    Si no hay contexto, devuelve None.
    
    Returns:
        Dict o None: Mensaje del sistema con el contexto o None si no hay contexto
    """
    context = _get_current_context()
    if not context or context.strip() == "":
        return None
    
    return {
        "role": "system",
        "content": f"CONTEXTO DE LA CONVERSACIÓN:\n\n{context}"
    }

# Función para inyectar el contexto en una lista de mensajes
def inject_context_to_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Inyecta el mensaje de contexto en la lista de mensajes justo antes del último mensaje del usuario.
    Si no hay contexto o no hay mensajes de usuario, no hace nada.
    
    Args:
        messages: Lista de mensajes de la conversación
        
    Returns:
        List: Lista de mensajes con el contexto inyectado
    """
    context_message = get_context_system_message()
    if not context_message or not messages:
        return messages
    
    # Crear una copia de los mensajes para no modificar el original
    new_messages = messages.copy()
    
    # Buscar el último mensaje del usuario para insertar el contexto justo antes
    user_indices = [i for i, msg in enumerate(new_messages) if msg.get('role') == 'user']
    
    if user_indices:
        # Insertar el contexto antes del último mensaje del usuario
        last_user_index = user_indices[-1]
        new_messages.insert(last_user_index, context_message)
    
    return new_messages

# Registrar un hook para inyectar el contexto en las conversaciones
def register_conversation_hook():
    """
    Registra un hook para inyectar el contexto en las conversaciones.
    Este hook debe ser llamado durante la inicialización de la aplicación.
    
    Este hook ya está integrado en el sistema a través de la modificación de chat_handlers.py,
    que ahora usa inject_context_to_messages() antes de enviar mensajes al LLM.
    """
    # La integración ya está hecha en chat_handlers.py
    print("Contexto de conversación registrado correctamente.")
    
    # Notificar al usuario
    ui.notify(
        "Sistema de contexto de conversación activado",
        color='positive',
        position='bottom-right',
        timeout=3000
    )
    
    return {"success": True, "message": "Contexto de conversación registrado correctamente."}