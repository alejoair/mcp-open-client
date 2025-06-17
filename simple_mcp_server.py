#!/usr/bin/env python3
"""
Servidor MCP simple para pruebas de diagnóstico
"""

from fastmcp import FastMCP

# Crear servidor MCP simple
mcp = FastMCP(name="TestServer")

@mcp.tool
def hello(name: str = "World") -> str:
    """Saluda a una persona."""
    return f"Hello, {name}!"

@mcp.tool
def add(a: int, b: int) -> int:
    """Suma dos números."""
    return a + b

@mcp.tool
def get_info() -> str:
    """Obtiene información del servidor."""
    return "This is a simple test MCP server"

if __name__ == "__main__":
    # Ejecutar en modo STDIO para compatibilidad con clientes MCP
    mcp.run()