from nicegui import ui

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
                    with ui.scroll_area().classes('h-full w-full'):
                        message_container = ui.column().classes('w-full gap-2')
                        with message_container:
                            # Sample messages for demo
                            ui.chat_message('Hello! How can I help you today?', name='Bot', sent=False)
                            ui.chat_message('I need help with NiceGUI layout design', name='You', sent=True)
                
                # Logs Panel with scroll
                with ui.tab_panel(logs_tab).classes('h-full'):
                    log = ui.log().classes('w-full h-full')
                    # Sample log entries
                    log.push('System initialized')
                    log.push('Chat session started')

            # SEND MESSAGE SECTION - Fixed at bottom
            with ui.row().classes('w-full items-center mb-25 shrink-0'):
                text_input = ui.input(placeholder='Message...').props('rounded outlined input-class=mx-3').classes('flex-grow')
                ui.button('Send', icon='send', on_click=lambda: handle_send(text_input, message_container))

def handle_send(input_field, message_container):
    """Handle sending a message"""
    if input_field.value and input_field.value.strip():
        message = input_field.value.strip()
        
        # Add user message
        with message_container:
            ui.chat_message(text=message, name='You', sent=True)
            
            # Add bot response (simulated)
            bot_response = f"Thanks for your message: '{message}'. This is a demo response!"
            ui.chat_message(text=bot_response, name='Bot', sent=False)
        
        # Clear input
        input_field.value = ''
        
        # Auto-scroll to bottom of the scroll area
        ui.run_javascript('''
            const scrollArea = document.querySelector('.q-scrollarea__container');
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
        ''')
        
        ui.notify('Message sent!', type='positive')
    else:
        ui.notify('Please enter a message', type='warning')