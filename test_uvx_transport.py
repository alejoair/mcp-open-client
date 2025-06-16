#!/usr/bin/env python3
"""
Test UvxStdioTransport específico para resolver BrokenResourceError con mcp-requests
Basado en la documentación oficial de FastMCP transports
"""

import asyncio
from fastmcp import Client
from fastmcp.client.transports import UvxStdioTransport

async def test_uvx_transport():
    print("=== TEST UVX STDIO TRANSPORT ===")
    
    # 1. Probar UvxStdioTransport específico para mcp-requests
    print("1. Probando UvxStdioTransport para mcp-requests...")
    
    try:
        # Usar el transporte específico para uvx según la documentación
        transport = UvxStdioTransport(
            tool_name="mcp-requests"
        )
        client = Client(transport)
        
        print("   Conectando con UvxStdioTransport...")
        
        async with client:
            print("   ✅ Conexión exitosa!")
            
            # Listar herramientas disponibles
            tools = await client.list_tools()
            print(f"   ✅ Tools encontrados: {len(tools)}")
            
            if tools:
                for i, tool in enumerate(tools[:3]):  # Mostrar primeras 3
                    print(f"      - {tool.name}: {tool.description}")
                    
                # Probar una herramienta simple
                try:
                    first_tool = tools[0]
                    print(f"   Probando tool: {first_tool.name}")
                    
                    # Intentar llamar la herramienta (puede fallar si requiere parámetros)
                    # result = await client.call_tool(first_tool.name, {})
                    # print(f"   ✅ Tool ejecutado: {result}")
                    
                except Exception as e:
                    print(f"   ⚠️  Tool requiere parámetros: {e}")
            
            # Probar ping si está disponible
            try:
                await client.ping()
                print("   ✅ Ping exitoso!")
            except Exception as e:
                print(f"   ⚠️  Ping falló: {e}")
                
    except Exception as e:
        print(f"   ❌ Error UvxStdioTransport: {e}")
        print(f"   Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    # 2. Comparar con configuración MCPConfig usando UVX
    print("\n2. Probando configuración MCPConfig equivalente...")
    
    try:
        # Configuración que debería usar UvxStdioTransport internamente
        config = {
            "mcpServers": {
                "mcp-requests": {
                    "command": "uvx",
                    "args": ["mcp-requests"]
                }
            }
        }
        
        client = Client(config)
        
        async with client:
            print("   ✅ Conexión MCPConfig exitosa!")
            
            tools = await client.list_tools()
            print(f"   ✅ Tools encontrados: {len(tools)}")
            
            # Verificar si los tools tienen prefijo del servidor
            if tools:
                for tool in tools[:3]:
                    print(f"      - {tool.name}")
                    
    except Exception as e:
        print(f"   ❌ Error MCPConfig: {e}")
        print(f"   Tipo: {type(e).__name__}")
    
    # 3. Probar con keep_alive=False para aislamiento completo
    print("\n3. Probando con keep_alive=False...")
    
    try:
        transport = UvxStdioTransport(
            tool_name="mcp-requests",
            keep_alive=False  # Nueva sesión cada vez
        )
        client = Client(transport)
        
        async with client:
            print("   ✅ Conexión con keep_alive=False exitosa!")
            
            tools = await client.list_tools()
            print(f"   ✅ Tools: {len(tools)}")
            
    except Exception as e:
        print(f"   ❌ Error keep_alive=False: {e}")
        print(f"   Tipo: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_uvx_transport())