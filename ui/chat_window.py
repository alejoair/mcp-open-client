from nicegui import ui, app
from datetime import datetime
import asyncio

def show_content(container):
    """
    Creates and renders a chat window in the provided container.
    This follows the pattern used by other UI components in the application.
    
    Args:
        container: The container to render the chat window in
    """
    container.clear()
    with container:
        ui.label('CHAT').classes('text-h4')
        ui.label('Chat with MCP servers and AI assistants.')
        ui.separator()
        
        # Create the chat interface
        chat = ChatWindow()
        chat.render()

class ChatWindow:
    def __init__(self):
        """Initialize the chat window"""
        self.messages = []
        self.user_message = ""
        self.messages_container = None
        self.message_input = None
        
    def render(self):
        """Render the chat window UI"""
        # Main container with modern styling from CSS
        with ui.card().classes('w-full chat-container'):
            # Header with controls
            with ui.row().classes('chat-header'):
                ui.label('CHAT').classes('chat-title')
                ui.button('Clear', icon='delete_sweep').props('flat round color=white').on('click', self.clear_chat)
            
            # Messages area with scrolling
            with ui.card().classes('chat-messages-area'):
                self.messages_container = ui.column().classes('chat-messages-container')
                self.update_messages()
            
            # Input area fixed at bottom
            with ui.row().classes('chat-input-area'):
                self.message_input = ui.input(placeholder='Type your message here...').classes('chat-input')
                self.message_input.on('keydown.enter', self.send_message)
                
                ui.button('', icon='send', on_click=self.send_message).classes('chat-send-button')
                
                self.message_input.on('input', self.update_user_message)
    
    def update_user_message(self, e):
        """Update the user message as it's typed"""
        self.user_message = e.value
    
    async def get_response_from_server(self, message):
        """
        Get a response from the selected MCP server.
        This is a placeholder for future integration with the MCP client.
        """
        # In a real implementation, this would use the MCP client to get a response
        # For now, we'll just return a simulated response
        await asyncio.sleep(1)  # Simulate network delay
        
        return "This is a simulated response from the MCP server."
    
    def send_message(self, e=None):
        """Send a message and clear the input field"""
        if not self.user_message.strip():
            return
            
        # Add user message to the list
        self.add_message(self.user_message, 'user')
        
        # Store the message for processing
        message_to_process = self.user_message
        
        # Clear input field
        self.message_input.value = ''
        self.user_message = ''
        
        # Create a background task to get the response
        async def get_and_add_response():
            response = await self.get_response_from_server(message_to_process)
            self.add_message(response, 'assistant')
        
        # Run the task asynchronously
        asyncio.create_task(get_and_add_response())
    
    def add_message(self, text, sender):
        """Add a message to the chat"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.messages.append({
            'text': text,
            'sender': sender,
            'timestamp': timestamp
        })
        self.update_messages()
        
        # Scroll to bottom - find the parent card that has overflow-auto
        if self.messages_container:
            parent_id = self.messages_container.parent.id
            ui.run_javascript(f'document.getElementById("{parent_id}").scrollTop = document.getElementById("{parent_id}").scrollHeight')
    
    def update_messages(self):
        """Update the messages display"""
        if not self.messages_container:
            return
            
        self.messages_container.clear()
        
        if not self.messages:
            # Show a welcome message if no messages
            with ui.column().classes('chat-welcome-container'):
                ui.icon('chat_bubble_outline', size='3rem').style('color: var(--primary-light); opacity: 0.7')
                ui.label('Start a conversation by typing a message below').classes('chat-welcome-text')
            return
        
        for msg in self.messages:
            sender = msg['sender']
            text = msg['text']
            timestamp = msg['timestamp']
            
            if sender == 'user':
                # User message (right-aligned)
                with ui.row().classes('w-full justify-end chat-message-spacing'):
                    with ui.card().classes('chat-user-message'):
                        ui.label(text)
                        ui.label(timestamp).classes('chat-timestamp')
            else:
                # Assistant message (left-aligned)
                with ui.row().classes('w-full justify-start chat-message-spacing'):
                    with ui.card().classes('chat-assistant-message'):
                        ui.label(text)
                        ui.label(timestamp).classes('chat-timestamp')
    
    def clear_chat(self):
        """Clear all messages from the chat"""
        self.messages = []
        self.update_messages()

