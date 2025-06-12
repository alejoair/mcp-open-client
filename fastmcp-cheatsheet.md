# FastMCP Cheatsheet

## 🚀 ¿Qué es MCP y FastMCP?

**Model Context Protocol (MCP)** es un estándar abierto que permite a los LLMs interactuar de forma segura con herramientas externas, datos y servicios. Es como **"USB-C para IA"** - una interfaz universal para conectar cualquier LLM compatible con cualquier fuente de datos o herramienta.

**FastMCP** es un framework de Python que elimina toda la complejidad del protocolo MCP, permitiéndote crear servidores MCP escribiendo funciones Python normales.

### ¿Cómo funciona MCP?
1. **Servidor MCP**: Expone herramientas y datos a través del protocolo
2. **Cliente MCP**: LLMs o aplicaciones que consumen estos recursos
3. **Transporte**: Cómo se comunican (STDIO, HTTP)

### Arquitectura MCP
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Cliente   │◄──►│ Transporte  │◄──►│  Servidor   │
│    (LLM)    │    │ (HTTP/STDIO)│    │  (FastMCP)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🏗️ Servidor Básico

```python
from fastmcp import FastMCP

# Crear servidor
mcp = FastMCP(name="Mi Servidor")

@mcp.tool
def saludar(nombre: str) -> str:
    """Saluda a una persona por su nombre."""
    return f"¡Hola, {nombre}!"

if __name__ == "__main__":
    mcp.run()  # STDIO por defecto
```

## 🔧 Tools (Herramientas)

**¿Qué son?** Functions que el LLM puede ejecutar para realizar acciones. Son como endpoints POST de una API - modifican estado, ejecutan cálculos, o interactúan con sistemas externos.

**¿Cuándo usarlos?** Para cualquier acción que el LLM necesite realizar:
- Cálculos matemáticos
- Consultas a APIs externas
- Modificar bases de datos
- Generar archivos
- Enviar emails

### Tool con Context y Metadatos
```python
from fastmcp import Context

@mcp.tool(
    name="analizar_archivo",
    description="Analiza un archivo y proporciona estadísticas detalladas",
    tags={"archivos", "analisis", "estadisticas"}
)
async def analizar_archivo(ruta: str, incluir_contenido: bool = False, ctx: Context) -> dict:
    """Analiza un archivo y retorna estadísticas completas."""
    await ctx.info(f"Iniciando análisis de {ruta}")
    
    # Simular análisis progresivo
    await ctx.report_progress(25, 100)
    
    # Leer configuración del servidor
    config = await ctx.read_resource("resource://config")
    max_size = config[0].content.get("max_file_size", 1000000)
    
    await ctx.report_progress(50, 100)
    
    # Simular procesamiento
    file_stats = {
        "ruta": ruta,
        "tamaño_bytes": 2048,
        "lineas": 45,
        "palabras": 320,
        "caracteres": 2048,
        "tipo": "texto",
        "encoding": "utf-8"
    }
    
    if incluir_contenido:
        await ctx.debug("Incluyendo contenido del archivo")
        file_stats["preview"] = "Primera línea del archivo..."
    
    await ctx.report_progress(100, 100)
    await ctx.info(f"Análisis completado para {ruta}")
    
    return file_stats
```

## 📄 Resources (Recursos)

**¿Qué son?** Fuentes de datos de solo lectura que el LLM puede consultar. Son como endpoints GET de una API - proporcionan información sin modificar estado.

**¿Cuándo usarlos?** Para exponer datos que el LLM necesita consultar:
- Configuraciones del sistema
- Estados actuales
- Archivos de referencia
- Documentación
- Logs del sistema

**Diferencia con Tools:** Los Resources proporcionan información, los Tools realizan acciones.

### Resource Estático
```python
@mcp.resource("resource://config")
def obtener_config() -> dict:
    """Proporciona la configuración de la aplicación."""
    return {"version": "1.0", "debug": True}
```

### Resource con Metadatos
```python
@mcp.resource(
    uri="data://status",
    name="Estado del Sistema",
    description="Estado operacional actual",
    mime_type="application/json",
    tags={"sistema", "monitoreo"}
)
def estado_sistema() -> dict:
    return {"estado": "operativo", "uptime": 12345}
```

## 🔀 Resource Templates (Plantillas)

**¿Qué son?** Resources dinámicos que generan contenido basado en parámetros en la URI. Permiten crear "familias" de recursos relacionados.

**¿Cuándo usarlos?** Cuando necesitas exponer datos que varían según parámetros:
- Perfiles de usuarios específicos (`users/{id}/profile`)
- Reportes por fecha (`reports/{year}/{month}`)
- Archivos en rutas dinámicas (`files/{path*}`)
- Datos filtrados por categoría

