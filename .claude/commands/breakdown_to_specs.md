---
description: Generate specification files from a task breakdown document
argument-hint: <breakdown file path>
model: opus
---

# Breakdown to Specs Generator

Generate specification files from a task breakdown document by launching sub-agents sequentially. Each sub-agent creates a detailed spec file by running /utils:prime and the suggested command (/dev:feature, /dev:bug, or /dev:chore).

## Purpose

This command reads a breakdown document (created via `/breakdown`) and automatically generates detailed specification files for each task. It orchestrates sub-agents to sequentially create specs, ensuring later specs are aware of earlier ones to avoid conflicts.

## Variables

BREAKDOWN_PATH: $ARGUMENTS (required)

## Instructions

### Your Role
You are the orchestrator managing sub-agents to generate specification files from the breakdown document provided in the `Variables` section.
- Use your reasoning model: THINK HARD about the orchestration requirements.


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
- Each todo should indicate: Task name, suggested command, status (pending)
- Track generated spec files as you progress

### Workflow for Each Task

For each task in the breakdown sequence, follow this process:

**1. Launch Sub-agent**
- Create a new general-purpose sub-agent to generate the spec for the current task
- Provide the sub-agent with:
  - The full breakdown document context
  - The specific task section they're working on
  - **The task number** (e.g., Task 1, Task 2, etc.) for use in spec filename
  - List of ALL previously generated spec files (from earlier tasks)
- Instruct the sub-agent to:
  1. Run `/utils:prime` to understand the codebase
  2. **Read all previously generated spec files** (paths will be provided)
     - This ensures awareness of earlier design decisions
     - Prevents conflicting approaches between tasks
     - Maintains consistency across the spec sequence
  3. Run the suggested command for this task:
     - If task suggests `/dev:feature`: Run `/dev:feature` with task context
     - If task suggests `/dev:bug`: Run `/dev:bug` with task context
     - If task suggests `/dev:chore`: Run `/dev:chore` with task context
     - If the taks doesn't include a suggested command, then read 
  4. The command will generate a spec file in `specs/` directory
  5. Report the path to the generated spec file

**2. Review Sub-agent Report**
- The sub-agent should report the path to the generated spec file
- Verify the spec file was created successfully
- Add the spec path to your list of generated specs (for next task's context)

**3. Decision Logic**
- **IF spec was generated successfully**:
  - Mark task as completed in TodoWrite
  - Add spec path to the list of prior specs
  - Move to the NEXT task in the sequence

- **IF spec generation failed**:
  - Retry ONCE (second attempt)
  - If still failing, STOP and report to user
  - Do NOT skip to the next task

**Why Prior Specs Matter**: Each task builds on previous ones. Later sub-agents must read earlier specs to ensure they:
- Use consistent patterns and approaches
- Don't contradict earlier design decisions
- Reference earlier implementations correctly
- Maintain architectural coherence

**4. Safety Limits**
- Maximum **2 attempts per task** (1 initial + 1 retry on failure)
- If 2 attempts fail for a single task, STOP and report to the user
- This prevents infinite loops and ensures user can intervene

**5. Error Handling**
- If a sub-agent fails or produces an error, retry ONCE
- If the retry fails, STOP immediately
- Report the error to the user and wait for guidance
- Do NOT skip to the next task or continue automatically on errors

**6. Progress Tracking**
- Use the TodoWrite tool to track progress through the task sequence
- Mark each task as in_progress when starting, completed when done
- Update the todo list after each sub-agent completes
- Maintain the list of generated spec file paths for final report

## Workflow Diagram

```
For each task in breakdown:
  attempt_count = 0

  While attempt_count < 2:
    1. Launch sub-agent with task context
    2. Sub-agent runs: /utils:prime
    3. Sub-agent reads: all previously generated specs
    4. Sub-agent runs: /dev:feature (or /dev:bug or /dev:chore)
    5. Sub-agent reports: generated spec file path
    6. Read sub-agent's report

    If spec file created successfully:
      Mark task complete in TodoWrite
      Add spec path to prior_specs list
      Break to next task

    If spec generation failed:
      attempt_count++
      If attempt_count < 2:
        Retry (continue loop)
      Else:
        Stop and report to user

    If error:
      Stop and report to user
```

## Sub-agent Prompt Template

When launching a sub-agent, use this structure:

```
You are generating a specification file for the following task from a breakdown document.

**Breakdown Document**: [path]
**Task Number**: [N]
**Task Title**: [title]
**Suggested Command**: [/dev:feature | /dev:bug | /dev:chore]

**Previously Generated Specs (READ THESE FIRST)**:
[List all prior spec file paths, or "None (this is the first task)"]

**Your Instructions**:
1. Run `/utils:prime` to understand the codebase
2. Read all previously generated spec files listed above (if any)
   - Note their approaches, patterns, and design decisions
   - Ensure your spec is consistent with earlier specs
   - Avoid conflicts or contradictions
3. Run [suggested command] with the following context:

**Task Context**:
[Copy the complete task section from breakdown, including:
- Description
- Complexity and estimated time
- Dependencies
- Deliverables
- Any special notes]

4. **IMPORTANT - Spec Filename Convention**:
   When the command generates the spec file, ensure the filename includes `-task-[N]-` after the spec number.
   - Example: For Task 1, the spec should be named `specs/083-task-1-description.md`
   - Example: For Task 2, the spec should be named `specs/084-task-2-description.md`
   - The command will provide the base naming convention; you just need to ensure `-task-[N]-` is inserted after the spec number.

5. Report back:
   - The path to the generated spec file
   - A brief summary of what the spec covers
   - Any design decisions that later tasks should be aware of

**Important**: Make sure your spec is detailed enough to be implemented by a future sub-agent using `/dev:implement`, but also aware of and consistent with the prior specs you read.
```

## Report

After completing all tasks (or encountering an error/limit):

- Summarize the spec generation results:
  - List each task and its status (completed, failed, or error)
  - List all generated spec file paths in order
  - Report total number of sub-agents launched per task (1 or 2)
  - Report any tasks that were skipped due to errors

- Provide the next step command:
  ```bash
  # To implement all generated specs, run:
  /orchestrate [spec1] [spec2] [spec3] ... [specN]
  ```

- Include a summary table:
  ```
  | Task | Suggested Command | Generated Spec | Status |
  |------|-------------------|----------------|--------|
  | Task 1: [title] | /dev:feature | specs/XXX-task-1.md | ✅ Completed |
  | Task 2: [title] | /dev:bug | specs/YYY-task-2.md | ✅ Completed |
  | ... | ... | ... | ... |
  ```

## Example Usage

```bash
# Generate specs from a breakdown file
/breakdown_to_specs ai_output/053-goals-html-template-consolidation-strategy-breakdown.md

# This will:
# 1. Parse the 5 tasks from the breakdown
# 2. Launch sub-agents to generate 5 spec files
# 3. Each sub-agent reads prior specs before generating theirs
# 4. Output: specs/083-task-1*.md, specs/084-task-2*.md, specs/085-task-3*.md, specs/086-task-4*.md, specs/087-task-5*.md
# 5. Provide /orchestrate command to implement all specs

# Then implement all generated specs:
/orchestrate specs/083-*.md specs/084-*.md specs/085-*.md specs/086-*.md specs/087-*.md
```


