# Directory Cleanup

## Purpose

Archive all numbered analysis files from ai_output/ and specs/ directories to reduce clutter.

## Variables

- **Target directories:** `ai_output/` and `specs/`
- **File pattern:** `NNN-*.md` (where NNN = 3-digit number)
- **Archive names:** `archived_ai_output.tar` and `archived_specs.tar`

## Instructions

- Only compress files with NNN-*.md prefix
- Do not compress files without numeric prefix (e.g., README.md, SUPABASE_SETUP.md)
- Do not compress folders
- Append to existing archives rather than creating new ones
- Process both directories using the same procedure

## Workflow

**For each directory (ai_output/, then specs/):**

1. **Navigate to target directory**

2. **Append numbered files to archive** - Use `find . -maxdepth 1 -name '[0-9][0-9][0-9]-*.md' -print0 | tar -rf archived_[dirname].tar --null -T -` to batch append all matching files directly to the archive

3. **Delete archived files** - Use `find . -maxdepth 1 -name '[0-9][0-9][0-9]-*.md' -delete` to remove all numbered files

4. **Verify and report** - Run `echo "Archive contains $(tar -tf archived_[dirname].tar | wc -l) files" && ls -1` to confirm cleanup

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
├── archived_specs.tar (contains 001-014)
└── templates/
```

**Processing:**
- **All NNN files:** 015, 023, 028, 031, 035, 037, 040, 042, 043, 044, 045 (11 files)
- **Append to archive:** All 11 files appended directly (no extraction needed), archive now contains 001-045 (26 files total)
- **Delete:** All 11 numbered files removed

**Directory after cleanup:**
```
specs/
├── README.md
├── archived_specs.tar (contains 001-045)
└── templates/
```

## Report

- Summarize files archived for each directory
- Report current file count and archive size
- List the range of NNN files now in archive (e.g., "001-045")
