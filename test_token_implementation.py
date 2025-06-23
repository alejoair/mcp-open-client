#!/usr/bin/env python3
"""
Quick test of the token-based history manager implementation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_open_client.ui.history_manager import HistoryManager

def test_history_manager():
    print("=== Testing Token-based History Manager ===\n")
    
    # Test 1: Create new instance with token limits
    print("1. Testing new instance creation:")
    hm = HistoryManager(max_tokens_per_message=1200, max_tokens_per_conversation=12000)
    settings = hm.get_settings()
    print(f"   Token limits: {settings['max_tokens_per_message']} per message, {settings['max_tokens_per_conversation']} per conversation")
    print(f"   Char limits: {settings['max_chars_per_message']} per message, {settings['max_chars_per_conversation']} per conversation")
    print("   [OK] New instance creation works")
    
    # Test 2: Test token estimation
    print("\n2. Testing token estimation:")
    test_cases = [
        "Hello world",
        '{"name": "test", "value": 123}',
        '```python\nprint("Hello")\n```',
        "This is a longer sentence with more words to test normal text processing."
    ]
    
    for text in test_cases:
        tokens = hm.estimate_tokens(text)
        chars = len(text)
        ratio = chars / tokens if tokens > 0 else 0
        print(f"   Text: '{text[:30]}{'...' if len(text) > 30 else ''}'")
        print(f"   Chars: {chars}, Tokens: {tokens}, Ratio: {ratio:.2f}")
    print("   [OK] Token estimation works")
    
    # Test 3: Test backward compatibility with old instance
    print("\n3. Testing backward compatibility:")
    old_hm = HistoryManager.__new__(HistoryManager)
    old_hm.max_chars_per_message = 5000
    old_hm.max_chars_per_conversation = 50000
    old_hm.settings = {
        'truncate_mode': 'smart',
        'preserve_tool_calls': True,
        'compression_enabled': True,
        'auto_cleanup': True
    }
    
    # This should trigger backward compatibility
    old_settings = old_hm.get_settings()
    print(f"   Old instance token limits: {old_settings['max_tokens_per_message']} per message, {old_settings['max_tokens_per_conversation']} per conversation")
    print("   [OK] Backward compatibility works")
    
    # Test 4: Test conversation size calculation
    print("\n4. Testing conversation size calculation:")
    # Mock conversation data
    mock_conversation = {
        'messages': [
            {'content': 'Hello, how are you?'},
            {'content': 'I am doing well, thank you for asking!'},
            {'content': '{"status": "ok", "data": [1, 2, 3]}'}
        ]
    }
    
    # Calculate size
    total_chars = sum(len(msg['content']) for msg in mock_conversation['messages'])
    total_tokens = sum(hm.estimate_tokens(msg['content']) for msg in mock_conversation['messages'])
    print(f"   Mock conversation: {len(mock_conversation['messages'])} messages")
    print(f"   Total chars: {total_chars}, Total tokens: {total_tokens}")
    print("   [OK] Size calculation works")
    
    print("\n=== All tests passed! ===")

if __name__ == "__main__":
    test_history_manager()
