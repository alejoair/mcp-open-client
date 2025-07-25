# Client Overview

> Learn how to use the FastMCP Client to interact with MCP servers.

export const VersionBadge = ({version}) => {
  return <code className="version-badge-container">
            <p className="version-badge">
                <span className="version-badge-label">New in version:</span> 
                <code className="version-badge-version">{version}</code>
            </p>
        </code>;
};

<VersionBadge version="2.0.0" />

The `fastmcp.Client` provides a high-level, asynchronous interface for interacting with any Model Context Protocol (MCP) server, whether it's built with FastMCP or another implementation. It simplifies communication by handling protocol details and connection management.

## FastMCP Client

The FastMCP Client architecture separates the protocol logic (`Client`) from the connection mechanism (`Transport`).

* **`Client`**: Handles sending MCP requests (like `tools/call`, `resources/read`), receiving responses, and managing callbacks.
* **`Transport`**: Responsible for establishing and maintaining the connection to the server (e.g., via WebSockets, SSE, Stdio, or in-memory).

### Transports

Clients must be initialized with a `transport`. You can either provide an already instantiated transport object, or provide a transport source and let FastMCP attempt to infer the correct transport to use.

The following inference rules are used to determine the appropriate `ClientTransport` based on the input type:

1. **`ClientTransport` Instance**: If you provide an already instantiated transport object, it's used directly.
2. **`FastMCP` Instance**: Creates a `FastMCPTransport` for efficient in-memory communication (ideal for testing). This also works with a **FastMCP 1.0 server** created via `mcp.server.fastmcp.FastMCP`.
3. **`Path` or `str` pointing to an existing file**:
   * If it ends with `.py`: Creates a `PythonStdioTransport` to run the script using `python`.
   * If it ends with `.js`: Creates a `NodeStdioTransport` to run the script using `node`.
4. **`AnyUrl` or `str` pointing to a URL that begins with `http://` or `https://`**:
   * Creates a `StreamableHttpTransport`
5. **`MCPConfig` or dictionary matching MCPConfig schema**: Creates a client that connects to one or more MCP servers specified in the config.
6. **Other**: Raises a `ValueError` if the type cannot be inferred.

```python
import asyncio
from fastmcp import Client, FastMCP

# Example transports (more details in Transports page)
server_instance = FastMCP(name="TestServer") # In-memory server
http_url = "https://example.com/mcp"        # HTTP server URL
server_script = "my_mcp_server.py"         # Path to a Python server file

# Client automatically infers the transport type
client_in_memory = Client(server_instance)
client_http = Client(http_url)

client_stdio = Client(server_script)

print(client_in_memory.transport)
print(client_http.transport)
print(client_stdio.transport)

# Expected Output (types may vary slightly based on environment):
# <FastMCP(server='TestServer')>
# <StreamableHttp(url='https://example.com/mcp')>
# <PythonStdioTransport(command='python', args=['/path/to/your/my_mcp_server.py'])>
```

You can also initialize a client from an MCP configuration dictionary or `MCPConfig` file:

```python
from fastmcp import Client

config = {
    "mcpServers": {
        "local": {"command": "python", "args": ["local_server.py"]},
        "remote": {"url": "https://example.com/mcp"},
    }
}

client_config = Client(config)
```

<Tip>
  For more control over connection details (like headers for SSE, environment variables for Stdio), you can instantiate the specific `ClientTransport` class yourself and pass it to the `Client`. See the [Transports](/clients/transports) page for details.
</Tip>

### Multi-Server Clients

<VersionBadge version="2.4.0" />

FastMCP supports creating clients that connect to multiple MCP servers through a single client interface using a standard MCP configuration format (`MCPConfig`). This configuration approach makes it easy to connect to multiple specialized servers or create composable systems with a simple, declarative syntax.

<Note>
  The MCP configuration format follows an emerging standard and may evolve as the specification matures. FastMCP will strive to maintain compatibility with future versions, but be aware that field names or structure might change.
</Note>

When you create a client with an `MCPConfig` containing multiple servers:

1. FastMCP creates a composite client that internally mounts all servers using their config names as prefixes
2. Tools and resources from each server are accessible with appropriate prefixes in the format `servername_toolname` and `protocol://servername/resource/path`
3. You interact with this as a single unified client, with requests automatically routed to the appropriate server

