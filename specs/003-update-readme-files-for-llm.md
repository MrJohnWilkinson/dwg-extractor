# Chore: Update README Files for LLM Agent Clarity

## Chore Description
Update all README.md files in the project to be concise and optimized for LLM agent consumption. Each README must be 150 lines or fewer, focusing on essential information that helps LLM agents understand the purpose, structure, and usage of each component. Remove verbose examples, lengthy templates, and redundant documentation while preserving critical information about the application architecture, workflow, and implementation guidelines.

## Relevant Files
Use these files to resolve the chore:

### Files to Modify
- **`README.md`** (currently empty/1 line) - Create a concise project overview explaining the DWG Block Extractor application to LLM agents. Should include: what the app does, tech stack, project structure, current phase, and quick start commands. Target: ~80-100 lines.

- **`app/README.md`** (currently 536 lines) - Drastically reduce from 536 to ≤150 lines. Keep: Python project structure for DWG extractor, uv usage, core directory layout, testing commands, and integration with scripts/start.sh. Remove: extensive examples for Flask/React/Go/Rust, multi-service examples, and verbose configuration examples that aren't relevant to this Python GUI application.

- **`specs/README.md`** (currently 446 lines) - Reduce from 446 to ≤150 lines. Keep: purpose of specs, ADW workflow, spec file structure (condensed template), naming conventions, and validation requirements. Remove: lengthy examples (User Authentication, Database Connection Leak), redundant template variations, and verbose best practices sections.

- **`.claude/commands/README.md`** (currently 106 lines) - Already under 150 lines but could be slightly condensed. Keep: heading standards, variables/arguments usage, directory organization, command invocation format. Ensure it stays focused on LLM agent needs.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Concise Project README
- Create `README.md` with the following sections:
  - Project title and one-sentence description
  - Purpose: What the DWG Block Extractor does (extract block counts from DWG/DXF → Excel)
  - Tech Stack: Python 3.11+, ezdxf, pandas, openpyxl, customtkinter, managed by uv
  - Project Structure: High-level overview of app/, specs/, scripts/, .claude/ directories
  - Current Status: Phase 1 complete (setup), Phase 2 next (core logic)
  - Quick Start: How to run the app (`scripts/start.sh`), run tests, install dependencies
  - Development Workflow: Brief mention of ADW and slash commands
  - Implementation Plan: Reference to ai_output/002-implementation-plan.md
- Target length: 80-100 lines
- Write in concise, technical language optimized for LLM parsing

### Step 2: Condense app/README.md
- Reduce from 536 lines to maximum 150 lines
- Keep these sections:
  - Application Directory purpose (2-3 lines)
  - Python Desktop Application structure (DWG extractor specific, ~30 lines)
  - pyproject.toml example with actual dependencies (ezdxf, pandas, openpyxl, customtkinter)
  - Testing section with pytest commands (~10 lines)
  - Environment variables section (condensed, ~10 lines)
  - Integration with scripts/start.sh (~10 lines)
- Remove entirely:
  - Flask, React/TypeScript, Node.js, Go, Rust examples
  - Multi-service application examples
  - Extensive environment variable examples
  - ADW integration examples (move brief mention to main README)
  - Verbose best practices section
- Reorganize to be laser-focused on this Python GUI application's structure

### Step 3: Condense specs/README.md
- Reduce from 446 lines to maximum 150 lines
- Keep these sections:
  - Purpose and ADW workflow (condensed to ~15 lines)
  - Single unified spec template showing all required sections (~40 lines):
    - Feature/Bug/Chore Description
    - Relevant Files
    - Step by Step Tasks
    - Validation Commands
    - Notes
  - Naming conventions (~10 lines)
  - Validation command guidelines (~10 lines)
  - Using specs with Claude Code (~10 lines)
  - Brief integration with GitHub issues (~10 lines)
- Remove entirely:
  - Separate templates for Feature/Bug/Chore (consolidate into one)
  - Lengthy User Authentication example
  - Lengthy Database Connection Leak example
  - Verbose best practices section with examples
  - Spec file lifecycle diagram
  - Tips for ADW Success section (redundant)
  - Common pitfalls section (too verbose)
- Focus on what LLM agents need: structure, required sections, validation importance

### Step 4: Review .claude/commands/README.md
- Currently 106 lines, already under 150 limit
- Make minor condensations if possible:
  - Reduce Variables and Arguments section slightly if verbose
  - Condense examples to one-liners
  - Ensure Directory Organization section is concise
- Target: Keep under 100 lines if possible
- Preserve all essential information about command structure and invocation

### Step 5: Validate Line Counts
- Run `wc -l` on all updated README files
- Verify each file is ≤150 lines (with .claude/commands/README.md ideally under 100)
- Verify README.md is 80-100 lines
- Ensure no critical information was lost during condensation

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `wc -l README.md` - Verify main README is 80-100 lines
- `wc -l app/README.md` - Verify app README is ≤150 lines
- `wc -l specs/README.md` - Verify specs README is ≤150 lines
- `wc -l .claude/commands/README.md` - Verify commands README is ≤150 lines (ideally <100)
- `cat README.md` - Manually verify content is clear and comprehensive for LLM agents
- `cat app/README.md | head -20` - Verify app README focuses on Python GUI structure
- `cat specs/README.md | grep -A 5 "Template"` - Verify unified template exists
- `test -f README.md && test -s README.md && echo "README.md exists and is not empty"` - Verify file exists

## Notes

### Design Decisions
1. **LLM-First Writing**: All content written in concise, technical language that LLM agents can quickly parse and understand. Remove conversational tone and verbose explanations.

2. **150-Line Hard Limit**: Enforced to ensure LLMs can consume README files efficiently without hitting context limits or wasting tokens on redundant information.

3. **Remove Irrelevant Examples**: This project is a Python GUI application using ezdxf/customtkinter. Examples for Flask, React, Go, Rust, etc. are noise for LLM agents working on this codebase.

4. **Consolidate Templates**: Instead of 3 separate spec templates (Feature, Bug, Chore), provide one unified template showing all possible sections. LLMs can adapt based on task type.

5. **Preserve Critical Information**:
   - Project structure and organization
   - Tech stack and dependencies
   - Workflow and command usage
   - Validation requirements
   - File organization patterns

### Focus for Each README
- **Main README.md**: "What is this project and how do I work with it?"
- **app/README.md**: "How is the application code structured?"
- **specs/README.md**: "How do I write implementation plans?"
- **.claude/commands/README.md**: "How do slash commands work?"

### Writing Style for LLMs
- Use bullet points and tables over paragraphs
- Include code blocks only when showing actual file content
- Use section headers for quick navigation
- Avoid redundancy and repetition
- Front-load critical information
- Use precise technical terminology
