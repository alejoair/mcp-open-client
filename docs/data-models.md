# Modelos de Datos

## Visión General

Los modelos de datos en MCP Open Client están definidos usando **Pydantic** para validación automática y serialización. Proporcionan una estructura robusta para toda la comunicación entre frontend y backend.

---

## 🔧 Modelos de Configuración

### ConfigResponse
**Propósito**: Respuesta estándar para operaciones de configuración

```python
class ConfigResponse(BaseModel):
    success: bool                    # Estado de la operación
    message: str = ""               # Mensaje descriptivo
    data: Optional[Dict[str, Any]] = None  # Datos opcionales
```

**Uso típico**:
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "data": { "updated_fields": ["provider_id"] }
}
```

### ProviderModel
**Propósito**: Representación de un proveedor LLM

```python
class ProviderModel(BaseModel):
    id: str                         # Identificador único
    name: str                       # Nombre visible
    base_url: str                   # URL base de la API
    has_api_key: bool              # Indica si tiene API key configurada
```

### ProvidersResponse
**Propósito**: Lista de proveedores disponibles

```python
class ProvidersResponse(BaseModel):
    providers: List[ProviderModel]
```

### ModelInfo
**Propósito**: Información de un modelo específico

```python
class ModelInfo(BaseModel):
    id: str                         # ID del modelo
    name: str                       # Nombre para mostrar
    description: Optional[str] = None  # Descripción opcional
    context_length: Optional[int] = None  # Longitud de contexto
    input_cost: Optional[float] = None    # Costo por token de input
    output_cost: Optional[float] = None   # Costo por token de output
```

### ModelsResponse
**Propósito**: Lista de modelos de un proveedor

```python
class ModelsResponse(BaseModel):
    provider_id: str
    models: List[ModelInfo]
```

### SelectedConfiguration
**Propósito**: Configuración actualmente seleccionada

```python
class SelectedConfiguration(BaseModel):
    provider_id: str = ""
    main_model: str = ""
    small_model: str = ""
```

### UIConfig
**Propósito**: Estado de la interfaz de usuario

```python
class UIConfig(BaseModel):
    left_sidebar_collapsed: bool = False
    right_sidebar_collapsed: bool = False
    bottom_panel_collapsed: bool = True
    theme_mode: str = "dark"
```

---

## 💬 Modelos de Chat

### ChatMessage
**Propósito**: Mensaje individual en una conversación

```python
class ChatMessage(BaseModel):
    role: str                       # "user", "assistant", "system", "tool"
    content: Optional[str] = None   # Contenido del mensaje
    tool_calls: Optional[List[ToolCall]] = None  # Tool calls del mensaje
    tool_call_id: Optional[str] = None  # ID para mensajes de tool
    name: Optional[str] = None      # Nombre del tool (para role="tool")
```

**Ejemplos de uso**:

```python
# Mensaje del usuario
user_message = ChatMessage(
    role="user",
    content="¿Cuál es la raíz cuadrada de 144?"
)

# Mensaje del asistente con tool call
assistant_message = ChatMessage(
    role="assistant",
    content=None,
    tool_calls=[
        ToolCall(
            id="call_123",
            type="function",
            function={"name": "calculate", "arguments": "sqrt(144)"}
        )
    ]
)

# Mensaje de respuesta del tool
tool_message = ChatMessage(
    role="tool",
    content="12",
    tool_call_id="call_123",
    name="calculate"
)
```

### ToolCall
**Propósito**: Llamada a una herramienta específica

```python
class ToolCall(BaseModel):
    id: str                         # ID único del tool call
    type: str = "function"          # Tipo de tool call
    function: Dict[str, Any]        # {"name": str, "arguments": str}
```

**Ejemplo**:
```python
tool_call = ToolCall(
    id="call_abc123",
    type="function",
    function={
        "name": "get_weather",
        "arguments": '{"location": "Madrid"}'
    }
)
```

### ToolResult
**Propósito**: Resultado de la ejecución de una herramienta

```python
class ToolResult(BaseModel):
    tool_call_id: str               # ID del tool call correspondiente
    name: str                       # Nombre de la herramienta
    content: str                    # Resultado de la ejecución
    status: str                     # "success" | "error"
    execution_time: Optional[float] = None  # Tiempo de ejecución en segundos
```

### Tool
**Propósito**: Definición de una herramienta disponible

```python
class Tool(BaseModel):
    type: str = "function"
    function: ToolFunction
```

### ToolFunction
**Propósito**: Metadatos de una función herramienta

```python
class ToolFunction(BaseModel):
    name: str                       # Nombre de la función
    description: str                # Descripción de lo que hace
    parameters: Dict[str, Any]      # JSON Schema de los parámetros
```

**Ejemplo completo**:
```python
calculator_tool = Tool(
    type="function",
    function=ToolFunction(
        name="calculate",
        description="Perform mathematical calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    )
)
```

---

## 📨 Modelos de Request/Response

### ChatCompletionRequest
**Propósito**: Request para chat completion

```python
class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]     # Mensajes de la conversación
    max_tokens: Optional[int] = 1000  # Límite de tokens
    temperature: Optional[float] = 0.7  # Creatividad del modelo
    tools: Optional[List[Tool]] = None  # Herramientas disponibles
    tool_choice: Optional[str] = "auto"  # "auto", "none", "required"
