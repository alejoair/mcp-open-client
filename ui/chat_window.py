from nicegui import ui
from api_client import APIClient
import asyncio

def show_content(container):
    """
    Creates a GPT-style chat interface in the provided container.
    
    Args:
        container: The container to render the chat interface in
    """
    # Clear and setup the container
    container.clear()
    container.classes('h-full w-full flex flex-col mb-25')
    
    with container:
        # Create an instance of APIClient
        api_client = APIClient()
        
        # Apply CSS for proper layout expansion
        ui.add_css('a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}')
        
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
            with ui.tab_panels(tabs, value=chat_tab).classes('w-full px-10 mx-auto flex-grow items-stretch'):
                
                # Chat Panel - Message container with scroll
                with ui.tab_panel(chat_tab).classes('items-stretch h-full'):
                    with ui.scroll_area().classes('h-full w-full') as scroll_area:
                        message_container = ui.column().classes('w-full gap-2')
                        with message_container:
                            # Sample messages for demo using markdown
                            with ui.card().classes('mr-auto ml-4 max-w-md'):
                                ui.markdown('**Bot:** Hello! How can I help you today?')
                            with ui.card().classes('ml-auto mr-4 max-w-md'):
                                ui.markdown('**You:** I need help with NiceGUI layout design')
                
                # Logs Panel with scroll
                with ui.tab_panel(logs_tab).classes('h-full'):
                    log = ui.log().classes('w-full h-full')
                    # Sample log entries
                    log.push('System initialized')
                    log.push('Chat session started')

            # SEND MESSAGE SECTION - Fixed at bottom
            with ui.row().classes('w-full items-center mb-25 shrink-0'):
                text_input = ui.input(placeholder='Message...').props('rounded outlined input-class=mx-3').classes('flex-grow')
                send_button = ui.button('Send', icon='send', on_click=lambda: handle_send(text_input, message_container, api_client, scroll_area)).props('no-caps')
                
                # Enable sending with Enter key
                text_input.on('keydown.enter', lambda: handle_send(text_input, message_container, api_client, scroll_area))

async def handle_send(input_field, message_container, api_client, scroll_area):
    """Handle sending a message asynchronously"""
    if input_field.value and input_field.value.strip():
        message = input_field.value.strip()
        
        # Add user message
        with message_container:
            with ui.card().classes('ml-auto mr-4 max-w-md'):
                ui.markdown(f'**You:** {message}')
        
        # Clear input
        input_field.value = ''
        
        # Auto-scroll to bottom using JavaScript (like in the examples)
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        
        # Send message to API and get response
        try:
            # Show spinner while waiting for response
            with message_container:
                spinner = ui.spinner('dots', size='lg')
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
            
            response = await api_client.chat_completion([{"role": "user", "content": message}])
            bot_response = response['choices'][0]['message']['content']
            
            # Remove spinner and add bot response
            spinner.delete()
            with message_container:
                with ui.card().classes('mr-auto ml-4 max-w-md'):
                    ui.markdown(f'**Bot:** {bot_response}')
            
            # Auto-scroll to bottom again
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
            
        except Exception as e:
            # Remove spinner if error occurs
            if 'spinner' in locals():
                spinner.delete()
            # Add error message to chat instead of using ui.notify
            with message_container:
                with ui.card().classes('mr-auto ml-4 max-w-md'):
                    ui.markdown(f'**System:** Error: {str(e)}')
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
    else:
        # For empty messages, we can't use ui.notify either, so we'll just ignore
        pass