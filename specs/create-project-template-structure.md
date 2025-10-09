# Chore: Create Starting Project Template

## Chore Description
Create a reusable starting project template that preserves the valuable Claude Code infrastructure (commands, hooks, ADW scripts) while removing the current Natural Language SQL Interface application. This template will serve as a foundation for building new applications while leveraging the existing AI Developer Workflow system, slash commands, and automation scripts.

The template should be clean, well-documented, and ready to use for starting new projects without the need to manually extract and reorganize the infrastructure components.

## Relevant Files

### Files to Preserve (Core Infrastructure)
- `.claude/commands/*.md` - All slash commands for workflow automation (/chore, /bug, /feature, /implement, /commit, /pull_request, etc.)
  - These provide the SDLC automation capabilities
- `.claude/hooks/*.py` - All hook scripts for pre/post tool use, notifications, and lifecycle events
  - Provide enhanced Claude Code behavior and logging
- `.claude/hooks/utils/**` - Utility modules for hooks (constants, LLM integrations)
  - Support infrastructure for hooks
- `.claude/settings.json` - Permissions and hook configurations
  - Defines the Claude Code environment behavior
- `adws/*.py` - All AI Developer Workflow scripts (agent.py, github.py, data_types.py, utils.py, trigger_*.py, adw_plan_build.py)
  - Core automation system for GitHub issue processing
- `adws/README.md` - ADW documentation
  - Explains how to use the workflow system
- `scripts/copy_dot_env.sh` - Environment setup utility
  - Helper for configuration
- `scripts/clear_issue_comments.sh` - GitHub utility
  - Workflow maintenance tool
- `scripts/delete_pr.sh` - GitHub utility
  - Workflow maintenance tool
- `scripts/expose_webhook.sh` - Webhook tunneling utility
  - For local webhook development
- `scripts/kill_trigger_webhook.sh` - Process management utility
  - Workflow management tool
- `scripts/stop_apps.sh` - Generic app stopping utility
  - Can be adapted for any app
- `.gitignore` - Ignore patterns (preserve and enhance)
  - Standard exclusions
- `.env.sample` - Root environment template
  - For ADW configuration
- `ai_docs/**` - AI/LLM documentation
  - Reference materials for working with Claude Code and AI APIs
- `README.md` - Will be replaced with template README

### Files to Remove (Application-Specific)
- `app/**` - Entire Natural Language SQL Interface application
  - Application-specific code to be replaced
- `specs/*.md` - Application-specific feature specifications
  - Old specs not relevant to template
- `scripts/start.sh` - Application-specific startup script
  - Tied to the SQL app structure

### New Files to Create

#### `README.md` (Template Version)
- Overview of what this template provides
- Quick start guide for using the template
- Documentation of the infrastructure components
- Instructions for customizing for a new project

#### `scripts/start.sh` (Template Version)
- Generic placeholder script that explains where to add application startup logic
- Examples of how to structure startup for different app types

#### `TEMPLATE_GUIDE.md`
- Comprehensive guide on using this template
- How to customize each component
- Best practices for structuring new projects
- Examples of different project types (web app, CLI tool, automation script, etc.)

#### `app/README.md`
- Placeholder explaining this is where your application code goes
- Suggested project structures for different app types
- Examples and guidelines

#### `specs/README.md`
- Explanation of the specs directory and how to use it
- Template spec file examples
- How specs integrate with the ADW workflow

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Template Documentation
- Create comprehensive `TEMPLATE_GUIDE.md` in the project root
  - Explain what this template provides (ADW system, slash commands, hooks)
  - Document each infrastructure component and its purpose
  - Provide step-by-step instructions for starting a new project
  - Include examples for different project types (web app, API, CLI, automation)
  - Explain how to customize the template for specific needs
  - Document environment variable requirements
  - Include troubleshooting section
- Create new root `README.md` tailored for the template
  - Clear title: "Claude Code Project Template"
  - Highlight key features (AI Developer Workflow, automated planning/implementation, slash commands)
  - Prerequisites section (Python, Node.js if needed, GitHub CLI, Claude Code, uv)
  - Quick start guide
  - Link to TEMPLATE_GUIDE.md for detailed instructions
  - Link to ADW documentation

### Step 2: Create Placeholder Application Structure
- Create `app/README.md` with guidance on application structure
  - Explain this directory is for your application code
  - Provide example structures for:
    - Python web app (FastAPI/Flask)
    - TypeScript/React web app
    - Python CLI tool
    - Node.js application
    - Single-file script
  - Explain how to integrate with scripts/start.sh
  - Environment variable best practices
- Remove all existing application code from `app/`
  - Delete `app/client/` directory entirely
  - Delete `app/server/` directory entirely

### Step 3: Update Scripts for Template Use
- Create new generic `scripts/start.sh`
  - Add clear comments explaining this is a template
  - Provide examples of different startup patterns
  - Include commented-out examples for:
    - Python server startup
    - Node.js app startup
    - Multiple service startup
    - Background process management
  - Keep the cleanup/trap functionality as a reusable pattern
