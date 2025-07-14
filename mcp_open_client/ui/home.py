from nicegui import ui

def show_content(container):
    """
    Creates and renders a clean, vertical home page in the provided container.
    
    Args:
        container: The container to render the home page in
    """
    container.clear()
    container.classes('q-pa-md')
    
    with container:
        ui.label('Home').classes('text-2xl font-bold mb-6')
        
        # Welcome card
        with ui.card().classes('w-full mb-6'):
            ui.label('Bienvenido a MCP Open Client').classes('text-lg font-semibold mb-3')
            ui.label('Tu hub central para conectar modelos de IA con herramientas externas a través del protocolo MCP. Gestiona servidores, configura APIs y chatea con capacidades expandidas.').classes('text-sm text-gray-600 mb-4')
        
        # MCP Servers
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('dns').classes('mr-2 text-primary')
                    ui.label('MCP Servers').classes('text-lg font-semibold')
                ui.button('Gestionar', icon='arrow_forward', on_click=lambda: ui.navigate.to('/mcp_servers')).props('flat color=primary')
            ui.label('Conecta y gestiona servidores MCP para expandir las capacidades de tu IA con herramientas externas como editores de código, bases de datos y APIs web.').classes('text-sm text-gray-600')
        
        # Configuration
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('settings').classes('mr-2 text-secondary')
                    ui.label('Configuración').classes('text-lg font-semibold')
                ui.button('Configurar', icon='arrow_forward', on_click=lambda: ui.navigate.to('/configure')).props('flat color=secondary')
            ui.label('Configura tus proveedores de IA (OpenAI, Claude, modelos locales), ajusta prompts del sistema y personaliza la experiencia según tus necesidades.').classes('text-sm text-gray-600')
        
        # Chat
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('chat').classes('mr-2 text-accent')
                    ui.label('Chat').classes('text-lg font-semibold')
                ui.button('Iniciar Chat', icon='arrow_forward', on_click=lambda: ui.navigate.to('/chat')).props('flat color=accent')
            ui.label('Interfaz de chat con streaming en tiempo real, historial de conversaciones, resaltado de sintaxis e integración completa con herramientas MCP.').classes('text-sm text-gray-600')
        
        # History Settings
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('history').classes('mr-2 text-info')
                    ui.label('Configuración de Historial').classes('text-lg font-semibold')
                ui.button('Gestionar', icon='arrow_forward', on_click=lambda: ui.navigate.to('/history_settings')).props('flat color=info')
            ui.label('Configura el límite de mensajes en conversaciones y gestiona la limpieza automática del historial para optimizar el rendimiento.').classes('text-sm text-gray-600')
        
        # Documentation & Help
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('help_outline').classes('mr-2 text-positive')
                    ui.label('Documentación y Soporte').classes('text-lg font-semibold')
                ui.button('Ver Docs', icon='open_in_new', on_click=lambda: ui.open('https://docs.mcp-open-client.com')).props('flat color=positive')
            ui.label('Guías de usuario, documentación técnica del protocolo MCP y soporte de la comunidad para aprovechar al máximo la aplicación.').classes('text-sm text-gray-600')
