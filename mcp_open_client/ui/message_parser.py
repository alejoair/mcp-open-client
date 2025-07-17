from nicegui import ui
import re
import json

def is_structured_response(content: str) -> bool:
    """Check if content contains structured response metadata."""
    return "<!-- RESPONSE_METADATA:" in content

def extract_response_metadata(content: str):
    """Extract metadata from structured response."""
    if not is_structured_response(content):
        return None
    
    pattern = r'<!-- RESPONSE_METADATA: ({.*?}) -->'
    match = re.search(pattern, content)
    
    if match:
        try:
            metadata_str = match.group(1)
            # Replace single quotes with double quotes for valid JSON
            metadata_str = metadata_str.replace("'", '"')
            # Replace Python boolean values with JSON boolean values
            metadata_str = metadata_str.replace('True', 'true').replace('False', 'false')
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return None
    
    return None

def clean_response_content(content: str) -> str:
    """Remove metadata comments from response content."""
    pattern = r'\n\n<!-- RESPONSE_METADATA: .*? -->'
    cleaned = re.sub(pattern, '', content)
    return cleaned.strip()

def apply_structured_response_style(container, metadata: dict):
    """Apply enhanced styling to container based on metadata with uniform design."""
    if not metadata:
        return
    
    background_color = metadata.get('background_color')
    border_color = metadata.get('border_color')
    text_color = metadata.get('text_color')
    
    # Base styling - always applied for uniformity
    base_style = (
        'padding: 16px; '
        'border-radius: 12px; '
        'margin: 8px 0; '
        'box-shadow: 0 2px 8px rgba(0,0,0,0.1); '
        'transition: all 0.2s ease; '
    )
    
    # Add colors if available
    color_style = ''
    if background_color:
        color_style += f'background-color: {background_color}; '
    if border_color:
        color_style += f'border-left: 5px solid {border_color}; '
    if text_color:
        color_style += f'color: {text_color}; '
    
    # Combine all styles
    full_style = base_style + color_style
    container.style(full_style)


def parse_and_render_message(message: str, container) -> None:
    """
    Parse a message and render it with proper code block formatting.
    
    Detects code blocks marked with triple backticks (```) and renders them
    using ui.code component, while rendering regular text as ui.markdown.
    
    Args:
        message: The message content to parse
        container: The UI container to add elements to
    """
    if not message or not message.strip():
        return
    
    # Check if this is a structured response with metadata
    metadata = extract_response_metadata(message)
    if metadata:
        # Clean the message content by removing metadata comments
        message = clean_response_content(message)
        
        # Apply structured response styling to the container
        apply_structured_response_style(container, metadata)
        
        # Add enhanced icon if present
        icon = metadata.get('icon')
        icon_bg = metadata.get('icon_bg')
        if icon:
            with container:
                # Create icon container with background
                with ui.row().classes('items-center mb-3'):
                    icon_style = (
                        'display: inline-flex; '
                        'align-items: center; '
                        'justify-content: center; '
                        'width: 32px; '
                        'height: 32px; '
                        'border-radius: 50%; '
                        'font-size: 16px; '
                        'margin-right: 8px; '
                    )
                    if icon_bg:
                        icon_style += f'background-color: {icon_bg}; '
                    
                    ui.label(icon).style(icon_style)
    
    # Pattern to match code blocks with optional language specification
    # Matches: ```language\ncode\n``` or ```\ncode\n```
    code_block_pattern = r'```(\w+)?\s*\n?(.*?)\n?\s*```'
    
    # Find all code blocks and their positions
    matches = list(re.finditer(code_block_pattern, message, re.DOTALL))
    
    if not matches:
        # No code blocks found, render as regular markdown
        with container:
            ui.markdown(message)
        return
    
    # Process message with code blocks
    last_end = 0
    
    with container:
        for match in matches:
            start, end = match.span()
            language = match.group(1) or 'python'  # Default to python if no language specified
            code_content = match.group(2).strip()
            
            # Render text before code block (if any)
            if start > last_end:
                text_before = message[last_end:start].strip()
                if text_before:
                    ui.markdown(text_before)
            # Render code block
            if code_content:
                ui.code(code_content, language=language).classes('w-full my-2 overflow-x-auto')
            
            
            last_end = end
        
        # Render remaining text after last code block (if any)
        if last_end < len(message):
            text_after = message[last_end:].strip()
            if text_after:
                ui.markdown(text_after)