```python
from fastmcp import Client

# Create a standard MCP configuration with multiple servers
config = {
    "mcpServers": {
        # A remote HTTP server
        "weather": {
            "url": "https://weather-api.example.com/mcp",
            "transport": "streamable-http"
        },
        # A local server running via stdio
        "assistant": {
            "command": "python",
            "args": ["./my_assistant_server.py"],
            "env": {"DEBUG": "true"}
        }
    }
}

# Create a client that connects to both servers
client = Client(config)

async def main():
    async with client:
        # Access tools from different servers with prefixes
        weather_data = await client.call_tool("weather_get_forecast", {"city": "London"})
        response = await client.call_tool("assistant_answer_question", {"question": "What's the capital of France?"})
        
        # Access resources with prefixed URIs
        weather_icons = await client.read_resource("weather://weather/icons/sunny")
        templates = await client.read_resource("resource://assistant/templates/list")
        
        print(f"Weather: {weather_data}")
        print(f"Assistant: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

If your configuration has only a single server, FastMCP will create a direct client to that server without any prefixing.

## Client Usage

### Connection Lifecycle

The client operates asynchronously and must be used within an `async with` block. This context manager handles establishing the connection, initializing the MCP session, and cleaning up resources upon exit.

```python
import asyncio
from fastmcp import Client

client = Client("my_mcp_server.py") # Assumes my_mcp_server.py exists

async def main():
    # Connection is established here
    async with client:
        print(f"Client connected: {client.is_connected()}")

        # Make MCP calls within the context
        tools = await client.list_tools()
        print(f"Available tools: {tools}")

        if any(tool.name == "greet" for tool in tools):
            result = await client.call_tool("greet", {"name": "World"})
            print(f"Greet result: {result}")

    # Connection is closed automatically here
    print(f"Client connected: {client.is_connected()}")

if __name__ == "__main__":
    asyncio.run(main())
```

You can make multiple calls to the server within the same `async with` block using the established session.

### Client Methods

The `Client` provides methods corresponding to standard MCP requests:

<Warning>
  The standard client methods return user-friendly representations that may change as the protocol evolves. For consistent access to the complete data structure, use the `*_mcp` methods described later.
</Warning>

#### Tool Operations

* **`list_tools()`**: Retrieves a list of tools available on the server.
  ```python
  tools = await client.list_tools()
  # tools -> list[mcp.types.Tool]
  ```
* **`call_tool(name: str, arguments: dict[str, Any] | None = None, timeout: float | None = None, progress_handler: ProgressHandler | None = None)`**: Executes a tool on the server.
  ```python
  result = await client.call_tool("add", {"a": 5, "b": 3})
  # result -> list[mcp.types.TextContent | mcp.types.ImageContent | ...]
  print(result[0].text) # Assuming TextContent, e.g., '8'

  # With timeout (aborts if execution takes longer than 2 seconds)
  result = await client.call_tool("long_running_task", {"param": "value"}, timeout=2.0)

  # With progress handler (to track execution progress)
  result = await client.call_tool(
      "long_running_task",
      {"param": "value"},
      progress_handler=my_progress_handler
  )
  ```
  * Arguments are passed as a dictionary. FastMCP servers automatically handle JSON string parsing for complex types if needed.
  * Returns a list of content objects (usually `TextContent` or `ImageContent`).
  * The optional `timeout` parameter limits the maximum execution time (in seconds) for this specific call, overriding any client-level timeout.
  * The optional `progress_handler` parameter receives progress updates during execution, overriding any client-level progress handler.

#### Resource Operations

* **`list_resources()`**: Retrieves a list of static resources.
  ```python
  resources = await client.list_resources()
  # resources -> list[mcp.types.Resource]
  ```
* **`list_resource_templates()`**: Retrieves a list of resource templates.
  ```python
  templates = await client.list_resource_templates()
  # templates -> list[mcp.types.ResourceTemplate]
  ```
* **`read_resource(uri: str | AnyUrl)`**: Reads the content of a resource or a resolved template.
  ```python
  # Read a static resource
  readme_content = await client.read_resource("file:///path/to/README.md")
  # readme_content -> list[mcp.types.TextResourceContents | mcp.types.BlobResourceContents]
  print(readme_content[0].text) # Assuming text

  # Read a resource generated from a template
  weather_content = await client.read_resource("data://weather/london")
  print(weather_content[0].text) # Assuming text JSON
  ```

#### Prompt Operations

* **`list_prompts()`**: Retrieves available prompt templates.
* **`get_prompt(name: str, arguments: dict[str, Any] | None = None)`**: Retrieves a rendered prompt message list.

### Raw MCP Protocol Objects

<VersionBadge version="2.2.7" />

The FastMCP client attempts to provide a "friendly" interface to the MCP protocol, but sometimes you may need access to the raw MCP protocol objects. Each of the main client methods that returns data has a corresponding `*_mcp` method that returns the raw MCP protocol objects directly.

<Warning>
  The standard client methods (without `_mcp`) return user-friendly representations of MCP data, while `*_mcp` methods will always return the complete MCP protocol objects. As the protocol evolves, changes to these user-friendly representations may occur and could potentially be breaking. If you need consistent, stable access to the full data structure, prefer using the `*_mcp` methods.
</Warning>

```python
# Standard method - returns just the list of tools
tools = await client.list_tools()
# tools -> list[mcp.types.Tool]

