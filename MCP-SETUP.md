# MCP Server Configuration Guide

**Last Updated**: 2025-11-30
**Migration Status**: ✅ COMPLETED
**Configuration Scope**: User (Global)

---

## Overview

All MCP servers for this project are configured globally (user scope) and available across all projects. This setup provides maximum reusability while maintaining clean project-specific configuration.

## User Scope (Global) Servers

These servers are available in all your projects:

### Utility Servers

#### playwright
- **Purpose**: Browser automation for testing and web interaction
- **Scope**: User (Global)
- **Command**: `npx -y @playwright/mcp@latest`
- **Environment Variables**: None

#### falkordb
- **Purpose**: Graph database operations
- **Scope**: User (Global)
- **Command**: `uv run --directory /home/donbr/graphiti-org/falkordb-fastmcp python main.py`
- **Environment Variables**: None

#### mcp-server-time
- **Purpose**: Timezone conversion and time queries
- **Scope**: User (Global)
- **Command**: `uvx mcp-server-time --local-timezone=America/Los_Angeles`
- **Environment Variables**: None
- **Example Usage**: "What time is it in Tokyo?"

#### sequential-thinking
- **Purpose**: Advanced reasoning framework for complex problem-solving
- **Scope**: User (Global)
- **Command**: `npx -y @modelcontextprotocol/server-sequential-thinking`
- **Environment Variables**: None
- **Example Usage**: "Use sequential thinking to analyze why vector databases outperform traditional databases for semantic search"

### Documentation Servers

