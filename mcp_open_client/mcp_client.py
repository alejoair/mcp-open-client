import asyncio
import json
import os
import subprocess
import signal
import sys
from typing import Dict, Any, List, Optional, Union
from fastmcp import Client, Context

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
        self.server_processes = {}  # Track launched server processes
    
    async def _launch_local_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Launch a local MCP server process."""
        if server_name in self.server_processes:
            # Server already running
            process = self.server_processes[server_name]
            if process.poll() is None:  # Process is still running
                print(f"Server {server_name} is already running")
                return True
            else:
                # Process died, remove it from tracking
                del self.server_processes[server_name]
        
        try:
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            if not command:
                print(f"No command specified for server {server_name}")
                return False
            
            # Prepare the full command
            full_command = [command] + args
            
            # Prepare environment variables
            process_env = os.environ.copy()
            process_env.update(env)
            
            print(f"Launching MCP server {server_name}: {' '.join(full_command)}")
            
            # Launch the process
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env,
                text=True,
                bufsize=0
            )
            
            # Store the process for later management
            self.server_processes[server_name] = process
            
            # Give the server a moment to start up
            await asyncio.sleep(1)
            
            # Check if the process is still running
            if process.poll() is None:
                print(f"Successfully launched MCP server {server_name} (PID: {process.pid})")
                return True
            else:
                print(f"Failed to launch MCP server {server_name} - process exited immediately")
                if server_name in self.server_processes:
                    del self.server_processes[server_name]
                return False
                
        except Exception as e:
            print(f"Error launching MCP server {server_name}: {str(e)}")
            return False
    
    async def _stop_local_server(self, server_name: str):
        """Stop a local MCP server process."""
        if server_name not in self.server_processes:
            return
        
        process = self.server_processes[server_name]
        try:
            if process.poll() is None:  # Process is still running
                print(f"Stopping MCP server {server_name} (PID: {process.pid})")
                
                # Try graceful shutdown first
                process.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    print(f"Force killing MCP server {server_name}")
                    process.kill()
                    process.wait()
                
                print(f"Stopped MCP server {server_name}")
            
        except Exception as e:
            print(f"Error stopping MCP server {server_name}: {str(e)}")
        finally:
            del self.server_processes[server_name]
    
    def _is_local_server(self, server_config: Dict[str, Any]) -> bool:
        """Check if a server configuration represents a local server."""
        return "command" in server_config and "args" in server_config
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize the MCP client with the given configuration."""
        # Prevent concurrent initializations to avoid infinite loops
        if self._initializing:
            print("MCP client initialization already in progress, skipping...")
            return False
        
        try:
            self._initializing = True
            self.config = config
            
            print("Starting MCP client initialization...")
            
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
                    
                    # Launch local servers first
                    launched_servers = {}
                    for server_name, server_config in active_servers.items():
                        if self._is_local_server(server_config):
                            print(f"Attempting to launch local server: {server_name}")
                            success = await self._launch_local_server(server_name, server_config)
                            if success:
                                launched_servers[server_name] = server_config
                                print(f"Successfully launched local server: {server_name}")
                            else:
                                print(f"Failed to launch local server {server_name}, skipping...")
                        else:
                            # Non-local servers (e.g., remote servers) are added directly
                            launched_servers[server_name] = server_config
                            print(f"Added non-local server: {server_name}")
                    
                    if launched_servers:
                        # Give servers additional time to fully initialize
                        if any(self._is_local_server(config) for config in launched_servers.values()):
                            print("Waiting for local servers to fully initialize...")
                            await asyncio.sleep(2)
                        
                        # Create configuration with only successfully launched servers
                        client_config = {"mcpServers": launched_servers}
                        try:
                            print("Creating MCP client...")
                            self.client = Client(client_config)
                            print(f"Successfully created MCP client with {len(launched_servers)} servers")
                            
                            # Check client connection status
                            print("Checking client connection...")
                            if await self._check_client_connection():
                                print("Client connection verified")
                                return True
                            else:
                                print("Client initialized but connection check failed")
                                return False
                        except Exception as e:
                            print(f"Error initializing MCP client: {str(e)}")
                            print(f"Client configuration: {json.dumps(client_config, indent=2)}")
                            # Stop any launched servers if client creation failed
                            for server_name in launched_servers:
                                if server_name in self.server_processes:
                                    await self._stop_local_server(server_name)
                            return False
                    else:
                        print("No servers could be launched or configured")
                        return False
                else:
                    print("No active servers found in configuration")
                    return False
            else:
                print("No MCP servers defined in configuration")
                return False
        except Exception as e:
            print(f"Unexpected error during MCP client initialization: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self._initializing = False  # Reset the flag when done
            print("MCP client initialization process completed")

    async def _check_client_connection(self) -> bool:
        """Check if the client is properly connected to the servers."""
        try:
            print("Starting client connection check...")
            # Use the context manager to ensure proper connection
            async with self.client as ctx:
                print("Client context manager entered successfully")
                print("Client configuration:", self.client.config)
                print("Attempting to list tools...")
                tools = await self.client.list_tools()
                print(f"Successfully listed {len(tools)} tools")
            return True
        except Exception as e:
            print(f"Error checking client connection: {str(e)}")
            print("Client configuration:", self.client.config)
            print("Active servers:", self.active_servers)
            import traceback
            traceback.print_exc()
            return False

    async def close(self):
        """Close the MCP client connection and stop local servers."""
        if self.client:
            # The fastmcp Client doesn't have a close method
            # Just set it to None to allow garbage collection
            self.client = None
        
        # Stop all running local servers
        for server_name in list(self.server_processes.keys()):
            await self._stop_local_server(server_name)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from connected MCP servers."""
        if not self.client:
            print("MCP client is not initialized")
            return []
        
        try:
            print("Attempting to list tools...")
            async with self.client:
                tools = await self.client.list_tools()
            print(f"Retrieved {len(tools)} MCP tools")
            return tools
        except Exception as e:
            print(f"Error listing tools: {str(e)}")
            print("MCP client status:")
            print(json.dumps(self.get_server_status(), indent=2))
            
            # Additional debugging information
            print("Debugging information:")
            print(f"Client object: {self.client}")
            print(f"Active servers: {self.active_servers}")
            
            # Attempt to get more information from the client
            try:
                info = await self.client.get_info()
                print(f"Client info: {info}")
            except Exception as info_error:
                print(f"Error getting client info: {str(info_error)}")
            
            return []
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources from connected MCP servers."""
        if not self.client:
            return []
        
        try:
            async with self.client:
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
            async with self.client:
                result = await self.client.call_tool(tool_name, params)
                return result
        except Exception as e:
            raise Exception(f"Error calling tool {tool_name}: {str(e)}")
    
    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read a resource from one of the connected MCP servers."""
        if not self.client:
            raise ValueError("MCP client not initialized")
        
        try:
            async with self.client:
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
    
    def get_server_processes(self) -> Dict[str, subprocess.Popen]:
        """Get the currently running server processes."""
        return self.server_processes.copy()
    
    def get_server_status(self) -> Dict[str, str]:
        """Get the status of all configured servers."""
        status = {}
        for server_name, server_config in self.active_servers.items():
            if self._is_local_server(server_config):
                if server_name in self.server_processes:
                    process = self.server_processes[server_name]
                    if process.poll() is None:
                        status[server_name] = f"Running (PID: {process.pid})"
                    else:
                        status[server_name] = "Stopped (process exited)"
                else:
                    status[server_name] = "Not started"
            else:
                status[server_name] = "Remote server"
        return status

# Create a singleton instance
mcp_client_manager = MCPClientManager()