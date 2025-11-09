"""
MCP Server Management API Routes
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..mcp_models import (
    MCPServer, CreateMCPServerRequest, UpdateMCPServerRequest,
    MCPServerResponse, MCPServersListResponse, MCPServerStatusResponse,
    MCPOperationResponse
)
from ...services.mcp_server_manager import mcp_server_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp/servers", tags=["MCP Servers"])


@router.post("", response_model=MCPServerResponse)
async def create_server(request: CreateMCPServerRequest):
    """Create a new MCP server"""
    try:
        logger.info(f"🚀 Creating MCP server: {request.name}")
        server = await mcp_server_manager.create_server(request)

        return MCPServerResponse(
            success=True,
            server=server,
            message=f"Server '{server.name}' created successfully"
        )

    except Exception as e:
        logger.error(f"❌ Error creating server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=MCPServersListResponse)
async def list_servers():
    """Get all MCP servers"""
    try:
        servers = await mcp_server_manager.list_servers()

        return MCPServersListResponse(
            success=True,
            servers=servers,
            total=len(servers)
        )

    except Exception as e:
        logger.error(f"❌ Error listing servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}", response_model=MCPServerResponse)
async def get_server(server_id: str):
    """Get server by ID"""
    try:
        server = await mcp_server_manager.get_server(server_id)

        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        return MCPServerResponse(
            success=True,
            server=server,
            message="Server retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{server_id}", response_model=MCPServerResponse)
async def update_server(server_id: str, request: UpdateMCPServerRequest):
    """Update server configuration"""
    try:
        server = await mcp_server_manager.update_server(server_id, request)

        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        return MCPServerResponse(
            success=True,
            server=server,
            message=f"Server '{server.name}' updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{server_id}", response_model=MCPOperationResponse)
async def delete_server(server_id: str):
    """Delete a server"""
    try:
        success = await mcp_server_manager.delete_server(server_id)

        if not success:
            raise HTTPException(status_code=404, detail="Server not found")

        return MCPOperationResponse(
            success=True,
            message="Server deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/start", response_model=MCPOperationResponse)
async def start_server(server_id: str):
    """Start a server"""
    try:
        success = await mcp_server_manager.start_server(server_id)

        if not success:
            return MCPOperationResponse(
                success=False,
                message="Failed to start server",
                data={"server_id": server_id}
            )

        return MCPOperationResponse(
            success=True,
            message="Server started successfully",
            data={"server_id": server_id}
        )

    except Exception as e:
        logger.error(f"❌ Error starting server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/stop", response_model=MCPOperationResponse)
async def stop_server(server_id: str):
    """Stop a server"""
    try:
        success = await mcp_server_manager.stop_server(server_id)

        if not success:
            return MCPOperationResponse(
                success=False,
                message="Failed to stop server",
                data={"server_id": server_id}
            )

        return MCPOperationResponse(
            success=True,
            message="Server stopped successfully",
            data={"server_id": server_id}
        )

    except Exception as e:
        logger.error(f"❌ Error stopping server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/restart", response_model=MCPOperationResponse)
async def restart_server(server_id: str):
    """Restart a server"""
    try:
        success = await mcp_server_manager.restart_server(server_id)

        if not success:
            return MCPOperationResponse(
                success=False,
                message="Failed to restart server",
                data={"server_id": server_id}
            )

        return MCPOperationResponse(
            success=True,
            message="Server restarted successfully",
            data={"server_id": server_id}
        )

    except Exception as e:
        logger.error(f"❌ Error restarting server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/status", response_model=Dict[str, Any])
async def get_server_status(server_id: str):
    """Get detailed server status"""
    try:
        status = await mcp_server_manager.get_server_status(server_id)

        if not status:
            raise HTTPException(status_code=404, detail="Server not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting server status {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/logs", response_model=List[Dict[str, Any]])
async def get_server_logs(
    server_id: str,
    lines: int = Query(100, ge=1, le=1000, description="Number of log lines to retrieve")
):
    """Get server logs"""
    try:
        logs = await mcp_server_manager.get_server_logs(server_id, lines)
        return logs

    except Exception as e:
        logger.error(f"❌ Error getting server logs {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/ping", response_model=MCPOperationResponse)
async def ping_server(server_id: str):
    """Ping server to check health"""
    try:
        success = await mcp_server_manager.ping_server(server_id)

        return MCPOperationResponse(
            success=success,
            message="Server is responsive" if success else "Server is not responsive",
            data={"server_id": server_id, "responsive": success}
        )

    except Exception as e:
        logger.error(f"❌ Error pinging server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-all", response_model=Dict[str, Any])
async def start_all_servers():
    """Start all servers"""
    try:
        results = await mcp_server_manager.start_all_servers()

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        return {
            "success": successful == total,
            "message": f"Started {successful}/{total} servers",
            "results": results,
            "total": total,
            "successful": successful,
            "failed": total - successful
        }

    except Exception as e:
        logger.error(f"❌ Error starting all servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-all", response_model=Dict[str, Any])
async def stop_all_servers():
    """Stop all servers"""
    try:
        results = await mcp_server_manager.stop_all_servers()

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        return {
            "success": successful == total,
            "message": f"Stopped {successful}/{total} servers",
            "results": results,
            "total": total,
            "successful": successful,
            "failed": total - successful
        }

    except Exception as e:
        logger.error(f"❌ Error stopping all servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))