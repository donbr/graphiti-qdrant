#!/usr/bin/env python3
"""
Analyze llms-full.txt structure for developing splitting strategy.

Usage:
    uv run scripts-temp/analyze_llms_structure.py

Analyzes the top 4 largest sources to understand:
- Document delimiter patterns
- Header structure (##, ###)
- Document count and sizes
- JSX component usage
"""

import re
from collections import Counter
from pathlib import Path

# Raw data directory
RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw'

# Top 4 sources by size (based on manifest)
TOP_SOURCES = ['Cursor', 'LangChain', 'Anthropic', 'Prefect']


def split_into_documents(content: str) -> list[dict]:
    """Split llms-full.txt content into individual documents.

    Pattern: # Title followed by Source: URL

    Returns:
        List of dicts with title, source_url, content, and size
    """
    # Pattern: # Title at start of line, followed by Source: URL
    pattern = r'^# (.+)\nSource: (https?://[^\n]+)\n'

    documents = []
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        doc_content = content[start:end].strip()

        documents.append({
            'title': match.group(1),
            'source_url': match.group(2),
            'content': doc_content,
            'size_chars': len(doc_content),
        })

    return documents


def analyze_headers(content: str) -> dict:
    """Analyze markdown header structure in content.

    Returns:
        Dict with counts for each header level
    """
    h1_count = len(re.findall(r'^# .+', content, re.MULTILINE))
    h2_count = len(re.findall(r'^## .+', content, re.MULTILINE))
    h3_count = len(re.findall(r'^### .+', content, re.MULTILINE))
    h4_count = len(re.findall(r'^#### .+', content, re.MULTILINE))

    return {
        'h1': h1_count,
        'h2': h2_count,
        'h3': h3_count,
        'h4': h4_count,
    }


def analyze_jsx_components(content: str) -> Counter:
    """Find JSX/MDX components used in content.

    Returns:
        Counter of component names
    """
    # Match <ComponentName or </ComponentName
    pattern = r'</?([A-Z][a-zA-Z]+)'
    matches = re.findall(pattern, content)
    return Counter(matches)


def analyze_source(source_name: str) -> dict:
    """Analyze a single source's llms-full.txt file.

    Returns:
        Dict with analysis results
    """
    llms_full_path = RAW_DIR / source_name / 'llms-full.txt'
    llms_path = RAW_DIR / source_name / 'llms.txt'

    if not llms_full_path.exists():
        return {'error': f'File not found: {llms_full_path}'}

    content = llms_full_path.read_text(encoding='utf-8')

    # Split into documents
    documents = split_into_documents(content)

    # Calculate document sizes
    doc_sizes = [d['size_chars'] for d in documents]
    avg_size = sum(doc_sizes) / len(doc_sizes) if doc_sizes else 0
    max_size = max(doc_sizes) if doc_sizes else 0
    min_size = min(doc_sizes) if doc_sizes else 0

    # Analyze headers in full content
    headers = analyze_headers(content)

    # Analyze JSX components
    jsx_components = analyze_jsx_components(content)

    # Check llms.txt for comparison
    llms_entries = 0
    if llms_path.exists():
        llms_content = llms_path.read_text(encoding='utf-8')
        # Count entries (lines starting with "- [")
        llms_entries = len(re.findall(r'^- \[', llms_content, re.MULTILINE))

    return {
        'file_size_kb': len(content) / 1024,
        'document_count': len(documents),
        'llms_txt_entries': llms_entries,
        'doc_sizes': {
            'avg_chars': avg_size,
            'max_chars': max_size,
            'min_chars': min_size,
            'total_chars': sum(doc_sizes),
        },
        'headers': headers,
        'top_jsx_components': jsx_components.most_common(10),
        'sample_titles': [d['title'] for d in documents[:5]],
    }


def print_analysis(source_name: str, analysis: dict):
    """Pretty print analysis results."""
    print(f'\n{"=" * 60}')
    print(f'Source: {source_name}')
    print(f'{"=" * 60}')

    if 'error' in analysis:
        print(f'  Error: {analysis["error"]}')
        return

    print(f'\nFile Size: {analysis["file_size_kb"]:.1f} KB')
    print(f'Document Count: {analysis["document_count"]}')
    print(f'llms.txt Entries: {analysis["llms_txt_entries"]}')

    print(f'\nDocument Sizes:')
    sizes = analysis['doc_sizes']
    print(f'  Average: {sizes["avg_chars"]:.0f} chars ({sizes["avg_chars"]/1000:.1f} KB)')
    print(f'  Max: {sizes["max_chars"]:,} chars ({sizes["max_chars"]/1000:.1f} KB)')
    print(f'  Min: {sizes["min_chars"]:,} chars')

    print(f'\nHeader Counts:')
    headers = analysis['headers']
    print(f'  # (h1): {headers["h1"]} (document delimiters)')
    print(f'  ## (h2): {headers["h2"]}')
    print(f'  ### (h3): {headers["h3"]}')
    print(f'  #### (h4): {headers["h4"]}')

    print(f'\nTop JSX Components:')
    for component, count in analysis['top_jsx_components']:
        print(f'  <{component}>: {count}')

    print(f'\nSample Titles:')
    for title in analysis['sample_titles']:
        print(f'  - {title[:60]}{"..." if len(title) > 60 else ""}')


def main():
    """Analyze top 4 sources for splitting strategy."""
    print('Analyzing llms-full.txt structure for top 4 sources')
    print(f'Raw directory: {RAW_DIR}')

    all_analyses = {}

    for source in TOP_SOURCES:
        analysis = analyze_source(source)
        all_analyses[source] = analysis
        print_analysis(source, analysis)

    # Summary recommendations
    print(f'\n{"=" * 60}')
    print('SPLITTING STRATEGY RECOMMENDATIONS')
    print(f'{"=" * 60}')

    print('\n1. PRIMARY SPLIT: Document Delimiter')
    print('   Pattern: ^# (.+)\\nSource: (https?://[^\\n]+)\\n')
    print('   Use regex to split llms-full.txt into individual documents')

    print('\n2. SECONDARY SPLIT: Markdown Headers')
    print('   For documents exceeding chunk size, use MarkdownHeaderTextSplitter')
    print('   Headers to split on: ##, ###')

    # Calculate optimal chunk size based on document analysis
    all_avg_sizes = [
        a['doc_sizes']['avg_chars']
        for a in all_analyses.values()
        if 'doc_sizes' in a
    ]
    overall_avg = sum(all_avg_sizes) / len(all_avg_sizes) if all_avg_sizes else 0

    print(f'\n3. CHUNK SIZE RECOMMENDATIONS')
    print(f'   Average document size: {overall_avg:.0f} chars ({overall_avg/1000:.1f} KB)')
    print('   Suggested chunk_size: 4000-8000 chars (fits most documents)')
    print('   Suggested chunk_overlap: 200-400 chars')

    print('\n4. METADATA TO PRESERVE')
    print('   - source (source name: Cursor, LangChain, etc.)')
    print('   - title (document title from # header)')
    print('   - source_url (URL from Source: line)')
    print('   - section (## header if split further)')
    print('   - subsection (### header if present)')


if __name__ == '__main__':
    main()
