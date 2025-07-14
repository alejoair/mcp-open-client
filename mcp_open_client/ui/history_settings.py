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
            
            ui.label('Máximo de mensajes por conversación').classes('text-sm text-gray-600 mb-2')
            
            with ui.row().classes('w-full items-center gap-4 mb-4'):
                max_messages = ui.number(
                    value=history_manager.max_messages,
                    min=10,
                    max=200,
                    step=10
                ).classes('flex-1')
                
                ui.label(f'Actual: {history_manager.max_messages} mensajes').classes('text-sm text-gray-600')
            
            # Update button
            def update_settings():
                history_manager.update_max_messages(int(max_messages.value))
                ui.notify(f'Configuración actualizada: Máximo {history_manager.max_messages} mensajes', color='positive')
            
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
                        ui.label('Caracteres').classes('text-sm text-gray-600')
                        ui.label(f"{conv_stats['total_chars']:,}").classes('text-2xl font-bold text-secondary')
                    
                    with ui.column().classes('flex-1'):
                        ui.label('Tokens estimados').classes('text-sm text-gray-600')
                        ui.label(f"{conv_stats['total_tokens']:,}").classes('text-2xl font-bold text-accent')
                
                # Progress bar
                progress = min(100, (conv_stats['message_count'] / history_manager.max_messages) * 100)
                ui.label(f'Uso del límite: {progress:.1f}%').classes('text-sm text-gray-600 mb-2')
                ui.linear_progress(progress / 100).classes('w-full mb-4')
                
                # Cleanup button
                def cleanup_now():
                    cleaned = history_manager.cleanup_conversation_if_needed(conv_id)
                    if cleaned:
                        ui.notify('Conversación limpiada', color='positive')
                        ui.navigate.reload()
                    else:
                        ui.notify('No es necesaria limpieza', color='info')
                
                if progress > 80:
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
