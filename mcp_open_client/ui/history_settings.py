"""
History Settings UI - Interfaz de configuración del gestor de historial
"""

from nicegui import ui
from .history_manager import history_manager


def create_history_settings_ui(container):
    """
    Crea la interfaz de configuración del history manager
    """
    with container:
        ui.label('History Manager Settings').classes('text-2xl font-bold mb-6')
        
        # Obtener configuración actual
        settings = history_manager.get_settings()
        
        # Información sobre límites
        with ui.card().classes('w-full mb-6'):
            ui.label('History Limits Information').classes('text-lg font-semibold mb-3')
            ui.label('Configure token limits for conversation management. Tokens provide better LLM compatibility than character counts.').classes('text-sm text-gray-600')
        
        # Configuración de límites
        with ui.card().classes('w-full mb-6'):
            ui.label('Token Limits').classes('text-lg font-semibold mb-3')
            
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1'):
                    ui.label('Max Tokens per Message')
                    max_tokens_per_message = ui.number(
                        value=settings['max_tokens_per_message'],
                        min=100,
                        max=5000,
                        step=50
                    ).classes('w-full')
                    ui.label(f"Current: {settings['max_tokens_per_message']:,} tokens (~{settings['max_tokens_per_message']*4:,} chars)").classes('text-sm text-gray-600')
                
                with ui.column().classes('flex-1'):
                    ui.label('Max Tokens per Conversation')
                    max_tokens_per_conversation = ui.number(
                        value=settings['max_tokens_per_conversation'],
                        min=1000,
                        max=50000,
                        step=500
                    ).classes('w-full')
                    ui.label(f"Current: {settings['max_tokens_per_conversation']:,} tokens (~{settings['max_tokens_per_conversation']*4:,} chars)").classes('text-sm text-gray-600')
        
        # Configuración de comportamiento
        with ui.card().classes('w-full mb-6'):
            ui.label('Behavior Settings').classes('text-lg font-semibold mb-3')
            
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1'):
                    ui.label('Truncation Mode')
                    truncate_mode = ui.select(
                        options=['smart', 'tail', 'head'],
                        value=settings['truncate_mode']
                    ).classes('w-full')
                    ui.label('Smart: preserves structure, Tail: keeps end, Head: keeps beginning').classes('text-sm text-gray-600')
                
                with ui.column().classes('flex-1'):
                    preserve_tool_calls = ui.checkbox(
                        'Preserve Tool Calls',
                        value=settings['preserve_tool_calls']
                    )
                    
                    auto_cleanup = ui.checkbox(
                        'Auto Cleanup',
                        value=settings['auto_cleanup']
                    )
                    
                    compression_enabled = ui.checkbox(
                        'Enable Compression',
                        value=settings['compression_enabled']
                    )
        
        # Acciones de limpieza manual
        with ui.card().classes('w-full mb-6'):
            ui.label('Manual Cleanup Actions').classes('text-lg font-semibold mb-3')
            
            with ui.row().classes('w-full gap-4'):
                async def cleanup_current_conversation():
                    from .chat_handlers import get_current_conversation_id
                    conv_id = get_current_conversation_id()
                    if conv_id:
                        cleaned = history_manager.cleanup_conversation_if_needed(conv_id)
                        if cleaned:
                            ui.notify('Current conversation cleaned up', type='positive')
                            refresh_stats()
                        else:
                            ui.notify('Current conversation is within limits', type='info')
                    else:
                        ui.notify('No active conversation', type='warning')
                
                ui.button(
                    'Cleanup Current Conversation',
                    icon='cleaning_services',
                    on_click=cleanup_current_conversation
                ).classes('').props('color=orange')
        
        # Botones de acción
        with ui.row().classes('w-full justify-end gap-4 mt-6'):
            def save_settings():
                try:
                    history_manager.update_settings(
                        max_tokens_per_message=int(max_tokens_per_message.value),
                        max_tokens_per_conversation=int(max_tokens_per_conversation.value),
                        truncate_mode=truncate_mode.value,
                        preserve_tool_calls=preserve_tool_calls.value,
                        auto_cleanup=auto_cleanup.value,
                        compression_enabled=compression_enabled.value
                    )
                    ui.notify('Settings saved successfully!', type='positive')
                    refresh_stats()
                except Exception as e:
                    ui.notify(f'Error saving settings: {str(e)}', type='negative')
            
            def reset_to_defaults():
                max_tokens_per_message.value = 1200
                max_tokens_per_conversation.value = 12000
                truncate_mode.value = 'smart'
                preserve_tool_calls.value = True
                auto_cleanup.value = True
                compression_enabled.value = True
                ui.notify('Settings reset to defaults', type='info')
            
            def refresh_stats():
                # Stats refresh removed - no longer tracking global totals
                pass
                # Aquí podrías actualizar los elementos de la UI si necesario
                pass
            
            ui.button('Reset to Defaults', icon='restore', on_click=reset_to_defaults).props('flat')
            ui.button('Save Settings', icon='save', on_click=save_settings).props('color=primary')


def create_conversation_details_ui(container, conversation_id: str):
    """
    Crea una interfaz detallada para una conversación específica
    """
    with container:
        ui.label(f'Conversation Details: {conversation_id[:8]}...').classes('text-xl font-bold mb-4')
        
        stats = history_manager.get_conversation_size(conversation_id)
        
        with ui.grid(columns=4).classes('w-full gap-4 mb-4'):
            with ui.card().classes('p-4 text-center'):
                ui.label(f"{stats['total_tokens']:,}").classes('text-xl font-bold text-blue-600')
                ui.label('Total Tokens').classes('text-sm text-gray-600')
            
            with ui.card().classes('p-4 text-center'):
                ui.label(f"{stats['total_chars']:,}").classes('text-xl font-bold text-gray-600')
                ui.label('Total Characters').classes('text-sm text-gray-600')
            
            with ui.card().classes('p-4 text-center'):
                ui.label(f"{stats['message_count']:,}").classes('text-xl font-bold text-green-600')
                ui.label('Messages').classes('text-sm text-gray-600')
            
            with ui.card().classes('p-4 text-center'):
                ui.label(f"{stats['avg_token_size']:,}").classes('text-xl font-bold text-purple-600')
                ui.label('Avg. Token Size').classes('text-sm text-gray-600')
        
        # Progreso hacia los límites
        with ui.card().classes('w-full p-4'):
            ui.label('Limits Progress').classes('text-lg font-semibold mb-3')
            
            settings = history_manager.get_settings()
            
            # Progreso de tokens por conversación
            conv_progress = min(100, (stats['total_tokens'] / settings['max_tokens_per_conversation']) * 100)
            ui.label(f"Conversation Size: {conv_progress:.1f}% of token limit")
            ui.linear_progress(value=conv_progress/100).classes('mb-2')
            
            # Note: Removed total progress - only per-conversation limits apply
            # Global history tracking removed - only per-conversation limits apply
