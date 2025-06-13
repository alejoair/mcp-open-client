from nicegui import ui
from mcp_open_client.api_client import APIClient
import asyncio
import re

# Variables globales
log_component = None
current_message_container = None

def parse_and_render_message(message: str, container) -> None:
    """
    Parse a message and render it with proper code block formatting.
    
    Detects code blocks marked with triple backticks (```) and renders them
    using ui.code component, while rendering regular text as ui.markdown.
    Only Python code blocks get an execute button.
    
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
            
            # Render code block with execute button ONLY for Python
            if code_content:
                with ui.row().classes('items-start'):
                    ui.code(code_content, language=language).classes('w-full my-2 nicegui-code')
                    # Only add execute button for Python code
                    if language == 'python':
                        ui.button('▶', on_click=lambda code=code_content: execute_python_code(code)).props('size=sm round color=green').classes('ml-2 mt-2')
            
            last_end = end
        
        # Render remaining text after last code block (if any)
        if last_end < len(message):
            text_after = message[last_end:].strip()
            if text_after:
                ui.markdown(text_after)

def execute_python_code(code: str):
    """Execute Python code using Pyodide and show output as new chat message"""
    global log_component, current_message_container
    
    if log_component:
        log_component.push('Executing Python code...')
    
    # Better escaping for JavaScript
    escaped_code = code.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    js_code = f"""
    if (window.pyodideReady && window.pyodide) {{
        try {{
            // Setup custom input function and capture stdout
            const setupCode = `
import sys
from io import StringIO
import js
import builtins

# Capture all output
old_stdout = sys.stdout
captured_output = StringIO()
sys.stdout = captured_output

def custom_input(prompt=""):
    # Get current output to show in prompt
    current_output = captured_output.getvalue()
    if current_output:
        display_prompt = current_output + prompt
    else:
        display_prompt = prompt
    
    result = js.prompt(display_prompt)
    
    if result is not None:
        # Print the input to our captured output
        print(result)
        return result
    else:
        return ""

# Replace built-in input with our custom function
builtins.input = custom_input
`;
            
            pyodide.runPython(setupCode);
            
            // Execute the user code
            const userCode = `{escaped_code}`;
            const result = pyodide.runPython(userCode);
            
            // Get all captured output
            const getOutputCode = `
final_output = captured_output.getvalue()
sys.stdout = old_stdout
final_output
`;
            const output = pyodide.runPython(getOutputCode);
            
            // Store result in window for Python to retrieve
            if (output && output.trim()) {{
                window.pythonResult = output;
            }} else if (result !== undefined && result !== null) {{
                window.pythonResult = 'Result: ' + String(result);
            }} else {{
                // Check if code defines functions but doesn't call them
                if (userCode.includes('def ') && !userCode.includes('()')) {{
                    window.pythonResult = 'Functions defined but not called';
                }} else {{
                    window.pythonResult = 'Code executed successfully (no output)';
                }}
            }}
            
        }} catch (error) {{
            // Restore stdout in case of error
            try {{
                pyodide.runPython('sys.stdout = old_stdout');
            }} catch (e) {{
                // Ignore cleanup errors
            }}
            window.pythonResult = 'Error: ' + error.message;
        }}
    }} else {{
        window.pythonResult = 'Error: Pyodide is still loading';
    }}
    """
    
    ui.run_javascript(js_code)
    
    # Check for result and show it in chat
    async def check_result():
        global log_component, current_message_container
        try:
            result = await ui.run_javascript("return window.pythonResult || null;", timeout=2.0)
            if result and current_message_container:
                # Add execution result as a new message in chat
                with current_message_container:
                    with ui.card().classes('mr-auto ml-4') as result_card:
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label('Output:').classes('font-bold mb-2')
                            ui.button('📤', on_click=lambda r=result: send_output_to_llm(r)).props('size=sm round color=blue').classes('ml-2')
                        # Render output without execute buttons and colors
                        if result.startswith('Error:'):
                            ui.label(result).classes('whitespace-pre-wrap')
                        else:
                            ui.code(result, language='text').classes('w-full my-2')
                
                # Log summary to logs
                if log_component:
                    if result.startswith('Error:'):
                        log_component.push(f'Execution failed: {result[:100]}...')
                    else:
                        log_component.push('Execution completed successfully')
                
                # Auto-scroll to bottom
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
                
                # Clear the result
                ui.run_javascript("window.pythonResult = null;")
        except:
            pass  # Ignore timeout or other errors
    
    ui.timer(0.5, check_result, once=True)

def send_output_to_llm(output_text: str):
    """Send the output text to the LLM as a user message"""
    global current_message_container
    
    if current_message_container:
        # Create the message to send
        message_to_send = f"Here's the output from my Python code execution:\n\n```\n{output_text}\n```"
        
        # Add user message to chat
        with current_message_container:
            with ui.card().classes('ml-auto mr-4 max-w-md') as user_card:
                ui.label('You:').classes('font-bold mb-2')
                parse_and_render_message(message_to_send, user_card)
        
        # Auto-scroll to bottom
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        
        # Send to API (simulate clicking the send functionality)
        async def send_to_api():
            global current_message_container
            try:
                # Get API client from globals if available
                api_client = APIClient()
                
                # Show spinner while waiting for response
                with current_message_container:
                    spinner = ui.spinner('dots', size='lg')
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
                
                response = await api_client.chat_completion([{"role": "user", "content": message_to_send}])
                bot_response = response['choices'][0]['message']['content']
                
                # Remove spinner and add bot response
                spinner.delete()
                with current_message_container:
                    with ui.card().classes('mr-auto ml-4') as bot_card:
                        ui.label('Bot:').classes('font-bold mb-2')
                        parse_and_render_message(bot_response, bot_card)
                
                # Auto-scroll to bottom again
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
                
            except Exception as e:
                # Remove spinner if error occurs
                if 'spinner' in locals():
                    spinner.delete()
                # Add error message to chat
                with current_message_container:
                    with ui.card().classes('mr-auto ml-4 max-w-md') as error_card:
                        ui.label('System:').classes('font-bold mb-2')
                        parse_and_render_message(f'Error: {str(e)}', error_card)
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        
        # Execute the API call
        ui.timer(0.1, send_to_api, once=True)

def show_content(container):
    """
    Creates a GPT-style chat interface in the provided container.
    
    Args:
        container: The container to render the chat interface in
    """
    global log_component, current_message_container
    
    # Clear and setup the container
    container.clear()
    container.classes('h-full w-full flex flex-col')
    
    # Add Pyodide HTML
    pyodide_html = """
    <script src="https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js"></script>
    <script>
        let pyodide;
        window.pyodideReady = false;
        window.pythonResult = null;
        
        async function initPyodide() {
            try {
                console.log("Loading Pyodide...");
                pyodide = await loadPyodide({
                    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/"
                });
                window.pyodide = pyodide;
                window.pyodideReady = true;
                console.log("Pyodide loaded successfully");
            } catch (error) {
                console.error("Error loading Pyodide:", error);
            }
        }
        
        initPyodide();
    </script>
    """
    
    with container:
        # Load Pyodide
        ui.add_body_html(pyodide_html)
        
        # Create an instance of APIClient
        api_client = APIClient()
        
        # Apply CSS for proper layout expansion and code styling
        ui.add_css('''
            a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}
            .nicegui-code {
                border-radius: 8px !important;
                margin: 8px 0 !important;
                font-size: 14px !important;
            }
            .q-card {
                border-radius: 12px !important;
            }
        ''')
        
        # Make the page content expand properly
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')
        
        # Main layout container
        with ui.column().classes('h-full w-full flex flex-col'):
            
            # TABS SECTION - Fixed at top
            with ui.tabs().classes('w-full shrink-0') as tabs:
                chat_tab = ui.tab('Chat')
                logs_tab = ui.tab('Logs')
            
            # CONTENT SECTION - Expandable middle area with fixed height
            with ui.tab_panels(tabs, value=chat_tab).classes('w-full mx-auto flex-grow items-stretch'):
                
                # Chat Panel - Message container with scroll
                with ui.tab_panel(chat_tab).classes('items-stretch h-full'):

                    with ui.scroll_area().classes('h-full w-full') as scroll_area:
                        message_container = ui.column().classes('w-full gap-2')
                        current_message_container = message_container  # Store reference globally
                        with message_container:
                            # Sample messages for demo
                            with ui.card().classes('') as demo_bot_card:
                                ui.label('Bot:').classes('font-bold mb-2')
                                parse_and_render_message('Hello! Try this Python code with input:\n```python\ndef saludar_usuario():\n    nombre = input("Por favor, ingresa tu nombre: ")\n    print(f"¡Hola, {nombre}! Bienvenido/a.")\n\n# Llamar a la función\nsaludar_usuario()\n```\n\nOr this Python code without input:\n```python\nprint("Numbers 1-5:")\nfor i in range(1, 6):\n    print(f"Number: {i}")\n```\n\nThis JavaScript code has no execute button:\n```javascript\nconsole.log("This is JavaScript");\n```', demo_bot_card)
                            with ui.card().classes('ml-auto mr-4') as demo_user_card:
                                ui.label('You:').classes('font-bold mb-2')
                                parse_and_render_message('I want to test Python code execution', demo_user_card)
                
                # Logs Panel with scroll
                with ui.tab_panel(logs_tab).classes('h-full'):
                    log_component = ui.log().classes('w-full h-full')
                    # Sample log entries
                    log_component.push('System initialized')
                    log_component.push('Chat session started')
                    log_component.push('Pyodide loading...')
                    log_component.push('Custom input() function enabled')

            # SEND MESSAGE SECTION - Fixed at bottom
            with ui.row().classes('w-full items-center mb-25 shrink-0'):
                text_input = ui.input(placeholder='Message...').props('rounded outlined input-class=mx-3').classes('flex-grow')
                send_button = ui.button('Send', icon='send', on_click=lambda: handle_send(text_input, message_container, api_client, scroll_area)).props('no-caps')
                
                # Enable sending with Enter key
                text_input.on('keydown.enter', lambda: handle_send(text_input, message_container, api_client, scroll_area))

async def handle_send(input_field, message_container, api_client, scroll_area):
    """Handle sending a message asynchronously"""
    if input_field.value and input_field.value.strip():
        message = input_field.value.strip()
        
        # Add user message
        with message_container:
            with ui.card().classes('ml-auto mr-4 max-w-md') as user_card:
                ui.label('You:').classes('font-bold mb-2')
                parse_and_render_message(message, user_card)
        
        # Clear input
        input_field.value = ''
        
        # Auto-scroll to bottom using JavaScript (like in the examples)
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        
        # Send message to API and get response
        try:
            # Show spinner while waiting for response
            with message_container:
                spinner = ui.spinner('dots', size='lg')
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
            
            response = await api_client.chat_completion([{"role": "user", "content": message}])
            bot_response = response['choices'][0]['message']['content']
            
            # Remove spinner and add bot response
            spinner.delete()
            with message_container:
                with ui.card().classes('mr-auto ml-4') as bot_card:
                    ui.label('Bot:').classes('font-bold mb-2')
                    parse_and_render_message(bot_response, bot_card)
            
            # Auto-scroll to bottom again
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
            
        except Exception as e:
            # Remove spinner if error occurs
            if 'spinner' in locals():
                spinner.delete()
            # Add error message to chat instead of using ui.notify
            with message_container:
                with ui.card().classes('mr-auto ml-4 max-w-md') as error_card:
                    ui.label('System:').classes('font-bold mb-2 text-red-600')
                    parse_and_render_message(f'Error: {str(e)}', error_card)
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
    else:
        # we'll just ignore
        pass