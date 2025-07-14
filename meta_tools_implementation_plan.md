# Plan de Implementación: Sistema de Meta Tools para MCP Open Client

## Introducción

Este documento describe el plan para implementar un sistema de "meta tools" en MCP Open Client. Estas herramientas especiales permitirán modificar el comportamiento de la aplicación a nivel de NiceGUI, a diferencia de las herramientas MCP estándar que se ejecutan en servidores externos.

## Fase 1: Arquitectura Básica

### 1.1. Estructura del Sistema

El sistema de meta tools se integrará en la arquitectura existente de MCP Open Client, pero funcionará en paralelo al sistema MCP. La idea principal es:

1. **Registro de Meta Tools**: Crear un registro independiente para las meta tools
2. **Detección de Meta Tools**: Modificar el sistema de detección de tool calls para identificar cuándo se debe usar una meta tool vs una herramienta MCP
3. **Ejecución de Meta Tools**: Implementar un mecanismo para ejecutar las meta tools en el contexto de NiceGUI

### 1.2. Componentes Iniciales

Para la primera fase, necesitaremos crear:

- **MetaToolRegistry**: Una clase para gestionar el registro y ejecución de meta tools
- **Modificaciones a handle_tool_call.py**: Para detectar y enrutar las meta tools
- **Ejemplo de Meta Tool**: Implementar una meta tool básica (ui.notify) como prueba de concepto

### 1.3. Flujo de Ejecución

El flujo básico será:

1. LLM genera una llamada a una meta tool
2. `handle_tool_call` detecta que es una meta tool (por prefijo o registro)
3. En lugar de enviarlo al MCP Client, lo envía al MetaToolRegistry
4. MetaToolRegistry ejecuta la meta tool en el contexto de NiceGUI
5. El resultado se devuelve al LLM como una respuesta de tool normal

## Próximos Pasos

En la siguiente iteración, detallaré:
- La implementación específica de MetaToolRegistry
- Las modificaciones exactas necesarias en handle_tool_call.py
- El formato de definición de las meta tools

## Fase 2: Implementación del MetaToolRegistry

### 2.1. Definición de la Clase MetaToolRegistry

```python
# meta_tools.py
import inspect
from typing import Dict, Any, List, Callable, Optional
from nicegui import ui

class MetaToolRegistry:
    """Registro y gestor de meta tools para MCP Open Client."""
    
    def __init__(self):
        self.tools = {}
        self.tool_schemas = {}
        self._register_default_tools()
    
    def register_tool(self, name: str, func: Callable, description: str, parameters_schema: Dict[str, Any]):
        """Registrar una nueva meta tool."""
        # Prefijamos el nombre para distinguirlo de herramientas MCP
        tool_name = f"meta-{name}" if not name.startswith("meta-") else name
        self.tools[tool_name] = func
        self.tool_schemas[tool_name] = {
            "name": tool_name,
            "description": description,
            "parameters": parameters_schema
        }
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar una meta tool registrada."""
        if not tool_name.startswith("meta-"):
            tool_name = f"meta-{tool_name}"
            
        if tool_name not in self.tools:
            return {"error": f"Meta tool '{tool_name}' not found"}
        
        try:
            func = self.tools[tool_name]
            # Verificar si la función es asíncrona
            if inspect.iscoroutinefunction(func):
                result = await func(**params)
            else:
                result = func(**params)
            
            # Formatear el resultado para que sea compatible con el formato de tool call
            return {"result": result}
        except Exception as e:
            return {"error": f"Error executing meta tool '{tool_name}': {str(e)}"}
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Obtener el esquema de todas las meta tools en formato compatible con OpenAI."""
        tools = []
        for name, schema in self.tool_schemas.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": schema["description"],
                    "parameters": schema["parameters"]
                }
            })
        return tools
    
    def _register_default_tools(self):
        """Registrar las meta tools predeterminadas."""
        # Registrar ui.notify como meta tool
        self.register_tool(
            name="ui_notify",
            func=self._ui_notify,
            description="Muestra una notificación en la interfaz de usuario",
            parameters_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje a mostrar"},
                    "type": {"type": "string", "enum": ["positive", "negative", "warning", "info"], "default": "info"},
                    "position": {"type": "string", "enum": ["top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"], "default": "bottom"},
                    "duration": {"type": "integer", "default": 3000}
                },
                "required": ["message"]
            }
        )
        
        # Aquí se pueden registrar más meta tools predeterminadas
    
    def _ui_notify(self, message: str, type: str = "info", position: str = "bottom", duration: int = 3000):
        """Implementación de la meta tool ui_notify."""
        ui.notify(message, type=type, position=position, timeout=duration)
        return f"Notification displayed: {message}"
```

