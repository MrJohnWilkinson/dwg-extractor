# Chore: Update orchestrate-opf.md for Context-Aware Sizing

## Chore Description
Update `.claude/commands/orchestrate-opf.md` to enable context-aware sizing by replacing task-based terminology with unit-based terminology and adding a new 4-step initial setup process. This allows the orchestrator to handle any document format by analyzing context requirements and right-sizing work units for optimal agent execution.

The file has reverted to an earlier state and needs to have the following changes re-applied:
1. Rename variable from `BREAKDOWN_FILE_PATH` to `DOCUMENT_PATH`
2. Replace the "Read and Parse" section with new 4-step process (Identify, Estimate, Determine, Track)
3. Update all terminology from "task/story/breakdown" to "unit/document"

## Relevant Files
Use these files to resolve the chore:

- `.claude/commands/orchestrate-opf.md` - The target file that needs updating. Contains the One Piece Flow orchestration command that manages sub-agents for sequential spec generation and implementation.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Rename Variable (line 17)

- Change `**Breakdown File Path**:` to `**DOCUMENT_PATH**: $ARGUMENTS (required)`
- Remove the separate `$ARGUMENTS` line (line 18) since it's now inline

### Step 2: Update Line 9 - Opening Description

- Change: "Each task in the breakdown is fully completed (spec generated, then implemented) before moving to the next task, allowing later tasks to learn from actual implementation results."
- To: "Each unit in the document is fully completed (spec generated, then implemented) before moving to the next unit, allowing later units to learn from actual implementation results."

### Step 3: Update Line 13 - Purpose Section

- Change: "This command implements a One Piece Flow workflow for task breakdowns. Instead of generating all specs first and then implementing them (batch processing), this command generates and implements each task one at a time."
- To: "This command implements a One Piece Flow workflow. Instead of generating all specs first and then implementing them (batch processing), this command generates and implements each unit one at a time."

### Step 4: Update Line 23 - Your Role Section

- Change: "You are the orchestrator managing sub-agents to complete tasks from the breakdown document in a One Piece Flow manner."
- To: "You are the orchestrator managing sub-agents to complete units from the document in a One Piece Flow manner."

### Step 5: Replace Initial Setup Section (lines 30-45)

Replace the entire "Read and Parse Breakdown File" and "Initialize Tracking" sections with:

```
**1. Identify Units**
- Read the document at <DOCUMENT_PATH>
- Identify units of work by scanning for numbered ### headings
  (e.g., `### User Story 1:`, `### Task 1:`, `### Step 1:`)
- Extract each unit's full content as context

**2. Estimate Units**
- For each unit, estimate context cost based on:
  - Files to read/modify
  - Lines of code involved
  - Test files to create/update
  - Algorithm complexity
- Classify each unit: Small, Medium, or Large

**3. Determine Breakdown**
- Small units: Group together until reaching context sweet spot → one spec
- Medium units: Each becomes its own spec → implement
- Large units: Subdivide into smaller units → re-estimate

**4. Initialize Tracking**
- Use TodoWrite to create todos for all units (pending/in_progress/completed)
- Update status as you progress:
  - "Generating spec for Unit N" → in_progress
  - "Implementing Unit N" → in_progress
  - "Unit N" → completed
- Track generated spec file paths throughout
```

### Step 6: Update Workflow Header (line 47)

- Change: `### Workflow for Each Task`
- To: `### Workflow for Each Unit`

### Step 7: Update Line 49

- Change: "For each task in the breakdown sequence, follow this two-phase process:"
- To: "For each unit, follow this two-phase process:"

### Step 8: Update Phase 1 Sub-agent Context (lines 55-60)

Replace:
```
- Provide the sub-agent with:
  - The full breakdown document context
  - The specific task section they're working on
  - The task number (e.g., Task 1, Task 2)
  - **List of ALL previously generated specs** (from earlier tasks)
  - **Implementation learnings** from previous tasks (what actually happened vs. what was planned)
```

With:
```
- Provide the sub-agent with:
  - Full unit content (may be single unit or grouped small units)
  - Unit identifier(s)
  - **List of ALL previously generated specs** (from earlier units)
  - **Implementation learnings** from previous units (what actually happened vs. what was planned)
```

### Step 9: Update Sub-agent Instructions (lines 61-66)

- Change line 63: "**Review implementation learnings** from prior tasks" → "**Review implementation learnings** from prior units"
- Change line 65: "Ensure spec filename includes `-task-[N]-`" → "Ensure spec filename includes `-unit-[N]-`"

