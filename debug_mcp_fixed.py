import asyncio
import json
from fastmcp import Client

async def test_fixed_mcp_connection():
    """
    Prueba la conexión MCP usando la configuración correcta para uvx
    basada en la documentación de FastMCP Client
    """
    print("=== Prueba de conexión MCP corregida ===")
    
    # Configuración corregida según documentación FastMCP
    # Para comandos con argumentos, usar command + args explícitamente
    config = {
        "mcpServers": {
            "mcp-requests": {
                "command": "uvx",
                "args": ["mcp-requests"],
                "env": {}  # Variables de entorno vacías
            }
        }
    }
    
    print(f"Configuración MCP: {json.dumps(config, indent=2)}")
    
    try:
        print("Creando cliente FastMCP...")
        async with Client(config) as client:
            print("✓ Cliente MCP creado exitosamente")
            
            # Listar herramientas disponibles
            print("\nListando herramientas disponibles...")
            tools = await client.list_tools()
            print(f"✓ Herramientas encontradas: {len(tools)}")
            
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Probar una herramienta simple si está disponible
            if tools:
                first_tool = tools[0]
                print(f"\nProbando herramienta: {first_tool.name}")
                
                # Intentar llamar la herramienta con parámetros mínimos
                try:
                    # Para mcp-requests, probablemente necesitemos una URL
                    if "get" in first_tool.name.lower() or "request" in first_tool.name.lower():
                        result = await client.call_tool(first_tool.name, {"url": "https://httpbin.org/get"})
                        print(f"✓ Herramienta ejecutada exitosamente")
                        print(f"Resultado: {result[0].text[:200]}...")
                    else:
                        print(f"Herramienta {first_tool.name} requiere parámetros específicos")
                except Exception as e:
                    print(f"Error ejecutando herramienta: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en conexión MCP: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def test_alternative_configs():
    """
    Prueba configuraciones alternativas para diagnosticar el problema
    """
    print("\n=== Pruebas de configuraciones alternativas ===")
    
    # Configuración 1: Sin variables de entorno
    config1 = {
        "mcpServers": {
            "mcp-requests": {
                "command": "uvx",
                "args": ["mcp-requests"]
            }
        }
    }
    
    # Configuración 2: Con timeout explícito (si FastMCP lo soporta)
    config2 = {
        "mcpServers": {
            "mcp-requests": {
                "command": "uvx", 
                "args": ["mcp-requests"],
                "timeout": 30
            }
        }
    }
    
    # Configuración 3: Usando python directamente con mcp-requests instalado
    config3 = {
        "mcpServers": {
            "mcp-requests": {
                "command": "python",
                "args": ["-m", "mcp_requests"]
            }
        }
    }
    
    configs = [
        ("Sin env", config1),
        ("Con timeout", config2), 
        ("Python directo", config3)
    ]
    
    for name, config in configs:
        print(f"\nProbando configuración: {name}")
        try:
            async with Client(config) as client:
                tools = await client.list_tools()
                print(f"✓ {name}: {len(tools)} herramientas encontradas")
                return True
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_fixed_mcp_connection())
    asyncio.run(test_alternative_configs())