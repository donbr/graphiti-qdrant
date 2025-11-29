# How Claude Code MCP Configuration Actually Works

## Important Discovery

Claude Code does **NOT** have a traditional "global" MCP configuration. Instead:

1. **All MCP servers are project-specific** - stored in `~/.claude.json` under `projects["/path/to/project"]`
2. **Each directory gets its own config** - When you run `claude` in a directory, it looks up that path in `~/.claude.json`
3. **Home directory is special** - Configuring MCP for `/home/donbr` makes it available when running `claude` from your home directory or subdirectories (unless they have their own config)

## How We Set It Up

We added `qdrant-docs` to the `/home/donbr` project config:

```json
{
  "projects": {
    "/home/donbr": {
      "mcpServers": {
        "qdrant-docs": {
          "type": "stdio",
          "command": "uv",
          "args": [
            "run",
            "--directory",
            "/home/donbr/graphiti-qdrant",
            "python",
            "/home/donbr/graphiti-qdrant/mcp_server.py"
          ],
          "env": {
            "QDRANT_API_URL": "...",
            "QDRANT_API_KEY": "...",
            "OPENAI_API_KEY": "..."
          }
        }
      }
    }
  }
}
```

## Where It Works

✅ **Works when you run `claude` from:**
- `/home/donbr` (home directory)
- `/home/donbr/any-project` (subdirectories without their own MCP config)
- Anywhere under `/home/donbr/`

❌ **Does NOT work when you run `claude` from:**
- `/tmp` or other directories outside `/home/donbr`
- Projects with their own MCP config that don't include `qdrant-docs`

## To Use From Any Directory

If you want `qdrant-docs` available in a specific project directory (like `/home/donbr/aie7/aie6`), you need to add it to that project's config:

```bash
cd /home/donbr/aie7/aie6
claude mcp add qdrant-docs \
  -e QDRANT_API_URL="..." \
  -e QDRANT_API_KEY="..." \
  -e OPENAI_API_KEY="..." \
  -- uv run --directory /home/donbr/graphiti-qdrant python /home/donbr/graphiti-qdrant/mcp_server.py
```

This adds `qdrant-docs` to the `/home/donbr/aie7/aie6` project config in `~/.claude.json`.

## Simpler Alternative: Project-Specific Config

Instead of configuring in `~/.claude.json`, you can use the **project-specific** `.claude/mcp.json` file that we already created:

**File:** `/home/donbr/graphiti-qdrant/.claude/mcp.json`

```json
{
  "mcpServers": {
    "qdrant-docs": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "env": {
        "QDRANT_API_URL": "${env:QDRANT_API_URL}",
        "QDRANT_API_KEY": "${env:QDRANT_API_KEY}",
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
      }
    }
  }
}
```

This **only** works when running `claude` from `/home/donbr/graphiti-qdrant`, but:
- ✅ It's checked into git (shareable with team)
- ✅ Environment variables auto-loaded from `.env`
- ✅ No manual configuration needed

## Current Status

You now have `qdrant-docs` configured in **two places**:

1. **`~/.claude.json` (for `/home/donbr`)** - Available when running `claude` from home directory or subdirectories
2. **`.claude/mcp.json` (for this project)** - Available when running `claude` specifically in `/home/donbr/graphiti-qdrant`

Both work! Choose whichever fits your workflow better.

## Recommendation

For **your workflow**, I recommend:

**Keep the `/home/donbr` config in `~/.claude.json`** because:
- ✅ Available in most of your working directories
- ✅ All your projects are under `/home/donbr/`
- ✅ One-time setup, works everywhere

**Exception:** If a specific project has its own MCP servers (like your AIE7 projects), you'll need to add `qdrant-docs` to those project configs too.

## Quick Test

From any directory under `/home/donbr`, run:

```bash
cd ~/aie7
claude
```

Then ask:

> "What documentation sources are available in qdrant-docs?"

If it works, the MCP server is configured correctly for that directory!
