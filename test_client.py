import asyncio
import sys
sys.path.append('.')
from mcp_open_client.mcp_client import MCPClientManager

async def test_client():
    print('Testing modified MCP client...', flush=True)
    try:
        client = MCPClientManager()
        # Need to load config first
        import json
        with open('mcp_open_client/settings/mcp-config.json', 'r') as f:
            config = json.load(f)
        await client.initialize(config)
        print(f'Client initialized with {len(client.active_servers)} servers', flush=True)
        
        tools = await client.list_tools()
        print(f'Found {len(tools)} total tools:', flush=True)
        for tool in tools:
            name = tool.get('name', 'unnamed')
            desc = tool.get('description', 'no description')
            print(f'  - {name}: {desc}', flush=True)
        
        return True
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}', flush=True)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_client())
    print(f'Client test result: {result}', flush=True)