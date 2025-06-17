import asyncio
import json
import subprocess
import sys
from fastmcp import Client

async def test_simple_server():
    """
    Prueba con nuestro servidor MCP simple para verificar si FastMCP funciona
    """
    print("=== Prueba con servidor MCP simple ===")
    
    config = {
        "mcpServers": {
            "test-server": {
                "command": "python",
                "args": ["simple_mcp_server.py"]
            }
        }
    }
    
    try:
        print("Probando servidor MCP simple...")
        async with Client(config) as client:
            print("✓ Conexión exitosa con servidor simple")
            
            tools = await client.list_tools()
            print(f"✓ Herramientas encontradas: {len(tools)}")
            
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Probar una herramienta
            if tools:
                result = await client.call_tool("test-server_hello", {"name": "FastMCP"})
                print(f"✓ Resultado: {result[0].text}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error con servidor simple: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_stdio():
    """
    Prueba comunicación STDIO directa sin FastMCP para aislar el problema
    """
    print("\n=== Prueba STDIO directa ===")
    
    try:
        # Iniciar proceso uvx mcp-requests
        process = subprocess.Popen(
            ["uvx", "mcp-requests"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        print("✓ Proceso uvx iniciado")
        
        # Enviar mensaje de inicialización MCP
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        message_str = json.dumps(init_message) + "\n"
        print(f"Enviando: {message_str.strip()}")
        
        process.stdin.write(message_str)
        process.stdin.flush()
        
        # Leer respuesta con timeout
        import select
        import time
        
        start_time = time.time()
        timeout = 5
        
        while time.time() - start_time < timeout:
            if process.stdout.readable():
                response = process.stdout.readline()
                if response:
                    print(f"✓ Respuesta recibida: {response.strip()}")
                    
                    # Enviar initialized
                    initialized = {
                        "jsonrpc": "2.0",
                        "method": "initialized",
                        "params": {}
                    }
                    init_str = json.dumps(initialized) + "\n"
                    process.stdin.write(init_str)
                    process.stdin.flush()
                    
                    # Listar herramientas
                    list_tools = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                    tools_str = json.dumps(list_tools) + "\n"
                    process.stdin.write(tools_str)
                    process.stdin.flush()
                    
                    # Leer respuesta de herramientas
                    tools_response = process.stdout.readline()
                    if tools_response:
                        print(f"✓ Herramientas: {tools_response.strip()}")
                    
                    process.terminate()
                    return True
            
            await asyncio.sleep(0.1)
        
        print("❌ Timeout esperando respuesta")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ Error en prueba STDIO: {e}")
        return False

async def test_uvx_alternatives():
    """
    Prueba alternativas a uvx para ejecutar mcp-requests
    """
    print("\n=== Prueba alternativas a uvx ===")
    
    alternatives = [
        # Instalar mcp-requests globalmente y usar python -m
        {
            "name": "pip install + python -m",
            "install_cmd": [sys.executable, "-m", "pip", "install", "mcp-requests"],
            "config": {
                "mcpServers": {
                    "mcp-requests": {
                        "command": sys.executable,
                        "args": ["-m", "mcp_requests"]
                    }
                }
            }
        },
        # Usar pipx en lugar de uvx
        {
            "name": "pipx",
            "install_cmd": ["pipx", "install", "mcp-requests"],
            "config": {
                "mcpServers": {
                    "mcp-requests": {
                        "command": "pipx",
                        "args": ["run", "mcp-requests"]
                    }
                }
            }
        }
    ]
    
    for alt in alternatives:
        print(f"\nProbando: {alt['name']}")
        
        try:
            # Intentar instalación
            print(f"Instalando con: {' '.join(alt['install_cmd'])}")
            result = subprocess.run(alt['install_cmd'], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✓ Instalación exitosa")
                
                # Probar cliente
                try:
                    async with Client(alt['config']) as client:
                        tools = await client.list_tools()
                        print(f"✓ {alt['name']}: {len(tools)} herramientas encontradas")
                        return True
                except Exception as e:
                    print(f"❌ Error con cliente {alt['name']}: {e}")
            else:
                print(f"❌ Error de instalación: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout en instalación de {alt['name']}")
        except Exception as e:
            print(f"❌ Error con {alt['name']}: {e}")
    
    return False

async def main():
    """
    Ejecuta todas las pruebas de diagnóstico
    """
    print("=== DIAGNÓSTICO COMPREHENSIVO MCP ===\n")
    
    # Prueba 1: Servidor simple
    simple_ok = await test_simple_server()
    
    # Prueba 2: STDIO directo
    stdio_ok = await test_direct_stdio()
    
    # Prueba 3: Alternativas a uvx
    alt_ok = await test_uvx_alternatives()
    
    print("\n=== RESUMEN ===")
    print(f"Servidor simple: {'✓' if simple_ok else '❌'}")
    print(f"STDIO directo: {'✓' if stdio_ok else '❌'}")
    print(f"Alternativas uvx: {'✓' if alt_ok else '❌'}")
    
    if simple_ok and not stdio_ok:
        print("\n🔍 DIAGNÓSTICO: FastMCP funciona, pero hay problema con uvx/mcp-requests")
    elif not simple_ok:
        print("\n🔍 DIAGNÓSTICO: Problema fundamental con FastMCP STDIO")
    elif alt_ok:
        print("\n🔍 DIAGNÓSTICO: uvx es el problema, usar alternativa")

if __name__ == "__main__":
    asyncio.run(main())