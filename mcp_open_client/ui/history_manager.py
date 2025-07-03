"""
Simple Rolling Window History Manager
"""

class HistoryManager:
    def __init__(self, max_messages=50):
        self._default_max_messages = max_messages
    
    @property
    def max_messages(self):
        """Get max_messages from storage on-demand"""
        try:
            from nicegui import app
            settings = app.storage.user.get('history-settings', {})
            return settings.get('max_messages', self._default_max_messages)
        except:
            return self._default_max_messages
    
    
    def update_max_messages(self, max_messages):
        """Update max messages setting and save to storage"""
        try:
            from nicegui import app
            if 'history-settings' not in app.storage.user:
                app.storage.user['history-settings'] = {}
            app.storage.user['history-settings']['max_messages'] = max_messages
            print(f"DEBUG: Updated max_messages to: {max_messages}")
        except Exception as e:
            print(f"DEBUG: Failed to save max_messages: {e}")
    
    def cleanup_conversation_if_needed(self, conversation_id: str) -> bool:
        """
        Simple rolling window: keep only the last max_messages messages.
        Tool call validation is handled by _final_tool_sequence_validation.
        """
        from .chat_handlers import get_conversation_storage
        conversations = get_conversation_storage()
        
        if conversation_id not in conversations:
            return False
        
        messages = conversations[conversation_id]['messages']
        original_count = len(messages)
        
        if original_count <= self.max_messages:
            return False
        
        # Simple rolling window: keep the last max_messages
        messages_to_remove = original_count - self.max_messages
        kept_messages = messages[messages_to_remove:]
        
        conversations[conversation_id]['messages'] = kept_messages
        
        # Save to storage
        from nicegui import app
        app.storage.user['conversations'] = conversations
        
        print(f"Rolling window: removed {messages_to_remove} messages, kept {len(kept_messages)} (target: {self.max_messages})")
        print(f"Conversation cleanup performed for {conversation_id}")
        return True
    

    def process_message_for_storage(self, message):
        """Process message for storage - simple passthrough"""
        return message
    
    def get_conversation_size(self, conversation_id: str):
        """Get conversation size info"""
        from .chat_handlers import get_conversation_storage
        conversations = get_conversation_storage()
        
        if conversation_id not in conversations:
            return {'total_tokens': 0, 'total_chars': 0, 'message_count': 0}
        
        messages = conversations[conversation_id]['messages']
        total_chars = sum(len(msg.get('content', '') or '') for msg in messages)
        
        return {
            'total_tokens': total_chars // 4,  # Rough token estimate
            'total_chars': total_chars,
            'message_count': len(messages)
        }
    
    @property
    def settings(self):
        """Simple settings dict"""
        return {
            'auto_cleanup': True,
            'max_tokens_per_message': 10000,
            'max_tokens_per_conversation': self.max_messages * 1000,  # Rough estimate
            'preserve_tool_calls': True,
            'compression_enabled': False,
            'truncate_mode': 'simple'
        }
    
    def get_settings(self):
        """Get settings dict"""
        return self.settings

# Global instance
history_manager = HistoryManager(max_messages=50)
