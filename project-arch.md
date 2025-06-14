# MCP Open Client - Arquitectura del Proyecto

## ¿Qué es MCP Open Client?

**MCP Open Client** es una aplicación que implementa el **Model Context Protocol (MCP)** para permitir que los LLMs interactúen de forma segura con herramientas externas, datos y servicios. Es como **"USB-C para IA"** - una interfaz universal para conectar cualquier LLM compatible con cualquier fuente de datos o herramienta.

### Arquitectura MCP en el Proyecto
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Client    │◄──►│   MCP Client    │◄──►│  MCP Servers    │
│ (LLM Interface) │    │  (Protocol)     │    │  (FastMCP)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Estructura General

```
mcp_open_client/
├── api_client.py          # Cliente API para comunicación con modelos de IA (LLM)
├── mcp_client.py          # Cliente MCP para conectar con servidores MCP
├── main.py                # Punto de entrada principal
├── cli.py                 # Interfaz de línea de comandos
├── settings/              # Configuraciones
│   ├── app-styles.css
│   ├── mcp-config.json
│   └── user-settings.json
└── ui/                    # Interfaz de usuario
    ├── chat_handlers.py   # Manejadores de eventos de chat
    ├── chat_interface.py  # Interfaz principal de chat
    ├── chat_window.py
    ├── configure.py
    ├── conversation_manager.py
    ├── home.py
    ├── mcp_servers.py
    └── message_parser.py
```

## Componentes Principales

### 1. API Client (LLM Interface)
**Propósito**: Maneja la comunicación con modelos de IA (LLMs) para generar respuestas de chat.

### 2. MCP Client (Protocol Handler)
**Propósito**: Implementa el protocolo MCP para conectar con servidores MCP que exponen herramientas y recursos.

### 3. UI Components
**Propósito**: Interfaz de usuario construida con NiceGUI para interacción del usuario.

## API Client - Uso y Arquitectura

### 1. Definición del API Client

**Archivo**: `mcp_open_client/api_client.py`

```python
class APIClient:
    def __init__(
        self,
        base_url: str = "http://192.168.58.101:8123",
        api_key: str = "sisas",
        model: str = "claude-3-5-sonnet",
        max_retries: int = 10,
        timeout: float = 60.0
    ):
```

**Características**:
- Utiliza `AsyncOpenAI` para comunicación asíncrona
- Configuración por defecto para servidor local
- Manejo de errores con `APIClientError`
- Logging detallado para debugging

**Métodos principales**:
- `chat_completion()`: Envía mensajes y recibe respuestas del modelo
- `list_models()`: Lista modelos disponibles en el servidor
- `close()`: Cierra la conexión (placeholder para consistencia)

### 2. Instanciación del API Client

**Archivo**: `mcp_open_client/ui/chat_interface.py`
**Línea**: 16

```python
def create_chat_interface(container):
    # Create an instance of APIClient
    api_client = APIClient()
```

**Contexto**: Se crea una instancia del API Client cuando se inicializa la interfaz de chat.

### 3. Uso del API Client

**Archivo**: `mcp_open_client/ui/chat_handlers.py`
**Función**: `handle_send()`
**Línea**: 211

```python
async def handle_send(input_field, message_container, api_client, scroll_area):
    # ... código de preparación ...
    
    # Envío a la API
    response = await api_client.chat_completion(api_messages)
    bot_response = response['choices'][0]['message']['content']
```

## MCP Client - Uso y Arquitectura

### 1. Definición del MCP Client

**Archivo**: `mcp_open_client/mcp_client.py`

```python
class MCPClientManager:
    def __init__(self):
        self.active_servers = {}
        self.initialized = False
```

**Características**:
- Maneja múltiples servidores MCP simultáneamente
- Conexión asíncrona a servidores via STDIO o HTTP
- Expone herramientas (tools) y recursos (resources) de servidores MCP
- Integración con FastMCP para servidores Python

**Métodos principales**:
- `initialize()`: Conecta a servidores MCP según configuración
- `list_tools()`: Lista todas las herramientas disponibles
- `list_resources()`: Lista todos los recursos disponibles
- `call_tool()`: Ejecuta una herramienta en un servidor MCP
- `read_resource()`: Lee un recurso de un servidor MCP

### 2. Configuración de Servidores MCP

**Archivo**: `settings/mcp-config.json`

