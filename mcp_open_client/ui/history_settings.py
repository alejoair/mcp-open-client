"""
Simple History Settings UI - Rolling Window Configuration
"""

from nicegui import ui
from .history_manager import history_manager

def create_history_settings_ui(container):
    """
    UI for configuring rolling window history with consistent styling
    """
    container.clear()
    container.classes('q-pa-md')
    
    with container:
        ui.label('Configuración de Historial').classes('text-2xl font-bold mb-6')

        
        # Overview card
        with ui.card().classes('w-full mb-6'):
            ui.label('Gestión de Historial de Conversaciones').classes('text-lg font-semibold mb-3')
            ui.label('Configura el límite de mensajes para optimizar el rendimiento. Cuando se supera el límite, los mensajes más antiguos se eliminan automáticamente preservando las secuencias de herramientas.').classes('text-sm text-gray-600 mb-4')
        
        # Configuration card
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('tune').classes('mr-2 text-primary')
                    ui.label('Configuración de Límites').classes('text-lg font-semibold')
            
            # Max messages configuration
            ui.label('Máximo de mensajes por conversación').classes('text-sm text-gray-600 mb-2')
            
            with ui.row().classes('w-full items-center gap-4 mb-4'):
                max_messages = ui.number(
                    value=history_manager.max_messages,
                    min=10,
                    max=200,
                    step=10
                ).classes('flex-1')
                
                ui.label(f'Actual: {history_manager.max_messages} mensajes').classes('text-sm text-gray-600')
                
            # Max tokens configuration
            ui.separator().classes('q-my-md')
            ui.label('Máximo de tokens por conversación').classes('text-sm text-gray-600 mb-2')
            
            with ui.row().classes('w-full items-center gap-4 mb-4'):
                settings = history_manager.settings
                max_tokens = ui.number(
                    value=settings.get('max_tokens_per_conversation', 50000),
                    min=10000,
                    max=200000,
                    step=10000
                ).classes('flex-1')
                
                ui.label(f'Actual: {settings.get("max_tokens_per_conversation", 50000):,} tokens').classes('text-sm text-gray-600')
            
            # Update button
            def update_settings():
                history_manager.update_max_messages(int(max_messages.value) if hasattr(max_messages, 'value') else max_messages)
                history_manager.update_setting('max_tokens_per_conversation', int(max_tokens.value) if hasattr(max_tokens, 'value') else max_tokens)
                
                # Get updated settings
                updated_settings = history_manager.settings
                
                ui.notify(
                    f'Configuración actualizada:\n'
                    f'- Máximo {updated_settings.get("max_messages")} mensajes\n'
                    f'- Máximo {updated_settings.get("max_tokens_per_conversation"):,} tokens',
                    color='positive'
                )
            
            ui.button('Actualizar Configuración', icon='save', on_click=update_settings).props('color=primary')
        
        # Current status card
        with ui.card().classes('w-full mb-6'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                with ui.row().classes('items-center'):
                    ui.icon('analytics').classes('mr-2 text-info')
                    ui.label('Estado de la Conversación Actual').classes('text-lg font-semibold')
            
            from .chat_handlers import get_current_conversation_id
            conv_id = get_current_conversation_id()
            
            if conv_id:
                conv_stats = history_manager.get_conversation_size(conv_id)
                
                with ui.row().classes('w-full gap-8 mb-4'):
                    with ui.column().classes('flex-1'):
                        ui.label('Mensajes').classes('text-sm text-gray-600')
                        ui.label(f"{conv_stats['message_count']}").classes('text-2xl font-bold text-primary')
                    
                    with ui.column().classes('flex-1'):
                        ui.label('Tokens').classes('text-sm text-gray-600')
                        ui.label(f"{conv_stats['total_tokens']:,}").classes('text-2xl font-bold text-accent')
                
                # Message progress bar
                msg_progress = min(100, (conv_stats['message_count'] / history_manager.max_messages) * 100)
                ui.label(f'Uso del límite de mensajes: {msg_progress:.1f}%').classes('text-sm text-gray-600 mb-2')
                ui.linear_progress(msg_progress / 100).classes('w-full mb-4')
                
                # Token progress bar
                settings = history_manager.settings
                max_tokens = settings.get('max_tokens_per_conversation', 50000)
                token_progress = min(100, (conv_stats['total_tokens'] / max_tokens) * 100)
                
                # Color changes based on percentage
                progress_color = 'primary'
                if token_progress > 90:
                    progress_color = 'negative'
                elif token_progress > 70:
                    progress_color = 'warning'
                    
                ui.label(f'Uso del límite de tokens: {token_progress:.1f}% ({conv_stats["total_tokens"]:,}/{max_tokens:,})').classes('text-sm text-gray-600 mb-2')
                ui.linear_progress(token_progress / 100).props(f'color={progress_color}').classes('w-full mb-4')
                
                # Cleanup button
                def cleanup_now():
                    cleaned = history_manager.cleanup_conversation_if_needed(conv_id)
                    if cleaned:
                        ui.notify('Conversación limpiada', color='positive')
                        ui.navigate.reload()
                    else:
                        ui.notify('No es necesaria limpieza', color='info')
                
                if msg_progress > 80:
                    ui.button('Limpiar Ahora', icon='cleaning_services', on_click=cleanup_now).props('color=warning')
                else:
                    ui.button('Limpiar Ahora', icon='cleaning_services', on_click=cleanup_now).props('color=secondary flat')
            else:
                ui.label('No hay conversación activa').classes('text-sm text-gray-600 text-center p-8')
                ui.label('Inicia una conversación en el chat para ver las estadísticas').classes('text-sm text-gray-600 text-center')

def create_conversation_details_ui(container):
    """
    Conversation details UI (deprecated - functionality moved to main UI)
    """
    # This function is kept for compatibility but the functionality
    # has been integrated into the main create_history_settings_ui
    pass
