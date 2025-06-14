#!/usr/bin/env python3
"""
Simple test MCP server using FastMCP
"""

import asyncio
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Test MCP Server")

@mcp.tool()
def get_current_time() -> str:
    """Get the current time"""
    import datetime
    return f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@mcp.tool()
def add_numbers(a: int, b: int) -> str:
    """Add two numbers together"""
    result = a + b
    return f"The sum of {a} and {b} is {result}"

@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user by name"""
    return f"Hello, {name}! Nice to meet you."

if __name__ == "__main__":
    mcp.run()