# Chore: Migrate devcontainer venv to /home/node/.venv

## Chore Description
Migrate the Python virtual environment location in the devcontainer from `/workspace/.venv` (inside the bind-mounted workspace) to `/home/node/.venv` (outside the workspace in the user's home directory).

This simplifies the devcontainer setup by:
- Eliminating the need for a Docker volume mount to shadow the workspace `.venv`
- Removing the sudoers rule for chown operations on the venv
- Simplifying the postCreateCommand

The current approach uses a volume mount to prevent WSL/container venv conflicts. The new approach avoids the conflict entirely by placing the venv outside the bind-mounted workspace.

## Relevant Files
Use these files to resolve the chore:

- `.devcontainer/devcontainer.json` - Contains mount configuration, environment variables, Python interpreter path, and postCreateCommand that all reference `/workspace/.venv`
- `.devcontainer/Dockerfile` - Contains a sudoers rule for chown on `/workspace/.venv` that is no longer needed
- `.devcontainer/README.md` - Documents the current venv mount strategy; needs updating to reflect the new approach

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update devcontainer.json mounts
- Remove the venv volume mount line:
  ```
  "source=${localWorkspaceFolderBasename}-venv,target=/workspace/.venv,type=volume"
  ```
- Keep the other two mounts (bash history volume, claude config bind)

### Step 2: Update devcontainer.json containerEnv
- Change `UV_PROJECT_ENVIRONMENT` from `/workspace/.venv` to `/home/node/.venv`
- Change `VIRTUAL_ENV` from `/workspace/.venv` to `/home/node/.venv`
- Change `PATH` from `/workspace/.venv/bin:/usr/local/share/npm-global/bin:/usr/local/bin:/usr/bin:/bin` to `/home/node/.venv/bin:/usr/local/share/npm-global/bin:/usr/local/bin:/usr/bin:/bin`

### Step 3: Update devcontainer.json python.defaultInterpreterPath
- Change from `${workspaceFolder}/.venv/bin/python` to `/home/node/.venv/bin/python`

### Step 4: Simplify devcontainer.json postCreateCommand
- Change from:
  ```
  "postCreateCommand": "sudo /bin/chown -R node:node /workspace/.venv && rm -rf /workspace/.venv/* /workspace/.venv/.* 2>/dev/null; uv venv /workspace/.venv --python $(which python3) && uv sync"
  ```
- To:
  ```
  "postCreateCommand": "uv venv /home/node/.venv --python $(which python3) && uv sync"
  ```

### Step 5: Update Dockerfile sudoers rules
- Remove line 122 that grants chown permission on `/workspace/.venv`:
  ```
  echo "node ALL=(root) NOPASSWD: /bin/chown -R node\:node /workspace/.venv" >> /etc/sudoers.d/node-firewall && \
  ```
- Ensure the firewall sudoers rule remains intact

### Step 6: Update README.md documentation
- Update the comparison table to remove the `.venv` volume mount row
- Update any references to `/workspace/.venv` to `/home/node/.venv`
- Add a note explaining the venv location strategy

### Step 7: Run validation commands
- Execute the validation commands below to confirm the changes are syntactically correct

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `python3 -c "import json; json.load(open('.devcontainer/devcontainer.json'))"` - Validate devcontainer.json is valid JSON
- `grep -q '/home/node/.venv' .devcontainer/devcontainer.json && echo "OK: venv path updated"` - Confirm new venv path is present
- `grep -q '/workspace/.venv' .devcontainer/devcontainer.json && echo "FAIL: old path still present" || echo "OK: old path removed"` - Confirm old venv path is removed
- `grep -q 'chown.*workspace/.venv' .devcontainer/Dockerfile && echo "FAIL: old sudoers rule present" || echo "OK: sudoers rule removed"` - Confirm sudoers rule is removed
- `uv run pytest app/tests/ -q` - Run tests to ensure no regressions in application code

## Notes
- After applying these changes, the devcontainer must be **rebuilt** for changes to take effect
- The orphaned Docker volume `${localWorkspaceFolderBasename}-venv` can be manually removed after confirming the new setup works: `docker volume rm dwg-extractor-venv`
- This change only affects the devcontainer environment; WSL development remains unchanged
- No application code changes are required
