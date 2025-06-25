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
                 max_tokens_per_message: int = 10000,       # ~40000 chars
                 max_tokens_per_conversation: int = 1000000):  # ~4M chars (1M tokens)
        """
        Inicializa el gestor de historial
        
        Args:
            max_tokens_per_message: Máximo de tokens por mensaje individual
            max_tokens_per_conversation: Máximo de tokens por conversación
        """
        self.max_tokens_per_message = max_tokens_per_message
        self.max_tokens_per_conversation = max_tokens_per_conversation
        
        # Mantener compatibilidad con valores de caracteres
        self.max_chars_per_message = max_tokens_per_message * 4  # Estimación conservadora
        self.max_chars_per_conversation = max_tokens_per_conversation * 4
        
        # Configuración por defecto
        self.settings = {
            'truncate_mode': 'smart',  # 'smart', 'tail', 'head'
            'preserve_tool_calls': True,
            'compression_enabled': True,
            'auto_cleanup': True
        }
        
        # Ensure backward compatibility
        self._ensure_token_attributes()
    
    def _ensure_token_attributes(self):
        """Ensure token attributes exist for backward compatibility"""
        if not hasattr(self, 'max_tokens_per_message'):
            # Default to 2500 tokens (~10000 chars) if no previous value exists
            self.max_tokens_per_message = getattr(self, 'max_tokens_per_message', 2500)
        if not hasattr(self, 'max_tokens_per_conversation'):
            # Default to 12500 tokens (~50000 chars) if no previous value exists
            self.max_tokens_per_conversation = getattr(self, 'max_tokens_per_conversation', 12500)
        
        # Ensure char attributes are synchronized with token attributes
        if not hasattr(self, 'max_chars_per_message'):
            self.max_chars_per_message = self.max_tokens_per_message * 4
        if not hasattr(self, 'max_chars_per_conversation'):
            self.max_chars_per_conversation = self.max_tokens_per_conversation * 4
    
    def estimate_tokens(self, text: str) -> int:
        """Estima tokens de forma inteligente basado en el tipo de contenido"""
        self._ensure_token_attributes()  # Ensure backward compatibility
        if not text:
            return 0
        
        # Ajustes por tipo de contenido
        if text.startswith('{') or text.startswith('['):  # JSON
            multiplier = 3.0
        elif '```' in text:  # Código
            multiplier = 3.2
        elif text.count(' ') / len(text) > 0.15:  # Texto normal
            multiplier = 4.2
        else:  # Texto denso
            multiplier = 3.8
        
        return int(len(text) / multiplier)
    
    def truncate_message_content(self, content: str, preserve_format: bool = True) -> Tuple[str, bool]:
        """Trunca el contenido basado en límite de tokens"""
        estimated_tokens = self.estimate_tokens(content)
        max_tokens = self.max_tokens_per_message
        
        if estimated_tokens <= max_tokens:
            return content, False
        
        # Calcular caracteres aproximados para el límite de tokens
        target_chars = max_tokens * 4  # Estimación conservadora
        
        truncated = False
        
        if self.settings['truncate_mode'] == 'smart':
            # Truncado inteligente preservando estructura
            truncated_content = self._smart_truncate(content, target_chars)
        elif self.settings['truncate_mode'] == 'tail':
            # Mantener el final
            truncated_content = "..." + content[-(target_chars - 3):]
        else:  # 'head'
            # Mantener el inicio
            truncated_content = content[:target_chars - 3] + "..."
        
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
    
    def _safe_truncate_json_arguments(self, args_str: str, max_length: int = 1000) -> str:
        """
        Safely truncate JSON arguments without breaking JSON structure
        
        Args:
            args_str: JSON string to truncate
            max_length: Maximum allowed length
            
        Returns:
            Valid JSON string that fits within max_length
        """
        if len(args_str) <= max_length:
            return args_str
        
        try:
            # Parse the JSON to ensure it's valid
            args_obj = json.loads(args_str)
            
            # Try compression first
            compressed = json.dumps(args_obj, separators=(',', ':'))
            if len(compressed) <= max_length:
                return compressed
            
            # If still too long, intelligently reduce content
            return self._intelligently_reduce_json(args_obj, max_length)
            
        except json.JSONDecodeError:
            # If it's not valid JSON, create a safe JSON wrapper
            safe_length = max_length - 50  # Reserve space for JSON structure
            truncated_content = args_str[:safe_length].replace('"', '\\"')  # Escape quotes
            return json.dumps({
                "original_content": truncated_content,
                "_error": "INVALID_JSON_TRUNCATED",
                "_original_length": len(args_str)
            })
    
    def _intelligently_reduce_json(self, obj, max_length: int) -> str:
        """
        Intelligently reduce JSON object size while maintaining structure
        """
        if isinstance(obj, dict):
            reduced_obj = {}
            for key, value in obj.items():
                # Always include small values
                if isinstance(value, (int, float, bool)) or (isinstance(value, str) and len(value) < 50):
                    reduced_obj[key] = value
                elif isinstance(value, str):
                    # Truncate long strings but keep them as valid strings
                    if len(value) > 100:
                        reduced_obj[key] = value[:97] + "..."
                    else:
                        reduced_obj[key] = value
                elif isinstance(value, (list, dict)):
                    # For complex objects, convert to string representation
                    str_repr = json.dumps(value, separators=(',', ':'))
                    if len(str_repr) > 50:
                        reduced_obj[key] = str_repr[:47] + "..."
                    else:
                        reduced_obj[key] = value
                else:
                    reduced_obj[key] = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            
            # Check if result fits
            result = json.dumps(reduced_obj, separators=(',', ':'))
            if len(result) <= max_length:
                return result
            
            # If still too long, keep only the most important keys
            essential_keys = list(reduced_obj.keys())[:3]  # Keep first 3 keys
            essential_obj = {k: reduced_obj[k] for k in essential_keys if k in reduced_obj}
            if len(reduced_obj) > len(essential_obj):
                essential_obj["_truncated"] = f"... and {len(reduced_obj) - len(essential_obj)} more fields"
            
            return json.dumps(essential_obj, separators=(',', ':'))
        
        elif isinstance(obj, list):
            if len(obj) <= 3:
                return json.dumps(obj, separators=(',', ':'))
            else:
                # Keep first 2 and indicate truncation
                reduced_list = obj[:2] + [f"... {len(obj) - 2} more items ..."]
                return json.dumps(reduced_list, separators=(',', ':'))
        
        else:
            # For primitive types, convert to string and truncate if needed
            str_value = json.dumps(obj)
            if len(str_value) <= max_length:
                return str_value
            else:
                return json.dumps(str(obj)[:max_length-10] + "...")
    
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
        
        # Procesar tool calls si están presentes con validación mejorada
        if 'tool_calls' in processed_message and self.settings['preserve_tool_calls']:
            processed_tool_calls = []
            for tool_call in processed_message['tool_calls']:
                # Validar estructura del tool call
                if (isinstance(tool_call, dict) and
                    'id' in tool_call and
                    'function' in tool_call and
                    isinstance(tool_call['function'], dict) and
                    'name' in tool_call['function']):
                    
                    processed_tool_call = tool_call.copy()
                    
                    # Truncar argumentos si son muy largos usando método seguro
                    if 'arguments' in processed_tool_call['function']:
                        args_str = processed_tool_call['function']['arguments']
                        if len(args_str) > 1000:  # Límite para argumentos
                            processed_tool_call['function']['arguments'] = self._safe_truncate_json_arguments(args_str, 1000)
                    
                    processed_tool_calls.append(processed_tool_call)
                else:
                    print(f"Warning: Removing invalid tool call during storage: {tool_call}")
            
            if processed_tool_calls:
                processed_message['tool_calls'] = processed_tool_calls
            else:
                # Remover tool_calls si ninguno es válido
                processed_message.pop('tool_calls', None)
        
        # Validar mensajes de tool result
        if processed_message.get('role') == 'tool':
            if not processed_message.get('tool_call_id'):
                print(f"Warning: Tool result message missing tool_call_id")
                return None  # Señal para omitir este mensaje
            if not processed_message.get('content'):
                processed_message['content'] = '[Empty tool result]'
        
        return processed_message
    
    def get_conversation_size(self, conversation_id: str, conversations: Dict[str, Any] = None) -> Dict[str, int]:
        """
        Calcula el tamaño de una conversación en tokens y caracteres
        
        Returns:
            Dict con 'total_tokens', 'total_chars', 'message_count', 'avg_token_size', 'avg_char_size'
        """
        if conversations is None:
            from .chat_handlers import get_conversation_storage
            conversations = get_conversation_storage()
        
        if conversation_id not in conversations:
            return {'total_tokens': 0, 'total_chars': 0, 'message_count': 0, 'avg_token_size': 0, 'avg_char_size': 0}
        
        messages = conversations[conversation_id].get('messages', [])
        total_chars = 0
        total_tokens = 0
        
        for message in messages:
            content = message.get('content', '')
            if content is not None:
                chars = len(content)
                tokens = self.estimate_tokens(content)
                total_chars += chars
                total_tokens += tokens
            else:
                # Log or handle the case where content is None
                print(f"Warning: Message content is None in conversation {conversation_id}")
            
            # Contar tool calls también
            if 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    if 'function' in tool_call and 'arguments' in tool_call['function']:
                        args_content = tool_call['function']['arguments']
                        total_chars += len(args_content)
                        total_tokens += self.estimate_tokens(args_content)
        
        message_count = len(messages)
        
        return {
            'total_tokens': total_tokens,
            'total_chars': total_chars,  # Mantener para referencia
            'message_count': message_count,
            'avg_token_size': total_tokens // message_count if message_count > 0 else 0,
            'avg_char_size': total_chars // message_count if message_count > 0 else 0
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
        """Limpia una conversación si excede los límites de tokens"""
        stats = self.get_conversation_size(conversation_id)
        
        if stats['total_tokens'] <= self.max_tokens_per_conversation:
            return False
        
        from .chat_handlers import get_conversation_storage
        conversations = get_conversation_storage()
        
        if conversation_id not in conversations:
            return False
        
        messages = conversations[conversation_id]['messages']
        
        # Estrategia: mantener mensajes más recientes
        tokens_to_remove = stats['total_tokens'] - self.max_tokens_per_conversation
        tokens_removed = 0
        messages_to_keep = []
        
        # Empezar desde el final y ir hacia atrás
        for message in reversed(messages):
            content = message.get('content', '') or ''
            message_tokens = self.estimate_tokens(content)
            if tokens_removed < tokens_to_remove:
                tokens_removed += message_tokens
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
    
    # Global history cleanup removed - only per-conversation limits apply
    
    def get_settings(self) -> Dict[str, Any]:
        """Obtiene la configuración actual"""
        self._ensure_token_attributes()  # Ensure backward compatibility
        return {
            'max_tokens_per_message': self.max_tokens_per_message,
            'max_tokens_per_conversation': self.max_tokens_per_conversation,
            'max_chars_per_message': self.max_chars_per_message,
            'max_chars_per_conversation': self.max_chars_per_conversation,
            **self.settings
        }
    
    def update_settings(self, **kwargs) -> None:
        """Actualiza la configuración"""
        for key, value in kwargs.items():
            if key in ['max_tokens_per_message', 'max_tokens_per_conversation']:
                setattr(self, key, value)
                # Update corresponding char limits
                if key == 'max_tokens_per_message':
                    self.max_chars_per_message = value * 4
                elif key == 'max_tokens_per_conversation':
                    self.max_chars_per_conversation = value * 4
            elif key in ['max_chars_per_message', 'max_chars_per_conversation']:
                setattr(self, key, value)
            elif key in self.settings:
                self.settings[key] = value


# Instancia global
history_manager = HistoryManager()
