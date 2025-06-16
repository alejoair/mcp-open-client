#!/usr/bin/env python3
"""
Simple MCP server for testing purposes.
"""

from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP(name="Test Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

@mcp.tool()
def get_info() -> str:
    """Get server information."""
    return "This is a test MCP server created for debugging purposes."

if __name__ == "__main__":
    print("Starting test MCP server...", flush=True)
    mcp.run()  # STDIO transport by default