# Orchestrate-OPF Command Sequence Analysis

## Executive Summary

The orchestrate-opf.md command implements a One Piece Flow workflow for sequential spec generation and implementation. While the overall sequence is logically sound, there are opportunities to improve conciseness, clarify ambiguous steps, and add missing error handling that exists in similar commands.

## Table Summary

| Step | Current State | Issue | Recommendation |
|------|---------------|-------|----------------|
| Initial Setup 1 | Identify Units | Clear | Keep as-is |
| Initial Setup 2 | Estimate Units | Verbose | Merge with step 3 |
| Initial Setup 3 | Determine Breakdown | Related to step 2 | Merge into single "Classify Units" step |
| Initial Setup 4 | Initialize Tracking | Clear | Keep as-is |
| Phase 1.1 | Launch Spec Sub-agent | Missing command type logic | Add classification guidance |
| Phase 1.2 | Verify and Proceed | No retry logic | Add 2-attempt retry (match breakdown_to_specs) |
| Phase 2.1 | Launch Impl Sub-agent | Redundant /utils:prime | Consider omitting (context shared via git state) |
| Phase 2.2 | Review/Capture Learnings | Clear | Keep as-is |

## Relevant Files

- `.claude/commands/orchestrate-opf.md` - The command being analyzed
- `.claude/commands/README.md` - Heading standards and structure guidelines
- `.claude/commands/breakdown_to_specs.md` - Similar orchestration command with better error handling
- `.claude/commands/dev/feature.md` - Referenced command for spec generation
- `.claude/commands/dev/implement.md` - Referenced command for implementation

## README.md Compliance

The command **follows** the heading standards correctly:

| Requirement | Status |
|-------------|--------|
| Uses only allowed headings | PASS |
| Correct heading order | PASS |
| Variables section (has argument-hint) | PASS |
| Named variable format (DOCUMENT_PATH) | PASS |
| Uses `<DOCUMENT_PATH>` in body | PASS |

## Sequence Logic Issues

### Issue 1: Redundant Steps (Estimate + Determine Breakdown)

**Lines 35-45**: Steps 2 and 3 are tightly coupled - estimation directly feeds breakdown determination.

```md
# Current: Two separate steps
**2. Estimate Units** (8 lines of instruction)
**3. Determine Breakdown** (3 lines of instruction)

# Recommended: Single combined step
**2. Classify Units**
- For each unit, estimate context cost (files, LOC, tests, complexity)
- Classify: Small (<30k tokens), Medium (30-90k), Large (90k+)
- Group small units to medium size, subdivide large units
```

### Issue 2: Missing Command Type Classification Logic

**Line 69**: Instructs sub-agent to "Run suggested command (`/dev:feature`, `/dev:bug`, or `/dev:chore`)" but provides no logic for determining which command applies.

**Problem**: The input document contains units like "### User Story 1:" - these don't inherently map to feature/bug/chore.

**Recommendation**: Add classification guidance:
```md
- Classify unit type by analyzing content:
  - New functionality/capability → /dev:feature
  - Fixing incorrect behavior → /dev:bug
  - Refactoring/maintenance/cleanup → /dev:chore
```

### Issue 3: Missing Retry Logic

**Lines 75-76**: States "On failure: STOP and report to user (do not retry or skip)"

**Contrast with breakdown_to_specs.md**: Lines 93-94 specify "Maximum **2 attempts per task** (1 initial + 1 retry on failure)"

**Recommendation**: Add consistent retry logic (1 retry before stopping) to match established patterns.

### Issue 4: First Unit Edge Case Not Explicit

**Line 65**: Sub-agent receives "Implementation learnings from previous units" but no explicit handling for first unit.

**Recommendation**: Add explicit note:
```md
- For first unit: "No prior learnings (this is the first unit)"
```

### Issue 5: Redundant /utils:prime Calls

Both Phase 1 (line 67) and Phase 2 (line 82) sub-agents run `/utils:prime`.

**Analysis**: Since Phase 2 runs immediately after Phase 1 on the same codebase state, the second prime may be unnecessary overhead.

**Consideration**: Keep both for sub-agent independence, or note this is intentional for context isolation.

## Structural Conciseness Opportunities

### "Your Role" Section (Lines 23-26)

Partially redundant with Purpose section. Could be reduced to:
```md
You are the orchestrator. Coordinate sub-agents but do not do work directly.
```

### Nested Numbered Lists

The Phase 1/Phase 2 structure has 3 levels of nesting (Phase → Numbered Step → Sub-numbered steps → Bullet points). Consider flattening:

```md
# Current structure (complex nesting)
#### Phase 1: Generate Specification
**1. Launch Spec Generation Sub-agent**
- Sub-agent instructions:
  1. Run `/utils:prime`
  2. Review implementation learnings...

# Simplified structure
#### Phase 1: Generate Specification
- Launch sub-agent with: unit content, identifier, prior learnings
- Sub-agent: Run /utils:prime → Review learnings → Run /dev:* → Commit spec
- Verify spec created, add to tracking list
- On failure: STOP (no retry/skip)
```

## Proposed Revised Structure

```md
## Instructions

### Your Role
Orchestrator coordinating sub-agents. Do not implement directly.

### Initial Setup
1. **Read Document** - Parse <DOCUMENT_PATH>, identify ### numbered units
2. **Classify Units** - Estimate token cost, classify Small/Medium/Large, group/split to medium size
3. **Initialize Tracking** - TodoWrite with all units, track spec paths

### Per-Unit Workflow

**Phase 1: Spec Generation**
- Launch sub-agent with: unit content, type classification, prior learnings
- Sub-agent: /utils:prime → Review learnings → /dev:{feature|bug|chore} → Commit
- Verify spec created; on failure: retry once, then STOP

**Phase 2: Implementation**
- Launch sub-agent: /utils:prime → /dev:implement [spec-path]
- Capture learnings: commits made, deviations, discoveries
- Mark complete; on error: STOP immediately
```

## Recommendations

1. **Merge Initial Setup steps 2+3** into single "Classify Units" step
2. **Add command type classification logic** (feature/bug/chore determination)
3. **Add retry logic** (1 retry before stopping) for consistency with breakdown_to_specs
4. **Handle first-unit edge case** explicitly (no prior learnings)
5. **Flatten nested structure** for scannability
6. **Consider removing "Your Role" section** or reducing to one line

## Next Steps

1. Decide if retry logic should be added (aligns with breakdown_to_specs pattern)
2. Determine if command type classification should be explicit or left to sub-agent judgment
3. Apply structural simplifications without losing essential detail
