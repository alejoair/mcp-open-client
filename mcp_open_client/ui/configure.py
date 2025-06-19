from nicegui import ui, app

def show_content(container):
    container.clear()
    with container:
        ui.label('CONFIGURE').classes('text-h4')
        ui.label('Configure your MCP client settings and preferences.')
        ui.separator()

        # Load USER configuration from user storage (persistent) - separate from MCP
        config = app.storage.user.get('user-config', {})

        # API Key input
        api_key_input = ui.input(label='API Key', value=config.get('api_key', '')).classes('w-full')

        # Base URL input
        base_url_input = ui.input(label='Base URL', value=config.get('base_url', 'http://192.168.58.101:8123')).classes('w-full')

        # Model selection
        model_options = ['gpt-3.5-turbo', 'gpt-4', 'claude-3-5-sonnet', 'claude-3-opus']
        model_select = ui.select(label='Model', options=model_options, value=config.get('model', 'claude-3-5-sonnet')).classes('w-full')

        def save_config():
            # Create new user config (independent from MCP config)
            new_user_config = {
                'api_key': api_key_input.value,
                'base_url': base_url_input.value,
                'model': model_select.value
            }
            
            # Update user storage - automatically persistent
            app.storage.user['user-config'] = new_user_config
            ui.notify('User configuration saved successfully', color='positive')

        ui.button('Save Configuration', on_click=save_config).props('color=primary')

        # Display current configuration
        with ui.expansion('Current Configuration', icon='settings').classes('w-full'):
            ui.label('API Key: ' + ('*' * len(config.get('api_key', ''))))
            ui.label('Base URL: ' + config.get('base_url', 'Not set'))
            ui.label('Model: ' + config.get('model', 'Not set'))

        # Add a button to reset configuration to defaults
        def reset_to_defaults():
            api_key_input.value = ''
            base_url_input.value = 'http://192.168.58.101:8123'
            model_select.value = 'claude-3-5-sonnet'
            ui.notify('Configuration reset to defaults', color='info')

        ui.button('Reset to Defaults', on_click=reset_to_defaults).props('color=secondary')
