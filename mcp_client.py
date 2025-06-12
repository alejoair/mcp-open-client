import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Union
from fastmcp import Client

class MCPClientManager:
    """
    Manager for MCP clients that handles connections to multiple MCP servers
    based on the configuration in app.storage.user['mcp-config'].
    """
    
    def __init__(self):
        self.client = None
        self.active_servers = {}
        self.config = {}
        self._initializing = False  # Flag to prevent concurrent initializations
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize the MCP client with the given configuration."""
        # Prevent concurrent initializations to avoid infinite loops
        if self._initializing:
            print("MCP client initialization already in progress, skipping...")
            return False
        
        try:
            self._initializing = True
            self.config = config
            
            # Close any existing client
            if self.client:
                # The fastmcp Client doesn't have a close method
                # Just set it to None to allow garbage collection
                self.client = None
            
            # Create a new client with the current configuration
            if "mcpServers" in config and config["mcpServers"]:
                # Filter out disabled servers
                active_servers = {
                    name: server_config
                    for name, server_config in config["mcpServers"].items()
                    if not server_config.get("disabled", False)
                }
                
                if active_servers:
                    self.active_servers = active_servers
                    # Create configuration with only active servers
                    client_config = {"mcpServers": active_servers}
                    try:
                        # Create the client - no need to call connect() as it's handled by the Client constructor
                        self.client = Client(client_config)
                        return True
                    except Exception as e:
                        print(f"Error initializing MCP client: {str(e)}")
                        return False
            
            return False
        finally:
            self._initializing = False  # Reset the flag when done
    
    async def close(self):
        """Close the MCP client connection."""
        if self.client:
            # The fastmcp Client doesn't have a close method
            # Just set it to None to allow garbage collection
            self.client = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from connected MCP servers."""
        if not self.client:
            return []
        
        try:
            tools = await self.client.list_tools()
            return tools
        except Exception as e:
            print(f"Error listing tools: {str(e)}")
            return []
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources from connected MCP servers."""
        if not self.client:
            return []
        
        try:
            resources = await self.client.list_resources()
            return resources
        except Exception as e:
            print(f"Error listing resources: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Call a tool on one of the connected MCP servers."""
        if not self.client:
            raise ValueError("MCP client not initialized")
        
        try:
            result = await self.client.call_tool(tool_name, params)
            return result
        except Exception as e:
            raise Exception(f"Error calling tool {tool_name}: {str(e)}")
    
    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read a resource from one of the connected MCP servers."""
        if not self.client:
            raise ValueError("MCP client not initialized")
        
        try:
            result = await self.client.read_resource(uri)
            return result
        except Exception as e:
            raise Exception(f"Error reading resource {uri}: {str(e)}")
    
    def get_active_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get the currently active MCP servers."""
        return self.active_servers
    
    def is_connected(self) -> bool:
        """Check if the client is connected to any MCP servers."""
        return self.client is not None

# Create a singleton instance
mcp_client_manager = MCPClientManager()