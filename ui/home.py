from nicegui import ui

def show_content(container):
    """
    Creates and renders a home page with a grid of cards in the provided container.
    
    Args:
        container: The container to render the home page in
    """
    # Ensure the parent container has proper height and takes full space
    container.clear()
    container.classes('h-full w-full flex flex-col')
    
    with container:
        ui.label('Home').classes('text-h4 text-primary mb-2')
        
        # Main content container that fills all available space
        with ui.card().classes('flex-grow w-full flex flex-col p-4'):
            # Welcome message
            with ui.card().classes('w-full p-4 text-center mb-4'):
                ui.label('Welcome to MCP Open Client').classes('text-h5 font-bold mb-2')
                ui.label('Your central hub for managing MCP servers and communications')
                ui.separator().classes('my-2')
                ui.label('Select a card below to explore features or use the navigation menu')
            
            # Grid of feature cards
            with ui.grid(columns=3).classes('w-full gap-4'):
                # Card 1
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-primary text-white'):
                        ui.label('MCP Servers').classes('text-h6')
                    with ui.card_section():
                        ui.label('Server Management').classes('text-subtitle1 font-bold')
                        ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')
                    with ui.card_section().classes('bg-gray-100'):
                        with ui.row().classes('justify-end'):
                            ui.button('Explore', icon='dns', on_click=lambda: ui.navigate.to('/mcp_servers')).props('flat')
                
                # Card 2
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-secondary text-white'):
                        ui.label('Configuration').classes('text-h6')
                    with ui.card_section():
                        ui.label('System Settings').classes('text-subtitle1 font-bold')
                        ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')
                    with ui.card_section().classes('bg-gray-100'):
                        with ui.row().classes('justify-end'):
                            ui.button('Configure', icon='settings', on_click=lambda: ui.navigate.to('/configure')).props('flat')
                
                # Card 3
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-accent text-white'):
                        ui.label('Chat').classes('text-h6')
                    with ui.card_section():
                        ui.label('Communication').classes('text-subtitle1 font-bold')
                        ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')
                    with ui.card_section().classes('bg-gray-100'):
                        with ui.row().classes('justify-end'):
                            ui.button('Open Chat', icon='chat', on_click=lambda: ui.navigate.to('/chat')).props('flat')
                
                # Card 4
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-positive text-white'):
                        ui.label('Documentation').classes('text-h6')
                    with ui.card_section():
                        ui.label('User Guides').classes('text-subtitle1 font-bold')
                        ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')
                    with ui.card_section().classes('bg-gray-100'):
                        with ui.row().classes('justify-end'):
                            ui.button('View Docs', icon='description', on_click=lambda: ui.open('https://docs.mcp-open-client.com')).props('flat')
                
                # Card 5
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-info text-white'):
                        ui.label('Status').classes('text-h6')
                    with ui.card_section():
                        ui.label('System Status').classes('text-subtitle1 font-bold')
                        ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')
                    with ui.card_section().classes('bg-gray-100'):
                        with ui.row().classes('justify-end'):
                            ui.button('Check Status', icon='monitoring', on_click=lambda: ui.notify('Status check initiated', color='info')).props('flat')
                
                # Card 6
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-warning text-white'):
                        ui.label('Help').classes('text-h6')
                    with ui.card_section():
                        ui.label('Support').classes('text-subtitle1 font-bold')
                        ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')
                    with ui.card_section().classes('bg-gray-100'):
                        with ui.row().classes('justify-end'):
                            ui.button('Get Help', icon='help', on_click=lambda: ui.notify('Help system coming soon', color='warning')).props('flat')