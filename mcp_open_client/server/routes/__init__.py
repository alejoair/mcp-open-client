"""
API routes for MCP Open Client
"""

from .config import router as config_router
from .chat import router as chat_router

__all__ = ['config_router', 'chat_router']