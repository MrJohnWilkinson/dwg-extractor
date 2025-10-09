# Claude Code Project Template

A production-ready template for building AI-powered software projects with automated development workflow, GitHub integration, and intelligent slash commands.

## What Is This?

This template provides everything you need to start a new software project with AI-first development capabilities:

- **AI Developer Workflow (ADW)**: Automatically process GitHub issues from classification to pull request
- **Claude Code Integration**: Enhanced with custom slash commands and hooks for consistent development
- **Production Infrastructure**: Logging, monitoring, scripts, and automation built-in
- **Multi-Language Support**: Infrastructure works with Python, Node.js, Go, Rust, or any language
- **Zero Application Code**: Clean slate for your project while preserving powerful automation

## Key Features

### 1. Automated Development Workflow

Create a GitHub issue, and ADW automatically:
- Classifies it (bug/feature/chore)
- Generates an implementation plan
- Implements the solution with Claude Code
- Creates commits and a pull request

```bash
# Process any GitHub issue automatically
cd adws
uv run adw_plan_build.py 123
```

### 2. Intelligent Slash Commands

Built-in commands for common development tasks:

```bash
claude /bug          # Plan and fix bugs
claude /feature      # Design and implement features
claude /chore        # Handle maintenance tasks
claude /implement    # Execute implementation plans
claude /commit       # Create semantic commits
claude /pull_request # Generate PRs with summaries
```

### 3. Extensible Hooks System

Customize Claude Code behavior with Python hooks:
- Pre/post tool use logging
- Custom notifications
- LLM integrations (Anthropic, OpenAI)
- Workflow lifecycle management

### 4. Production-Ready Scripts

Utilities for deployment and operations:
- Application startup/shutdown
- Webhook tunneling for local development
- Environment setup helpers
- GitHub utilities

## Quick Start

### Prerequisites

Install required tools:

```bash
# GitHub CLI
brew install gh  # macOS
# or: sudo apt install gh  # Ubuntu/Debian
# or: winget install --id GitHub.cli  # Windows

gh auth login

# Claude Code CLI
# Follow: https://docs.anthropic.com/en/docs/claude-code

# Python dependency manager (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

### Setup Your Project

1. **Clone this template**
   ```bash
   git clone <template-url> my-new-project
   cd my-new-project
   ```

2. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your values:
   # - ANTHROPIC_API_KEY (from https://console.anthropic.com/)
   # - GITHUB_REPO_URL (your repository URL)
   ```

3. **Initialize your repository**
   ```bash
   git remote remove origin
   git remote add origin https://github.com/your-username/your-new-repo.git
   git push -u origin main
   ```

4. **Build your application**

   See [TEMPLATE_GUIDE.md](./TEMPLATE_GUIDE.md) for detailed examples of different project types:
   - Python web apps (FastAPI/Flask)
   - TypeScript/React apps
   - CLI tools
   - Node.js servers
   - And more...

### Your First ADW Workflow

1. **Create a GitHub issue**
   ```bash
   gh issue create --title "Add user authentication" \
     --body "Implement JWT-based auth with login/logout endpoints"
   ```

2. **Let ADW handle it**
   ```bash
   # Option 1: Manual processing
   cd adws
   uv run adw_plan_build.py 1

   # Option 2: Automatic monitoring
   uv run trigger_cron.py  # Polls every 20 seconds

   # Option 3: Webhook (instant)
   uv run trigger_webhook.py
   ```

3. **Review the pull request**
   ```bash
   gh pr view
   gh pr diff
   gh pr merge
   ```

## Project Structure

```
.
├── .claude/
│   ├── commands/           # Slash commands (/bug, /feature, /commit, etc.)
│   ├── hooks/              # Pre/post tool use hooks
│   └── settings.json       # Claude Code configuration
├── adws/                   # AI Developer Workflow system
│   ├── adw_plan_build.py   # Main workflow orchestrator
│   ├── agent.py            # Claude Code CLI integration
│   ├── github.py           # GitHub API operations
│   ├── trigger_cron.py     # Polling-based monitoring
│   └── trigger_webhook.py  # Webhook-based monitoring
├── ai_docs/                # AI/LLM reference documentation
├── app/                    # Your application code goes here
│   └── README.md           # Application structure guidance
├── scripts/                # Utility scripts
│   ├── start.sh            # Application startup (customize this)
│   ├── stop_apps.sh        # Application shutdown
│   └── ...                 # GitHub and webhook utilities
├── specs/                  # Implementation plans and specifications
│   └── README.md           # Spec templates and examples
├── .env.sample             # Environment variable template
├── .gitignore              # Multi-language git ignore patterns
├── README.md               # This file
└── TEMPLATE_GUIDE.md       # Comprehensive usage guide
```

## Documentation

- **[TEMPLATE_GUIDE.md](./TEMPLATE_GUIDE.md)** - Comprehensive guide with:
  - Detailed infrastructure component documentation
  - Step-by-step project setup tutorials
  - Project type examples (web apps, APIs, CLI tools)
  - Customization instructions
  - ADW workflow tutorials
  - Troubleshooting guide

