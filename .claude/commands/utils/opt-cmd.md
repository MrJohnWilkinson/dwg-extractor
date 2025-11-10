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
- After command completes, read timing log from `logs/{session_id}/tool_timing.json`
- Display sequential timing table showing tool executions, notifications, and wait times
- No analysis, no recommendations, no optimizations - just raw timing data from hooks

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
   - Read timing log: `logs/{session_id}/tool_timing.json`
   - Parse timing entries:
     - `event: "pre"` - Tool call started
     - `event: "post"` - Tool call completed (includes duration)
     - `event: "notification"` - Claude waiting for user input
   - Calculate elapsed times from first timestamp
   - Output table format:
     ```
     TIMING REPORT
     =============
     Step | Elapsed   | Duration | Description
     -----|-----------|----------|----------------------------------
     1    | 00:00.000 | 0.012s   | Bash: date +%s.%N
     2    | 00:00.012 | 0.004s   | Read: command file
     3    | 00:00.016 | -        | WAIT: User confirmation
     4    | 00:15.234 | 1.368s   | Bash: git clone...
     ...
     END  | 01:23.456 | -        | Total elapsed: 1m 23.456s

     Command execution time: 4.548s (23.3%)
     AI/User decision time: 14.988s (76.7%)
     ```
   - Differentiate tool execution vs wait times
   - No analysis or recommendations - just raw timing data

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

Display timing report generated from automatic hook logs:

**Data Source:** `logs/{session_id}/tool_timing.json`

**Report Format:**

```
TIMING REPORT
=============

Step | Elapsed   | Duration | Description
-----|-----------|----------|----------------------------------
1    | 00:00.000 | 0.012s   | Bash: date +%s.%N
2    | 00:00.012 | 0.004s   | Read: update_repo_template.md
3    | 00:00.016 | -        | WAIT: User confirmation
4    | 00:15.234 | 1.368s   | Bash: git clone...
5    | 00:16.602 | 0.015s   | Bash: copy files
6    | 00:16.617 | 3.145s   | Bash: commit and push
7    | 00:19.762 | 0.008s   | Bash: cleanup
-----|-----------|----------|----------------------------------
END  | 00:19.770 | -        | Total elapsed: 19.770s

Command execution time: 4.552s (23.0%)
AI/User decision time: 15.218s (77.0%)
```

**Breakdown:**
- Tool execution times from `duration` field in post events
- Wait times calculated from gaps between tool post → notification → next tool pre
- Elapsed times calculated from first timestamp
- No analysis, no recommendations, just raw data from hooks
