# Playwright MCP Setup

## Purpose

Configure Playwright MCP for browser automation in WSL environments. This enables E2E testing, web scraping, and browser-based interactions through the MCP protocol.

## Instructions

### 1. Verify Xvfb Installation

Check if Xvfb (virtual display server) is installed:

```bash
which xvfb-run
```

If not found, install it:

```bash
sudo apt-get update && sudo apt-get install -y xvfb
```

### 2. Start Virtual Display

Start Xvfb on display :99:

```bash
Xvfb :99 -screen 0 1280x1024x24 -ac -nolisten tcp -dpi 96 +extension RANDR &
```

Verify it's running:

```bash
ps aux | grep "Xvfb :99" | grep -v grep
```

You should see output showing Xvfb running. If no output, the command failed - retry the start command.

### 3. Install Playwright Browsers

Install Chromium browser for Playwright:

```bash
npx playwright install chromium
```

This downloads the browser to `~/.cache/ms-playwright/`.

### 4. Create MCP Configuration

Create `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":99"
      }
    }
  }
}
```

### 5. Restart Claude Code

**Important:** Completely exit and restart Claude Code (not just reload) for MCP changes to take effect.

### 6. Test the Setup

After restart, test with:

```
Navigate to https://example.com and take a screenshot
```

## Relevant Files

- `.mcp.json` - MCP server configuration (project root)
- `~/.cache/ms-playwright/` - Playwright browser binaries

## Workflow

1. Check prerequisites (Xvfb installed)
2. Start virtual display (Xvfb :99)
3. Install Playwright browsers
4. Configure MCP in `.mcp.json`
5. Restart Claude Code
6. Test browser automation

## Expertise

**Common Issues:**

**Xvfb not running:**
- Symptom: DISPLAY or X server connection errors
- Solution: Restart Xvfb with the command in step 2

**Browser executable not found:**
- Symptom: "Executable doesn't exist at .../chromium-XXXX/chrome-linux/chrome"
- Solution: Check installed versions and create symlink if needed:

```bash
ls -la ~/.cache/ms-playwright/
ln -s ~/.cache/ms-playwright/chromium-ACTUAL ~/.cache/ms-playwright/chromium-EXPECTED
```

**MCP not loading:**
- Verify `.mcp.json` is in project root (not `.claude/` folder)
- Check JSON syntax validity
- Fully exit and restart Claude Code (critical step)

**Session Persistence:**

Xvfb must be restarted each WSL session. To auto-start, add to `~/.bashrc`:

```bash
if ! pgrep -x Xvfb > /dev/null; then
    Xvfb :99 -screen 0 1280x1024x24 -ac -nolisten tcp -dpi 96 +extension RANDR > /dev/null 2>&1 &
fi
```

## Examples

**Basic Navigation:**
```
Navigate to http://localhost:3000
```

**Page Interaction:**
```
Fill the email field with "test@example.com", fill the password field with "password123", and click the login button
```

**Data Extraction:**
```
Get all visible text from the current page
```

**Screenshots:**
```
Take a screenshot of the page and save it
```

**JavaScript Execution:**
```
Execute JavaScript to get the page title
```