- **[adws/README.md](./adws/README.md)** - ADW system documentation:
  - Script usage guide
  - Workflow examples
  - Configuration options
  - Debugging tips

- **[app/README.md](./app/README.md)** - Application structure guidance

- **[specs/README.md](./specs/README.md)** - Specification templates

## Environment Configuration

Required environment variables in `.env`:

```bash
# Required for Claude Code
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Required for ADW
GITHUB_REPO_URL=https://github.com/owner/repo

# Optional (only if using different account than 'gh auth login')
GITHUB_PAT=ghp_xxxxx

# Optional features
E2B_API_KEY=xxxxx                              # Cloud sandboxing
CLOUDFLARED_TUNNEL_TOKEN=xxxxx                 # Webhook tunneling
CLAUDE_CODE_PATH=claude                        # Custom Claude path
CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true  # Directory management
```

See [TEMPLATE_GUIDE.md - Environment Configuration](./TEMPLATE_GUIDE.md#environment-configuration) for details.

## Common Tasks

### Run ADW on an Issue
```bash
cd adws
uv run adw_plan_build.py <issue_number>
```

### Enable Automatic Processing
```bash
cd adws
uv run trigger_cron.py  # Polls GitHub every 20 seconds
```

### Set Up Webhooks (Instant Processing)
```bash
cd adws
uv run trigger_webhook.py  # Start server

# In another terminal (for local development)
../scripts/expose_webhook.sh  # Expose to internet
```

### Use Slash Commands
```bash
claude /feature         # Plan a new feature
claude /bug             # Fix a bug
claude /implement @specs/my-plan.md  # Execute a plan
claude /commit          # Create semantic commit
claude /pull_request    # Generate PR
```

### Start Your Application
```bash
./scripts/start.sh      # After customizing for your app
```

## Examples

### Python FastAPI App

```bash
# Create structure
mkdir -p app/src/api app/tests
touch app/src/main.py app/pyproject.toml

# Update scripts/start.sh
echo "cd app && uv run uvicorn src.main:app --reload" > scripts/start.sh

# Start development
./scripts/start.sh
```

### TypeScript React App

```bash
# Create structure
mkdir -p app/src/components app/public
touch app/package.json app/tsconfig.json app/vite.config.ts

# Update scripts/start.sh
echo "cd app && npm install && npm run dev" > scripts/start.sh

# Start development
./scripts/start.sh
```

See [TEMPLATE_GUIDE.md - Project Type Examples](./TEMPLATE_GUIDE.md#project-type-examples) for more.

## Customization

### Add a Custom Slash Command

Create `.claude/commands/my_command.md`:
```markdown
My custom command description and instructions for Claude Code.
```

Use it:
```bash
claude /my_command
```

### Customize ADW Behavior

Edit files in `adws/`:
- `agent.py` - Change model, timeout, or agent behavior
- `trigger_cron.py` - Modify polling logic
- `trigger_webhook.py` - Add custom webhook handlers

### Add Custom Hooks

Edit `.claude/hooks/*.py` to add:
- Notifications (Slack, email, etc.)
- Custom logging
- External integrations
- Validation rules

See [TEMPLATE_GUIDE.md - Customization Guide](./TEMPLATE_GUIDE.md#customization-guide) for details.

## Troubleshooting

### Claude Code not found
```bash
which claude  # Check if installed
# Install from: https://docs.anthropic.com/en/docs/claude-code

# Or specify path in .env
echo "CLAUDE_CODE_PATH=/full/path/to/claude" >> .env
```

### GitHub authentication failed
```bash
gh auth status  # Check status
gh auth login   # Re-authenticate
```

### ADW not processing issues
```bash
# Check environment
env | grep -E "(GITHUB|ANTHROPIC)"

# Manually trigger
cd adws
uv run adw_plan_build.py <issue_number>
```

See [TEMPLATE_GUIDE.md - Troubleshooting](./TEMPLATE_GUIDE.md#troubleshooting) for complete guide.

## Contributing

This template is designed to evolve with your needs:

1. **Customize for your project** - Modify infrastructure components
2. **Improve and extend** - Add features that help your workflow
3. **Share improvements** - Submit PRs to benefit other users

## Resources

- **Claude Code Docs**: https://docs.anthropic.com/en/docs/claude-code
- **GitHub CLI Manual**: https://cli.github.com/manual/
- **uv Documentation**: https://github.com/astral-sh/uv
- **Anthropic API**: https://console.anthropic.com/

## License

This template is provided as-is for use in your projects. Customize freely.

## Next Steps

1. Read [TEMPLATE_GUIDE.md](./TEMPLATE_GUIDE.md) for comprehensive setup instructions
2. Configure your `.env` file
3. Create your application in `app/`
4. Create your first GitHub issue
5. Let ADW automate your development workflow

**Happy building with AI-powered development!**
