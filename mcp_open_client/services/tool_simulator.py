"""
Tool execution simulator for MCP-style tools
This simulates tool execution until real MCP integration is implemented
"""
import asyncio
import json
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime

class ToolSimulator:
    """Simulates tool execution for testing and development"""

    def __init__(self):
        self.tools = {
            "calculate": self._calculate,
            "get_current_time": self._get_current_time,
            "search_web": self._search_web,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "get_weather": self._get_weather
        }

    async def execute_tool(self, tool_call_id: str, name: str, arguments: str) -> Dict[str, Any]:
        """
        Simulate tool execution
        Returns: {
            "tool_call_id": str,
            "name": str,
            "content": str,
            "status": "success" | "error",
            "execution_time": float
        }
        """
        start_time = time.time()

        try:
            # Parse arguments
            try:
                args = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return {
                    "tool_call_id": tool_call_id,
                    "name": name,
                    "content": f"Error: Invalid JSON arguments: {arguments}",
                    "status": "error",
                    "execution_time": time.time() - start_time
                }

            # Simulate network delay
            await self._simulate_delay()

            # Execute tool if available
            if name in self.tools:
                result = await self.tools[name](args)
                content = result if isinstance(result, str) else json.dumps(result)
            else:
                content = f"Error: Tool '{name}' not found. Available tools: {list(self.tools.keys())}"
                status = "error"

            execution_time = time.time() - start_time

            return {
                "tool_call_id": tool_call_id,
                "name": name,
                "content": content,
                "status": "success" if name in self.tools else "error",
                "execution_time": execution_time
            }

        except Exception as e:
            return {
                "tool_call_id": tool_call_id,
                "name": name,
                "content": f"Error executing tool: {str(e)}",
                "status": "error",
                "execution_time": time.time() - start_time
            }

    async def _simulate_delay(self):
        """Simulate realistic tool execution delay"""
        delay = random.uniform(0.5, 2.0)  # 0.5-2 seconds
        await asyncio.sleep(delay)

    async def _calculate(self, args: Dict[str, Any]) -> str:
        """Simulate calculator tool"""
        expression = args.get("expression", "")
        if not expression:
            return "Error: No expression provided"

        try:
            # Simple calculator (eval is normally dangerous, but this is a simulation)
            # In real MCP, this would call actual calculator tool
            result = eval(expression.replace("^", "**"))
            return str(result)
        except Exception as e:
            return f"Calculation error: {str(e)}"

    async def _get_current_time(self, args: Dict[str, Any]) -> str:
        """Simulate time tool"""
        timezone = args.get("timezone", "UTC")
        current_time = datetime.now()
        return f"Current time ({timezone}): {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

    async def _search_web(self, args: Dict[str, Any]) -> str:
        """Simulate web search tool"""
        query = args.get("query", "")
        if not query:
            return "Error: No search query provided"

        # Simulate search results
        results = [
            f"Search result 1 for '{query}': Lorem ipsum...",
            f"Search result 2 for '{query}': Dolor sit amet...",
            f"Search result 3 for '{query}': Consectetur adipiscing..."
        ]
        return "\n".join(results)

    async def _read_file(self, args: Dict[str, Any]) -> str:
        """Simulate file reading tool"""
        file_path = args.get("path", "")
        if not file_path:
            return "Error: No file path provided"

        # Simulate file content
        return f"Simulated content of file: {file_path}\nLine 1: Sample data\nLine 2: More data..."

    async def _write_file(self, args: Dict[str, Any]) -> str:
        """Simulate file writing tool"""
        file_path = args.get("path", "")
        content = args.get("content", "")

        if not file_path:
            return "Error: No file path provided"

        # Simulate successful write
        return f"Successfully wrote {len(content)} characters to {file_path}"

    async def _get_weather(self, args: Dict[str, Any]) -> str:
        """Simulate weather tool"""
        location = args.get("location", "Unknown Location")

        # Simulate weather data
        conditions = ["sunny", "cloudy", "rainy", "snowy"]
        temperatures = range(15, 35)

        condition = random.choice(conditions)
        temp = random.choice(temperatures)

        return f"Weather in {location}: {condition.title()}, {temp}°C"

# Global simulator instance
tool_simulator = ToolSimulator()