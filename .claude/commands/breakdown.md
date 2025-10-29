---
description: Break down large documents into manageable single-session tasks
argument-hint: <file path to document>
---

# Breakdown Planning

Break down a large document (spec, report, or plan) into high-level tasks that can each be completed in a single work session (2-4 hours). Each broken-down task can then have its own dedicated spec created using `/dev:feature`, `/dev:bug`, or `/dev:chore`.

## Purpose

This command helps decompose complex implementation plans, analysis reports, or feature specs into atomic, manageable work units. Instead of tackling a massive spec all at once, you break it into focused tasks that:

- Can be completed in a single work session (2-4 hours)
- Are self-contained enough to become their own spec
- Have clear dependencies and ordering
- Can be assigned appropriate command types (/dev:feature, /dev:bug, /dev:chore)

## Instructions
1. **Use yout thinking model**  Ultrathink.  

1. **Read and Analyze** the input document thoroughly
   - Understand the overall scope and goals
   - Identify major components or phases
   - Note any existing task breakdowns or phases

2. **Identify Logical Work Units** that can each become standalone tasks
   - Each task should take 2-4 hours to complete
   - Tasks should have clear boundaries and deliverables
   - Avoid tasks that are too granular (< 1 hour) or too broad (> 1 day)
   - Group related changes together (e.g., "Add backend endpoint + tests" not separate tasks)

3. **Determine Dependencies** between tasks
   - Which tasks must be completed before others?
   - Which tasks can be done in parallel?
   - Are there any blocking dependencies?

4. **Assess Complexity** for each task
   - **Simple**: Straightforward implementation, well-defined, minimal risk
   - **Medium**: Requires some research/design, moderate complexity
   - **Complex**: Significant unknowns, architectural decisions, high risk

5. **Recommend Appropriate Command** for each task
   - `/dev:feature` - Net new functionality or enhancement
   - `/dev:bug` - Fix defect or incorrect behavior
   - `/dev:chore` - Maintenance, refactoring, documentation, tooling

6. **Create Breakdown Document** using the Template below
   - Save to `ai_output/{original-filename}-breakdown.md`
   - Use clear, descriptive task titles
   - Include enough context so each task can stand alone

## Template

```md
# Breakdown: <Original Document Title>

## Source Document
- **Path**: <path/to/original/document.md>
- **Type**: <spec/report/plan>
- **Original Scope**: <brief description of what the original document covers>

## Overview
<1-2 sentence summary of how the work is being broken down>

## Task Breakdown

### Task 1: <Task Title>
**Suggested Command**: `/dev:feature` | `/dev:bug` | `/dev:chore`
**Complexity**: Simple | Medium | Complex
**Estimated Time**: 2-4 hours
**Dependencies**: None | Task X must be completed first

**Description**:
<Clear description of what needs to be done in this task. Include:
- Specific files or components affected
- Key functionality to implement/fix
- Testing requirements
- Any special considerations>

**Deliverables**:
- <Specific output or completion criteria>
- <What should be working when this task is done>

---

### Task 2: <Task Title>
**Suggested Command**: `/dev:feature` | `/dev:bug` | `/dev:chore`
**Complexity**: Simple | Medium | Complex
**Estimated Time**: 2-4 hours
**Dependencies**: Task 1

**Description**:
<Task description>

**Deliverables**:
- <Deliverable 1>
- <Deliverable 2>

---

<Repeat for all tasks...>

## Execution Order
1. Task 1 (no dependencies)
2. Task 2 (depends on Task 1)
3. Tasks 3, 4, 5 (can be done in parallel after Task 2)
4. Task 6 (final integration, depends on all previous)

## Notes
<Any additional context, considerations, or recommendations for executing these tasks>
```

## Examples

### Example 1: Breaking Down a Large Feature Spec

**Original Document**: `specs/042-implement-goals-system.md` (comprehensive goals feature)

**Breakdown Result**:
```
Task 1: Database Schema and Migration (2-3 hours, Medium complexity)
Task 2: Backend Models and Validation (2-3 hours, Simple complexity)
Task 3: API Endpoints - CRUD Operations (3-4 hours, Medium complexity)
Task 4: Goal Evaluation Engine (3-4 hours, Complex complexity)
Task 5: Frontend Goal Creation UI (3-4 hours, Medium complexity)
Task 6: Frontend Goal Display and Progress (2-3 hours, Simple complexity)
Task 7: Integration Tests and E2E Validation (2-3 hours, Medium complexity)
```

### Example 2: Breaking Down an Analysis Report

**Original Document**: `ai_output/035-performance-optimization-analysis.md`

**Breakdown Result**:
```
Task 1: Fix N+1 Query Problem in Logs Endpoint (2-3 hours, Medium complexity) - /dev:bug
Task 2: Implement Database Indexing Strategy (2-3 hours, Simple complexity) - /dev:chore
Task 3: Add Response Caching Layer (3-4 hours, Medium complexity) - /dev:feature
Task 4: Optimize Frontend Rendering (2-3 hours, Medium complexity) - /dev:bug
```

## Document to Break Down
$ARGUMENTS

## Report
- Summarize the work you've just done in a concise bullet point list
- Include the path to the breakdown document you created
- List the number of tasks created and their complexity distribution
