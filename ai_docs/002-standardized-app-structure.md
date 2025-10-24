# TAC Standardized Application Structure

## Executive Summary
The TAC course follows a highly consistent, modular application structure across all projects. The standard pattern uses an `app/` directory split into `client/` and `server/`, complemented by an `adws/` directory for AI Developer Workflows, and supporting directories for scripts, specs, and documentation. This structure scales from simple projects to complex multi-application systems.

## Table Summary

| Directory | Purpose | Found In | Required | Key Files |
|-----------|---------|----------|----------|-----------|
| `app/` | Main application container | tac-2 to tac-8 | Yes | - |
| `app/client/` | Frontend Vite + TypeScript app | tac-2 to tac-8 | Yes | `vite.config.ts`, `package.json`, `index.html` |
| `app/server/` | Backend Python FastAPI server | tac-2 to tac-8 | Yes | `server.py`, `pyproject.toml`, `.env.sample` |
| `adws/` | AI Developer Workflows (automation) | tac-4 to tac-8 | No | `adw_*.py`, `README.md` |
| `scripts/` | Shell scripts for operations | tac-2 to tac-8 | Yes | `start.sh`, `stop_apps.sh` |
| `specs/` | Feature specifications | tac-4 to tac-8 | No | Feature spec markdown files |
| `ai_docs/` | AI/LLM documentation | tac-7, tac-8 | No | Documentation for AI agents |
| `.claude/` | Claude Code CLI configuration | tac-4 to tac-8 | No | `settings.json`, `/hooks`, `/commands` |

## Standard Structure: Full-Stack Application

This is the **core structure** used across tac-2 through tac-7:

```
project-root/
├── README.md                    # Project documentation
├── .env.sample                  # Environment variable template
├── .gitignore                   # Git ignore rules
│
├── app/                         # Main application directory
│   ├── client/                  # Frontend application (Vite + TypeScript)
│   │   ├── src/
│   │   │   ├── main.ts         # Application entry point
│   │   │   ├── style.css       # Global styles
│   │   │   ├── types.d.ts      # TypeScript type definitions
│   │   │   ├── vite-env.d.ts   # Vite environment types
│   │   │   └── api/
│   │   │       └── client.ts   # API client for backend communication
│   │   ├── public/             # Static assets
│   │   │   ├── vite.svg
│   │   │   └── sample-data/    # Sample CSV/JSON files
│   │   ├── index.html          # HTML entry point
│   │   ├── package.json        # Node dependencies
│   │   ├── vite.config.ts      # Vite configuration (with proxy)
│   │   └── tsconfig.json       # TypeScript configuration
│   │
│   └── server/                  # Backend application (Python + FastAPI)
│       ├── core/               # Core business logic modules
│       │   ├── __init__.py
│       │   ├── data_models.py  # Pydantic models
│       │   ├── file_processor.py
│       │   ├── sql_processor.py
│       │   ├── llm_processor.py
│       │   ├── insights.py
│       │   ├── sql_security.py # (tac-4+)
│       │   └── constants.py    # (tac-6+)
│       ├── tests/              # Test suite
│       │   ├── __init__.py
│       │   ├── core/          # Unit tests for core modules
│       │   │   ├── __init__.py
│       │   │   ├── test_sql_processor.py
│       │   │   ├── test_file_processor.py
│       │   │   └── test_llm_processor.py
│       │   ├── assets/        # Test fixtures and data
│       │   │   ├── test_users.csv
│       │   │   ├── test_products.json
│       │   │   └── invalid.csv
│       │   └── test_sql_injection.py  # (tac-4+)
│       ├── db/                # SQLite database (gitignored)
│       ├── .env.sample        # Environment template
│       ├── .env               # Actual environment (gitignored)
│       ├── server.py          # FastAPI application entry point
│       ├── main.py            # (tac-4+) Alternative entry point
│       ├── pyproject.toml     # Python dependencies (uv)
│       ├── .python-version    # Python version specification
│       └── .venv/             # Virtual environment (gitignored)
│
├── scripts/                    # Utility scripts
│   ├── start.sh               # Start both client and server
│   └── stop_apps.sh           # Stop running apps
│
└── specs/                      # (Optional) Feature specifications
    └── *.md                    # Markdown specification files
```

## Extended Structure: With AI Developer Workflows (tac-4+)

Projects that include automation and AI workflows add these directories:

