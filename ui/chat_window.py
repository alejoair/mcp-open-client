from nicegui import ui

"""
LAYOUT GUIDE FOR PROPER SCROLLING:

1. Parent container needs:
   - h-full: to take full height of its parent
   - flex flex-col: to enable vertical flex layout

2. Fixed-height elements need:
   - shrink-0: to prevent them from shrinking when content grows

3. Scrollable area needs:
   - flex-grow: to take remaining space
   - No fixed height (let it expand naturally)

4. Content inside scroll area:
   - Can have any height (will scroll as needed)
"""

def show_content(container):
    """
    Creates and renders a chat window in the provided container.
    
    Args:
        container: The container to render the chat window in
    """
    # Ensure the parent container has proper height and takes full space
    container.clear()
    container.classes('h-full w-full flex flex-col')
    with container:
        ui.label('Chat').classes('text-h4 text-primary mb-2')
        
        # Container that fills all available space with border
        with ui.card().classes('flex-grow w-full flex flex-col justify-between p-4'):
            # Header area (fixed height)
            with ui.row().classes('w-full shrink-0 mb-2'):
                ui.label('Container Header').classes('text-lg font-bold')
                ui.space()
                ui.button(icon='refresh').props('flat')
            
            # Scrollable content area (takes remaining space)
            with ui.scroll_area().classes('w-full flex-grow'):
                with ui.column().classes('w-full gap-2 p-2'):
                    # Welcome message
                    with ui.card().classes('w-full p-4 text-center'):
                        ui.label('Scrollable Content Demo').classes('text-xl font-bold mb-2')
                        ui.label('This area scrolls independently while header and footer stay fixed')
                        ui.separator().classes('my-2')
                        ui.label('Try scrolling down to see more items')
                    
                    # Generate some sample content
                    for i in range(20):
                        with ui.card().classes('w-full p-2'):
                            ui.label(f'Item {i+1}')
            
            # Footer area (fixed height) - aligned to bottom
            with ui.row().classes('w-full shrink-0 mt-auto items-center'):
                input_field = ui.input(placeholder='Type something...').classes('flex-grow')
                ui.button('Send', icon='send').classes('ml-2')
