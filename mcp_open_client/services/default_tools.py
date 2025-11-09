"""
Default Tools Configuration - Defines built-in tools available to the model
"""

def get_default_tools():
    """
    Returns the default set of tools available to all chat completions.
    These tools are always included unless explicitly overridden.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "respond_to_user",
                "description": "Respond directly to the user with text. Use this for general conversation, questions about yourself, capabilities, or any response that doesn't require specific tools.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "The response text to send to the user"
                        }
                    },
                    "required": ["response"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to calculate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get current time and date information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (default: UTC)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information (simulated)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information (simulated)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location to get weather for"
                        },
                        "units": {
                            "type": "string",
                            "description": "Temperature units (celsius/fahrenheit, default: celsius)"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]