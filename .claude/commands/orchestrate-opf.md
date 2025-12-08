---
description: Generate and implement specs in one piece flow from document containing any size tasks, stories, phases etc
argument-hint: <breakdown file path>
model: opus
---

# One Piece Flow Orchestration

Orchestrate sub-agents to sequentially generate and implement specifications in a single flow. Each unit in the document is fully completed (spec generated, then implemented) before moving to the next unit, allowing later units to learn from actual implementation results.

## Purpose

This command implements a One Piece Flow workflow. Instead of generating all specs first and then implementing them (batch processing), this command generates and implements each unit one at a time. This ensures that each subsequent spec can account for the reality of what was actually built, not just what was planned.

## Variables

DOCUMENT_PATH: $ARGUMENTS (required) - Path to breakdown document containing units of work

## Instructions

### Your Role
You are the orchestrator managing sub-agents to complete units in a One Piece Flow manner.
- Maintain context and learnings across the entire workflow
- Coordinate sub-agents but do not perform implementation work directly

### Initial Setup

**1. Read Document**
- Read the document at <DOCUMENT_PATH>
- Identify units by scanning for numbered ### headings (e.g., `### User Story 1:`, `### Task 1:`)

**2. Classify Units**
- For each unit, estimate LLM context cost based on: files to read/modify, lines of code, test files, complexity
- Classify each: Small (<30k tokens), Medium (30-90k tokens), Large (90k+ tokens)
- Group small units together until reaching medium size
- Subdivide large units into medium-sized chunks
- Determine command type by analyzing content:
  - New functionality → `/dev:feature`
  - Fixing incorrect behavior → `/dev:bug`
  - Refactoring/maintenance → `/dev:chore`

**3. Initialize Tracking**
- Use TodoWrite to create todos for all classified units
- Track status: pending → in_progress → completed
- Maintain list of generated spec file paths throughout

### Per-Unit Workflow

#### Phase 1: Generate Specification

**1. Launch Spec Generation Sub-agent**
- Provide sub-agent with:
  - Full unit content (single unit or grouped small units)
  - Unit identifier and command type classification
  - Implementation learnings from previous units (or "None" for first unit)
- Sub-agent instructions:
  1. Run `/utils:prime`
  2. Review implementation learnings from prior units
  3. Run classified command (`/dev:feature`, `/dev:bug`, or `/dev:chore`)
  4. Use spec filename format: `XXX-unit-[N]-description.md`
  5. Commit the spec file

**2. Verify and Proceed**
- Confirm spec file was created successfully
- Add path to generated specs list
- On failure: Retry once. If still failing, STOP and report to user

#### Phase 2: Implement Specification

**1. Launch Implementation Sub-agent**
- Create sub-agent on same branch with current git state
- Sub-agent instructions:
  1. Run `/utils:prime`
  2. Run `/dev:implement [spec-path]`

**2. Capture Learnings and Complete**
- Read sub-agent report (includes `git diff --stat`)
- Capture implementation learnings:
  - Git commits made (what was actually built)
  - Deviations from document assumptions
  - Approach changes or discoveries
- Mark unit completed in TodoWrite
- On error: STOP immediately and report to user

Proceed to next unit.

## Report

After completing all units (or encountering an error/limit):

- Summarize the One Piece Flow orchestration results:
  - List each unit and its status (completed, limit reached, or error)
  - List all generated spec file paths in order
  - Report any units that were skipped due to errors
  - Include final `git log --oneline -20` to show all commits made
  - Include summary of overall changes from start to finish

- Provide comparison to original document:
  - Units completed as planned
  - Units that deviated from the plan (and why)
  - Key learnings discovered during implementation

- Summary table:
  ```
  | Unit | Suggested Cmd | Generated Spec | Status |
  |------|---------------|----------------|--------|
  | Unit 1: [title] | /dev:feature | specs/XXX-unit-1.md | ✅ Completed |
  | Unit 2: [title] | /dev:bug | specs/YYY-unit-2.md | ✅ Completed |
  ```
