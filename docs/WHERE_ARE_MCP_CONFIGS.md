# Where Are MCP Server Configurations?

## TL;DR

All MCP server configurations are stored in **`~/.claude.json`** under `projects["/path/to/directory"]`.

**There is no global MCP config** - each directory gets its own configuration.

## Your Current Setup

You have `qdrant-docs` configured in **3 places**:

### 1. Home Directory (`/home/donbr`)

```json
{
  "projects": {
    "/home/donbr": {
      "mcpServers": {
        "qdrant-docs": {
          "command": "uv",
          "args": ["run", "--directory", "/home/donbr/graphiti-qdrant", "python", "/home/donbr/graphiti-qdrant/mcp_server.py"],
          "env": { ... }
        }
      }
    }
  }
}
```

**When it's used:** When you run `claude` from `/home/donbr` or any subdirectory that **doesn't have its own MCP config**.

### 2. This Project (`/home/donbr/graphiti-qdrant`)

```json
{
  "projects": {
    "/home/donbr/graphiti-qdrant": {
      "mcpServers": {
        "qdrant-docs": {
          "command": "uv",
          "args": ["run", "python", "mcp_server.py"],
          "env": { ... }
        }
      }
    }
  }
}
```

**When it's used:** Only when you run `claude` from `/home/donbr/graphiti-qdrant`.

### 3. /tmp (Can be removed)

```json
{
  "projects": {
    "/tmp": {
      "mcpServers": {
        "qdrant-docs": { ... }
      }
    }
  }
}
```

**When it's used:** Only when you run `claude` from `/tmp` (probably don't need this).

## Why Other Projects Don't See `qdrant-docs`

When you run `claude mcp list` from a project directory, Claude Code:

1. Looks up that **exact path** in `~/.claude.json`
2. If the project has **its own** `mcpServers`, uses **only those**
3. Otherwise, falls back to parent directory configs

### Example: Your AIE7 Project

```json
{
  "projects": {
    "/home/donbr/aie7stg/AIE7-Staging": {
      "mcpServers": {
        "context7": { ... },
        "brave-search": { ... },
        "sequential-thinking": { ... }
        // qdrant-docs is NOT here
      }
    }
  }
}
```

When you `cd /home/donbr/aie7stg/AIE7-Staging` and run `claude mcp list`, you see:
- ✅ context7
- ✅ brave-search
- ✅ sequential-thinking
- ❌ qdrant-docs (not in this project's config)

Even though `/home/donbr` has `qdrant-docs`, it's **not inherited** because this project has its own `mcpServers` defined.

## How to Add `qdrant-docs` to Another Project

### Option 1: Use the Helper Script (Easiest)

```bash
cd /home/donbr/graphiti-qdrant
python scripts/add_qdrant_to_project.py /home/donbr/aie7/my-project
```

This automatically:
- Reads environment variables from this project's `.env`
- Adds `qdrant-docs` to that project's config in `~/.claude.json`
- Uses absolute paths so it works from anywhere

### Option 2: Use `claude mcp add` from the Project

```bash
cd /home/donbr/aie7/my-project
claude mcp add qdrant-docs \
  -e QDRANT_API_URL="$(grep QDRANT_API_URL /home/donbr/graphiti-qdrant/.env | cut -d= -f2)" \
  -e QDRANT_API_KEY="$(grep QDRANT_API_KEY /home/donbr/graphiti-qdrant/.env | cut -d= -f2)" \
  -e OPENAI_API_KEY="$(grep OPENAI_API_KEY /home/donbr/graphiti-qdrant/.env | cut -d= -f2)" \
  -- uv run --directory /home/donbr/graphiti-qdrant python /home/donbr/graphiti-qdrant/mcp_server.py
```

### Option 3: Manually Edit `~/.claude.json`

1. Open `~/.claude.json`
2. Find the project path under `projects`
3. Add `qdrant-docs` to its `mcpServers` object
4. Save and restart Claude Code

## Where to Check Configs

```bash
# View all MCP configs
cat ~/.claude.json | jq '.projects | to_entries[] | select(.value.mcpServers | length > 0) | {path: .key, servers: .value.mcpServers | keys}'

# View config for a specific project
cat ~/.claude.json | jq '.projects["/home/donbr/graphiti-qdrant"].mcpServers'

# Check which projects have qdrant-docs
cat ~/.claude.json | jq '.projects | to_entries[] | select(.value.mcpServers["qdrant-docs"]) | .key'
```

## Architecture Diagram

```
~/.claude.json
│
├── projects
│   │
│   ├── "/home/donbr"
│   │   └── mcpServers
│   │       └── qdrant-docs ✅
│   │
│   ├── "/home/donbr/graphiti-qdrant"
│   │   └── mcpServers
│   │       └── qdrant-docs ✅
│   │
│   ├── "/home/donbr/aie7/my-project"
│   │   └── mcpServers
│   │       ├── context7
│   │       ├── brave-search
│   │       └── qdrant-docs ❌ (not configured)
│   │
│   └── "/tmp"
│       └── mcpServers
│           └── qdrant-docs ✅ (can remove)
```

## Common Scenarios

### Scenario 1: Want `qdrant-docs` Everywhere

**Problem:** Too many projects to configure individually.

**Solution:** Most of your projects are under `/home/donbr/`, which **already has `qdrant-docs`**.

It will work automatically **unless** a subdirectory has its own `mcpServers` defined.

For projects with their own configs, use the helper script:

```bash
for project in ~/aie7/*; do
  python scripts/add_qdrant_to_project.py "$project"
done
```

### Scenario 2: Want to Remove `/tmp` Config

```bash
# Method 1: Use jq
jq 'del(.projects["/tmp"])' ~/.claude.json > /tmp/claude.json.tmp && mv /tmp/claude.json.tmp ~/.claude.json

# Method 2: Remove manually
# Edit ~/.claude.json and delete the "/tmp" section under projects
```

### Scenario 3: Check Which MCP Servers Are Available

```bash
# From any directory
claude mcp list

# This shows MCP servers for the current working directory
```

## Best Practices

1. **Home directory config** - Good for general-purpose tools you want everywhere
2. **Project-specific configs** - Better for project-specific tools or overrides
3. **Use absolute paths** - Ensures MCP servers work from any directory
4. **Document in README** - List required MCP servers in project docs
5. **Share configs** - Team members need to set up their own `~/.claude.json`

## Summary

- ✅ All MCP configs are in `~/.claude.json`
- ✅ Organized by project path
- ✅ No inheritance if a project has its own `mcpServers`
- ✅ Use helper script to add to new projects
- ❌ No global config (use `/home/donbr` as pseudo-global)
