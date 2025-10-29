# Directory Cleanup

## Purpose

Archive old numbered analysis files from ai_output/ and specs/ directories while keeping the 10 most recent files accessible. This reduces directory clutter while preserving historical documentation.

## Variables

- **Target directories:** `ai_output/` and `specs/`
- **File pattern:** `NNN-*.md` (where NNN = 3-digit number)
- **Archive names:** `archived_ai_output.tar.gz` and `archived_specs.tar.gz`
- **Retention count:** Top 10 highest numbered files remain active

## Instructions

- Only compress files with NNN-*.md prefix
- Do not compress files without numeric prefix (e.g., README.md, SUPABASE_SETUP.md)
- Do not compress folders
- Append to existing archives rather than creating new ones
- Process both directories using the same procedure

## Workflow

**For each directory (ai_output/, then specs/):**

1. **Navigate to target directory**

2. **Identify all numbered files** - Find all files matching `NNN-*.md` pattern (3-digit prefix)

3. **Sort files numerically** - Order by NNN number (lowest to highest)

4. **Determine archive candidates** - Exclude the top 10 highest numbered files, select all remaining NNN-*.md files for archiving

5. **Extract existing archive (if present)** - If `archived_[dirname].tar.gz` exists, extract it to temporary location to append new files

6. **Create/update compressed archive** - Add all archive candidate files to `archived_[dirname].tar.gz` (appending to existing content if archive was present)

7. **Verify archive contents** - List archive contents and confirm expected file count

8. **Delete archived original files** - Remove only the NNN-*.md files that were added to the archive

9. **Confirm cleanup** - List directory to verify:
   - Top 10 highest NNN-*.md files remain
   - Non-numbered files remain (e.g., SUPABASE_SETUP.md)
   - Folders remain untouched
   - Archive file is present

**Repeat for second directory**

## Examples

**Directory before cleanup:**
```
specs/
├── 015-feature-alpha.md
├── 023-bugfix-beta.md
├── 028-refactor-gamma.md
├── 031-testing-delta.md
├── 035-ui-epsilon.md
├── 037-api-zeta.md
├── 040-db-schema.md
├── 042-optimistic-ui.md
├── 043-extend-optimistic.md
├── 044-editable-fields.md
├── 045-remove-legacy.md
├── README.md
├── archived_specs.tar.gz (contains 001-014)
└── templates/
```

**Processing:**
- **All NNN files:** 015, 023, 028, 031, 035, 037, 040, 042, 043, 044, 045 (11 files)
- **Top 10 to keep:** 023, 028, 031, 035, 037, 040, 042, 043, 044, 045
- **To archive:** 015-feature-alpha.md
- **Extract existing archive:** 001-014 files extracted to temp
- **Add to archive:** 015 added, archive now contains 001-015 (15 files total)
- **Delete:** 015-feature-alpha.md removed

**Directory after cleanup:**
```
specs/
├── 023-bugfix-beta.md
├── 028-refactor-gamma.md
├── 031-testing-delta.md
├── 035-ui-epsilon.md
├── 037-api-zeta.md
├── 040-db-schema.md
├── 042-optimistic-ui.md
├── 043-extend-optimistic.md
├── 044-editable-fields.md
├── 045-remove-legacy.md
├── README.md
├── archived_specs.tar.gz (contains 001-015)
└── templates/
```

## Report

- Summarize files archived for each directory
- Report current file count and archive size
- List the range of NNN files now in archive (e.g., "001-035")
- Confirm top 10 files remaining active
