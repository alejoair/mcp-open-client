from nicegui import ui
from mcp_open_client.api_client import APIClient


# Variables globales para el ejecutor
log_component = None
current_message_container = None


def set_global_components(log_comp, message_container):
    """Set global components for the Python executor"""
    global log_component, current_message_container
    log_component = log_comp
    current_message_container = message_container


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
                from .message_parser import parse_and_render_message
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
                        from .message_parser import parse_and_render_message
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
                        from .message_parser import parse_and_render_message
                        parse_and_render_message(f'Error: {str(e)}', error_card)
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        
        # Execute the API call
        ui.timer(0.1, send_to_api, once=True)


def get_pyodide_html():
    """Get the HTML script for loading Pyodide"""
    return """
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