#!/usr/bin/env python3
"""
Script to remove/replace emoji characters from Python files to fix Windows console encoding issues.
"""
import os
import re

# Emoji mappings - replace with text equivalents
EMOJI_REPLACEMENTS = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]',
    '💡': '[TIP]',
    '🔄': 'Refresh',
    '📊': '[STATUS]',
    '🔔': '[UPDATE]',
    '🐛': '[DEBUG]',
    '⚙️': '[WORKING]',
    '📢': '[NOTIFICATION]',
    '🔄': '[CONTINUE]',
    '📝': '[NOTES]',
    '✨': '[ADVANTAGE]',
    '🚀': '[START]',
    '📋': '[PARAMS]',
    '🔵': '[INFO]',
    '✓': '[SELECTED]',
    '🔴': '[ERROR]',
    '🔚': '[TERMINAL]',
    '🚫': '[FORBIDDEN]',
    '🎉': '[SUCCESS]',
    '❓': '[QUESTION]',
    '🔊': '[SOUND]',
}

def clean_emoji_from_file(filepath):
    """Clean emojis from a single file."""
    print(f"Processing: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = False

        # Replace known emojis
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                changes_made = True
                print(f"  Replaced '{emoji}' with '{replacement}'")

        # Remove any remaining emojis using regex
        emoji_pattern = re.compile(
            r'[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F'
            r'\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF'
            r'\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F'
            r'\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
        )

        remaining_emojis = emoji_pattern.findall(content)
        if remaining_emojis:
            for emoji in remaining_emojis:
                print(f"  Removing remaining emoji: {repr(emoji)}")
            content = emoji_pattern.sub('[EMOJI]', content)
            changes_made = True

        if changes_made:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [OK] File updated")
            return True
        else:
            print(f"  - No changes needed")
            return False

    except Exception as e:
        print(f"  ERROR processing {filepath}: {e}")
        return False

def main():
    """Main function to clean emojis from Python files."""
    project_root = r'C:\Users\Usuario\Desktop\proyecto-mcp\mcp-open-client\mcp_open_client'

    files_to_process = [
        'main.py',
        'meta_tools/notify_user.py',
        'meta_tools/respond_to_user.py',
        'ui/chat_handlers.py',
        'ui/configure.py',
        'ui/handle_tool_call.py',
        'ui/history_settings.py',
        'ui/message_parser.py'
    ]

    files_changed = 0

    print("Cleaning emoji characters from Python files...")
    print("=" * 50)

    for file_rel in files_to_process:
        filepath = os.path.join(project_root, file_rel)
        if os.path.exists(filepath):
            if clean_emoji_from_file(filepath):
                files_changed += 1
        else:
            print(f"WARNING: File not found: {filepath}")

    print("=" * 50)
    print(f"[OK] Cleanup complete! {files_changed} files were modified.")

    # Also clean the settings file if it has emojis
    settings_file = os.path.join(project_root, 'settings', 'user-settings.json')
    if os.path.exists(settings_file):
        print(f"Processing JSON settings file: {settings_file}")
        clean_emoji_from_file(settings_file)

if __name__ == '__main__':
    main()