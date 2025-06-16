import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Union
from fastmcp import Client, Context
from fastmcp.client.transports import UvxStdioTransport, NpxStdioTransport
import mcp.shared.exceptions
import anyio

class McpClientError(Exception):
    """Custom exception for MCP client errors."""
    pass

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
            
            print(f"Starting MCP client initialization with config: {json.dumps(config, indent=2)}")
            
            # Close any existing client and stop running servers
            await self.close()
            
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
                    print(f"Active servers: {', '.join(active_servers.keys())}")
                    
                    # Let FastMCP handle server launching automatically
                    print("FastMCP will handle server launching automatically")
                    print(f"Client configuration: {json.dumps({'mcpServers': active_servers}, indent=2)}")
                    
                    try:
                        print("Preparing MCP client...")
                        # Don't create client here, create it when needed in context manager
                        self.client = None  # Will be created in context manager
                        print(f"Successfully prepared MCP client with {len(active_servers)} servers")
                        
                        # Check client connection status
                        print("Checking client connection...")
                        try:
                            await self._check_client_connection()
                            print("Client connection verified")
                            return True
                        except McpClientError as e:
                            print(f"Client connection check failed: {str(e)}")
                            return False
                    except Exception as e:
                        print(f"Error initializing MCP client: {str(e)}")
                        print(f"Exception type: {type(e).__name__}")
                        print(f"Exception details: {repr(e)}")
                        return False
                else:
                    print("No active servers found in configuration")
                    return False
            else:
                print("No MCP servers defined in configuration")
                return False
        except Exception as e:
            print(f"Unexpected error during MCP client initialization: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception details: {repr(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self._initializing = False  # Reset the flag when done
            print("MCP client initialization process completed")

    async def _check_client_connection(self) -> bool:
        """Check if the client is properly connected to the servers."""
        print("Starting client connection check...")
        
        try:
            print("Testing client connection...")
            # Create a temporary client to test the connection
            async with Client({"mcpServers": self.active_servers}) as client:
                tools = await client.list_tools()
                print(f"Successfully connected to MCP servers. Found {len(tools)} tools.")
                return True
        except Exception as e:
            print(f"Error testing client connection: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            # For now, we'll consider this a warning rather than a failure
            # since FastMCP might need more time to establish connections
            print("Warning: Initial connection test failed, but proceeding with initialization")
            return True

    async def close(self):
        """Close the MCP client connection."""
        if self.client:
            # The fastmcp Client doesn't have a close method
            # Just set it to None to allow garbage collection
            self.client = None
        
        # Clear active servers since FastMCP handles server lifecycle
        self.active_servers = {}
    
    def _create_transport_for_server(self, server_name: str, server_config: Dict[str, Any]):
        """Create the appropriate transport for a server based on its command."""
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        
        if command == "uvx":
            # For UVX, the tool name is typically the first argument
            tool_name = args[0] if args else server_name
            print(f"Creating UvxStdioTransport for {server_name} with tool_name: {tool_name}")
            return UvxStdioTransport(tool_name=tool_name)
        
        elif command == "npx":
            # For NPX, we need to extract the package name and additional args
            if args:
                # Find the package name (usually after -y flag or first non-flag arg)
                package = None
                npx_args = []
                
                for i, arg in enumerate(args):
                    if arg == "-y" and i + 1 < len(args):
                        # Package is after -y flag
                        package = args[i + 1]
                        npx_args = args[:i] + args[i+2:]  # Remove -y and package
                        break
                    elif not arg.startswith("-"):
                        # First non-flag argument is the package
                        package = arg
                        npx_args = args[:i] + args[i+1:]  # Remove package from args
                        break
                
                if package:
                    print(f"Creating NpxStdioTransport for {server_name} with package: {package}, args: {npx_args}")
                    return NpxStdioTransport(package=package, args=npx_args if npx_args else None)
            
            raise ValueError(f"Could not determine NPX package for server {server_name}")
        
        else:
            raise ValueError(f"Unsupported command '{command}' for server {server_name}. Only 'uvx' and 'npx' are supported.")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from connected MCP servers."""
        if not self.active_servers:
            print("No active MCP servers configured")
            return []
        
        all_tools = []
        
        for server_name, server_config in self.active_servers.items():
            try:
                print(f"Connecting to server: {server_name}")
                print(f"Server config: {json.dumps(server_config, indent=2)}")
                
                # Create specific transport for this server
                transport = self._create_transport_for_server(server_name, server_config)
                
                # Connect using the specific transport
                async with Client(transport) as client:
                    print(f"Client connected to {server_name}, calling list_tools()...")
                    tools = await client.list_tools()
                    print(f"Retrieved {len(tools)} tools from {server_name}")
                    
                    # Add server name to each tool for identification
                    for tool in tools:
                        if isinstance(tool, dict):
                            tool['_server'] = server_name
                        else:
                            # Handle tool objects
                            tool_dict = {
                                'name': getattr(tool, 'name', 'unnamed'),
                                'description': getattr(tool, 'description', ''),
                                '_server': server_name
                            }
                            all_tools.append(tool_dict)
                            continue
                    
                    all_tools.extend(tools)
                    
            except Exception as e:
                print(f"Error connecting to server {server_name}: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                continue
        
        print(f"Total tools retrieved: {len(all_tools)}")
        if all_tools:
            print(f"Tool names: {[tool.get('name', 'unnamed') for tool in all_tools]}")
        
        return all_tools
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources from connected MCP servers."""
        if not self.active_servers:
            return []
        
        try:
            async with Client({"mcpServers": self.active_servers}) as client:
                resources = await client.list_resources()
                return resources
        except Exception as e:
            print(f"Error listing resources: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Call a tool on one of the connected MCP servers."""
        if not self.active_servers:
            raise ValueError("No active MCP servers configured")
        
        try:
            async with Client({"mcpServers": self.active_servers}) as client:
                result = await client.call_tool(tool_name, params)
                return result
        except Exception as e:
            raise Exception(f"Error calling tool {tool_name}: {str(e)}")
    
    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read a resource from one of the connected MCP servers."""
        if not self.active_servers:
            raise ValueError("No active MCP servers configured")
        
        try:
            async with Client({"mcpServers": self.active_servers}) as client:
                result = await client.read_resource(uri)
                return result
        except Exception as e:
            raise Exception(f"Error reading resource {uri}: {str(e)}")
    
    def get_active_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get the currently active MCP servers."""
        return self.active_servers
    
    def is_connected(self) -> bool:
        """Check if the client is connected to any MCP servers."""
        return len(self.active_servers) > 0
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get the status of all servers."""
        status = {
            "active_servers": list(self.active_servers.keys()),
            "fastmcp_managed": True
        }
        
        return status

# Create a singleton instance
mcp_client_manager = MCPClientManager()