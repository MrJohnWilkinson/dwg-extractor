# Application Directory

This directory is where your application code lives. The template provides the infrastructure (ADW, slash commands, hooks), and this is where you build your actual project.

## Getting Started

Choose the project type that matches your needs, create the appropriate structure, and customize `scripts/start.sh` to launch your application.

## Project Structure Examples

### Python Web Application (FastAPI)

```
app/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # Data models
│   ├── services/
│   │   ├── __init__.py
│   │   └── database.py      # Business logic
│   └── config.py            # Configuration
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
├── pyproject.toml           # Dependencies (uv)
├── .env.sample              # Environment template
└── README.md                # App documentation
```

**Example `src/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="My Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Example `pyproject.toml`:**
```toml
[project]
name = "my-application"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-dotenv>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Python Web Application (Flask)

```
app/
├── src/
│   ├── __init__.py
│   ├── app.py               # Flask app
│   ├── routes/
│   │   └── main.py
│   ├── models/
│   │   └── user.py
│   └── templates/
│       └── index.html
├── tests/
├── pyproject.toml
└── .env.sample
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
uv run flask run --debug --host 0.0.0.0 --port 8000
```

### TypeScript/React Web Application

```
app/
├── src/
│   ├── main.tsx             # Entry point
│   ├── App.tsx              # Root component
│   ├── components/
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   └── About.tsx
│   ├── services/
│   │   └── api.ts           # API client
│   ├── types/
│   │   └── index.d.ts
│   └── styles/
│       └── global.css
├── public/
│   └── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts           # Or webpack, etc.
└── .env.sample
```

**Example `package.json`:**
```json
{
  "name": "my-app",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
npm install
npm run dev
```

### Node.js API Server (Express)

```
app/
├── src/
│   ├── index.ts             # Server entry point
│   ├── routes/
│   │   ├── users.ts
│   │   └── auth.ts
│   ├── controllers/
│   │   └── userController.ts
│   ├── middleware/
│   │   └── auth.ts
│   ├── models/
│   │   └── User.ts
│   └── config/
│       └── database.ts
├── tests/
├── package.json
├── tsconfig.json
└── .env.sample
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
npm install
npm run dev
```

### Python CLI Tool

```
app/
├── src/
│   ├── __init__.py
│   ├── cli.py               # Click or argparse CLI
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── init.py
│   │   └── process.py
│   └── utils/
│       └── helpers.py
├── tests/
├── pyproject.toml
└── README.md
```

**Example `src/cli.py` (using Click):**
```python
import click

@click.group()
def cli():
    """My CLI tool."""
    pass

@cli.command()
@click.argument('name')
def hello(name):
    """Say hello."""
    click.echo(f'Hello {name}!')

if __name__ == '__main__':
    cli()
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
uv run python -m src.cli "$@"
```

### Go Application

```
app/
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── internal/
│   ├── api/
│   │   └── handlers.go
│   ├── models/
│   │   └── user.go
│   └── services/
│       └── database.go
├── pkg/
│   └── utils/
├── go.mod
├── go.sum
└── README.md
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
go run cmd/server/main.go
```

### Rust Application

```
app/
├── src/
│   ├── main.rs              # Binary entry point
│   ├── lib.rs               # Library root
│   ├── api/
│   │   └── mod.rs
│   └── models/
│       └── mod.rs
├── tests/
├── Cargo.toml
└── README.md
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
cargo run
```

### Single-File Script

For simple automation scripts or prototypes:

```
app/
├── main.py                  # or main.js, main.go, etc.
├── requirements.txt         # or package.json, go.mod, etc.
└── README.md
```

**Update `../scripts/start.sh`:**
```bash
#!/bin/bash
cd app
uv run python main.py "$@"
```

## Multi-Service Applications

For applications with multiple services (frontend + backend, multiple microservices):

```
app/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── src/
│   ├── pyproject.toml
│   └── .env.sample
├── worker/
│   ├── src/
│   └── pyproject.toml
└── docker-compose.yml       # Optional
```