### 2.2. Instanciación del Registro

Se debe crear una instancia global del registro para que esté disponible en toda la aplicación:

```python
# En meta_tools.py (continuación)

# Instancia global del registro de meta tools
meta_tool_registry = MetaToolRegistry()
```

## Fase 3: Modificaciones al Sistema Existente

### 3.1. Modificaciones a handle_tool_call.py

Es necesario modificar la función `handle_tool_call` para detectar y ejecutar meta tools:

```python
# handle_tool_call.py (modificado)

# Importar el registro de meta tools
from .meta_tools import meta_tool_registry

async def handle_tool_call(tool_call):
    """Handle a tool call from the LLM."""
    try:
        function_call = tool_call.get("function", {})
        tool_name = function_call.get("name", "")
        arguments_str = function_call.get("arguments", "{}")
        
        # Intentar reparar el JSON si es necesario
        arguments = attempt_json_repair(arguments_str)
        
        # Validar y limpiar los argumentos
        arguments = validate_and_clean_arguments(tool_name, arguments)
        
        # Verificar si es una meta tool (por el prefijo "meta-")
        if tool_name.startswith("meta-") or f"meta-{tool_name}" in meta_tool_registry.tools:
            # Es una meta tool, ejecutarla usando el registro de meta tools
            print(f"Executing meta tool: {tool_name}")
            result = await meta_tool_registry.execute_tool(tool_name, arguments)
            
            # Formatear el resultado para que sea compatible con el formato de OpenAI
            return {
                "tool_call_id": tool_call["id"],
                "content": json.dumps(result, ensure_ascii=False)
            }
        else:
            # Es una herramienta MCP normal, usar el flujo existente
            print(f"Executing MCP tool: {tool_name}")
            result = await mcp_client_manager.call_tool(tool_name, arguments)
            return {
                "tool_call_id": tool_call["id"],
                "content": result
            }
    except Exception as e:
        error_message = f"Error executing tool '{tool_call.get('function', {}).get('name', 'unknown')}': {str(e)}"
        print(f"Tool execution error: {error_message}")
        return {
            "tool_call_id": tool_call["id"],
            "content": error_message
        }
```

### 3.2. Modificaciones a get_available_tools()

También debemos modificar la función `get_available_tools()` para incluir las meta tools:

```python
# handle_tool_call.py (modificado)

async def get_available_tools():
    """Get available tools for the LLM."""
    try:
        # Obtener herramientas MCP
        mcp_tools = []
        if mcp_client_manager.is_initialized():
            try:
                mcp_tools = await mcp_client_manager.list_tools()
            except Exception as e:
                print(f"Error listing MCP tools: {str(e)}")
        
        # Obtener meta tools
        meta_tools = meta_tool_registry.get_tools_schema()
        
        # Combinar ambos conjuntos de herramientas
        all_tools = mcp_tools + meta_tools
        
        return all_tools
    except Exception as e:
        print(f"Error getting available tools: {str(e)}")
        return []
```

## Fase 4: Implementación de Meta Tools Adicionales

### 4.1. Estructura para Crear Nuevas Meta Tools

Para facilitar la creación y registro de nuevas meta tools, podemos implementar un sistema de decoradores:

```python
# meta_tools.py (continuación)

def meta_tool(name: str, description: str, parameters_schema: Dict[str, Any]):
    """Decorador para registrar una función como meta tool."""
    def decorator(func):
        meta_tool_registry.register_tool(name, func, description, parameters_schema)
        return func
    return decorator
```

### 4.2. Ejemplos de Meta Tools Adicionales

Aquí hay algunos ejemplos de meta tools útiles que podemos implementar:

