---
description: Archive ai_output and specs directories to tar files
argument-hint: [files to exclude]
model: opus
---

# Archive Directories

## Purpose

Archive all files from ai_output/ and specs/ to their respective .tar files, excluding specified files.

## Variables

- **EXCLUDE_FILES:** $ARGUMENTS (optional) - Relative paths of files to keep unarchived

## Instructions

1. For ai_output/:

   - Find all files (not subdirectories, not \*.tar)
   - Exclude any files in <EXCLUDE_FILES>
   - Append to ai_output/ai_output.tar
   - Delete archived files

2. For specs/:

   - Find all files (not subdirectories, not \*.tar)
   - Exclude any files in <EXCLUDE_FILES>
   - Append to specs/specs.tar
   - Delete archived files

3. Commit: "chore: archive ai_output and specs files"

## Report

- Files archived per directory
- Files excluded (if any)
- Final directory contents