# Raw MCP method - returns the full protocol object
result = await client.list_tools_mcp()
# result -> mcp.types.ListToolsResult
tools = result.tools
```

Available raw MCP methods:

* **`list_tools_mcp()`**: Returns `mcp.types.ListToolsResult`
* **`call_tool_mcp(name, arguments)`**: Returns `mcp.types.CallToolResult`
* **`list_resources_mcp()`**: Returns `mcp.types.ListResourcesResult`
* **`list_resource_templates_mcp()`**: Returns `mcp.types.ListResourceTemplatesResult`
* **`read_resource_mcp(uri)`**: Returns `mcp.types.ReadResourceResult`
* **`list_prompts_mcp()`**: Returns `mcp.types.ListPromptsResult`
* **`get_prompt_mcp(name, arguments)`**: Returns `mcp.types.GetPromptResult`
* **`complete_mcp(ref, argument)`**: Returns `mcp.types.CompleteResult`

These methods are especially useful for debugging or when you need to access metadata or fields that aren't exposed by the simplified methods.

### Additional Features

#### Pinging the Server

The client can be used to ping the server to verify connectivity.

```python
async with client:
    await client.ping()
    print("Server is reachable")
```

#### Session Management

When using stdio transports, clients support a `keep_alive` feature (enabled by default) that maintains subprocess sessions between connection contexts. You can manually control this behavior using the client's `close()` method.

When `keep_alive=False`, the client will automatically close the session when the context manager exits.

```python
from fastmcp import Client

client = Client("my_mcp_server.py")  # keep_alive=True by default

async def example():
    async with client:
        await client.ping()
    
    async with client:
        await client.ping()  # Same subprocess as above
```

<Note>
  For detailed examples and configuration options, see [Session Management in Transports](/clients/transports#session-management).
</Note>

#### Timeouts

<VersionBadge version="2.3.4" />

You can control request timeouts at both the client level and individual request level:

```python
from fastmcp import Client
from fastmcp.exceptions import McpError

# Client with a global 5-second timeout for all requests
client = Client(
    my_mcp_server,
    timeout=5.0  # Default timeout in seconds
)

async with client:
    # This uses the global 5-second timeout
    result1 = await client.call_tool("quick_task", {"param": "value"})
    
    # This specifies a 10-second timeout for this specific call
    result2 = await client.call_tool("slow_task", {"param": "value"}, timeout=10.0)
    
    try:
        # This will likely timeout
        result3 = await client.call_tool("medium_task", {"param": "value"}, timeout=0.01)
    except McpError as e:
        # Handle timeout error
        print(f"The task timed out: {e}")
```

<Warning>
  Timeout behavior varies between transport types:

  * With **SSE** transport, the per-request (tool call) timeout **always** takes precedence, regardless of which is lower.
  * With **HTTP** transport, the **lower** of the two timeouts (client or tool call) takes precedence.

  For consistent behavior across all transports, we recommend explicitly setting timeouts at the individual tool call level when needed, rather than relying on client-level timeouts.
</Warning>

#### Error Handling

When a `call_tool` request results in an error on the server (e.g., the tool function raised an exception), the `client.call_tool()` method will raise a `fastmcp.exceptions.ClientError`.

```python
async def safe_call_tool():
    async with client:
        try:
            # Assume 'divide' tool exists and might raise ZeroDivisionError
            result = await client.call_tool("divide", {"a": 10, "b": 0})
            print(f"Result: {result}")
        except ClientError as e:
            print(f"Tool call failed: {e}")
        except ConnectionError as e:
            print(f"Connection failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Example Output if division by zero occurs:
# Tool call failed: Division by zero is not allowed.
```

Other errors, like connection failures, will raise standard Python exceptions (e.g., `ConnectionError`, `TimeoutError`).

<Tip>
  The client transport often has its own error-handling mechanisms, so you can not always trap errors like those raised by `call_tool` outside of the `async with` block. Instead, you can use `call_tool_mcp()` to get the raw `mcp.types.CallToolResult` object and handle errors yourself by checking its `isError` attribute.
</Tip>
