Para crear un cliente que maneja varios servidores MCP usando un archivo de configuración JSON, puedes usar la clase Client de FastMCP con una configuración MCPConfig. Te explico cómo hacerlo paso a paso:

1. Estructura del archivo de configuración JSON
Primero, crea un archivo de configuración JSON que defina los servidores MCP:

json
{
  "mcpServers": {
    "weather": {
      "url": "https://weather-api.example.com/mcp",
      "transport": "streamable-http"
    },
    "database": {
      "command": "python",
      "args": ["./database_server.py"],
      "env": {
        "DB_PATH": "/path/to/database.db",
        "DEBUG": "true"
      }
    },
    "calculator": {
      "command": "uv",
      "args": [
        "run",
        "--with", "numpy",
        "python",
        "./calculator_server.py"
      ]
    },
    "remote_api": {
      "url": "https://api.example.com/mcp/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    }
  }
}
2. Crear el cliente multi-servidor
Aquí tienes un ejemplo completo de cómo crear y usar un cliente que maneja múltiples servidores:

python
import asyncio
import json
from pathlib import Path
from fastmcp import Client

async def main():
    # Cargar la configuración desde el archivo JSON
    config_path = Path("mcp_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Crear el cliente con la configuración multi-servidor
    client = Client(config)
    
    async with client:
        # Listar todas las herramientas disponibles de todos los servidores
        print("=== Herramientas disponibles ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # Listar todos los recursos disponibles
        print("\n=== Recursos disponibles ===")
        resources = await client.list_resources()
        for resource in resources:
            print(f"- {resource.uri}: {resource.name}")
        
        # Usar herramientas con prefijos (el nombre del servidor se usa como prefijo)
        try:
            # Llamar una herramienta del servidor weather
            weather_result = await client.call_tool(
                "weather_get_forecast", 
                {"city": "London"}
            )
            print(f"\n=== Pronóstico del tiempo ===")
            print(weather_result[0].text)
        except Exception as e:
            print(f"Error llamando weather tool: {e}")
        
        try:
            # Llamar una herramienta del servidor calculator
            calc_result = await client.call_tool(
                "calculator_add", 
                {"a": 10, "b": 20}
            )
            print(f"\n=== Resultado de cálculo ===")
            print(calc_result[0].text)
        except Exception as e:
            print(f"Error llamando calculator tool: {e}")
        
        # Leer recursos con prefijos
        try:
            # Leer un recurso del servidor database
            db_resource = await client.read_resource("database://database/users/list")
            print(f"\n=== Datos de usuarios ===")
            print(db_resource[0].text)
        except Exception as e:
            print(f"Error leyendo database resource: {e}")

if __name__ == "__main__":
    asyncio.run(main())
3. Configuración avanzada con autenticación
Si necesitas autenticación para algunos servidores, puedes incluirla en la configuración:

json
{
  "mcpServers": {
    "secure_api": {
      "url": "https://secure-api.example.com/mcp",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer your-access-token",
        "X-API-Key": "your-api-key"
      }
    },
    "oauth_server": {
      "url": "https://oauth-server.example.com/mcp",
      "transport": "streamable-http",
      "auth": "oauth"
    }
  }
}
4. Gestión de configuración dinámica
También puedes crear una clase para gestionar la configuración de manera más organizada:

python
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from fastmcp import Client

class MCPMultiClient:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.client = Client(self.config)
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON"""
        with open(self.config_path, "r") as f:
            return json.load(f)
    
    def reload_config(self):
        """Recarga la configuración desde el archivo"""
        self.config = self._load_config()
        # Nota: necesitarías recrear el cliente para aplicar cambios
        self.client = Client(self.config)
    
    async def get_server_tools(self, server_prefix: str) -> list:
        """Obtiene las herramientas de un servidor específico"""
        async with self.client:
            all_tools = await self.client.list_tools()
            return [tool for tool in all_tools if tool.name.startswith(f"{server_prefix}_")]
    
    async def call_server_tool(self, server_name: str, tool_name: str, arguments: dict):
        """Llama a una herramienta específica de un servidor"""
        full_tool_name = f"{server_name}_{tool_name}"
        async with self.client:
            return await self.client.call_tool(full_tool_name, arguments)
    
    async def list_all_capabilities(self):
        """Lista todas las capacidades disponibles"""
        async with self.client:
            tools = await self.client.list_tools()
            resources = await self.client.list_resources()
            prompts = await self.client.list_prompts()
            
            return {
                "tools": [{"name": t.name, "description": t.description} for t in tools],
                "resources": [{"uri": r.uri, "name": r.name} for r in resources],
                "prompts": [{"name": p.name, "description": p.description} for p in prompts]
            }

# Uso de la clase
async def example_usage():
    multi_client = MCPMultiClient("mcp_config.json")
    
    # Listar todas las capacidades
    capabilities = await multi_client.list_all_capabilities()
    print("Capacidades disponibles:", json.dumps(capabilities, indent=2))
    
    # Obtener herramientas de un servidor específico
    weather_tools = await multi_client.get_server_tools("weather")
    print(f"Herramientas del servidor weather: {[t.name for t in weather_tools]}")
    
    # Llamar a una herramienta específica
    try:
        result = await multi_client.call_server_tool(
            "calculator", 
            "multiply", 
            {"a": 5, "b": 3}
        )
        print(f"Resultado: {result[0].text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(example_usage())
5. Manejo de errores y fallbacks
Para un cliente robusto, puedes implementar manejo de errores y fallbacks:

python
import asyncio
import logging
from fastmcp import Client
from fastmcp.exceptions import ClientError

async def robust_multi_client_example():
    config = {
        "mcpServers": {
            "primary": {"url": "https://primary-api.com/mcp"},
            "backup": {"command": "python", "args": ["backup_server.py"]}
        }
    }
    
    client = Client(config)
    
    async with client:
        try:
            # Intentar usar el servidor primario
            result = await client.call_tool("primary_important_function", {"data": "test"})
            print(f"Resultado del servidor primario: {result[0].text}")
        except ClientError as e:
            logging.warning(f"Error en servidor primario: {e}")
            try:
                # Fallback al servidor de respaldo
                result = await client.call_tool("backup_important_function", {"data": "test"})
                print(f"Resultado del servidor de respaldo: {result[0].text}")
            except ClientError as backup_error:
                logging.error(f"Error en ambos servidores: {backup_error}")

if __name__ == "__main__":
    asyncio.run(robust_multi_client_example())
Puntos clave a recordar:
Prefijos automáticos: Cuando usas múltiples servidores, FastMCP automáticamente prefija las herramientas y recursos con el nombre del servidor (ej: weather_get_forecast).
Configuración flexible: Puedes mezclar servidores locales (stdio) y remotos (HTTP) en la misma configuración.
Un solo cliente: FastMCP crea un cliente unificado que maneja todos los servidores internamente.
Gestión de sesiones: El cliente maneja automáticamente las conexiones a todos los servidores configurados.
Esta aproximación te permite crear aplicaciones que integren múltiples servicios MCP de manera transparente y eficiente.





