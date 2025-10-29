# Prepare Application

Setup the application for the review or test.

## Variables

PORT: 5173 (hardcoded - Activity Logger frontend port)

## Setup

1. Reset the database (for testing scenarios):
   - Run `scripts/supabase_local.sh reset` (resets local Supabase instance)
   - Note: This is only for local testing. Production uses Supabase cloud.

2. Start the application:
   - IMPORTANT: Make sure the server and client are running on a background process using `nohup sh ./scripts/start.sh > /dev/null 2>&1 &`
   - The start.sh script will start all 3 services:
     - Log Server (WebSocket): port 8001
     - Backend API (FastAPI): port 8002
     - Frontend (Vite): port 5173
   - Use `./scripts/stop_apps.sh` to stop the server and client

3. Verify the application is running:
   - The application should be accessible at http://localhost:5173

Note: Read `scripts/` and `README.md` for more information on how to start, stop and reset the server and client.