Configuración estándar MCPConfig para múltiples servidores:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["-m", "mcp_server_filesystem", "/path/to/directory"],
      "env": {"DEBUG": "true"}
    },
    "weather": {
      "url": "https://weather-api.example.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

## Flujo de Comunicación

### 1. Flujo Completo: Usuario → LLM → MCP

```
Usuario escribe mensaje
    ↓
chat_interface.py (captura evento)
    ↓
chat_handlers.py (handle_send)
    ↓
api_client.py (chat_completion) ──→ LLM procesa y decide usar herramientas
    ↓                                    ↓
Respuesta del modelo ←──────────── mcp_client.py (call_tool/read_resource)
    ↓                                    ↓
Renderizado en UI ←─────────────── Servidor MCP (FastMCP/otros)
```

### 2. Flujo de Mensajes de Chat (Solo LLM)

```
Usuario escribe mensaje
    ↓
chat_interface.py (captura evento)
    ↓
chat_handlers.py (handle_send)
    ↓
api_client.py (chat_completion)
    ↓
Servidor de IA (procesamiento)
    ↓
Respuesta del modelo
    ↓
Renderizado en UI
```

### 3. Flujo de Herramientas MCP

```
LLM decide usar herramienta
    ↓
mcp_client.py (call_tool)
    ↓
Servidor MCP (FastMCP)
    ↓
@mcp.tool function ejecutada
    ↓
Resultado retornado al LLM
    ↓
LLM incorpora resultado en respuesta
```

### 4. Configuración del API Client

**Configuración por defecto**:
- **Base URL**: `http://192.168.58.101:8123`
- **API Key**: `"sisas"`
- **Modelo**: `"claude-3-5-sonnet"`
- **Max Retries**: 10
- **Timeout**: 60.0 segundos

### 5. Configuración del MCP Client

**Configuración dinámica** desde `settings/mcp-config.json`:
- **Servidores STDIO**: Para herramientas locales (filesystem, git, etc.)
- **Servidores HTTP**: Para servicios remotos (APIs, microservicios)
- **Múltiples servidores**: Cada uno expone diferentes capacidades

### 3. Manejo de Errores

El API Client implementa manejo robusto de errores:

```python
try:
    response = await self._client.chat.completions.create(**params)
    return response.model_dump()
except openai.OpenAIError as e:
    error_msg = f"OpenAI API error in chat completion: {str(e)}"
    logger.error(error_msg)
    raise APIClientError(error_msg) from e
except Exception as e:
    error_msg = f"Unexpected error in chat completion: {str(e)}"
    logger.error(error_msg)
    raise APIClientError(error_msg) from e
```

## Integración con la UI

### 1. Paso de Parámetros

El `api_client` se pasa como parámetro a través de la cadena de funciones:

```python
# En chat_interface.py
async def send_message():
    await handle_send(text_input, message_container, api_client, scroll_area)

# En chat_handlers.py
async def handle_send(input_field, message_container, api_client, scroll_area):
    # Uso del api_client aquí
```

### 2. Formato de Mensajes

Los mensajes se convierten al formato esperado por la API:

```python
api_messages = []
for msg in conversation_messages:
    api_messages.append({
        "role": msg["role"],      # 'user' o 'assistant'
        "content": msg["content"] # Contenido del mensaje
    })
```

## Funcionalidades Avanzadas

### 1. Soporte para Streaming

El API Client incluye soporte para respuestas en streaming:

```python
if stream:
    logger.info("Streaming mode requested")
    stream_resp = await self._client.chat.completions.create(**params)
    # Placeholder para implementación de streaming
    return {"choices": [{"message": {"content": "Streaming response placeholder"}}]}
```

### 2. Parámetros Configurables

Soporte para parámetros avanzados del modelo:

- `temperature`: Control de creatividad (0-2)
- `max_tokens`: Límite de tokens de respuesta
- `top_p`: Nucleus sampling
- `frequency_penalty`: Penalización por frecuencia
- `presence_penalty`: Penalización por presencia
- `stop`: Secuencias de parada

### 3. Logging Detallado

Sistema de logging completo para debugging:

```python
logger.info(f"Creating chat completion with model: {model_to_use}")
logger.info("Chat completion successful")
logger.error(error_msg)
```

## Integración MCP + LLM

### 1. Cómo el LLM Usa Herramientas MCP

El LLM puede decidir automáticamente usar herramientas MCP basado en:

- **Descripción de herramientas**: Cada `@mcp.tool` tiene descripción que el LLM entiende
- **Parámetros tipados**: El LLM sabe qué parámetros necesita cada herramienta
- **Contexto de conversación**: El LLM decide cuándo una herramienta es relevante

Ejemplo de herramienta MCP que el LLM puede usar:

```python
@mcp.tool
def analizar_archivo(ruta: str, incluir_contenido: bool = False) -> dict:
    """Analiza un archivo y proporciona estadísticas detalladas."""
    return {
        "ruta": ruta,
        "tamaño_bytes": 2048,
        "lineas": 45,
        "palabras": 320,
        "tipo": "texto"
    }
```

### 2. Recursos MCP para Contexto

Los recursos MCP proporcionan información de solo lectura que el LLM puede consultar:

```python
@mcp.resource("config://app/settings")
def obtener_configuracion() -> dict:
    """Configuración actual de la aplicación."""
    return {"version": "1.0", "debug": True}
```

## Consideraciones de Arquitectura

### 1. Separación de Responsabilidades

- **api_client.py**: Comunicación con LLMs (OpenAI-compatible APIs)
- **mcp_client.py**: Comunicación con servidores MCP (herramientas y recursos)
- **chat_handlers.py**: Lógica de manejo de eventos y orquestación
- **chat_interface.py**: Renderizado de UI
- **conversation_manager.py**: Gestión de conversaciones

### 2. Asincronía

Todo el flujo de comunicación es asíncrono para mantener la UI responsiva:

```python
async def handle_send(...)
async def chat_completion(...)
async def call_tool(...)
async def read_resource(...)
```

### 3. Manejo de Estado

- **API Client**: Mantiene conexión con LLM
- **MCP Client**: Mantiene conexiones activas con múltiples servidores MCP
- **Conversation Manager**: Gestiona historial de conversaciones
- **UI State**: Maneja estado de la interfaz de usuario

### 4. Protocolo MCP

El proyecto implementa el estándar MCP que permite:

- **Interoperabilidad**: Cualquier servidor MCP puede conectarse
- **Extensibilidad**: Nuevas herramientas se agregan sin modificar el cliente
- **Seguridad**: Protocolo controlado para acceso a recursos externos
- **Estandarización**: Interfaz universal para herramientas de IA

## Puntos de Extensión

### 1. Múltiples Proveedores de LLM

La arquitectura permite fácilmente agregar soporte para múltiples proveedores de IA modificando la clase `APIClient`.

### 2. Nuevos Servidores MCP

Agregar nuevos servidores MCP es tan simple como:

1. **Crear servidor FastMCP**:
```python
from fastmcp import FastMCP

mcp = FastMCP("mi-servidor")

@mcp.tool
def nueva_herramienta(param: str) -> str:
    return f"Procesado: {param}"

if __name__ == "__main__":
    mcp.run()
```

2. **Agregar a configuración**:
```json
{
  "mcpServers": {
    "mi-servidor": {
      "command": "python",
      "args": ["mi_servidor.py"]
    }
  }
}
```

### 3. Configuración Dinámica

- **API Client**: Parámetros configurables desde UI o archivos
- **MCP Servers**: Configuración dinámica via `mcp-config.json`
- **UI Components**: Temas y estilos configurables

### 4. Plugins y Extensiones

La separación clara de responsabilidades facilita:

- **Nuevos tipos de herramientas MCP**
- **Diferentes transportes de comunicación**
- **Múltiples interfaces de usuario**
- **Integración con otros protocolos**

## Funcionalidad de Cliente MCP - Interfaz de Gestión

### 1. Archivo: `mcp_open_client/ui/mcp_servers.py`

**Propósito**: Proporciona una interfaz gráfica completa para gestionar servidores MCP, permitiendo agregar, editar, eliminar y configurar servidores de forma visual.

### 2. Funcionalidades Principales

#### A. Gestión de Configuración
```python
def save_config_to_file(config: Dict[str, Any]) -> bool:
    """Save the MCP configuration to the file system"""
```

**Características**:
- Guarda configuración en `mcp_open_client/settings/mcp-config.json`
- Sincronización entre almacenamiento de usuario y archivo del sistema
- Manejo de errores con notificaciones visuales

#### B. Visualización de Servidores
```python
def show_content(container):
    """Main function to display the MCP servers management UI"""
```

**Interfaz visual incluye**:
- **Grid de tarjetas**: Cada servidor se muestra en una tarjeta individual
- **Indicadores de estado**: Activo/Deshabilitado con badges de color
- **Tipos de servidor**: HTTP (nube) vs Local (computadora) con iconos
- **Detalles expandibles**: Información completa de configuración

#### C. Tipos de Servidores Soportados

**1. Servidores HTTP/Remotos**:
```json
{
  "weather": {
    "url": "https://weather-api.example.com/mcp",
    "transport": "streamable-http"
  }
}
```

**2. Servidores Locales/STDIO**:
```json
{
  "filesystem": {
    "command": "python",
    "args": ["-m", "mcp_server_filesystem", "/path/to/directory"],
    "env": {"DEBUG": "true"}
  }
}
```

### 3. Operaciones CRUD Completas

#### A. Crear Servidor (`show_add_dialog`)
**Funcionalidades**:
- Formulario dinámico que cambia según tipo de servidor
- Validación de campos requeridos
- Soporte para variables de entorno
- Configuración de argumentos de línea de comandos

**Campos para servidor HTTP**:
- URL del servidor
- Tipo de transporte (streamable-http, http)

**Campos para servidor Local**:
- Comando a ejecutar
- Argumentos (separados por espacios)
- Variables de entorno (formato key=value)

#### B. Leer/Visualizar Servidores (`refresh_servers_list`)
**Características**:
- Actualización automática de la lista
- Detección automática del tipo de servidor
- Indicadores visuales de estado
- Información detallada en paneles expandibles

#### C. Actualizar Servidor (`show_edit_dialog`)
**Funcionalidades**:
- Preserva el estado habilitado/deshabilitado
- Formulario pre-poblado con valores actuales
- Validación de cambios
- Actualización en tiempo real del cliente MCP

#### D. Eliminar Servidor (`show_delete_dialog`)
**Características**:
- Diálogo de confirmación
- Eliminación segura con advertencias
- Actualización automática de conexiones MCP

### 4. Gestión de Estado de Servidores

#### A. Toggle de Estado (`toggle_server_status`)
```python
def toggle_server_status(server_name, is_active):
    """Toggle a server's active status"""
```

**Funcionalidades**:
- Habilitar/deshabilitar servidores sin eliminarlos
- Actualización inmediata del cliente MCP
- Notificaciones de estado
- Persistencia en archivo de configuración

#### B. Integración con MCP Client Manager
```python
async def update_mcp_client():
    try:
        success = await mcp_client_manager.initialize(current_config)
        if success:
            active_servers = mcp_client_manager.get_active_servers()
            app.storage.user['mcp_status'] = f"Connected to {len(active_servers)} MCP servers"
```

**Características**:
- Reinicialización automática del cliente MCP
- Actualización de estado en tiempo real
- Manejo de errores de conexión
- Feedback visual del estado de conexión

### 5. Funcionalidades Avanzadas

#### A. Reset a Configuración por Defecto (`reset_to_default`)
**Propósito**: Restaurar configuración desde archivo de respaldo
**Uso**: Recuperación rápida de configuración conocida

#### B. Persistencia Dual
**Storage de Usuario**: Para estado de sesión
**Archivo JSON**: Para persistencia entre sesiones

#### C. Validación de Configuración
- Campos requeridos según tipo de servidor
- Formato de variables de entorno
- Validación de URLs para servidores HTTP

### 6. Flujo de Trabajo Típico

```
1. Usuario abre interfaz MCP Servers
   ↓
2. Sistema carga configuración desde storage/archivo
   ↓
3. Muestra grid de servidores existentes
   ↓
4. Usuario puede:
   - Agregar nuevo servidor → Formulario dinámico
   - Editar servidor existente → Formulario pre-poblado
   - Habilitar/deshabilitar → Toggle inmediato
   - Eliminar servidor → Confirmación + eliminación
   ↓
5. Cada cambio actualiza:
   - Storage de usuario
   - Archivo de configuración
   - Cliente MCP (reconexión)
   - Interfaz visual
```

### 7. Integración con el Ecosistema

#### A. Conexión con MCP Client Manager
- Reinicialización automática tras cambios
- Sincronización de estado de servidores activos
- Manejo de errores de conexión

#### B. Persistencia de Configuración
- Archivo: `mcp_open_client/settings/mcp-config.json`
- Formato estándar MCPConfig compatible con Claude Desktop
- Backup automático en user storage

#### C. Feedback Visual
- Notificaciones toast para acciones
- Badges de estado en tiempo real
- Indicadores de tipo de servidor
- Paneles expandibles para detalles

## Ventajas del Diseño MCP

### 1. Modularidad
Cada servidor MCP es independiente y puede desarrollarse por separado.

### 2. Reutilización
Las herramientas MCP pueden ser usadas por cualquier LLM compatible.

### 3. Seguridad
El protocolo MCP controla qué herramientas puede usar el LLM.

### 4. Escalabilidad
Nuevas capacidades se agregan creando nuevos servidores MCP, no modificando el cliente.

### 5. Estándar Abierto
Compatible con cualquier implementación del protocolo MCP (Claude Desktop, otros clientes).

### 6. Gestión Visual Intuitiva
La interfaz `mcp_servers.py` hace que la gestión de servidores MCP sea accesible para usuarios no técnicos.

### 7. Configuración Flexible
Soporte tanto para servidores remotos (HTTP) como locales (STDIO) con configuración unificada.

### 8. Actualizaciones en Tiempo Real
Los cambios en la configuración se reflejan inmediatamente en las conexiones MCP activas.