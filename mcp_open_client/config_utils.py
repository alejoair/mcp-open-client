import json

def load_initial_config_from_files():
    """Load initial configuration from files into user storage (one-time operation)"""
    configs_loaded = {}
    
    # Load MCP configuration (only MCP servers)
    try:
        with open('mcp_open_client/settings/mcp-config.json', 'r') as f:
            mcp_file_config = json.load(f)
            configs_loaded['mcp-config'] = mcp_file_config
            print("Loaded MCP servers configuration from mcp-config.json")
    except Exception as e:
        print(f"Warning: Could not load MCP config: {str(e)}")
        configs_loaded['mcp-config'] = {"mcpServers": {}}

    # Load user settings (API settings) from user-settings.json
    try:
        with open('mcp_open_client/settings/user-settings.json', 'r') as f:
            user_settings_file = json.load(f)
            configs_loaded['user-settings'] = user_settings_file
            print("Loaded user settings from user-settings.json")
            print(f"Base URL: {user_settings_file.get('base_url', 'Not found')}")
    except Exception as e:
        print(f"Warning: Could not load user settings: {str(e)}")
        # Provide default user settings if file doesn't exist
        configs_loaded['user-settings'] = {
            'api_key': '',
            'base_url': 'http://192.168.58.101:8123',
            'model': 'claude-3-5-sonnet'
        }
        print("Using default user settings")

    # Ensure both configs are always present
    if 'user-settings' not in configs_loaded:
        configs_loaded['user-settings'] = {
            'api_key': '',
            'base_url': 'http://192.168.58.101:8123',
            'model': 'claude-3-5-sonnet'
        }
    
    if 'mcp-config' not in configs_loaded:
        configs_loaded['mcp-config'] = {"mcpServers": {}}
    
    return configs_loaded