```
project-root/
├── (all previous directories...)
│
├── adws/                       # AI Developer Workflows
│   ├── README.md              # ADW documentation
│   │
│   ├── adw_modules/           # Shared modules
│   │   ├── __init__.py
│   │   ├── agent.py           # Agent execution logic
│   │   ├── data_types.py      # Type definitions
│   │   ├── github.py          # GitHub integration
│   │   ├── git_ops.py         # Git operations
│   │   ├── workflow_ops.py    # Workflow orchestration
│   │   ├── worktree_ops.py    # (tac-7+) Worktree management
│   │   ├── state.py           # State management
│   │   ├── utils.py           # Utility functions
│   │   └── r2_uploader.py     # (Optional) R2 storage
│   │
│   ├── adw_triggers/          # Trigger mechanisms
│   │   ├── __init__.py
│   │   ├── trigger_cron.py    # Scheduled execution
│   │   └── trigger_webhook.py # Webhook-based execution
│   │
│   ├── adw_tests/             # ADW test suite
│   │   ├── __init__.py
│   │   ├── health_check.py
│   │   ├── test_agents.py
│   │   └── sandbox_poc.py
│   │
│   └── adw_*.py               # Workflow implementations
│       ├── adw_plan.py        # Planning workflow
│       ├── adw_build.py       # Build workflow
│       ├── adw_test.py        # Testing workflow
│       ├── adw_review.py      # Review workflow
│       ├── adw_document.py    # Documentation workflow
│       ├── adw_patch.py       # Patching workflow
│       ├── adw_sdlc.py        # Full SDLC workflow
│       ├── adw_plan_build.py  # Combined plan+build
│       ├── adw_plan_build_iso.py     # (tac-7+) Isolated execution
│       └── (additional workflow combinations...)
│
├── .claude/                    # Claude Code CLI configuration
│   ├── settings.json          # Claude settings
│   ├── hooks/                 # Event hooks for automation
│   │   ├── pre_tool_use.py
│   │   ├── post_tool_use.py
│   │   ├── user_prompt_submit.py
│   │   ├── notification.py
│   │   ├── stop.py
│   │   ├── send_event.py
│   │   └── utils/             # Hook utilities
│   │       ├── summarizer.py
│   │       ├── constants.py
│   │       ├── llm/           # LLM integrations
│   │       └── tts/           # Text-to-speech
│   └── commands/              # Slash commands
│       ├── plan.md
│       ├── build.md
│       ├── implement.md
│       ├── chore.md
│       ├── start.md
│       └── (additional commands...)
│
├── ai_docs/                    # (Optional) AI documentation
│   ├── README.md
│   └── *.md                    # AI-specific documentation
│
├── logs/                       # (Generated) Session logs
│   └── {session-id}/          # Per-session log directories
│       ├── chat.json
│       ├── pre_tool_use.json
│       ├── post_tool_use.json
│       └── notification.json
│
└── agents/                     # (Optional) Agent execution logs
    └── *.log                   # Agent run logs
```

## Vue 3 Application Structure (tac-8)

For Vue 3 + Tailwind projects, the client structure changes:

```
app/client/  (or apps/client/)
├── src/
│   ├── main.ts                # Vue app initialization
│   ├── App.vue                # Root component
│   ├── style.css              # Global styles (Tailwind)
│   ├── types.ts               # Type definitions
│   ├── vite-env.d.ts          # Vite types
│   │
│   ├── components/            # Vue components
│   │   ├── HelloWorld.vue
│   │   ├── EventTimeline.vue
│   │   ├── EventRow.vue
│   │   ├── FilterPanel.vue
│   │   ├── ThemeManager.vue
│   │   └── (other components...)
│   │
│   ├── composables/           # Vue composables (hooks)
│   │   ├── useWebSocket.ts
│   │   ├── useThemes.ts
│   │   ├── useMediaQuery.ts
│   │   └── (other composables...)
│   │
│   ├── types/                 # TypeScript types
│   │   └── theme.ts
│   │
│   └── utils/                 # Utility functions
│       └── chartRenderer.ts
│
├── public/                    # Static assets
│   ├── bg.png
│   └── sample-data/
│
├── index.html                 # HTML entry
├── package.json               # Dependencies (includes Vue 3)
├── vite.config.ts             # Vite config with @vitejs/plugin-vue
├── tsconfig.json              # TypeScript config
├── tailwind.config.js         # Tailwind configuration
└── postcss.config.js          # PostCSS configuration
```

