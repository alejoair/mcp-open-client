# Sistema de Chat y Streaming

## Visión General

El sistema de chat maneja la comunicación en tiempo real con proveedores LLM, incluyendo streaming de respuestas y ejecución de tool calls. Está diseñado para ser extensible y soportar múltiples proveedores.

## 🔧 Componentes Principales

### ChatClient - Cliente Universal LLM

#### 📄 Ubicación
`mcp_open_client/services/chat_client.py`

#### 🏗️ Arquitectura

```python
class ChatClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        # Context manager - crea sesión HTTP

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cierra sesión HTTP automáticamente
```

#### 🔌 Métodos Principales

##### Chat Simple
```python
async def create_completion(
    self,
    provider_id: str,
    model: str,
    messages: List[Dict[str, Any]],
    api_key: str,
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> str:
```

##### Chat con Streaming ⚡
```python
async def create_streaming_completion(
    self,
    provider_id: str,
    model: str,
    messages: List[Dict[str, Any]],
    api_key: str,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto"
):
```

### 🌊 Streaming Response Processing

#### Detección de Content Types
El cliente procesa diferentes tipos de contenido en tiempo real:

1. **Reasoning** (`delta.reasoning`)
   - Proceso de pensamiento del modelo
   - Se muestra en sección colapsible

2. **Content** (`delta.content` o `delta.text`)
   - Respuesta principal del modelo
   - Se muestra como contenido principal

3. **Tool Calls** (`delta.tool_calls`)
   - Llamadas a herramientas detectadas
   - Se procesan incrementalmente

#### Especial: zai-glm-4.6 Model
```python
# Manejo especial para modelo que solo envía 'reasoning'
if reasoning:
    yield {"type": "reasoning", "content": reasoning}
if content:
    yield {"type": "content", "content": content}
elif text:
    yield {"type": "content", "content": text}
elif reasoning:
    # Si solo hay reasoning, también enviarlo como content
    yield {"type": "content", "content": reasoning}
```

## 🛠️ Tool Calls System

### ToolSimulator - Simulador de Herramientas

#### 📄 Ubicación
`mcp_open_client/services/tool_simulator.py`

#### 🎯 Propósito
Simula la ejecución de herramientas durante desarrollo, preparando el sistema para futura integración MCP.

#### 🧰 Herramientas Disponibles

##### 1. calculate
```python
async def calculate(self, expression: str) -> str:
    # Evalúa expresiones matemáticas
    # ⚠️ Usa eval() - solo en simulación
```

##### 2. get_current_time
```python
async def get_current_time(self, timezone: str = "UTC") -> str:
    # Retorna fecha/hora actual
```

##### 3. search_web
```python
async def search_web(self, query: str) -> str:
    # Simulación de búsqueda web
```

##### 4. get_weather
```python
async def get_weather(self, location: str) -> str:
    # Simulación de información del clima
```

##### 5. read_file / write_file
```python
async def read_file(self, filename: str) -> str:
async def write_file(self, filename: str, content: str) -> str:
    # Simulación de operaciones de archivo
```

#### ⚡ Simulación Realista
```python
async def execute_tool(self, tool_call_id: str, name: str, arguments: str):
    # Delay realista (100-500ms)
    await self._simulate_delay()

    # Ejecución con timing
    start_time = time.time()
    # ... ejecución ...
    execution_time = time.time() - start_time

    return {
        "tool_call_id": tool_call_id,
        "name": name,
        "content": result,
        "status": "success|error",
        "execution_time": execution_time
    }
```

## 🛣️ Chat Routes - API Endpoints

### 📄 Ubicación
`mcp_open_client/server/routes/chat.py`

### 🌐 Endpoints

#### POST /api/chat/completions
**Chat simple sin streaming**

#### POST /api/chat/completions/stream ⚡
**Chat con streaming y tool calls**

### 🔄 Flujo de Streaming

#### 1. Validación y Configuración
```python
# Obtener configuración actual
config = config_manager.get_config()
selected = config.get('selected_configuration', {})
provider_id = selected.get('provider_id')
main_model = selected.get('main_model')

# Validar configuración
if not provider_id or not main_model:
    yield error_event

# Obtener API key
api_key = config_manager.get_provider_api_key(provider_id)
```

