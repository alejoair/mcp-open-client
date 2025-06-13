# Plan Detallado: Consola Python Persistente con Pyodide - ACTUALIZADO

## 1. ANÁLISIS DEL ESTADO ACTUAL

### Componentes Existentes Identificados:
- **`PythonExecutor`** (`mcp_open_client/ui/python_executor.py`):
  - ✅ Manejo básico de Pyodide
  - ✅ Interceptación de `input()` con diálogos modales
  - ✅ Captura de output con StringIO
  - ✅ Ejecución de código con manejo de errores
  - ❌ **NO persistente** - cada ejecución es independiente
  - ❌ No hay historial de comandos
  - ❌ No hay autocompletado

- **`ChatInterface`** (`mcp_open_client/ui/chat_interface.py`):
  - ✅ Sistema de pestañas (Chat, Logs)
  - ✅ Componente `ui.log()` en pestaña Logs
  - ✅ Integración con NiceGUI
  - ✅ Sistema de scroll y contenedores

- **Infraestructura NiceGUI**:
  - ✅ `ui.log()` para output en tiempo real
  - ✅ `ui.input()` para entrada de comandos
  - ✅ Sistema de eventos de teclado
  - ✅ Manejo de CSS y estilos

### Limitaciones Actuales Identificadas:
1. **Contexto no persistente**: Variables se pierden entre ejecuciones
2. **Input modal**: Bloquea la interfaz con diálogos
3. **No hay consola interactiva**: Solo ejecución de bloques de código
4. **Falta historial**: No se puede navegar comandos anteriores
5. **No hay autocompletado**: Falta introspección de Python

## 2. ARQUITECTURA PROPUESTA - ACTUALIZADA

### 2.1 Modificaciones a Componentes Existentes

#### A. Refactorización de `PythonExecutor` → `PyodideConsoleManager`
- **Mantener**: Lógica de inicialización de Pyodide
- **Agregar**: Contexto global persistente
- **Mejorar**: Manejo de input() sin modales
- **Nuevo**: Sistema de historial y autocompletado

#### B. Extensión de `ChatInterface`
- **Mantener**: Estructura de pestañas existente
- **Modificar**: Pestaña Logs para incluir consola interactiva
- **Agregar**: Layout específico para consola Python

### 2.2 Nuevos Componentes

#### A. `PersistentPythonConsole` (Nuevo)
```python
class PersistentPythonConsole:
    def __init__(self, log_component):
        self.log_component = log_component
        self.pyodide_manager = PyodideConsoleManager()
        self.command_history = CommandHistory()
        self.input_handler = ConsoleInputHandler()
        self.globals_dict = {}  # Contexto persistente
        self.locals_dict = {}
```

#### B. `ConsoleInputHandler` (Nuevo)
```python
class ConsoleInputHandler:
    def __init__(self):
        self.current_input = ""
        self.history_index = 0
        self.multiline_buffer = []
        self.in_multiline_mode = False
        self.autocompleter = AutoCompleter()
```

#### C. `CommandHistory` (Nuevo)
```python
class CommandHistory:
    def __init__(self, max_size=1000):
        self.commands = []
        self.max_size = max_size
        self.current_index = 0
```

## 3. IMPLEMENTACIÓN DETALLADA POR FASES

### 3.1 FASE 1: Infraestructura Base (Semana 1)

#### A. Refactorizar PythonExecutor
**Archivo**: `mcp_open_client/ui/pyodide_console_manager.py`

```python
class PyodideConsoleManager:
    def __init__(self):
        self.pyodide = None
        self.globals_dict = {'__builtins__': __builtins__}
        self.locals_dict = {}
        self.output_buffer = StringIO()
        self.input_queue = asyncio.Queue()
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar Pyodide con contexto persistente"""
        # Reutilizar lógica existente de python_executor.py
        # Agregar setup de contexto persistente
        
    async def execute_persistent(self, code: str) -> ExecutionResult:
        """Ejecutar código manteniendo contexto entre ejecuciones"""
        # Usar self.globals_dict y self.locals_dict
        # Mantener variables, imports, funciones definidas
```

#### B. Crear Estructura de Archivos
```
mcp_open_client/ui/console/
├── __init__.py
├── persistent_console.py          # Consola principal
├── pyodide_console_manager.py     # Gestión de Pyodide (refactorizado)
├── console_input_handler.py       # Manejo de entrada
├── command_history.py             # Historial de comandos
├── autocomplete.py                # Autocompletado
└── console_ui.py                  # Componentes UI específicos
```

