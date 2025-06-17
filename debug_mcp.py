#!/usr/bin/env python3
"""
Script de diagnóstico para probar la conexión MCP y identificar el problema.
"""
import asyncio
import json
import traceback
from fastmcp import Client

async def test_mcp_connection():
    """Prueba la conexión MCP paso a paso para diagnosticar el problema."""
    
    print("=== Diagnóstico MCP ===")
    
    # Configuración de prueba (igual a la que usa la aplicación)
    config = {
        "mcpServers": {
            "mcp-requests": {
                "disabled": False,
                "command": "uvx",
                "args": ["mcp-requests"],
                "env": {"key": "val"}
            }
        }
    }
    
    print(f"1. Configuración: {json.dumps(config, indent=2)}")
    
    try:
        print("2. Creando cliente FastMCP...")
        client = Client(config)
        print("   ✓ Cliente creado exitosamente")
        
        print("3. Intentando conectar...")
        async with client as connected_client:
            print("   ✓ Conexión establecida")
            
            print("4. Probando ping...")
            await connected_client.ping()
            print("   ✓ Ping exitoso")
            
            print("5. Listando herramientas...")
            tools = await connected_client.list_tools()
            print(f"   ✓ Herramientas obtenidas: {len(tools)}")
            
            for i, tool in enumerate(tools):
                print(f"   - Tool {i+1}: {tool.name} - {tool.description}")
            
            print("6. Listando recursos...")
            resources = await connected_client.list_resources()
            print(f"   ✓ Recursos obtenidos: {len(resources)}")
            
            for i, resource in enumerate(resources):
                print(f"   - Resource {i+1}: {resource.uri}")
            
            print("7. Probando llamada a herramienta...")
            if tools:
                first_tool = tools[0]
                print(f"   Probando herramienta: {first_tool.name}")
                try:
                    # Intentar llamar con parámetros vacíos
                    result = await connected_client.call_tool(first_tool.name, {})
                    print(f"   ✓ Llamada exitosa: {result}")
                except Exception as e:
                    print(f"   ⚠ Error en llamada (esperado): {e}")
            
        print("8. Conexión cerrada correctamente")
        print("\n=== DIAGNÓSTICO EXITOSO ===")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN DIAGNÓSTICO:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print(f"Traceback:")
        traceback.print_exc()
        return False

async def test_multiple_connections():
    """Prueba múltiples conexiones para ver si el problema es de concurrencia."""
    print("\n=== Prueba de Múltiples Conexiones ===")
    
    config = {
        "mcpServers": {
            "mcp-requests": {
                "disabled": False,
                "command": "uvx",
                "args": ["mcp-requests"],
                "env": {"key": "val"}
            }
        }
    }
    
    for i in range(3):
        print(f"\nConexión {i+1}:")
        try:
            client = Client(config)
            async with client as connected_client:
                tools = await connected_client.list_tools()
                print(f"   ✓ Conexión {i+1}: {len(tools)} herramientas")
        except Exception as e:
            print(f"   ❌ Conexión {i+1} falló: {e}")

async def test_with_timeout():
    """Prueba con timeout para ver si es un problema de tiempo."""
    print("\n=== Prueba con Timeout ===")
    
    config = {
        "mcpServers": {
            "mcp-requests": {
                "disabled": False,
                "command": "uvx",
                "args": ["mcp-requests"],
                "env": {"key": "val"}
            }
        }
    }
    
    try:
        client = Client(config, timeout=30.0)  # 30 segundos de timeout
        async with client as connected_client:
            print("Conexión con timeout establecida")
            tools = await connected_client.list_tools()
            print(f"✓ Herramientas con timeout: {len(tools)}")
    except Exception as e:
        print(f"❌ Error con timeout: {e}")

if __name__ == "__main__":
    async def main():
        success = await test_mcp_connection()
        if success:
            await test_multiple_connections()
            await test_with_timeout()
        else:
            print("\nEl diagnóstico básico falló. Revisa la configuración del servidor MCP.")
    
    asyncio.run(main())