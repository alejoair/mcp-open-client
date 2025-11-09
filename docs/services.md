# Servicios del Backend

## Visión General

Los servicios del backend proporcionan la lógica de negocio principal para comunicación con LLMs, simulación de herramientas y gestión de providers. Están organizados modularmente para facilitar mantenimiento y extensión.

---

## 🌐 ChatClient - Cliente Universal LLM

### 📄 Ubicación
`mcp_open_client/services/chat_client.py`

### 🎯 Responsabilidades
- Comunicación HTTP con múltiples proveedores LLM
- Manejo de streaming con Server-Sent Events
- Procesamiento de tool calls en tiempo real
- Gestión de sesiones HTTP asíncronas

### 🏗️ Diseño

#### Context Manager Pattern
```python
class ChatClient:
    async def __aenter__(self):
        """Crear sesión HTTP reutilizable"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automático de recursos"""
        if self._session:
            await self._session.close()
```

#### Provider Abstraction
```python
def get_provider_headers(self, provider_id: str, api_key: str) -> Dict[str, str]:
    """Headers específicos por provider"""
    header_mapping = {
        "openai": {"Authorization": f"Bearer {api_key}"},
        "anthropic": {"x-api-key": api_key},
        "cerebras": {"Authorization": f"Bearer {api_key}"}
    }
    return header_mapping.get(provider_id, {})
```

### 🔧 Métodos Principales

#### create_completion()
**Chat completion simple**
- Response única, sin streaming
- Para casos donde no se necesita tiempo real
- Retorna string con respuesta completa

#### create_streaming_completion() ⚡
**Chat completion con streaming**
- Generator asíncrono de eventos
- Procesamiento en tiempo real
- Soporte para tool calls
- Yields de diferentes tipos de eventos

### 🌊 Streaming Event Types

#### Reasoning Events
```python
{"type": "reasoning", "content": "Model thinking process..."}
```

#### Content Events
```python
{"type": "content", "content": "Main response text..."}
```

#### Tool Call Events
```python
{"type": "tool_call_start", "tool_call_id": "call_123", "function_name": "calculate"}
{"type": "tool_call_arguments", "tool_call_id": "call_123", "arguments": "2+2"}
```

### 🔌 Provider Compatibility

#### OpenAI Format
- Compatible con formato OpenAI Chat Completions
- Soporte para tool calls
- Headers: `Authorization: Bearer {api_key}`

#### Cerebras (zai-glm-4.6)
- Formato compatible con OpenAI
- Especificidad: Solo envía `delta.reasoning`
- Manejo especial en procesamiento

#### Anthropic (Preparado)
- Headers: `x-api-key: {api_key}`
- Adaptación de formato (futuro)

---

## 🛠️ ToolSimulator - Simulador de Herramientas

### 📄 Ubicación
`mcp_open_client/services/tool_simulator.py`

### 🎯 Propósito
Simula ejecución de herramientas durante desarrollo, proporcionando una base sólida para futura integración MCP (Model Context Protocol).

### 🧰 Herramientas Implementadas

#### 1. calculate - Calculadora Matemática
```python
async def calculate(self, expression: str) -> str:
    """
    Evalúa expresiones matemáticas básicas
    ⚠️ Usa eval() - SOLO para simulación
    """
    try:
        # Validación básica de seguridad
        if any(dangerous in expression for dangerous in ['import', 'exec', '__']):
            return "Error: Unsafe operation"

        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

#### 2. get_current_time - Información Temporal
```python
async def get_current_time(self, timezone: str = "UTC") -> str:
    """Retorna fecha y hora actual"""
    from datetime import datetime
    now = datetime.now()
    return f"Current time ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"
```

#### 3. search_web - Búsqueda Simulada
```python
async def search_web(self, query: str) -> str:
    """Simula búsqueda web con resultados ficticios"""
    return f"Search results for '{query}':\n" \
           f"1. Example result about {query}\n" \
           f"2. Another relevant article\n" \
           f"3. Related information source"
```

#### 4. get_weather - Información Meteorológica
```python
async def get_weather(self, location: str) -> str:
    """Simula información del clima"""
    temp = random.randint(15, 30)
    conditions = random.choice(["sunny", "cloudy", "rainy"])
    return f"Weather in {location}: {temp}°C, {conditions}"
```

#### 5. read_file / write_file - Operaciones de Archivo
```python
async def read_file(self, filename: str) -> str:
    """Simula lectura de archivo"""
    return f"Contents of {filename}:\n[Simulated file content]"

async def write_file(self, filename: str, content: str) -> str:
    """Simula escritura de archivo"""
    return f"Successfully wrote {len(content)} characters to {filename}"
```

### ⚡ Características de Simulación

#### Delays Realistas
```python
async def _simulate_delay(self):
    """Simula delay de red realista"""
    delay = random.uniform(0.1, 0.5)  # 100-500ms
    await asyncio.sleep(delay)
