---
description: Break down large documents into manageable single-session tasks
argument-hint: <file path to document>
---

# Breakdown Planning

Break down a large document (spec, report, or plan) into high-level tasks that can each be completed in a single work session day of work. The purpose is to have a 1 to 5 bullet point high level prompt, for each task, that can used to create a spec file with `/dev:feature`, `/dev:bug`, or `/dev:chore`.

## Purpose

Decompose or group tasks in plans, analysis reports, or feature specs into simple work units.  The work units should be described simply and should NOT be prescriptive.  The total work units in any breakdown must NOT be more than 5.  

**Each work unit must be:**
- Approximately a single day of work
- Self-contained (ie. each task should NOT need to reference another task for context)
- Have clear dependencies and ordering
- Assigned the appropriate command type (/dev:feature, /dev:bug, /dev:chore)
- Maximum 5 bullet points


## Instructions
1. **Use your thinking model**  Think hard.

1. **Read and Analyze** the input document thoroughly
   - Understand the overall scope and goals
   - Identify major components or phases
   - Note any existing task breakdowns or phases

2. **Identify Logical Work Units** that can be grouped or separated
   - Each task should take approx a day to complete
   - Tasks should have clear scope boundaries

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
<1-3 sentence summary of how the work is being broken down>

## Task Breakdown

### Task 1: <Task Title>
**Focus Area**: <General area/component being worked on, e.g., "Frontend chat interface", "Backend API layer", "Database schema">
**Suggested Command**: `/dev:feature` | `/dev:bug` | `/dev:chore`
**Complexity**: Simple | Medium | Complex
**Dependencies**: None | Task X must be completed first

**Description**:
<Clear description of what needs to be done in this task.  Keep this high level, using 1 to 5 bullet points.  Provide important files, but AVOID being too descriptive. Include:
- The main specific files or components affected
- Key functionality to implement/fix
- Clear scope boundaries

---

### Task 2: <Task Title>
**Focus Area**: <General area/component being worked on, e.g., "Frontend chat interface", "Backend API layer", "Database schema">
**Suggested Command**: `/dev:feature` | `/dev:bug` | `/dev:chore`
**Complexity**: Simple | Medium | Complex
**Dependencies**: None | Task X must be completed first

**Description**:
<Clear description of what needs to be done in this task.  Keep this high level, using 1 to 5 bullet points.  Provide important files, but AVOID being too descriptive. Include:
- The main specific files or components affected
- Key functionality to implement/fix
- Clear scope boundaries

---

<Repeat for remaining tasks (up to 5 total)...>

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
```md
# Breakdown: Implement Goals System

## Source Document
- **Path**: specs/042-implement-goals-system.md
- **Type**: spec
- **Original Scope**: Comprehensive goals tracking feature with milestones, progress tracking, and user-defined success criteria

## Overview
Breaking down the goals system into 5 sequential tasks, starting with data layer and backend logic, then building frontend components, and finishing with end-to-end validation. Tasks 3 and 4 can be parallelized after Task 2 is complete.

## Task Breakdown

### Task 1: Database Schema and Backend Models
**Focus Area**: Backend data layer
**Suggested Command**: `/dev:chore`
**Complexity**: Medium
**Dependencies**: None

**Description**:
- Create database migration for goals tables (goals, milestones, progress)
- Implement backend models with validation logic
- Add unit tests for model validation

---

### Task 2: API Endpoints for Goal Management
**Focus Area**: Backend API layer
**Suggested Command**: `/dev:feature`
**Complexity**: Medium
**Dependencies**: Task 1 must be completed first

**Description**:
- Build CRUD endpoints for goals (`/api/goals`)
- Implement goal evaluation logic
- Add API integration tests

---

### Task 3: Frontend Goal Creation Interface
**Focus Area**: Frontend goals components
**Suggested Command**: `/dev:feature`
**Complexity**: Medium
**Dependencies**: Task 2 must be completed first

**Description**:
- Create goal creation form with validation
- Implement milestone input components
- Connect to backend API endpoints

---

### Task 4: Frontend Goal Display and Progress Tracking
**Focus Area**: Frontend goals components
**Suggested Command**: `/dev:feature`
**Complexity**: Simple
**Dependencies**: Task 2 must be completed first

**Description**:
- Build goal list view with filtering
- Implement progress visualization components
- Add real-time progress updates

---

### Task 5: End-to-End Testing and Validation
**Focus Area**: Testing infrastructure
**Suggested Command**: `/dev:chore`
**Complexity**: Simple
**Dependencies**: Tasks 3 and 4 must be completed first

**Description**:
- Create E2E tests for complete goal workflow
- Test edge cases and error handling
- Validate performance with realistic data volumes

## Execution Order
1. Task 1 (no dependencies)
2. Task 2 (depends on Task 1)
3. Tasks 3, 4 (can be done in parallel after Task 2)
4. Task 5 (final integration, depends on Tasks 3 and 4)

## Notes
The frontend tasks (3 and 4) can be parallelized after the API layer is complete. Consider deploying to staging after Task 4 to gather early user feedback before final testing phase.
```

### Example 2: Breaking Down an Analysis Report

**Original Document**: `ai_output/035-performance-optimization-analysis.md`

**Breakdown Result**:
```md
# Breakdown: Performance Optimization Analysis

## Source Document
- **Path**: ai_output/035-performance-optimization-analysis.md
- **Type**: report
- **Original Scope**: Analysis of performance bottlenecks across database queries, API responses, and frontend rendering

## Overview
Breaking down performance improvements into 4 parallel work streams that can mostly be executed independently, with caching layer dependent on database optimizations being complete.

## Task Breakdown

### Task 1: Fix N+1 Query Problem in Logs Endpoint
**Focus Area**: Backend API optimization
**Suggested Command**: `/dev:bug`
**Complexity**: Medium
**Dependencies**: None

**Description**:
- Identify all N+1 queries in logs API endpoint
- Implement eager loading for related models
- Add query performance tests

---

### Task 2: Implement Database Indexing Strategy
**Focus Area**: Database layer
**Suggested Command**: `/dev:chore`
**Complexity**: Simple
**Dependencies**: None

**Description**:
- Add indexes to frequently queried columns
- Create database migration for indexes
- Measure query performance improvements

---

### Task 3: Add Response Caching Layer
**Focus Area**: Backend caching infrastructure
**Suggested Command**: `/dev:feature`
**Complexity**: Medium
**Dependencies**: Tasks 1 and 2 must be completed first

**Description**:
- Implement Redis caching for API responses
- Add cache invalidation logic
- Configure cache TTL strategies

---

### Task 4: Optimize Frontend Rendering Performance
**Focus Area**: Frontend performance
**Suggested Command**: `/dev:bug`
**Complexity**: Medium
**Dependencies**: None

**Description**:
- Identify and fix unnecessary re-renders
- Implement component memoization
- Add performance monitoring

## Execution Order
1. Tasks 1, 2, 4 (can be done in parallel)
2. Task 3 (depends on Tasks 1 and 2)

## Notes
Tasks 1, 2, and 4 are independent and can be worked on simultaneously by different developers. Task 3 should wait for database optimizations to avoid caching inefficient queries.
```

## Document to Break Down
$ARGUMENTS

## Report
- Summarize the work you've just done in a concise bullet point list
- Include the path to the breakdown document you created
- List the number of tasks created and their complexity distribution
