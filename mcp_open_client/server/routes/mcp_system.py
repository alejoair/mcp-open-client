"""
MCP System Health and Monitoring API Routes
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..mcp_models import MCPOperationResponse
from ...services.mcp_server_manager import mcp_server_manager
from ...services.mcp_process_manager import mcp_process_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp/system", tags=["MCP System"])


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health():
    """Get overall MCP system health"""
    try:
        health = await mcp_server_manager.get_system_health()

        # Add additional system metrics
        process_statuses = await mcp_process_manager.get_all_process_status()

        # Calculate additional metrics
        total_memory_mb = 0
        total_cpu_percent = 0
        active_processes = 0

        for status in process_statuses.values():
            if status.get("running"):
                active_processes += 1
                total_memory_mb += status.get("memory_mb", 0)
                total_cpu_percent += status.get("cpu_percent", 0)

        health.update({
            "processes": {
                "active": active_processes,
                "total_memory_mb": round(total_memory_mb, 2),
                "avg_cpu_percent": round(total_cpu_percent / max(active_processes, 1), 2),
                "details": process_statuses
            }
        })

        logger.info(f"📊 System health check: {health['healthy']} ({health['running_servers']}/{health['total_servers']} running)")
        return health

    except Exception as e:
        logger.error(f"❌ Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=Dict[str, Any])
async def get_system_status():
    """Get detailed system status"""
    try:
        # Get all server statuses
        servers = await mcp_server_manager.list_servers()
        server_statuses = {}

        for server in servers:
            status = await mcp_server_manager.get_server_status(server.id)
            server_statuses[server.id] = {
                "name": server.name,
                "status": server.status.value,
                "type": server.type.value,
                "process": status.get("process", {}) if status else {},
                "health": {
                    "last_ping": server.health.last_ping.isoformat() if server.health.last_ping else None,
                    "uptime": server.health.uptime,
                    "process_id": server.health.process_id,
                    "error_count": len(server.health.errors)
                }
            }

        # Get process manager status
        all_processes = await mcp_process_manager.get_all_process_status()

        # Get health data for timestamp
        health_data = await mcp_server_manager.get_system_health()

        return {
            "timestamp": health_data["timestamp"],
            "system_healthy": health_data["healthy"],
            "summary": {
                "total_servers": len(servers),
                "running_servers": sum(1 for s in servers if s.status.value == "running"),
                "active_processes": len([p for p in all_processes.values() if p.get("running")]),
                "total_errors": sum(len(s.health.errors) for s in servers)
            },
            "servers": server_statuses,
            "processes": all_processes
        }

    except Exception as e:
        logger.error(f"❌ Error getting system status: {e}")
        # Return basic health data as fallback
        health_data = await mcp_server_manager.get_system_health()
        return {
            "error": str(e),
            "fallback_health": health_data
        }


@router.post("/cleanup", response_model=MCPOperationResponse)
async def cleanup_system():
    """Clean up orphaned processes and resources"""
    try:
        logger.info("🧹 Starting system cleanup")

        # Stop all processes
        stop_results = await mcp_process_manager.stop_all_processes()

        # Count results
        stopped_count = sum(1 for success in stop_results.values() if success)
        total_count = len(stop_results)

        # Update server statuses to reflect cleanup
        servers = await mcp_server_manager.list_servers()
        for server in servers:
            if server.id in stop_results:
                # Force update status if process was stopped
                server.status = "stopped"

        message = f"Cleanup completed: stopped {stopped_count}/{total_count} processes"
        logger.info(f"✅ {message}")

        return MCPOperationResponse(
            success=stopped_count == total_count,
            message=message,
            data={
                "stopped_processes": stopped_count,
                "total_processes": total_count,
                "results": stop_results
            }
        )

    except Exception as e:
        logger.error(f"❌ Error during system cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_system_logs():
    """Get aggregated system logs from all servers"""
    try:
        servers = await mcp_server_manager.list_servers()
        all_logs = []

        for server in servers:
            try:
                server_logs = await mcp_server_manager.get_server_logs(server.id, lines=50)

                # Add server context to each log entry
                for log in server_logs:
                    log["server_id"] = server.id
                    log["server_name"] = server.name
                    all_logs.append(log)

            except Exception as e:
                logger.warning(f"⚠️ Could not get logs for server {server.id}: {e}")
                # Add error entry
                all_logs.append({
                    "timestamp": "unknown",
                    "stream": "system",
                    "message": f"Error retrieving logs: {str(e)}",
                    "server_id": server.id,
                    "server_name": server.name
                })

        # Sort by timestamp (newest first)
        # Note: This is basic sorting, in production you'd want proper timestamp parsing
        all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Limit to most recent 200 entries
        return all_logs[:200]

    except Exception as e:
        logger.error(f"❌ Error getting system logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics():
    """Get system performance metrics"""
    try:
        # Get basic health data
        health = await mcp_server_manager.get_system_health()

        # Get process metrics
        process_statuses = await mcp_process_manager.get_all_process_status()

        # Calculate aggregated metrics
        total_memory = 0
        total_cpu = 0
        running_count = 0
        uptime_total = 0

        for status in process_statuses.values():
            if status.get("running"):
                running_count += 1
                total_memory += status.get("memory_mb", 0)
                total_cpu += status.get("cpu_percent", 0)
                uptime_total += status.get("uptime", 0)

        metrics = {
            "timestamp": health["timestamp"],
            "system": {
                "healthy": health["healthy"],
                "uptime_avg_seconds": uptime_total / max(running_count, 1)
            },
            "servers": {
                "total": health["total_servers"],
                "running": health["running_servers"],
                "stopped": health["stopped_servers"],
                "error": health["error_servers"]
            },
            "resources": {
                "total_memory_mb": round(total_memory, 2),
                "avg_memory_mb": round(total_memory / max(running_count, 1), 2),
                "total_cpu_percent": round(total_cpu, 2),
                "avg_cpu_percent": round(total_cpu / max(running_count, 1), 2),
                "active_processes": running_count
            },
            "health_score": 100.0 if health["healthy"] else 0.0
        }

        # Adjust health score based on error rate
        if health["total_servers"] > 0:
            error_rate = health["error_servers"] / health["total_servers"]
            metrics["health_score"] = max(0, 100 - (error_rate * 100))

        logger.debug(f"📊 System metrics: {metrics['health_score']}% health score")
        return metrics

    except Exception as e:
        logger.error(f"❌ Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=Dict[str, Any])
async def get_system_info():
    """Get general system information"""
    try:
        import platform
        import psutil
        from pathlib import Path

        # Get MCP client info
        config_dir = Path.home() / ".mcp-client"

        system_info = {
            "mcp_client": {
                "version": "1.0.0",  # TODO: Get from package
                "config_dir": str(config_dir),
                "config_exists": config_dir.exists()
            },
            "platform": {
                "system": platform.system(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_free_gb": round(psutil.disk_usage('.').free / (1024**3), 2)
            }
        }

        # Add MCP-specific stats
        health = await mcp_server_manager.get_system_health()
        system_info["mcp_stats"] = {
            "total_servers": health["total_servers"],
            "running_servers": health["running_servers"],
            "process_count": health["process_count"],
            "system_healthy": health["healthy"]
        }

        return system_info

    except Exception as e:
        logger.error(f"❌ Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))