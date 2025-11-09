# MCP Open Client

A modern, web-based MCP (Model Context Protocol) client with FastAPI backend and React frontend.

## Features

- 🌐 Web-based interface built with React and CDN libraries (zero build process)
- 🚀 FastAPI backend for high performance
- 🔧 Easy configuration and setup
- 📡 WebSocket support for real-time communication
- 🎨 Modern UI with Ant Design components
- 🔒 Secure MCP server connections

## Quick Start

### Installation

```bash
pip install mcp-open-client
```

### Basic Usage

```bash
# Start the MCP client server
mcp-open-client

# Or with custom configuration
mcp-open-client --host 0.0.0.0 --port 8080
```

Then open your browser to `http://localhost:8080` to access the web interface.

## Architecture

### Frontend
- **React 18** - Core UI framework
- **Ant Design** - Professional UI components
- **Tailwind CSS** - Utility-first styling
- **CDN-based** - No build process required

### Backend
- **FastAPI** - High-performance Python web framework
- **WebSockets** - Real-time MCP communication
- **Static file serving** - Integrated web server
- **MCP Protocol** - Native Model Context Protocol support

## Development

### Project Structure

```
mcp-open-client/
├── mcp_open_client/          # Python package
│   ├── server/               # FastAPI server code
│   ├── ui/                   # User interface components
│   └── cli.py               # Command line interface
├── tests/                   # Test suite
└── pyproject.toml          # Project configuration
```

### Development Installation

```bash
git clone https://github.com/your-org/mcp-open-client
cd mcp-open-client
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

## Configuration

The MCP Open Client can be configured through:

1. **Command line arguments**
2. **Environment variables**
3. **Configuration files**

See the [Configuration Guide](docs/configuration.md) for details.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Model Context Protocol](https://github.com/anthropics/mcp) - Official MCP specification
- [Rayflow](https://github.com/your-org/rayflow) - Visual workflow editor that inspired this architecture