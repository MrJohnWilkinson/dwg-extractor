#!/bin/bash

#######################################################################
# Application Startup Script (Template Version)
#
# This is a template startup script. Customize it for your application.
#
# Usage:
#   ./scripts/start.sh [args]
#
# Examples for different application types are provided below.
# Uncomment and modify the appropriate section for your project.
#######################################################################

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}  Template Startup Script${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""
echo -e "${BLUE}This is a template startup script.${NC}"
echo -e "${BLUE}Customize it for your application by editing:${NC}"
echo -e "  ${GREEN}scripts/start.sh${NC}"
echo ""
echo "See ${GREEN}app/README.md${NC} for examples of different project types."
echo ""

# Get the script's directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

#######################################################################
# CLEANUP HANDLER (Keep this - works for all application types)
#######################################################################

cleanup() {
    echo -e "\n${BLUE}Shutting down services...${NC}"

    # Kill all child processes
    jobs -p | xargs -r kill 2>/dev/null

    # Wait for processes to terminate
    wait

    echo -e "${GREEN}Services stopped successfully.${NC}"
    exit 0
}

# Trap EXIT, INT, and TERM signals
trap cleanup EXIT INT TERM

#######################################################################
# EXAMPLE 1: Python FastAPI/Flask Application
#######################################################################
#
# Uncomment and customize for a Python web application:
#
# # Check for .env file (optional)
# if [ ! -f "$PROJECT_ROOT/app/.env" ]; then
#     echo -e "${YELLOW}Warning: No .env file found in app/.${NC}"
#     echo "Consider creating one from app/.env.sample"
# fi
#
# echo -e "${GREEN}Starting Python application...${NC}"
# cd "$PROJECT_ROOT/app"
#
# # For FastAPI:
# uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
# APP_PID=$!
#
# # Or for Flask:
# # uv run flask run --debug --host 0.0.0.0 --port 8000 &
# # APP_PID=$!
#
# sleep 2
# if kill -0 $APP_PID 2>/dev/null; then
#     echo -e "${GREEN}✓ Application started successfully!${NC}"
#     echo -e "${BLUE}Server: http://localhost:8000${NC}"
#     echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
# else
#     echo -e "${RED}Application failed to start!${NC}"
#     exit 1
# fi
#
# wait

#######################################################################
# EXAMPLE 2: Node.js/TypeScript Application
#######################################################################
#
# Uncomment and customize for a Node.js application:
#
# echo -e "${GREEN}Starting Node.js application...${NC}"
# cd "$PROJECT_ROOT/app"
# npm install
# npm run dev &
# APP_PID=$!
#
# sleep 2
# if kill -0 $APP_PID 2>/dev/null; then
#     echo -e "${GREEN}✓ Application started successfully!${NC}"
#     echo -e "${BLUE}Server: http://localhost:3000${NC}"
# else
#     echo -e "${RED}Application failed to start!${NC}"
#     exit 1
# fi
#
# wait

#######################################################################
# EXAMPLE 3: Frontend + Backend (Multi-Service)
#######################################################################
#
# Uncomment and customize for a full-stack application:
#
# # Check for backend .env
# if [ ! -f "$PROJECT_ROOT/app/backend/.env" ]; then
#     echo -e "${RED}Error: No .env file in app/backend/${NC}"
#     echo "Run: cd app/backend && cp .env.sample .env"
#     exit 1
# fi
#
# # Start backend
# echo -e "${GREEN}Starting backend server...${NC}"
# cd "$PROJECT_ROOT/app/backend"
# uv run uvicorn src.main:app --reload --port 8000 &
# BACKEND_PID=$!
# sleep 3
#
# if ! kill -0 $BACKEND_PID 2>/dev/null; then
#     echo -e "${RED}Backend failed to start!${NC}"
#     exit 1
# fi
#
# # Start frontend
# echo -e "${GREEN}Starting frontend server...${NC}"
# cd "$PROJECT_ROOT/app/frontend"
# npm run dev &
# FRONTEND_PID=$!
# sleep 3
#
# if ! kill -0 $FRONTEND_PID 2>/dev/null; then
#     echo -e "${RED}Frontend failed to start!${NC}"
#     exit 1
# fi
#
# echo -e "${GREEN}✓ All services started successfully!${NC}"
# echo -e "${BLUE}Frontend: http://localhost:5173${NC}"
# echo -e "${BLUE}Backend:  http://localhost:8000${NC}"
# echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
# echo ""
# echo "Press Ctrl+C to stop all services..."
#
# wait

#######################################################################
# EXAMPLE 4: Python CLI Tool
#######################################################################
#
# Uncomment and customize for a CLI application:
#
# echo -e "${GREEN}Running CLI application...${NC}"
# cd "$PROJECT_ROOT/app"
# uv run python -m src.cli "$@"

#######################################################################
# EXAMPLE 5: Go Application
#######################################################################
#
# Uncomment and customize for a Go application:
#
# echo -e "${GREEN}Starting Go application...${NC}"
# cd "$PROJECT_ROOT/app"
# go run cmd/server/main.go &
# APP_PID=$!
#
# sleep 2
# if kill -0 $APP_PID 2>/dev/null; then
#     echo -e "${GREEN}✓ Application started successfully!${NC}"
#     echo -e "${BLUE}Server: http://localhost:8080${NC}"
# else
#     echo -e "${RED}Application failed to start!${NC}"
#     exit 1
# fi
#
# wait

#######################################################################
# EXAMPLE 6: Rust Application
#######################################################################
#
# Uncomment and customize for a Rust application:
#
# echo -e "${GREEN}Starting Rust application...${NC}"
# cd "$PROJECT_ROOT/app"
# cargo run &
# APP_PID=$!
#
# sleep 2
# if kill -0 $APP_PID 2>/dev/null; then
#     echo -e "${GREEN}✓ Application started successfully!${NC}"
# else
#     echo -e "${RED}Application failed to start!${NC}"
#     exit 1
# fi
#
# wait

#######################################################################
# EXAMPLE 7: Single-File Script
#######################################################################
#
# Uncomment and customize for a simple script:
#
# echo -e "${GREEN}Running script...${NC}"
# cd "$PROJECT_ROOT/app"
# uv run python main.py "$@"
# # Or: node main.js "$@"
# # Or: go run main.go "$@"

#######################################################################
# EXAMPLE 8: Docker Compose
#######################################################################
#
# Uncomment and customize for Docker-based applications:
#
# echo -e "${GREEN}Starting services with Docker Compose...${NC}"
# cd "$PROJECT_ROOT/app"
# docker-compose up &
# DOCKER_PID=$!
#
# echo -e "${GREEN}✓ Docker services started!${NC}"
# echo "Press Ctrl+C to stop all services..."
#
# wait

#######################################################################
# DEFAULT TEMPLATE MESSAGE
#######################################################################

echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Build your application in ${GREEN}app/${NC}"
echo "  2. Choose the appropriate example above"
echo "  3. Uncomment and customize for your needs"
echo "  4. Test with: ${GREEN}./scripts/start.sh${NC}"
echo ""
echo "See ${GREEN}app/README.md${NC} for detailed project structure examples."
echo ""

# Wait for Ctrl+C
echo "Press Ctrl+C to exit..."
wait
