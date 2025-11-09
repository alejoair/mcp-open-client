"""FastAPI application for MCP Open Client."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Import configuration manager
from mcp_open_client.config import config_manager

# Import routers
from mcp_open_client.server.routes import config_router
from mcp_open_client.server.routes import chat_router


def create_app(web_dir: Optional[Path] = None, config_file: Optional[Path] = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="MCP Open Client",
        description="A modern, web-based MCP (Model Context Protocol) client",
        version="0.1.0"
    )

    # Default UI directory (bundled with package)
    if web_dir is None:
        web_dir = Path(__file__).parent.parent / "ui"

    # Mount static files if UI directory exists
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    # Include API routers
    app.include_router(config_router)
    app.include_router(chat_router)

    @app.get("/")
    async def root():
        """Serve the main HTML page or index.html from UI directory."""
        # Try to serve index.html from UI directory first
        if web_dir and web_dir.exists():
            index_path = web_dir / "index.html"
            if index_path.exists():
                from fastapi.responses import FileResponse
                return FileResponse(path=str(index_path), media_type='text/html')

        # Fallback to default HTML page
        return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Open Client</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 60px 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
        }
        .logo {
            font-size: 48px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 16px;
            font-size: 32px;
            font-weight: 600;
        }
        .subtitle {
            color: #666;
            margin-bottom: 40px;
            font-size: 18px;
            line-height: 1.6;
        }
        .status {
            display: inline-flex;
            align-items: center;
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 12px 20px;
            color: #0369a1;
            font-weight: 500;
            margin-bottom: 30px;
        }
        .status::before {
            content: "✓";
            margin-right: 8px;
            color: #059669;
            font-weight: bold;
        }
        .features {
            text-align: left;
            margin-top: 30px;
        }
        .feature {
            margin: 12px 0;
            padding: 8px 0;
            color: #555;
        }
        .feature::before {
            content: "→";
            margin-right: 12px;
            color: #667eea;
            font-weight: bold;
        }
        .footer {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀</div>
        <h1>MCP Open Client</h1>
        <p class="subtitle">
            A modern, web-based MCP (Model Context Protocol) client with FastAPI backend and React frontend.
        </p>

        <div class="status">
            Server is running successfully!
        </div>

        <div class="features">
            <div class="feature">Zero-config setup with CDN-based frontend</div>
            <div class="feature">FastAPI backend for high performance</div>
            <div class="feature">WebSocket support for real-time communication</div>
            <div class="feature">Modern UI with professional components</div>
        </div>

        <div class="footer">
            <p><strong>Next steps:</strong></p>
            <p>The web interface is ready for development. Add your static files (HTML, JS, CSS) to the <code>/ui</code> directory to get started.</p>
            <p>• Place your <code>index.html</code> in the UI directory to replace this page</p>
            <p>• Add JavaScript, CSS, and other assets to the UI directory</p>
            <p>• Visit <code>/docs</code> to explore the API documentation</p>
            <p>• Static files are served directly from <code>/ui</code> directory</p>
        </div>
    </div>
</body>
</html>
        """)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "mcp-open-client"}

    # Serve static files (this should be last to act as catch-all)
    if web_dir and web_dir.exists():
        @app.get("/{filename:path}")
        async def serve_static_files(filename: str):
            """Serve static files from UI directory."""
            from fastapi import HTTPException
            from fastapi.responses import FileResponse

            # Security: prevent directory traversal
            if ".." in filename or filename.startswith("/"):
                raise HTTPException(status_code=404, detail="File not found")

            file_path = web_dir / filename

            # Check if file exists and is actually a file
            if file_path.exists() and file_path.is_file():
                # Determine content type based on file extension
                content_type_map = {
                    '.html': 'text/html',
                    '.js': 'application/javascript',
                    '.css': 'text/css',
                    '.json': 'application/json',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.svg': 'image/svg+xml',
                    '.ico': 'image/x-icon'
                }

                file_ext = file_path.suffix.lower()
                media_type = content_type_map.get(file_ext, 'application/octet-stream')

                return FileResponse(
                    path=str(file_path),
                    media_type=media_type,
                    filename=file_path.name
                )

            # If file doesn't exist, fall through to 404
            raise HTTPException(status_code=404, detail="File not found")

    return app


# Create app instance for uvicorn hot reload mode
app = None

def get_app() -> FastAPI:
    """Get or create app instance for hot reload mode."""
    global app
    if app is None:
        # Get configuration from environment variables set by CLI
        web_dir_str = os.getenv("MCP_WEB_DIR")
        config_file_str = os.getenv("MCP_CONFIG_FILE")

        web_dir = Path(web_dir_str) if web_dir_str else None
        config_file = Path(config_file_str) if config_file_str else None

        app = create_app(web_dir=web_dir, config_file=config_file)

    return app

# For uvicorn import - debug reload
app = get_app()