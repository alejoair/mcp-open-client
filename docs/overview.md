# Visión General de la Arquitectura

## Arquitectura General

MCP Open Client es una aplicación web que actúa como cliente universal para múltiples proveedores de LLM (Large Language Models). Su arquitectura está dividida en backend (FastAPI/Python) y frontend (HTML/JavaScript).

## Componentes Principales del Backend

### 🏗️ Arquitectura en Capas

```
┌─────────────────────────────────────┐
│           Frontend (UI)             │
│     HTML/JS + Components            │
└─────────────┬───────────────────────┘
              │ HTTP/REST API
┌─────────────▼───────────────────────┐
│          API Layer                  │
│    FastAPI Routes & Models          │
├─────────────────────────────────────┤
│        Services Layer               │
│   ChatClient + ToolSimulator        │
├─────────────────────────────────────┤
│     Configuration Layer             │
│       ConfigManager                 │
├─────────────────────────────────────┤
│        Provider Layer               │
│   OpenAI, Anthropic, Cerebras...    │
└─────────────────────────────────────┘
```

### 🔧 Componentes Core

#### **ConfigManager**
- **Ubicación**: `mcp_open_client/config/config_manager.py`
- **Responsabilidad**: Gestión centralizada de toda la configuración
- **Funciones**:
  - Gestión de providers LLM
  - Configuración seleccionada (provider + modelos)
  - Encriptación/desencriptación de API keys
  - Configuración de UI
  - Persistencia en JSON

#### **FastAPI Application**
- **Ubicación**: `mcp_open_client/server/app.py`
- **Responsabilidad**: Servidor web principal
- **Funciones**:
  - Configuración CORS
  - Registro de rutas
  - Servicio de archivos estáticos
  - Middleware de manejo de errores

#### **ChatClient**
- **Ubicación**: `mcp_open_client/services/chat_client.py`
- **Responsabilidad**: Cliente HTTP para proveedores LLM
- **Funciones**:
  - Comunicación con APIs de LLM
  - Streaming de respuestas (SSE)
  - Manejo de tool calls
  - Gestión de contexto de conversación

#### **ToolSimulator**
- **Ubicación**: `mcp_open_client/services/tool_simulator.py`
- **Responsabilidad**: Simulación de herramientas durante desarrollo
- **Funciones**:
  - Ejecución simulada de tools
  - Delays realistas
  - Manejo de errores
  - Preparación para integración MCP

### 🛣️ Flujo de Datos Principal

#### Chat Request Flow
1. **Frontend** envía request a `/api/chat/completions/stream`
2. **Chat Route** valida y obtiene configuración
3. **ConfigManager** proporciona provider y API key
4. **ChatClient** se conecta al proveedor LLM
5. **Streaming Response** se devuelve al frontend vía SSE
6. **Tool Calls** (si los hay) se procesan con **ToolSimulator**

#### Configuration Flow
1. **Frontend** solicita configuración vía `/api/config/*`
2. **Config Routes** procesan requests
3. **ConfigManager** lee/escribe configuración
4. **Encryption** protege API keys
5. **JSON File** persiste la configuración

## Características Arquitectónicas

### ✅ Fortalezas
- **Modular**: Separación clara de responsabilidades
- **Extensible**: Fácil agregar nuevos providers
- **Seguro**: Encriptación de API keys
- **Real-time**: Streaming de respuestas
- **Configurable**: Sistema de configuración flexible

### 🔄 Patrones Implementados
- **Singleton**: ConfigManager global
- **Factory**: Creación de clientes por provider
- **Strategy**: Diferentes implementaciones por provider
- **Observer**: Streaming con SSE
- **Adapter**: Abstracción de diferentes APIs LLM

### 🚀 Tecnologías Utilizadas
- **FastAPI**: Framework web moderno
- **Pydantic**: Validación y serialización de datos
- **Cryptography**: Encriptación de datos sensibles
- **aiohttp**: Cliente HTTP asíncrono
- **Server-Sent Events**: Streaming en tiempo real

## Integraciones Externas

### 🤖 Proveedores LLM Soportados
- **OpenAI** (GPT models)
- **Anthropic** (Claude models)
- **Cerebras** (zai-glm models)
- **Extensible** para nuevos proveedores

### 🛠️ Tool Call System
- **Detección**: Automática en streaming
- **Ejecución**: Simulada (preparado para MCP)
- **Resultado**: Integrado en conversación
- **Formato**: Compatible con OpenAI

## Estado Actual vs Futuro

### ✅ Implementado
- Gestión de múltiples providers
- Chat streaming con tool calls
- Sistema de configuración robusto
- UI funcional y responsive

### 🚧 En Desarrollo/Planeado
- Integración real con MCP
- Configuración avanzada de modelos
- Sistema de plugins
- Historial de conversaciones