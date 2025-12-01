#!/usr/bin/env python3
"""
Claude Code .claude.json Cleanup Script
Safely removes project configurations for non-existent directories

Usage:
    # Dry run (analysis only)
    python3 cleanup_claude_json.py

    # Execute cleanup
    python3 cleanup_claude_json.py --execute
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_config(config_path):
    """Create timestamped backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{config_path}.backup.{timestamp}"
    shutil.copy2(config_path, backup_path)

    # Also create a safe backup in backups directory
    backup_dir = Path.home() / "backups" / "claude-code"
    backup_dir.mkdir(parents=True, exist_ok=True)
    safe_backup = backup_dir / f"claude.json.backup.{timestamp}"
    shutil.copy2(config_path, safe_backup)

    print(f"✅ Backup created: {backup_path}")
    print(f"✅ Safe backup: {safe_backup}")
    return backup_path

def load_config(config_path):
    """Load .claude.json"""
    with open(config_path, 'r') as f:
        return json.load(f)

def analyze_projects(data):
    """Analyze project configurations"""
    projects = data.get('projects', {})

    analysis = {
        'total': len(projects),
        'missing_dirs': [],
        'existing_dirs': [],
        'empty_configs': [],
        'large_configs': [],
        'mcp_servers': []
    }

    # Analyze each project
    for path, config in projects.items():
        # Check if directory exists
        if not os.path.isdir(path):
            analysis['missing_dirs'].append(path)
        else:
            analysis['existing_dirs'].append(path)

        # Check config size
        size = len(json.dumps(config))
        if size < 500:
            analysis['empty_configs'].append((path, size))
        elif size > 2000:
            analysis['large_configs'].append((path, size))

        # Check for MCP servers
        if config.get('mcpServers'):
            server_count = len(config['mcpServers'])
            if server_count > 0:
                analysis['mcp_servers'].append((path, server_count, list(config['mcpServers'].keys())))

    return analysis

def print_analysis(analysis):
    """Print analysis results"""
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    print(f"\n📊 Overall Statistics:")
    print(f"   Total projects: {analysis['total']}")
    print(f"   Existing directories: {len(analysis['existing_dirs'])}")
    print(f"   Missing directories: {len(analysis['missing_dirs'])}")
    print(f"   Empty configs (< 500 bytes): {len(analysis['empty_configs'])}")
    print(f"   Large configs (> 2KB): {len(analysis['large_configs'])}")
    print(f"   Projects with MCP servers: {len(analysis['mcp_servers'])}")

    if analysis['missing_dirs']:
        print(f"\n❌ Missing Directories ({len(analysis['missing_dirs'])} total):")
        for i, path in enumerate(analysis['missing_dirs'][:20], 1):
            print(f"   {i}. {path}")
        if len(analysis['missing_dirs']) > 20:
            print(f"   ... and {len(analysis['missing_dirs']) - 20} more")

    if analysis['large_configs']:
        print(f"\n📦 Largest Configs (Top 10):")
        sorted_large = sorted(analysis['large_configs'], key=lambda x: x[1], reverse=True)
        for path, size in sorted_large[:10]:
            print(f"   {size:,} bytes - {path}")

    if analysis['mcp_servers']:
        print(f"\n🔧 Projects with MCP Servers (Top 10):")
        for path, count, servers in analysis['mcp_servers'][:10]:
            print(f"   {path}")
            print(f"      {count} servers: {', '.join(servers[:3])}{'...' if len(servers) > 3 else ''}")

def cleanup_missing_directories(config_path, dry_run=True):
    """Remove projects for missing directories"""

    print("\n" + "="*60)
    print("CLEANUP: MISSING DIRECTORIES")
    print("="*60)

    # Load config
    data = load_config(config_path)
    original_projects = data.get('projects', {})
    original_count = len(original_projects)

    # Identify missing directories
    to_remove = []
    for path in original_projects.keys():
        if not os.path.isdir(path):
            to_remove.append(path)

    if not to_remove:
        print("\n✅ No missing directories found. Config is clean!")
        return

    print(f"\nFound {len(to_remove)} projects with missing directories")

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("Run with --execute to apply changes\n")

        print("Would remove:")
        for i, path in enumerate(to_remove[:20], 1):
            print(f"   {i}. {path}")
        if len(to_remove) > 20:
            print(f"   ... and {len(to_remove) - 20} more")

        # Calculate size reduction
        removed_size = sum(len(json.dumps(original_projects[p])) for p in to_remove)
        remaining_size = sum(len(json.dumps(v)) for k, v in original_projects.items() if k not in to_remove)
        total_size = removed_size + remaining_size

        print(f"\nEstimated impact:")
        print(f"   Projects before: {original_count}")
        print(f"   Projects after: {original_count - len(to_remove)}")
        print(f"   Size reduction: ~{removed_size:,} bytes ({removed_size/total_size*100:.1f}%)")

    else:
        # EXECUTE MODE
        print("\n🔄 EXECUTING CLEANUP...\n")

        # Remove missing directories
        removed = {}
        for path in to_remove:
            removed[path] = original_projects.pop(path)

        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Cleanup complete!")
        print(f"   Removed: {len(removed)} projects")
        print(f"   Remaining: {len(original_projects)} projects")

        # Show what was removed
        print(f"\nRemoved projects:")
        for i, path in enumerate(list(removed.keys())[:15], 1):
            print(f"   {i}. {path}")
        if len(removed) > 15:
            print(f"   ... and {len(removed) - 15} more")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Cleanup Claude Code .claude.json file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (safe - no changes)
    python3 cleanup_claude_json.py

    # Execute cleanup
    python3 cleanup_claude_json.py --execute

    # Custom config path
    python3 cleanup_claude_json.py --config ~/custom/.claude.json --execute
        """
    )
    parser.add_argument('--config',
                       default=os.path.expanduser('~/.claude.json'),
                       help='Path to .claude.json (default: ~/.claude.json)')
    parser.add_argument('--execute',
                       action='store_true',
                       help='Execute cleanup (default is dry-run)')

    args = parser.parse_args()

    config_path = args.config
    dry_run = not args.execute

    # Header
    print("\n" + "="*60)
    print("CLAUDE CODE .claude.json CLEANUP TOOL")
    print("="*60)
    print(f"\nConfig file: {config_path}")
    print(f"Mode: {'🔍 DRY RUN (analysis only)' if dry_run else '⚠️  EXECUTE (will modify file)'}")

    # Check if file exists
    if not os.path.isfile(config_path):
        print(f"\n❌ ERROR: Config file not found: {config_path}")
        return 1

    # Get file size
    file_size = os.path.getsize(config_path)
    print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # Create backup (even for dry run)
    backup_path = backup_config(config_path)

    # Load and analyze
    data = load_config(config_path)
    analysis = analyze_projects(data)

    # Print analysis
    print_analysis(analysis)

    # Cleanup
    cleanup_missing_directories(config_path, dry_run=dry_run)

    # Final summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nBackup location: {backup_path}")

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("To execute cleanup, run:")
        print(f"   python3 {__file__} --execute")
    else:
        print("\n✅ Cleanup completed successfully!")
        print("Verify Claude Code still works, then you can remove old backups")

        # Show new file size
        new_size = os.path.getsize(config_path)
        reduction = file_size - new_size
        print(f"\nFile size change:")
        print(f"   Before: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"   After:  {new_size:,} bytes ({new_size/1024:.1f} KB)")
        print(f"   Saved:  {reduction:,} bytes ({reduction/file_size*100:.1f}%)")

    print()
    return 0

if __name__ == "__main__":
    exit(main())
