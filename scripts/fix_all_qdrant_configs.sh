#!/bin/bash
# Fix all qdrant-docs MCP configurations to use absolute paths
#
# This script finds all projects with broken qdrant-docs configs
# (using relative paths) and fixes them to use absolute paths.

set -e

cd "$(dirname "$0")/.."

echo "Finding and fixing broken qdrant-docs configurations..."
echo ""

python3 << 'EOF'
import json
from pathlib import Path

config_path = Path.home() / ".claude.json"

with open(config_path, 'r') as f:
    config = json.load(f)

# Get environment variables from graphiti-qdrant
graphiti_path = Path(__file__).parent.parent.resolve() if '__file__' in dir() else Path.cwd()
env_path = graphiti_path / ".env"

env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value

# Find and fix projects with broken qdrant-docs configs
fixed_count = 0

for project_path, project_config in config.get("projects", {}).items():
    mcp_servers = project_config.get("mcpServers", {})
    if "qdrant-docs" in mcp_servers:
        server_config = mcp_servers["qdrant-docs"]
        args = server_config.get("args", [])

        # Check if it's using relative path or missing --directory
        needs_fix = (
            "mcp_server.py" in args and
            "/home/donbr/graphiti-qdrant" not in str(args)
        )

        if needs_fix:
            print(f"🔧 Fixing: {project_path}")

            # Update to use absolute paths
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
                    "QDRANT_API_URL": env_vars.get("QDRANT_API_URL", ""),
                    "QDRANT_API_KEY": env_vars.get("QDRANT_API_KEY", ""),
                    "OPENAI_API_KEY": env_vars.get("OPENAI_API_KEY", "")
                }
            }
            fixed_count += 1

if fixed_count > 0:
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Fixed {fixed_count} configuration(s)")
    print(f"\nUpdated: {config_path}")
else:
    print("✅ All configurations are already correct!")

EOF

echo ""
echo "Done! Run 'claude mcp list' to verify."
