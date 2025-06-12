from nicegui import ui, app
import asyncio
import json
import sys

# Import UI components
from ui.mcp_servers import show_content as show_mcp_servers_content
from ui.configure import show_content as show_configure_content
from ui.conversations import show_content as show_conversations_content
from ui.chat_window import show_content as show_chat_content

# Import MCP client manager
from mcp_client import mcp_client_manager

# Load the external CSS file from settings directory with cache busting
ui.add_css(f'settings/app-styles.css?v={__import__("time").time()}')

@ui.page('/')
def index():
    # Inicializar storage SOLO al inicio
    app.storage.user['user-settings'] = {"clave": "valor"}
    
    # Initialize theme from browser storage or default to dark
    if 'dark_mode' not in app.storage.browser:
        app.storage.browser['dark_mode'] = True
    ui.dark_mode().bind_value(app.storage.browser, 'dark_mode')
    
    # Always reload the configuration from file to ensure we have the latest version
    try:
        app.storage.user['mcp-config'] = json.load(open('./settings/mcp-config.json'))
        print("Loaded MCP configuration from file")
    except Exception as e:
        print(f"Error loading MCP configuration: {str(e)}")
        if not app.storage.user.get('mcp-config'):
            app.storage.user['mcp-config'] = {"mcpServers": {}}
    
    # Initialize MCP client manager with the configuration
    async def init_mcp_client():
        # Add a flag to prevent multiple initializations
        if not hasattr(app.storage.user, 'mcp_initializing') or not app.storage.user.mcp_initializing:
            app.storage.user.mcp_initializing = True
            try:
                config = app.storage.user.get('mcp-config', {})
                success = await mcp_client_manager.initialize(config)
                
                # We need to use a safe way to notify from background tasks
                if success:
                    active_servers = mcp_client_manager.get_active_servers()
                    server_count = len(active_servers)
                    # Use app.storage to communicate with the UI
                    app.storage.user['mcp_status'] = f"Connected to {server_count} MCP servers"
                    app.storage.user['mcp_status_color'] = 'positive'
                else:
                    app.storage.user['mcp_status'] = "No active MCP servers found"
                    app.storage.user['mcp_status_color'] = 'warning'
            finally:
                app.storage.user.mcp_initializing = False
    
    # Run the initialization asynchronously
    asyncio.create_task(init_mcp_client())
    
    # Create a status indicator that updates from storage
    last_status = {'message': None, 'color': None}
    
    def update_status():
        nonlocal last_status
        if 'mcp_status' in app.storage.user:
            status = app.storage.user['mcp_status']
            color = app.storage.user.get('mcp_status_color', 'info')
            
            # Only show notification if status has changed
            if status != last_status['message'] or color != last_status['color']:
                ui.notify(status, color=color)
                last_status['message'] = status
                last_status['color'] = color
    
    # Check for status updates periodically
    ui.timer(1.0, update_status)
    
    # Variable local para sección activa (NO usar storage para esto)
    active_section = 'mcp_servers'
    
    content_container = ui.element('div').classes('q-pa-md w-full')
    
    def update_content(section):
        nonlocal active_section
        active_section = section  # ✅ Variable local, NO storage
        content_container.clear()
        
        if section == 'mcp_servers':
            show_mcp_servers_content(content_container)
        elif section == 'configure':
            show_configure_content(content_container)
        elif section == 'conversations':
            show_conversations_content(content_container)
        elif section == 'chat':
            show_chat_content(content_container)
    
    with ui.header(elevated=True).classes('app-header items-center'):
        ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
        ui.space()
        ui.label('MCP Client').classes('text-h5 text-white')
        ui.space()
        # Theme toggle button
        ui.button(icon='dark_mode', on_click=lambda: ui.dark_mode().toggle()).props('flat color=white').tooltip('Toggle dark/light mode')
    
    with ui.left_drawer(top_corner=True, bottom_corner=True).classes('nav-drawer') as left_drawer:
        ui.label('Navigation Menu').classes('text-h6 q-pa-md nav-title')
        with ui.list().classes('w-full'):
            with ui.item(on_click=lambda: update_content('mcp_servers')).classes('cursor-pointer'):
                ui.icon('dns')
                ui.label('MCP SERVERS')
            
            with ui.item(on_click=lambda: update_content('configure')).classes('cursor-pointer'):
                ui.icon('settings')
                ui.label('CONFIGURE')
            
            with ui.item(on_click=lambda: update_content('conversations')).classes('cursor-pointer'):
                ui.icon('forum')
                ui.label('CONVERSATIONS')
                
            with ui.item(on_click=lambda: update_content('chat')).classes('cursor-pointer'):
                ui.icon('chat')
                ui.label('CHAT')
    
    with ui.footer().classes('app-footer text-white q-pa-sm'):
        ui.label('© 2025 MCP Client - All rights reserved')
    
    # Initialize with the default content
    show_mcp_servers_content(content_container)

# Configurar el puerto
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(storage_secret="ultrasecretkeyboard", port=8081, reload=True, dark=True)