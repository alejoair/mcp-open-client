# Estructura del Proyecto

## Organización de Directorios

```
mcp-open-client/
├── 📁 docs/                          # Documentación de arquitectura
├── 📁 mcp_open_client/               # Código fuente principal
│   ├── 📄 __init__.py
│   ├── 📄 __about__.py               # Metadata del proyecto
│   ├── 📄 cli.py                     # Interfaz de línea de comandos
│   ├── 📁 config/                    # Sistema de configuración
│   │   ├── 📄 __init__.py
│   │   ├── 📄 config_manager.py      # [CORE] Gestión centralizada de configuración
│   │   ├── 📄 app_config.json        # Archivo de configuración persistente
│   │   └── 📄 .encryption_key        # Clave de encriptación (auto-generada)
│   ├── 📁 server/                    # Servidor web FastAPI
│   │   ├── 📄 __init__.py
│   │   ├── 📄 app.py                 # [CORE] Aplicación FastAPI principal
│   │   ├── 📄 models.py              # [CORE] Modelos Pydantic
│   │   └── 📁 routes/                # Endpoints REST API
│   │       ├── 📄 __init__.py
│   │       ├── 📄 chat.py            # [CORE] Rutas de chat y streaming
│   │       └── 📄 config.py          # [CORE] Rutas de configuración
│   ├── 📁 services/                  # Servicios de backend
│   │   ├── 📄 __init__.py
│   │   ├── 📄 chat_client.py         # [CORE] Cliente para proveedores LLM
│   │   ├── 📄 tool_simulator.py      # [CORE] Simulador de herramientas
│   │   └── 📄 provider_client.py     # Cliente genérico para providers
│   └── 📁 ui/                        # Frontend web
│       ├── 📄 index.html             # Página principal
│       └── 📁 components/            # Componentes JavaScript
│           ├── 📄 TerminalHeader.js  # Header de la aplicación
│           ├── 📄 LeftBar.js         # [CORE] Panel de configuración
│           ├── 📄 RightBar.js        # Panel lateral derecho
│           ├── 📄 MainContent.js     # Contenido principal
│           ├── 📄 ChatWindow.js      # [CORE] Interface de chat
│           ├── 📄 ChatInput.js       # Input de mensajes
│           └── 📄 BottomBar.js       # Barra inferior
├── 📄 pyproject.toml                 # Configuración del proyecto Python
├── 📄 README.md                      # Documentación principal
└── 📄 .gitignore                     # Archivos ignorados por git
```

## Archivos Core (Críticos)

### 🔧 Backend Core
- **`config_manager.py`** - Gestión centralizada de toda la configuración
- **`app.py`** - Servidor FastAPI y configuración CORS
- **`models.py`** - Modelos de datos Pydantic para API
- **`chat.py`** - Endpoints de chat con streaming y tool calls
- **`config.py`** - Endpoints de configuración
- **`chat_client.py`** - Cliente HTTP para providers LLM
- **`tool_simulator.py`** - Simulación de herramientas

### 🎨 Frontend Core
- **`LeftBar.js`** - Panel de configuración de providers y modelos
- **`ChatWindow.js`** - Interface principal de chat con streaming
- **`ChatInput.js`** - Input de mensajes del usuario

## Descripción de Componentes

### 📁 config/
**Propósito**: Gestión centralizada de configuración

#### 📄 config_manager.py
- **Clases**: `ConfigManager`
- **Responsabilidades**:
  - Carga y persistencia de configuración
  - Gestión de providers LLM
  - Encriptación/desencriptación de API keys
  - Configuración de UI
  - Configuración seleccionada (provider + modelos)
- **Patrón**: Singleton global (`config_manager`)

#### 📄 app_config.json
```json
{
  "app": { "name": "MCP Open Client", "version": "1.0.0" },
  "providers": [...],
  "selected_configuration": {...},
  "ui": {...},
  "mcp": {...}
}
```

### 📁 server/
**Propósito**: API REST y modelos de datos

#### 📄 app.py
- **Framework**: FastAPI
- **Funcionalidades**:
  - Configuración CORS
  - Registro de rutas (`/api/chat`, `/api/config`)
  - Servicio de archivos estáticos
  - Punto de entrada del servidor

#### 📄 models.py
- **Modelos principales**:
  - `ChatMessage`, `ToolCall`, `ToolResult`
  - `ChatCompletionRequest/Response`
  - `ProviderModel`, `ConfigResponse`
- **Validación**: Pydantic con validación automática

### 📁 server/routes/
**Propósito**: Endpoints REST organizados por funcionalidad

#### 📄 chat.py
- **Endpoints**:
  - `POST /api/chat/completions` - Chat simple
  - `POST /api/chat/completions/stream` - Chat con streaming
- **Características**:
  - Server-Sent Events (SSE)
  - Tool call detection y ejecución
  - Streaming de reasoning/content separado

#### 📄 config.py
- **Endpoints**:
  - `GET /api/config/` - Configuración actual
  - `GET /api/config/providers` - Lista de providers
  - `GET /api/config/providers/{id}/models` - Modelos por provider
  - `PUT /api/config/selected` - Actualizar selección
  - `POST /api/config/providers/{id}/api-key` - Configurar API key

### 📁 services/
**Propósito**: Lógica de negocio y servicios

#### 📄 chat_client.py
- **Clase**: `ChatClient`
- **Responsabilidades**:
  - Cliente HTTP asíncrono (aiohttp)
  - Comunicación con diferentes providers LLM
  - Streaming de respuestas
  - Manejo de tool calls
  - Context manager para gestión de conexiones

#### 📄 tool_simulator.py
- **Clase**: `ToolSimulator`
- **Herramientas simuladas**:
  - `calculate` - Operaciones matemáticas
  - `get_current_time` - Tiempo actual
  - `search_web` - Búsqueda simulada
  - `get_weather` - Clima simulado
  - `read_file`, `write_file` - Operaciones de archivo

### 📁 ui/components/
**Propósito**: Componentes del frontend

#### 📄 LeftBar.js
- **Funcionalidades**:
  - Selección de provider LLM
  - Configuración de API keys
  - Selección de modelos (main/small)
  - Carga dinámica de modelos por provider

#### 📄 ChatWindow.js
- **Funcionalidades**:
  - Display de mensajes de chat
  - Streaming en tiempo real
  - Separación de reasoning/content
  - Manejo de tool calls y resultados
  - Interface responsive con scroll automático

## Flujo de Archivos

### Chat Request Flow
```
ChatInput.js → ChatWindow.js → /api/chat/completions/stream
                                      ↓
chat.py → chat_client.py → Provider API → Streaming Response
    ↓                           ↓
tool_simulator.py ← tool_calls ←┘
```

### Configuration Flow
```
LeftBar.js → /api/config/* → config.py → config_manager.py
                                              ↓
                                         app_config.json
```

## Convenciones de Nombres

- **Archivos**: `snake_case.py`
- **Clases**: `PascalCase`
- **Funciones/métodos**: `snake_case()`
- **Endpoints**: `/api/resource/action`
- **Variables JS**: `camelCase`
- **Componentes JS**: `PascalCase.js`