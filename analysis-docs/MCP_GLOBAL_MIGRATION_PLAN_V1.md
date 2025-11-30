# MCP Global Migration Plan - Version 1.0

**Project**: graphiti-qdrant MCP Server Consolidation
**Date**: 2025-11-30
**Objective**: Convert project-scoped MCP servers to user/global scope for cross-project availability

---

## Executive Summary

This plan addresses critical scope misalignment in the current MCP server configuration. Four generic utility servers are incorrectly configured at project scope, forcing reconfiguration for each new project. This migration will convert them to user scope (global), making them available across all projects while maintaining consistency and reducing maintenance burden.

**Current State**: 2 user-scoped, 4 project-scoped, 1 local-scoped servers
**Target State**: 7 user-scoped servers with clean, consolidated configuration
**Effectiveness Improvement**: 4/10 → 9/10

---

## Current State Analysis

### MCP Server Inventory

| Server Name | Current Scope | Should Be | Reason |
|------------|---------------|-----------|---------|
| playwright | User ✅ | User | Generic browser automation |
| falkordb | User ✅ | User | Generic graph database tool |
| **mcp-server-time** | **Project ❌** | **User** | Generic timezone utility |
| **sequential-thinking** | **Project ❌** | **User** | Generic reasoning framework |
| **Context7** | **Project ❌** | **User** | Generic documentation lookup |
| **ai-docs-server** | **Project ❌** | **User** | Generic docs access (13 sources) |
| qdrant-docs | Local ⚠️ | User (TBD) | Semantic doc search - needs research |

### Configuration File Status

```
📁 Configuration Files (BEFORE)
├── .mcp.json (Project scope)
│   ├── mcp-server-time
│   ├── sequential-thinking
│   ├── Context7
│   └── ai-docs-server
├── .claude/mcp.json (Local scope)
│   └── qdrant-docs [CONFIG DRIFT ISSUE]
└── .mcp copy.json (Backup/inactive)
    └── 6 servers including variants
```

---

## Critical Issues Identified

### 🔴 Issue 1: Wrong Scope for Generic Tools (CRITICAL)

**Problem**: Generic utilities configured at project scope instead of user scope

