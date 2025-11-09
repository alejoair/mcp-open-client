"""
MCP Server Manager - Core service for managing MCP servers
"""
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from ..server.mcp_models import (
    MCPServer, MCPServerConfig, MCPServerConnection, MCPServerMetadata,
    MCPServerHealth, MCPServerStatus, CreateMCPServerRequest, UpdateMCPServerRequest,
    MCPTool
)
from .mcp_process_manager import mcp_process_manager

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Central manager for MCP servers"""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.mcp-open-client"))
        self.servers_file = self.config_dir / "servers.json"
        self.servers: Dict[str, MCPServer] = {}

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing servers
        self._load_servers()

    def _load_servers(self):
        """Load servers from persistent storage"""
        try:
            if self.servers_file.exists():
                with open(self.servers_file, 'r', encoding='utf-8') as f:
                    servers_data = json.load(f)

                for server_data in servers_data.values():
                    server = MCPServer(**server_data)
                    self.servers[server.id] = server

                logger.info(f"Loaded {len(self.servers)} MCP servers from {self.servers_file}")
            else:
                logger.info("No existing servers file found, starting with empty server list")

        except Exception as e:
            logger.error(f"Error loading servers: {e}")
            self.servers = {}

    def _save_servers(self):
        """Save servers to persistent storage"""
        try:
            servers_data = {}
            for server_id, server in self.servers.items():
                servers_data[server_id] = server.model_dump()

            with open(self.servers_file, 'w', encoding='utf-8') as f:
                json.dump(servers_data, f, indent=2, default=str)

            logger.debug(f"Saved {len(self.servers)} servers to {self.servers_file}")

        except Exception as e:
            logger.error(f"Error saving servers: {e}")

    async def create_server(self, request: CreateMCPServerRequest) -> MCPServer:
        """Create a new MCP server"""
        try:
            # Create server object
            server = MCPServer(
                name=request.name,
                description=request.description,
                type=request.type,
                config=request.config,
                connection=request.connection or MCPServerConnection(),
                metadata=MCPServerMetadata(),
                health=MCPServerHealth()
            )

            # Store server
            self.servers[server.id] = server
            self._save_servers()

            logger.info(f"✅ Created MCP server '{server.name}' (ID: {server.id})")
            return server

        except Exception as e:
            logger.error(f"❌ Error creating MCP server: {e}")
            raise

    async def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID"""
        return self.servers.get(server_id)

    async def list_servers(self) -> List[MCPServer]:
        """Get all servers"""
        return list(self.servers.values())

    async def update_server(self, server_id: str, request: UpdateMCPServerRequest) -> Optional[MCPServer]:
        """Update server configuration"""
        try:
            if server_id not in self.servers:
                return None

            server = self.servers[server_id]

            # Update fields if provided
            if request.name is not None:
                server.name = request.name
            if request.description is not None:
                server.description = request.description
            if request.config is not None:
                server.config = request.config
            if request.connection is not None:
                server.connection = request.connection

            # Update metadata
            server.metadata.updated_at = datetime.now()

            self._save_servers()
            logger.info(f"✅ Updated MCP server '{server.name}' (ID: {server_id})")
            return server

        except Exception as e:
            logger.error(f"❌ Error updating MCP server {server_id}: {e}")
            raise

    async def delete_server(self, server_id: str) -> bool:
        """Delete server"""
        try:
            if server_id not in self.servers:
                return False

            server = self.servers[server_id]

            # Stop server if running
            if server.status == MCPServerStatus.RUNNING:
                await self.stop_server(server_id)

            # Remove from storage
            del self.servers[server_id]
            self._save_servers()

            logger.info(f"✅ Deleted MCP server '{server.name}' (ID: {server_id})")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting MCP server {server_id}: {e}")
            return False

    async def start_server(self, server_id: str) -> bool:
        """Start a server"""
        try:
            if server_id not in self.servers:
                logger.error(f"Server {server_id} not found")
                return False

            server = self.servers[server_id]

            if server.status == MCPServerStatus.RUNNING:
                logger.warning(f"Server {server_id} is already running")
                return True

            # Update status
            server.status = MCPServerStatus.STARTING
            logger.info(f"🚀 Starting MCP server '{server.name}' (ID: {server_id})")

            # Start process
            success = await mcp_process_manager.start_subprocess(
                server_id=server_id,
                command=server.config.command,
                args=server.config.args,
                env=server.config.env,
                working_dir=server.config.working_dir,
                timeout=server.config.timeout
            )

            if success:
                server.status = MCPServerStatus.RUNNING
                server.health.last_ping = datetime.now()
                logger.info(f"✅ MCP server '{server.name}' started successfully")
            else:
                server.status = MCPServerStatus.ERROR
                server.health.errors.append(f"Failed to start at {datetime.now()}")
                logger.error(f"❌ Failed to start MCP server '{server.name}'")

            self._save_servers()
            return success

        except Exception as e:
            logger.error(f"❌ Error starting MCP server {server_id}: {e}")
            if server_id in self.servers:
                self.servers[server_id].status = MCPServerStatus.ERROR
                self.servers[server_id].health.errors.append(f"Start error: {str(e)}")
                self._save_servers()
            return False

    async def stop_server(self, server_id: str) -> bool:
        """Stop a server"""
        try:
            if server_id not in self.servers:
                logger.error(f"Server {server_id} not found")
                return False

            server = self.servers[server_id]

            if server.status == MCPServerStatus.STOPPED:
                logger.warning(f"Server {server_id} is already stopped")
                return True

            # Update status
            server.status = MCPServerStatus.STOPPING
            logger.info(f"🛑 Stopping MCP server '{server.name}' (ID: {server_id})")

            # Stop process
            success = await mcp_process_manager.stop_subprocess(server_id)

            if success:
                server.status = MCPServerStatus.STOPPED
                logger.info(f"✅ MCP server '{server.name}' stopped successfully")
            else:
                server.status = MCPServerStatus.ERROR
                server.health.errors.append(f"Failed to stop at {datetime.now()}")
                logger.error(f"❌ Failed to stop MCP server '{server.name}'")

            self._save_servers()
            return success

        except Exception as e:
            logger.error(f"❌ Error stopping MCP server {server_id}: {e}")
            if server_id in self.servers:
                self.servers[server_id].status = MCPServerStatus.ERROR
                self.servers[server_id].health.errors.append(f"Stop error: {str(e)}")
                self._save_servers()
            return False

    async def restart_server(self, server_id: str) -> bool:
        """Restart a server"""
        try:
            if server_id not in self.servers:
                logger.error(f"Server {server_id} not found")
                return False

            server = self.servers[server_id]
            logger.info(f"🔄 Restarting MCP server '{server.name}' (ID: {server_id})")

            # Stop first
            if server.status == MCPServerStatus.RUNNING:
                await self.stop_server(server_id)

            # Wait a moment
            import asyncio
            await asyncio.sleep(1.0)

            # Start again
            return await self.start_server(server_id)

        except Exception as e:
            logger.error(f"❌ Error restarting MCP server {server_id}: {e}")
            return False

    async def ping_server(self, server_id: str) -> bool:
        """Ping server to check health"""
        try:
            if server_id not in self.servers:
                return False

            server = self.servers[server_id]

            if server.status != MCPServerStatus.RUNNING:
                return False

            # Check process health
            ping_result = await mcp_process_manager.ping_process(server_id)

            if ping_result:
                server.health.last_ping = datetime.now()
                # Calculate uptime
                process_status = await mcp_process_manager.get_process_status(server_id)
                if process_status.get("running"):
                    server.health.uptime = process_status.get("uptime", 0)
                    server.health.process_id = process_status.get("process_id")
            else:
                server.status = MCPServerStatus.ERROR
                server.health.errors.append(f"Ping failed at {datetime.now()}")

            self._save_servers()
            return ping_result

        except Exception as e:
            logger.error(f"❌ Error pinging MCP server {server_id}: {e}")
            return False

    async def get_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed server status"""
        try:
            if server_id not in self.servers:
                return None

            server = self.servers[server_id]

            # Get process status
            process_status = await mcp_process_manager.get_process_status(server_id)

            # Update server status based on process
            if process_status.get("running"):
                if server.status != MCPServerStatus.RUNNING:
                    server.status = MCPServerStatus.RUNNING
            else:
                if server.status == MCPServerStatus.RUNNING:
                    server.status = MCPServerStatus.STOPPED

            status = {
                "server": server.model_dump(),
                "process": process_status
            }

            return status

        except Exception as e:
            logger.error(f"❌ Error getting server status {server_id}: {e}")
            return None

    async def get_server_logs(self, server_id: str, lines: int = 100) -> List[Dict[str, Any]]:
        """Get server logs"""
        try:
            return await mcp_process_manager.get_process_logs(server_id, lines)
        except Exception as e:
            logger.error(f"❌ Error getting server logs {server_id}: {e}")
            return []

    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all servers"""
        results = {}
        for server_id in self.servers:
            results[server_id] = await self.start_server(server_id)
        return results

    async def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all servers"""
        results = {}
        for server_id in self.servers:
            results[server_id] = await self.stop_server(server_id)
        return results

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            total_servers = len(self.servers)
            running_servers = sum(1 for s in self.servers.values() if s.status == MCPServerStatus.RUNNING)
            error_servers = sum(1 for s in self.servers.values() if s.status == MCPServerStatus.ERROR)

            # Get process overview
            process_statuses = await mcp_process_manager.get_all_process_status()

            return {
                "total_servers": total_servers,
                "running_servers": running_servers,
                "stopped_servers": total_servers - running_servers - error_servers,
                "error_servers": error_servers,
                "process_count": len(process_statuses),
                "healthy": error_servers == 0,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error getting system health: {e}")
            return {
                "error": str(e),
                "healthy": False,
                "timestamp": datetime.now().isoformat()
            }


# Global instance
mcp_server_manager = MCPServerManager()