```python
# En un nuevo archivo meta_tools_implementations.py

from .meta_tools import meta_tool, meta_tool_registry
from nicegui import ui, app
from typing import Dict, Any, List, Optional
import asyncio

@meta_tool(
    name="ui_dialog",
    description="Muestra un diálogo modal con un mensaje personalizado",
    parameters_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Título del diálogo"},
            "content": {"type": "string", "description": "Contenido del diálogo"},
            "options": {"type": "object", "description": "Opciones adicionales"}
        },
        "required": ["title", "content"]
    }
)
async def show_dialog(title: str, content: str, options: Dict[str, Any] = None):
    """Muestra un diálogo modal."""
    options = options or {}
    
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes('text-h6')
        ui.separator()
        ui.label(content)
        with ui.row().classes('w-full justify-end'):
            ui.button('OK', on_click=dialog.close)
    
    dialog.open()
    # Esperar un momento para que el diálogo se muestre
    await asyncio.sleep(0.5)
    
    return {"status": "success", "message": f"Dialog shown with title: {title}"}

@meta_tool(
    name="app_get_storage",
    description="Obtiene un valor almacenado en el storage de la aplicación",
    parameters_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Clave del valor a obtener"},
            "storage_type": {"type": "string", "enum": ["user", "app"], "default": "user"}
        },
        "required": ["key"]
    }
)
def get_storage(key: str, storage_type: str = "user"):
    """Obtiene un valor del storage de la aplicación."""
    try:
        if storage_type == "user":
            value = app.storage.user.get(key)
        else:
            value = app.storage.app.get(key)
        
        return {"key": key, "value": value}
    except Exception as e:
        return {"error": f"Error accessing storage: {str(e)}"}

@meta_tool(
    name="app_set_storage",
    description="Almacena un valor en el storage de la aplicación",
    parameters_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Clave para almacenar el valor"},
            "value": {"type": "object", "description": "Valor a almacenar"},
            "storage_type": {"type": "string", "enum": ["user", "app"], "default": "user"}
        },
        "required": ["key", "value"]
    }
)
def set_storage(key: str, value: Any, storage_type: str = "user"):
    """Almacena un valor en el storage de la aplicación."""
    try:
        if storage_type == "user":
            app.storage.user[key] = value
        else:
            app.storage.app[key] = value
        
        return {"status": "success", "message": f"Value stored with key: {key}"}
    except Exception as e:
        return {"error": f"Error setting storage: {str(e)}"}
```

## Fase 5: Consideraciones de Seguridad y Pruebas

### 5.1. Consideraciones de Seguridad

Las meta tools tienen acceso directo a la aplicación, lo que plantea consideraciones de seguridad importantes:

1. **Validación de Parámetros**: Implementar validación estricta de todos los parámetros para evitar inyecciones o comportamientos inesperados.

2. **Limitación de Acceso**: Considerar la implementación de un sistema de permisos para las meta tools más sensibles.

3. **Sandboxing**: Limitar el alcance de lo que pueden hacer las meta tools para evitar modificaciones no deseadas.

4. **Logging**: Registrar todas las llamadas a meta tools para auditoría y depuración.

### 5.2. Plan de Pruebas

Para asegurar el correcto funcionamiento del sistema de meta tools, se deben realizar las siguientes pruebas:

1. **Pruebas Unitarias**:
   - Verificar el registro correcto de meta tools
   - Probar la ejecución de meta tools con parámetros válidos e inválidos
   - Comprobar el manejo de errores

2. **Pruebas de Integración**:
   - Verificar la integración con el sistema de tool calling existente
   - Probar la combinación de meta tools y herramientas MCP en una misma conversación
   - Comprobar que las meta tools se muestran correctamente en el esquema de herramientas

3. **Pruebas de UI**:
   - Verificar que las notificaciones y diálogos se muestran correctamente
   - Comprobar la interacción del usuario con los elementos de UI generados por meta tools

## Fase 6: Documentación e Integración Final

### 6.1. Documentación

Crear documentación detallada sobre:

1. **Uso del Sistema de Meta Tools**: Cómo funciona y cómo integrarlo
2. **Creación de Nuevas Meta Tools**: Guía paso a paso
3. **Referencia de API**: Documentación completa de las meta tools disponibles
4. **Consideraciones de Seguridad**: Buenas prácticas y advertencias

### 6.2. Integración en la Aplicación Principal

Pasos finales para la integración completa:

1. Importar el módulo de meta tools en el punto de entrada de la aplicación
2. Registrar las meta tools adicionales
3. Verificar que las meta tools aparecen en el esquema de herramientas
4. Realizar pruebas finales de integración

