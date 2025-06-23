#!/usr/bin/env python3
"""
Script para incrementar automáticamente la versión en pyproject.toml
Uso: python bump_version.py [major|minor|patch]
"""
import re
import sys
import argparse
from pathlib import Path

def get_current_version():
    """Lee la versión actual del pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text(encoding='utf-8')
    version_match = re.search(r'version = "([^"]+)"', content)
    
    if not version_match:
        raise ValueError("Version not found in pyproject.toml")
    
    return version_match.group(1)

def bump_version(current_version, bump_type):
    """Incrementa la versión según el tipo especificado"""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError("bump_type must be 'major', 'minor', or 'patch'")
    
    return f"{major}.{minor}.{patch}"

def update_version_in_file(new_version):
    """Actualiza la versión en pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding='utf-8')
    
    # Reemplazar la versión
    new_content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    
    pyproject_path.write_text(new_content, encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='Bump version in pyproject.toml')
    parser.add_argument(
        'bump_type',
        choices=['major', 'minor', 'patch'],
        help='Type of version bump'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    try:
        current_version = get_current_version()
        new_version = bump_version(current_version, args.bump_type)
        
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")
        
        if args.dry_run:
            print("Dry run - no changes made")
        else:
            update_version_in_file(new_version)
            print(f"Version updated to {new_version}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
