from nicegui import ui
from .message_parser import parse_and_render_message
import asyncio


async def safe_scroll_to_bottom(scroll_area):
    """Safely scroll to bottom with error handling and delay"""
    try:
        # Small delay to ensure DOM is updated
        await asyncio.sleep(0.1)
        scroll_area.scroll_to(percent=1.0)
    except Exception as e:
        # Silently ignore scroll errors to prevent crashes
        print(f"Scroll error (non-critical): {e}")


async def handle_send(input_field, message_container, api_client, scroll_area):
    """Handle sending a message asynchronously"""
    if input_field.value and input_field.value.strip():
        message = input_field.value.strip()
        
        # Add user message
        with message_container:
            with ui.card().classes('ml-auto mr-4 max-w-md') as user_card:
                ui.label('You:').classes('font-bold mb-2')
                parse_and_render_message(message, user_card)
        
        # Clear input
        input_field.value = ''
        
        # Auto-scroll to bottom of the scroll area (with error handling)
        await safe_scroll_to_bottom(scroll_area)
        
        # Send message to API and get response
        try:
            # Show spinner while waiting for response
            with message_container:
                spinner = ui.spinner('dots', size='lg')
            await safe_scroll_to_bottom(scroll_area)
            
            response = await api_client.chat_completion([{"role": "user", "content": message}])
            bot_response = response['choices'][0]['message']['content']
            
            # Remove spinner and add bot response
            spinner.delete()
            with message_container:
                with ui.card().classes('mr-auto ml-4') as bot_card:
                    ui.label('Bot:').classes('font-bold mb-2')
                    parse_and_render_message(bot_response, bot_card)
            
            # Auto-scroll to bottom again (with error handling)
            await safe_scroll_to_bottom(scroll_area)
            
        except Exception as e:
            # Remove spinner if error occurs
            if 'spinner' in locals():
                spinner.delete()
            # Add error message to chat instead of using ui.notify
            with message_container:
                with ui.card().classes('mr-auto ml-4 max-w-md') as error_card:
                    ui.label('System:').classes('font-bold mb-2 text-red-600')
                    parse_and_render_message(f'Error: {str(e)}', error_card)
            await safe_scroll_to_bottom(scroll_area)
    else:
        # we'll just ignore
        pass