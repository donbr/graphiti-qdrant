# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python project for downloading, processing, and loading documentation from various sources (llms.txt and llms-full.txt files) into Qdrant vector database using LangChain. The project focuses on preparing technical documentation from sources like Cursor, LangChain, Anthropic, PydanticAI, and others for vector search.

## Environment Setup

This project uses `uv` for dependency management and Python 3.11+.

### Initial Setup
```bash
# Install dependencies
uv sync

# Copy environment template and configure
cp .env.example .env
# Edit .env with your QDRANT_API_KEY and QDRANT_API_URL
```

### Required Environment Variables
- `QDRANT_API_KEY`: Your Qdrant API key
- `QDRANT_API_URL`: Your Qdrant instance URL (e.g., https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333)

## Common Commands

### Running Scripts
```bash
# Download llms.txt and llms-full.txt from all configured sources
uv run scripts/download_llms_raw.py

# Analyze structure of downloaded documentation
uv run scripts/analyze_llms_structure.py

# Split llms-full.txt files into individual pages/documents
uv run scripts/split_llms_pages.py

# Run main application
uv run main.py
```

## Data Pipeline Architecture

### Directory Structure
```
data/
├── raw/                    # Downloaded llms.txt and llms-full.txt files
│   ├── {Source}/          # One directory per source (Cursor, LangChain, etc.)
│   │   ├── llms.txt
│   │   ├── llms-full.txt
│   └── manifest.json      # Download metadata and status
├── interim/               # Intermediate processing results
│   └── pages/            # Individual pages split from llms-full.txt
│       ├── {Source}/     # One directory per source
│       │   ├── 0000_Page_Title.json
│       │   ├── manifest.json
│       └── manifest.json  # Overall processing metadata
└── processed/            # Final processed data ready for vector DB
```

### Processing Pipeline

1. **Download Stage** (`download_llms_raw.py`)
   - Async download of llms.txt and llms-full.txt from 11 documentation sources
   - Sources: Cursor, PydanticAI, McpProtocol, FastMCP, LangChain, Prefect, Anthropic, OpenAI, Vue, Supabase, Zep
   - Outputs to `data/raw/{Source}/`
   - Generates `data/raw/manifest.json` with download status and metrics

2. **Analysis Stage** (`analyze_llms_structure.py`)
   - Analyzes top 4 largest sources (Cursor, LangChain, Anthropic, Prefect)
   - Examines document delimiters, header structure, JSX components
   - Provides splitting strategy recommendations
   - Used for understanding documentation structure before processing

3. **Splitting Stage** (`split_llms_pages.py`)
   - Two splitting strategies based on source format:
     - **URL Pattern**: Sources with `# Title\nSource: URL` format (LangChain, Anthropic, Prefect, FastMCP, McpProtocol)
     - **Header-Only Pattern**: Sources with just `# Title` (PydanticAI, Zep)
   - Handles code block neutralization to prevent false header matches
   - Outputs individual JSON files per page to `data/interim/pages/{Source}/`
   - Each page includes: title, source_url (if available), content, content_length

### Document Splitting Patterns

**URL Pattern** (most sources):
```
# Page Title
Source: https://example.com/page

[page content]
```

**Header-Only Pattern** (PydanticAI, Zep):
```
# Page Title

[page content]
```

The header-only pattern uses code block neutralization: converts `# ` inside code blocks to `### ` to prevent Python comments from being treated as page delimiters.

## Key Dependencies

- **httpx**: Async HTTP client for downloading documentation
- **langchain**: Framework for LLM applications
- **langchain-community**: Community integrations
- **langchain-qdrant**: Qdrant vector store integration
- **datasets**: Hugging Face datasets library
- **ipywidgets**: Interactive widgets (for notebooks)

## Development Notes

- Never commit `.env` files with real API keys - only commit `.env.example` with placeholders
- The `data/` directory structure supports a clear ETL pipeline: raw → interim → processed
- Async operations are used for efficient parallel downloads across multiple sources
- All scripts generate manifest.json files for tracking processing metadata and debugging
