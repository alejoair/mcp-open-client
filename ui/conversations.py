from nicegui import ui

def show_content(container):
    container.clear()
    with container:
        ui.label('CONFIGURE').classes('text-h4')
        ui.label('Configure your MCP client settings and preferences.')
        ui.separator()
        
        # Define table data
        rows = [
            {'setting': 'API Endpoint', 'value': 'https://api.mcp.example.com', 'status': 'Connected', 'actions': 'Edit'},
            {'setting': 'Authentication', 'value': 'OAuth2', 'status': 'Active', 'actions': 'View'},
            {'setting': 'Data Storage', 'value': 'Local', 'status': 'Enabled', 'actions': 'Configure'},
        ]
        
        # Create table with rows
        columns = [
            {'name': 'setting', 'label': 'Setting', 'field': 'setting'},
            {'name': 'value', 'label': 'Value', 'field': 'value'},
            {'name': 'status', 'label': 'Status', 'field': 'status'},
            {'name': 'actions', 'label': 'Actions', 'field': 'actions'},
        ]
        
        # Using the correct table API
        table = ui.table(columns=columns, rows=rows).classes('w-full').style('max-height: 400px')
        
        ui.button('Add Setting', icon='settings').props('color=primary')