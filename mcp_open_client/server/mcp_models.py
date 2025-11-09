"""
MCP Server Management - Pydantic Models
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
import uuid


class MCPServerStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class MCPTransportType(str, Enum):
    STDIO = "stdio"
    TCP = "tcp"
    WEBSOCKET = "websocket"


class MCPServerType(str, Enum):
    SUBPROCESS = "subprocess"
    DOCKER = "docker"
    STDIO = "stdio"


class MCPServerConfig(BaseModel):
    """Server configuration settings"""
    command: str = Field(..., description="Command to execute")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    working_dir: Optional[str] = Field(None, description="Working directory")
    timeout: float = Field(30.0, description="Startup timeout in seconds")


class MCPServerConnection(BaseModel):
    """Server connection settings"""
    transport: MCPTransportType = Field(MCPTransportType.STDIO, description="Transport protocol")
    host: Optional[str] = Field(None, description="Host address for TCP/WebSocket")
    port: Optional[int] = Field(None, description="Port number for TCP/WebSocket")


class MCPServerHealth(BaseModel):
    """Server health monitoring data"""
    last_ping: Optional[datetime] = Field(None, description="Last successful ping")
    uptime: float = Field(0.0, description="Uptime in seconds")
    errors: List[str] = Field(default_factory=list, description="Recent error messages")
    process_id: Optional[int] = Field(None, description="Process ID if subprocess")


class MCPServerMetadata(BaseModel):
    """Server metadata"""
    version: Optional[str] = Field(None, description="Server version")
    author: Optional[str] = Field(None, description="Server author")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class MCPServer(BaseModel):
    """Complete MCP Server representation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique server ID")
    name: str = Field(..., description="Human-readable server name")
    description: Optional[str] = Field(None, description="Server description")
    status: MCPServerStatus = Field(MCPServerStatus.STOPPED, description="Current server status")
    type: MCPServerType = Field(MCPServerType.SUBPROCESS, description="Server type")
    config: MCPServerConfig = Field(..., description="Server configuration")
    connection: MCPServerConnection = Field(default_factory=MCPServerConnection, description="Connection settings")
    metadata: MCPServerMetadata = Field(default_factory=MCPServerMetadata, description="Server metadata")
    health: MCPServerHealth = Field(default_factory=MCPServerHealth, description="Health monitoring data")


class MCPTool(BaseModel):
    """MCP Tool representation"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server_id: str = Field(..., description="Parent server ID")
    schema: Dict[str, Any] = Field(..., description="Tool JSON schema")
    enabled: bool = Field(True, description="Whether tool is enabled")
    usage_count: int = Field(0, description="Number of times used")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")


# Request/Response models
class CreateMCPServerRequest(BaseModel):
    """Request to create a new MCP server"""
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    type: MCPServerType = Field(MCPServerType.SUBPROCESS, description="Server type")
    config: MCPServerConfig = Field(..., description="Server configuration")
    connection: Optional[MCPServerConnection] = Field(None, description="Connection settings")


class UpdateMCPServerRequest(BaseModel):
    """Request to update MCP server configuration"""
    name: Optional[str] = Field(None, description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    config: Optional[MCPServerConfig] = Field(None, description="Server configuration")
    connection: Optional[MCPServerConnection] = Field(None, description="Connection settings")


class MCPServerResponse(BaseModel):
    """Response with MCP server data"""
    success: bool = Field(..., description="Operation success")
    server: Optional[MCPServer] = Field(None, description="Server data")
    message: Optional[str] = Field(None, description="Response message")


class MCPServersListResponse(BaseModel):
    """Response with list of MCP servers"""
    success: bool = Field(..., description="Operation success")
    servers: List[MCPServer] = Field(..., description="List of servers")
    total: int = Field(..., description="Total server count")


class MCPServerStatusResponse(BaseModel):
    """Response with server status information"""
    success: bool = Field(..., description="Operation success")
    server_id: str = Field(..., description="Server ID")
    status: MCPServerStatus = Field(..., description="Current status")
    health: MCPServerHealth = Field(..., description="Health data")
    message: Optional[str] = Field(None, description="Status message")


class MCPToolsResponse(BaseModel):
    """Response with MCP tools data"""
    success: bool = Field(..., description="Operation success")
    tools: List[MCPTool] = Field(..., description="List of tools")
    total: int = Field(..., description="Total tool count")
    server_id: Optional[str] = Field(None, description="Filter by server ID")


class MCPOperationResponse(BaseModel):
    """Generic operation response"""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")