## Fase 7: Extensibilidad y Casos de Uso Avanzados

### 7.1. Sistema de Plugins para Meta Tools

Para hacer el sistema aún más extensible, podemos implementar un sistema de plugins que permita cargar meta tools desde módulos externos:

```python
# meta_tools_plugins.py
import importlib
import importlib.util
import os
import sys
from typing import List, Dict, Any

class MetaToolPluginLoader:
    """Cargador de plugins para meta tools."""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.loaded_plugins = {}
    
    def discover_plugins(self) -> List[str]:
        """Descubrir plugins disponibles en el directorio de plugins."""
        plugin_files = []
        
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return plugin_files
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_files.append(os.path.join(self.plugins_dir, filename))
        
        return plugin_files
    
    def load_plugin(self, plugin_path: str) -> bool:
        """Cargar un plugin desde un archivo."""
        try:
            plugin_name = os.path.basename(plugin_path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # Registrar el plugin
            self.loaded_plugins[plugin_name] = module
            
            # Verificar si el plugin tiene una función de inicialización
            if hasattr(module, "register_meta_tools"):
                module.register_meta_tools()
            
            print(f"Loaded meta tool plugin: {plugin_name}")
            return True
        except Exception as e:
            print(f"Error loading plugin {plugin_path}: {str(e)}")
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """Cargar todos los plugins disponibles."""
        results = {}
        plugin_files = self.discover_plugins()
        
        for plugin_path in plugin_files:
            plugin_name = os.path.basename(plugin_path).replace(".py", "")
            results[plugin_name] = self.load_plugin(plugin_path)
        
        return results
```

### 7.2. Ejemplos de Casos de Uso Avanzados

El sistema de meta tools permite implementar funcionalidades avanzadas que van más allá de las herramientas MCP estándar:

1. **Manipulación de la Interfaz de Usuario**:
   - Crear nuevos elementos de UI dinámicamente
   - Modificar la apariencia de la aplicación
   - Implementar modos de visualización personalizados

2. **Integración con el Sistema**:
   - Acceder y modificar la configuración de la aplicación
   - Gestionar conversaciones y historial
   - Controlar el comportamiento del LLM

3. **Interacción con Recursos Locales**:
   - Acceder a archivos locales (con las debidas restricciones de seguridad)
   - Gestionar recursos de la aplicación
   - Interactuar con bases de datos locales

4. **Automatización de Flujos de Trabajo**:
   - Crear secuencias de acciones predefinidas
   - Implementar workflows personalizados
   - Automatizar tareas repetitivas

## Resumen de Implementación

### Cronograma Sugerido

| Fase | Descripción | Tiempo Estimado |
|------|-------------|------------------|
| 1 | Arquitectura Básica | 1 día |
| 2 | Implementación del MetaToolRegistry | 1 día |
| 3 | Modificaciones al Sistema Existente | 1 día |
| 4 | Implementación de Meta Tools Adicionales | 2 días |
| 5 | Pruebas y Seguridad | 2 días |
| 6 | Documentación e Integración Final | 1 día |
| 7 | Sistema de Plugins (opcional) | 2 días |

### Archivos a Crear/Modificar

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `meta_tools.py` | Nuevo | Implementación del registro de meta tools |
| `meta_tools_implementations.py` | Nuevo | Implementaciones de meta tools específicas |
| `meta_tools_plugins.py` | Nuevo | Sistema de carga de plugins (opcional) |
| `handle_tool_call.py` | Modificar | Integración con el sistema existente |
| `__init__.py` | Modificar | Exportar las clases y funciones necesarias |

### Consideraciones Finales

1. **Compatibilidad**: Asegurar que el sistema de meta tools sea compatible con diferentes LLMs y versiones de la API.

2. **Rendimiento**: Monitorear el impacto en el rendimiento, especialmente para meta tools que modifican la UI.

3. **Mantenibilidad**: Diseñar el sistema para que sea fácil de mantener y extender en el futuro.

4. **Experiencia de Usuario**: Asegurar que las meta tools mejoren la experiencia del usuario y no la compliquen.

5. **Documentación**: Mantener una documentación clara y actualizada para facilitar la adopción y extensión del sistema.
```
```