---
description: Create a new PowerShell alias or function-based alias
argument-hint: [alias_name] [command/path]
model: opus
hints: PowerShell alias creation - $1=alias_name $2=command_or_path
---

# Create PowerShell Alias

## Purpose

Create a new PowerShell alias in the user's profile. Supports both direct command aliases and function-based aliases for directory navigation.

## Variables

- ALIAS_NAME: $1 (required) - The name of the alias to create
- COMMAND_PATH: $2 (required) - The command, executable path, or directory path to alias

## Instructions

1. Determine alias type based on <COMMAND_PATH>:
   - If directory/path requiring navigation: Use function wrapper approach
   - If command/executable: Use direct alias approach

2. For **function-based aliases** (directory navigation):
   - Create function: `function <FunctionName> { Set-Location "<COMMAND_PATH>" }`
   - Create alias: `Set-Alias -Name <ALIAS_NAME> -Value <FunctionName> -Force`
   - Append both to PowerShell profile

3. For **direct aliases** (commands/executables):
   - Create alias: `Set-Alias -Name <ALIAS_NAME> -Value '<COMMAND_PATH>' -Force`
   - Append to PowerShell profile

4. Update startup display section:
   - Locate the "Quick Navigation Aliases:" section
   - Add line: `Write-Host "  <ALIAS_NAME>    description" -ForegroundColor Green`

5. Update aliases filter function:
   - Locate the `function aliases` section
   - Add <ALIAS_NAME> to the array in `Where-Object` clause

6. Reload profile to activate:
   - Run: `. $PROFILE` in PowerShell

## Relevant Files

- `C:\Users\johnw\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1` - Main PowerShell profile
  - **Startup display section**: Between "Quick Navigation Aliases:" heading and closing separator
  - **Alias definitions section**: After the startup display block
  - **Helper functions section**: Contains the `function aliases` definition

## Workflow

1. **Add alias definition to profile**:
   - Location: After existing alias definitions
   - For navigation: Create function + alias pair
   - For commands: Create direct alias

2. **Add to startup display** (optional):
   - Location: In the "Quick Navigation Aliases:" section
   - Format: `Write-Host "  alias-name    description" -ForegroundColor Green`

3. **Add to aliases filter** (optional):
   - Location: In the `function aliases` Where-Object array
   - Update: Add alias name to the array

4. **Reload profile**:
   - Execute: `. $PROFILE`

## Examples

**Example 1: Directory navigation alias**
```powershell
# Creates ac-scr alias for navigating to autocad-scripts
function Set-AutoCADScripts { Set-Location "C:\Users\johnw\Desktop\Desktop Reference\GitProjectsDesktop\autocad-scripts" }
Set-Alias -Name ac-scr -Value Set-AutoCADScripts -Force
```

**Example 2: Direct command alias**
```powershell
# Creates claude alias for Claude Code CLI
Set-Alias claude "C:\Users\johnw\.local\bin\claude.exe"
```
