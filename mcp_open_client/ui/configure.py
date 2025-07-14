from nicegui import ui, app
from mcp_open_client.config_utils import load_initial_config_from_files
from mcp_open_client.api_client import APIClient
import asyncio

# Global API client instance for updates
_api_client_instance = None

def get_api_client():
    """Get or create API client instance"""
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = APIClient()
    return _api_client_instance

def show_content(container):
    print("DEBUG: Starting show_content function")
    container.clear()
    with container:
        print("DEBUG: Inside container context")
        # Header section with modern styling
        # Header section removed - going straight to content
        print("DEBUG: Creating header section")
        print("DEBUG: Header section created successfully")
        print("DEBUG: About to create main configuration card")
        # Main configuration card  
        with ui.card().classes('w-full max-w-4xl q-ma-auto q-pa-lg'):
            print("DEBUG: Inside main card context")
            # Function to get current config (always fresh from storage)
            def get_current_config():
                try:
                    result = app.storage.user.get('user-settings', {})
                    print(f"DEBUG: get_current_config returned")
                    return result
                except Exception as e:
                    print(f"DEBUG: Error in get_current_config: {str(e)}")
                    return {}

            print("DEBUG: About to load current configuration")
            # Load current configuration
            config = get_current_config()
            print(f"DEBUG: Configuration loaded")

            # API Configuration Section
            print("DEBUG: Creating API Configuration section")
            with ui.column().classes('w-full q-mb-lg'):
                print("DEBUG: Inside API Configuration column")
                ui.label('🔑 API Configuration').classes('text-h6 text-weight-semibold q-mb-md')
                print("DEBUG: API Configuration label created")
                
                # API Key input with password toggle
                print("DEBUG: About to create API Key row")
                with ui.row().classes('w-full q-col-gutter-md'):
                    print("DEBUG: Inside API Key row")
                    # Safe handling of API key value
                    api_key_value = config.get('api_key', '')
                    print(f"DEBUG: API key length: {len(api_key_value)}")
                    # Truncate very long API keys for display
                    if len(api_key_value) > 100:
                        api_key_value = api_key_value[:100]
                        print("DEBUG: API key truncated for display")
                    print("DEBUG: About to create API key input")
                    api_key_input = ui.input(
                        label='API Key', 
                        value=api_key_value,
                        password=True,
                        password_toggle_button=True
                    ).classes('col-12 col-sm-6')
                    print("DEBUG: API key input created successfully")

                print("DEBUG: About to create Base URL input")
                # Base URL input
                base_url_input = ui.input(
                    label='Base URL', 
                    value=config.get('base_url', 'http://192.168.58.101:8123')
                ).classes('w-full q-mt-md')
                
                # Add info about refreshing models
                with ui.row().classes('w-full q-mt-sm items-center'):
                    ui.icon('lightbulb').classes('q-mr-sm text-amber-6')
                    ui.label('Click "Refresh Models" after changing API settings to load available models').classes('text-caption text-grey-7')

            # System Prompt Configuration Section
            with ui.column().classes('w-full q-mb-lg'):
                ui.label('🤖 System Prompt Configuration').classes('text-h6 q-mb-md')
                
                # System prompt textarea
                system_prompt_input = ui.textarea(
                    label='System Prompt',
                    value=config.get('system_prompt', 'You are a helpful assistant.'),
                    placeholder='Enter your system prompt here...',
                ).classes('w-full').style('min-height: 120px')
                
                # Add info about system prompt
                with ui.row().classes('w-full q-mt-sm items-center'):
                    ui.icon('info').classes('q-mr-sm text-blue-6')
                    ui.label('The system prompt defines the AI assistant\'s behavior and personality. It will be sent as the first message in every conversation.').classes('text-caption text-grey-7')

            # Model Selection Section
            with ui.column().classes('w-full q-mb-lg'):
                ui.label('🤖 Model Selection').classes('text-h6 q-mb-md')
                
                # Model selection - Dynamic loading
                model_select_container = ui.column().classes('w-full')
                model_select = None
                
                async def load_models():
                    nonlocal model_select
                    model_select_container.clear()
                    
                    # Default fallback models
                    default_models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3-5-sonnet', 'claude-3-opus']
                    # Get current config from user storage (updated)
                    current_config = get_current_config()
                    current_model = current_config.get('model', 'claude-3-5-sonnet')
                    
                    with model_select_container:
                        # Show loading state
                        loading_container = ui.row().classes('w-full items-center q-pa-md')
                        with loading_container:
                            ui.spinner('dots', size='sm').classes('q-mr-sm')
                            ui.label('Loading available models...')
                        
                        # Save current config to restore later
                        original_config = get_current_config()
                        
                        try:
                            # Temporarily update API client with current form settings for testing
                            temp_config = {
                                'api_key': api_key_input.value,
                                'base_url': base_url_input.value,
                                'model': current_model
                            }
                            app.storage.user['user-settings'] = temp_config
                            
                            # Try to get models from API with timeout
                            api_client = get_api_client()
                            api_client.update_settings()
                            
                            # Add timeout to prevent hanging
                            models_data = await asyncio.wait_for(
                                api_client.list_models(), 
                                timeout=10.0  # 10 second timeout
                            )
                            
                            # Extract model names/IDs
                            if models_data:
                                model_options = []
                                for model in models_data:
                                    # Handle different response formats
                                    if isinstance(model, dict):
                                        model_name = model.get('id') or model.get('name') or model.get('model')
                                        if model_name:
                                            model_options.append(model_name)
                                
                                if not model_options:
                                    model_options = default_models
                                    ui.notify('No models found in API response, using defaults', color='warning', position='top')
                                else:
                                    ui.notify(f'Loaded {len(model_options)} models from API', color='positive', position='top')
                            else:
                                model_options = default_models
                                ui.notify('Empty response from API, using default models', color='warning', position='top')
                                
                        except asyncio.TimeoutError:
                            print("Timeout loading models from API")
                            model_options = default_models
                            ui.notify('API request timed out (10s), using default models', color='warning', position='top')
                        except Exception as e:
                            print(f"Error loading models from API: {str(e)}")
                            model_options = default_models
                            ui.notify('Failed to load models from API, using defaults', color='warning', position='top')
                        finally:
                            # Restore original config (don't auto-save test settings)
                            app.storage.user['user-settings'] = original_config
                            api_client = get_api_client()
                            api_client.update_settings()
                        
                        # Always ensure we have model_options (even if API failed)
                        if 'model_options' not in locals():
                            model_options = default_models
                            ui.notify('Using default models due to API error', color='warning', position='top')
                        
                        # Clear loading state
                        loading_container.clear()
                        
                        # Create model select with loaded options
                        # Ensure current model is in options, if not add it
                        if current_model not in model_options:
                            model_options.insert(0, current_model)
                        
                        # Always create the model_select (never leave it as None)
                        model_select = ui.select(
                            label='Model', 
                            options=model_options, 
                            value=current_model
                        ).classes('w-full')
                        
                        # Add refresh button
                        with ui.row().classes('w-full items-center q-mt-md q-col-gutter-sm'):
                            ui.button('🔄 Refresh Models', on_click=load_models).props('size=sm color=secondary outline').classes('col-auto')
                            ui.label('Reload models using current API settings').classes('col text-caption text-grey-6')
                
                # Create initial model selector with defaults (no API call)
                def create_initial_model_select():
                    nonlocal model_select
                    model_select_container.clear()
                    
                    default_models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3-5-sonnet', 'claude-3-opus']
                    # Get current config from user storage (updated)
                    current_config = get_current_config()
                    current_model = current_config.get('model', 'claude-3-5-sonnet')
                    
                    # Ensure current model is in options
                    if current_model not in default_models:
                        default_models.insert(0, current_model)
                    
                    with model_select_container:
                        model_select = ui.select(
                            label='Model', 
                            options=default_models, 
                            value=current_model
                        ).classes('w-full')
                        
                        # Add info and refresh button
                        with ui.row().classes('w-full items-center q-mt-md q-col-gutter-sm'):
                            ui.button('🔄 Load Models from API', on_click=load_models).props('size=sm color=primary outline').classes('col-auto')
                            ui.label('Click to load available models from your API').classes('col text-caption text-grey-6')
                        
                        with ui.row().classes('w-full q-mt-sm items-center'):
                            ui.icon('info').classes('q-mr-sm text-blue-6')
                            ui.label('Using default models. Click "Load Models from API" to get models from your server.').classes('text-caption text-grey-7')
                
                # Create initial state
                create_initial_model_select()
            
            # Auto-refresh fields on page load to ensure they reflect current storage
            def auto_refresh_on_load():
                current_config = get_current_config()
                if current_config:  # Only if there's saved config
                    api_key_input.value = current_config.get('api_key', '')
                    base_url_input.value = current_config.get('base_url', 'http://192.168.58.101:8123')
                    system_prompt_input.value = current_config.get('system_prompt', 'You are a helpful assistant.')
                    # Force UI update
                    api_key_input.update()
                    base_url_input.update()
                    system_prompt_input.update()
            
            # Call auto-refresh
            auto_refresh_on_load()
            
            def save_config():
                # Check if model_select is available (should always be available now)
                if model_select is None:
                    ui.notify('Error: Model selector not initialized. Try refreshing models first.', color='warning', position='top')
                    return
                
                # Create new user config (independent from MCP config)
                new_user_config = {
                    'api_key': api_key_input.value,
                    'base_url': base_url_input.value,
                    'model': model_select.value,
                    'system_prompt': system_prompt_input.value
                }
                
                # Update user storage - automatically persistent
                app.storage.user['user-settings'] = new_user_config
                
                # Update API client with new settings
                try:
                    api_client = get_api_client()
                    api_client.update_settings()
                    ui.notify('Configuration saved and API client updated successfully!', color='positive', position='top')
                except Exception as e:
                    print(f"Error updating API client: {str(e)}")
                    ui.notify('Configuration saved, but API client update failed', color='warning', position='top')
            
            # Add a button to reset configuration to defaults
            def reset_to_factory():
                # Check if model_select is available (should always be available now)
                if model_select is None:
                    ui.notify('Error: Model selector not initialized. Try refreshing models first.', color='warning', position='top')
                    return
                    
                try:
                    initial_configs = load_initial_config_from_files()
                    initial_config = initial_configs.get('user-settings', {})
                    
                    print(f"Reset to factory - Initial config loaded: {initial_config}")
                    
                    # Update input fields
                    api_key_input.value = initial_config.get('api_key', '')
                    base_url_input.value = initial_config.get('base_url', 'http://192.168.58.101:8123')
                    model_select.value = initial_config.get('model', 'claude-3-5-sonnet')
                    system_prompt_input.value = initial_config.get('system_prompt', 'You are a helpful assistant.')
                    
                    # Update user storage with initial configuration
                    app.storage.user['user-settings'] = initial_config
                    
                    # Force UI update
                    api_key_input.update()
                    base_url_input.update()
                    model_select.update()
                    system_prompt_input.update()
                    
                    # Update API client with new settings
                    api_client = get_api_client()
                    api_client.update_settings()
                    
                    ui.notify('Configuration reset to factory settings and API client updated successfully!', color='positive', position='top')
                    
                except Exception as e:
                    print(f"Error during factory reset: {str(e)}")
                    ui.notify(f'Error resetting configuration: {str(e)}', color='negative', position='top')

            def confirm_reset():
                with ui.dialog() as dialog, ui.card().classes('q-pa-lg'):
                    with ui.column().classes('items-center text-center q-gutter-md'):
                        ui.icon('warning', size='lg').classes('text-orange-6')
                        ui.label('Reset to Factory Settings').classes('text-h6 text-weight-bold')
                        ui.label('This will overwrite your current configuration with the factory defaults.').classes('text-body2 text-grey-7')
                        
                        with ui.row().classes('q-gutter-md justify-center'):
                            ui.button('Cancel', on_click=dialog.close).props('color=secondary outline')
                            ui.button('🔄 Confirm Reset', on_click=lambda: [reset_to_factory(), dialog.close()]).props('color=negative')
                dialog.open()

            # Action buttons section
            with ui.column().classes('w-full q-mt-xl'):
                with ui.row().classes('w-full q-gutter-md justify-center flex-wrap'):
                    ui.button('💾 Save Configuration', on_click=save_config).props('color=primary size=lg').classes('col-12 col-sm-auto')
                    ui.button('🔄 Reset to Factory Settings', on_click=confirm_reset).props('color=secondary size=lg outline').classes('col-12 col-sm-auto')