- Update `scripts/stop_apps.sh` if needed
  - Make it more generic for any application
  - Add documentation comments
- Ensure all other scripts are documented
  - Add header comments explaining purpose
  - Add usage examples
  - Ensure they work independently of the old app

### Step 4: Clean Up Specifications
- Remove application-specific spec files
  - Delete `specs/fix-sql-injection-vulnerabilities.md`
  - Delete `specs/init_nlq_to_sql_to_table.md`
  - Delete `specs/query-history-panel.md`
  - Delete `specs/replace-print-with-logging.md`
- Create `specs/README.md`
  - Explain the purpose of the specs directory
  - Provide template for feature specs
  - Provide template for bug fix specs
  - Provide template for chore specs
  - Explain how specs are used in the ADW workflow
  - Include examples from past specs (sanitized/generic versions)

### Step 5: Update Environment Configuration
- Review `.env.sample` in project root
  - Ensure it has all ADW-required variables documented
  - Add comments explaining each variable
  - Include optional variables with explanations
- Create guidance for application-specific environment variables
  - Add section in TEMPLATE_GUIDE.md about extending .env.sample
  - Provide examples of common patterns

### Step 6: Verify and Document Infrastructure Components
- Review `.claude/commands/` directory
  - Ensure all commands are documented
  - Verify they work independently of the old app
  - Add usage notes to TEMPLATE_GUIDE.md
- Review `.claude/hooks/` directory
  - Verify hooks work with template structure
  - Document any customization points
  - Add troubleshooting notes
- Review `adws/` directory
  - Ensure all scripts are documented
  - Verify they work with cleaned structure
  - Update adws/README.md if needed for template context
- Verify `.claude/settings.json`
  - Review permissions to ensure they're appropriate for template
  - Document any customization points

### Step 7: Update .gitignore for Template
- Review current `.gitignore`
  - Ensure it covers common patterns for various project types
  - Add sections for:
    - Python projects
    - Node.js projects
    - Go projects
    - Rust projects
    - Database files
    - IDE files
  - Keep agent outputs, logs, trees excluded
- Add comments explaining each section

### Step 8: Create Example Project Guide
- Add to `TEMPLATE_GUIDE.md` a complete walkthrough
  - "Creating Your First Project with This Template"
  - Step-by-step example creating a simple application
  - Show how to use slash commands
  - Demonstrate the ADW workflow
  - Include GitHub issue workflow example

### Step 9: Clean Up Repository Artifacts
- Remove Zone.Identifier files (these are Windows/WSL artifacts)
  - Find and document these in the plan but note they'll be removed during implementation
- Ensure no application-specific artifacts remain
  - Check for orphaned config files
  - Check for unused dependencies references
  - Verify no hardcoded paths to old app

### Step 10: Validation
- Run validation commands to ensure template is clean and functional
- Verify documentation is complete and accurate
- Test that scripts run without errors (or provide appropriate guidance)

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `find . -name "*.md" -exec head -1 {} \;` - Verify all markdown files have proper headers
- `ls -la app/` - Verify app directory is clean with only README.md
- `ls -la specs/` - Verify specs directory is clean with only README.md
- `ls -la .claude/commands/` - Verify all slash commands are present
- `ls -la .claude/hooks/` - Verify all hooks are present
- `ls -la adws/` - Verify all ADW scripts are present
- `bash -n scripts/start.sh` - Verify start.sh has no syntax errors
- `bash -n scripts/stop_apps.sh` - Verify stop_apps.sh has no syntax errors
- `bash -n scripts/copy_dot_env.sh` - Verify copy_dot_env.sh has no syntax errors
- `cat README.md` - Verify new template README is comprehensive
- `cat TEMPLATE_GUIDE.md` - Verify template guide is complete
- `git status` - Check for any untracked or unexpected files

## Notes

### Design Decisions
1. **Preserve All Infrastructure**: The ADW system, slash commands, and hooks are the core value - preserve everything in `.claude/` and `adws/`
2. **Clean Slate for Application**: Remove all application-specific code to provide a blank canvas
3. **Comprehensive Documentation**: Since this is a template, documentation is critical - create extensive guides
4. **Multi-Language Support**: While the infrastructure is Python-based, the template should support starting projects in any language

### Future Enhancements
- Consider creating multiple template branches for different project types (python-web, node-api, cli-tool, etc.)
- Could add example projects in separate branches
- Might want to create a template initialization script that asks questions and sets up basics

### Key Benefits of This Template
1. **AI-First Development**: Built-in ADW workflow for automated planning and implementation
2. **GitHub Integration**: Seamless issue-to-PR workflow
3. **Quality Automation**: Slash commands for consistent development practices
4. **Extensible Hooks**: Customizable behavior for Claude Code interactions
5. **Production-Ready Infrastructure**: Logging, monitoring, and deployment helpers included
