"""
Implementación del sistema de meta tools para MCP Open Client.
"""

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
    
    def _ui_notify(self, message: str, type: str = "info", position: str = "bottom", duration: int = 3000):
        """Implementación de la meta tool ui_notify."""
        ui.notify(message, type=type, position=position, timeout=duration)
        return f"Notification displayed: {message}"

# Decorador para facilitar el registro de meta tools
def meta_tool(name: str, description: str, parameters_schema: Dict[str, Any]):
    """Decorador para registrar una función como meta tool."""
    def decorator(func):
        meta_tool_registry.register_tool(name, func, description, parameters_schema)
        return func
    return decorator

# Instancia global del registro de meta tools
meta_tool_registry = MetaToolRegistry()