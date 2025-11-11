# E2E Test Orchestrator

Orchestrate end-to-end (E2E) test execution by spawning sub-agents for each test scenario. This preserves the orchestrator's context window and allows testing files with many scenarios.

## Variables

e2e_test_file: $1 (required - relative path to test file, e.g., "tests/e2e/goal_standalone_page_scenarios.md")
test_name: Derived from test file name (e.g., "goal_standalone_page_scenarios.md" → "goal_standalone_page_scenarios")

## Orchestrator Role

**You are the orchestrator. Your responsibilities:**
1. Read and parse the test file
2. Detect scenarios (single or multiple)
3. Spawn one sub-agent per scenario (sequentially)
4. Aggregate results from all sub-agents
5. Return final JSON report

**DO NOT execute Playwright commands yourself.** Sub-agents handle all browser automation.

## Setup

Read and Execute `.claude/commands/prepare_app.md` now to prepare the application for testing.

## Instructions

### Step 1: Read and Parse Test File

- Read the `e2e_test_file`
- Identify if it contains:
  - **Multiple scenarios**: Look for headers like `## Scenario 1`, `## Scenario 2`, `# Scenario: Name`, etc.
  - **Single scenario**: No scenario markers, entire file is one test
- Extract each scenario's content including User Story, Test Steps, Success Criteria

### Step 2: Spawn Sub-Agents (Sequential)

For each scenario, spawn a sub-agent using the Task tool:

**Sub-Agent Prompt Template:**
```
Execute this E2E test scenario for the Activity Logger application using Playwright browser automation.

## Application Details
- URL: http://localhost:5173
- Services: Log server (8001), Backend API (8002), Frontend (5173)

## Scenario to Test
<paste the full scenario content here including User Story, Test Steps, Success Criteria>

## Execution Instructions
1. Initialize Playwright browser in HEADED mode for visibility
2. Navigate to http://localhost:5173
3. Execute each Test Step in order using Playwright MCP tools
4. Capture screenshots as specified in the test steps
5. Verify all Success Criteria
6. Allow time for async operations and element visibility
7. If any step fails, mark test as FAILED immediately with detailed error

## Screenshot Directory
Save all screenshots to:
.playwright-mcp/test_e2e/<test_name>/<scenario_name>/

Where:
- <test_name> = "goal_standalone_page_scenarios" (from test file name)
- <scenario_name> = "scenario_1" or descriptive name from scenario header

Example paths:
- .playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_1/01_initial_load.png
- .playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_1/02_modal_opened.png

## Error Reporting
If you encounter an error, report exactly which step failed:
- Format: "(Step X ❌) Failed to find element with selector 'activity-input' on page 'http://localhost:5173'"
- Include what was expected vs what actually happened

## Return Format
Return ONLY this JSON (no other text):
{
  "scenario_name": "Scenario 1: Initial Load",
  "status": "passed|failed",
  "screenshots": [
    ".playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_1/01_initial_load.png",
    ".playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_1/02_modal_opened.png"
  ],
  "error": null
}

Note: Set "error" to null if passed, or error description string if failed.
```

**Important:**
- Use `subagent_type="general-purpose"` for Task tool
- Spawn sub-agents **sequentially** (one at a time, not parallel)
- Wait for each sub-agent to complete before spawning the next
- Extract the JSON result from each sub-agent's response
- Unless you have already used more than 110000 tokens, don't stop due to token budget constraints.  Using sub-agents will mean your token budget should be plenty.  

### Step 3: Aggregate Results

After all sub-agents complete:
1. Collect all scenario results
2. Determine overall status:
   - "passed" if ALL scenarios passed
   - "failed" if ANY scenario failed
3. Combine into final JSON report

## Output Format

Return this JSON structure:

```json
{
  "test_file": "tests/e2e/goal_standalone_page_scenarios.md",
  "overall_status": "passed|failed",
  "total_scenarios": 3,
  "passed_scenarios": 2,
  "failed_scenarios": 1,
  "scenarios": [
    {
      "scenario_name": "Scenario 1: Initial Load",
      "status": "passed",
      "screenshots": [
        ".playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_1/01_initial_load.png",
        ".playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_1/02_navigation.png"
      ],
      "error": null
    },
    {
      "scenario_name": "Scenario 2: Create Goal",
      "status": "failed",
      "screenshots": [
        ".playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_2/01_modal_opened.png"
      ],
      "error": "(Step 3 ❌) Failed to find element with selector 'goal-submit-btn' on page 'http://localhost:5173'"
    },
    {
      "scenario_name": "Scenario 3: View Goals List",
      "status": "passed",
      "screenshots": [
        ".playwright-mcp/test_e2e/goal_standalone_page_scenarios/scenario_3/01_goals_list.png"
      ],
      "error": null
    }
  ]
}
```

## Example Usage

```bash
# Test file with single scenario
claude /test_e2e tests/e2e/activity_creation.md

# Test file with multiple scenarios
claude /test_e2e tests/e2e/goal_standalone_page_scenarios.md
```

## Notes

- **Context window preservation**: By using sub-agents, the orchestrator stays lightweight even with many scenarios
- **Sequential execution**: Prevents browser resource conflicts
- **Flexible format**: Supports both single-scenario and multi-scenario test files
- **Isolation**: Each scenario runs in fresh sub-agent context with clean state
