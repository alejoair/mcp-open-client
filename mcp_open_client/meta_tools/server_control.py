"""
Meta tools para gestionar tools MCP y Meta.

Este módulo proporciona meta tools para listar y controlar el estado
de activación de tools MCP y Meta Tools individuales.
"""

from nicegui import ui, app
from mcp_open_client.meta_tools.meta_tool import meta_tool
from mcp_open_client.mcp_client import mcp_client_manager


@meta_tool(
    name="mcp_list_tools",
    description="Lista todas las tools MCP disponibles y su estado de activación",
    parameters_schema={
        "type": "object",
        "properties": {
            "show_only_enabled": {
                "type": "boolean",
                "description": "Si es true, solo muestra tools habilitadas",
                "default": False
            }
        },
        "required": []
    }
)
async def list_mcp_tools(show_only_enabled: bool = False):
    """
    Lista todas las tools MCP disponibles y su estado.
    
    Args:
        show_only_enabled: Si es true, solo muestra tools habilitadas
    
    Returns:
        Lista de tools con su estado de activación
    """
    from mcp_open_client.config_utils import is_tool_enabled
    
    # Verificar si hay servidores MCP conectados
    if not mcp_client_manager.is_connected():
        return {"error": "No hay servidores MCP conectados"}
    
    try:
        # Obtener todas las tools MCP disponibles
        mcp_tools = await mcp_client_manager.list_tools()
        active_servers = mcp_client_manager.get_active_servers()
        
        if not mcp_tools:
            return {"message": "No hay tools MCP disponibles"}
        
        tools_info = []
        enabled_count = 0
        
        for tool in mcp_tools:
            # Handle both dict and object formats (same as get_available_tools)
            if hasattr(tool, 'name'):
                # FastMCP Tool object
                full_tool_name = tool.name
                tool_desc = tool.description
            else:
                # Dict format
                full_tool_name = tool.get('name', '')
                tool_desc = tool.get('description', '')
            
            # MISMA LÓGICA QUE get_available_tools(): Extraer servidor y nombre real de la tool
            # Formato: "servidor_nombre_tool" -> servidor="servidor", tool="nombre_tool"
            if '_' in full_tool_name:
                # Buscar el primer _ para separar servidor del resto
                parts = full_tool_name.split('_', 1)
                server_name = parts[0]
                actual_tool_name = parts[1]
            else:
                # Si no tiene _, asumir que no tiene prefijo de servidor
                server_name = 'unknown'
                actual_tool_name = full_tool_name
            
            # Construir tool_id usando el mismo formato que get_available_tools
            tool_id = f"{server_name}:{actual_tool_name}"
            is_enabled = is_tool_enabled(tool_id, 'mcp')
            
            if show_only_enabled and not is_enabled:
                continue
                
            if is_enabled:
                enabled_count += 1
            
            tools_info.append({
                "tool_id": tool_id,
                "servidor": server_name,
                "nombre": actual_tool_name,
                "nombre_completo": full_tool_name,  # Para debugging
                "descripcion": tool_desc[:100] + "..." if len(tool_desc) > 100 else tool_desc,
                "habilitada": is_enabled
            })
        
        # Mostrar resumen en la UI
        ui.notify(
            f"Tools MCP: {len(tools_info)} encontradas, {enabled_count} habilitadas",
            color='info'
        )
        
        return {
            "total_tools": len(tools_info),
            "tools_habilitadas": enabled_count,
            "tools": tools_info
        }
        
    except Exception as e:
        return {"error": f"Error al obtener tools: {str(e)}"}

@meta_tool(
    name="mcp_toggle_tool",
    description="Activa o desactiva una tool específica (MCP o Meta) por su ID",
    parameters_schema={
        "type": "object",
        "properties": {
            "tool_id": {
                "type": "string",
                "description": "ID de la tool a activar/desactivar. Para MCP tools usa formato 'servidor:nombre', para Meta tools solo el nombre"
            },
            "enabled": {
                "type": "boolean",
                "description": "True para activar la tool, False para desactivarla"
            },
            "tool_type": {
                "type": "string",
                "enum": ["mcp", "meta"],
                "description": "Tipo de tool: 'mcp' para tools MCP, 'meta' para Meta Tools"
            }
        },
        "required": ["tool_id", "enabled", "tool_type"]
    }
)
def toggle_tool(tool_id: str, enabled: bool, tool_type: str):
    """
    Activa o desactiva una tool específica por su ID.
    
    Args:
        tool_id: ID de la tool (formato 'servidor:nombre' para MCP, nombre para Meta)
        enabled: True para activar, False para desactivar
        tool_type: Tipo de tool ('mcp' o 'meta')
    
    Returns:
        Mensaje con el resultado de la operación
    """
    from mcp_open_client.config_utils import set_tool_enabled
    
    # Validar tipo de tool
    if tool_type not in ['mcp', 'meta']:
        return {"error": f"Tipo de tool inválido: {tool_type}. Debe ser 'mcp' o 'meta'"}
    
    try:
        # Realizar el toggle
        set_tool_enabled(tool_id, enabled, tool_type)
        
        # Mostrar notificación
        action = "habilitada" if enabled else "deshabilitada"
        ui.notify(
            f"{tool_type.upper()} tool '{tool_id}' {action}",
            color='positive'
        )
        
        return {
            "result": f"{tool_type.upper()} tool '{tool_id}' {action} correctamente",
            "tool_id": tool_id,
            "enabled": enabled,
            "tool_type": tool_type
        }
    except Exception as e:
        error_msg = f"Error al cambiar estado de la tool '{tool_id}': {str(e)}"
        ui.notify(error_msg, color='negative')
        return {"error": error_msg}