### 3.2 FASE 2: UI de Consola Interactiva (Semana 2)

#### A. Modificar ChatInterface para Consola
**Archivo**: `mcp_open_client/ui/chat_interface.py`

```python
# En la pestaña Logs, reemplazar ui.log() simple con:
with ui.tab_panel(logs_tab).classes('h-full'):
    # Área de output (readonly)
    console_output = ui.log().classes('w-full flex-grow font-mono')
    
    # Área de input interactiva
    with ui.row().classes('w-full items-center p-2'):
        prompt_label = ui.label('>>> ').classes('text-green-600 font-mono')
        console_input = ui.input(
            placeholder='Enter Python command...'
        ).classes('flex-grow font-mono').props('outlined dense')
        
    # Crear instancia de consola persistente
    python_console = PersistentPythonConsole(console_output, console_input)
```

#### B. Implementar Manejo de Eventos de Teclado
```python
class ConsoleInputHandler:
    def setup_keyboard_events(self, input_element):
        # Enter: Ejecutar comando
        input_element.on('keydown.enter', self.handle_enter)
        # Shift+Enter: Nueva línea
        input_element.on('keydown.shift.enter', self.handle_multiline)
        # Up/Down: Navegar historial
        input_element.on('keydown.up', self.history_previous)
        input_element.on('keydown.down', self.history_next)
        # Tab: Autocompletado
        input_element.on('keydown.tab', self.handle_autocomplete)
        # Ctrl+C: Interrumpir
        input_element.on('keydown.ctrl.c', self.interrupt_execution)
        # Ctrl+L: Limpiar consola
        input_element.on('keydown.ctrl.l', self.clear_console)
```

### 3.3 FASE 3: Contexto Persistente y Input() No Bloqueante (Semana 3)

#### A. Implementar Contexto Persistente
```python
class PyodideConsoleManager:
    async def execute_persistent(self, code: str):
        """Ejecutar código manteniendo contexto"""
        try:
            # Usar exec() con globals y locals persistentes
            exec(code, self.globals_dict, self.locals_dict)
            
            # Actualizar globals con nuevas definiciones de locals
            self.globals_dict.update(self.locals_dict)
            
        except Exception as e:
            return ExecutionResult(error=str(e))
```

#### B. Input() No Bloqueante con Cola de Mensajes
```python
class NonBlockingInputManager:
    def __init__(self, console_ui):
        self.console_ui = console_ui
        self.pending_inputs = {}
        self.input_counter = 0
        
    def setup_custom_input(self):
        """Configurar input() personalizado en Pyodide"""
        custom_input_code = """
import asyncio
from js import prompt_for_input

async def async_input(prompt=""):
    # Enviar solicitud a UI
    input_id = await prompt_for_input(prompt)
    # Esperar respuesta
    return await wait_for_input_response(input_id)

# Reemplazar input() built-in
import builtins
builtins.input = lambda prompt="": asyncio.run(async_input(prompt))
"""
        self.pyodide.runPython(custom_input_code)
```

#### C. Manejo de Comandos Multi-línea
```python
class MultilineDetector:
    def is_incomplete(self, code: str) -> bool:
        """Detectar si el código está incompleto"""
        try:
            compile(code, '<string>', 'exec')
            return False
        except SyntaxError as e:
            # Si el error es "unexpected EOF", el código está incompleto
            return "unexpected EOF" in str(e)
        except:
            return False
            
    def get_continuation_prompt(self, code: str) -> str:
        """Obtener prompt de continuación apropiado"""
        indent_level = self.calculate_indent_level(code)
        return "... " + "    " * indent_level
```

### 3.4 FASE 4: Funcionalidades Avanzadas (Semana 4)

