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
    container.clear()
    with container:
        # Header section with modern styling
        with ui.column().classes('configure-header w-full mb-6'):
            ui.label('⚙️ CONFIGURE').classes('configure-title text-h3 font-bold mb-2')
            ui.label('Configure your API settings and preferences.').classes('configure-subtitle text-subtitle1 text-grey-7')
        
        # Main configuration card
        with ui.card().classes('configure-card w-full max-w-2xl mx-auto p-6'):
            # Function to get current config (always fresh from storage)
            def get_current_config():
                return app.storage.user.get('user-settings', {})

            # Load current configuration
            config = get_current_config()

            # API Configuration Section
            with ui.column().classes('configure-section mb-6'):
                ui.label('🔑 API Configuration').classes('section-title text-h6 font-semibold mb-4')
                
                # API Key input with password toggle
                with ui.row().classes('w-full'):
                    api_key_input = ui.input(
                        label='API Key', 
                        value=config.get('api_key', ''),
                        password=True,
                        password_toggle_button=True
                    ).classes('configure-input flex-1')

                # Base URL input  
                base_url_input = ui.input(
                    label='Base URL', 
                    value=config.get('base_url', 'http://192.168.58.101:8123')
                ).classes('configure-input w-full mt-3')
                
                # Add info about refreshing models
                with ui.row().classes('info-tip mt-3'):
                    ui.icon('lightbulb').classes('text-amber-600 mr-2')
                    ui.label('Click "Refresh Models" after changing API settings to load available models').classes('tip-text text-caption text-grey-7')

            # System Prompt Configuration Section
            with ui.column().classes('configure-section mb-6'):
                ui.label('🤖 System Prompt Configuration').classes('section-title text-h6 font-semibold mb-4')
                
                # System prompt textarea
                system_prompt_input = ui.textarea(
                    label='System Prompt',
                    value=config.get('system_prompt', 'You are a helpful assistant.'),
                    placeholder='Enter your system prompt here...',
                ).classes('configure-input w-full').style('min-height: 120px')
                
                # Add info about system prompt
                with ui.row().classes('info-tip mt-3'):
                    ui.icon('info').classes('text-blue-600 mr-2')
                    ui.label('The system prompt defines the AI assistant\'s behavior and personality. It will be sent as the first message in every conversation.').classes('tip-text text-caption text-grey-7')

            # Model Selection Section
            with ui.column().classes('configure-section mb-6'):
                ui.label('🤖 Model Selection').classes('section-title text-h6 font-semibold mb-4')
                
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
                        loading_container = ui.row().classes('w-full items-center')
                        with loading_container:
                            ui.spinner('dots', size='sm')
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
                                    ui.notify('No models found in API response, using defaults', color='warning')
                                else:
                                    ui.notify(f'Loaded {len(model_options)} models from API', color='positive')
                            else:
                                model_options = default_models
                                ui.notify('Empty response from API, using default models', color='warning')
                                
                        except asyncio.TimeoutError:
                            print("Timeout loading models from API")
                            model_options = default_models
                            ui.notify('API request timed out (10s), using default models', color='warning')
                        except Exception as e:
                            print(f"Error loading models from API: {str(e)}")
                            model_options = default_models
                            ui.notify('Failed to load models from API, using defaults', color='warning')
                        finally:
                            # Restore original config (don't auto-save test settings)
                            app.storage.user['user-settings'] = original_config
                            api_client = get_api_client()
                            api_client.update_settings()
                        
                        # Always ensure we have model_options (even if API failed)
                        if 'model_options' not in locals():
                            model_options = default_models
                            ui.notify('Using default models due to API error', color='warning')
                        
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
                        ).classes('configure-input w-full')
                        
                        # Add refresh button
                        with ui.row().classes('w-full items-center mt-3'):
                            ui.button('🔄 Refresh Models', on_click=load_models).classes('model-refresh-btn').props('size=sm color=secondary outline')
                            ui.label('Reload models using current API settings').classes('text-caption text-grey-6 ml-2')
                
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
                        ).classes('configure-input w-full')
                        
                        # Add info and refresh button
                        with ui.row().classes('w-full items-center mt-3'):
                            ui.button('🔄 Load Models from API', on_click=load_models).classes('model-refresh-btn').props('size=sm color=primary outline')
                            ui.label('Click to load available models from your API').classes('text-caption text-grey-6 ml-2')
                        
                        with ui.row().classes('info-tip mt-2'):
                            ui.icon('info').classes('text-blue-600 mr-2')
                            ui.label('Using default models. Click "Load Models from API" to get models from your server.').classes('tip-text text-caption text-grey-7')
                
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
                    ui.notify('Error: Model selector not initialized. Try refreshing models first.', color='warning')
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
                    ui.notify('Configuration saved and API client updated successfully!', color='positive')
                except Exception as e:
                    print(f"Error updating API client: {str(e)}")
                    ui.notify('Configuration saved, but API client update failed', color='warning')
            
            # Add a button to reset configuration to defaults
            def reset_to_factory():
                # Check if model_select is available (should always be available now)
                if model_select is None:
                    ui.notify('Error: Model selector not initialized. Try refreshing models first.', color='warning')
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
                    
                    ui.notify('Configuration reset to factory settings and API client updated successfully!', color='positive')
                    
                except Exception as e:
                    print(f"Error during factory reset: {str(e)}")
                    ui.notify(f'Error resetting configuration: {str(e)}', color='negative')

            def confirm_reset():
                with ui.dialog() as dialog, ui.card().classes('configure-dialog'):
                    with ui.column().classes('items-center text-center'):
                        ui.icon('warning', size='lg').classes('text-orange-600 mb-2')
                        ui.label('Reset to Factory Settings').classes('text-h6 font-bold mb-2')
                        ui.label('This will overwrite your current configuration with the factory defaults.').classes('text-body2 text-grey-7 mb-4')
                        
                        with ui.row().classes('gap-3'):
                            ui.button('Cancel', on_click=dialog.close).classes('reset-cancel-btn').props('color=secondary outline')
                            ui.button('🔄 Confirm Reset', on_click=lambda: [reset_to_factory(), dialog.close()]).classes('reset-confirm-btn').props('color=negative')
                dialog.open()

            # Action buttons section
            with ui.column().classes('configure-actions mt-8'):
                with ui.row().classes('w-full gap-4 justify-center'):
                    ui.button('💾 Save Configuration', on_click=save_config).classes('save-btn').props('color=primary size=lg')
                    ui.button('🔄 Reset to Factory Settings', on_click=confirm_reset).classes('reset-btn').props('color=secondary size=lg outline')
