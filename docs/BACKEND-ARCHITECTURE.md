# 🏗️ MCP Open Client - Backend Architecture Overview

## 📋 **Core Server Infrastructure**

### `server/app.py`
- **FastAPI application setup** - Main ASGI app creation and middleware
- **CORS configuration** - Cross-origin handling for frontend
- **Route registration** - Mounts all API routes
- **Static file serving** - Serves UI assets

### `server/models.py`
- **Pydantic data models** - Request/response validation
- **ChatMessage, ChatCompletionRequest, ChatCompletionResponse**
- **Type safety** for API contracts

## 🌐 **API Routes Layer**

### `server/routes/config.py`
- **Configuration management API** - Provider settings, model selection
- **GET/PUT endpoints** - Read/write configuration
- **Provider discovery** - Available LLM providers and models
- **API key management** - Encrypted storage/retrieval

### `server/routes/chat.py` ⭐ **CORE CHAT ENGINE**
- **Main chat endpoints** - `/api/chat/completions` and `/stream`
- **Request validation** - Message format, provider checks
- **Streaming coordinator** - SSE event orchestration
- **Tool call delegation** - Hands off to ToolCallHandler
- **Event broadcasting** - Real-time updates to frontend

## 🔧 **Service Layer**

### `services/chat_client.py` 📡 **LLM CONNECTOR**
- **Universal LLM interface** - Abstracts provider differences
- **HTTP client management** - Connection pooling, timeouts
- **Streaming response parsing** - Real-time chunk processing
- **Provider-specific adapters** - Handles different API formats
- **Error handling** - Network failures, rate limits

### `services/tool_call_handler.py` 🔄 **TOOL ORCHESTRATOR**
- **Recursive tool execution** - Multi-round tool calling
- **Loop prevention** - Max iteration limits (default: 5)
- **Event streaming** - Progress updates via SSE
- **Special tool handling** - `respond_to_user` content propagation
- **Error recovery** - Graceful failure handling

### `services/tool_simulator.py` 🛠️ **TOOL IMPLEMENTATIONS**
- **Built-in tool execution** - Math, time, weather, web search
- **Realistic simulation** - Delays, error scenarios
- **Tool registry** - Dynamic tool discovery
- **Future MCP bridge** - Preparatory interface

### `services/default_tools.py` ⚙️ **TOOL DEFINITIONS**
- **Tool schema configuration** - Function signatures, descriptions
- **Tool catalog** - Available tools for model selection
- **Modular tool registry** - Easy addition/removal

## 💾 **Configuration Layer**

### `config/config_manager.py`
- **Settings persistence** - JSON configuration storage
- **Provider management** - API keys, endpoints, models
- **Encryption/decryption** - Secure credential handling
- **Configuration validation** - Schema enforcement

### `config/__init__.py`
- **Configuration loading** - App startup initialization
- **Default settings** - Fallback configurations

## 🔌 **Legacy/Compatibility**

### `services/provider_client.py`
- **Legacy provider interface** - Backward compatibility
- **Migration bridge** - Transition to new ChatClient

## 📦 **Utilities**

### `cli.py`
- **Command-line interface** - Server startup, configuration
- **Development tools** - Debug modes, hot reload

### `__about__.py` & `__init__.py`
- **Package metadata** - Version, author info
- **Module initialization** - Import setup

---

## 🌊 **Data Flow Architecture**

1. **Request Entry** → `routes/chat.py` validates and routes
2. **LLM Communication** → `chat_client.py` handles provider calls
3. **Tool Detection** → Tool calls extracted from LLM response
4. **Tool Execution** → `tool_call_handler.py` orchestrates recursive execution
5. **Tool Implementation** → `tool_simulator.py` executes actual tools
6. **Response Assembly** → Results combined and streamed back
7. **Frontend Updates** → SSE events update UI in real-time

## 🎯 **Key Design Principles**

- **Modular separation** - Each service has single responsibility
- **Event-driven** - Real-time streaming via SSE
- **Provider agnostic** - Unified interface for all LLM providers
- **Tool extensibility** - Easy addition of new capabilities
- **Error resilience** - Graceful degradation and recovery
- **Development friendly** - Hot reload, detailed logging

## 📊 **File Responsibilities Matrix**

| Component | Responsibility | Key Functions |
|-----------|----------------|---------------|
| `app.py` | Server bootstrap | FastAPI setup, middleware, routing |
| `models.py` | Data validation | Pydantic models, type safety |
| `routes/chat.py` | Chat API | Streaming, tool coordination, SSE |
| `routes/config.py` | Configuration API | Settings CRUD, provider management |
| `chat_client.py` | LLM communication | HTTP client, response parsing |
| `tool_call_handler.py` | Tool orchestration | Recursive execution, event streaming |
| `tool_simulator.py` | Tool execution | Built-in tools, simulation layer |
| `default_tools.py` | Tool definitions | Schema, catalog, registry |
| `config_manager.py` | Settings management | Persistence, encryption, validation |

## 🔧 **Recent Refactoring Improvements**

### Tool Calling System (Latest)
- ✅ **Separated tool concerns** - Clean separation between routing and tool logic
- ✅ **Added recursive tool calling** - Multi-round tool execution support
- ✅ **Fixed event mismatch** - Backend/frontend event synchronization
- ✅ **Added respond_to_user tool** - Eliminates inappropriate tool usage
- ✅ **Improved error handling** - Graceful degradation and recovery

### Architecture Benefits
- **Maintainability** - Clear separation of concerns
- **Testability** - Isolated components for unit testing
- **Extensibility** - Easy addition of new tools and providers
- **Reliability** - Robust error handling and recovery
- **Performance** - Efficient streaming and resource management