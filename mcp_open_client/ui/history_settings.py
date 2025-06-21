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
        
        # Estadísticas actuales
        with ui.card().classes('w-full mb-6'):
            ui.label('Current Statistics').classes('text-lg font-semibold mb-3')
            
            stats = history_manager.get_total_history_size()
            
            with ui.grid(columns=4).classes('w-full gap-4'):
                with ui.card().classes('p-4 text-center'):
                    ui.label(f"{stats['total_chars']:,}").classes('text-2xl font-bold text-blue-600')
                    ui.label('Total Characters').classes('text-sm text-gray-600')
                
                with ui.card().classes('p-4 text-center'):
                    ui.label(f"{stats['total_messages']:,}").classes('text-2xl font-bold text-green-600')
                    ui.label('Total Messages').classes('text-sm text-gray-600')
                
                with ui.card().classes('p-4 text-center'):
                    ui.label(f"{stats['conversation_count']:,}").classes('text-2xl font-bold text-purple-600')
                    ui.label('Conversations').classes('text-sm text-gray-600')
                
                with ui.card().classes('p-4 text-center'):
                    ui.label(f"{stats['avg_chars_per_conversation']:,}").classes('text-2xl font-bold text-orange-600')
                    ui.label('Avg. Chars/Conv').classes('text-sm text-gray-600')
        
        # Configuración de límites
        with ui.card().classes('w-full mb-6'):
            ui.label('Character Limits').classes('text-lg font-semibold mb-3')
            
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1'):
                    ui.label('Max Characters per Message')
                    max_chars_per_message = ui.number(
                        value=settings['max_chars_per_message'],
                        min=500,
                        max=50000,
                        step=500
                    ).classes('w-full')
                    ui.label(f"Current: {settings['max_chars_per_message']:,} chars").classes('text-sm text-gray-600')
                
                with ui.column().classes('flex-1'):
                    ui.label('Max Characters per Conversation')
                    max_chars_per_conversation = ui.number(
                        value=settings['max_chars_per_conversation'],
                        min=5000,
                        max=500000,
                        step=5000
                    ).classes('w-full')
                    ui.label(f"Current: {settings['max_chars_per_conversation']:,} chars").classes('text-sm text-gray-600')
                
                with ui.column().classes('flex-1'):
                    ui.label('Max Total Characters')
                    max_total_chars = ui.number(
                        value=settings['max_total_chars'],
                        min=50000,
                        max=5000000,
                        step=50000
                    ).classes('w-full')
                    ui.label(f"Current: {settings['max_total_chars']:,} chars").classes('text-sm text-gray-600')
        
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
                
                async def cleanup_all_history():
                    result = history_manager.cleanup_history_if_needed()
                    if result['cleaned']:\n                        ui.notify(f\"Cleaned up {result['conversations_removed']} conversations\", type='positive')\n                        refresh_stats()\n                    else:\n                        ui.notify('History is within limits', type='info')\n                \n                ui.button(\n                    'Cleanup Current Conversation',\n                    icon='cleaning_services',\n                    on_click=cleanup_current_conversation\n                ).classes('').props('color=orange')\n                \n                ui.button(\n                    'Cleanup All History',\n                    icon='delete_sweep',\n                    on_click=cleanup_all_history\n                ).classes('').props('color=red')\n        \n        # Botones de acción\n        with ui.row().classes('w-full justify-end gap-4 mt-6'):\n            def save_settings():\n                try:\n                    history_manager.update_settings(\n                        max_chars_per_message=int(max_chars_per_message.value),\n                        max_chars_per_conversation=int(max_chars_per_conversation.value),\n                        max_total_chars=int(max_total_chars.value),\n                        truncate_mode=truncate_mode.value,\n                        preserve_tool_calls=preserve_tool_calls.value,\n                        auto_cleanup=auto_cleanup.value,\n                        compression_enabled=compression_enabled.value\n                    )\n                    ui.notify('Settings saved successfully!', type='positive')\n                    refresh_stats()\n                except Exception as e:\n                    ui.notify(f'Error saving settings: {str(e)}', type='negative')\n            \n            def reset_to_defaults():\n                max_chars_per_message.value = 5000\n                max_chars_per_conversation.value = 50000\n                max_total_chars.value = 500000\n                truncate_mode.value = 'smart'\n                preserve_tool_calls.value = True\n                auto_cleanup.value = True\n                compression_enabled.value = True\n                ui.notify('Settings reset to defaults', type='info')\n            \n            def refresh_stats():\n                # Refrescar estadísticas\n                new_stats = history_manager.get_total_history_size()\n                # Aquí podrías actualizar los elementos de la UI si necesario\n                pass\n            \n            ui.button('Reset to Defaults', icon='restore', on_click=reset_to_defaults).props('flat')\n            ui.button('Save Settings', icon='save', on_click=save_settings).props('color=primary')\n\n\ndef create_conversation_details_ui(container, conversation_id: str):\n    \"\"\"\n    Crea una interfaz detallada para una conversación específica\n    \"\"\"\n    with container:\n        ui.label(f'Conversation Details: {conversation_id[:8]}...').classes('text-xl font-bold mb-4')\n        \n        stats = history_manager.get_conversation_size(conversation_id)\n        \n        with ui.grid(columns=3).classes('w-full gap-4 mb-4'):\n            with ui.card().classes('p-4 text-center'):\n                ui.label(f\"{stats['total_chars']:,}\").classes('text-xl font-bold text-blue-600')\n                ui.label('Total Characters').classes('text-sm text-gray-600')\n            \n            with ui.card().classes('p-4 text-center'):\n                ui.label(f\"{stats['message_count']:,}\").classes('text-xl font-bold text-green-600')\n                ui.label('Messages').classes('text-sm text-gray-600')\n            \n            with ui.card().classes('p-4 text-center'):\n                ui.label(f\"{stats['avg_message_size']:,}\").classes('text-xl font-bold text-purple-600')\n                ui.label('Avg. Message Size').classes('text-sm text-gray-600')\n        \n        # Progreso hacia los límites\n        with ui.card().classes('w-full p-4'):\n            ui.label('Limits Progress').classes('text-lg font-semibold mb-3')\n            \n            settings = history_manager.get_settings()\n            \n            # Progreso de caracteres por conversación\n            conv_progress = min(100, (stats['total_chars'] / settings['max_chars_per_conversation']) * 100)\n            ui.label(f\"Conversation Size: {conv_progress:.1f}% of limit\")\n            ui.linear_progress(value=conv_progress/100).classes('mb-2')\n            \n            # Progreso total\n            total_stats = history_manager.get_total_history_size()\n            total_progress = min(100, (total_stats['total_chars'] / settings['max_total_chars']) * 100)\n            ui.label(f\"Total History Size: {total_progress:.1f}% of limit\")\n            ui.linear_progress(value=total_progress/100)\n