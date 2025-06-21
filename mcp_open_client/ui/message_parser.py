from nicegui import ui
import re


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