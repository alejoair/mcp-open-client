"""
History Manager - Sistema de gestión y limitación del historial de conversaciones
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class HistoryManager:
    """
    Gestiona el historial de conversaciones con límites de caracteres y optimizaciones
    """
    
    def __init__(self, 
                 max_chars_per_message: int = 5000,
                 max_chars_per_conversation: int = 50000,
                 max_total_chars: int = 500000):
        """
        Inicializa el gestor de historial
        
        Args:
            max_chars_per_message: Máximo de caracteres por mensaje individual
            max_chars_per_conversation: Máximo de caracteres por conversación
            max_total_chars: Máximo de caracteres totales en todo el historial
        """
        self.max_chars_per_message = max_chars_per_message
        self.max_chars_per_conversation = max_chars_per_conversation
        self.max_total_chars = max_total_chars
        
        # Configuración por defecto
        self.settings = {
            'truncate_mode': 'smart',  # 'smart', 'tail', 'head'
            'preserve_tool_calls': True,
            'compression_enabled': True,
            'auto_cleanup': True
        }
    
    def truncate_message_content(self, content: str, preserve_format: bool = True) -> Tuple[str, bool]:
        """
        Trunca el contenido de un mensaje si excede el límite
        
        Args:
            content: Contenido del mensaje
            preserve_format: Si preservar formato markdown/código
            
        Returns:
            Tuple de (contenido_truncado, fue_truncado)
        """
        if len(content) <= self.max_chars_per_message:
            return content, False
        
        truncated = False
        
        if self.settings['truncate_mode'] == 'smart':
            # Truncado inteligente preservando estructura
            truncated_content = self._smart_truncate(content, self.max_chars_per_message)
        elif self.settings['truncate_mode'] == 'tail':
            # Mantener el final
            truncated_content = "..." + content[-(self.max_chars_per_message - 3):]
        else:  # 'head'
            # Mantener el inicio
            truncated_content = content[:self.max_chars_per_message - 3] + "..."
        
        return truncated_content, True
    
    def _smart_truncate(self, content: str, max_chars: int) -> str:
        """
        Truncado inteligente que preserva estructura de código y markdown
        """
        if len(content) <= max_chars:
            return content
        
        # Reservar espacio para indicador de truncado
        available_chars = max_chars - 20
        
        # Intentar cortar en párrafos
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            truncated = ""
            for paragraph in paragraphs:
                if len(truncated + paragraph) <= available_chars:
                    truncated += paragraph + '\n\n'
                else:
                    break
            if truncated:
                return truncated.rstrip() + "\n\n[... truncated]"
        
        # Intentar cortar en líneas
        lines = content.split('\n')
        if len(lines) > 1:
            truncated = ""
            for line in lines:
                if len(truncated + line) <= available_chars:
                    truncated += line + '\n'
                else:
                    break
            if truncated:
                return truncated.rstrip() + "\n[... truncated]"
        
        # Corte simple si no hay estructura clara
        return content[:available_chars] + "\n[... truncated]"
    
    def process_message_for_storage(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje antes de guardarlo, aplicando límites y optimizaciones
        
        Args:
            message: Mensaje original
            
        Returns:
            Mensaje procesado para almacenamiento
        """
        processed_message = message.copy()
        
        # Procesar contenido principal
        if 'content' in processed_message and processed_message['content']:
            original_content = processed_message['content']
            truncated_content, was_truncated = self.truncate_message_content(original_content)
            
            processed_message['content'] = truncated_content
            
            if was_truncated:
                processed_message['_truncated'] = True
                processed_message['_original_length'] = len(original_content)
        
        # Procesar tool calls si están presentes
        if 'tool_calls' in processed_message and self.settings['preserve_tool_calls']:
            processed_tool_calls = []
            for tool_call in processed_message['tool_calls']:
                processed_tool_call = tool_call.copy()
                
                # Truncar argumentos si son muy largos
                if 'function' in processed_tool_call and 'arguments' in processed_tool_call['function']:
                    args_str = processed_tool_call['function']['arguments']
                    if len(args_str) > 1000:  # Límite para argumentos
                        try:
                            # Intentar parsear y comprimir JSON
                            args_obj = json.loads(args_str)
                            compressed_args = json.dumps(args_obj, separators=(',', ':'))
                            if len(compressed_args) <= 1000:
                                processed_tool_call['function']['arguments'] = compressed_args
                            else:
                                processed_tool_call['function']['arguments'] = compressed_args[:997] + "..."
                        except:
                            processed_tool_call['function']['arguments'] = args_str[:997] + "..."
                
                processed_tool_calls.append(processed_tool_call)
            
            processed_message['tool_calls'] = processed_tool_calls
        
        return processed_message
    
    def get_conversation_size(self, conversation_id: str, conversations: Dict[str, Any] = None) -> Dict[str, int]:
        """
        Calcula el tamaño de una conversación
        
        Returns:
            Dict con 'total_chars', 'message_count', 'avg_message_size'
        """
        if conversations is None:
            from .chat_handlers import get_conversation_storage
            conversations = get_conversation_storage()
        
        if conversation_id not in conversations:
            return {'total_chars': 0, 'message_count': 0, 'avg_message_size': 0}
        
        messages = conversations[conversation_id].get('messages', [])
        total_chars = 0
        
        for message in messages:
            content = message.get('content', '')
            total_chars += len(content)
            
            # Contar tool calls también
            if 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    if 'function' in tool_call and 'arguments' in tool_call['function']:
                        total_chars += len(tool_call['function']['arguments'])
        
        message_count = len(messages)
        avg_size = total_chars // message_count if message_count > 0 else 0
        
        return {
            'total_chars': total_chars,
            'message_count': message_count,
            'avg_message_size': avg_size
        }
    
    def get_total_history_size(self) -> Dict[str, int]:
        """
        Calcula el tamaño total del historial
        """
        from .chat_handlers import get_conversation_storage
        
        conversations = get_conversation_storage()
        total_chars = 0
        total_messages = 0
        conversation_count = len(conversations)
        
        for conv_id in conversations:
            conv_stats = self.get_conversation_size(conv_id)
            total_chars += conv_stats['total_chars']
            total_messages += conv_stats['message_count']
        
        return {
            'total_chars': total_chars,
            'total_messages': total_messages,
            'conversation_count': conversation_count,
            'avg_chars_per_conversation': total_chars // conversation_count if conversation_count > 0 else 0
        }
    
    def cleanup_conversation_if_needed(self, conversation_id: str) -> bool:
        """
        Limpia una conversación si excede los límites
        
        Returns:
            True si se realizó limpieza
        """
        stats = self.get_conversation_size(conversation_id)
        
        if stats['total_chars'] <= self.max_chars_per_conversation:
            return False
        
        from .chat_handlers import get_conversation_storage
        conversations = get_conversation_storage()
        
        if conversation_id not in conversations:
            return False
        
        messages = conversations[conversation_id]['messages']
        
        # Estrategia: mantener mensajes más recientes
        chars_to_remove = stats['total_chars'] - self.max_chars_per_conversation
        chars_removed = 0
        messages_to_keep = []
        
        # Empezar desde el final y ir hacia atrás
        for message in reversed(messages):
            message_size = len(message.get('content', ''))
            if chars_removed < chars_to_remove:
                chars_removed += message_size
            else:
                messages_to_keep.insert(0, message)
        
        if len(messages_to_keep) < len(messages):
            conversations[conversation_id]['messages'] = messages_to_keep
            conversations[conversation_id]['_cleaned_at'] = datetime.now().isoformat()
            # Update storage through chat_handlers
            from nicegui import app
            app.storage.user['conversations'] = conversations
            return True
        
        return False
    
    def cleanup_history_if_needed(self) -> Dict[str, Any]:
        """
        Limpia todo el historial si excede los límites globales
        
        Returns:
            Dict con estadísticas de limpieza
        """
        stats = self.get_total_history_size()
        
        if stats['total_chars'] <= self.max_total_chars:
            return {'cleaned': False, 'stats': stats}
        
        from .chat_handlers import get_conversation_storage
        conversations = get_conversation_storage()
        
        # Ordenar conversaciones por fecha de actualización (más antigas primero)
        sorted_conversations = sorted(
            conversations.items(),
            key=lambda x: x[1].get('updated_at', '0')
        )
        
        chars_to_remove = stats['total_chars'] - self.max_total_chars
        chars_removed = 0
        conversations_removed = 0
        
        for conv_id, conv_data in sorted_conversations:
            if chars_removed >= chars_to_remove:
                break
            
            conv_stats = self.get_conversation_size(conv_id)
            chars_removed += conv_stats['total_chars']
            del conversations[conv_id]
            conversations_removed += 1
        
        if conversations_removed > 0:
            from nicegui import app
            app.storage.user['conversations'] = conversations
        
        new_stats = self.get_total_history_size()
        
        return {
            'cleaned': True,
            'conversations_removed': conversations_removed,
            'chars_removed': chars_removed,
            'old_stats': stats,
            'new_stats': new_stats
        }
    
    def get_settings(self) -> Dict[str, Any]:
        """Obtiene la configuración actual"""
        return {
            'max_chars_per_message': self.max_chars_per_message,
            'max_chars_per_conversation': self.max_chars_per_conversation,
            'max_total_chars': self.max_total_chars,
            **self.settings
        }
    
    def update_settings(self, **kwargs) -> None:
        """Actualiza la configuración"""
        for key, value in kwargs.items():
            if key in ['max_chars_per_message', 'max_chars_per_conversation', 'max_total_chars']:
                setattr(self, key, value)
            elif key in self.settings:
                self.settings[key] = value


# Instancia global
history_manager = HistoryManager()
