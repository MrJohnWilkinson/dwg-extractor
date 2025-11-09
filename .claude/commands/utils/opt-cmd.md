---
allowed-tools: Bash(date:*), Bash(time:*), Read, AskUserQuestion
argument-hint: <path-to-command.md>
description: Track command execution timing with sequential step-by-step timestamps
---

# Track Command Timing

Monitors command execution by tracking timestamps at each step and displaying a sequential timing report. No analysis or optimization - just raw timing data.

## Variables

command_path: $ARGUMENTS (relative path to command file, e.g., `.claude/commands/utils/start.md`)

## Instructions

- IMPORTANT: Only track timing for command files, not application code
- IMPORTANT: Always ask user for test arguments BEFORE executing the target command
- Monitor timing at every step: capture timestamp before/after each tool call
- Output sequential list showing: step number, timestamp, duration, description
- No analysis, no recommendations, no optimizations - just raw timing data
- Keep output minimal during execution, display final sequential list at end

## Workflow

1. **Validate Input**
   - Capture start timestamp: `date +%s.%N` (store as START_TIME)
   - Read command file from `command_path`
   - Verify it's a valid command file (has metadata, workflow sections)
   - Ask user: "What arguments should I use to test this command?"
   - Store test arguments for execution

2. **Execute and Track Timing**
   - Initialize step counter (step=1)
   - Before each tool call: capture timestamp with `date +%s.%N`
   - Execute the command's workflow exactly as written
   - Wrap all bash commands with `time` to measure execution
   - After each tool call: capture timestamp again
   - Store: step number, start timestamp, end timestamp, duration (from `time`), description
   - Track user confirmation requests/responses as separate timing entries
   - Continue until command completes or fails
   - Capture final timestamp: `date +%s.%N` (store as END_TIME)

3. **Display Sequential Timing List**
   - Calculate elapsed time from START_TIME for each step
   - Output table format:
     ```
     TIMING REPORT
     =============
     Step | Elapsed   | Duration | Description
     -----|-----------|----------|----------------------------------
     1    | 00:00.000 | 0.012s   | Capture start timestamp
     2    | 00:00.012 | 0.000s   | Read command file
     3    | 00:00.012 | 0.015s   | Execute step X
     ...
     N    | 01:23.456 | -        | END (total elapsed: 1m 23.456s)
     ```
   - Include user wait times as separate entries (e.g., "WAIT: User confirmation")
   - No calculations, no analysis, no recommendations - just the raw timing data

## Examples

**Track timing for update_repo_template command:**
```
/utils:opt-cmd .claude/commands/utils/update_repo_template.md
```

**Track timing for start command:**
```
/utils:opt-cmd .claude/commands/utils/start.md
```

**Track timing for a development workflow command:**
```
/utils:opt-cmd .claude/commands/dev/implement.md
```

## Report

Display simple sequential timing list:

```
TIMING REPORT
=============

Step | Elapsed   | Duration | Description
-----|-----------|----------|----------------------------------
1    | 00:00.000 | 0.012s   | Capture start timestamp
2    | 00:00.012 | 0.000s   | Read command file
3    | 00:00.012 | -        | Ask user for test arguments
4    | 00:15.000 | -        | WAIT: User provides arguments
5    | 00:15.000 | 1.368s   | Clone repository
6    | 00:16.368 | 0.015s   | Copy files
7    | 00:16.383 | 3.145s   | Commit and push
8    | 00:19.528 | 0.008s   | Cleanup
-----|-----------|----------|----------------------------------
END  | 00:19.536 | -        | Total elapsed: 19.536s

Command execution time: 4.548s (23.3%)
AI/User decision time: 14.988s (76.7%)
```

That's it - no analysis, no recommendations, just the raw data.