**Cómo funcionan:** El LLM solicita `users://123/profile` → FastMCP llama `perfil_usuario(user_id="123")`

### Template Básico
```python
@mcp.resource("users://{user_id}/profile")
def perfil_usuario(user_id: str) -> dict:
    """Obtiene el perfil de un usuario específico."""
    return {"id": user_id, "nombre": f"Usuario {user_id}"}
```

### Template con Múltiples Parámetros
```python
@mcp.resource("repos://{owner}/{repo}/info")
def info_repositorio(owner: str, repo: str) -> dict:
    """Información de un repositorio GitHub."""
    return {
        "owner": owner,
        "name": repo,
        "full_name": f"{owner}/{repo}"
    }
```

### Template con Wildcards
```python
@mcp.resource("files://{filepath*}")
def contenido_archivo(filepath: str) -> str:
    """Obtiene contenido de cualquier ruta de archivo."""
    return f"Contenido del archivo: {filepath}"
```

## 💬 Prompts

**¿Qué son?** Plantillas de mensajes reutilizables que ayudan a estructurar las instrucciones para el LLM. Son como "snippets" o "macros" para generar prompts consistentes.

**¿Cuándo usarlos?** Para estandarizar interacciones comunes:
- Análisis de código consistentes
- Formatos de respuesta específicos
- Configuraciones de roleplay
- Templates de documentación

**Diferencia con Tools/Resources:** Los Prompts no ejecutan código ni proporcionan datos, generan instrucciones para el LLM.

### Prompt Básico
```python
@mcp.prompt
def analizar_codigo(codigo: str) -> str:
    """Genera prompt para análisis de código."""
    return f"Por favor analiza este código:\n\n{codigo}"
```

### Prompt con Múltiples Mensajes
```python
from fastmcp.prompts.prompt import Message

@mcp.prompt
def roleplay(personaje: str, situacion: str) -> list[Message]:
    """Configura un escenario de roleplay."""
    return [
        Message(f"Eres {personaje}. Situación: {situacion}"),
        Message("Entendido, estoy listo.", role="assistant")
    ]
```

## 🏃 Ejecutar Servidor

**Transportes disponibles:**

### STDIO (Por defecto)
**¿Qué es?** Comunicación a través de entrada/salida estándar
**¿Cuándo usar?** Para herramientas locales y clientes como Claude Desktop
```python
mcp.run()  # Para clientes locales como Claude Desktop
```

### HTTP Streamable
**¿Qué es?** Comunicación HTTP moderna y eficiente
**¿Cuándo usar?** Para servicios web, microservicios, servidores remotos
```python
mcp.run(transport="streamable-http", port=8000)
```

### Asíncrono
```python
await mcp.run_async(transport="streamable-http")
```

## 👤 Cliente

**¿Qué hace el Cliente?** Se conecta a servidores MCP para usar sus herramientas y recursos. Puede ser un LLM (como Claude) o tu propio código Python.

**Flujo típico:**
1. Conectar al servidor
2. Listar herramientas/recursos disponibles
3. Llamar herramientas con parámetros
4. Leer recursos por URI

### Cliente Básico
```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("mi_servidor.py") as client:
        # Listar tools
        tools = await client.list_tools()
        
        # Llamar tool
        resultado = await client.call_tool("sumar", {"a": 5, "b": 3})
        print(resultado[0].text)

asyncio.run(main())
```

### Cliente Multi-Servidor
**¿Qué hace?** Conecta a múltiples servidores MCP a través de una configuración unificada usando el estándar MCPConfig.

```python
from fastmcp import Client

# Configuración para múltiples servidores
config = {
    "mcpServers": {
        # Servidor remoto HTTP
        "weather": {
            "url": "https://weather-api.example.com/mcp",
            "transport": "streamable-http"
        },
        # Servidor local via stdio
        "assistant": {
            "command": "python",
            "args": ["./assistant_server.py"],
            "env": {"DEBUG": "true"}
        }
    }
}

async def main():
    # Un solo cliente maneja múltiples servidores
    async with Client(config) as client:
        # Tools con prefijos automáticos del nombre del servidor
        weather = await client.call_tool("weather_get_forecast", {"city": "London"})
        answer = await client.call_tool("assistant_answer_question", {"query": "¿Qué es MCP?"})
        
        # Resources con URIs prefijadas
        icons = await client.read_resource("weather://weather/icons/sunny")
        docs = await client.read_resource("resource://assistant/docs/mcp")

asyncio.run(main())
```

