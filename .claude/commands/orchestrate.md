---
model: opus
---

# Spec Orchestration

Orchestrate sub-agents to sequentially complete multiple implementation specs.

## Purpose

This command manages the sequential execution of multiple specification files by launching sub-agents to implement each spec. 

## Variables

SPEC_PATHS: $ARGUMENTS (required, space-separated spec file paths)

## Instructions
- You are the orchestrator managing sub-agents to complete the specs listed in the `Variables` section above.
- Use your reasoning model: ULTRATHINK about the orchestration requirements.

## Workflow
```
For each spec in sequence:
- Create a new general-purpose sub-agent
- Instruct the sub-agent to use `/utils:prime`
- Instruct the sub-agent to use `/dev:implement [spec-path]` custom slash command to implement the specification.
- wait for sub-agent to complete implementation, commit and report
- If more specs remain, launch NEW sub-agent and repeat until all specs in SPEC_PATHS are complete
```

## Report

After completing all specs (or encountering an error/limit):

- Summarize the orchestration results:
  - List each spec and its status (completed, limit reached, or error)
  - Include final `git log --oneline -10` to show all commits made
  - Include summary of overall changes from start to finish
