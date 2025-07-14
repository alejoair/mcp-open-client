"""
Meta tools para controlar servidores MCP.

Este módulo proporciona meta tools para activar o desactivar servidores MCP
sin necesidad de navegar a la interfaz de configuración de servidores.
"""

from nicegui import ui, app
from mcp_open_client.meta_tools.meta_tool import meta_tool
from mcp_open_client.mcp_client import mcp_client_manager

@meta_tool(
    name="mcp_toggle_server",
    description="Activa o desactiva un servidor MCP específico por su nombre",
    parameters_schema={
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Nombre del servidor MCP a activar/desactivar"
            },
            "enable": {
                "type": "boolean",
                "description": "True para activar el servidor, False para desactivarlo"
            }
        },
        "required": ["server_name", "enable"]
    }
)
async def toggle_mcp_server(server_name: str, enable: bool):
    """
    Activa o desactiva un servidor MCP específico.
    
    Args:
        server_name: Nombre del servidor a activar/desactivar
        enable: True para activar, False para desactivar
    
    Returns:
        Mensaje con el resultado de la operación
    """
    # Obtener la configuración actual
    current_config = app.storage.user.get('mcp-config', {})
    
    # Verificar si hay servidores configurados
    if "mcpServers" not in current_config or not current_config["mcpServers"]:
        return {"error": "No hay servidores MCP configurados"}
    
    # Verificar si el servidor existe
    if server_name not in current_config["mcpServers"]:
        return {"error": f"El servidor '{server_name}' no existe"}
    
    # Cambiar el estado del servidor (disabled = !enable)
    current_config["mcpServers"][server_name]["disabled"] = not enable
    
    # Guardar la configuración actualizada
    app.storage.user['mcp-config'] = current_config
    
    # Actualizar el cliente MCP
    try:
        success = await mcp_client_manager.initialize(current_config)
        
        if success:
            active_servers = mcp_client_manager.get_active_servers()
            status = "activado" if enable else "desactivado"
            
            # Mostrar notificación
            ui.notify(
                f"Servidor '{server_name}' {status}",
                color='positive' if success else 'negative'
            )
            
            # Actualizar el estado en el almacenamiento
            app.storage.user['mcp_status'] = f"Conectado a {len(active_servers)} servidores MCP"
            app.storage.user['mcp_status_color'] = 'positive'
            
            return f"Servidor '{server_name}' {status} correctamente. Conectado a {len(active_servers)} servidores MCP."
        else:
            app.storage.user['mcp_status'] = "No hay servidores MCP activos"
            app.storage.user['mcp_status_color'] = 'warning'
            return {"error": f"No se pudo inicializar el cliente MCP después de {status} el servidor '{server_name}'"}
            
    except Exception as e:
        error_msg = f"Error al actualizar el cliente MCP: {str(e)}"
        app.storage.user['mcp_status'] = error_msg
        app.storage.user['mcp_status_color'] = 'negative'
        return {"error": error_msg}

@meta_tool(
    name="mcp_list_servers",
    description="Lista todos los servidores MCP configurados y su estado",
    parameters_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_mcp_servers():
    """
    Lista todos los servidores MCP configurados y su estado.
    
    Returns:
        Lista de servidores con su estado
    """
    # Obtener la configuración actual
    current_config = app.storage.user.get('mcp-config', {})
    
    # Verificar si hay servidores configurados
    if "mcpServers" not in current_config or not current_config["mcpServers"]:
        return {"message": "No hay servidores MCP configurados"}
    
    # Obtener información de los servidores
    servers_info = []
    for name, config in current_config["mcpServers"].items():
        is_disabled = config.get('disabled', False)
        status = "Desactivado" if is_disabled else "Activo"
        
        # Determinar el tipo de servidor
        if 'url' in config:
            server_type = 'HTTP'
            details = config.get('url', '')
        elif 'command' in config:
            server_type = 'Local'
            details = f"{config.get('command', '')} {' '.join(config.get('args', []))}"
        else:
            server_type = 'Desconocido'
            details = ''
        
        servers_info.append({
            "nombre": name,
            "tipo": server_type,
            "estado": status,
            "detalles": details
        })
    
    # Mostrar también en la UI
    active_count = sum(1 for s in servers_info if s["estado"] == "Activo")
    ui.notify(
        f"Servidores MCP: {len(servers_info)} configurados, {active_count} activos",
        color='info'
    )
    
    return {
        "total_servidores": len(servers_info),
        "servidores_activos": active_count,
        "servidores": servers_info
    }

@meta_tool(
    name="mcp_restart_all_servers",
    description="Reinicia todos los servidores MCP activos",
    parameters_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def restart_all_mcp_servers():
    """
    Reinicia todos los servidores MCP activos.
    
    Returns:
        Mensaje con el resultado de la operación
    """
    # Obtener la configuración actual
    current_config = app.storage.user.get('mcp-config', {})
    
    # Verificar si hay servidores configurados
    if "mcpServers" not in current_config or not current_config["mcpServers"]:
        return {"error": "No hay servidores MCP configurados"}
    
    # Reiniciar el cliente MCP
    try:
        ui.notify("Reiniciando servidores MCP...", color='info')
        
        success = await mcp_client_manager.initialize(current_config)
        
        if success:
            active_servers = mcp_client_manager.get_active_servers()
            
            # Actualizar el estado en el almacenamiento
            app.storage.user['mcp_status'] = f"Conectado a {len(active_servers)} servidores MCP"
            app.storage.user['mcp_status_color'] = 'positive'
            
            ui.notify(
                f"Servidores MCP reiniciados. {len(active_servers)} servidores activos.",
                color='positive'
            )
            
            return f"Servidores MCP reiniciados correctamente. Conectado a {len(active_servers)} servidores MCP."
        else:
            app.storage.user['mcp_status'] = "No hay servidores MCP activos"
            app.storage.user['mcp_status_color'] = 'warning'
            
            ui.notify("No se pudo inicializar ningún servidor MCP", color='warning')
            
            return {"error": "No se pudo inicializar ningún servidor MCP"}
            
    except Exception as e:
        error_msg = f"Error al reiniciar los servidores MCP: {str(e)}"
        app.storage.user['mcp_status'] = error_msg
        app.storage.user['mcp_status_color'] = 'negative'
        
        ui.notify(error_msg, color='negative')
        
        return {"error": error_msg}