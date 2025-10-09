#!/bin/bash

#######################################################################
# Application Stop Script (Template Version)
#
# Gracefully stops running application processes and services.
#
# Usage:
#   ./scripts/stop_apps.sh
#
# This script will:
#   - Stop the start.sh script and its child processes
#   - Stop webhook server (trigger_webhook.py)
#   - Stop processes on common development ports
#
# Customize this script to match your application's needs.
#######################################################################

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping application services...${NC}"
echo ""

# Stop start.sh and its child processes
echo -e "${GREEN}Killing start.sh processes and children...${NC}"
pkill -f "start.sh" 2>/dev/null

# Stop webhook server (part of ADW infrastructure)
echo -e "${GREEN}Killing webhook server...${NC}"
pkill -f "trigger_webhook.py" 2>/dev/null

# Stop cron trigger (part of ADW infrastructure)
echo -e "${GREEN}Killing cron trigger...${NC}"
pkill -f "trigger_cron.py" 2>/dev/null

#######################################################################
# PORT-BASED CLEANUP
#######################################################################

# Common development ports - customize based on your application
echo -e "${GREEN}Killing processes on common development ports...${NC}"

# Default ports:
# 5173 - Vite dev server (frontend)
# 3000 - Node.js/Express/React dev server
# 8000 - Python FastAPI/Flask/Django
# 8001 - ADW webhook server
# 8080 - Go/Java applications
# 3001 - Alternative Node.js port

# Kill processes on these ports (customize as needed)
lsof -ti:5173,3000,8000,8001,8080,3001 2>/dev/null | xargs kill -9 2>/dev/null

#######################################################################
# PROCESS NAME-BASED CLEANUP (Optional - uncomment if needed)
#######################################################################

# Uncomment and customize based on your application:

# Python applications
# pkill -f "uvicorn" 2>/dev/null
# pkill -f "gunicorn" 2>/dev/null
# pkill -f "flask run" 2>/dev/null
# pkill -f "python.*server.py" 2>/dev/null

# Node.js applications
# pkill -f "node.*server" 2>/dev/null
# pkill -f "npm run dev" 2>/dev/null
# pkill -f "vite" 2>/dev/null

# Go applications
# pkill -f "go run" 2>/dev/null

# Rust applications
# pkill -f "cargo run" 2>/dev/null

# Docker
# docker-compose -f app/docker-compose.yml down 2>/dev/null

#######################################################################
# CLEANUP VERIFICATION
#######################################################################

# Give processes a moment to terminate
sleep 1

# Check if any processes are still running on key ports
REMAINING_PROCESSES=$(lsof -ti:5173,3000,8000,8001,8080,3001 2>/dev/null | wc -l)

if [ "$REMAINING_PROCESSES" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All services stopped successfully!${NC}"
else
    echo ""
    echo -e "${YELLOW}Warning: Some processes may still be running.${NC}"
    echo "Run 'lsof -ti:PORT | xargs kill -9' for specific ports if needed."
fi
