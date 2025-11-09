# API Endpoints

## Visión General

El backend expone una API REST completa para configuración y chat a través de FastAPI. Todos los endpoints siguen el patrón `/api/{resource}/{action}`.

## 🌐 Base URLs

- **Desarrollo**: `http://localhost:8007/api`
- **Producción**: `{deployment_url}/api`

---

## 🔧 Configuration Endpoints

**Prefix**: `/api/config`

### GET /api/config/
**Obtener configuración actual completa**

**Response**:
```json
{
  "success": true,
  "data": {
    "app": { "name": "MCP Open Client", "version": "1.0.0" },
    "providers": [...],
    "selected_configuration": {...},
    "ui": {...}
  }
}
```

### GET /api/config/providers
**Obtener lista de todos los providers**

**Response**:
```json
{
  "providers": [
    {
      "id": "cerebras",
      "name": "Cerebras",
      "base_url": "https://api.cerebras.ai/v1",
      "has_api_key": true
    }
  ]
}
```

### GET /api/config/providers/{provider_id}/models
**Obtener modelos disponibles para un provider**

**Parameters**:
- `provider_id` (path): ID del provider

**Response**:
```json
{
  "provider_id": "cerebras",
  "models": [
    {
      "id": "zai-glm-4.6",
      "name": "zai-glm-4.6",
      "description": "Fast reasoning model"
    }
  ]
}
```

**Errors**:
- `400`: Provider no configurado o sin API key
- `404`: Provider no encontrado
- `500`: Error al obtener modelos del provider

### POST /api/config/providers/{provider_id}/api-key
**Configurar API key para un provider**

**Parameters**:
- `provider_id` (path): ID del provider

**Request Body**:
```json
{
  "api_key": "sk-..."
}
```

**Response**:
```json
{
  "success": true,
  "message": "API key configured successfully"
}
```

**Errors**:
- `400`: API key no proporcionada
- `404`: Provider no encontrado
- `500`: Error de encriptación

### PUT /api/config/selected
**Actualizar configuración seleccionada**

**Request Body**:
```json
{
  "provider_id": "cerebras",
  "main_model": "zai-glm-4.6",
  "small_model": "gpt-oss-120b"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Selected configuration updated successfully"
}
```

### PUT /api/config/ui
**Actualizar configuración de UI**

**Request Body**:
```json
{
  "left_sidebar_collapsed": false,
  "right_sidebar_collapsed": false,
  "bottom_panel_collapsed": true,
  "theme_mode": "dark"
}
```

**Response**:
```json
{
  "success": true,
  "message": "UI configuration updated successfully"
}
```

### POST /api/config/reset
**Resetear configuración a valores por defecto**

**Response**:
```json
{
  "success": true,
  "message": "Configuration reset functionality not yet implemented"
}
```

**Status**: No implementado completamente

---

## 💬 Chat Endpoints

**Prefix**: `/api/chat`

### POST /api/chat/completions
**Chat completion simple (sin streaming)**

**Request Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Explica qué es la IA"
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response**:
```json
{
  "response": "La inteligencia artificial es...",
  "model": "zai-glm-4.6",
  "provider": "cerebras",
  "message_count": 1
}
```

**Errors**:
- `400`: No hay provider o modelo configurado
- `404`: Provider no encontrado
- `500`: Error de comunicación con LLM

### POST /api/chat/completions/stream ⚡
**Chat completion con streaming (SSE)**

**Request Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Calcula 15 * 24 + 8"
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response**: Server-Sent Events (SSE)

**Headers**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
```

#### Event Types

##### Start Event
```
data: {"type": "start"}
```

##### Reasoning Chunk
```
data: {
  "type": "reasoning_chunk",
  "content": "Analyzing the math problem...",
  "accumulated_reasoning": "Full reasoning so far..."
}
```

##### Content Chunk
```
data: {
  "type": "content_chunk",
  "content": "The result is",
  "accumulated_content": "Full content so far..."
}
```

##### Tool Call Start
```
data: {
  "type": "tool_call_start",
  "tool_call_id": "call_123",
  "function_name": "calculate"
}
```

##### Tool Call Arguments
```
data: {
  "type": "tool_call_arguments",
  "tool_call_id": "call_123",
  "arguments": "15 * 24 + 8",
  "full_arguments": "15 * 24 + 8"
}
```

##### Tool Execution Start
```
data: {
  "type": "tool_execution_start",
  "tool_call_id": "call_123",
  "function_name": "calculate"
}
```

##### Tool Execution Complete
```
data: {
  "type": "tool_execution_complete",
  "tool_result": {
    "tool_call_id": "call_123",
    "name": "calculate",
    "content": "368",
    "status": "success",
    "execution_time": 0.1234
  }
}
```

##### Tool Execution Error
```
data: {
  "type": "tool_execution_error",
  "tool_result": {
    "tool_call_id": "call_123",
    "name": "calculate",
    "content": "Error: Invalid expression",
    "status": "error"
  }
}
```

##### Complete Event
```
data: {
  "type": "complete",
  "final_content": "The result is 368",
  "final_reasoning": "Full reasoning...",
  "tool_calls": [...],
  "tool_results": [...],
  "model": "zai-glm-4.6",
  "provider": "cerebras",
  "message_count": 1
}
```

##### Error Event
```
data: {
  "type": "error",
  "error": "Error message"
}
```

##### End Stream
```
data: [DONE]
```

## 🛠️ Tool Calls Integration

### Default Tools Available
Todos los requests de chat incluyen automáticamente estas herramientas:

1. **calculate**
   - Descripción: "Perform mathematical calculations"
   - Parámetros: `expression` (string)

2. **get_current_time**
   - Descripción: "Get the current time and date"
   - Parámetros: `timezone` (string, opcional)

3. **search_web**
   - Descripción: "Search the web for information"
   - Parámetros: `query` (string)

4. **get_weather**
   - Descripción: "Get weather information for a location"
   - Parámetros: `location` (string)

### Tool Choice Strategy
- **Default**: `"auto"` - El modelo decide cuándo usar tools
- **Alternativas**: `"none"`, `"required"`, o tool específico

## 📄 Data Models

### ChatMessage
```typescript
{
  role: "user" | "assistant" | "system" | "tool",
  content?: string,
  tool_calls?: ToolCall[],
  tool_call_id?: string,  // Para mensajes de tool
  name?: string           // Nombre del tool
}
```

### ToolCall
```typescript
{
  id: string,
  type: "function",
  function: {
    name: string,
    arguments: string  // JSON string
  }
}
```

### ToolResult
```typescript
{
  tool_call_id: string,
  name: string,
  content: string,
  status: "success" | "error",
  execution_time?: number
}
```

## 🔒 Security Headers

Todos los endpoints incluyen:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

## 📊 Status Codes

- **200**: Success
- **400**: Bad Request (datos inválidos, configuración faltante)
- **404**: Not Found (provider/modelo no encontrado)
- **500**: Internal Server Error (errores de sistema, APIs externas)

## 🔄 Error Handling

### Standard Error Response
```json
{
  "detail": "Error message"
}
```

### Common Errors
- "No provider configured"
- "No main model configured"
- "Provider not found"
- "No API key configured for {provider}"
- "Failed to fetch models from provider"