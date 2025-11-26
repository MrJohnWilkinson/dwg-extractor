---
description: Orchestrate sub-agents to sequentially complete multiple implementation specs
argument-hint: <spec file paths>
model: opus
---

# Spec Orchestration

Orchestrate sub-agents to sequentially complete multiple implementation specs. For each spec, launch sub-agents in a loop until completion is verified, with safety limits and error handling.

## Purpose

This command manages the sequential execution of multiple specification files by launching sub-agents to implement each spec. It ensures each spec is fully completed before moving to the next one.

## Variables

SPEC_PATHS: $ARGUMENTS (required, space-separated spec file paths)

## Instructions

### Your Role
You are the orchestrator managing sub-agents to complete the specs listed in the `Variables` section above.
- Use your reasoning model: ULTRATHINK about the orchestration requirements.

### Workflow for Each Spec

For each spec in the sequence, follow this process:

**1. Launch Sub-agent**
- Create a new general-purpose sub-agent to work on the current spec
- The sub-agent will work in the same branch and directory, continuing from the current git state
- Instruct the sub-agent to:
  1. Run `/utils:prime` to understand the codebase
  2. Run `/dev:implement [spec-path]` to implement the specification (this produces a git diff report)

**2. Review Sub-agent Report**
- The sub-agent's `/dev:implement` command produces a report including `git diff --stat`
- Read this report from the sub-agent's final message
- Check if changes were made (files/lines changed > 0)

**3. Decision Logic**
- **IF changes were made** (files/lines > 0 in the report):
  - The sub-agent made progress but may not have completed all tasks
  - Launch a NEW sub-agent for the SAME spec (repeat from step **1. Launch Sub-agent**)
  - IMPORTANT: - If changes were made, this means you MUST launch a NEW sub-agent, superceding any advice from the agent suggesting all tasks were finished.  The ONLY exception to this is if the changes are NOT related to this spec.
  - This ensures large specs that exceed a single agent's context are fully completed
  - This aso prevents against some agents who will declare tasks as complete, even whey they are not.

- **IF NO changes** (0 files, 0 lines in the report) AND all validations are complete:
  - The spec is complete
  - Move to the NEXT spec in the sequence

**Why This Loop?** Large specs may exceed a single agent's context window, leaving tasks incomplete. Re-running ensures full completion - subsequent runs continue where the previous agent left off until no further changes are needed.

**4. Safety Limits**
- Maximum **5 sub-agent attempts per spec**
- If 5 sub-agents have run for a single spec, STOP and report to the user
- This prevents infinite loops

**5. Error Handling**
- If a sub-agent fails or produces an error, STOP immediately
- Report the error to the user and wait for guidance
- Do NOT skip to the next spec or retry automatically on errors

**6. Progress Tracking**
- Use the TodoWrite tool to track progress through the spec sequence
- Mark each spec as in_progress, completed, or blocked
- Update the todo list after each sub-agent completes

## Workflow

```
For each spec in sequence:
  attempt_count = 0

  While attempt_count < 5:
    1. Launch sub-agent with spec
    2. Sub-agent runs: /utils:prime, /dev:implement [spec]
    3. Sub-agent's /dev:implement produces git diff report
    4. Sub-agent commits and pushes changes
    5. Read sub-agent's report

    If report shows changes (files/lines > 0):
      attempt_count++
      Continue loop (launch another sub-agent)

    If report shows no changes (0 files, 0 lines):
      Mark spec complete
      Break to next spec

    If error:
      Stop and report to user

  If attempt_count == 5:
    Stop and report limit reached
```

## Report

After completing all specs (or encountering an error/limit):

- Summarize the orchestration results:
  - List each spec and its status (completed, limit reached, or error)
  - Report total number of sub-agents launched per spec
  - Report any specs that were skipped due to errors
  - Include final `git log --oneline -10` to show all commits made
  - Include summary of overall changes from start to finish
