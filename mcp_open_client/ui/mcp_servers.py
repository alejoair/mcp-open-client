from nicegui import ui, app
import asyncio
from mcp_open_client.config_utils import load_initial_config_from_files
from mcp_open_client.mcp_client import mcp_client_manager

# File operations removed - using only app.storage.user which is persistent
# Configuration is automatically saved by NiceGUI's storage system

def show_content(container):
    """Main function to display the MCP servers management UI"""
    container.clear()
    container.classes('q-pa-md')
    
    with container:
        ui.label('MCP Servers').classes('text-2xl font-bold mb-6')
        
        # Get the current MCP configuration from user storage
        mcp_config = app.storage.user.get('mcp-config', {})
        
        # If no configuration exists in user storage, initialize with default
        if not mcp_config:
            mcp_config = {"mcpServers": {}}
            app.storage.user['mcp-config'] = mcp_config
        
        servers = mcp_config.get("mcpServers", {})
        
        # Actions card
        with ui.card().classes('w-full mb-6'):
            ui.label('Gestión de Servidores').classes('text-lg font-semibold mb-3')
            ui.label('Conecta herramientas externas a través del protocolo MCP para expandir las capacidades de tu IA.').classes('text-sm text-gray-600 mb-4')
            
            with ui.row().classes('w-full gap-4'):
                ui.button('Agregar Servidor', icon='add', on_click=lambda: show_add_dialog()).props('color=primary')
                ui.button('Restaurar por Defecto', icon='refresh', on_click=lambda: reset_to_default()).props('color=warning')
        
        # Status overview card
        with ui.card().classes('w-full mb-6'):
            ui.label('Estado Actual').classes('text-lg font-semibold mb-3')
            
            if servers:
                active_count = sum(1 for config in servers.values() if not config.get('disabled', False))
                total_count = len(servers)
                ui.label(f'Servidores configurados: {total_count}').classes('text-sm text-gray-600')
                ui.label(f'Servidores activos: {active_count}').classes('text-sm text-gray-600')
                
                if active_count > 0:
                    ui.linear_progress(active_count / total_count).classes('w-full mt-2')
                    ui.label(f'{(active_count/total_count)*100:.0f}% de servidores activos').classes('text-sm text-gray-600')
            else:
                ui.label('No hay servidores configurados').classes('text-sm text-gray-600')
        
        # Create a container for the servers list that can be refreshed
        servers_container = ui.column().classes('w-full')
        
        def refresh_servers_list():
            """Refresh the servers list UI"""
            servers_container.clear()
            
            # Get the latest config
            current_config = app.storage.user.get('mcp-config', {})
            current_servers = current_config.get("mcpServers", {})
            
            if not current_servers:
                with servers_container:
                    with ui.card().classes('w-full mb-6'):
                        ui.label('No hay servidores configurados').classes('text-lg font-semibold text-center p-8')
                        ui.label('Haz clic en "Agregar Servidor" para comenzar').classes('text-sm text-gray-600 text-center')
                return
            
            with servers_container:
                ui.label('Servidores Configurados').classes('text-lg font-semibold mb-4')
                
                for name, config in current_servers.items():
                    # Determine server type and details
                    if 'url' in config:
                        server_type = 'HTTP'
                        details = config.get('url', '')
                        icon = 'cloud'
                        color = 'info'
                    elif 'command' in config:
                        server_type = 'Local'
                        details = f"{config.get('command', '')} {' '.join(config.get('args', []))}"
                        icon = 'computer'
                        color = 'secondary'
                    else:
                        server_type = 'Desconocido'
                        details = ''
                        icon = 'help'
                        color = 'warning'
                    
                    # Determine status
                    is_disabled = config.get('disabled', False)
                    status = 'Deshabilitado' if is_disabled else 'Activo'
                    
                    # Server card
                    with ui.card().classes('w-full mb-4'):
                        with ui.row().classes('w-full items-center justify-between mb-3'):
                            with ui.row().classes('items-center'):
                                ui.icon(icon).classes(f'mr-2 text-{color}')
                                ui.label(name).classes('text-lg font-semibold')
                                ui.badge(status).classes(f"{'bg-green text-white' if not is_disabled else 'bg-gray text-white'} ml-2")
                            
                            with ui.row().classes('gap-2'):
                                ui.switch(
                                    value=not is_disabled,
                                    on_change=lambda e, name=name: toggle_server_status(name, not e.value)
                                ).props('color=primary').tooltip('Habilitar/Deshabilitar')
                                
                                ui.button('', icon='edit', on_click=lambda name=name, config=config: show_edit_dialog(name, config)).props('flat round color=primary size=sm').tooltip('Editar')
                                ui.button('', icon='delete', on_click=lambda name=name: show_delete_dialog(name)).props('flat round color=negative size=sm').tooltip('Eliminar')
                        
                        ui.label(f'Tipo: {server_type}').classes('text-sm text-gray-600 mb-2')
                        
                        with ui.expansion('Detalles de Configuración', icon='info').classes('w-full'):
                            ui.label(details).classes('text-sm font-mono bg-gray-100 p-2 rounded')
        
        # Function to toggle server status
        def toggle_server_status(server_name, is_active):
            """Toggle a server's active status"""
            current_config = app.storage.user.get('mcp-config', {})
            if "mcpServers" in current_config and server_name in current_config["mcpServers"]:
                # Toggle the disabled flag (note: in the config, 'disabled' means not active)
                current_config["mcpServers"][server_name]["disabled"] = is_active
                
                app.storage.user['mcp-config'] = current_config
                
                status_text = "disabled" if is_active else "enabled"
                ui.notify(f"Server '{server_name}' {status_text}", color='positive')
                
                # Update the MCP client manager with the new configuration
                async def update_mcp_client():
                    try:
                        success = await mcp_client_manager.initialize(current_config)
                        if success:
                            active_servers = mcp_client_manager.get_active_servers()
                            # Use storage for safe notification from background tasks
                            app.storage.user['mcp_status'] = f"Connected to {len(active_servers)} MCP servers"
                            app.storage.user['mcp_status_color'] = 'positive'
                        else:
                            app.storage.user['mcp_status'] = "No active MCP servers"
                            app.storage.user['mcp_status_color'] = 'warning'
                    except Exception as e:
                        app.storage.user['mcp_status'] = f"Error connecting to MCP servers: {str(e)}"
                        app.storage.user['mcp_status_color'] = 'negative'
                    
                    # Only refresh the UI after the client has been initialized
                    # This prevents potential race conditions
                    refresh_servers_list()
                
                # Run the update asynchronously
                asyncio.create_task(update_mcp_client())
        
        # Function to delete a server
        def delete_server(server_name):
            """Delete a server from the configuration"""
            current_config = app.storage.user.get('mcp-config', {})
            if "mcpServers" in current_config and server_name in current_config["mcpServers"]:
                del current_config["mcpServers"][server_name]
                app.storage.user['mcp-config'] = current_config
                
                # Save configuration to file
                # Configuration automatically saved in user storage
                
                ui.notify(f"Server '{server_name}' deleted", color='positive')
                
                # Update the MCP client manager with the new configuration
                async def update_mcp_client():
                    try:
                        success = await mcp_client_manager.initialize(current_config)
                        if success:
                            active_servers = mcp_client_manager.get_active_servers()
                            # Use storage for safe notification from background tasks
                            app.storage.user['mcp_status'] = f"Connected to {len(active_servers)} MCP servers"
                            app.storage.user['mcp_status_color'] = 'positive'
                        else:
                            app.storage.user['mcp_status'] = "No active MCP servers"
                            app.storage.user['mcp_status_color'] = 'warning'
                    except Exception as e:
                        app.storage.user['mcp_status'] = f"Error connecting to MCP servers: {str(e)}"
                        app.storage.user['mcp_status_color'] = 'negative'
                    
                    # Only refresh the UI after the client has been initialized
                    # This prevents potential race conditions
                    refresh_servers_list()
                
                # Run the update asynchronously
                asyncio.create_task(update_mcp_client())
        
        # Dialog to confirm server deletion
        def show_delete_dialog(server_name):
            """Show confirmation dialog to delete a server"""
            with ui.dialog() as dialog, ui.card().classes('p-4'):
                ui.label(f'Delete Server: {server_name}').classes('text-h6')
                ui.label('Are you sure you want to delete this server? This action cannot be undone.')
                
                with ui.row().classes('w-full justify-end'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    ui.button('Delete', on_click=lambda: [delete_server(server_name), dialog.close()]).props('color=negative')
            
            # Open the dialog
            dialog.open()
        
        # Dialog to edit a server
        def show_edit_dialog(server_name, server_config):
            """Show dialog to edit a server"""
            with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
                ui.label(f'Edit Server: {server_name}').classes('text-h6')
                
                # Determine server type
                is_http = 'url' in server_config
                
                # Server type selection (disabled for editing)
                server_type = 'HTTP' if is_http else 'Local'
                ui.label(f'Server Type: {server_type}').classes('text-bold')
                
                # HTTP server fields
                if is_http:
                    url = ui.input('Server URL', value=server_config.get('url', '')).classes('w-full')
                    transport_options = ['streamable-http', 'http']
                    transport = ui.select(
                        transport_options,
                        value=server_config.get('transport', 'streamable-http'),
                        label='Transport'
                    ).classes('w-full')
                
                # Local command fields
                else:
                    command = ui.input('Command', value=server_config.get('command', '')).classes('w-full')
                    args = ui.input(
                        'Arguments (space-separated)',
                        value=' '.join(server_config.get('args', []))
                    ).classes('w-full')
                    
                    env_text = ''
                    if 'env' in server_config and server_config['env']:
                        env_text = '\n'.join([f"{k}={v}" for k, v in server_config['env'].items()])
                    
                    env_vars = ui.input(
                        'Environment Variables (key=value, one per line)',
                        value=env_text
                    ).classes('w-full').props('type=textarea rows=3')
                
                # Buttons
                with ui.row().classes('w-full justify-end'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    
                    def update_server():
                        current_config = app.storage.user.get('mcp-config', {})
                        if "mcpServers" not in current_config or server_name not in current_config["mcpServers"]:
                            ui.notify(f"Server '{server_name}' not found", color='negative')
                            return
                        
                        # Preserve the disabled status
                        is_disabled = current_config["mcpServers"][server_name].get('disabled', False)
                        
                        # Create updated config
                        updated_config = {"disabled": is_disabled}
                        
                        if is_http:
                            if not url.value:
                                ui.notify('URL is required', color='negative')
                                return
                            updated_config["url"] = url.value
                            updated_config["transport"] = transport.value
                        else:
                            if not command.value:
                                ui.notify('Command is required', color='negative')
                                return
                            updated_config["command"] = command.value
                            
                            if args.value:
                                updated_config["args"] = args.value.split()
                            
                            if env_vars.value:
                                env_dict = {}
                                for line in env_vars.value.splitlines():
                                    if '=' in line:
                                        key, value = line.split('=', 1)
                                        env_dict[key.strip()] = value.strip()
                                if env_dict:
                                    updated_config["env"] = env_dict
                        
                        # Update the configuration
                        current_config["mcpServers"][server_name] = updated_config
                        app.storage.user['mcp-config'] = current_config
                        
                        # Configuration automatically saved in user storage
                        
                        # Update the MCP client manager with the new configuration
                        async def update_mcp_client():
                            try:
                                success = await mcp_client_manager.initialize(current_config)
                                if success:
                                    active_servers = mcp_client_manager.get_active_servers()
                                    # Use storage for safe notification from background tasks
                                    app.storage.user['mcp_status'] = f"Connected to {len(active_servers)} MCP servers"
                                    app.storage.user['mcp_status_color'] = 'positive'
                                else:
                                    app.storage.user['mcp_status'] = "No active MCP servers"
                                    app.storage.user['mcp_status_color'] = 'warning'
                            except Exception as e:
                                app.storage.user['mcp_status'] = f"Error connecting to MCP servers: {str(e)}"
                                app.storage.user['mcp_status_color'] = 'negative'
                            
                            # Only refresh the UI after the client has been initialized
                            # This prevents potential race conditions
                            refresh_servers_list()
                        
                        # Run the update asynchronously
                        asyncio.create_task(update_mcp_client())
                        
                        ui.notify(f"Server '{server_name}' updated", color='positive')
                        dialog.close()
                    
                    ui.button('Update', on_click=update_server).props('color=primary')
            
            # Open the dialog
            dialog.open()
        
        # Dialog to add a new server
        def show_add_dialog():
            """Show dialog to add a new server"""
            with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
                ui.label('Add New MCP Server').classes('text-h6')
                
                server_name = ui.input('Server Name').classes('w-full')
                
                # Server type selection
                server_type = ui.radio(['HTTP', 'Local'], value='Local').props('inline')
                
                # HTTP server fields
                http_container = ui.column().classes('w-full')
                with http_container:
                    url = ui.input('Server URL').classes('w-full')
                    transport = ui.select(
                        ['streamable-http', 'http'],
                        value='streamable-http',
                        label='Transport'
                    ).classes('w-full')
                
                # Local command fields
                cmd_container = ui.column().classes('w-full')
                with cmd_container:
                    command = ui.input('Command').classes('w-full')
                    args = ui.input('Arguments (space-separated)').classes('w-full')
                    env_vars = ui.input('Environment Variables (key=value, one per line)').classes('w-full')
                    env_vars.props('type=textarea rows=3')
                
                # Toggle visibility based on server type
                def toggle_server_type():
                    if server_type.value == 'HTTP':
                        http_container.classes(remove='hidden')
                        cmd_container.classes(add='hidden')
                    else:
                        http_container.classes(add='hidden')
                        cmd_container.classes(remove='hidden')
                
                server_type.on('change', toggle_server_type)
                
                # Initial setup
                toggle_server_type()
                
                # Buttons
                with ui.row().classes('w-full justify-end'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    
                    def add_server():
                        name = server_name.value.strip()
                        if not name:
                            ui.notify('Server name is required', color='negative')
                            return
                        
                        current_config = app.storage.user.get('mcp-config', {})
                        if "mcpServers" not in current_config:
                            current_config["mcpServers"] = {}
                        
                        if name in current_config["mcpServers"]:
                            ui.notify(f"Server '{name}' already exists", color='negative')
                            return
                        
                        # Create new server config
                        new_config = {"disabled": False}
                        
                        if server_type.value == 'HTTP':
                            if not url.value:
                                ui.notify('URL is required', color='negative')
                                return
                            new_config["url"] = url.value
                            new_config["transport"] = transport.value
                        else:
                            if not command.value:
                                ui.notify('Command is required', color='negative')
                                return
                            new_config["command"] = command.value
                            
                            if args.value:
                                new_config["args"] = args.value.split()
                            
                            if env_vars.value:
                                env_dict = {}
                                for line in env_vars.value.splitlines():
                                    if '=' in line:
                                        key, value = line.split('=', 1)
                                        env_dict[key.strip()] = value.strip()
                                if env_dict:
                                    new_config["env"] = env_dict
                        
                        # Add the new server to the configuration
                        current_config["mcpServers"][name] = new_config
                        app.storage.user['mcp-config'] = current_config
                        
                        # Configuration automatically saved in user storage
                        
                        # Update the MCP client manager with the new configuration
                        async def update_mcp_client():
                            try:
                                success = await mcp_client_manager.initialize(current_config)
                                if success:
                                    active_servers = mcp_client_manager.get_active_servers()
                                    # Use storage for safe notification from background tasks
                                    app.storage.user['mcp_status'] = f"Connected to {len(active_servers)} MCP servers"
                                    app.storage.user['mcp_status_color'] = 'positive'
                                else:
                                    app.storage.user['mcp_status'] = "No active MCP servers"
                                    app.storage.user['mcp_status_color'] = 'warning'
                            except Exception as e:
                                app.storage.user['mcp_status'] = f"Error connecting to MCP servers: {str(e)}"
                                app.storage.user['mcp_status_color'] = 'negative'
                            
                            # Only refresh the UI after the client has been initialized
                            # This prevents potential race conditions
                            refresh_servers_list()
                        
                        # Run the update asynchronously
                        asyncio.create_task(update_mcp_client())
                        
                        ui.notify(f"Server '{name}' added", color='positive')
                        dialog.close()
                    
                    ui.button('Add', on_click=add_server).props('color=primary')
            
            # Open the dialog
            dialog.open()
        
        # Function to reset configuration to default
        def reset_to_default():
            """Reset the MCP configuration to default values from files"""
            try:
                # Load initial configuration from files
                initial_configs = load_initial_config_from_files()
                default_config = initial_configs.get('mcp-config', {"mcpServers": {}})
                
                print(f"Reset to default - MCP config loaded from files: {default_config}")
                
                # Update the user storage with default configuration from files
                app.storage.user['mcp-config'] = default_config
                
                # Update the MCP client manager with the default configuration
                async def update_mcp_client():
                    try:
                        success = await mcp_client_manager.initialize(default_config)
                        if success:
                            active_servers = mcp_client_manager.get_active_servers()
                            # Use storage for safe notification from background tasks
                            app.storage.user['mcp_status'] = f"Connected to {len(active_servers)} MCP servers"
                            app.storage.user['mcp_status_color'] = 'positive'
                        else:
                            app.storage.user['mcp_status'] = "No active MCP servers"
                            app.storage.user['mcp_status_color'] = 'warning'
                    except Exception as e:
                        app.storage.user['mcp_status'] = f"Error connecting to MCP servers: {str(e)}"
                        app.storage.user['mcp_status_color'] = 'negative'
                    
                    # Refresh the UI after the client has been initialized
                    refresh_servers_list()
                
                # Run the update asynchronously
                asyncio.create_task(update_mcp_client())
                
                ui.notify('Configuration reset to default values', color='positive')
            except Exception as e:
                ui.notify(f'Error resetting configuration: {str(e)}', color='negative')
        
        # Initial load of the servers list
        refresh_servers_list()