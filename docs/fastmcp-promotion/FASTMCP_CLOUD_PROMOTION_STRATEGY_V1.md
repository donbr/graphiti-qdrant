# FastMCP Cloud Promotion Strategy v1.0

**Document Purpose**: Strategy for promoting local MCP servers to FastMCP Cloud
**Target Servers**: `qdrant-docs` and `falkordb`
**Date**: 2025-11-30
**Status**: Version 1.0 - Planning Phase

---

## Executive Summary

This strategy addresses the critical need to **promote local MCP servers to cloud-hosted endpoints**, enabling access across multiple platforms and tools. While local FastMCP servers (stdio transport) work perfectly with Claude Code Desktop, they're **inaccessible to web-based clients** like Claude Code Web, Claude.ai, and other cloud LLM applications.

**Core Problem**: Platform fragmentation limits MCP utility
- **Local (stdio)**: Works with Claude Code Desktop ✅
- **Cloud (HTTP)**: Required for Claude Code Web, Claude.ai, and multi-client access ❌

**Solution**: FastMCP Cloud deployment with robust local validation workflow

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [FastMCP Cloud Overview](#fastmcp-cloud-overview)
3. [The Human-in-the-Loop Advantage](#the-human-in-the-loop-advantage)
4. [Server Analysis: qdrant-docs](#server-analysis-qdrant-docs)
5. [Server Analysis: falkordb](#server-analysis-falkordb)
6. [Promotion Workflow](#promotion-workflow)
7. [Testing & Validation Strategy](#testing--validation-strategy)
8. [Deployment Checklist](#deployment-checklist)
9. [Security & Authentication](#security--authentication)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Rollback & Recovery](#rollback--recovery)

---

## Current State Analysis

### Local MCP Server Inventory

| Server | Location | Transport | Status | Cloud Ready? |
|--------|----------|-----------|--------|--------------|
| **qdrant-docs** | `/home/donbr/graphiti-qdrant` | stdio | ✅ Active | 🟡 Needs Prep |
| **falkordb** | `/home/donbr/graphiti-org/falkordb-fastmcp` | stdio | ✅ Active | 🟡 Needs Prep |

### Platform Access Matrix

| Platform | stdio (Local) | HTTP (Cloud) |
|----------|---------------|--------------|
| Claude Code Desktop | ✅ Works | ✅ Works |
| Claude Code Web | ❌ No Access | ✅ Works |
| Claude.ai | ❌ No Access | ✅ Works |
| Cursor Desktop | ✅ Works | ✅ Works |
| Mobile Clients | ❌ No Access | ✅ Works |

**Key Insight**: Cloud deployment unlocks 3-4x more platforms.

### Current Limitations

1. **Platform Lock-in**: Can only use MCP servers on machines where they're installed
2. **No Web Access**: Cannot use qdrant-docs or falkordb from Claude.ai or web clients
3. **Team Collaboration**: Cannot share MCP servers with teammates without manual setup
4. **Multi-Device**: Must configure servers separately on each machine

---

## FastMCP Cloud Overview

### What is FastMCP Cloud?

[FastMCP Cloud](https://fastmcp.cloud) is a managed platform by the FastMCP team for hosting MCP servers.

**Key Features**:
- **Free during beta** 🎉
- **GitHub-based deployment** (push to deploy)
- **Automatic HTTPS endpoints** (`https://your-project.fastmcp.app/mcp`)
- **Built-in OAuth authentication**
- **Zero infrastructure management**

### Deployment URL Pattern

```
https://<project-name>.fastmcp.app/mcp
```

**Example**:
- `qdrant-docs` → `https://qdrant-docs.fastmcp.app/mcp`
- `falkordb` → `https://falkordb-mcp.fastmcp.app/mcp`

### Prerequisites

✅ GitHub account
✅ Git repository with FastMCP server code
✅ Environment variables configuration
✅ FastMCP 2.0 compatible server (both ours are!)

---

## The Human-in-the-Loop Advantage

### FastMCP's Testing Philosophy

FastMCP provides **comprehensive local testing** that keeps humans in the loop BEFORE cloud deployment. This is the key differentiator from "deploy and pray" approaches.

### Three-Tier Testing Strategy

#### 1️⃣ **In-Memory Testing** (Fastest, Safest)

**What**: Test server logic directly in Python process - **no network, no deployment**

**Benefits**:
- ✅ Zero latency (microseconds vs. milliseconds)
- ✅ Deterministic (no network flakiness)
- ✅ Full Python debugging (breakpoints, stack traces)
- ✅ No external dependencies

**Example** (qdrant-docs):
```python
from fastmcp import FastMCP, Client
from mcp_server import mcp  # Your qdrant-docs server

async def test_search_locally():
    """Test qdrant-docs WITHOUT deploying anywhere"""
    # Direct in-memory connection
    async with Client(mcp) as client:
        # Ping the server
        assert await client.ping()

        # List available tools
        tools = await client.list_tools()
        assert "search_docs" in [t.name for t in tools]

        # Test search functionality
        result = await client.call_tool(
            "search_docs",
            {"query": "FastMCP authentication", "k": 3}
        )
        assert "Found 3 results" in result.content[0].text

        # Test source filtering
        result = await client.call_tool(
            "search_docs",
            {"query": "agents", "source": "LangChain"}
        )
        assert "LangChain" in result.content[0].text

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search_locally())
```

**Why This Matters**: Catch bugs in **seconds**, not after deployment.

#### 2️⃣ **Local HTTP Testing** (Network Behavior)

**What**: Run server locally on `localhost:8000`, test with HTTP client

**Benefits**:
- ✅ Tests real network transport
- ✅ Tests authentication flows (OAuth, API keys)
- ✅ Tests serialization/deserialization
- ✅ Still fully local (no cloud deployment)

**Example** (falkordb):
```python
import subprocess
import asyncio
from fastmcp import Client

# Start server in background (or use tmux/screen)
server_process = subprocess.Popen(
    ["uv", "run", "python", "main.py"],
    cwd="/home/donbr/graphiti-org/falkordb-fastmcp"
)

async def test_http_locally():
    """Test falkordb via HTTP before cloud deployment"""
    try:
        # Connect to local HTTP server
        async with Client("http://localhost:8000/mcp/") as client:
            await client.ping()

            # Test listing graphs
            result = await client.call_tool("list_graphs", {})
            graphs = json.loads(result.content[0].text)
            assert graphs["success"] == True

            # Test query execution
            result = await client.call_tool(
                "execute_query",
                {
                    "graph_name": "test",
                    "query": "MATCH (n) RETURN n LIMIT 5"
                }
            )
            assert "success" in result.content[0].text

    finally:
        server_process.terminate()

asyncio.run(test_http_locally())
```

**Why This Matters**: Validate **network behavior** before deploying to real users.

#### 3️⃣ **Preview Deployment** (Cloud Staging)

**What**: Deploy to FastMCP Cloud, test with real URL, **then** promote to production

**Benefits**:
- ✅ Tests actual cloud environment
- ✅ Tests GitHub OAuth integration
- ✅ Tests environment variable handling
- ✅ Can share preview URL with trusted testers

**Example Workflow**:
```bash
# Deploy to preview
git push origin preview-branch

# FastMCP Cloud auto-deploys to:
# https://qdrant-docs-preview.fastmcp.app/mcp

# Test from Claude Code Web
claude mcp add --transport http qdrant-docs-preview \
  https://qdrant-docs-preview.fastmcp.app/mcp

# Validate in Claude Code Web
> Search qdrant-docs for "prompt engineering"

# If works: merge to main
git checkout main
git merge preview-branch
git push origin main

# Now live at: https://qdrant-docs.fastmcp.app/mcp
```

**Why This Matters**: Test in **real cloud environment** with **zero user impact**.

### Human-in-the-Loop Benefits Summary

| Testing Tier | Speed | Realism | Risk | Best For |
|--------------|-------|---------|------|----------|
| In-Memory | ⚡⚡⚡ | Low | None | Logic & unit tests |
| Local HTTP | ⚡⚡ | Medium | None | Network & auth |
| Preview | ⚡ | High | Low | Final validation |

**Key Principle**: **Catch issues early** where they're cheap to fix, not in production.

---

## Server Analysis: qdrant-docs

### Overview

**Purpose**: Semantic search over pre-indexed llms-full.txt documentation
**Location**: `/home/donbr/graphiti-qdrant/mcp_server.py`
**Framework**: FastMCP 2.0 ✅
**Current Transport**: stdio (local only)
**Target Transport**: HTTP (cloud-accessible)

### Current Implementation Analysis

```python
# File: mcp_server.py
from fastmcp import FastMCP
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

mcp = FastMCP("qdrant-docs-search")

@mcp.tool()
def search_docs(query: str, k: int = 5, source: Optional[str] = None) -> str:
    """Semantic search over documentation"""
    # ... implementation

@mcp.tool()
def list_sources() -> str:
    """List available documentation sources"""
    # ... implementation
```

**✅ Cloud-Ready Indicators**:
- Uses FastMCP 2.0 framework
- No file system dependencies (uses remote Qdrant)
- Stateless design (each query independent)
- Environment variable based config

**⚠️ Cloud Preparation Needed**:
- API keys must be configured in FastMCP Cloud environment
- Test Qdrant connectivity from cloud (network access)
- Validate OpenAI API rate limits for cloud usage
- Consider response size limits (1000 char preview OK)

### Dependencies

**External Services**:
- Qdrant Cloud (already remote ✅)
- OpenAI API (already remote ✅)

**Environment Variables Required**:
```bash
QDRANT_API_URL=https://your-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=<secret>
OPENAI_API_KEY=<secret>
```

### Cloud Deployment Readiness: 🟢 HIGH

**Strengths**:
- Already uses cloud services (Qdrant, OpenAI)
- No local file dependencies
- Stateless design
- Well-defined tool interface

**Challenges**:
- Need to configure 3 environment variables in cloud
- OpenAI costs will increase with more users
- Qdrant rate limits to monitor

---

## Server Analysis: falkordb

### Overview

**Purpose**: FalkorDB graph database query interface
**Location**: `/home/donbr/graphiti-org/falkordb-fastmcp`
**Framework**: FastMCP 2.0 ✅
**Current Transport**: stdio (local only)
**Target Transport**: HTTP (cloud-accessible)

### Current Implementation Analysis

```python
# File: src/falkordb_mcp/server.py
from fastmcp import FastMCP

mcp = FastMCP("FalkorDB")

@mcp.tool()
def execute_query(
    graph_name: str,
    query: str,
    params: Optional[Dict[str, Any]] = None
) -> str:
    """Execute Cypher query against FalkorDB"""
    # ... implementation

@mcp.tool()
def list_graphs() -> str:
    """List all available graphs"""
    # ... implementation

@mcp.tool()
def get_graph_metadata(graph_name: str) -> str:
    """Get metadata for a specific graph"""
    # ... implementation
```

**✅ Cloud-Ready Indicators**:
- Uses FastMCP 2.0 framework
- Connects to external FalkorDB instance (configurable)
- Stateless query execution
- JSON-based responses

**⚠️ Cloud Preparation Needed**:
- FalkorDB connection must be network-accessible from cloud
- Authentication/authorization for multi-user access
- Query timeout configuration (prevent long-running queries)
- Consider read-only mode for public deployment

### Dependencies

**External Services**:
- FalkorDB instance (must be network-accessible)

**Environment Variables Required**:
```bash
FALKORDB_HOST=<host>
FALKORDB_PORT=<port>
FALKORDB_PASSWORD=<secret>  # if auth enabled
```

### Cloud Deployment Readiness: 🟡 MEDIUM

**Strengths**:
- Clean FastMCP implementation
- External database (no local state)
- Well-structured tools

**Challenges**:
- **FalkorDB accessibility**: Must ensure cloud can reach database
- **Security**: May need read-only user for cloud deployment
- **Query safety**: Need timeout/resource limits
- **Multi-tenancy**: Consider graph-level access control

**Recommendation**: Deploy with **read-only access** first, expand permissions later.

---

## Promotion Workflow

### Phase 1: Local Preparation

#### Step 1.1: Repository Setup

**qdrant-docs**:
```bash
cd /home/donbr/graphiti-qdrant

# Ensure clean git state
git status

# Create deployment branch
git checkout -b fastmcp-cloud-deploy

# Verify FastMCP server structure
ls mcp_server.py  # Should exist
cat pyproject.toml  # Should have fastmcp dependency
```

**falkordb**:
```bash
cd /home/donbr/graphiti-org/falkordb-fastmcp

git status
git checkout -b fastmcp-cloud-deploy

# Verify structure
ls main.py src/falkordb_mcp/server.py
```

#### Step 1.2: Environment Variable Audit

Create `.env.example` for documentation:

**qdrant-docs** (`.env.example`):
```bash
# Required for FastMCP Cloud deployment
QDRANT_API_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

**falkordb** (`.env.example`):
```bash
# Required for FastMCP Cloud deployment
FALKORDB_HOST=your-falkordb-host
FALKORDB_PORT=6379
FALKORDB_PASSWORD=your-falkordb-password-here  # if applicable
```

**⚠️ Security**: NEVER commit `.env` with real values. Only `.env.example` with placeholders.

#### Step 1.3: Write In-Memory Tests

**qdrant-docs** (`tests/test_mcp_server.py`):
```python
"""
In-memory tests for qdrant-docs MCP server.
Run before cloud deployment to validate logic.
"""
import pytest
from fastmcp import Client
from mcp_server import mcp

@pytest.mark.asyncio
async def test_server_ping():
    """Basic connectivity test"""
    async with Client(mcp) as client:
        assert await client.ping()

@pytest.mark.asyncio
async def test_list_sources():
    """Test list_sources tool"""
    async with Client(mcp) as client:
        result = await client.call_tool("list_sources", {})
        content = result.content[0].text
        assert "Anthropic" in content
        assert "LangChain" in content
        assert "FastMCP" in content

@pytest.mark.asyncio
async def test_search_docs():
    """Test semantic search"""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_docs",
            {"query": "FastMCP deployment", "k": 3}
        )
        content = result.content[0].text
        assert "Found 3 results" in content
        assert "FastMCP" in content or "deployment" in content

@pytest.mark.asyncio
async def test_search_with_source_filter():
    """Test source filtering"""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_docs",
            {"query": "authentication", "source": "Anthropic", "k": 2}
        )
        content = result.content[0].text
        assert "Anthropic" in content

@pytest.mark.asyncio
async def test_invalid_k_parameter():
    """Test k parameter validation"""
    async with Client(mcp) as client:
        # Should clamp to max 20
        result = await client.call_tool(
            "search_docs",
            {"query": "test", "k": 100}
        )
        # Should work (clamped internally)
        assert result.content[0].text
```

**Run tests**:
```bash
cd /home/donbr/graphiti-qdrant

# Install test dependencies
uv add --dev pytest pytest-asyncio

# Run in-memory tests
uv run pytest tests/test_mcp_server.py -v
```

**Expected Output**:
```
tests/test_mcp_server.py::test_server_ping PASSED
tests/test_mcp_server.py::test_list_sources PASSED
tests/test_mcp_server.py::test_search_docs PASSED
tests/test_mcp_server.py::test_search_with_source_filter PASSED
tests/test_mcp_server.py::test_invalid_k_parameter PASSED

✅ 5 passed in 2.34s
```

**falkordb** (`tests/test_server.py`):
```python
"""In-memory tests for falkordb MCP server"""
import pytest
from fastmcp import Client
from src.falkordb_mcp.server import mcp

@pytest.mark.asyncio
async def test_server_ping():
    async with Client(mcp) as client:
        assert await client.ping()

@pytest.mark.asyncio
async def test_list_graphs():
    async with Client(mcp) as client:
        result = await client.call_tool("list_graphs", {})
        content = result.content[0].text
        assert "success" in content

# Add more tests based on your FalkorDB setup
```

### Phase 2: Local HTTP Testing

#### Step 2.1: Run Server Locally

**Terminal 1** (qdrant-docs):
```bash
cd /home/donbr/graphiti-qdrant
uv run fastmcp run mcp_server.py
```

**Terminal 1** (falkordb):
```bash
cd /home/donbr/graphiti-org/falkordb-fastmcp
uv run python main.py
```

Server should start on `http://localhost:8000/mcp/`

#### Step 2.2: Test HTTP Transport

**Terminal 2** (test script `test_http_local.py`):
```python
"""
Test MCP server via HTTP transport locally.
This validates network behavior before cloud deployment.
"""
import asyncio
from fastmcp import Client

async def test_qdrant_docs_http():
    print("🧪 Testing qdrant-docs via HTTP...")

    async with Client("http://localhost:8000/mcp/") as client:
        # Test connectivity
        print("✓ Ping:", await client.ping())

        # List tools
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools")

        # Test search
        result = await client.call_tool(
            "search_docs",
            {"query": "FastMCP authentication", "k": 2}
        )
        print("✓ Search result length:", len(result.content[0].text))
        print("Preview:", result.content[0].text[:200])

if __name__ == "__main__":
    asyncio.run(test_qdrant_docs_http())
```

**Run**:
```bash
uv run python test_http_local.py
```

**Expected Output**:
```
🧪 Testing qdrant-docs via HTTP...
✓ Ping: True
✓ Found 2 tools
✓ Search result length: 3247
Preview: Found 2 results for: 'FastMCP authentication'

================================================================================
Result 1/2
================================================================================
Title: Authentication
Source: FastMCP
URL: https://gofastmcp.com/servers/auth...
```

✅ **If this works**: Network transport is good, ready for cloud!
❌ **If this fails**: Debug locally before attempting cloud deployment.

### Phase 3: FastMCP Cloud Deployment

#### Step 3.1: Connect GitHub Repository

**Via FastMCP Cloud Dashboard**:

1. Visit https://fastmcp.cloud
2. Sign in with GitHub
3. Click "New Project"
4. **Connect Repository**:
   - For qdrant-docs: Select `graphiti-qdrant` repo
   - For falkordb: Select `falkordb-fastmcp` repo
5. **Configure Build**:
   - Entry point: `mcp_server.py` (qdrant-docs) or `main.py` (falkordb)
   - Branch: `main`
   - Auto-deploy: ✅ Enabled

#### Step 3.2: Configure Environment Variables

**In FastMCP Cloud Dashboard**:

**qdrant-docs**:
```
QDRANT_API_URL = https://1d48094c-93af-4f43-8a71-8ffd45883525.us-west-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY = <from-vault>
OPENAI_API_KEY = <from-vault>
```

**falkordb**:
```
FALKORDB_HOST = <your-host>
FALKORDB_PORT = 6379
FALKORDB_PASSWORD = <from-vault>
```

**🔒 Security Best Practice**: Use FastMCP Cloud's secret storage, never hardcode.

#### Step 3.3: Deploy

```bash
# qdrant-docs
cd /home/donbr/graphiti-qdrant
git push origin main

# falkordb
cd /home/donbr/graphiti-org/falkordb-fastmcp
git push origin main
```

**FastMCP Cloud automatically**:
1. Detects push to `main`
2. Pulls code from GitHub
3. Installs dependencies (`uv sync`)
4. Starts MCP server
5. Exposes HTTPS endpoint

**Deployment URLs**:
- qdrant-docs: `https://qdrant-docs.fastmcp.app/mcp`
- falkordb: `https://falkordb-mcp.fastmcp.app/mcp`

### Phase 4: Cloud Validation

#### Step 4.1: Test from Claude Code Desktop

```bash
# Add cloud endpoints as user-scoped servers
claude mcp add --transport http qdrant-docs-cloud --scope user \
  https://qdrant-docs.fastmcp.app/mcp

claude mcp add --transport http falkordb-cloud --scope user \
  https://falkordb-mcp.fastmcp.app/mcp

# Verify
claude mcp list | grep -E "(qdrant-docs-cloud|falkordb-cloud)"
```

**Test in Claude Code**:
```
> Search qdrant-docs-cloud for "prompt engineering"
> List all graphs in falkordb-cloud
```

#### Step 4.2: Test from Claude Code Web

1. Visit https://code.claude.com (web version)
2. Open MCP settings
3. Add HTTP servers:
   - `https://qdrant-docs.fastmcp.app/mcp`
   - `https://falkordb-mcp.fastmcp.app/mcp`
4. Test queries same as desktop

✅ **Success Criteria**: Both servers work identically on desktop and web.

---

## Testing & Validation Strategy

### Testing Pyramid

```
         🔺
        /  \
       /Cloud\         ← 5% of tests (final validation)
      /Preview\
     /----------\
    /  Local   \       ← 15% of tests (network behavior)
   /    HTTP    \
  /--------------\
 /   In-Memory   \    ← 80% of tests (fast, deterministic)
/________________ \
```

### Test Coverage Goals

| Component | Coverage | Method |
|-----------|----------|--------|
| Tool Logic | 90%+ | In-memory unit tests |
| Network Transport | 100% | Local HTTP tests |
| Authentication | 100% | Local + preview |
| Cloud Environment | 100% | Preview deployment |

### Validation Checklist

**In-Memory Tests** (Run first):
- [ ] Server starts without errors
- [ ] All tools callable
- [ ] Tool parameters validated
- [ ] Error handling works
- [ ] Response formats correct

**Local HTTP Tests** (Run second):
- [ ] HTTP server starts
- [ ] Client connects successfully
- [ ] Tools work over network
- [ ] JSON serialization correct
- [ ] Timeout handling works

**Cloud Preview Tests** (Run third):
- [ ] Deployment succeeds
- [ ] Environment variables loaded
- [ ] External service connectivity (Qdrant, FalkorDB)
- [ ] OAuth flow works (if applicable)
- [ ] Performance acceptable (< 2s response)

**Production Smoke Tests** (Run last):
- [ ] Accessible from Claude Code Desktop
- [ ] Accessible from Claude Code Web
- [ ] Accessible from Claude.ai
- [ ] Rate limits appropriate
- [ ] Monitoring enabled

---

## Deployment Checklist

### Pre-Deployment

**Code**:
- [ ] All in-memory tests passing
- [ ] Local HTTP tests passing
- [ ] No sensitive data in code
- [ ] `.env.example` documented
- [ ] `.gitignore` includes `.env`

**Configuration**:
- [ ] Environment variables documented
- [ ] Secrets stored securely (not in git)
- [ ] API rate limits understood
- [ ] Cost implications assessed

**Documentation**:
- [ ] README updated with cloud URL
- [ ] API usage examples provided
- [ ] Troubleshooting guide written

### Deployment

- [ ] GitHub repository connected
- [ ] Environment variables configured in FastMCP Cloud
- [ ] Preview deployment tested
- [ ] Production deployment successful
- [ ] URLs accessible

### Post-Deployment

- [ ] Desktop client tested
- [ ] Web client tested
- [ ] Performance benchmarked
- [ ] Monitoring configured
- [ ] Team notified
- [ ] Documentation updated

---

## Security & Authentication

### FastMCP Cloud Security Features

**Built-in**:
- ✅ HTTPS (TLS 1.3)
- ✅ DDoS protection
- ✅ Rate limiting
- ✅ GitHub OAuth support

### Authentication Options

#### Option 1: No Auth (Public Endpoints)

**Use Case**: Read-only, non-sensitive data

**Example**: qdrant-docs (documentation is public)

**Configuration**: None needed

**Pros**: Simplest, fastest
**Cons**: Anyone can use (cost/rate limits)

#### Option 2: GitHub OAuth

**Use Case**: Restrict to GitHub users/orgs

**Configuration**:
```python
# In mcp_server.py
from fastmcp import FastMCP
from fastmcp.auth import GitHubOAuthProvider

mcp = FastMCP("qdrant-docs-search")

# Enable GitHub OAuth
mcp.auth = GitHubOAuthProvider(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    allowed_orgs=["your-org"]  # Optional: restrict to org
)
```

**Pros**: Standard OAuth flow, org-level access control
**Cons**: Users must authenticate

#### Option 3: API Keys

**Use Case**: Programmatic access, service-to-service

**Configuration**:
```python
from fastmcp.auth import BearerTokenProvider

mcp.auth = BearerTokenProvider({
    "secret-key-1": "user-1",
    "secret-key-2": "user-2",
})
```

**Pros**: Simple for automation
**Cons**: Manual key management

### Recommended Authentication Strategy

| Server | Recommendation | Rationale |
|--------|---------------|-----------|
| **qdrant-docs** | No Auth (public) | Documentation is public, no sensitive data |
| **falkordb** | GitHub OAuth | Graph data may be sensitive, need access control |

**Rationale**:
- **qdrant-docs**: Public documentation search is low-risk, maximize accessibility
- **falkordb**: Database queries could expose sensitive graph data, restrict access

---

## Monitoring & Maintenance

### FastMCP Cloud Monitoring

**Built-in Metrics**:
- Request count
- Response time (p50, p95, p99)
- Error rate
- Active connections

**Access**: FastMCP Cloud dashboard → Project → Metrics

### Key Metrics to Watch

**qdrant-docs**:
- OpenAI API costs (increases with usage)
- Qdrant query latency
- Cache hit rate (if caching added)

**falkordb**:
- Query execution time
- FalkorDB connection pool saturation
- Long-running query count

### Alerting Strategy

**Critical Alerts** (immediate action):
- Error rate > 5%
- Response time p95 > 10s
- Service down > 1 minute

**Warning Alerts** (investigate):
- OpenAI costs > $50/day (qdrant-docs)
- Query time p95 > 5s (falkordb)
- Rate limit approaching

### Maintenance Schedule

**Weekly**:
- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Monitor API costs

**Monthly**:
- [ ] Update dependencies (`uv sync --upgrade`)
- [ ] Review and optimize slow queries
- [ ] Audit access logs (if auth enabled)

**Quarterly**:
- [ ] Load testing
- [ ] Security review
- [ ] Cost optimization review

---

## Rollback & Recovery

### Rollback Procedure

**If cloud deployment fails or has issues**:

#### Step 1: Immediate Mitigation

```bash
# Remove cloud endpoint from Claude Code
claude mcp remove qdrant-docs-cloud --scope user
claude mcp remove falkordb-cloud --scope user

# Fall back to local servers (already configured)
# Users revert to local-only access
```

#### Step 2: Investigate

```bash
# Check FastMCP Cloud logs
# Dashboard → Project → Logs

# Common issues:
# - Missing environment variables
# - Service connectivity (Qdrant, FalkorDB)
# - Dependency conflicts
```

#### Step 3: Fix & Redeploy

```bash
# Fix issue locally first
cd /home/donbr/graphiti-qdrant

# Test fix with in-memory tests
uv run pytest tests/

# Test fix with local HTTP
uv run fastmcp run mcp_server.py
# (test in another terminal)

# Commit fix
git add .
git commit -m "fix: resolve cloud deployment issue"
git push origin main

# FastMCP Cloud auto-redeploys
```

#### Step 4: Validate

```bash
# Re-add cloud endpoint
claude mcp add --transport http qdrant-docs-cloud --scope user \
  https://qdrant-docs.fastmcp.app/mcp

# Test
# > Search qdrant-docs-cloud for "test"
```

### Disaster Recovery

**Worst Case**: FastMCP Cloud service outage

**Mitigation**:
1. Local servers remain functional ✅
2. Users unaffected (fall back to local)
3. No data loss (Qdrant and FalkorDB external)

**Recovery Time Objective (RTO)**: < 1 hour
**Recovery Point Objective (RPO)**: 0 (no data stored in MCP servers)

---

## Success Metrics

### Phase 1 (Local Validation)

- [ ] 100% in-memory tests passing
- [ ] 100% local HTTP tests passing
- [ ] < 500ms response time locally

### Phase 2 (Cloud Deployment)

- [ ] Successful deployment to FastMCP Cloud
- [ ] < 2s response time from cloud
- [ ] Accessible from 3+ platforms (desktop, web, mobile)

### Phase 3 (Production)

- [ ] > 95% uptime
- [ ] < 5% error rate
- [ ] < $100/month operating costs
- [ ] Positive user feedback

---

## Next Steps

### Immediate (Week 1)

1. **Set up testing infrastructure**:
   - [ ] Write in-memory tests for qdrant-docs
   - [ ] Write in-memory tests for falkordb
   - [ ] Run tests locally, achieve 100% pass rate

2. **Local HTTP validation**:
   - [ ] Test qdrant-docs via `localhost:8000`
   - [ ] Test falkordb via `localhost:8000`
   - [ ] Measure performance baselines

### Short-term (Week 2-3)

3. **Deploy qdrant-docs to cloud** (lower risk):
   - [ ] Connect GitHub repo to FastMCP Cloud
   - [ ] Configure environment variables
   - [ ] Deploy and validate
   - [ ] Test from multiple platforms

4. **Deploy falkordb to cloud** (higher complexity):
   - [ ] Ensure FalkorDB network accessibility
   - [ ] Configure read-only access
   - [ ] Deploy with GitHub OAuth
   - [ ] Validate security controls

### Long-term (Month 2+)

5. **Optimize and scale**:
   - [ ] Add caching to qdrant-docs (reduce OpenAI costs)
   - [ ] Implement query analytics
   - [ ] Set up cost alerts
   - [ ] Gather user feedback

6. **Expand MCP portfolio**:
   - [ ] Identify additional local servers to promote
   - [ ] Create reusable deployment templates
   - [ ] Document best practices

---

## Conclusion

### The Promotion Pyramid

```
                 🌐
                /  \
               /Cloud\          ← Multi-platform access
              /FastMCP\         ← HTTPS endpoints
             /---------\        ← Global availability
            /  Preview  \       ← Staging validation
           /  Deployment \
          /---------------\
         /  Local HTTP    \    ← Network testing
        /    Testing       \   ← Auth validation
       /-------------------\
      /   In-Memory Tests   \  ← Logic validation
     /     (Human-in-Loop)   \ ← Fast iteration
    /_________________________\
```

### Key Takeaways

1. **Testing First**: FastMCP's in-memory testing keeps humans in the loop and catches bugs before deployment
2. **Gradual Promotion**: Local → HTTP → Preview → Production ensures safety
3. **Platform Multiplication**: Cloud deployment unlocks 3-4x more platforms
4. **Low Risk**: Can always fall back to local servers if cloud issues arise

### Why This Strategy Works

✅ **Human-in-the-Loop**: Comprehensive testing before deployment
✅ **Zero Downtime**: Local servers remain available during cloud transition
✅ **Incremental Risk**: Test with qdrant-docs (public data) before falkordb (sensitive data)
✅ **Reversible**: Can roll back at any stage

### Final Recommendation

**Start with qdrant-docs**:
- Lower risk (public documentation)
- No auth complexity
- Immediate value (accessible from web clients)
- Proves the workflow for falkordb

**Once confident, promote falkordb**:
- Add GitHub OAuth
- Validate security controls
- Monitor query performance
- Expand access gradually

---

## Appendix A: Quick Reference Commands

### Local Testing

```bash
# In-memory tests (fastest)
uv run pytest tests/test_mcp_server.py -v

# Local HTTP server
uv run fastmcp run mcp_server.py

# Test HTTP locally
uv run python test_http_local.py
```

### Cloud Deployment

```bash
# Deploy to cloud (auto-triggers on push)
git push origin main

# Add cloud endpoint to Claude Code
claude mcp add --transport http qdrant-docs-cloud --scope user \
  https://qdrant-docs.fastmcp.app/mcp

# Remove cloud endpoint (rollback)
claude mcp remove qdrant-docs-cloud --scope user
```

### Monitoring

```bash
# Check deployment status
# Visit: https://fastmcp.cloud/projects/qdrant-docs

# View logs
# Dashboard → Logs → Select time range

# Check costs
# Dashboard → Usage → API costs
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-30
**Next Review**: After qdrant-docs cloud deployment
**Status**: Ready for implementation

---

## References

- [FastMCP Cloud Documentation](https://gofastmcp.com/deployment/fastmcp-cloud)
- [FastMCP Testing Guide](https://gofastmcp.com/patterns/testing)
- [FastMCP Authentication](https://gofastmcp.com/servers/auth/authentication)
- [qdrant-docs source](file:///home/donbr/graphiti-qdrant/mcp_server.py)
- [falkordb source](file:///home/donbr/graphiti-org/falkordb-fastmcp/src/falkordb_mcp/server.py)
