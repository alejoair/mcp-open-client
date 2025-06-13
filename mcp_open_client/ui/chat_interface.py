from nicegui import ui
from mcp_open_client.api_client import APIClient
from .message_parser import parse_and_render_message
from .chat_handlers import handle_send
from .python_executor import get_pyodide_html, set_global_components


def create_chat_interface(container):
    """
    Creates the main chat interface with tabs, message area, and input.
    
    Args:
        container: The container to render the chat interface in
    """
    # Create an instance of APIClient
    api_client = APIClient()
    
    # Apply CSS for proper layout expansion and code styling
    ui.add_css('''
        a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}
        .nicegui-code {
            border-radius: 8px !important;
            margin: 8px 0 !important;
            font-size: 14px !important;
        }
        .q-card {
            border-radius: 12px !important;
        }
    ''')
    
    # Make the page content expand properly
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')
    
    # Main layout container
    with ui.column().classes('h-full w-full flex flex-col'):
        
        # TABS SECTION - Fixed at top
        with ui.tabs().classes('w-full shrink-0') as tabs:
            chat_tab = ui.tab('Chat')
            logs_tab = ui.tab('Logs')
        
        # CONTENT SECTION - Expandable middle area with fixed height
        with ui.tab_panels(tabs, value=chat_tab).classes('w-full mx-auto flex-grow items-stretch'):
            
            # Chat Panel - Message container with scroll
            with ui.tab_panel(chat_tab).classes('items-stretch h-full'):

                with ui.scroll_area().classes('h-full w-full') as scroll_area:
                    message_container = ui.column().classes('w-full gap-2')
                    
                    # Create demo messages
                    create_demo_messages(message_container)
            
            # Logs Panel with scroll
            with ui.tab_panel(logs_tab).classes('h-full'):
                log_component = ui.log().classes('w-full h-full')
                # Sample log entries
                log_component.push('System initialized')
                log_component.push('Chat session started')
                log_component.push('Pyodide loading...')
                log_component.push('Custom input() function enabled')

        # Set global components for Python executor
        set_global_components(log_component, message_container)

        # SEND MESSAGE SECTION - Fixed at bottom
        with ui.row().classes('w-full items-center mb-25 shrink-0'):
            text_input = ui.input(placeholder='Message...').props('rounded outlined input-class=mx-3').classes('flex-grow')
            # Create async wrapper functions for the event handlers
            async def send_message():
                await handle_send(text_input, message_container, api_client, scroll_area)
            
            send_button = ui.button('Send', icon='send', on_click=send_message).props('no-caps')
            
            # Enable sending with Enter key
            text_input.on('keydown.enter', send_message)


def create_demo_messages(message_container):
    """Create demo messages for the chat interface"""
    with message_container:
        # Sample messages for demo
        with ui.card().classes('') as demo_bot_card:
            ui.label('Bot:').classes('font-bold mb-2')
            demo_message = '''Hello! Try this Python code with input:
```python
def saludar_usuario():
    nombre = input("Por favor, ingresa tu nombre: ")
    print(f"¡Hola, {nombre}! Bienvenido/a.")

# Llamar a la función
saludar_usuario()
```

Or this Python code without input:
```python
print("Numbers 1-5:")
for i in range(1, 6):
    print(f"Number: {i}")
```

This JavaScript code has no execute button:
```javascript
console.log("This is JavaScript");
```'''
            parse_and_render_message(demo_message, demo_bot_card)
            
        with ui.card().classes('ml-auto mr-4') as demo_user_card:
            ui.label('You:').classes('font-bold mb-2')
            parse_and_render_message('I want to test Python code execution', demo_user_card)