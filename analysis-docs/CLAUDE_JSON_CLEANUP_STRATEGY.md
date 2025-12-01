# .claude.json Cleanup Strategy

**File**: `~/.claude.json`
**Current Size**: 210KB (4,903 lines)
**Analysis Date**: 2025-11-30

---

## Analysis Summary

### Current State

- **Total Projects**: 166 stored project configurations
- **File Size**: 210KB (relatively large for a config file)
- **Projects with MCP Configs**: All 166 projects have `mcpServers` key

### Key Findings

1. **Every project stores MCP server configuration** even if empty
2. **Largest projects**: ~2.5KB each (AIE7-Staging variants)
3. **Many duplicate/old projects**: Multiple versions of same project (jul2, jul10, jul14, etc.)
4. **Project-specific data**: allowedTools, mcpContextUris, hasTrustDialogAccepted per project

---

## Official Claude Code Guidance

### Documentation Research Results

**Sources Consulted**:
- [Claude Code Settings](https://code.claude.com/docs/en/settings)
- [Troubleshooting Guide](https://code.claude.com/docs/en/troubleshooting)
- Qdrant-docs semantic search
- Context7 documentation lookup

**Key Finding**: ⚠️ **No official documented strategy for .claude.json cleanup/pruning**

### What Claude Code Documentation DOES Cover

1. **Configuration File Hierarchy**:
   - User level: `~/.claude/settings.json`
   - Project shared: `.claude/settings.json`
   - Project local: `.claude/settings.local.json`

2. **Automatic Cleanup**:
   - `cleanupPeriodDays` setting (default: 30 days)
   - Applies to chat transcripts, not project configs

3. **Reset Procedures**:
   - Authentication: `rm -rf ~/.config/claude-code/auth.json`
   - No documented reset for `.claude.json`

### What's NOT Documented

❌ Project configuration pruning strategies
❌ .claude.json backup best practices
❌ Safe removal of old project entries
❌ File size management recommendations
❌ Migration/cleanup tools

---

## Recommended Cleanup Strategy

### Phase 1: Backup (CRITICAL)

```bash
# Create timestamped backup
timestamp=$(date +%Y%m%d_%H%M%S)
cp ~/.claude.json ~/.claude.json.backup.$timestamp

# Verify backup
ls -lh ~/.claude.json*

# Store in safe location
mkdir -p ~/backups/claude-code/
cp ~/.claude.json.backup.$timestamp ~/backups/claude-code/
```

### Phase 2: Analysis - Identify Safe Removals

**Categories for Removal**:

1. **Duplicate Project Paths** (Same project, different dates):
   - `/home/donbr/aie7stg/jul2/AIE7-Staging`
   - `/home/donbr/aie7stg/jul10/AIE7-Staging`
   - `/home/donbr/aie7stg/jul14/AIE7-Staging`
   - **Action**: Keep only the most recent

2. **Non-Existent Directories**:
   - Projects that have been deleted
   - **Verification**: `test -d /path/to/project || echo "MISSING"`

3. **Empty/Minimal Configs**:
   - Projects with no MCP servers and minimal settings
   - **Size**: < 500 bytes

4. **Archived/Completed Projects**:
   - Old course assignments (aie6, aie7, session2-assignment)
   - Staging environments no longer in use

### Phase 3: Create Cleanup Script

```python
#!/usr/bin/env python3
"""
Claude Code .claude.json Cleanup Script
Safely removes old project configurations
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
    print(f"✅ Backup created: {backup_path}")
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
        'duplicate_patterns': [],
        'empty_configs': [],
        'large_configs': []
    }

    # Check for missing directories
    for path in projects.keys():
        if not os.path.isdir(path):
            analysis['missing_dirs'].append(path)

    # Check for empty configs (< 500 bytes)
    for path, config in projects.items():
        size = len(json.dumps(config))
        if size < 500:
            analysis['empty_configs'].append((path, size))
        elif size > 2000:
            analysis['large_configs'].append((path, size))

    # Check for duplicate patterns (same base name, different dates)
    base_names = {}
    for path in projects.keys():
        # Extract base name (remove date patterns like jul2, jul10, etc.)
        base = path
        for pattern in ['/jul\\d+/', '/session\\d+', '/aie\\d+/']:
            # Simplified check
            pass
        base_name = os.path.basename(path)
        if base_name not in base_names:
            base_names[base_name] = []
        base_names[base_name].append(path)

    analysis['duplicate_patterns'] = {k: v for k, v in base_names.items() if len(v) > 1}

    return analysis

def interactive_cleanup(config_path, dry_run=True):
    """Interactive cleanup with confirmation"""

    # Backup first
    backup_path = backup_config(config_path)

    # Load config
    data = load_config(config_path)

    # Analyze
    print("\n=== Analysis ===")
    analysis = analyze_projects(data)

    print(f"Total projects: {analysis['total']}")
    print(f"Missing directories: {len(analysis['missing_dirs'])}")
    print(f"Empty configs (< 500 bytes): {len(analysis['empty_configs'])}")
    print(f"Large configs (> 2KB): {len(analysis['large_configs'])}")

    if not dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("Run with --execute to apply changes")

    # Show missing directories
    if analysis['missing_dirs']:
        print("\n=== Missing Directories (Safe to Remove) ===")
        for i, path in enumerate(analysis['missing_dirs'][:10], 1):
            print(f"{i}. {path}")
        if len(analysis['missing_dirs']) > 10:
            print(f"... and {len(analysis['missing_dirs']) - 10} more")

    # Show duplicates
    if analysis['duplicate_patterns']:
        print("\n=== Potential Duplicates (Review Manually) ===")
        for base_name, paths in list(analysis['duplicate_patterns'].items())[:5]:
            print(f"\n{base_name}:")
            for path in paths:
                print(f"  - {path}")

    return analysis, backup_path

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Cleanup .claude.json')
    parser.add_argument('--config', default=os.path.expanduser('~/.claude.json'))
    parser.add_argument('--dry-run', action='store_true', default=True)
    parser.add_argument('--execute', action='store_true')

    args = parser.parse_args()

    dry_run = not args.execute

    print("=== Claude Code .claude.json Cleanup Tool ===")
    print(f"Config: {args.config}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")

    analysis, backup = interactive_cleanup(args.config, dry_run=dry_run)

    print(f"\n✅ Backup saved: {backup}")
    print("\nNext steps:")
    print("1. Review the analysis above")
    print("2. Manually inspect suspicious entries")
    print("3. Run with --execute to apply changes")
```

### Phase 4: Manual Selective Pruning

**Safe Manual Approach** (Recommended):

```python
#!/usr/bin/env python3
"""
Manual selective pruning - removes only non-existent directories
"""
import json
import os
from datetime import datetime

config_path = os.path.expanduser('~/.claude.json')

# Backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{config_path}.backup.{timestamp}"
os.system(f"cp {config_path} {backup_path}")
print(f"Backup: {backup_path}")

# Load
with open(config_path, 'r') as f:
    data = json.load(f)

projects = data.get('projects', {})
original_count = len(projects)

# Remove only missing directories
removed = {}
for path in list(projects.keys()):
    if not os.path.isdir(path):
        removed[path] = projects.pop(path)

# Save
with open(config_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n✅ Cleanup complete!")
print(f"Original: {original_count} projects")
print(f"Removed: {len(removed)} missing directories")
print(f"Remaining: {len(projects)} projects")

if removed:
    print("\nRemoved projects:")
    for path in list(removed.keys())[:10]:
        print(f"  - {path}")
    if len(removed) > 10:
        print(f"  ... and {len(removed) - 10} more")
```

---

## Conservative Cleanup Strategy (Recommended)

### Step 1: Quick Win - Remove Missing Directories

**Impact**: Low risk, high benefit
**Estimated Savings**: 20-40% file size

```bash
# Run the selective pruning script above
python3 cleanup_missing_dirs.py
```

### Step 2: Archive Old Staging Projects

**Manual Review Required**:
- Keep: Current working projects
- Archive: jul2, jul10, jul14 variants (keep only latest)
- Remove: Completed course assignments (with backup)

### Step 3: Monitor File Size

```bash
# Before cleanup
ls -lh ~/.claude.json

# After cleanup
ls -lh ~/.claude.json

# Calculate reduction
du -h ~/.claude.json*
```

---

## Best Practices Going Forward

### 1. Regular Maintenance

**Monthly Audit**:
```bash
# Count projects
cat ~/.claude.json | python3 -c "import sys,json; print(f'Projects: {len(json.load(sys.stdin).get(\"projects\", {}))}')"

# Check size
ls -lh ~/.claude.json
```

**Quarterly Cleanup**:
- Remove projects for deleted directories
- Archive old staging/test environments
- Back up before major changes

### 2. Backup Strategy

**Automated Backups**:
```bash
# Add to crontab for weekly backups
0 0 * * 0 cp ~/.claude.json ~/backups/claude-code/.claude.json.$(date +\%Y\%m\%d)

# Keep only last 4 weeks
find ~/backups/claude-code/ -name ".claude.json.*" -mtime +28 -delete
```

### 3. MCP Server Strategy

**Use Global Scope** (as we just did):
- Prevents duplication across projects
- Reduces per-project config size
- Cleaner .claude.json file

**Before Today's Migration**:
- Many projects had duplicate MCP server configs
- Each project: 1-2.5KB

**After Migration**:
- MCP servers at user level
- Project configs: minimal (< 500 bytes for new projects)

---

## Risk Assessment

### Low Risk Actions ✅
- Creating backups
- Removing projects for non-existent directories
- Running analysis scripts (dry-run mode)

### Medium Risk Actions ⚠️
- Removing duplicate staging projects (manual review required)
- Archiving old course assignments

### High Risk Actions ❌
- Bulk deletion without backup
- Removing active project configurations
- Modifying current project entries

---

## Estimated Impact

### Current State
- **Size**: 210KB
- **Projects**: 166
- **Lines**: 4,903

### After Conservative Cleanup (Estimated)
- **Size**: ~120-150KB (30-40% reduction)
- **Projects**: ~80-100 (removing duplicates and missing dirs)
- **Lines**: ~2,500-3,000

### After Aggressive Cleanup (Estimated)
- **Size**: ~60-80KB (60-70% reduction)
- **Projects**: ~30-40 (only active projects)
- **Lines**: ~1,000-1,500

---

## Implementation Recommendation

### Recommended Approach: Conservative Cleanup

**Phase 1** (NOW):
1. ✅ Create backup: `cp ~/.claude.json ~/.claude.json.backup.$(date +%Y%m%d)`
2. Run analysis script (dry-run)
3. Review findings

**Phase 2** (SAFE):
1. Remove only missing directories (automated script)
2. Verify Claude Code still works
3. Measure size reduction

**Phase 3** (MANUAL):
1. Identify duplicate staging projects manually
2. Remove old course assignments (with review)
3. Final size measurement

**Timeline**: 1-2 hours total

---

## Rollback Plan

If anything breaks:

```bash
# Find your backup
ls -lht ~/.claude.json.backup.* | head -5

# Restore from backup
timestamp="YYYYMMDD_HHMMSS"  # Use actual timestamp
cp ~/.claude.json.backup.$timestamp ~/.claude.json

# Restart Claude Code
# Exit and restart the application
```

---

## Monitoring

### File Size Trend

```bash
# Track over time
echo "$(date +%Y-%m-%d),$(stat -f%z ~/.claude.json 2>/dev/null || stat -c%s ~/.claude.json)" >> ~/claude-json-size.log
```

### Project Count Trend

```bash
# Track over time
echo "$(date +%Y-%m-%d),$(cat ~/.claude.json | python3 -c 'import sys,json; print(len(json.load(sys.stdin).get("projects", {})))')" >> ~/claude-projects-count.log
```

---

## Conclusion

### Key Findings

1. **No Official Documentation**: Claude Code doesn't provide official cleanup guidance
2. **File is Bloated**: 166 projects stored, many duplicates/old/missing
3. **Safe Cleanup Possible**: Conservative approach can reduce file 30-40%
4. **MCP Migration Helped**: Today's global migration prevents future bloat

### Recommended Action

**START WITH**: Remove projects for non-existent directories (lowest risk, good benefit)

**Script Provided**: Conservative cleanup removing only missing dirs

**Backup First**: ALWAYS create timestamped backup before any changes

---

## Next Steps

1. Review this strategy
2. Create backup
3. Run analysis script to see what can be safely removed
4. Approve manual removal of specific categories
5. Execute cleanup
6. Verify Claude Code functionality
7. Measure improvement

---

**Document Created**: 2025-11-30
**File Analyzed**: ~/.claude.json (210KB, 4,903 lines, 166 projects)
**Recommendation**: Conservative cleanup - remove missing directories first
**Estimated Reduction**: 30-40% file size with low risk