```

#### Ejecución con Timing
```python
async def execute_tool(self, tool_call_id: str, name: str, arguments: str):
    start_time = time.time()

    # Simulación de delay
    await self._simulate_delay()

    # Ejecución
    if name in self.tools:
        args = json.loads(arguments)
        result = await self.tools[name](**args)
    else:
        result = f"Tool '{name}' not found"

    # Medición de tiempo
    execution_time = time.time() - start_time

    return {
        "tool_call_id": tool_call_id,
        "name": name,
        "content": result,
        "status": "success" if name in self.tools else "error",
        "execution_time": execution_time
    }
```

#### Global Instance
```python
# Instancia global singleton
tool_simulator = ToolSimulator()
```

---

## 🔧 ProviderClient - Cliente Genérico

### 📄 Ubicación
`mcp_open_client/services/provider_client.py`

### 🎯 Propósito
Cliente HTTP genérico para comunicación con APIs de proveedores. Funcionalidad básica que puede ser extendida.

### 🛠️ Funcionalidades
- HTTP client básico con aiohttp
- Manejo de timeouts
- Headers personalizables
- Base para extensiones específicas por provider

---

## 🔗 Integración entre Servicios

### 🔄 Flujo de Chat con Tools

#### 1. Request Inicial
```
Frontend → Chat Routes → ConfigManager
                    ↓
              ChatClient ← Provider Config
```

#### 2. Streaming Response
```
LLM Provider → ChatClient → Stream Processing
                          ↓
                    Tool Detection
                          ↓
                   Tool Call Events
```

#### 3. Tool Execution
```
Tool Calls → ToolSimulator → Execution Results
                          ↓
                   Result Events
```

#### 4. Response Completion
```
All Events → Frontend → UI Updates
```

### 🏗️ Dependency Injection

#### Config Manager
```python
# Global instance accesible por todos los servicios
from mcp_open_client.config import config_manager

# Usado en chat routes
provider_id = config_manager.get_selected_config().get('provider_id')
api_key = config_manager.get_provider_api_key(provider_id)
```

#### Tool Simulator
```python
# Global instance para consistencia
from mcp_open_client.services.tool_simulator import tool_simulator

# Usado en chat routes para ejecutar tools
result = await tool_simulator.execute_tool(...)
```

## 🚀 Performance y Escalabilidad

### ⚡ Optimizaciones

#### Connection Pooling
- **ChatClient**: Reutiliza sesiones HTTP
- **aiohttp**: Connection pooling automático
- **Limits**: Configuración de límites de conexión

#### Async Processing
- **Streaming**: No bloquea el hilo principal
- **Tool Execution**: Paralelo cuando es posible
- **Memory Management**: Cleanup automático

#### Resource Management
```python
# Context managers para cleanup automático
async with ChatClient() as client:
    # Recursos se liberan automáticamente
```

### 📊 Monitoring y Logging

#### Request Logging
```python
logger.info(f"🤖 Chat request: {len(messages)} messages to {provider_id}/{model}")
logger.info(f"✅ Chat response received: {len(response_text)} characters")
logger.info(f"🔧 Executing {len(tool_calls)} tool calls")
```

#### Error Logging
```python
logger.error(f"Chat completion failed: {e}")
logger.error(f"Tool execution failed: {e}")
```

## 🔮 Extensibilidad

### 🔌 Añadir Nuevo Provider

#### 1. Extender ChatClient
```python
def get_provider_headers(self, provider_id: str, api_key: str):
    # Agregar nuevo provider
    if provider_id == "new_provider":
        return {"Authorization": f"Custom {api_key}"}
```

#### 2. Configurar en ConfigManager
```python
# Agregar a default providers
{
    "id": "new_provider",
    "name": "New Provider",
    "base_url": "https://api.newprovider.com/v1"
}
```

### 🛠️ Añadir Nueva Tool

#### 1. Implementar en ToolSimulator
```python
async def new_tool(self, param: str) -> str:
    """Nueva herramienta simulada"""
    # Lógica de la herramienta
    return result

# Registrar en constructor
self.tools = {
    "new_tool": self.new_tool,
    # ... otras tools
}
```

#### 2. Agregar a Default Tools (chat routes)
```python
{
    "type": "function",
    "function": {
        "name": "new_tool",
        "description": "Description of new tool",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param"]
        }
    }
}
```

## 🔐 Consideraciones de Seguridad

### 🛡️ ToolSimulator Security
- **Eval Protection**: Validación antes de eval()
- **Sandboxing**: Operaciones limitadas
- **Input Validation**: JSON parsing seguro
- **Error Handling**: No exposición de internals

### 🔒 ChatClient Security
- **API Key Protection**: No logs de keys sensibles
- **Timeout Protection**: Prevenir conexiones infinitas
- **Resource Limits**: Límites de memoria y conexiones
- **HTTPS Only**: Conexiones seguras por defecto