#### 2. Preparación de Tools
```python
# Tools por defecto incluidas automáticamente
default_tools = [
    {"type": "function", "function": {"name": "calculate", ...}},
    {"type": "function", "function": {"name": "get_current_time", ...}},
    {"type": "function", "function": {"name": "search_web", ...}},
    {"type": "function", "function": {"name": "get_weather", ...}}
]

# tool_choice: "auto" permite al modelo decidir
```

#### 3. Processing del Streaming
```python
async for data_chunk in client.create_streaming_completion(...):
    chunk_type = data_chunk.get("type", "content")

    if chunk_type == "reasoning":
        # Procesar chunk de reasoning
        yield reasoning_event

    elif chunk_type == "tool_call_start":
        # Iniciar acumulación de tool call
        active_tool_calls[tool_call_id] = {...}
        yield tool_call_start_event

    elif chunk_type == "tool_call_arguments":
        # Acumular argumentos del tool call
        yield tool_call_arguments_event

    else: # content
        # Procesar contenido principal
        yield content_event
```

#### 4. Ejecución de Tool Calls
```python
# Después del streaming, ejecutar tools detectados
if active_tool_calls:
    for tool_call_id, tool_call in active_tool_calls.items():
        # Señalar inicio de ejecución
        yield tool_execution_start_event

        try:
            # Ejecutar con ToolSimulator
            result = await tool_simulator.execute_tool(
                tool_call_id=tool_call_id,
                name=tool_call['function_name'],
                arguments=tool_call['arguments']
            )
            yield tool_execution_complete_event

        except Exception as e:
            yield tool_execution_error_event
```

## 🎨 Frontend Integration

### ChatWindow.js - Interface Principal

#### 📄 Ubicación
`mcp_open_client/ui/components/ChatWindow.js`

#### 🔄 Event Handling
```javascript
// Configuración SSE
const eventSource = new EventSource('/api/chat/completions/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'reasoning_chunk':
            updateReasoningSection(data);
            break;
        case 'content_chunk':
            updateMainContent(data);
            break;
        case 'tool_call_start':
            createToolCallDisplay(data);
            break;
        case 'tool_execution_complete':
            updateToolResult(data);
            break;
        case 'complete':
            finalizeMessage(data);
            break;
    }
};
```

#### 🎯 Message Structure
```javascript
const message = {
    role: 'assistant',
    content: 'Main response content',
    reasoning: 'Model reasoning process',
    tool_calls: [...],
    tool_results: [...],
    isStreaming: false,
    timestamp: new Date().toISOString()
};
```

## 🚀 Performance Features

### ⚡ Optimizaciones

#### Streaming Chunks
- **Buffering**: Chunks pequeños se bufferean para mejor UX
- **Debouncing**: Updates de UI se optimizan
- **Memory**: Liberación automática de recursos

#### Connection Management
```python
# Context manager automático
async with ChatClient() as client:
    # Sesión HTTP reutilizable
    # Cleanup automático
```

#### Error Recovery
- **Timeout**: Requests con timeout configurable
- **Retry**: Lógica de retry para fallos transitorios
- **Graceful**: Manejo elegante de desconexiones

## 🔐 Security Considerations

### 🛡️ Protecciones

#### API Keys
- Nunca se exponen en logs
- Desencriptación solo cuando es necesario
- No se envían al frontend

#### Tool Execution
- Sandboxing en ToolSimulator
- Validación de argumentos
- Limits de ejecución

#### Input Validation
- Validación Pydantic automática
- Sanitización de inputs
- Rate limiting (futuro)

## 🔮 Extensibilidad

### 🔌 Nuevos Providers
```python
# Agregar soporte para nuevo provider
def get_provider_headers(provider_id: str, api_key: str):
    if provider_id == "new_provider":
        return {"Authorization": f"Bearer {api_key}"}
```

### 🛠️ Nuevas Tools
```python
# Agregar nueva herramienta al ToolSimulator
async def new_tool(self, param: str) -> str:
    # Implementación de la herramienta
    return result
```

### 📡 Protocolos de Streaming
El sistema está preparado para diferentes formatos de streaming (OpenAI, Anthropic, etc.).