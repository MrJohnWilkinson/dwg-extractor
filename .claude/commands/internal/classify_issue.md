---
description: Select appropriate command based on GitHub issue type
argument-hint: <github issue JSON>
model: opus
---

# Github Issue Command Selection

Based on the `Github Issue` below, follow the `Instructions` to select the appropriate command to execute based on the `Command Mapping`.

## Variables

GITHUB_ISSUE: $ARGUMENTS (required)

## Instructions

- Based on the details in the `Github Issue`, select the appropriate command to execute.
- Respond exclusively with '/' followed by the command to execute.
- Use the command mapping to help you decide which command to respond with.
- Think hard about the command to execute.

## Command Mapping

- Respond with `/dev:chore` if the issue is a chore.
- Respond with `/dev:bug` if the issue is a bug.
- Respond with `/dev:feature` if the issue is a feature.
- Respond with `0` if the issue isn't any of the above.
