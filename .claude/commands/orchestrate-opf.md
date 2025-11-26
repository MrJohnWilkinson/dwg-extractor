---
description: Generate and implement specs in one piece flow from breakdown document
argument-hint: <breakdown file path>
model: opus
---

# One Piece Flow Orchestration

Orchestrate sub-agents to sequentially generate and implement specifications in a single flow. Each task in the breakdown is fully completed (spec generated, then implemented) before moving to the next task, allowing later tasks to learn from actual implementation results.

## Purpose

This command implements a One Piece Flow workflow for task breakdowns. Instead of generating all specs first and then implementing them (batch processing), this command generates and implements each task one at a time. This ensures that each subsequent spec can account for the reality of what was actually built, not just what was planned.

## Variables

**Breakdown File Path**:
$ARGUMENTS

## Instructions

### Your Role
You are the orchestrator managing sub-agents to complete tasks from the breakdown document in a One Piece Flow manner.
- Use your reasoning model: ULTRATHINK about the orchestration requirements.
- You maintain context and learnings across the entire workflow
- You coordinate sub-agents but do not do the work directly

### Initial Setup

**1. Read and Parse Breakdown File**
- Read the breakdown file provided in $ARGUMENTS
- Extract all tasks following the standard format:
  - Task number and title (e.g., "### Task 1: Implement URL Parameter Handling")
  - Suggested command (e.g., "**Suggested Command**: `/dev:feature`")
  - Complexity level
  - Estimated time
  - Dependencies
  - Description and deliverables
- Validate that the breakdown follows the expected format
- Create a task list with all extracted tasks

**2. Initialize Tracking**
- Use TodoWrite to create a todo list with all tasks from the breakdown
- Each todo should indicate: Task name, status (pending/in_progress/completed)
- Track generated spec files and implementation results as you progress

### Workflow for Each Task

For each task in the breakdown sequence, follow this two-phase process:

#### Phase 1: Generate Specification

**1. Launch Spec Generation Sub-agent**
- Create a new general-purpose sub-agent to generate the spec for this task
- Provide the sub-agent with:
  - The full breakdown document context
  - The specific task section they're working on
  - The task number (e.g., Task 1, Task 2)
  - **List of ALL previously generated specs** (from earlier tasks)
  - **Implementation learnings** from previous tasks (what actually happened vs. what was planned)
- Instruct the sub-agent to:
  1. Run `/utils:prime` to understand the codebase
  2. **Review implementation learnings** from prior tasks to understand the current state
  3. Run the suggested command (`/dev:feature`, `/dev:bug`, or `/dev:chore`) with task context
  4. Ensure spec filename includes `-task-[N]-` after the spec number
  5. Report the path to the generated spec file

**2. Review Spec Generation Report**
- Verify the spec file was created successfully
- Add the spec path to your list of generated specs

**3. Spec Generation Decision Logic**
- **IF spec was generated successfully**:
  - Add spec path to the list of prior specs
  - Proceed to Phase 2 (Implementation)

- **IF spec generation failed**:
  - Retry ONCE (second attempt)
  - If still failing, STOP and report to user
  - Do NOT skip to implementation or next task

**4. Spec Generation Safety Limits**
- Maximum **2 attempts per task** for spec generation
- If 2 attempts fail, STOP and report to the user

#### Phase 2: Implement Specification

**1. Launch Implementation Sub-agent**
- Create a new general-purpose sub-agent to implement the spec just generated
- The sub-agent will work in the same branch and directory, continuing from the current git state
- Instruct the sub-agent to:
  1. Run `/utils:prime` to understand the codebase
  2. Run `/dev:implement [spec-path]` to implement the specification

**2. Review Implementation Report**
- The sub-agent's `/dev:implement` produces a report including `git diff --stat`
- Read this report from the sub-agent's final message
- Check if it contains the flag `MORE-TO-DO`

**3. Implementation Decision Logic**
- **If the `MORE-TO-DO` flag is in the report**:
  - The sub-agent made progress but may not have completed all tasks
  - Launch a NEW sub-agent for the SAME spec (repeat from Phase 2, step 1) with context on the unfinished tasks