## Multi-App Structure (tac-8)

For projects with multiple applications, use subdirectories:

```
tac-8/
├── tac8_app1__agent_layer_primitives/
│   ├── adws/
│   ├── apps/
│   └── README.md
│
├── tac8_app2__multi_agent_todone/
│   ├── adws/
│   ├── apps/
│   └── README.md
│
├── tac8_app3__out_loop_multi_agent_task_board/
│   ├── adws/
│   ├── apps/                  # Note: "apps" instead of "app"
│   │   ├── client/           # Vue 3 + Tailwind
│   │   └── server/           # Node.js + TypeScript
│   ├── .claude/
│   ├── scripts/
│   └── README.md
│
└── (additional apps...)
```

## Key Configuration Files

### Client Configuration

**package.json** (Vanilla TypeScript):

```json
{
  "name": "client",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "typescript": "~5.8.3",
    "vite": "^6.3.5"
  }
}
```

**package.json** (Vue 3 + Tailwind):

```json
{
  "name": "multi-agent-observability-client",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.17"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0.0",
    "tailwindcss": "^3.4.16",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.5.3",
    "typescript": "~5.8.3",
    "vite": "^7.0.4",
    "vue-tsc": "^2.2.12"
  }
}
```

**vite.config.ts** (Vanilla):

```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

**vite.config.ts** (Vue 3):

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
})
```

### Server Configuration

**pyproject.toml**:

```toml
[project]
name = "server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "anthropic",
    "openai",
    # ... other dependencies
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
]
```

**server.py** (Entry point):

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes...
```

## Naming Conventions

### Files

- **Python**: `snake_case.py` (e.g., `llm_processor.py`, `data_models.py`)
- **TypeScript**: `camelCase.ts` or `kebab-case.ts` (e.g., `client.ts`)
- **Vue**: `PascalCase.vue` (e.g., `EventTimeline.vue`, `ThemeManager.vue`)
- **Config**: `kebab-case.config.ts` (e.g., `vite.config.ts`, `tailwind.config.js`)
- **ADW workflows**: `adw_*.py` prefix (e.g., `adw_plan_build.py`)

### Directories

- **Top-level**: `kebab-case` or `snake_case` (e.g., `app/`, `adws/`, `ai_docs/`)
- **Python modules**: `snake_case` (e.g., `adw_modules/`, `adw_triggers/`)
- **Vue**: `camelCase` (e.g., `composables/`, `components/`)

## Environment Management

### Root Level

```
.env.sample           # Template for all environment variables
```

### Server Level

```
app/server/.env.sample  # Backend-specific environment template
app/server/.env         # Actual environment (gitignored)
```

**Required Variables**:

- `OPENAI_API_KEY` (for AI features)
- `ANTHROPIC_API_KEY` (for Claude integration)
- `GITHUB_REPO_URL` (for ADW workflows)
- `GITHUB_PAT` (optional, for GitHub operations)

## Scripts

### Standard Scripts

**scripts/start.sh**:

- Checks for `.env` file existence
- Starts backend server (port 8000)
- Starts frontend dev server (port 5173)
- Handles graceful shutdown with Ctrl+C

**scripts/stop_apps.sh**:

- Kills running processes on ports 8000 and 5173

## Recommendations

### For New Projects

1. **Start with the basic structure** (app/client + app/server)
2. **Add scripts/** directory immediately for convenience
3. **Use .env.sample** templates to document required environment variables
4. **Follow the core/ module pattern** for backend business logic
5. **Add adws/** only when you need AI automation workflows

### Scaling Up

1. **Keep client and server separate** - never mix frontend and backend code
2. **Use the adw_modules/** pattern for shared workflow code
3. **Create .claude/** configuration when using Claude Code CLI extensively
4. **Add ai_docs/** for prompt engineering documentation
5. **Use specs/** for detailed feature specifications

### Vue 3 Projects

1. **Create composables/** for reusable logic
2. **Organize components/** by feature or function
3. **Include tailwind.config.js** when using Tailwind CSS
4. **Use types/** subdirectory for complex type definitions

## Next Steps

1. **Clone the basic structure** from tac-2/tac-3 for simple projects
2. **Clone tac-6/tac-7** for projects with AI workflows
3. **Clone tac-8/tac8_app3** for Vue 3 + Tailwind projects
4. **Adapt the adws/** structure based on your automation needs
5. **Follow the .claude/** pattern if using Claude Code CLI hooks and commands