## 📝 Tipos de Parámetros

### Tipos Básicos
```python
@mcp.tool
def tipos_basicos(
    texto: str,
    numero: int,
    decimal: float,
    booleano: bool
) -> str:
    return "Procesado"
```

### Tipos Opcionales
```python
@mcp.tool
def parametros_opcionales(
    requerido: str,
    opcional: int = 10,
    puede_ser_none: str | None = None
) -> str:
    return "Procesado"
```

### Tipos de Colección
```python
@mcp.tool
def colecciones(
    lista: list[str],
    diccionario: dict[str, int],
    conjunto: set[int]
) -> str:
    return "Procesado"
```

### Tipos Literales
```python
from typing import Literal

@mcp.tool
def con_literales(
    modo: Literal["rapido", "lento", "medio"] = "medio"
) -> str:
    return f"Modo: {modo}"
```

### Tipos con Validación Pydantic
```python
from typing import Annotated
from pydantic import Field

@mcp.tool
def con_validacion(
    edad: Annotated[int, Field(ge=0, le=120)],
    email: Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")]
) -> str:
    return "Validado"
```

## 🔐 Autenticación

### Bearer Token (Servidor)
```python
from fastmcp.server.auth import BearerAuthProvider

auth = BearerAuthProvider(
    public_key="your-public-key",
    audience="mi-servidor"
)

mcp = FastMCP(name="Servidor Seguro", auth=auth)
```

## 🌐 OpenAPI Integration

**¿Qué hace?** Convierte automáticamente cualquier API REST con especificación OpenAPI en un servidor MCP completo, sin escribir código manual.

**Beneficios:**
- Cero duplicación de código
- Todos los endpoints se vuelven herramientas MCP
- Validación automática de parámetros
- Documentación automática

### Desde Especificación OpenAPI
```python
import httpx

client = httpx.AsyncClient(base_url="https://api.ejemplo.com")
openapi_spec = httpx.get("https://api.ejemplo.com/openapi.json").json()

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="API Servidor"
)
```

### Desde FastAPI
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def obtener_usuarios():
    return [{"id": 1, "nombre": "Juan"}]

mcp = FastMCP.from_fastapi(app=app)
```

## 🔧 CLI Commands

```bash
# Ejecutar servidor
fastmcp run servidor.py

# Modo desarrollo con inspector
fastmcp dev servidor.py

# Instalar en Claude Desktop
fastmcp install servidor.py

# Con dependencias
fastmcp install servidor.py --with pandas --with requests

# Ver versión
fastmcp version
```

## 🛠️ Configuración Avanzada

### Configuración del Servidor
```python
mcp = FastMCP(
    name="Mi Servidor",
    instructions="Instrucciones para el servidor",
    dependencies=["requests", "pandas"],
    include_tags={"publico"},
    exclude_tags={"interno"},
    mask_error_details=True
)
```

### Deshabilitar/Habilitar Componentes
```python
@mcp.tool(enabled=False)
def tool_deshabilitado():
    return "No disponible"

# Programáticamente
tool_deshabilitado.enable()
tool_deshabilitado.disable()
```

## 📋 Patrones Comunes

### Manejo de Errores
```python
from fastmcp.exceptions import ToolError

@mcp.tool
def dividir(a: float, b: float) -> float:
    if b == 0:
        raise ToolError("No se puede dividir por cero")
    return a / b
```

### Context para Logging
```python
@mcp.tool
async def con_logging(datos: str, ctx: Context) -> str:
    await ctx.info("Iniciando procesamiento")
    await ctx.debug(f"Datos: {datos}")
    await ctx.warning("Advertencia de ejemplo")
    return "Procesado"
```

### Datos Binarios
```python
from fastmcp import Image

@mcp.tool
def generar_imagen() -> Image:
    # ... crear imagen ...
    return Image(data=img_bytes, format="png")
```

## 🔍 Testing

**¿Por qué testing?** Asegura que tus herramientas y recursos funcionen correctamente antes de exponerlos a LLMs en producción.

**Ventaja de FastMCP:** Testing in-memory sin necesidad de procesos separados o conexiones de red.

### Test In-Memory
```python
import pytest
from fastmcp import Client

@pytest.fixture
def servidor():
    mcp = FastMCP("Test")
    
    @mcp.tool
    def sumar(a: int, b: int) -> int:
        return a + b
    
    return mcp

async def test_tool(servidor):
    async with Client(servidor) as client:
        resultado = await client.call_tool("sumar", {"a": 2, "b": 3})
        assert resultado[0].text == "5"
```