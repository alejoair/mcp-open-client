# MCP Open Client

> A modern, web-based chat application that implements the Model Context Protocol (MCP) for seamless integration between Large Language Models and external tools.

## 🚀 What is MCP Open Client?

**MCP Open Client** is a NiceGUI-based chat application that serves as a bridge between AI models and external tools through the **Model Context Protocol (MCP)**. Think of it as "USB-C for AI" - a universal interface that allows any compatible LLM to securely interact with external data sources, tools, and services.

### Key Features

- 🤖 **Multi-LLM Support**: Compatible with Claude, OpenAI, and other OpenAI-compatible APIs
- 🔧 **MCP Integration**: Connect to MCP servers for enhanced functionality
- 💬 **Modern Chat Interface**: Clean, responsive web UI built with NiceGUI
- 📚 **Conversation Management**: Save, load, and organize your chat history
- ⚙️ **Easy Configuration**: Web-based settings management
- 🌐 **Local & Remote**: Works with local models and cloud APIs
- 🔒 **Secure**: All configurations stored locally

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │◄──►│   MCP Client    │◄──►│  MCP Servers    │
│   (NiceGUI)     │    │  (Protocol)     │    │  (FastMCP)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
    Chat Interface         API Integration         External Tools
    • Conversations        • OpenAI API           • File Systems
    • History             • Claude API            • Databases
    • Settings            • Local Models          • Web Services
```

## 📦 Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install mcp-open-client
mcp-open-client
```

### Option 2: Install from Source
```bash
git clone https://github.com/alejoair/mcp-open-client.git
cd mcp-open-client
pip install -e .
mcp-open-client
```

### Option 3: Development Setup
```bash
git clone https://github.com/alejoair/mcp-open-client.git
cd mcp-open-client
pip install -r requirements.txt
python -m mcp_open_client.main
```

## 🚀 Quick Start

1. **Launch the application**:
   ```bash
   mcp-open-client
   ```

2. **Open your browser** to `http://localhost:8080`

3. **Configure your API settings**:
   - Go to Configuration → API Settings
   - Add your API key and model preferences
   - Choose from OpenAI, Claude, or local models

4. **Set up MCP servers** (optional):
   - Go to Configuration → MCP Servers
   - Add servers for enhanced functionality

5. **Start chatting**!

## ⚙️ Configuration

### API Settings
Configure your preferred AI model in the web interface:

- **API Key**: Your OpenAI/Claude API key
- **Base URL**: API endpoint (supports local models like LM Studio)
- **Model**: Choose your preferred model
- **System Prompt**: Customize the assistant's behavior

### MCP Servers
Connect external tools and services:

```json
{
  "mcpServers": {
    "mcp-requests": {
      "disabled": false,
      "command": "uvx",
      "args": ["mcp-requests"],
      "transport": "stdio"
    },
    "mcp-code-editor": {
      "disabled": false,
      "command": "uvx",
      "args": ["mcp-code-editor"]
    }
  }
}
```

## 🛠️ Supported MCP Servers

The client works with any MCP-compliant server. Popular options include:

- **mcp-requests**: HTTP request capabilities
- **mcp-code-editor**: File system operations
- **mcp-database**: Database connectivity
- **Custom servers**: Build your own with FastMCP

## 🔧 Development

### Project Structure
```
mcp_open_client/
├── main.py                    # Application entry point
├── api_client.py             # LLM API communication
├── mcp_client.py             # MCP protocol handler
├── config_utils.py           # Configuration management
├── settings/                 # Default configurations
│   ├── user-settings.json    # API settings
│   └── mcp-config.json      # MCP server config
└── ui/                      # User interface components
    ├── home.py              # Home page
    ├── chat_interface.py    # Chat UI
    ├── configure.py         # Settings UI
    ├── mcp_servers.py       # MCP management
    └── chat_handlers.py     # Chat logic
```

### Running Tests
```bash
python -m pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🌟 Features in Detail

### Chat Interface
- **Real-time messaging** with streaming responses
- **Conversation history** with search and organization
- **Message formatting** with syntax highlighting
- **Tool integration** via MCP protocol

### Configuration Management
- **Web-based settings** - no need to edit config files
- **Multiple API providers** - OpenAI, Anthropic, local models
- **MCP server management** - enable/disable servers on the fly
- **Theme customization** - dark/light mode support

### MCP Integration
- **Protocol compliance** - works with any MCP server
- **Dynamic server loading** - add servers without restart
- **Tool discovery** - automatic detection of available tools
- **Error handling** - graceful degradation when servers are unavailable

## 📋 Requirements

- Python 3.7+
- Modern web browser
- Internet connection (for cloud APIs) or local model setup

### Dependencies
- `nicegui` - Web UI framework
- `openai` - API client library
- `fastmcp` - MCP protocol implementation
- `websockets` - WebSocket support
- `requests` - HTTP client
- `jsonschema` - Configuration validation

## 🐛 Troubleshooting

### Common Issues

**Connection Problems**:
- Check your API key and base URL
- Verify network connectivity
- Ensure MCP servers are running

**UI Issues**:
- Clear browser cache
- Try a different browser
- Check browser console for errors

**MCP Server Issues**:
- Verify server configuration
- Check server logs
- Test servers independently

### Getting Help

- 📖 Check the [documentation](https://github.com/alejoair/mcp-open-client/wiki)
- 🐛 [Report bugs](https://github.com/alejoair/mcp-open-client/issues)
- 💬 [Ask questions](https://github.com/alejoair/mcp-open-client/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [NiceGUI](https://nicegui.io/) for the web interface
- Uses [FastMCP](https://github.com/jlowin/fastmcp) for MCP protocol implementation
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/) specification

## 🔗 Links

- **Homepage**: [https://github.com/alejoair/mcp-open-client](https://github.com/alejoair/mcp-open-client)
- **Documentation**: [Wiki](https://github.com/alejoair/mcp-open-client/wiki)
- **Bug Tracker**: [Issues](https://github.com/alejoair/mcp-open-client/issues)
- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

---

Made with ❤️ by [alejoair](https://github.com/alejoair)
