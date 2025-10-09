# Specifications Directory

This directory contains implementation plans and technical specifications for features, bugs, and chores. These specs are used by the AI Developer Workflow (ADW) system to guide implementation.

## Purpose

Specification files serve as:
- **Planning documents** - Detailed blueprints for implementation
- **Implementation guides** - Step-by-step instructions for Claude Code
- **Documentation** - Record of design decisions and approach
- **Communication** - Clear description of requirements and acceptance criteria

## How Specs Work with ADW

The ADW workflow creates and uses spec files:

1. **GitHub Issue Created** → User creates an issue
2. **Classification** → `/classify_issue` determines type (bug/feature/chore)
3. **Planning** → `sdlc_planner` agent creates a spec file in this directory
4. **Implementation** → `sdlc_implementor` agent reads the spec and implements it
5. **PR Creation** → Changes are committed and PR is created with spec reference

## Spec File Templates

### Feature Specification Template

Create a new file: `specs/feature-name.md`

```markdown
# Feature: [Feature Name]

## Feature Description
[1-2 paragraphs describing what this feature does and why it's needed]

## Relevant Files
- `path/to/file1.py` - [What will change and why]
- `path/to/file2.ts` - [What will change and why]
- `path/to/new_file.py` - [New file, what it will contain]

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: [First Major Task]
- [Specific action item]
- [Specific action item]
- [Specific action item]

### Step 2: [Second Major Task]
- [Specific action item]
- [Specific action item]

### Step 3: [Third Major Task]
- [Specific action item]
- [Specific action item]

[Continue with all steps...]

## Validation Commands
Execute every command to validate the feature is complete with zero regressions.

- `command to test 1` - Description of what this validates
- `command to test 2` - Description of what this validates
- `command to test 3` - Description of what this validates

## Notes

### Design Decisions
1. **[Decision 1]**: [Rationale]
2. **[Decision 2]**: [Rationale]

### Future Enhancements
- [Possible improvement 1]
- [Possible improvement 2]

### Dependencies
- [External library or API needed]
- [Other features this depends on]
```

### Bug Fix Specification Template

Create a new file: `specs/fix-bug-description.md`

```markdown
# Bug Fix: [Bug Description]

## Bug Description
[Detailed description of the bug, including symptoms and impact]

## Root Cause
[Analysis of what's causing the bug]

## Relevant Files
- `path/to/buggy_file.py` - [What's wrong and how to fix it]
- `path/to/related_file.ts` - [Related changes needed]
- `path/to/test_file.py` - [Tests to add/update]

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Reproduce the Bug
- [How to trigger the bug]
- [Expected vs actual behavior]
- [Verification steps]

### Step 2: Implement the Fix
- [Specific code changes needed]
- [Files to modify]
- [Approach to take]

### Step 3: Add Tests
- [Test cases to prevent regression]
- [Edge cases to cover]

### Step 4: Verify the Fix
- [Validation steps]
- [Integration testing]

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `command to reproduce bug` - Should no longer exhibit buggy behavior
- `pytest path/to/tests` - All tests should pass
- `command to test edge case 1` - Edge case validation
- `command to test edge case 2` - Edge case validation

## Notes

### Root Cause Analysis
[Detailed explanation of why the bug occurred]

### Prevention
[How to prevent similar bugs in the future]

### Related Issues
- [Link to related GitHub issues or PRs]
```

### Chore Specification Template

Create a new file: `specs/chore-description.md`

```markdown
# Chore: [Chore Description]

## Chore Description
[Description of maintenance, refactoring, or infrastructure work]

## Relevant Files
- `path/to/file1.py` - [Changes needed]
- `path/to/file2.ts` - [Changes needed]

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: [First Task]
- [Specific action item]
- [Specific action item]

### Step 2: [Second Task]
- [Specific action item]
- [Specific action item]

[Continue with all steps...]

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `command 1` - Validation description
- `command 2` - Validation description

## Notes

### Design Decisions
[Explain choices made during implementation]

### Future Improvements
[Suggestions for future enhancement]
```

## Example Specifications

### Example 1: User Authentication Feature

