from nicegui import ui
from mcp_open_client.api_client import APIClient
from .message_parser import parse_and_render_message
from .chat_handlers import handle_send, get_messages, get_current_conversation_id, render_message_to_ui
from .conversation_manager import conversation_manager


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
        .q-field__control {
            border-radius: 12px !important;
        }
        .q-field--outlined .q-field__control {
            border-radius: 12px !important;
        }
    ''')
    
    # Make the page content expand properly
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')
    
    # Main layout container - optimized for mobile
    with ui.column().classes('chat-container h-full w-full flex flex-col'):
                
                # TABS SECTION - Fixed at top (optional, can be hidden on mobile)
                with ui.tabs().classes('w-full shrink-0') as tabs:
                    chat_tab = ui.tab('Chat')
                
                # CONTENT SECTION - Expandable middle area with fixed height
                with ui.tab_panels(tabs, value=chat_tab).classes('w-full mx-auto flex-grow items-stretch'):
                    
                    # Chat Panel - Message container with scroll
                    with ui.tab_panel(chat_tab).classes('items-stretch h-full'):

                        with ui.scroll_area().classes('chat-messages h-full w-full') as scroll_area:
                            message_container = ui.column().classes('w-full gap-2 q-pa-md')
                            
                            # Load messages from current conversation
                            load_conversation_messages(message_container)
                    
                # Set up conversation manager callback to refresh chat
                async def refresh_chat():
                    message_container.clear()
                    load_conversation_messages(message_container)
                    # Import and use the improved scroll function
                    from .chat_handlers import safe_scroll_to_bottom
                    await safe_scroll_to_bottom(scroll_area, delay=0.3)
                
                conversation_manager.set_refresh_callback(refresh_chat)

                # SEND MESSAGE SECTION - Fixed at bottom, mobile optimized
                with ui.row().classes('chat-input-area w-full items-end gap-3 shrink-0'):
                    text_input = ui.textarea(placeholder='Type your message... (Press Enter to send)').props('rounded outlined autogrow input-style="max-height: 120px"').classes('mobile-textarea flex-grow')
                    
                    # Create async wrapper functions for the event handlers
                    async def send_message():
                        if text_input.value and text_input.value.strip():
                            await handle_send(text_input, message_container, api_client, scroll_area)
                    
                    send_button = ui.button(icon='send', on_click=send_message).classes('send-button')
                    
                    # Enable sending with Enter key
                    text_input.on('keydown.enter', send_message)
                    
                    # Add instructions for users
                    ui.label('Press Enter to send, Shift+Enter for new line').classes('text-caption text-grey-6 q-mt-xs')


def load_conversation_messages(message_container):
    """Load messages from the current conversation"""
    messages = get_messages()
    
    if not messages:
        # Show welcome message if no conversation is active
        with message_container:
            with ui.card().classes('') as welcome_card:
                ui.label('Assistant:').classes('font-bold mb-2')
                welcome_message = '''Welcome to MCP Open Client!

I can help you interact with MCP (Model Context Protocol) servers.

Try asking me something or create a new conversation to get started.'''
                parse_and_render_message(welcome_message, welcome_card)
        return
    
    render_messages(message_container)

def render_messages(message_container):
    """Render all messages from the current conversation"""
    messages = get_messages()
    
    # Clear existing messages
    message_container.clear()
    
    if not messages:
        # Show welcome message if no messages
        with message_container:
            with ui.card().classes('') as welcome_card:
                ui.label('Welcome!').classes('font-bold mb-2')
                welcome_message = '''Welcome to MCP Open Client!

I can help you interact with MCP (Model Context Protocol) servers and answer your questions.

Try asking me something or create a new conversation to get started.'''
                parse_and_render_message(welcome_message, welcome_card)
        return
    
    # Render all messages from the conversation using the centralized function
    for message in messages:
        render_message_to_ui(message, message_container)


def create_demo_messages(message_container):
    """Create demo messages for the chat interface"""
    with message_container:
        # Sample messages for demo
        with ui.card().classes('') as demo_bot_card:
            ui.label('Bot:').classes('font-bold mb-2')
            demo_message = '''Hello! I can help you interact with MCP servers and answer your questions.

Feel free to ask me anything or start a conversation!'''
            parse_and_render_message(demo_message, demo_bot_card)
            
        with ui.card().classes('ml-auto mr-4') as demo_user_card:
            ui.label('You:').classes('font-bold mb-2')
            parse_and_render_message('Hello! How can you help me?', demo_user_card)