```

### ChatCompletionResponse
**Propósito**: Respuesta de chat completion

```python
class ChatCompletionResponse(BaseModel):
    response: str                   # Respuesta del modelo
    model: str                      # Modelo utilizado
    provider: str                   # Proveedor utilizado
    message_count: int              # Número de mensajes en la conversación
    tool_calls: Optional[List[ToolCall]] = None  # Tool calls realizados
    tool_results: Optional[List[ToolResult]] = None  # Resultados de tools
```

---

## 📋 Modelos de Request para Configuration

### SetAPIKeyRequest
**Propósito**: Configurar API key de un proveedor

```python
class SetAPIKeyRequest(BaseModel):
    api_key: str                    # API key en texto plano (se encripta)
```

### UpdateConfigRequest
**Propósito**: Actualizar configuración seleccionada

```python
class UpdateConfigRequest(BaseModel):
    provider_id: Optional[str] = None
    main_model: Optional[str] = None
    small_model: Optional[str] = None
```

### UpdateUIConfigRequest
**Propósito**: Actualizar configuración de UI

```python
class UpdateUIConfigRequest(BaseModel):
    left_sidebar_collapsed: Optional[bool] = None
    right_sidebar_collapsed: Optional[bool] = None
    bottom_panel_collapsed: Optional[bool] = None
    theme_mode: Optional[str] = None
```

---

## 📊 Modelos de Response Compuestos

### CurrentConfigResponse
**Propósito**: Configuración completa actual

```python
class CurrentConfigResponse(BaseModel):
    success: bool
    data: Dict[str, Any]            # Configuración completa del sistema
```

**Estructura típica del data**:
```json
{
  "app": {
    "name": "MCP Open Client",
    "version": "1.0.0",
    "theme": "terminal-dark"
  },
  "providers": [...],
  "selected_configuration": {...},
  "ui": {...},
  "mcp": {...}
}
```

---

## 🔄 Streaming Data Models

### Streaming Event Types
Los eventos de streaming no tienen modelos Pydantic específicos, pero siguen estructuras consistentes:

#### Start Event
```json
{"type": "start"}
```

#### Content Chunk
```json
{
  "type": "content_chunk",
  "content": "texto del chunk",
  "accumulated_content": "texto completo hasta ahora"
}
```

#### Reasoning Chunk
```json
{
  "type": "reasoning_chunk",
  "content": "proceso de razonamiento",
  "accumulated_reasoning": "razonamiento completo"
}
```

#### Tool Call Start
```json
{
  "type": "tool_call_start",
  "tool_call_id": "call_123",
  "function_name": "calculate"
}
```

#### Tool Call Arguments
```json
{
  "type": "tool_call_arguments",
  "tool_call_id": "call_123",
  "arguments": "2+2",
  "full_arguments": "2+2"
}
```

#### Tool Execution Events
```json
{
  "type": "tool_execution_start",
  "tool_call_id": "call_123",
  "function_name": "calculate"
}

{
  "type": "tool_execution_complete",
  "tool_result": {
    "tool_call_id": "call_123",
    "name": "calculate",
    "content": "4",
    "status": "success",
    "execution_time": 0.123
  }
}
```

#### Complete Event
```json
{
  "type": "complete",
  "final_content": "La respuesta es 4",
  "final_reasoning": "Calculé 2+2 usando la función calculate",
  "tool_calls": [...],
  "tool_results": [...],
  "model": "zai-glm-4.6",
  "provider": "cerebras",
  "message_count": 2
}
```

#### Error Event
```json
{
  "type": "error",
  "error": "Error message"
}
```

---

## 🔍 Validación y Serialización

### Validation Features
Pydantic proporciona validación automática:

```python
# Validación de tipos
chat_message = ChatMessage(
    role="invalid_role",  # ❌ No validará si hay enum constraints
    content=123           # ❌ Debe ser string
)

# Validación de campos requeridos
chat_request = ChatCompletionRequest()  # ❌ Falta 'messages'

# Validación exitosa
chat_request = ChatCompletionRequest(
    messages=[
        ChatMessage(role="user", content="Hello")
    ],
    max_tokens=500,
    temperature=0.8
)
```

### Serialization
```python
# A dict
data = chat_message.dict()

# A JSON
json_str = chat_message.json()

# Desde dict
chat_message = ChatMessage(**data)

# Desde JSON
chat_message = ChatMessage.parse_raw(json_str)
```

### Optional Fields
Los campos opcionales tienen valores por defecto:

```python
request = ChatCompletionRequest(
    messages=[...]
    # max_tokens será 1000 (default)
    # temperature será 0.7 (default)
    # tools será None (default)
)
```

---

## 🎯 Mejores Prácticas

### Extending Models
```python
# Extender modelos existentes
class EnhancedChatMessage(ChatMessage):
    metadata: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
```

### Custom Validators
```python
from pydantic import validator

class ValidatedChatMessage(ChatMessage):
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = {'user', 'assistant', 'system', 'tool'}
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of {allowed_roles}')
        return v

    @validator('content')
    def validate_content_length(cls, v):
        if v and len(v) > 10000:
            raise ValueError('Content too long')
        return v
```

### Type Hints Usage
```python
from typing import List, Optional, Dict, Any

def process_messages(messages: List[ChatMessage]) -> ChatCompletionResponse:
    # Función tipada que maneja modelos Pydantic
    pass

def handle_tool_calls(tool_calls: Optional[List[ToolCall]]) -> List[ToolResult]:
    # Manejo de campos opcionales
    if not tool_calls:
        return []

    results = []
    for tool_call in tool_calls:
        # Procesar cada tool call
        pass

    return results
```