**Update `../scripts/start.sh` for multi-service:**
```bash
#!/bin/bash

# Trap Ctrl+C and cleanup
cleanup() {
    echo "Stopping all services..."
    kill $BACKEND_PID $FRONTEND_PID $WORKER_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Start backend
echo "Starting backend..."
cd app/backend
uv run uvicorn src.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ../..

# Start frontend
echo "Starting frontend..."
cd app/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

# Start worker
echo "Starting worker..."
cd app/worker
uv run python src/worker.py &
WORKER_PID=$!
cd ../..

echo "All services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop all services"

# Wait for any service to exit
wait
```

## Environment Variables

Create `.env.sample` in your app directory (or subdirectories) for application-specific configuration:

```bash
# Application Settings
APP_NAME=My Application
DEBUG=true
PORT=8000

# Database
DATABASE_URL=postgresql://localhost/myapp

# External APIs
STRIPE_API_KEY=sk_test_xxxxx
SENDGRID_API_KEY=SG.xxxxx

# Feature Flags
ENABLE_ANALYTICS=true
```

**Loading environment variables:**

Python (with python-dotenv):
```python
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")
```

Node.js (with dotenv):
```javascript
import 'dotenv/config';
const databaseUrl = process.env.DATABASE_URL;
```

## Testing

### Python (pytest)

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

Run tests:
```bash
cd app
uv run pytest
uv run pytest --cov=src  # With coverage
```

### TypeScript/JavaScript (Vitest or Jest)

Add to `package.json`:
```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0"
  },
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

Run tests:
```bash
cd app
npm test
```

## Integrating with scripts/start.sh

The template's `scripts/start.sh` is designed to be customized for your application. After setting up your project structure:

1. **Edit `scripts/start.sh`** to start your specific application
2. **Add environment checks** if needed (e.g., verify .env exists)
3. **Add health checks** to verify services started correctly
4. **Handle cleanup** properly on exit

See `scripts/start.sh` for a template with examples.

## ADW Integration

When using the AI Developer Workflow (ADW) system with your application:

1. **Issue Creation**: Create GitHub issues for features, bugs, or chores
2. **Planning**: ADW generates plans in `specs/` directory
3. **Implementation**: ADW modifies files in this `app/` directory
4. **Testing**: Mention testing requirements in issues for ADW to generate tests

Example issue for ADW:
```markdown
Title: Add user authentication endpoint

Body:
Implement a /auth/login endpoint that:
- Accepts email and password
- Returns a JWT token
- Includes proper error handling
- Has unit tests with >90% coverage
- Uses bcrypt for password hashing
```

ADW will:
1. Create a plan in `specs/`
2. Implement the endpoint in `app/src/`
3. Create tests in `app/tests/`
4. Update dependencies if needed

## Best Practices

1. **Keep app/ focused on application code**
   - Infrastructure belongs in `.claude/`, `adws/`, `scripts/`
   - Application code belongs in `app/`

2. **Use environment variables for configuration**
   - Never commit secrets or API keys
   - Use `.env.sample` as a template
   - Load `.env` in your application

3. **Write tests**
   - ADW can generate tests if you specify in issues
   - Keep tests alongside code

4. **Document your application**
   - Update this README with your specifics
   - Document API endpoints
   - Include setup instructions

5. **Use semantic versioning**
   - Update version in `package.json` or `pyproject.toml`
   - Tag releases in git

## Next Steps

1. **Choose your project type** from the examples above
2. **Create the directory structure** for your application
3. **Update `scripts/start.sh`** to launch your app
4. **Create `.env.sample`** with your configuration needs
5. **Update this README** with your application details
6. **Start building** and let ADW help automate your workflow!

## Resources

- **Python/FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Node.js/Express**: https://expressjs.com/
- **Go**: https://go.dev/doc/
- **Rust**: https://www.rust-lang.org/learn

For infrastructure and workflow documentation, see the main [README.md](../README.md) and [TEMPLATE_GUIDE.md](../TEMPLATE_GUIDE.md).