```markdown
# Feature: Add User Authentication

## Feature Description
Implement JWT-based authentication system with login and logout endpoints. Users will be able to create accounts, log in with email/password, and receive JWT tokens for authenticated API access.

## Relevant Files
- `app/src/api/auth.py` - New file with authentication endpoints
- `app/src/models/user.py` - New User model with password hashing
- `app/src/middleware/auth.py` - JWT validation middleware
- `app/src/main.py` - Register auth routes and middleware
- `app/tests/test_auth.py` - New authentication tests
- `app/pyproject.toml` - Add dependencies (PyJWT, passlib)

## Step by Step Tasks

### Step 1: Install Dependencies
- Add `PyJWT>=2.8.0` to pyproject.toml
- Add `passlib[bcrypt]>=1.7.4` to pyproject.toml
- Run `uv sync` to install

### Step 2: Create User Model
- Create `app/src/models/user.py`
- Add User class with fields: id, email, hashed_password, created_at
- Implement password hashing with bcrypt
- Implement password verification method

### Step 3: Create Authentication Endpoints
- Create `app/src/api/auth.py`
- Implement POST /auth/register endpoint
- Implement POST /auth/login endpoint (returns JWT)
- Implement POST /auth/logout endpoint
- Add proper error handling and validation

### Step 4: Create JWT Middleware
- Create `app/src/middleware/auth.py`
- Implement JWT token creation function
- Implement JWT token validation middleware
- Handle token expiration and invalid tokens

### Step 5: Integrate with Main Application
- Update `app/src/main.py` to register auth routes
- Add JWT middleware to protected routes
- Configure JWT secret from environment

### Step 6: Write Tests
- Create `app/tests/test_auth.py`
- Test user registration (success and failures)
- Test login (success and failures)
- Test protected endpoints with/without valid tokens
- Test token expiration
- Achieve >90% code coverage

## Validation Commands

- `cd app && uv run pytest tests/test_auth.py -v` - All auth tests pass
- `cd app && uv run pytest --cov=src/api/auth --cov=src/models/user --cov=src/middleware/auth` - Coverage >90%
- `cd app && uv run uvicorn src.main:app --reload` - Server starts without errors
- `curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"password123"}'` - Returns 201
- `curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"password123"}'` - Returns JWT token

## Notes

### Design Decisions
1. **JWT over Sessions**: Stateless authentication for easier scaling
2. **bcrypt for Password Hashing**: Industry standard, secure
3. **Environment-based Secret**: Never hardcode JWT secrets

### Future Enhancements
- Add refresh tokens for extended sessions
- Implement password reset functionality
- Add OAuth providers (Google, GitHub)
- Rate limiting on auth endpoints

### Dependencies
- PyJWT: For JWT token creation and validation
- passlib: For secure password hashing
```

### Example 2: Fix Database Connection Leak

```markdown
# Bug Fix: Database Connection Pool Exhaustion

## Bug Description
Application crashes after prolonged use with error "Too many connections". Database connections are not being properly returned to the pool, causing resource exhaustion under moderate load.

## Root Cause
Database query functions are not using context managers, leading to connections remaining open when exceptions occur. The connection pool reaches max capacity after ~100 requests.

## Relevant Files
- `app/src/services/database.py` - Missing context managers for connections
- `app/src/api/routes.py` - Endpoints using database without proper cleanup
- `app/tests/test_database.py` - Add connection pool tests

## Step by Step Tasks

### Step 1: Reproduce the Bug
- Start application
- Run load test: `ab -n 200 -c 10 http://localhost:8000/api/users`
- Observe "Too many connections" error after ~100 requests
- Check connection pool metrics

### Step 2: Implement Connection Context Manager
- Update `database.py` to use context managers
- Ensure all `get_connection()` calls use `with` statement
- Add automatic rollback on exceptions
- Add connection pool monitoring

### Step 3: Update All Database Queries
- Update `routes.py` to use new context manager
- Update all database service methods
- Ensure connections are released in finally blocks

### Step 4: Add Connection Pool Configuration
- Add configurable pool size from environment
- Add connection timeout configuration
- Add pool overflow limit

### Step 5: Add Tests
- Create connection pool stress tests
- Test connection release on exceptions
- Test pool exhaustion handling
- Verify no leaks under load

## Validation Commands