- **IF no `MORE-TO-DO` flag is in the reprot**:
  - The spec is fully implemented
  - **Capture implementation learnings**:
    - Review git commits made during implementation
    - Note any deviations from the original breakdown's assumptions
    - Note any discoveries or approach changes
    - Document the actual state of the system now
  - Mark this task as completed
  - Proceed to the NEXT task in the breakdown (Phase 1)

**Why This Loop?** Large specs may exceed a single agent's context window, leaving tasks incomplete. Re-running ensures full completion - subsequent runs continue where the previous agent left off until no further changes are needed.

**4. Implementation Safety Limits**
- Maximum **5 sub-agent attempts per spec implementation**
- If 5 sub-agents have run for a single spec, STOP and report to the user
- This prevents infinite loops

**5. Error Handling**
- If a sub-agent fails or produces an error, STOP immediately
- Report the error to the user and wait for guidance
- Do NOT skip to the next task or retry automatically on errors

**6. Progress Tracking**
- Use the TodoWrite tool to track progress through the task sequence
- Mark each task phase appropriately:
  - "Generating spec for Task N" → in_progress
  - "Implementing spec for Task N" → in_progress
  - "Task N complete" → completed
- Update the todo list after each sub-agent completes

### Capturing and Using Implementation Learnings

**What to Capture After Each Implementation:**
- Git commits made (what was actually built)
- Any design decisions that differed from the breakdown
- Discoveries about the codebase that affect future tasks
- Changes to file structure, naming conventions, or patterns
- Any assumptions in the breakdown that proved incorrect

**How to Pass Learnings to Next Spec Generation:**
When launching the next spec generation sub-agent, include:
- Summary of what was actually built in previous task(s)
- Any changes to the plan or approach
- Current state of the codebase (what exists now)
- Recommendations for how this task should integrate with what was actually built

## Workflow

```
For each task in breakdown:
  # Phase 1: Generate Spec
  spec_attempt = 0

  While spec_attempt < 2:
    1. Launch sub-agent to generate spec
    2. Sub-agent runs: /utils:prime
    3. Sub-agent reads: prior specs + implementation learnings
    4. Sub-agent runs: /dev:feature (or /dev:bug or /dev:chore)
    5. Sub-agent reports: generated spec file path

    If spec created successfully:
      Add spec to prior_specs list
      Break to Phase 2

    If spec generation failed:
      spec_attempt++
      If spec_attempt < 2:
        Retry
      Else:
        Stop and report to user

  # Phase 2: Implement Spec
  impl_attempt = 0

  While impl_attempt < 5:
    1. Launch sub-agent to implement spec
    2. Sub-agent runs: /utils:prime, /dev:implement [spec]
    3. Sub-agent commits and pushes changes
    4. Read sub-agent's report (git diff --stat)

    If report shows changes (files/lines > 0):
      impl_attempt++
      Continue loop (launch another implementation sub-agent)

    If report shows no changes (0 files, 0 lines):
      Capture implementation learnings:
        - What was actually built
        - Any deviations from breakdown
        - Current state of codebase
      Mark task complete
      Break to next task (Phase 1)

    If error:
      Stop and report to user

  If impl_attempt == 5:
    Stop and report limit reached

Continue to next task...
```

## Report

After completing all tasks (or encountering an error/limit):

- Summarize the One Piece Flow orchestration results:
  - List each task and its status (completed, limit reached, or error)
  - List all generated spec file paths in order
  - Report total number of sub-agents launched per task (spec generation + implementation)
  - Report any tasks that were skipped due to errors
  - Include final `git log --oneline -20` to show all commits made
  - Include summary of overall changes from start to finish

- Provide comparison to original breakdown:
  - Tasks completed as planned
  - Tasks that deviated from the plan (and why)
  - Key learnings discovered during implementation

- Summary table:
  ```
  | Task | Suggested Cmd | Generated Spec | Spec Attempts | Impl Attempts | Status |
  |------|---------------|----------------|---------------|---------------|--------|
  | Task 1: [title] | /dev:feature | specs/XXX-task-1.md | 1 | 2 | ✅ Completed |
  | Task 2: [title] | /dev:bug | specs/YYY-task-2.md | 1 | 1 | ✅ Completed |
  | ... | ... | ... | ... | ... | ... |
  ```