### Step 10: Update Spec Generation Decision Logic (lines 72-84)

- Change line 75: "Proceed to Phase 2 (Implementation)" (keep as is)
- Change line 80: "Do NOT skip to implementation or next task" → "Do NOT skip to implementation or next unit"
- Change line 83: "Maximum **2 attempts per task**" → "Maximum **2 attempts per unit**"

### Step 11: Update Implementation Decision Logic (lines 100-113)

- Change line 102: "may not have completed all tasks" → "may not have completed all items"
- Change line 109: "deviations from the original breakdown's assumptions" → "deviations from the original document's assumptions"
- Change line 112: "Mark this task as completed" → "Mark this unit as completed"
- Change line 113: "Proceed to the NEXT task in the breakdown (Phase 1)" → "Proceed to the NEXT unit (Phase 1)"

### Step 12: Update Progress Tracking Section (lines 127-133)

- Change line 128: "track progress through the task sequence" → "track progress through the unit sequence"
- Change line 130: "Generating spec for Task N" → "Generating spec for Unit N"
- Change line 131: "Implementing spec for Task N" → "Implementing Unit N"
- Change line 132: "Task N complete" → "Unit N" → completed

### Step 13: Update Capturing and Using Implementation Learnings (lines 135-149)

- Change line 139: "differed from the breakdown" → "differed from the document"
- Change line 140: "affect future tasks" → "affect future units"
- Change line 142: "assumptions in the breakdown" → "assumptions in the document"
- Change line 146: "built in previous task(s)" → "built in previous unit(s)"
- Change line 149: "how this task should integrate" → "how this unit should integrate"

### Step 14: Update Workflow Pseudocode Section (lines 151-204)

- Change line 154: "For each task in breakdown:" → "For each unit in document:"
- Change line 194: "Mark task complete" → "Mark unit complete"
- Change line 195: "Break to next task (Phase 1)" → "Break to next unit (Phase 1)"
- Change line 203: "Continue to next task..." → "Continue to next unit..."

### Step 15: Update Report Section (lines 206-230)

- Change line 208: "After completing all tasks" → "After completing all units"
- Change line 211: "List each task and its status" → "List each unit and its status"
- Change line 213: "sub-agents launched per task" → "sub-agents launched per unit"
- Change line 214: "any tasks that were skipped" → "any units that were skipped"
- Change line 218: "comparison to original breakdown:" → "comparison to original document:"
- Change line 219: "Tasks completed as planned" → "Units completed as planned"
- Change line 220: "Tasks that deviated" → "Units that deviated"
- Change line 225: "| Task |" → "| Unit |"
- Change line 227: "Task 1: [title]" → "Unit 1: [title]", "specs/XXX-task-1.md" → "specs/XXX-unit-1.md"
- Change line 228: "Task 2: [title]" → "Unit 2: [title]", "specs/YYY-task-2.md" → "specs/YYY-unit-2.md"

### Step 16: Update Frontmatter Description (line 2)

- Change: `description: Generate and implement specs in one piece flow from breakdown document`
- To: `description: Generate and implement specs in one piece flow from document`

### Step 17: Update Argument Hint (line 3)

- Change: `argument-hint: <breakdown file path>`
- To: `argument-hint: <document path>`

### Step 18: Validate Changes

- Run validation commands to ensure the file is properly formatted
- Verify all "task" and "breakdown" references have been replaced with "unit" and "document"

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `grep -c "task" .claude/commands/orchestrate-opf.md` - Should return 0 or only instances where "task" is part of compound words not meant to be replaced
- `grep -c "breakdown" .claude/commands/orchestrate-opf.md` - Should return 0
- `grep -c "unit" .claude/commands/orchestrate-opf.md` - Should return multiple matches confirming replacements
- `grep -c "DOCUMENT_PATH" .claude/commands/orchestrate-opf.md` - Should return at least 1
- `head -20 .claude/commands/orchestrate-opf.md` - Verify frontmatter and opening sections look correct

## Notes

- The terminology changes are comprehensive - search for "task" and "breakdown" to ensure all instances are caught
- Some instances of "task" in phrases like "TodoWrite" should NOT be changed
- The new 4-step process (Identify Units, Estimate Units, Determine Breakdown, Initialize Tracking) replaces the previous 2-step process
- The spec filename format changes from `-task-[N]-` to `-unit-[N]-`
- This is a text replacement chore - no logic changes, just terminology alignment
