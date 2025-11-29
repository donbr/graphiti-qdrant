#!/usr/bin/env python3
"""
Add qdrant-docs MCP server to a specific project in ~/.claude.json

Usage:
    python scripts/add_qdrant_to_project.py /path/to/project
"""

import json
import os
import sys
from pathlib import Path

def add_qdrant_to_project(project_path: str):
    """Add qdrant-docs MCP server to a project's configuration."""

    # Resolve absolute path
    project_path = str(Path(project_path).resolve())

    # Get environment variables from graphiti-qdrant
    graphiti_path = Path(__file__).parent.parent
    env_path = graphiti_path / ".env"

    if not env_path.exists():
        print(f"❌ Error: .env file not found at {env_path}")
        print("Please create a .env file with QDRANT_API_URL, QDRANT_API_KEY, and OPENAI_API_KEY")
        return 1

    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value

    required_vars = ["QDRANT_API_URL", "QDRANT_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if var not in env_vars]

    if missing_vars:
        print(f"❌ Error: Missing environment variables in .env: {', '.join(missing_vars)}")
        return 1

    # Read ~/.claude.json
    config_path = Path.home() / ".claude.json"

    if not config_path.exists():
        print(f"❌ Error: {config_path} not found")
        return 1

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Ensure project exists in config
    if project_path not in config["projects"]:
        print(f"ℹ️  Project {project_path} not found in config, creating...")
        config["projects"][project_path] = {
            "allowedTools": [],
            "mcpContextUris": [],
            "mcpServers": {},
            "enabledMcpjsonServers": [],
            "disabledMcpjsonServers": [],
            "hasTrustDialogAccepted": False,
            "projectOnboardingSeenCount": 0,
            "hasClaudeMdExternalIncludesApproved": False,
            "hasClaudeMdExternalIncludesWarningShown": False
        }

    # Add qdrant-docs MCP server
    config["projects"][project_path]["mcpServers"]["qdrant-docs"] = {
        "type": "stdio",
        "command": "uv",
        "args": [
            "run",
            "--directory",
            str(graphiti_path),
            "python",
            str(graphiti_path / "mcp_server.py")
        ],
        "env": {
            "QDRANT_API_URL": env_vars["QDRANT_API_URL"],
            "QDRANT_API_KEY": env_vars["QDRANT_API_KEY"],
            "OPENAI_API_KEY": env_vars["OPENAI_API_KEY"]
        }
    }

    # Save config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Added qdrant-docs to {project_path}")
    print(f"\nConfiguration:")
    print(f"  Command: uv run --directory {graphiti_path} python {graphiti_path}/mcp_server.py")
    print(f"  QDRANT_API_URL: {env_vars['QDRANT_API_URL']}")
    print(f"  QDRANT_API_KEY: {'SET' if env_vars['QDRANT_API_KEY'] else 'NOT SET'}")
    print(f"  OPENAI_API_KEY: {'SET' if env_vars['OPENAI_API_KEY'] else 'NOT SET'}")
    print(f"\nTo verify:")
    print(f"  cd {project_path}")
    print(f"  claude mcp list")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/add_qdrant_to_project.py /path/to/project")
        print("\nExample:")
        print("  python scripts/add_qdrant_to_project.py ~/aie7/my-project")
        sys.exit(1)

    sys.exit(add_qdrant_to_project(sys.argv[1]))
