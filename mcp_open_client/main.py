from nicegui import ui, app
import asyncio
import json
import sys

# Import UI components
from mcp_open_client.ui.home import show_content as show_home_content
from mcp_open_client.ui.mcp_servers import show_content as show_mcp_servers_content
from mcp_open_client.ui.configure import show_content as show_configure_content
from mcp_open_client.ui.chat_window import show_content as show_chat_content

# Import MCP client manager
from mcp_open_client.mcp_client import mcp_client_manager

# Import conversation manager
from mcp_open_client.ui.conversation_manager import conversation_manager
from mcp_open_client.ui.chat_handlers import (
    get_all_conversations, create_new_conversation, load_conversation,
    delete_conversation, get_current_conversation_id
)

# Load the external CSS file from settings directory with cache busting
ui.add_css(f'mcp_open_client/settings/app-styles.css?v={__import__("time").time()}')

def init_storage():
    """Initialize storage without JavaScript execution"""
    # Initialize user settings
    if 'user-settings' not in app.storage.user:
        app.storage.user['user-settings'] = {"clave": "valor"}
    
    # Initialize theme from browser storage or default to dark
    if 'dark_mode' not in app.storage.browser:
        app.storage.browser['dark_mode'] = True
    ui.dark_mode().bind_value(app.storage.browser, 'dark_mode')
    
    # Always load configuration from file to ensure persistence
    try:
        with open('mcp_open_client/settings/mcp-config.json', 'r') as f:
            app.storage.user['mcp-config'] = json.load(f)
        print("Loaded MCP configuration from file")
    except Exception as e:
        print(f"Error loading MCP configuration: {str(e)}")
        # Only initialize empty config if it doesn't exist in storage
        if 'mcp-config' not in app.storage.user:
            app.storage.user['mcp-config'] = {"mcpServers": {}}

async def init_mcp_client():
    """Initialize MCP client manager with the configuration"""
    # Add a flag to prevent multiple initializations
    if not hasattr(app.storage.user, 'mcp_initializing') or not app.storage.user.mcp_initializing:
        app.storage.user.mcp_initializing = True
        try:
            config = app.storage.user.get('mcp-config', {})
            print(f"Initializing MCP client with config: {json.dumps(config, indent=2)}")
            
            if not config or not config.get('mcpServers'):
                raise ValueError("Invalid or empty MCP configuration")
            
            success = await mcp_client_manager.initialize(config)
            
            # We need to use a safe way to notify from background tasks
            if success:
                active_servers = mcp_client_manager.get_active_servers()
                server_count = len(active_servers)
                print(f"Successfully connected to {server_count} MCP servers")
                print(f"Active servers: {', '.join(active_servers.keys())}")
                # Use app.storage to communicate with the UI
                app.storage.user['mcp_status'] = f"Connected to {server_count} MCP servers"
                app.storage.user['mcp_status_color'] = 'positive'
            else:
                print("Failed to connect to any MCP servers")
                print("MCP client status:", mcp_client_manager.get_server_status())
                app.storage.user['mcp_status'] = "No active MCP servers found"
                app.storage.user['mcp_status_color'] = 'warning'
        except ValueError as ve:
            print(f"Configuration error: {str(ve)}")
            app.storage.user['mcp_status'] = f"Configuration error: {str(ve)}"
            app.storage.user['mcp_status_color'] = 'negative'
        except Exception as e:
            print(f"Error initializing MCP client: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception details: {repr(e)}")
            app.storage.user['mcp_status'] = f"Error: {str(e)}"
            app.storage.user['mcp_status_color'] = 'negative'
        finally:
            app.storage.user.mcp_initializing = False



# Global variables
conversations_container = None
current_update_content_function = None

def create_conversations_section():
    """Create the conversations section in the sidebar"""
    with ui.column().classes('w-full'):
        ui.label('Conversations').classes('text-subtitle1 text-weight-medium q-mb-sm')
        
        # New conversation button
        ui.button(
            'New Chat',
            icon='add',
            on_click=lambda: create_new_conversation_and_refresh()
        ).props('flat no-caps align-left full-width size=sm color=primary').classes('q-mb-sm')
    
        # Conversations list container - store reference globally for updates
        global conversations_container
        conversations_container = ui.column().classes('w-full')
        populate_conversations_list(conversations_container)
        
        return conversations_container

def create_new_conversation_and_refresh():
    """Create a new conversation and refresh the UI"""
    create_new_conversation()
    refresh_conversations_list()
    # Also refresh chat UI if callback is set
    conversation_manager.refresh_chat_ui()
    ui.notify('New conversation created', color='positive')

def refresh_conversations_list():
    """Refresh the conversations list in the sidebar"""
    global conversations_container
    if conversations_container:
        populate_conversations_list(conversations_container)

def populate_conversations_list(container):
    """Populate the conversations list in the sidebar"""
    if not container:
        return
        
    container.clear()
    
    conversations = get_all_conversations()
    current_id = get_current_conversation_id()
    
    with container:
        if not conversations:
            ui.label('No conversations yet').classes('text-caption text-grey-6 q-pa-sm')
            return
        
        # Sort conversations by updated_at (most recent first)
        sorted_conversations = sorted(
            conversations.items(),
            key=lambda x: x[1].get('updated_at', '0'),
            reverse=True
        )
        
        # Show only the 5 most recent conversations in sidebar
        for conv_id, conv_data in sorted_conversations[:5]:
            title = conv_data.get('title', f'Chat {conv_id[:8]}')
            message_count = len(conv_data.get('messages', []))
            
            # Highlight current conversation
            button_classes = 'drawer-btn text-left q-py-xs q-px-sm'
            if conv_id == current_id:
                button_classes += ' bg-blue-1 text-blue-8'
            
            with ui.row().classes('w-full items-center no-wrap'):
                # Conversation button (takes most space)
                conv_btn = ui.button(
                    title,
                    on_click=lambda cid=conv_id: load_conversation_and_refresh(cid)
                ).props('flat no-caps align-left').classes(f'{button_classes} flex-1 text-caption')
                conv_btn.style('min-width: 0; overflow: hidden; text-overflow: ellipsis;')
                
                # Delete button (small)
                ui.button(
                    icon='delete_outline',
                    on_click=lambda cid=conv_id: delete_conversation_with_confirm(cid)
                ).props('flat round size=xs color=grey-6').classes('q-ml-xs').style('min-width: 20px; width: 20px; height: 20px;')

