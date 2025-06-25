from nicegui import ui
from mcp_open_client.api_client import APIClient
from .message_parser import parse_and_render_message
from .chat_handlers import handle_send, get_messages, get_current_conversation_id, render_message_to_ui, set_stats_update_callback, set_stop_generation
from .history_manager import history_manager
from .conversation_manager import conversation_manager
import asyncio

# Global variable to track generation state
generation_active = False
stop_generation = False

def create_chat_interface(container):
    """
    Creates the main chat interface with tabs, message area, and input.
    
    Args:
        container: The container to render the chat interface in
    """
    # Create an instance of APIClient
    api_client = APIClient()
    
    # All CSS styles are now in the external CSS file
    
    # Make the page content expand properly
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')
    
    # Main layout container - optimized for mobile
    with ui.column().classes('chat-container h-full w-full flex flex-col'):
                
                # TABS SECTION - Fixed at top (optional, can be hidden on mobile)
                with ui.tabs().classes('w-full shrink-0') as tabs:
                    chat_tab = ui.tab('Chat')
                
                # STATS SECTION - Conversation statistics bar
                stats_container = create_stats_bar()
                # Register the stats update callback
                set_stats_update_callback(stats_container.update_stats)
                
                # CONTENT SECTION - Expandable middle area with fixed height
                with ui.tab_panels(tabs, value=chat_tab).classes('w-full flex-grow items-stretch'):
                    
                    # Chat Panel - Message container with scroll
                    with ui.tab_panel(chat_tab).classes('items-stretch h-full'):

                        with ui.scroll_area().classes('chat-messages h-full w-full') as scroll_area:
                            message_container = ui.column().classes('w-full gap-1')
                            
                            # Load messages from current conversation
                            load_conversation_messages(message_container)
                    
                # Set up conversation manager callback to refresh chat
                async def refresh_chat():
                    message_container.clear()
                    load_conversation_messages(message_container)
                    # Update stats when conversation changes
                    stats_container.update_stats()
                    # Import and use the improved scroll function
                    from .chat_handlers import safe_scroll_to_bottom
                    await safe_scroll_to_bottom(scroll_area, delay=0.3)
                
                conversation_manager.set_refresh_callback(refresh_chat)

                # SEND MESSAGE SECTION - Fixed at bottom, mobile optimized
                with ui.row().classes('w-full items-center gap-3 shrink-0 p-1'):
                    text_input = ui.textarea(placeholder='Type your message...').props('outlined autogrow input-style="max-height: 120px;"').classes('flex-grow min-h-12 rounded-lg')
                    
                    # Create async wrapper functions for the event handlers
                    async def send_message():
                        global generation_active, stop_generation
                        if not generation_active and text_input.value and text_input.value.strip():
                            # Start generation
                            generation_active = True
                            stop_generation = False
                            
                            # Change button to stop mode
                            send_button.props('color=negative icon=stop')
                            send_button.tooltip = 'Stop generation'
                            text_input.props('disable')
                            
                            try:
                                await handle_send(text_input, message_container, api_client, scroll_area, send_button)
                            finally:
                                # Reset button to send mode
                                generation_active = False
                                send_button.props('color=primary icon=send')
                                send_button.tooltip = 'Send message'
                                text_input.props(remove='disable')
                    
                    async def stop_generation_handler():
                        global stop_generation
                        if generation_active:
                            stop_generation = True
                            set_stop_generation()  # Notify chat_handlers
                            # Reset button immediately
                            send_button.props('color=primary icon=send')
                            send_button.tooltip = 'Send message'
                            text_input.props(remove='disable')
                    
                    # Button that changes function based on state
                    async def button_click():
                        if generation_active:
                            await stop_generation_handler()
                        else:
                            await send_message()
                    
                    send_button = ui.button(icon='send', on_click=button_click).classes('h-12 w-12 min-w-12 rounded-full').props('color=primary')
                    send_button.tooltip = 'Send message'
                    
                    # Enable sending with Enter key (only when not generating)
                    async def handle_enter():
                        if not generation_active:
                            await send_message()
                    
                    text_input.on('keydown.enter', handle_enter)
                    


def load_conversation_messages(message_container):
    """Load messages from the current conversation"""
    messages = get_messages()
    
    if not messages:
        # Show welcome message if no conversation is active
        with message_container:
            with ui.card().classes('') as welcome_card:
                # Role label removed - visual distinction by position and color
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
                ui.label('Welcome!').classes('font-bold')
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
            demo_message = '''Hello! I can help you interact with MCP servers and answer your questions.

Feel free to ask me anything or start a conversation!'''
            parse_and_render_message(demo_message, demo_bot_card)
            
        with ui.card().classes('ml-auto mr-4') as demo_user_card:
            # Role label removed - visual distinction by position and color
            parse_and_render_message('Hello! How can you help me?', demo_user_card)


def create_stats_bar():
    """Create a statistics bar showing current conversation info"""
    with ui.row().classes('w-full bg-gray-800/20 border-b border-gray-700 p-2 items-center justify-between text-xs') as stats_container:
        # Left side - Conversation stats
        with ui.row().classes('items-center gap-4'):
            conv_chars_label = ui.label('0 chars').classes('text-gray-400')
            ui.separator().props('vertical')
            conv_messages_label = ui.label('0 messages').classes('text-gray-400')
            ui.separator().props('vertical')
            conv_limit_label = ui.label('0%').classes('text-gray-400')
        
        # Right side - Conversation ID indicator
        with ui.row().classes('items-center gap-2'):
            history_indicator = ui.label('').classes('text-gray-500 text-xs')
            
    # Function to update stats
    def update_stats():
        conv_id = get_current_conversation_id()
        if conv_id:
            # Get conversation stats
            conv_stats = history_manager.get_conversation_size(conv_id)
            settings = history_manager.get_settings()
            
            # Update conversation stats - show tokens as primary
            conv_chars_label.text = f"{conv_stats['total_tokens']:,} tokens"
            conv_messages_label.text = f"{conv_stats['message_count']} messages"
            
            # Calculate and show percentage of limit based on tokens
            token_percentage = (conv_stats['total_tokens'] / settings['max_tokens_per_conversation']) * 100
            conv_limit_label.text = f"{token_percentage:.1f}% of limit"
            
            # Color coding based on token percentage
            if token_percentage > 90:
                conv_limit_label.classes('text-red-400', remove='text-yellow-400 text-gray-400')
            elif token_percentage > 70:
                conv_limit_label.classes('text-yellow-400', remove='text-red-400 text-gray-400')
            else:
                conv_limit_label.classes('text-gray-400', remove='text-red-400 text-yellow-400')
            
            # Show conversation ID and chars as secondary info
            history_indicator.text = f"ID: {conv_id[:8]}... | {conv_stats['total_chars']:,} chars"
        else:
            # No active conversation
            conv_chars_label.text = "No conversation"
            conv_messages_label.text = ""
            conv_limit_label.text = ""
            history_indicator.text = ""
    
    # Initial update
    update_stats()
    
    # Store the update function so it can be called from outside
    stats_container.update_stats = update_stats
    
    return stats_container
