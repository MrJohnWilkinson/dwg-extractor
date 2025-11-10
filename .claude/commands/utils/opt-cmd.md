---
allowed-tools: Bash(date:*), Bash(find:*), Bash(jq:*), Read, SlashCommand, AskUserQuestion
argument-hint: <path-to-command.md>
description: Analyze command execution timing using automatic hook-captured timestamps
---

# Track Command Timing

Executes a command and analyzes its timing using automatic hook-captured timestamps. Displays a sequential timing report showing tool execution times, LLM processing times, and user wait times. No analysis or optimization - just raw timing data.

## Variables

command_path: $ARGUMENTS (relative path to command file, e.g., `.claude/commands/utils/start.md`)

## Instructions

- IMPORTANT: Only track timing for command files, not application code
- IMPORTANT: Always ask user for test arguments BEFORE executing the target command
- IMPORTANT: Wait for user to confirm with "start" before executing the command
- Timing is automatically captured by hooks (pre_tool_timing.py, post_tool_timing.py, notification_timing.py)
- After command completes, read timing log from `logs-timestamped/{session_id}/tool_timing.json`
- **CRITICAL: Filter out opt-cmd's own overhead** - only report timing for the actual target command
  - Exclude opt-cmd setup (Read command file, AskUserQuestion, SlashCommand invocation)
  - Exclude opt-cmd reporting (finding session ID, globbing for logs, reading timing JSON)
  - Only include steps between SlashCommand completion and start of opt-cmd report generation
- Display sequential timing table showing tool executions, notifications, and wait times
- Reset elapsed times to start from the first target command tool call (not from opt-cmd start)
- No analysis, no recommendations, no optimizations - just raw timing data from target command

## Workflow

1. **Validate Input and Get Arguments**
   - Read command file from `command_path`
   - Verify it's a valid command file (has metadata, workflow sections)
   - Ask user: "What arguments should I use to test this command?"
   - Store test arguments for execution
   - Show preview: "Will execute: /{command} {arguments}"
   - Ask user to confirm with "start"

2. **Execute Target Command**
   - Determine command name from file path (e.g., `.claude/commands/utils/start.md` → `/utils:start`)
   - Use `SlashCommand` tool to invoke: `/{command} {arguments}`
   - Timing hooks automatically capture:
     - Pre-tool timestamps (before each tool call)
     - Post-tool timestamps (after each tool call)
     - Tool execution durations (calculated from pre/post)
     - Notification timestamps (when Claude waits for user input)
   - Wait for command to complete (success or failure)

3. **Display Sequential Timing Report**
   - Find current session ID from environment or recent logs
   - Read timing log: `logs-timestamped/{session_id}/tool_timing.json`
   - **Filter timing data to exclude opt-cmd overhead:**
     - Find the SlashCommand invocation step (where opt-cmd launched the target command)
     - **START boundary:** First tool call AFTER the SlashCommand post event
     - **END boundary:** Last tool call BEFORE opt-cmd starts report generation
     - Exclude all steps before START (opt-cmd setup: Read, AskUserQuestion, SlashCommand)
     - Exclude all steps after END (opt-cmd reporting: Bash(echo $CLAUDE_SESSION_ID), Glob, Read timing.json)
     - Only include timing data from the actual target command execution
   - Parse filtered timing entries:
     - `event: "pre"` - Tool call started
     - `event: "post"` - Tool call completed (includes duration)
     - `event: "notification"` - Claude waiting for user input
   - Calculate elapsed times from first TARGET COMMAND timestamp (not first overall timestamp)
   - Reset step numbers to start from 1 for the filtered data
   - Output table format:
     ```
     TIMING REPORT FOR: /{command_name} {arguments}
     ================================================
     Step | Elapsed   | Duration | Description
     -----|-----------|----------|----------------------------------
     1    | 00:00.000 | 4.252s   | Bash: Validate paths...
     2    | 00:04.252 | -        | WAIT: User confirmation
     3    | 00:17.140 | 4.492s   | Bash: Clone template...
     ...
     END  | 01:23.456 | -        | Total elapsed: 1m 23.456s

     Command execution time: 14.575s (11.8%)
     AI/User decision time: 108.674s (88.2%)
     ```
   - Differentiate tool execution vs wait times
   - No analysis or recommendations - just raw timing data from target command only

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

Display timing report generated from automatic hook logs, filtered to exclude opt-cmd overhead:

**Data Source:** `logs-timestamped/{session_id}/tool_timing.json` (filtered)

**Filtering Logic:**
- Excludes all tool calls BEFORE the target command starts (opt-cmd setup)
- Excludes all tool calls AFTER the target command ends (opt-cmd report generation)
- Only includes timing data from the actual target command execution
- Resets step numbers and elapsed times to start from the target command's first tool call

**Report Format:**

```
TIMING REPORT FOR: /utils:update_repo_template .claude/commands
================================================================

Step | Elapsed   | Duration | Description
-----|-----------|----------|----------------------------------
1    | 00:00.000 | 4.252s   | Bash: Validate paths and pre-compute workflow variables
2    | 00:04.252 | -        | WAIT: User confirms proceed with sync
3    | 00:17.140 | 4.492s   | Bash: Clone template repository to temp directory
4    | 00:25.632 | 2.747s   | Bash: Batch sync and stage all changes
5    | 00:31.720 | 0.536s   | Bash: Show staged changes and check for differences
6    | 01:00.237 | -        | WAIT: User confirms push to template main
7    | 01:02.413 | 1.676s   | Bash: Commit and push changes to template repository
-----|-----------|----------|----------------------------------
END  | 01:04.089 | -        | Total elapsed: 1m 04.089s

Command execution time: 13.703s (21.4%)
AI/User decision time: 50.386s (78.6%)
```

**Breakdown:**
- Tool execution times from `duration` field in post events
- Wait times calculated from gaps between tool calls (AI processing + user input)
- Elapsed times reset to start from first target command tool call
- Excludes opt-cmd overhead (setup and reporting steps)
- No analysis, no recommendations, just raw data from target command only
