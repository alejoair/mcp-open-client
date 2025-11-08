"""
Meta tool para notificaciones al usuario sin terminar el flujo.
Permite al LLM enviar mensajes informativos al usuario manteniendo el control.
"""

from typing import Dict, Any, Optional
from mcp_open_client.meta_tools.meta_tool import meta_tool
from nicegui import ui

# Tipos de notificación específicos para notify_user
# Enfocados en informar sin terminar el flujo
NOTIFICATION_TYPES = {
    "info": {
        "icon": "ℹ️",
        "description": "Información general",
        "background_color": "#e8f5e8",  # Verde suave
        "border_color": "#4caf50",
        "text_color": "#2e7d32",
        "icon_bg": "#c8e6c9"
    },
    "status": {
        "icon": "📊",
        "description": "Estado actual del sistema o proceso",
        "background_color": "#e3f2fd",  # Azul suave
        "border_color": "#2196f3",
        "text_color": "#1565c0",
        "icon_bg": "#bbdefb"
    },
    "update": {
        "icon": "🔔",
        "description": "Actualización o cambio de estado",
        "background_color": "#fff8e1",  # Amarillo suave
        "border_color": "#ffc107",
        "text_color": "#f57f17",
        "icon_bg": "#fff3c4"
    },
    "alert": {
        "icon": "⚠️",
        "description": "Alerta o advertencia no crítica",
        "background_color": "#fff3e0",  # Naranja suave
        "border_color": "#ff9800",
        "text_color": "#e65100",
        "icon_bg": "#ffcc80"
    },
    "debug": {
        "icon": "🐛",
        "description": "Información de depuración",
        "background_color": "#f3e5f5",  # Púrpura suave
        "border_color": "#9c27b0",
        "text_color": "#6a1b9a",
        "icon_bg": "#e1bee7"
    },
    "working": {
        "icon": "⚙️",
        "description": "Proceso en ejecución",
        "background_color": "#f5f5f5",  # Gris neutro
        "border_color": "#9e9e9e",
        "text_color": "#424242",
        "icon_bg": "#e0e0e0"
    }
}

@meta_tool(
    name="notify_user",
    description="""
    📢 HERRAMIENTA DE NOTIFICACIÓN - Envía mensajes informativos sin terminar el flujo.
    
    ✅ CARACTERÍSTICA CLAVE: Esta herramienta NO termina la conversación.
    🔄 Puedes continuar ejecutando más herramientas después de usar notify_user.
    
    Tipos de notificación disponibles:
    - status: Estado actual del sistema o proceso 📊
    - update: Actualización o cambio de estado 🔔
    - alert: Alerta o advertencia no crítica ⚠️
    - debug: Información de depuración 🐛
    - working: Proceso en ejecución ⚙️
    
    📝 CUÁNDO USAR:
    - Para informar progreso de tareas largas
    - Para confirmar acciones intermedias
    - Para mostrar estado de procesos en curso
    - Para dar actualizaciones sin terminar el flujo
    
    ✨ VENTAJA: Mantiene la transparencia con el usuario mientras continúas trabajando.
    """,
    parameters_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Contenido del mensaje a mostrar al usuario"
            },
            "response_type": {
                "type": "string",
                "description": "Tipo de notificación que determina el estilo visual",
                "enum": list(NOTIFICATION_TYPES.keys()),
                "default": "info"
            },
            "title": {
                "type": "string",
                "description": "Título opcional para la notificación"
            }
        },
        "required": ["content"]
    }
)
async def notify_user(content: str, response_type: str = "info", title: Optional[str] = None) -> str:
    """
    Envía una notificación al usuario sin terminar el flujo.
    
    Args:
        content: Contenido principal de la notificación
        response_type: Tipo de notificación para determinar el estilo visual
        title: Título opcional para la notificación
        
    Returns:
        Confirmación de que el mensaje fue enviado al usuario
    """
    # Validar tipo de respuesta
    if response_type not in NOTIFICATION_TYPES:
        response_type = "info"
    
    # Obtener configuración del tipo
    type_config = NOTIFICATION_TYPES[response_type]
    icon = type_config["icon"]
    
    # Construir respuesta formateada
    formatted_response = content
    
    if title:
        formatted_response = f"**{title}**\n\n{content}"
    
    # Agregar metadatos como comentario para que la UI pueda aplicar estilos
    response_metadata = {
        "response_type": response_type,
        "icon": icon,
        "background_color": type_config["background_color"],
        "border_color": type_config["border_color"],
        "text_color": type_config["text_color"],
        "icon_bg": type_config["icon_bg"],
        "is_notification": True,  # Marca que esta es una notificación (no terminal)
        "is_terminal": False      # NO termina el flujo
    }
    
    # Agregar metadatos embebidos que serán procesados por message_parser.py
    formatted_response += f"\n\n<!-- RESPONSE_METADATA: {response_metadata} -->"
    
    # Esta respuesta será enviada al usuario como mensaje del asistente
    # El contenido formateado será procesado por chat_handlers.py
    # usando el mismo mecanismo que respond_to_user pero sin terminar el flujo
    
    # Retornar el contenido formateado que será mostrado al usuario
    # handle_tool_call.py se encargará de separar la confirmación para el LLM
    return formatted_response


def get_notification_types() -> Dict[str, Dict[str, Any]]:
    """
    Obtiene la lista de tipos de notificación disponibles.
    Reutiliza los mismos tipos que respond_to_user para consistencia visual.
    
    Returns:
        Diccionario con los tipos de notificación y sus configuraciones
    """
    return NOTIFICATION_TYPES.copy()


def is_notification_message(content: str) -> bool:
    """
    Verifica si un mensaje contiene metadatos de notificación.
    
    Args:
        content: Contenido del mensaje a verificar
        
    Returns:
        True si el mensaje es una notificación, False en caso contrario
    """
    import re
    pattern = r'<!-- RESPONSE_METADATA: (.+?) -->'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        try:
            import json
            metadata = json.loads(match.group(1).replace("'", '"'))
            return metadata.get("is_notification", False)
        except (json.JSONDecodeError, AttributeError):
            pass
    
    return False


def extract_notification_metadata(content: str) -> Optional[Dict[str, Any]]:
    """
    Extrae los metadatos de notificación de un mensaje.
    
    Args:
        content: Contenido del mensaje
        
    Returns:
        Diccionario con los metadatos o None si no los hay
    """
    import re
    pattern = r'<!-- RESPONSE_METADATA: (.+?) -->'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        try:
            import json
            metadata = json.loads(match.group(1).replace("'", '"'))
            if metadata.get("is_notification", False):
                return metadata
        except (json.JSONDecodeError, AttributeError):
            pass
    
    return None


def clean_notification_content(content: str) -> str:
    """
    Limpia el contenido removiendo los metadatos embebidos.
    
    Args:
        content: Contenido con metadatos embebidos
        
    Returns:
        Contenido limpio sin metadatos
    """
    import re
    # Remover el comentario con metadatos
    pattern = r'\n\n<!-- RESPONSE_METADATA: .+? -->'
    cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
    return cleaned.strip()