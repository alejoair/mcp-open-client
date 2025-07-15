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
    with ui.column().classes('chat-container h-full w-full flex flex-col').style('box-sizing: border-box; background: transparent;'):
                
                # TABS SECTION - Fixed at top (optional, can be hidden on mobile)
                with ui.tabs().classes('w-full shrink-0').style('display: none;') as tabs:
                    chat_tab = ui.tab('Chat')
                
                # STATS SECTION - Conversation statistics bar
                stats_container = create_stats_bar()
                # Register the stats update callback
                set_stats_update_callback(stats_container.update_stats)
                
                # CONTENT SECTION - Expandable middle area with fixed height
                with ui.tab_panels(tabs, value=chat_tab).classes('w-full flex-grow items-stretch'):
                    
                    # Chat Panel - Message container with scroll
                    with ui.tab_panel(chat_tab).classes('items-stretch h-full').style('padding: 0; margin: 0;'):

                        with ui.scroll_area().classes('chat-messages h-full w-full').style('background: transparent !important;') as scroll_area:
                            message_container = ui.column().classes('w-full')
                            
                            # Load messages from current conversation
                            load_conversation_messages(message_container)
                    
                # Set up conversation manager callback to refresh chat
                def refresh_chat():
                    print(f"🔄 REFRESH_CHAT called - Loading conversation")
                    message_container.clear()
                    load_conversation_messages(message_container)
                    # Update stats when conversation changes
                    stats_container.update_stats()
                    
                    # Use longer delay for conversation loading (DOM needs more time)
                    def do_scroll():
                        print(f"⬇️ SCROLL CONVERSATION LOAD - DOM ready, executing scroll")
                        
                        # Find the current scroll_area dynamically instead of using stale reference
                        try:
                            # Query for the scroll area with the specific class
                            current_scroll_areas = [elem for elem in ui.context.client.elements.values() 
                                                   if hasattr(elem, '__class__') and 
                                                   elem.__class__.__name__ == 'ScrollArea' and 
                                                   hasattr(elem, 'classes') and 
                                                   'chat-messages' in str(elem.classes)]
                            
                            if current_scroll_areas:
                                current_scroll_area = current_scroll_areas[0]  # Take the first (should be only one)
                                print(f"📎 SCROLL DEBUG: Found current scroll_area={type(current_scroll_area)}, id={getattr(current_scroll_area, 'id', 'N/A')}")
                                print(f"📏 SCROLL DEBUG: message_container children={len(message_container.default_slot.children) if hasattr(message_container, 'default_slot') else 'N/A'}")
                                
                                result = current_scroll_area.scroll_to(percent=1.0)
                                print(f"✅ SCROLL COMPLETED - conversation load, result={result}")
                                print(f"🎯 SCROLL DEBUG: scroll_to called successfully on current scroll_area")
                            else:
                                print(f"❌ No scroll_area found with chat-messages class")
                                # Fallback to original reference
                                print(f"📎 FALLBACK: Using original scroll_area={type(scroll_area)}, id={getattr(scroll_area, 'id', 'N/A')}")
                                result = scroll_area.scroll_to(percent=1.0)
                                print(f"✅ FALLBACK SCROLL COMPLETED")
                                
                        except Exception as e:
                            print(f"❌ Scroll error: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    try:
                        # Use longer delay for conversation loading - DOM needs more time to render
                        print(f"⏰ SETTING ui.timer for conversation load with delay=0.3 (longer for DOM)")
                        ui.timer(0.3, do_scroll, once=True)
                        print(f"✅ Timer set successfully for conversation load")
                    except Exception as timer_error:
                        print(f"⚠️ ui.timer failed for conversation load: {timer_error}")
                    
                    print(f"✅ REFRESH_CHAT completed")
                
                conversation_manager.set_refresh_callback(refresh_chat)

                # SEND MESSAGE SECTION - Fixed at bottom, mobile optimized
                with ui.row().classes('w-full items-center shrink-0 input-row'):
                    text_input = ui.textarea(placeholder='Type your message...').props('outlined autogrow input-style="max-height: 80px;"').classes('flex-grow rounded-lg chat-input-field')
                    
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
    print(f"📝 LOADING MESSAGES: Found {len(messages) if messages else 0} messages")
    
    if not messages:
        print(f"👋 SHOWING welcome message - no conversation active")
        # Show welcome message if no conversation is active
        with message_container:
            with ui.card().classes('') as welcome_card:
                # Role label removed - visual distinction by position and color
                welcome_message = '''Welcome to MCP Open Client!

I can help you interact with MCP (Model Context Protocol) servers.

Try asking me something or create a new conversation to get started.'''
                parse_and_render_message(welcome_message, welcome_card)
        return
    
    print(f"🎨 RENDERING {len(messages)} messages to container")
    render_messages(message_container)
    print(f"✅ MESSAGES RENDERED successfully")

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
    with ui.row().classes('w-full border-b border-gray-700 py-2 items-center justify-between text-xs') as stats_container:
        # Left side - Conversation stats
        with ui.row().classes('items-center gap-4'):
            conv_messages_label = ui.label('0 messages').classes('text-gray-400')
            ui.separator().props('vertical')
            conv_tokens_label = ui.label('0 tokens').classes('text-gray-400')
            ui.separator().props('vertical')
            conv_limit_label = ui.label('0%').classes('text-gray-400')
            
    # Function to update stats
    def update_stats():
        conv_id = get_current_conversation_id()
        if conv_id:
            # Get conversation stats - use our enhanced get_messages with stats
            conversation_data = get_messages(include_stats=True)
            conv_stats = conversation_data.get('stats', {})
            settings = history_manager.get_settings()
            
            # Update conversation stats - show tokens as primary metric
            conv_messages_label.text = f"{conv_stats.get('message_count', 0)} messages"
            
            # Format token count with thousands separator
            total_tokens = conv_stats.get('total_tokens', 0)
            conv_tokens_label.text = f"{total_tokens:,} tokens"
            
            # Calculate and show percentage of limit based on tokens
            max_tokens = settings.get('max_tokens_per_conversation', 50000)
            token_percentage = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0
            conv_limit_label.text = f"{token_percentage:.1f}% of limit"
            
            # Show token counting method as tooltip
            token_method = settings.get('token_counting_method', 'heuristic')
            conv_tokens_label.tooltip = f"Counted using {token_method}"
            
            # Color coding based on token percentage
            if token_percentage > 90:
                conv_limit_label.classes('text-red-400', remove='text-yellow-400 text-gray-400')
                conv_tokens_label.classes('text-red-400', remove='text-yellow-400 text-gray-400')
            elif token_percentage > 70:
                conv_limit_label.classes('text-yellow-400', remove='text-red-400 text-gray-400')
                conv_tokens_label.classes('text-yellow-400', remove='text-red-400 text-gray-400')
            else:
                conv_limit_label.classes('text-gray-400', remove='text-red-400 text-yellow-400')
                conv_tokens_label.classes('text-gray-400', remove='text-red-400 text-yellow-400')
            
            # Show conversation ID and chars as secondary info
            # Removed history_indicator - no longer showing conversation ID
        else:
            # No active conversation
            conv_messages_label.text = ""
            conv_tokens_label.text = ""
            conv_limit_label.text = ""
    
    # Initial update
    update_stats()
    
    # Store the update function so it can be called from outside
    stats_container.update_stats = update_stats
    
    return stats_container