def load_conversation_and_refresh(conversation_id: str):
    """Load a conversation and refresh the UI"""
    load_conversation(conversation_id)
    refresh_conversations_list()
    # Also refresh chat UI if callback is set
    conversation_manager.refresh_chat_ui()
    # Switch to chat view automatically
    global current_update_content_function
    if current_update_content_function:
        current_update_content_function('chat')
    ui.notify(f'Loaded conversation', color='info')

def delete_conversation_with_confirm(conversation_id: str):
    """Delete a conversation with confirmation"""
    def confirm_delete():
        delete_conversation(conversation_id)
        refresh_conversations_list()
        # Also refresh chat UI if callback is set
        conversation_manager.refresh_chat_ui()
        ui.notify('Conversation deleted', color='warning')
        dialog.close()
    
    def cancel_delete():
        dialog.close()
    
    with ui.dialog() as dialog:
        with ui.card().classes('q-pa-md'):
            ui.label('Delete Conversation?').classes('text-h6 q-mb-md')
            ui.label('This action cannot be undone.').classes('q-mb-md')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=cancel_delete).props('flat')
                ui.button('Delete', on_click=confirm_delete).props('color=red')
    
    dialog.open()

def setup_ui():
    """Setup the UI components"""
    @ui.page('/')
    def index():
        """Main application page"""
        
        # Initialize storage first
        init_storage()
        
        # Run the MCP initialization asynchronously
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
        active_section = 'home'
        
        # Función para verificar si una sección está activa
        def is_active(section):
            return 'active' if section == active_section else ''
        
        content_container = ui.row().classes('h-full w-full')
        
        def update_content(section):
            nonlocal active_section
            active_section = section  # ✅ Variable local, NO storage
            # Actualizar las clases de los elementos del menú
            for item in left_drawer.default_slot.children:
                if hasattr(item, 'default_slot') and item.default_slot.children:
                    for child in item.default_slot.children:
                        if hasattr(child, 'classes'):
                            section_name = child.props.get('on_click', lambda: None).__name__.split('_')[-1]
                            if section_name == section:
                                child.classes(add='active')
                            else:
                                child.classes(remove='active')
            content_container.clear()
            
            if section == 'home':
                show_home_content(content_container)
            elif section == 'mcp_servers':
                show_mcp_servers_content(content_container)
            elif section == 'configure':
                show_configure_content(content_container)
            elif section == 'chat':
                show_chat_content(content_container)
        
        # Make update_content available globally
        global current_update_content_function
        current_update_content_function = update_content
        
        with ui.header(elevated=True).classes('app-header'):
            with ui.row().classes('items-center full-width'):
                with ui.row().classes('items-center'):
                    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').classes('q-mr-sm')
                    ui.label('MCP-Open-Client').classes('app-title text-h5')
                
                ui.space()
                
                with ui.row().classes('items-center'):
                    ui.button(icon='notifications').classes('q-mr-sm').tooltip('Notifications')
                    ui.button(icon='help_outline').classes('q-mr-sm').tooltip('Help')
                    ui.button(icon='dark_mode', on_click=lambda: ui.dark_mode().toggle()).classes('q-mr-sm').tooltip('Toggle dark/light mode')
                    ui.button(icon='account_circle').tooltip('User Account')
        
        with ui.left_drawer(top_corner=True, bottom_corner=True).classes('nav-drawer q-pa-md') as left_drawer:
            ui.label('Navigation Menu').classes('text-h6 nav-title q-mb-lg')
            
            with ui.column().classes('w-full gap-2'):
                # Home button
                ui.button(
                    'Home',
                    icon='home',
                    on_click=lambda: update_content('home')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("home")}'
                )
                # MCP Servers button
                ui.button(
                    'MCP Servers',
                    icon='dns',
                    on_click=lambda: update_content('mcp_servers')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("mcp_servers")}'
                )
                
                # Configure button
                ui.button(
                    'Configure',
                    icon='settings',
                    on_click=lambda: update_content('configure')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("configure")}'
                )
                
                # Chat button
                ui.button(
                    'Chat',
                    icon='chat',
                    on_click=lambda: update_content('chat')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("chat")}'
                )
            
            # Conversations section
            ui.separator().classes('q-my-md')
            create_conversations_section()
            
            ui.separator()
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('© 2025 MCP Open Client').classes('text-subtitle2')
                with ui.row().classes('items-center'):
                    ui.button('Documentation', on_click=lambda: ui.open('https://docs.mcp-open-client.com'))
        
        # Set home as the default content
        update_content('chat')

def main():
    """Main entry point"""
    setup_ui()

def cli_entry():
    """Entry point for console script"""
    setup_ui()

# Setup UI when module is imported
setup_ui()

# Run the server - this needs to be at module level for entry points
ui.run(
    storage_secret="ultrasecretkeyboard",
    port=8082,
    reload=False,
    dark=True,
    show_welcome_message=True,
    show=False
)