# Git Rebuild Strategy Analysis: Restarting from ad25eab

## Executive Summary

Restarting from commit ad25eab is the correct strategy. Your two reference documents provide excellent guidance, and the retrospective analysis proves that only 3 of 17 commits delivered working solutions. The recommended approach is creating a new branch from ad25eab (not hard reset) to preserve current work as reference while implementing a clean rebuild using the user stories as specs.

## Table Summary

| Strategy | Risk | Code Preservation | Complexity | Recommended |
|----------|------|-------------------|------------|-------------|
| New branch from ad25eab | Low | Full (reference branch) | Low | **YES** |
| Hard reset to ad25eab | Medium | Lost forever | Low | No |
| Cherry-pick 3 winning commits | Medium | Partial | High | Fallback option |
| Incremental revert | High | Tangled history | Very High | No |

## Relevant Files

- **ai_output/005-content-zone-optimization-retrospective.md** - Documents which implementations actually worked (3 wins out of 17 commits)
- **ai_output/006-rebuild-user-stories-from-e356096.md** - Comprehensive user stories with implementation requirements, lessons learned, and recommended order
- **specs/022-polygon-count-threshold.md, specs/023-line-segment-threshold.md, specs/021-file-based-debug-logging.md** - The 3 specs that actually worked and should be retained
- **app/core/geometry.py** - 786 lines changed, core of the complexity issues
- **app/core/extractor.py** - 781 lines changed, contains abort logic that needed 3 follow-ups
- **app/tests/core/test_content_zone.py** - 602 lines of tests worth preserving

## Current State Analysis

**Commits After ad25eab:** 17 commits with ~28,700 lines changed in `app/`

**Working Implementations (3):**
1. `065f3b3` - Polygon count threshold (30) - prevents O(n^3) hang
2. `d8bc7c6` - LINE segment threshold (200) - prevents DFS hang
3. `cd39fe1` - File-based DEBUG logging with flush

**Problematic Implementations (14):**
- Live log viewer: GUI blocks during computation
- Abort extraction: Required 3 follow-up commits
- Final 2 commits: Still diagnosing unresolved hangs

## Recommended Git Strategy

### Step 1: Preserve Current Work
```bash
# Create backup tag for current state
git tag backup-content-zone-attempt-1 HEAD

# Create reference branch (optional but useful)
git branch content-zone-reference dwg-extractor-stage
```

### Step 2: Create Clean Rebuild Branch
```bash
# Create new branch from the clean commit
git checkout -b content-zone-rebuild-v2 ad25eab
```

### Step 3: Copy Reference Documents to New Branch
```bash
# Checkout just the retrospective docs from current branch
git checkout dwg-extractor-stage -- ai_output/005-content-zone-optimization-retrospective.md
git checkout dwg-extractor-stage -- ai_output/006-rebuild-user-stories-from-e356096.md
git commit -m "docs: add retrospective analysis for content zone rebuild"
```

### Step 4: Implement Using User Stories as Specs
Follow the order from document 006:
1. Content Zone Detection + Polygon Threshold + LINE Threshold (together)
2. Union Bounding Box
3. File-Based Logging
4. Abort Option (with proper checkpoints from start)
5. Live Log Viewer (optional)

## Why Not Other Strategies

### Hard Reset (`git reset --hard ad25eab`)
- **Risk:** Destroys 17 commits permanently
- **Problem:** You lose the working code for thresholds and logging
- **No rollback:** Can't reference what worked

### Cherry-Pick Winning Commits
- **Risk:** Complex interdependencies
- **Problem:** 065f3b3 (polygon threshold) depends on content zone detection existing
- **Fragile:** May introduce partial states

### Incremental Revert
- **Risk:** Git history becomes confusing
- **Problem:** Commits are interdependent (abort feature spans 4 commits)
- **Technical debt:** Messy history harder to understand later

## Implementation Workflow for Single Dev + Claude Code

### Pattern: User Story → Spec → Implementation → Test

1. **Convert each user story to a spec file**
   ```
   specs/028-content-zone-with-thresholds.md
   specs/029-union-bounding-box.md
   specs/030-file-based-debug-logging.md
   specs/031-abort-extraction-responsive.md
   ```

2. **Use Claude Code to implement each spec**
   - One spec = one commit (or logical commit sequence)
   - Include tests in same commit as implementation
   - Run full test suite before committing

3. **Reference the old branch when needed**
   ```bash
   # View what the old implementation looked like
   git show content-zone-reference:app/core/geometry.py

   # Diff specific function
   git diff content-zone-rebuild-v2..content-zone-reference -- app/core/geometry.py
   ```

## Key Lessons to Apply in Rebuild

From document 005 (Retrospective):

1. **Implement thresholds WITH the feature, not after**
   - Don't wait for production hangs to discover O(n^3)
   - Spec 028 should include polygon threshold (30) and LINE threshold (200) from day 1

2. **Abort checkpoints inside loops, not just between phases**
   - Original abort required 3 follow-up commits
   - New spec should specify exact checkpoint locations

3. **File-based logging is the monitoring solution**
   - GUI log viewer blocks during computation
   - Implement file logging before testing with real files

4. **Test with complex fixtures early**
   - Create `many_lines_test.dxf` and `equal_area_test.dxf` immediately
   - Small test files won't reveal performance issues

## Recommendations

1. **Use new branch approach** - Preserves current work while providing clean slate
2. **Copy docs 005/006 to new branch** - They become your implementation guide
3. **Create consolidated specs** - Combine related user stories into single specs (e.g., content zone + both thresholds)
4. **Commit atomically** - Each feature complete with tests before moving to next
5. **Keep reference branch** - Compare implementation approaches when stuck

## Next Steps

1. Run the git commands from "Recommended Git Strategy" section
2. Copy retrospective docs to new branch
3. Create `specs/028-content-zone-with-thresholds.md` combining user stories 1-3
4. Implement core content zone with thresholds as first feature
5. Validate with `uv run pytest app/tests/` before proceeding