#### A. Autocompletado Inteligente
```python
class AutoCompleter:
    def __init__(self, pyodide_manager):
        self.pyodide = pyodide_manager
        
    async def get_completions(self, text: str, cursor_pos: int):
        """Obtener sugerencias de autocompletado"""
        # Usar introspección de Python
        completion_code = f"""
import inspect
import keyword

def get_completions(text, globals_dict, locals_dict):
    completions = []
    
    # Palabras clave de Python
    if text:
        completions.extend([kw for kw in keyword.kwlist if kw.startswith(text)])
    
    # Variables y funciones en scope
    all_names = {{**globals_dict, **locals_dict}}
    completions.extend([name for name in all_names.keys() if name.startswith(text)])
    
    # Atributos de objetos (si hay un punto)
    if '.' in text:
        obj_name, attr_prefix = text.rsplit('.', 1)
        try:
            obj = eval(obj_name, globals_dict, locals_dict)
            attrs = [attr for attr in dir(obj) if attr.startswith(attr_prefix)]
            completions.extend([f"{{obj_name}}.{{attr}}" for attr in attrs])
        except:
            pass
    
    return sorted(set(completions))

get_completions("{text}", globals(), locals())
"""
        
        result = self.pyodide.runPython(completion_code)
        return result
```

#### B. Historial Persistente
```python
class CommandHistory:
    def __init__(self, storage_file="console_history.json"):
        self.storage_file = storage_file
        self.commands = self.load_history()
        self.current_index = len(self.commands)
        
    def load_history(self):
        """Cargar historial desde almacenamiento local"""
        try:
            # Usar app.storage.client de NiceGUI
            from nicegui import app
            return app.storage.client.get('console_history', [])
        except:
            return []
            
    def save_history(self):
        """Guardar historial en almacenamiento local"""
        try:
            from nicegui import app
            app.storage.client['console_history'] = self.commands[-1000:]  # Últimos 1000
        except:
            pass
```

### 3.5 FASE 5: Integración y Refinamiento (Semana 5)

#### A. Integración Completa en ChatInterface
```python
def create_python_console_tab(container):
    """Crear pestaña de consola Python completa"""
    with container:
        # Layout principal de consola
        with ui.column().classes('h-full w-full'):
            # Área de output
            console_output = ui.log().classes('w-full flex-grow font-mono text-sm')
            
            # Barra de estado
            with ui.row().classes('w-full items-center p-2 bg-gray-100'):
                status_label = ui.label('Python Console Ready').classes('text-sm')
                ui.space()
                clear_button = ui.button('Clear', icon='clear', 
                                       on_click=lambda: console_output.clear()).props('flat dense')
            
            # Área de input
            with ui.row().classes('w-full items-start p-2'):
                prompt_label = ui.label('>>> ').classes('text-green-600 font-mono whitespace-pre')
                console_input = ui.textarea(
                    placeholder='Enter Python command... (Shift+Enter for new line, Enter to execute)'
                ).classes('flex-grow font-mono').props('outlined dense autogrow')
            
            # Crear e inicializar consola
            python_console = PersistentPythonConsole(
                output_component=console_output,
                input_component=console_input,
                prompt_component=prompt_label,
                status_component=status_label
            )
            
            return python_console
```

## 4. CASOS DE USO ESPECÍFICOS

### 4.1 Sesión de Consola Típica
```python
>>> import math
>>> x = 10
>>> y = math.sqrt(x)
>>> print(f"Square root of {x} is {y}")
Square root of 10 is 3.1622776601683795

>>> def fibonacci(n):
...     if n <= 1:
...         return n
...     return fibonacci(n-1) + fibonacci(n-2)
... 
>>> fibonacci(10)
55

>>> name = input("Enter your name: ")
Enter your name: Juan
>>> print(f"Hello, {name}!")
Hello, Juan!
```

### 4.2 Manejo de Errores
```python
>>> x = 1 / 0
ZeroDivisionError: division by zero

>>> # Variables anteriores siguen disponibles
>>> print(x)  # x no fue definida debido al error
NameError: name 'x' is not defined

>>> y  # Pero y sigue disponible de antes
3.1622776601683795
```

### 4.3 Input() Interactivo
```python
>>> for i in range(3):
...     name = input(f"Enter name {i+1}: ")
...     print(f"Hello, {name}!")
... 
Enter name 1: Alice
Hello, Alice!
Enter name 2: Bob
Hello, Bob!
Enter name 3: Charlie
Hello, Charlie!
```

## 5. IMPLEMENTACIÓN TÉCNICA DETALLADA

### 5.1 Modificación de ChatInterface (Archivo: chat_interface.py)

```python
# Línea 65-71: Reemplazar pestaña Logs simple
with ui.tab_panel(logs_tab).classes('h-full'):
    # Crear consola Python persistente