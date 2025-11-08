#!/usr/bin/env python3
"""
Test script to verify meta tools registration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing meta tools registry...")

try:
    # Import meta tools system
    from mcp_open_client.meta_tools import meta_tool_registry
    print("SUCCESS: meta_tool_registry imported successfully")

    # Check registered tools
    tools = meta_tool_registry.tools
    print(f"SUCCESS: Registered tools: {list(tools.keys())}")

    # Check schemas
    schemas = meta_tool_registry.get_tools_schema()
    print(f"SUCCESS: Tool schemas count: {len(schemas) if schemas else 0}")

    if schemas:
        for schema in schemas:
            print(f"  - {schema['function']['name']}")
    else:
        print("ERROR: No schemas found!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()