**Impact**:
- Must reconfigure for every new project
- Violates DRY (Don't Repeat Yourself) principle
- Defeats MCP's scope system design
- Increases maintenance burden

**Affected Servers**: mcp-server-time, sequential-thinking, Context7, ai-docs-server

### 🔴 Issue 2: Configuration Drift (CRITICAL)

**Problem**: qdrant-docs config in `.claude/mcp.json` doesn't match actual running command

**Config Says**:
```json
{
  "command": "uv",
  "args": ["run", "python", "mcp_server.py"]
}
```

**Actually Running**:
```bash
uv run --directory /home/donbr/graphiti-qdrant --with fastmcp fastmcp run /home/donbr/graphiti-qdrant/mcp_server.py
```

**Impact**: Config file cannot successfully start the server if used fresh

### 🔴 Issue 3: Invalid Environment Variable Syntax (CRITICAL)

**Problem**: Using `${env:VAR}` instead of `${VAR}`

**Location**: `.claude/mcp.json` lines 7-9

**Impact**: May cause startup failures or variable expansion issues

### 🟡 Issue 4: Configuration File Fragmentation (MODERATE)

**Problem**: Three MCP config files with overlapping definitions

**Impact**: Confusion about source of truth, versioning challenges

### 🟡 Issue 5: Functional Duplication (MODERATE)

**Question**: Are ai-docs-server and qdrant-docs intentionally complementary?

- **ai-docs-server**: Fetches from 13 llms.txt sources on-demand
- **qdrant-docs**: Semantic search over pre-indexed documentation

**Needs Research**: Clarify intended use cases and relationship

### 🟢 Issue 6: Mystery Environment Variable (LOW)

**Question**: Why does Context7 require CALCOM_API_KEY?

**Needs Research**: Investigate if this is required and what it's used for

---

## Research Questions

Before proceeding with migration, these questions require investigation:

### 1. qdrant-docs Scope Decision

**User's Position**: Should be global - contains llms-full.txt split by page to reduce context overhead

**Research Needed**:
- Current best practices for global documentation servers
- Whether project-specific path dependencies are acceptable in global scope
- Alternative approaches for cross-project documentation access

### 2. CALCOM_API_KEY Requirement

**Research Needed**:
- Is CALCOM_API_KEY actually required for Context7?
- What happens if removed?
- Does it affect rate limits (daily/monthly requests)?
- Context7 official documentation review

### 3. ai-docs-server vs qdrant-docs Relationship

**User's Position**: Complementary - qdrant-docs is initial subset of ai-docs-server's llms-full.txt versions

**Understanding**:
- ai-docs-server: Fetches llms.txt files (lightweight)
- qdrant-docs: Pre-processed llms-full.txt split by page (comprehensive but indexed)
- Use case: qdrant-docs reduces context size and cost

**Validation Needed**: Confirm this strategy aligns with current best practices

### 4. Environment Variable Strategy

**Current Issues**:
- Inconsistent env object handling (sometimes empty `{}`, sometimes omitted)
- Incorrect `${env:VAR}` syntax
- Reliance on .env files vs shell environment

**Research Needed**:
- Best practices for MCP server environment variables
- Testing approach to verify env vars are accessible globally
- Strategy for managing secrets across projects

---

## Migration Plan (Pending Research)

### Phase 1: Pre-Migration Research ⏳

**Status**: IN PROGRESS

**Tasks**:
- [ ] Research Context7 CALCOM_API_KEY requirement
- [ ] Validate qdrant-docs global scope approach
- [ ] Review environment variable best practices
- [ ] Test current environment variable accessibility

### Phase 2: Backup Current Configuration

```bash
# Backup all MCP configs with timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
cp .mcp.json ".mcp.json.backup.$timestamp"
cp .claude/mcp.json ".claude/mcp.json.backup.$timestamp"
cp ".mcp copy.json" ".mcp-copy.json.backup.$timestamp"
```

### Phase 3: Convert Simple Servers to User Scope

**3.1. mcp-server-time**
```bash
claude mcp add --transport stdio mcp-server-time --scope user \
  -- uvx mcp-server-time --local-timezone=America/Los_Angeles
```

**3.2. sequential-thinking**
```bash
claude mcp add --transport stdio sequential-thinking --scope user \
  -- npx -y @modelcontextprotocol/server-sequential-thinking
```

**Verification**:
```bash
claude mcp get mcp-server-time    # Should show "User config"
claude mcp get sequential-thinking # Should show "User config"
```

### Phase 4: Convert Complex Servers with JSON

**4.1. Context7** (pending CALCOM_API_KEY research)
```bash
# Version A: With CALCOM_API_KEY (if research confirms it's needed)
claude mcp add-json Context7 --scope user '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp"],
  "env": {"CALCOM_API_KEY": "${CALCOM_API_KEY}"}
}'

# Version B: Without CALCOM_API_KEY (if research shows it's not needed)
claude mcp add-json Context7 --scope user '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp"]
}'
```

**4.2. ai-docs-server**
```bash
claude mcp add-json ai-docs-server --scope user '{
  "type": "stdio",
  "command": "uvx",
  "args": [
    "--from", "mcpdoc", "mcpdoc",
    "--urls",
    "Cursor:https://docs.cursor.com/llms.txt",
    "PydanticAI:https://ai.pydantic.dev/llms.txt",
    "MCPProtocol:https://modelcontextprotocol.io/llms.txt",
    "FastMCP:https://gofastmcp.com/llms.txt",
    "GoogleA2A:https://google-a2a.github.io/A2A/latest/llms.txt",
    "LangChain:https://docs.langchain.com/llms.txt",
    "Prefect:https://docs.prefect.io/llms.txt",
    "VercelAI:https://sdk.vercel.ai/llms.txt",
    "Anthropic:https://docs.anthropic.com/llms.txt",
    "OpenAI:https://cdn.openai.com/API/docs/txt/llms.txt",
    "Vue:https://vuejs.org/llms.txt",
    "Supabase:https://supabase.com/llms.txt",
    "Zep:https://help.getzep.com/llms.txt",
    "--transport", "stdio",
    "--follow-redirects",
    "--timeout", "20",
    "--allowed-domains",
    "ai.pydantic.dev", "modelcontextprotocol.io", "raw.githubusercontent.com",
    "docs.langchain.com", "sdk.vercel.ai", "docs.cursor.com",
    "docs.anthropic.com", "gofastmcp.com", "google-a2a.github.io",
    "vuejs.org", "supabase.com", "cdn.openai.com",
    "docs.prefect.io", "getzep.com"
  ]
}'
```

### Phase 5: Handle qdrant-docs (Pending Scope Decision)

**Option A: Convert to User Scope** (User's preference - pending validation)

```bash
claude mcp add-json qdrant-docs --scope user '{
  "type": "stdio",
  "command": "uv",
  "args": [
    "run", "--directory", "/home/donbr/graphiti-qdrant",
    "--with", "fastmcp", "fastmcp", "run",
    "/home/donbr/graphiti-qdrant/mcp_server.py"
  ],
  "env": {
    "QDRANT_API_URL": "${QDRANT_API_URL}",
    "QDRANT_API_KEY": "${QDRANT_API_KEY}",
    "OPENAI_API_KEY": "${OPENAI_API_KEY}"
  }
}'
```

**Consideration**: This makes qdrant-docs globally available but always points to this project's directory and Qdrant collection. This is acceptable if:
- The llms-full.txt collection is intended for global use
- Other projects benefit from accessing this centralized documentation
- The project path dependency is understood and intentional

### Phase 6: Comprehensive Testing

**6.1. Verify Scope Assignment**
```bash
# All should show "User config (available in all your projects)"
claude mcp get mcp-server-time
claude mcp get sequential-thinking
claude mcp get Context7
claude mcp get ai-docs-server
claude mcp get qdrant-docs
```

**6.2. Functional Testing**

Within Claude Code:
```
> What time is it in Tokyo? (tests mcp-server-time)
> Use sequential thinking to analyze [complex problem] (tests sequential-thinking)
> Search Context7 for [technical topic] (tests Context7)
> Get documentation for [topic] from ai-docs-server (tests ai-docs-server)
> Search qdrant-docs for [technical concept] (tests qdrant-docs)
```

**6.3. Cross-Project Availability Test**
```bash
cd /tmp
claude mcp list  # All user-scoped servers should appear
# Test functionality from different directory
```

**6.4. Environment Variable Validation**
```bash
# Ensure all required env vars are accessible
echo $QDRANT_API_URL
echo $QDRANT_API_KEY
echo $OPENAI_API_KEY
echo $CALCOM_API_KEY  # If needed

# If any are missing, add to ~/.bashrc or ~/.zshrc
export QDRANT_API_URL="your-value"
export QDRANT_API_KEY="your-value"
export OPENAI_API_KEY="your-value"
```

### Phase 7: Cleanup Configuration Files

**7.1. Clean .mcp.json**
```bash
# Remove all 4 converted servers from .mcp.json
# File should become empty or contain only project-specific servers
```

Result:
```json
{
  "mcpServers": {}
}
```

**7.2. Remove .claude/mcp.json**
```bash
# If qdrant-docs was converted to user scope
rm .claude/mcp.json

# Otherwise, update it with corrected configuration
```

**7.3. Archive Backup File**
```bash
mv ".mcp copy.json" .archive/mcp-config-backup.json
```

### Phase 8: Documentation

**8.1. Create MCP-SETUP.md**

Document all global MCP servers, their purposes, and required environment variables.

**8.2. Update Project README**

Add section about MCP server dependencies and setup requirements.

**8.3. Create Environment Variable Template**

Create `.env.example` with all required variables:
```bash
# MCP Server Environment Variables
QDRANT_API_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
OPENAI_API_KEY=your-openai-api-key
CALCOM_API_KEY=your-calcom-api-key  # If required by Context7
```

---

## Rollback Plan

If issues arise during migration:

```bash
# Restore from backups
timestamp="YYYYMMDD_HHMMSS"  # Use actual backup timestamp
cp ".mcp.json.backup.$timestamp" .mcp.json
cp ".claude/mcp.json.backup.$timestamp" .claude/mcp.json

# Remove user-scoped servers
claude mcp remove mcp-server-time --scope user
claude mcp remove sequential-thinking --scope user
claude mcp remove Context7 --scope user
claude mcp remove ai-docs-server --scope user
claude mcp remove qdrant-docs --scope user  # If converted

# Restart Claude Code to reload project configs
```

---

## Success Criteria

- [ ] All 4 target servers converted to user scope
- [ ] qdrant-docs scope decision made and implemented
- [ ] All servers show "User config" in `claude mcp list`
- [ ] All servers functional in current project
- [ ] All servers accessible from different project directory
- [ ] Environment variables properly configured and accessible
- [ ] Configuration files cleaned and consolidated
- [ ] Documentation created (MCP-SETUP.md)
- [ ] No configuration drift issues
- [ ] No duplicate servers at multiple scopes

---

## Post-Migration Best Practices

### Adding New MCP Servers

**Decision Tree**:
1. Is this server useful across multiple projects?
   - YES → Use `--scope user`
   - NO → Use `--scope project` or `--scope local`

2. Does it have complex configuration (many args, env vars)?
   - YES → Use `claude mcp add-json`
   - NO → Use `claude mcp add`

### Environment Variable Management

- Store secrets in shell environment (~/.bashrc, ~/.zshrc)
- NEVER commit .env files with real API keys
- Use .env.example for documentation
- Use ${VAR} syntax in .mcp.json files (NOT ${env:VAR})

### Configuration Maintenance

- Keep only ONE source of truth per scope
- Document purpose of each MCP server
- Regularly audit with `claude mcp list`
- Remove unused servers promptly
- Back up configs before major changes

---

## Timeline

**Phase 1 (Research)**: Pending completion
**Phase 2-7 (Migration)**: ~1-2 hours
**Phase 8 (Documentation)**: ~30 minutes

**Total Estimated Time**: 2-3 hours including research validation

---

## Open Questions for Research (v2)

1. **Context7 CALCOM_API_KEY**: Required? Rate limit implications?
2. **qdrant-docs global scope**: Best practice validation needed
3. **Environment variables**: Test accessibility from user scope
4. **ai-docs-server vs qdrant-docs**: Validate complementary strategy

**Next Step**: Complete research phase and create v2 with findings incorporated.

---

## Notes

- This is v1 - pending research validation
- v2 will incorporate research findings
- All critical issues identified must be addressed
- User preference for qdrant-docs global scope noted
- Blog post to follow documenting the analysis experience

---

**Document Status**: Draft v1 - Pending Research
**Last Updated**: 2025-11-30
**Next Update**: After research completion
