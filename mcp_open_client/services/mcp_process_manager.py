"""
MCP Process Manager - Handles subprocess lifecycle for MCP servers
"""
import asyncio
import logging
import time
import signal
import psutil
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPProcess:
    """Represents a running MCP server process"""
    process_id: int
    server_id: str
    process: asyncio.subprocess.Process
    command: str
    started_at: datetime
    stdout_reader: Optional[asyncio.StreamReader] = None
    stderr_reader: Optional[asyncio.StreamReader] = None


class MCPProcessManager:
    """Manages MCP server processes and their lifecycle"""

    def __init__(self):
        self.processes: Dict[str, MCPProcess] = {}
        self.process_logs: Dict[str, list] = {}
        self.max_log_lines = 1000

    async def start_subprocess(self, server_id: str, command: str, args: list,
                              env: Dict[str, str] = None, working_dir: str = None,
                              timeout: float = 30.0) -> bool:
        """
        Start a new MCP server subprocess

        Args:
            server_id: Unique server identifier
            command: Command to execute
            args: Command arguments
            env: Environment variables
            working_dir: Working directory
            timeout: Startup timeout

        Returns:
            bool: Success status
        """
        try:
            if server_id in self.processes:
                logger.warning(f"Process for server {server_id} already exists")
                return False

            # Build full command
            full_command = [command] + args
            logger.info(f"Starting MCP server {server_id}: {' '.join(full_command)}")

            # Prepare environment
            process_env = dict(env) if env else {}

            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=process_env,
                cwd=working_dir
            )

            # Create process tracking object
            mcp_process = MCPProcess(
                process_id=process.pid,
                server_id=server_id,
                process=process,
                command=' '.join(full_command),
                started_at=datetime.now(),
                stdout_reader=process.stdout,
                stderr_reader=process.stderr
            )

            self.processes[server_id] = mcp_process
            self.process_logs[server_id] = []

            # Start log monitoring
            asyncio.create_task(self._monitor_process_logs(server_id))

            # Wait for process to be ready (basic check)
            await asyncio.sleep(1.0)  # Give process time to start

            if await self.is_process_running(server_id):
                logger.info(f"✅ MCP server {server_id} started successfully (PID: {process.pid})")
                return True
            else:
                logger.error(f"❌ MCP server {server_id} failed to start")
                await self.stop_subprocess(server_id)
                return False

        except Exception as e:
            logger.error(f"❌ Error starting MCP server {server_id}: {e}")
            if server_id in self.processes:
                del self.processes[server_id]
            return False

    async def stop_subprocess(self, server_id: str, timeout: float = 10.0) -> bool:
        """
        Stop a running MCP server subprocess

        Args:
            server_id: Server identifier
            timeout: Graceful shutdown timeout

        Returns:
            bool: Success status
        """
        try:
            if server_id not in self.processes:
                logger.warning(f"No process found for server {server_id}")
                return False

            mcp_process = self.processes[server_id]
            process = mcp_process.process

            logger.info(f"Stopping MCP server {server_id} (PID: {process.pid})")

            # Try graceful shutdown first
            process.terminate()

            try:
                # Wait for graceful shutdown
                await asyncio.wait_for(process.wait(), timeout=timeout)
                logger.info(f"✅ MCP server {server_id} stopped gracefully")
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown failed
                logger.warning(f"⚠️ MCP server {server_id} didn't stop gracefully, force killing")
                process.kill()
                await process.wait()
                logger.info(f"✅ MCP server {server_id} force stopped")

            # Cleanup
            del self.processes[server_id]
            # Keep logs for debugging but limit size
            if server_id in self.process_logs:
                self.process_logs[server_id] = self.process_logs[server_id][-100:]

            return True

        except Exception as e:
            logger.error(f"❌ Error stopping MCP server {server_id}: {e}")
            # Cleanup anyway
            if server_id in self.processes:
                del self.processes[server_id]
            return False

    async def restart_subprocess(self, server_id: str, command: str, args: list,
                                env: Dict[str, str] = None, working_dir: str = None,
                                timeout: float = 30.0) -> bool:
        """Restart a MCP server subprocess"""
        logger.info(f"Restarting MCP server {server_id}")

        # Stop if running
        if await self.is_process_running(server_id):
            await self.stop_subprocess(server_id)

        # Wait a moment before restart
        await asyncio.sleep(1.0)

        # Start again
        return await self.start_subprocess(server_id, command, args, env, working_dir, timeout)

    async def is_process_running(self, server_id: str) -> bool:
        """Check if a process is running"""
        try:
            if server_id not in self.processes:
                return False

            process = self.processes[server_id].process
            return process.returncode is None

        except Exception:
            return False

    async def get_process_status(self, server_id: str) -> Dict[str, Any]:
        """Get detailed process status"""
        try:
            if server_id not in self.processes:
                return {
                    "running": False,
                    "error": "Process not found"
                }

            mcp_process = self.processes[server_id]
            process = mcp_process.process

            running = process.returncode is None
            uptime = (datetime.now() - mcp_process.started_at).total_seconds()

            status = {
                "running": running,
                "process_id": mcp_process.process_id,
                "started_at": mcp_process.started_at.isoformat(),
                "uptime": uptime,
                "command": mcp_process.command,
                "return_code": process.returncode
            }

            # Add system resource info if running
            if running:
                try:
                    proc = psutil.Process(mcp_process.process_id)
                    status.update({
                        "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                        "cpu_percent": proc.cpu_percent(),
                        "num_threads": proc.num_threads()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return status

        except Exception as e:
            return {
                "running": False,
                "error": str(e)
            }

    async def get_process_logs(self, server_id: str, lines: int = 100) -> list:
        """Get recent process logs"""
        if server_id not in self.process_logs:
            return []

        logs = self.process_logs[server_id]
        return logs[-lines:] if lines > 0 else logs

    async def ping_process(self, server_id: str) -> bool:
        """Ping process to check if it's responsive"""
        try:
            if not await self.is_process_running(server_id):
                return False

            # Basic ping - just check if process is alive
            # In future, this could send actual MCP ping message
            return True

        except Exception:
            return False

    async def stop_all_processes(self) -> Dict[str, bool]:
        """Stop all running processes"""
        results = {}

        for server_id in list(self.processes.keys()):
            results[server_id] = await self.stop_subprocess(server_id)

        return results

    async def get_all_process_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all processes"""
        status = {}

        for server_id in self.processes:
            status[server_id] = await self.get_process_status(server_id)

        return status

    async def _monitor_process_logs(self, server_id: str):
        """Monitor process stdout/stderr and store logs"""
        try:
            if server_id not in self.processes:
                return

            mcp_process = self.processes[server_id]

            async def read_stream(stream, stream_name):
                while server_id in self.processes:
                    try:
                        line = await stream.readline()
                        if not line:
                            break

                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "stream": stream_name,
                            "message": line.decode().rstrip()
                        }

                        if server_id in self.process_logs:
                            self.process_logs[server_id].append(log_entry)

                            # Limit log size
                            if len(self.process_logs[server_id]) > self.max_log_lines:
                                self.process_logs[server_id] = self.process_logs[server_id][-self.max_log_lines:]

                    except Exception as e:
                        logger.debug(f"Log monitoring error for {server_id}: {e}")
                        break

            # Monitor both streams concurrently
            if mcp_process.stdout_reader:
                asyncio.create_task(read_stream(mcp_process.stdout_reader, "stdout"))

            if mcp_process.stderr_reader:
                asyncio.create_task(read_stream(mcp_process.stderr_reader, "stderr"))

        except Exception as e:
            logger.error(f"Error monitoring logs for {server_id}: {e}")


# Global instance
mcp_process_manager = MCPProcessManager()