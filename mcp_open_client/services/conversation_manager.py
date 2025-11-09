"""
Conversation manager for handling tool call conversations with storage
This manages the format and storage of conversations that include tool calls
"""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ConversationToolCall:
    """Single tool call with execution result"""
    id: str
    function_name: str
    arguments: str
    result: Optional[str] = None
    status: str = "pending"  # "pending", "executed", "error"
    execution_time: Optional[float] = None
    timestamp: Optional[str] = None

@dataclass
class ConversationMessage:
    """Message in conversation with tool call support"""
    role: str  # "user", "assistant", "system", "tool"
    content: Optional[str] = None
    reasoning: Optional[str] = None
    tool_calls: Optional[List[ConversationToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool result messages
    name: Optional[str] = None  # Tool name for tool messages
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class Conversation:
    """Complete conversation with metadata"""
    id: str
    title: str
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str
    provider: str
    model: str
    total_tokens: Optional[int] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

class ConversationManager:
    """Manages conversation storage and retrieval with tool call support"""

    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def create_conversation(
        self,
        title: str,
        provider: str,
        model: str
    ) -> Conversation:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            title=title,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            provider=provider,
            model=model
        )
        return conversation

    def add_user_message(
        self,
        conversation: Conversation,
        content: str
    ) -> ConversationMessage:
        """Add user message to conversation"""
        message = ConversationMessage(
            role="user",
            content=content
        )
        conversation.messages.append(message)
        conversation.updated_at = datetime.now().isoformat()
        return message

    def add_assistant_message(
        self,
        conversation: Conversation,
        content: Optional[str] = None,
        reasoning: Optional[str] = None,
        tool_calls: Optional[List[ConversationToolCall]] = None
    ) -> ConversationMessage:
        """Add assistant message with optional tool calls"""
        message = ConversationMessage(
            role="assistant",
            content=content,
            reasoning=reasoning,
            tool_calls=tool_calls
        )
        conversation.messages.append(message)
        conversation.updated_at = datetime.now().isoformat()
        return message

    def add_tool_result_message(
        self,
        conversation: Conversation,
        tool_call_id: str,
        tool_name: str,
        result: str,
        status: str = "success"
    ) -> ConversationMessage:
        """Add tool result message"""
        message = ConversationMessage(
            role="tool",
            content=result,
            tool_call_id=tool_call_id,
            name=tool_name
        )
        conversation.messages.append(message)
        conversation.updated_at = datetime.now().isoformat()
        return message

    def save_conversation(self, conversation: Conversation) -> str:
        """Save conversation to storage"""
        file_path = self.storage_dir / f"{conversation.id}.json"

        # Convert to dict for JSON serialization
        conversation_dict = asdict(conversation)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_dict, f, indent=2, ensure_ascii=False)

        return str(file_path)

    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from storage"""
        file_path = self.storage_dir / f"{conversation_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert tool calls back to objects
            messages = []
            for msg_data in data.get('messages', []):
                tool_calls = None
                if msg_data.get('tool_calls'):
                    tool_calls = [
                        ConversationToolCall(**tc) for tc in msg_data['tool_calls']
                    ]

                message = ConversationMessage(
                    role=msg_data['role'],
                    content=msg_data.get('content'),
                    reasoning=msg_data.get('reasoning'),
                    tool_calls=tool_calls,
                    tool_call_id=msg_data.get('tool_call_id'),
                    name=msg_data.get('name'),
                    timestamp=msg_data.get('timestamp')
                )
                messages.append(message)

            conversation = Conversation(
                id=data['id'],
                title=data['title'],
                messages=messages,
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                provider=data['provider'],
                model=data['model'],
                total_tokens=data.get('total_tokens')
            )

            return conversation

        except Exception as e:
            print(f"Error loading conversation {conversation_id}: {e}")
            return None

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations with metadata"""
        conversations = []

        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Return metadata only
                conversations.append({
                    'id': data['id'],
                    'title': data['title'],
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'provider': data['provider'],
                    'model': data['model'],
                    'message_count': len(data.get('messages', [])),
                    'has_tool_calls': any(
                        msg.get('tool_calls') for msg in data.get('messages', [])
                    )
                })
            except Exception as e:
                print(f"Error reading conversation file {file_path}: {e}")
                continue

        # Sort by updated_at desc
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from storage"""
        file_path = self.storage_dir / f"{conversation_id}.json"

        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                print(f"Error deleting conversation {conversation_id}: {e}")
                return False
        return False

# Global conversation manager instance
conversation_manager = ConversationManager()