- `cd app && uv run pytest tests/test_database.py::test_connection_pool -v` - Connection pool tests pass
- `cd app && uv run pytest tests/test_database.py::test_connection_leak -v` - No leaks detected
- `ab -n 500 -c 20 http://localhost:8000/api/users` - All requests succeed
- `curl http://localhost:8000/metrics | grep db_connections` - Pool metrics within limits

## Notes

### Root Cause Analysis
The original implementation called `connection.close()` explicitly, but exceptions would skip the close statement. Using context managers ensures cleanup even on exceptions.

### Prevention
- Code review checklist: Always use context managers for resources
- Add pre-commit hook to detect missing context managers
- Monitor connection pool metrics in production

### Related Issues
- GitHub issue #123: Connection timeout errors
- Similar pattern in cache connection handling (future fix needed)
```

## Best Practices

### Writing Effective Specs

1. **Be Specific**: Provide exact file paths, function names, and code snippets
2. **Order Matters**: Number steps that must be executed in sequence
3. **Include Validation**: Always provide commands to verify completion
4. **Think About Edge Cases**: Cover error handling and edge cases
5. **Document Decisions**: Explain "why" not just "what"

### Naming Conventions

Use descriptive file names:
- Features: `feature-name-description.md`
- Bugs: `fix-bug-description.md`
- Chores: `chore-task-description.md`

Examples:
- `add-user-authentication-system.md`
- `fix-database-connection-leak.md`
- `refactor-api-error-handling.md`
- `upgrade-python-dependencies.md`

### Validation Commands

Always include validation commands that:
- **Test functionality**: Verify the feature works
- **Test edge cases**: Cover error scenarios
- **Run tests**: Execute test suite
- **Check regressions**: Ensure nothing broke
- **Verify quality**: Run linters, type checkers

## Using Specs with Claude Code

### Manual Implementation

```bash
# With a spec file already created
claude /implement @specs/feature-name.md
```

### ADW Automatic Implementation

```bash
# ADW creates spec and implements automatically
cd adws
uv run adw_plan_build.py <issue-number>
```

### Creating Specs Manually

```bash
# Use the /feature, /bug, or /chore commands
claude /feature @<issue-url>
claude /bug @<issue-url>
claude /chore @<issue-url>
```

## Integration with GitHub Issues

When ADW processes a GitHub issue:

1. Issue is classified as bug/feature/chore
2. Spec is created in this directory based on template
3. Spec file name includes issue number: `feature-42-user-auth.md`
4. Implementation follows spec exactly
5. PR references the spec file
6. Spec becomes documentation of what was built

## Spec File Lifecycle

```
1. Creation      → Spec written based on GitHub issue
2. Review        → Spec reviewed for completeness
3. Implementation → Claude Code follows spec
4. Validation    → Validation commands executed
5. Archive       → Spec remains as documentation
```

## Tips for ADW Success

1. **Detailed GitHub Issues**: More detail = better specs
2. **Include Examples**: Show expected behavior in issues
3. **Specify Tests**: Mention test requirements in issues
4. **Reference Files**: Mention relevant files in issues
5. **Acceptance Criteria**: Clear definition of "done"

## Common Pitfalls

❌ **Vague Steps**: "Update the code"
✅ **Specific Steps**: "Update `src/api/routes.py` line 42 to add error handling"

❌ **No Validation**: Missing test commands
✅ **Clear Validation**: "Run `pytest tests/test_api.py::test_error_handling`"

❌ **Missing Context**: "Fix the bug"
✅ **Detailed Context**: "Fix NullPointerException in UserService.getUser() when user_id is None"

❌ **No Edge Cases**: Only happy path
✅ **Comprehensive**: "Test with valid user, invalid user, missing user, and null user"

## Resources

- **ADW Documentation**: See `adws/README.md`
- **Template Guide**: See `TEMPLATE_GUIDE.md`
- **Slash Commands**: Run `claude /tools` to see all commands

## Next Steps

1. **Review Templates**: Understand the structure above
2. **Create Your First Spec**: Use a template for your next feature
3. **Test with Claude Code**: Run `/implement @specs/your-spec.md`
4. **Iterate**: Refine based on results

Good specs lead to better implementations. Take time to write detailed, actionable specifications and Claude Code will deliver high-quality results.
