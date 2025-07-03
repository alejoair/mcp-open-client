"""
Simple History Settings UI - Rolling Window Configuration
"""

from nicegui import ui
from .history_manager import history_manager

def create_history_settings_ui(container):
    """
    Simple UI for configuring rolling window history
    """
    with container:
        ui.label('History Settings').classes('text-2xl font-bold mb-6')
        
        # Rolling window configuration
        with ui.card().classes('w-full mb-6'):
            ui.label('Rolling Window Configuration').classes('text-lg font-semibold mb-3')
            ui.label('Configure the maximum number of messages to keep in conversation history. When this limit is exceeded, older messages are automatically removed while preserving tool call sequences.').classes('text-sm text-gray-600 mb-4')
            
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1'):
                    ui.label('Max Messages per Conversation')
                    max_messages = ui.number(
                        value=history_manager.max_messages,
                        min=10,
                        max=200,
                        step=10
                    ).classes('w-full')
                    ui.label(f"Current: {history_manager.max_messages} messages").classes('text-sm text-gray-600')
            
            # Update button
            def update_settings():
                history_manager.update_max_messages(int(max_messages.value))
                ui.notify(f'Settings updated: Max {history_manager.max_messages} messages', type='positive')
            
            ui.button('Update Settings', on_click=update_settings).classes('bg-blue-500 text-white mt-4')
        
        # Current status
        with ui.card().classes('w-full mb-6'):
            ui.label('Current Status').classes('text-lg font-semibold mb-3')
            
            from .chat_handlers import get_current_conversation_id
            conv_id = get_current_conversation_id()
            
            if conv_id:
                conv_stats = history_manager.get_conversation_size(conv_id)
                ui.label(f"Current conversation: {conv_stats['message_count']} messages")
                ui.label(f"Characters: {conv_stats['total_chars']:,}")
                
                # Progress bar
                progress = min(100, (conv_stats['message_count'] / history_manager.max_messages) * 100)
                ui.linear_progress(progress / 100).classes('w-full mt-2')
                ui.label(f"{progress:.1f}% of message limit").classes('text-sm text-gray-600')
                
                # Cleanup button
                def cleanup_now():
                    cleaned = history_manager.cleanup_conversation_if_needed(conv_id)
                    if cleaned:
                        ui.notify('Conversation cleaned up', type='positive')
                        # Refresh the stats display
                        ui.navigate.reload()
                    else:
                        ui.notify('No cleanup needed', type='info')
                
                ui.button('Cleanup Now', on_click=cleanup_now).classes('bg-orange-500 text-white mt-2')
            else:
                ui.label('No active conversation')

def create_conversation_details_ui(container):
    """
    Simple conversation details UI
    """
    with container:
        ui.label('Conversation Details').classes('text-xl font-bold mb-4')
        
        from .chat_handlers import get_current_conversation_id
        conv_id = get_current_conversation_id()
        
        if conv_id:
            stats = history_manager.get_conversation_size(conv_id)
            
            with ui.card().classes('w-full'):
                ui.label(f"Messages: {stats['message_count']}")
                ui.label(f"Characters: {stats['total_chars']:,}")
                ui.label(f"Estimated tokens: {stats['total_tokens']:,}")
                
                progress = min(100, (stats['message_count'] / history_manager.max_messages) * 100)
                ui.linear_progress(progress / 100).classes('w-full mt-2')
                ui.label(f"{progress:.1f}% of message limit").classes('text-sm text-gray-600')
        else:
            ui.label('No active conversation')