#### Context7
- **Purpose**: Real-time documentation lookup with semantic search
- **Scope**: User (Global)
- **Command**: `npx -y @upstash/context7-mcp`
- **Environment Variables**: `CONTEXT7_API_KEY` (optional but recommended)
- **API Key**: Get at https://context7.com/dashboard
- **Rate Limits**: Higher limits with API key, lower without
- **Example Usage**: "Search Context7 for FastMCP authentication examples"
- **⚠️ Note**: Uses `CONTEXT7_API_KEY` (NOT `CALCOM_API_KEY` - this was a bug that's been fixed)

#### ai-docs-server
- **Purpose**: Access to 13 llms.txt documentation indexes
- **Scope**: User (Global)
- **Command**: `uvx --from mcpdoc mcpdoc --urls [13 documentation sources]`
- **Environment Variables**: None
- **Documentation Sources**:
  - Cursor: https://docs.cursor.com/llms.txt
  - PydanticAI: https://ai.pydantic.dev/llms.txt
  - MCPProtocol: https://modelcontextprotocol.io/llms.txt
  - FastMCP: https://gofastmcp.com/llms.txt
  - GoogleA2A: https://google-a2a.github.io/A2A/latest/llms.txt
  - LangChain: https://docs.langchain.com/llms.txt
  - Prefect: https://docs.prefect.io/llms.txt
  - VercelAI: https://sdk.vercel.ai/llms.txt
  - Anthropic: https://docs.anthropic.com/llms.txt
  - OpenAI: https://cdn.openai.com/API/docs/txt/llms.txt
  - Vue: https://vuejs.org/llms.txt
  - Supabase: https://supabase.com/llms.txt
  - Zep: https://help.getzep.com/llms.txt
- **Use Case**: Discovery - "What topics does LangChain cover?", "Show me Anthropic's documentation index"

#### qdrant-docs
- **Purpose**: Semantic search over pre-indexed llms-full.txt documentation (chunked by page)
- **Scope**: User (Global)
- **Command**: `uv run --directory /home/donbr/graphiti-qdrant --with fastmcp fastmcp run /home/donbr/graphiti-qdrant/mcp_server.py`
- **Collection**: llms-full-silver (Qdrant vector database)
- **Chunking Strategy**: RecursiveCharacterTextSplitter (chunk_size=1000, chunk_overlap=100)
- **Environment Variables**:
  - `QDRANT_API_URL` (required)
  - `QDRANT_API_KEY` (required)
  - `OPENAI_API_KEY` (required for embeddings)
- **Use Case**: Detailed queries - "How do I implement async streaming in LangChain?", "Explain Claude's prompt caching implementation"
- **Note**: Points to this project's directory but provides global documentation access

---

## Documentation Server Strategy

### Complementary Design

The documentation servers are **intentionally complementary**, not redundant:

**ai-docs-server** (lightweight llms.txt):
- File size: ~10-50KB per source
- Content: Index/table of contents level
- Purpose: Discovery and topic overview
- Token usage: Minimal

**qdrant-docs** (semantic search llms-full.txt):
- File size: 1-10MB+ per source (pre-indexed)
- Content: Complete documentation with examples
- Purpose: Detailed implementation queries
- Token usage: 90%+ reduction vs. full-text retrieval (due to semantic search)

### When to Use Each

```
ai-docs-server Examples:
> "What documentation is available for LangChain?"
> "Show me the main sections of Anthropic docs"
> "List Prefect's documentation topics"

qdrant-docs Examples:
> "How do I implement streaming with async in LangChain?"
> "Show me detailed examples of Claude's prompt caching"
> "Explain FastMCP authentication with code examples"
```

### Combined Workflow

1. **Discovery**: Use ai-docs-server to find what's available
2. **Deep Dive**: Use qdrant-docs for detailed implementation
3. **Result**: Optimal context usage and cost efficiency

---

## Environment Variables

### Required Environment Variables

Add these to your shell environment (~/.bashrc or ~/.zshrc):

```bash
# Qdrant Vector Store (for qdrant-docs)
export QDRANT_API_URL="https://your-instance.cloud.qdrant.io:6333"
export QDRANT_API_KEY="your-qdrant-api-key"

# OpenAI (for embeddings in qdrant-docs)
export OPENAI_API_KEY="your-openai-api-key"

# Context7 (optional but recommended for higher rate limits)
export CONTEXT7_API_KEY="your-context7-api-key"
```

### Getting API Keys

- **Qdrant**: https://cloud.qdrant.io/
- **OpenAI**: https://platform.openai.com/api-keys
- **Context7**: https://context7.com/dashboard (optional - provides higher rate limits)

### Verifying Environment Variables

```bash
# Check if all required variables are set
echo "QDRANT_API_URL: ${QDRANT_API_URL:+SET}"
echo "QDRANT_API_KEY: ${QDRANT_API_KEY:+SET}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo "CONTEXT7_API_KEY: ${CONTEXT7_API_KEY:+SET}"
```

---

## Adding New MCP Servers

### Decision Tree

**Question 1**: Is this server useful across multiple projects?
- **YES** → Use `--scope user` (global)
- **NO** → Use `--scope project` (project-specific)

**Question 2**: Does it have complex configuration (many args, environment variables)?
- **YES** → Use `claude mcp add-json`
- **NO** → Use `claude mcp add`

### Examples

**Simple Global Server**:
```bash
claude mcp add --transport stdio myserver --scope user -- npx -y @org/myserver
```

**Complex Global Server**:
```bash
claude mcp add-json myserver --scope user '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@org/myserver"],
  "env": {"API_KEY": "${API_KEY}"}
}'
```

**Project-Specific Server**:
```bash
claude mcp add --transport stdio project-tool --scope project -- ./scripts/mcp-tool.py
```

---

## Managing MCP Servers

### Listing Servers

```bash
# List all configured MCP servers
claude mcp list

# Get details for a specific server
claude mcp get servername
```

### Removing Servers

```bash
# Remove a user-scoped (global) server
claude mcp remove servername --scope user

# Remove a project-scoped server
claude mcp remove servername --scope project
```

### Checking Server Status

Within Claude Code:
```
> /mcp
```

This shows all servers with authentication status and health checks.

---

## Troubleshooting

### Server Not Found

```bash
# Verify server is configured
claude mcp list

# Check server details
claude mcp get servername
```

### Authentication Errors

**For Qdrant/OpenAI**:
```bash
# Verify environment variables are set in your shell
echo $QDRANT_API_KEY
echo $OPENAI_API_KEY
```

**For Context7**:
```bash
# Ensure using CONTEXT7_API_KEY (not CALCOM_API_KEY)
echo $CONTEXT7_API_KEY

# Verify key is valid at dashboard
open https://context7.com/dashboard
```

### Context7 401 Errors

**Common Issue**: Using `CALCOM_API_KEY` instead of `CONTEXT7_API_KEY`

**Fix**:
1. Check your configuration uses `CONTEXT7_API_KEY`
2. Verify the environment variable is set: `echo $CONTEXT7_API_KEY`
3. Get/verify your API key at: https://context7.com/dashboard

### Server Won't Start

**Check Command**:
```bash
# Get the exact command being used
claude mcp get servername

# Test the command manually
# Copy the command from output and run it
```

**Check Dependencies**:
```bash
# For npx-based servers
npm install -g @org/package

# For uvx-based servers
uv tool install package-name
```

---

## Maintenance

### Monthly Audit Checklist

- [ ] Run `claude mcp list` - review all configured servers
- [ ] Remove unused servers to reduce overhead
- [ ] Check Context7 rate limit usage at dashboard
- [ ] Verify API keys are still valid
- [ ] Update server dependencies if needed

### Backup Configuration

Before making major changes:

```bash
# Backup user-level config
cp ~/.claude.json ~/.claude.json.backup.$(date +%Y%m%d)
```

### Rate Limit Monitoring

**Context7**:
- Check usage at: https://context7.com/dashboard
- Upgrade plan if hitting limits frequently

**OpenAI**:
- Monitor usage at: https://platform.openai.com/usage
- qdrant-docs uses embeddings (text-embedding-3-small model)

**Qdrant**:
- Check cluster usage at: https://cloud.qdrant.io/
- Monitor collection size and query volume

---

## Migration History

### 2025-11-30: Global Migration Completed

**What Changed**:
- ✅ Fixed critical bug: Context7 API key variable (CALCOM_API_KEY → CONTEXT7_API_KEY)
- ✅ Migrated 5 servers from project/local scope to user scope
- ✅ Cleaned up configuration file fragmentation
- ✅ Created comprehensive documentation

**Migrated Servers**:
1. mcp-server-time (Project → User)
2. sequential-thinking (Project → User)
3. Context7 (Project → User, API key fixed)
4. ai-docs-server (Project → User)
5. qdrant-docs (Already User scope, validated)

**Files Archived**:
- `.archive/mcp-config-original.json` - Original backup config
- `.archive/mcp.json.backup.20251130_120659` - Pre-migration backup

**Effectiveness Improvement**: 4/10 → 9/10

---

## Best Practices

### Environment Variable Management

✅ **DO**:
- Store secrets in shell environment (~/.bashrc, ~/.zshrc)
- Use `${VAR}` syntax in MCP configs
- Keep .env.example for documentation
- Never commit .env files with real keys

❌ **DON'T**:
- Hardcode API keys in config files
- Use `${env:VAR}` syntax (incorrect)
- Commit secrets to version control
- Share API keys in screenshots or logs

### Scope Strategy

**User Scope** (Global):
- Generic utilities (time, thinking, browser automation)
- Documentation servers used across projects
- Tools with no project-specific dependencies

**Project Scope**:
- Project-specific tools and scripts
- Servers tied to project directory structure
- Custom integrations unique to the project

**Local Scope**:
- Experimental configurations
- Temporary server overrides
- Personal customizations not for sharing

### Configuration as Code

- Keep .mcp.json minimal (or empty for fully global setup)
- Document server purposes in this file
- Use version control for .mcp.json (but NOT .env)
- Archive old configs before major changes

---

## Support and Resources

### Official Documentation

- **MCP Protocol**: https://modelcontextprotocol.io
- **Claude Code**: https://code.claude.com/docs/en/mcp
- **Context7**: https://context7.com/docs
- **Qdrant**: https://qdrant.tech/documentation/

### Getting Help

**MCP Servers**:
- GitHub: https://github.com/modelcontextprotocol/servers
- Community: https://discord.gg/modelcontextprotocol

**Claude Code**:
- Documentation: https://code.claude.com/docs
- GitHub Issues: https://github.com/anthropics/claude-code/issues

---

## Appendix: Complete Server List

| Server | Scope | Purpose | Dependencies |
|--------|-------|---------|--------------|
| playwright | User | Browser automation | npx |
| falkordb | User | Graph database | uv, Python |
| mcp-server-time | User | Timezone conversion | uvx |
| sequential-thinking | User | Reasoning framework | npx |
| Context7 | User | Doc lookup | npx, CONTEXT7_API_KEY (opt) |
| ai-docs-server | User | 13 doc indexes | uvx, mcpdoc |
| qdrant-docs | User | Semantic doc search | uv, Qdrant, OpenAI |

**Total**: 7 global servers, 0 project servers, 0 local servers

---

**This documentation was created as part of the MCP Global Migration project on 2025-11-30.**

For detailed migration process and research findings, see:
- [MCP_GLOBAL_MIGRATION_PLAN_V2.md](./MCP_GLOBAL_MIGRATION_PLAN_V2.md)
- [MCP_MIGRATION_BLOG_POST.md](./MCP_MIGRATION_BLOG_POST.md)
