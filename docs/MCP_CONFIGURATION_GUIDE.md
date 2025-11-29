# MCP Server Configuration Guide

## Choose Your Setup Method

You have **two options** for configuring the Qdrant MCP server with Claude Code:

## Comparison

| Feature | Project-Specific | Global |
|---------|------------------|--------|
| **Scope** | Only this project | All Claude Code sessions |
| **Configuration file** | `.claude/mcp.json` (in project) | `~/.claude/mcp.json` (user home) |
| **Availability** | Only when working in `/home/donbr/graphiti-qdrant` | Everywhere |
| **Setup command** | `./scripts/add_to_claude_code_project.sh` | `./scripts/add_to_claude_code.sh` |
| **Dependencies** | Uses project's uv environment | Uses project's uv environment |
| **Environment vars** | From project's `.env` | From project's `.env` |
| **Best for** | Isolated project work | Frequent doc searches across projects |

## Recommendation

**Use Project-Specific (Option A)** if:
- ✅ You primarily work on this project
- ✅ You want clean separation between projects
- ✅ You might move/delete this project later
- ✅ You want to version control the MCP config (`.claude/mcp.json` is checked in)

**Use Global (Option B)** if:
- ✅ You want documentation search everywhere
- ✅ You don't mind the dependency on this project's location
- ✅ You frequently need to look up documentation while working on other projects

## Setup Instructions

### Option A: Project-Specific (Recommended)

1. **Run the setup script:**
   ```bash
   ./scripts/add_to_claude_code_project.sh
   ```

2. **Verify the configuration:**
   ```bash
   cat .claude/mcp.json
   ```

   You should see:
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

3. **Start Claude Code in this project:**
   ```bash
   cd /home/donbr/graphiti-qdrant
   claude
   ```

4. **Test it:**
   > "What documentation sources are available?"

   Claude should use the `list_sources()` tool.

### Option B: Global Configuration

1. **Run the setup script:**
   ```bash
   ./scripts/add_to_claude_code.sh
   ```

2. **Verify the configuration:**
   ```bash
   claude mcp list
   ```

   You should see `qdrant-docs` in the output.

3. **Test it from any directory:**
   ```bash
   cd /tmp
   claude
   ```

   > "What documentation sources are available?"

   Claude should use the `list_sources()` tool even from `/tmp`.

## Switching Between Options

### From Project-Specific to Global

1. The `.claude/mcp.json` file already exists (checked into git)
2. Run the global setup:
   ```bash
   ./scripts/add_to_claude_code.sh
   ```
3. Now you have BOTH configurations (project-specific takes precedence when in this project)

### From Global to Project-Specific Only

1. Remove the global configuration:
   ```bash
   claude mcp remove qdrant-docs
   ```

2. The project-specific configuration in `.claude/mcp.json` remains active when working in this project

## Technical Details

### Project-Specific Configuration

**Location:** `/home/donbr/graphiti-qdrant/.claude/mcp.json`

**How it works:**
- Claude Code automatically loads `.claude/mcp.json` when starting in a directory
- Environment variables are resolved from the project's `.env` file
- The `uv run` command executes in the project directory
- No global configuration needed

**Pros:**
- ✅ Clean, isolated configuration
- ✅ Can be version controlled (already in git)
- ✅ No impact on other projects
- ✅ Easy to share with team

**Cons:**
- ⚠️ Only works in this project directory
- ⚠️ Need to `cd` to project to use

### Global Configuration

**Location:** `~/.claude/mcp.json`

**How it works:**
- Claude Code always loads `~/.claude/mcp.json` for all sessions
- The command specifies absolute paths to this project
- Environment variables loaded from this project's `.env`
- Available everywhere, but tied to this project

**Pros:**
- ✅ Available in all Claude Code sessions
- ✅ No need to `cd` to project

**Cons:**
- ⚠️ Breaks if you move/delete this project
- ⚠️ Harder to share configuration with team
- ⚠️ Global namespace (name conflicts possible)

## Environment Variables

Both configurations use the same environment variables from `.env`:

```bash
QDRANT_API_URL=https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
OPENAI_API_KEY=sk-proj-your_openai_key
```

**Project-Specific:** Automatically loads `.env` from project root

**Global:** Loads `.env` from the project path specified in the command

## Troubleshooting

### Project-Specific not working

1. **Check if Claude Code is in the project directory:**
   ```bash
   pwd
   # Should output: /home/donbr/graphiti-qdrant
   ```

2. **Verify `.claude/mcp.json` exists:**
   ```bash
   ls -la .claude/mcp.json
   ```

3. **Test the MCP server directly:**
   ```bash
   uv run python scripts/test_mcp_server.py
   ```

### Global not working

1. **Check global MCP configuration:**
   ```bash
   claude mcp list
   ```

2. **Verify the server is registered:**
   ```bash
   cat ~/.claude/mcp.json | grep qdrant-docs
   ```

3. **Check absolute paths are correct:**
   ```bash
   ls /home/donbr/graphiti-qdrant/mcp_server.py
   ```

## Version Control

The **project-specific** configuration (`.claude/mcp.json`) is already checked into git.

If someone else clones this repository:
1. They run `uv sync` to install dependencies
2. They copy `.env.example` to `.env` and add their API keys
3. The `.claude/mcp.json` file is already present
4. They start Claude Code in the project - it works automatically!

The **global** configuration is NOT version controlled (it's in `~/.claude/mcp.json`).

## Recommendation Summary

For this project, I recommend **Project-Specific** because:
1. ✅ Configuration already exists in `.claude/mcp.json`
2. ✅ Team members can clone and use immediately
3. ✅ Clean separation from other work
4. ✅ No dependency on absolute paths

You can always add the global configuration later if you find yourself wanting documentation search in other projects.
