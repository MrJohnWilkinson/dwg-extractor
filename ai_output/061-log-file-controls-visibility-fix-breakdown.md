# Breakdown: Log File Controls Not Visible in GUI

## Source Document
- **Path**: specs/061-log-file-controls-visibility-fix.md
- **Type**: spec (bug fix)
- **Original Scope**: Fix visibility issue where log file controls are cut off due to insufficient window height

## Overview
This is a minimal bug fix requiring a single line change. The entire fix can be completed in one short task - no breakdown into multiple tasks is necessary.

## Task Breakdown

### Task 1: Fix Window Geometry for Log File Controls Visibility
**Focus Area**: GUI window sizing
**Suggested Command**: `/dev:bug`
**Complexity**: Simple
**Dependencies**: None

**Description**:
- Update window geometry in `app/main.py` from `600x500` to `600x750`
- The log file controls (checkbox + dropdown) already exist in the code but are cut off by insufficient window height
- Single line change at line 70

---

## Execution Order
1. Task 1 (no dependencies, standalone fix)

## Notes
- This is an extremely simple fix - one line change to a geometry string
- The bug fix spec (061) is already detailed enough to serve as the implementation guide
- No additional breakdown is warranted; implementing via `/dev:bug` with the existing spec is the most efficient approach
- Total estimated time: < 30 minutes including validation
