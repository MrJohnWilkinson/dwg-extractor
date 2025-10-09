# Claude Code Project Template - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [What This Template Provides](#what-this-template-provides)
3. [Infrastructure Components](#infrastructure-components)
4. [Quick Start](#quick-start)
5. [Starting Your First Project](#starting-your-first-project)
6. [Project Type Examples](#project-type-examples)
7. [Customization Guide](#customization-guide)
8. [ADW Workflow Tutorial](#adw-workflow-tutorial)
9. [Environment Configuration](#environment-configuration)
10. [Troubleshooting](#troubleshooting)

## Overview

This template provides a production-ready foundation for building AI-powered software projects with Claude Code. It includes a complete AI Developer Workflow (ADW) system that automates the entire software development lifecycle from GitHub issue to pull request.

### Key Benefits
- **AI-First Development**: Automated planning and implementation using Claude Code
- **GitHub Integration**: Seamless issue-to-PR workflow with automatic branch management
- **Quality Automation**: Slash commands for consistent development practices
- **Extensible Hooks**: Customizable behavior for Claude Code interactions
- **Production-Ready Infrastructure**: Logging, monitoring, and deployment helpers included
- **Multi-Language Support**: Infrastructure works with any programming language

## What This Template Provides

### 1. AI Developer Workflow (ADW) System
Located in `adws/`, this system automatically:
- Classifies GitHub issues (bug/feature/chore)
- Generates implementation plans
- Implements solutions using Claude Code
- Creates commits and pull requests
- Manages branch lifecycle

### 2. Claude Code Slash Commands
Located in `.claude/commands/`, these provide:
- `/bug` - Plan and implement bug fixes
- `/feature` - Plan and implement new features
- `/chore` - Plan and implement maintenance tasks
- `/implement` - Execute implementation plans
- `/commit` - Create semantic git commits
- `/pull_request` - Generate pull requests
- Plus utilities: `/classify_issue`, `/generate_branch_name`, `/find_plan_file`, etc.

### 3. Claude Code Hooks
Located in `.claude/hooks/`, these enhance Claude Code with:
- Pre/post tool use logging
- Notifications and status updates
- Custom LLM integrations (Anthropic, OpenAI)
- Workflow lifecycle management

### 4. Utility Scripts
Located in `scripts/`, providing:
- `start.sh` - Application startup (template, customize for your app)
- `stop_apps.sh` - Graceful application shutdown
- `copy_dot_env.sh` - Environment setup helper
- `expose_webhook.sh` - Webhook tunneling for local development
- GitHub utilities: `clear_issue_comments.sh`, `delete_pr.sh`

### 5. Documentation
Located in `ai_docs/`, including:
- Claude Code CLI reference
- Anthropic and OpenAI API quick starts
- SDK documentation
- E2B sandbox integration guide

## Infrastructure Components

### Claude Code Commands (`.claude/commands/`)

Each command is a markdown file that contains prompts for Claude Code:

- **Issue Management**
  - `bug.md` - Analyze and fix bugs
  - `feature.md` - Design and implement features
  - `chore.md` - Handle maintenance tasks
  - `classify_issue.md` - Automatically categorize issues

- **Development Workflow**
  - `implement.md` - Execute implementation plans
  - `commit.md` - Create semantic commits
  - `pull_request.md` - Generate PRs with summaries

- **Utilities**
  - `generate_branch_name.md` - Create semantic branch names
  - `find_plan_file.md` - Locate planning documents
  - `tools.md` - List available tools
  - `prime.md` - Initialize Claude Code context
  - `start.md` - Quick start guide

### Hooks System (`.claude/hooks/`)

Python scripts that execute at key points in Claude Code's lifecycle:

- `pre_tool_use.py` - Runs before each tool execution
- `post_tool_use.py` - Runs after each tool execution
- `notification.py` - Sends notifications on events
- `stop.py` - Cleanup when Claude Code stops
- `subagent_stop.py` - Cleanup when sub-agents stop

**Utilities** (`utils/`):
- `constants.py` - Shared configuration
- `llm/anth.py` - Anthropic API integration
- `llm/oai.py` - OpenAI API integration

### ADW Scripts (`adws/`)

Core automation system:

- `adw_plan_build.py` - Main workflow orchestrator (plan → implement → PR)
- `agent.py` - Claude Code CLI integration
- `github.py` - GitHub API operations
- `data_types.py` - Type-safe data models
- `utils.py` - Shared utilities
- `trigger_cron.py` - Polling-based issue monitoring
- `trigger_webhook.py` - Webhook-based issue monitoring
- `health_check.py` - System health monitoring

## Quick Start

### Prerequisites

1. **GitHub CLI**
   ```bash
   # macOS
   brew install gh

   # Ubuntu/Debian
   sudo apt install gh

   # Windows
   winget install --id GitHub.cli

   # Authenticate
   gh auth login
   ```

2. **Claude Code CLI**
   Follow instructions at https://docs.anthropic.com/en/docs/claude-code

3. **Python (uv)**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

### Initial Setup

1. **Clone this template**
   ```bash
   git clone <your-template-repo-url> my-new-project
   cd my-new-project
   ```

2. **Set up environment variables**
   ```bash
   # Copy and edit the environment template
   cp .env.sample .env

   # Edit .env with your values
   # Required:
   # - ANTHROPIC_API_KEY (from https://console.anthropic.com/)
   # - GITHUB_REPO_URL (your repo URL)
   # Optional:
   # - GITHUB_PAT (only if using different account than gh auth)
   # - E2B_API_KEY (for cloud sandboxing)
   # - CLOUDFLARED_TUNNEL_TOKEN (for webhook tunneling)
   ```

3. **Test the infrastructure**
   ```bash
   # Verify Claude Code works
   claude --version

   # Test a slash command
   claude /tools

   # Check ADW system
   cd adws
   uv run python -c "import agent; print('ADW ready')"
   ```

## Starting Your First Project

### Example: Creating a Python Web Application

Let's walk through creating a FastAPI web application using this template.

#### Step 1: Set Up Your Repository

```bash
# Initialize your new project
git remote remove origin  # Remove template origin
git remote add origin https://github.com/your-username/your-new-repo.git

# Update .env with your repo URL
echo "GITHUB_REPO_URL=https://github.com/your-username/your-new-repo" >> .env
```

#### Step 2: Create Your Application Structure

```bash
# Create FastAPI app structure
mkdir -p app/src/api app/src/models app/src/services
touch app/src/__init__.py
touch app/src/main.py
```

Create `app/src/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="My Application")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

#### Step 3: Set Up Dependencies

Create `app/pyproject.toml`:
```toml
[project]
name = "my-application"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Step 4: Update start.sh

Edit `scripts/start.sh` to start your application:
```bash
#!/bin/bash

# Start FastAPI application
echo "Starting FastAPI application..."
cd app
uv run uvicorn src.main:app --reload --port 8000 &
APP_PID=$!
cd ..

# Wait for termination
wait $APP_PID
```

#### Step 5: Create Your First Issue Using ADW

```bash
# Create a GitHub issue for a new feature
gh issue create --title "Add user authentication" --body "Implement JWT-based authentication"

# Get the issue number (e.g., #1)
gh issue list

# Process the issue with ADW
cd adws
uv run adw_plan_build.py 1
```

The ADW system will:
1. Read the issue
2. Create a feature branch
3. Generate an implementation plan
4. Implement the authentication system
5. Create a pull request

#### Step 6: Review and Merge

```bash
# View the generated PR
gh pr view

# Review the changes
gh pr diff

# Merge when ready
gh pr merge
```

## Project Type Examples

### Python Web Application (FastAPI/Flask)

**Directory Structure:**
```
app/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   │   └── user.py
│   └── services/
│       └── database.py
├── tests/
│   └── test_api.py
├── pyproject.toml
└── .env.sample
```

**start.sh snippet:**
```bash
cd app
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### TypeScript/React Web App

**Directory Structure:**
```
app/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**start.sh snippet:**
```bash
cd app
npm install
npm run dev
```

### Python CLI Tool

**Directory Structure:**
```
app/
├── src/
│   ├── __init__.py
│   ├── cli.py
│   └── commands/
│       ├── init.py
│       └── process.py
├── tests/
├── pyproject.toml
└── README.md
```

**start.sh snippet:**
```bash
cd app
uv run python -m src.cli "$@"
```

### Node.js API Server

**Directory Structure:**
```
app/
├── src/
│   ├── index.ts
│   ├── routes/
│   ├── controllers/
│   └── middleware/
├── package.json
└── tsconfig.json
```

**start.sh snippet:**
```bash
cd app
npm install
npm run start
```

### Single-File Script

**Directory Structure:**
```
app/
├── main.py  # or main.js, main.go, etc.
├── requirements.txt  # or package.json, go.mod, etc.
└── README.md
```

**start.sh snippet:**
```bash
cd app
uv run python main.py
```

## Customization Guide

### Customizing Slash Commands

Slash commands are markdown files in `.claude/commands/`. To create a new command:

1. Create a new `.md` file: `.claude/commands/my_command.md`
2. Write the prompt for Claude Code
3. Use it: `claude /my_command`

**Example** - Create `.claude/commands/test.md`:
```markdown
Run all tests in the project and report the results.

1. Find all test files
2. Run the test suite
3. Report failures with details
4. Suggest fixes for any failures
```

Usage:
```bash
claude /test
```

### Customizing Hooks

Hooks are Python scripts that run at specific lifecycle events. To modify:

1. Edit the relevant hook in `.claude/hooks/`
2. Hooks receive event data via stdin as JSON
3. Hooks can output to stdout/stderr

**Example** - Add Slack notifications to `post_tool_use.py`:
```python
import os
import json
import requests

def send_slack_notification(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={"text": message})

# Add to the hook
event = json.loads(sys.stdin.read())
if event.get("tool_name") == "Write":
    send_slack_notification(f"File written: {event['parameters']['file_path']}")
```

### Extending ADW

To add custom ADW functionality:

1. **Add new triggers** - Modify `trigger_cron.py` or `trigger_webhook.py`
2. **Custom agents** - Create new agents in `agent.py`
3. **Issue processing** - Extend `adw_plan_build.py`

**Example** - Add custom issue labels:
```python
# In adw_plan_build.py, after classification
if issue_command == "/feature":
    github.add_labels(issue_number, ["enhancement", "ai-generated"])
```

### Multi-Language Support

While the infrastructure is Python-based, your application can use any language:

1. **Update start.sh** for your language's runtime
2. **Add language-specific .gitignore** entries
3. **Update app/README.md** with language-specific guidance

The ADW system and Claude Code work with any language.

## ADW Workflow Tutorial

### Understanding the ADW Workflow

ADW (AI Developer Workflow) automates the complete software development lifecycle:

```
GitHub Issue → Classification → Planning → Implementation → PR → Review → Merge
```

### Step-by-Step ADW Example

Let's process a real issue from start to finish.

#### 1. Create a GitHub Issue

```bash
gh issue create \
  --title "Add rate limiting to API endpoints" \
  --body "Implement rate limiting to prevent API abuse. Use 100 requests per minute per IP."
```

Issue created: #42

#### 2. Manual Processing (Option A)

```bash
cd adws
uv run adw_plan_build.py 42
```

#### 3. Automatic Processing (Option B)

```bash
# Start cron-based monitoring (polls every 20 seconds)
cd adws
uv run trigger_cron.py
```

Or with webhooks (instant):
```bash
cd adws
uv run trigger_webhook.py

# In another terminal, expose to internet
../scripts/expose_webhook.sh
```

#### 4. ADW Execution Flow

**Classification Phase:**
```
ADW ID: a1b2c3d4
Analyzing issue #42...
Classification: /feature
Creating branch: feat-42-a1b2c3d4-add-rate-limiting-api-endpoints
```

**Planning Phase:**
```
Running sdlc_planner agent...
Generating plan: specs/add-rate-limiting-api-endpoints.md
Plan includes:
  - Install rate limiting library
  - Create middleware
  - Add tests
  - Update documentation
```

**Implementation Phase:**
```
Running sdlc_implementor agent...
Implementing plan from specs/add-rate-limiting-api-endpoints.md
Changes:
  - app/src/middleware/rate_limit.py (new)
  - app/src/main.py (modified)
  - app/tests/test_rate_limit.py (new)
  - app/requirements.txt (modified)
```

**Integration Phase:**
```
Creating commit...
Creating pull request...
PR created: https://github.com/owner/repo/pull/43
```

#### 5. Review the Results

```bash
# View the PR
gh pr view 43

# Check the diff
gh pr diff 43

# Review plan file
cat specs/add-rate-limiting-api-endpoints.md

# Check agent outputs
cat agents/a1b2c3d4/sdlc_planner/raw_output.jsonl | tail -1 | jq .
cat agents/a1b2c3d4/sdlc_implementor/raw_output.jsonl | tail -1 | jq .
```

#### 6. Trigger Re-processing

If you need to re-run ADW on an issue:
```bash
# Comment "adw" on the issue
gh issue comment 42 --body "adw"

# Or run manually
cd adws
uv run adw_plan_build.py 42
```

### ADW Configuration

#### Trigger Methods

**1. Manual (adw_plan_build.py)**
- Run on-demand for specific issues
- Best for: Testing, one-off tasks
- Usage: `uv run adw_plan_build.py <issue_number>`

**2. Cron (trigger_cron.py)**
- Polls GitHub every 20 seconds
- Processes new issues and "adw" comments
- Best for: Low-traffic repos, no webhook access
- Usage: `uv run trigger_cron.py`

**3. Webhook (trigger_webhook.py)**
- Instant processing on issue events
- Requires public URL (use expose_webhook.sh for local dev)
- Best for: Production, high-traffic repos
- Usage: `uv run trigger_webhook.py`

#### Issue Triggers

ADW processes an issue when:
1. Issue has no comments (brand new)
2. Latest comment is exactly "adw"
3. Webhook receives issue creation event

### Advanced ADW Usage

#### Custom Classification

Edit `.claude/commands/classify_issue.md` to change classification logic.

#### Multiple Agent Passes

Re-run implementation if first attempt needs improvement:
```bash
cd adws
uv run adw_plan_build.py 42  # First pass
# Review results
uv run adw_plan_build.py 42  # Second pass (refines existing work)
```

#### Skip Planning

If you already have a plan file:
```bash
claude /implement @specs/my-existing-plan.md
```

## Environment Configuration

### Required Variables

```bash
# Anthropic API Key (required for Claude Code)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# GitHub Repository URL (required for ADW)
GITHUB_REPO_URL=https://github.com/owner/repo
```

### Optional Variables

```bash
# GitHub Personal Access Token
# Only needed if using different account than 'gh auth login'
GITHUB_PAT=ghp_xxxxx

# Claude Code executable path
# Default: "claude" (searches PATH)
CLAUDE_CODE_PATH=/usr/local/bin/claude

# E2B API Key (for cloud sandboxing)
E2B_API_KEY=xxxxx

# Cloudflare Tunnel Token (for webhook exposure)
CLOUDFLARED_TUNNEL_TOKEN=xxxxx

# Claude Code behavior
CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true
```

### Application-Specific Variables

Add your own variables to `.env.sample` and `.env`:

```bash
# Database
DATABASE_URL=postgresql://localhost/mydb

# API Keys
STRIPE_API_KEY=sk_test_xxxxx
SENDGRID_API_KEY=SG.xxxxx

# Feature Flags
ENABLE_ANALYTICS=true
DEBUG_MODE=false
```

### Loading Environment Variables

**In Python:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
```

**In Node.js:**
```javascript
import 'dotenv/config';
const apiKey = process.env.ANTHROPIC_API_KEY;
```

**In shell scripts:**
```bash
source .env
echo $ANTHROPIC_API_KEY
```

## Troubleshooting

### Claude Code Issues

**Problem: "claude: command not found"**
```bash
# Check if installed
which claude

# Reinstall from https://docs.anthropic.com/en/docs/claude-code

# Or specify path in .env
echo "CLAUDE_CODE_PATH=/full/path/to/claude" >> .env
```

**Problem: "API key not configured"**
```bash
# Check environment
env | grep ANTHROPIC_API_KEY

# Add to .env
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" >> .env

# Load it
source .env
```

### ADW Issues

**Problem: "GitHub CLI not authenticated"**
```bash
# Check auth status
gh auth status

# Login
gh auth login

# Verify
gh repo view
```

**Problem: "Issue not being processed"**
```bash
# Check ADW is running
ps aux | grep trigger

# Check issue status
gh issue view 42

# Manually trigger
cd adws
uv run adw_plan_build.py 42
```

**Problem: "Agent execution failed"**
```bash
# Check agent output
cd agents/<adw_id>/sdlc_planner
cat raw_output.jsonl | tail -1 | jq .

# Look for errors
cd agents/<adw_id>/sdlc_implementor
cat raw_output.jsonl | grep -i error
```

### Git Issues

**Problem: "Branch already exists"**
```bash
# Delete old branch
git branch -D feat-42-xxxxx-branch-name
git push origin --delete feat-42-xxxxx-branch-name

# Re-run ADW
cd adws
uv run adw_plan_build.py 42
```

**Problem: "Merge conflicts"**
```bash
# Update branch
git checkout feat-42-xxxxx-branch-name
git rebase main

# Resolve conflicts
# ... edit files ...
git add .
git rebase --continue
git push --force-with-lease
```

### Hook Issues

**Problem: "Hook failed to execute"**
```bash
# Check hook permissions
ls -la .claude/hooks/*.py

# Make executable
chmod +x .claude/hooks/*.py

# Test hook manually
echo '{"tool_name":"test"}' | python .claude/hooks/post_tool_use.py
```

**Problem: "Missing Python dependencies in hooks"**
```bash
# Install hook dependencies
cd .claude/hooks
uv pip install anthropic openai requests
```

### Webhook Issues

**Problem: "Webhook not receiving events"**
```bash
# Check server is running
curl http://localhost:8001/health

# Check GitHub webhook configuration
gh api repos/:owner/:repo/hooks

# Check webhook logs
# Look for POST requests to /gh-webhook
```

**Problem: "Cloudflare tunnel not working"**
```bash
# Check tunnel is running
ps aux | grep cloudflared

# Restart tunnel
../scripts/expose_webhook.sh

# Verify public URL
curl https://your-tunnel-url.trycloudflare.com/health
```

### Common Error Messages

**"No such file or directory: specs/..."**
- The plan file wasn't created. Check planner agent output.
- Solution: Run planning phase again or create plan manually.

**"GitHub API rate limit exceeded"**
- You've hit GitHub's rate limit (5000 requests/hour).
- Solution: Wait for rate limit reset or use authentication token.

**"Claude Code timeout"**
- Claude Code took too long to respond.
- Solution: Increase timeout in `agent.py` or simplify the task.

**"Branch protection rules prevent push"**
- Your repo requires PR reviews even for ADW.
- Solution: Configure branch protection to allow bot pushes or push to different branch.

### Getting Help

1. **Check Documentation**
   - This guide
   - `adws/README.md`
   - `ai_docs/` directory

2. **Check Logs**
   - Agent outputs: `agents/<adw_id>/*/raw_output.jsonl`
   - Webhook logs: stdout from `trigger_webhook.py`
   - Cron logs: stdout from `trigger_cron.py`

3. **Debug Mode**
   ```bash
   export ADW_DEBUG=true
   cd adws
   uv run adw_plan_build.py 42
   ```

4. **Community Resources**
   - Claude Code docs: https://docs.anthropic.com/en/docs/claude-code
   - Anthropic Discord: https://discord.gg/anthropic
   - GitHub Discussions: Create discussions in your repo

## Best Practices

### Development Workflow

1. **Use Descriptive Issue Titles**: ADW uses the title for branch and file names
2. **Write Detailed Issue Descriptions**: Better descriptions = better plans
3. **Review Plans Before Implementation**: Check `specs/*.md` before merging PRs
4. **Use Semantic Commit Messages**: ADW generates these automatically
5. **Keep Branches Short-Lived**: Merge PRs quickly to avoid conflicts

### Code Organization

1. **Keep Application Code in app/**: Separates infrastructure from application
2. **Document in specs/**: Store all planning documents
3. **Use .env for Configuration**: Never commit secrets
4. **Write Tests**: ADW can generate tests if you specify in issue
5. **Update Documentation**: Keep README.md current

### ADW Usage

1. **One Issue = One Feature**: Keep issues focused
2. **Use Labels**: Tag issues with priority/type
3. **Review Agent Output**: Check `agents/` directory after runs
4. **Monitor API Usage**: Claude Code and GitHub have rate limits
5. **Set Up Branch Protection**: Require reviews for ADW PRs

### Security

1. **Never Commit .env**: It's in .gitignore, but double-check
2. **Use Fine-Grained Tokens**: Minimal permissions for GitHub PAT
3. **Rotate Keys Regularly**: Update API keys periodically
4. **Review PRs Before Merge**: Even AI-generated code needs review
5. **Enable Branch Protection**: Prevent direct pushes to main

## Next Steps

1. **Explore the Infrastructure**
   ```bash
   # List slash commands
   ls .claude/commands/

   # Read ADW documentation
   cat adws/README.md

   # Check hook utilities
   ls .claude/hooks/utils/
   ```

2. **Create Your Application**
   - Follow examples in [Project Type Examples](#project-type-examples)
   - Customize `scripts/start.sh` for your app
   - Update `app/README.md` with your structure

3. **Set Up GitHub Integration**
   - Configure webhook or start cron monitoring
   - Create your first issue
   - Let ADW handle it end-to-end

4. **Customize for Your Needs**
   - Add custom slash commands
   - Modify hooks for notifications
   - Extend ADW with custom logic

5. **Build Something Amazing**
   - The infrastructure is ready
   - Focus on your application logic
   - Let AI handle the workflow

## Additional Resources

- **Claude Code Documentation**: https://docs.anthropic.com/en/docs/claude-code
- **GitHub CLI Documentation**: https://cli.github.com/manual/
- **uv Documentation**: https://github.com/astral-sh/uv
- **E2B Documentation**: https://e2b.dev/docs (for cloud sandboxing)

## Template Maintenance

This template is designed to be maintained independently of your application:

1. **Update ADW Scripts**: Pull updates from template repo
2. **Update Slash Commands**: Modify for your workflow
3. **Update Hooks**: Add custom behavior
4. **Update Documentation**: Keep guides current

## Contributing Back to Template

If you make improvements to the infrastructure:

1. Fork the template repository
2. Make your changes to infrastructure (not app-specific code)
3. Submit a PR with improvements
4. Help others benefit from your work

---

**You're ready to start!** Create your first issue and watch ADW automate your development workflow.
