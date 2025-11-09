"""Command line interface for MCP Open Client."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn
from mcp_open_client.__about__ import __version__

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to.",
    show_default=True,
)
@click.option(
    "--port",
    default=8080,
    type=int,
    help="Port to bind the server to.",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload for development.",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error"]),
    help="Set the logging level.",
    show_default=True,
)
@click.option(
    "--web-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing web frontend files. If not provided, uses bundled files.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to configuration file.",
)
@click.version_option(version=__version__, prog_name="mcp-open-client")
def main(
    host: str,
    port: int,
    reload: bool,
    log_level: str,
    web_dir: Optional[str],
    config: Optional[str],
) -> None:
    """
    MCP Open Client - A modern, web-based MCP (Model Context Protocol) client.

    This command starts the MCP Open Client web server, providing a browser-based
    interface for connecting to and interacting with MCP servers.

    Examples:

        # Start with default settings
        mcp-open-client

        # Start on a different port
        mcp-open-client --port 8080

        # Enable development mode with auto-reload
        mcp-open-client --reload --log-level debug

        # Use custom web directory
        mcp-open-client --web-dir ./my-custom-frontend
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Log startup information
    logger.info(f"Starting MCP Open Client v{__version__}")
    logger.info(f"Server will be available at: http://{host}:{port}")

    if web_dir:
        logger.info(f"Using custom web directory: {web_dir}")

    if config:
        logger.info(f"Using configuration file: {config}")

    try:
        # Configure uvicorn
        uvicorn_config = {
            "host": host,
            "port": port,
            "log_level": log_level,
        }

        if reload:
            # For development, use module import string for hot reload
            # Set environment variables for app configuration
            import os
            if web_dir:
                os.environ["MCP_WEB_DIR"] = str(Path(web_dir))
            if config:
                os.environ["MCP_CONFIG_FILE"] = str(Path(config))

            uvicorn_config.update({
                "reload": True,
                "reload_dirs": [str(Path(__file__).parent)],
            })
            logger.info("Development mode: auto-reload enabled")

            # Use import string for reload
            uvicorn.run("mcp_open_client.server.app:app", **uvicorn_config)
        else:
            # For production, create app directly
            from mcp_open_client.server.app import create_app

            app_config = {
                "web_dir": Path(web_dir) if web_dir else None,
                "config_file": Path(config) if config else None,
            }

            app = create_app(**app_config)
            uvicorn.run(app, **uvicorn_config)

    except KeyboardInterrupt:
        logger.info("Shutting down MCP Open Client...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """MCP Open Client command line tools."""
    pass


@cli.command()
@click.option(
    "--output",
    "-o",
    default="mcp-config.json",
    help="Output configuration file path.",
    show_default=True,
)
def init_config(output: str) -> None:
    """Generate a default configuration file."""
    import json

    default_config = {
        "servers": [],
        "ui": {
            "theme": "light",
            "autoConnect": False
        },
        "logging": {
            "level": "info",
            "file": None
        }
    }

    output_path = Path(output)

    if output_path.exists():
        if not click.confirm(f"Configuration file {output} already exists. Overwrite?"):
            click.echo("Cancelled.")
            return

    try:
        with open(output_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        click.echo(f"✓ Configuration file created: {output}")
        click.echo("\nEdit this file to configure your MCP servers and preferences.")

    except Exception as e:
        click.echo(f"✗ Error creating configuration file: {e}")
        sys.exit(1)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"MCP Open Client v{__version__}")


if __name__ == "__main__":
    main()