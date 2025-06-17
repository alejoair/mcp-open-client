#!/usr/bin/env python3
"""
Script de diagnóstico detallado para el problema MCP.
"""
import asyncio
import subprocess
import json
import time
import sys

async def test_uvx_command():
    """Prueba el comando uvx directamente."""
    print("=== Prueba del comando uvx ===")
    
    try:
        # Probar uvx --version
        result = subprocess.run(['uvx', '--version'], 
                              capture_output=True, text=True, timeout=10)
        print(f"uvx --version: {result.stdout.strip()}")
        print(f"Return code: {result.returncode}")
        
        # Probar uvx mcp-requests con timeout corto
        print("\nProbando uvx mcp-requests...")
        proc = subprocess.Popen(['uvx', 'mcp-requests'], 
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        
        # Esperar un poco para ver si el proceso se inicia
        time.sleep(2)
        
        if proc.poll() is None:
            print("✓ Proceso uvx mcp-requests iniciado correctamente")
            
            # Enviar un mensaje MCP básico
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
            
            try:
                proc.stdin.write(json.dumps(init_message) + '\n')
                proc.stdin.flush()
                
                # Intentar leer respuesta con timeout
                proc.stdout.settimeout(5)
                response = proc.stdout.readline()
                print(f"Respuesta del servidor: {response.strip()}")
                
            except Exception as e:
                print(f"Error en comunicación MCP: {e}")
            
            # Terminar el proceso
            proc.terminate()
            proc.wait(timeout=5)
        else:
            print(f"❌ Proceso terminó inmediatamente con código: {proc.returncode}")
            stderr = proc.stderr.read()
            if stderr:
                print(f"Error: {stderr}")
                
    except subprocess.TimeoutExpired:
        print("❌ Timeout ejecutando uvx")
    except FileNotFoundError:
        print("❌ uvx no encontrado en PATH")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_alternative_config():
    """Prueba configuraciones alternativas."""
    print("\n=== Prueba de configuraciones alternativas ===")
    
    from fastmcp import Client
    
    # Configuración 1: Sin variables de entorno
    config1 = {
        "mcpServers": {
            "mcp-requests": {
                "command": "uvx",
                "args": ["mcp-requests"]
            }
        }
    }
    
    print("1. Probando sin variables de entorno...")
    try:
        client = Client(config1)
        async with client as connected_client:
            print("   ✓ Conexión exitosa sin env vars")
            tools = await connected_client.list_tools()
            print(f"   ✓ {len(tools)} herramientas obtenidas")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Configuración 2: Con timeout explícito
    print("\n2. Probando con timeout explícito...")
    try:
        client = Client(config1, timeout=60.0)
        async with client as connected_client:
            print("   ✓ Conexión exitosa con timeout")
            tools = await connected_client.list_tools()
            print(f"   ✓ {len(tools)} herramientas obtenidas")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Configuración 3: Usando python directamente
    config3 = {
        "mcpServers": {
            "mcp-requests": {
                "command": "python",
                "args": ["-m", "pip", "install", "mcp-requests", "&&", "python", "-m", "mcp_requests"]
            }
        }
    }
    
    print("\n3. Probando instalación directa...")
    try:
        # Primero instalar mcp-requests
        subprocess.run([sys.executable, "-m", "pip", "install", "mcp-requests"], 
                      check=True, capture_output=True)
        print("   ✓ mcp-requests instalado")
        
        # Ahora probar con python -m
        config3_fixed = {
            "mcpServers": {
                "mcp-requests": {
                    "command": sys.executable,
                    "args": ["-m", "mcp_requests"]
                }
            }
        }
        
        client = Client(config3_fixed)
        async with client as connected_client:
            print("   ✓ Conexión exitosa con python -m")
            tools = await connected_client.list_tools()
            print(f"   ✓ {len(tools)} herramientas obtenidas")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def test_manual_stdio():
    """Prueba manual de comunicación STDIO."""
    print("\n=== Prueba manual STDIO ===")
    
    try:
        # Iniciar proceso manualmente
        proc = subprocess.Popen(['uvx', 'mcp-requests'],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        
        print("Proceso iniciado, enviando initialize...")
        
        # Mensaje de inicialización
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "debug-client", "version": "1.0.0"}
            }
        }
        
        # Enviar mensaje
        proc.stdin.write(json.dumps(init_msg) + '\n')
        proc.stdin.flush()
        
        # Leer respuesta con timeout
        import select
        import os
        
        if os.name == 'nt':  # Windows
            # En Windows, usar threading para timeout
            import threading
            import queue
            
            def read_output(proc, q):
                try:
                    line = proc.stdout.readline()
                    q.put(line)
                except:
                    q.put(None)
            
            q = queue.Queue()
            t = threading.Thread(target=read_output, args=(proc, q))
            t.start()
            t.join(timeout=10)
            
            if not q.empty():
                response = q.get()
                print(f"Respuesta: {response.strip()}")
            else:
                print("❌ Timeout leyendo respuesta")
        else:
            # Unix/Linux
            ready, _, _ = select.select([proc.stdout], [], [], 10)
            if ready:
                response = proc.stdout.readline()
                print(f"Respuesta: {response.strip()}")
            else:
                print("❌ Timeout leyendo respuesta")
        
        # Limpiar
        proc.terminate()
        proc.wait(timeout=5)
        
    except Exception as e:
        print(f"❌ Error en prueba manual: {e}")

if __name__ == "__main__":
    async def main():
        await test_uvx_command()
        await test_alternative_config()
        await test_manual_stdio()
    
    asyncio.run(main())