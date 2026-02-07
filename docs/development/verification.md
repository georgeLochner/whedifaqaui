# Verification and Testing

This document defines the testing and quality gates for autonomous agentic development, ensuring code correctness before tasks are marked complete.

---

## Core Principle

**Never close a task with failing tests.**

Tests are the signal that implementation is correct. If tests fail, the implementation is incomplete or incorrect.

---

## Verification Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    Implement Feature                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Run Specified Tests                             │
│                                                              │
│  docker compose exec backend pytest tests/unit/...          │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
    ┌─────────┐         ┌─────────┐
    │  PASS   │         │  FAIL   │
    └────┬────┘         └────┬────┘
         │                   │
         │                   ▼
         │           ┌──────────────────┐
         │           │  Read Error      │
         │           │  Understand Issue│
         │           └────┬─────────────┘
         │                │
         │                ▼
         │           ┌──────────────────┐
         │           │  Fix Code        │
         │           └────┬─────────────┘
         │                │
         │                └──────┐
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Check for Regressions                              │
│                                                              │
│  Run related/integration tests to ensure no breakage        │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
    ┌─────────┐         ┌─────────┐
    │ No Reg. │         │  Reg!   │
    └────┬────┘         └────┬────┘
         │                   │
         │                   └─────► Fix regressions ──┐
         │                                             │
         │                    ┌────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Commit Code                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Close Task                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Categories

### 1. Unit Tests

**Scope**: Single function/class in isolation

**Purpose**: Verify individual components work correctly

**Location**: `tests/unit/`

**Running**:
```bash
# Run all unit tests
docker compose exec backend pytest tests/unit/ -v

# Run specific test file
docker compose exec backend pytest tests/unit/test_videos.py -v

# Run specific test function
docker compose exec backend pytest tests/unit/test_videos.py::test_upload_valid_file -v
```

**When to run**: After every code change

---

### 2. Integration Tests

**Scope**: Multiple components working together

**Purpose**: Verify components integrate correctly

**Location**: `tests/integration/`

**Running**:
```bash
# Run all integration tests
docker compose exec backend pytest tests/integration/ -v

# Run specific integration test
docker compose exec backend pytest tests/integration/test_video_pipeline.py -v
```

**When to run**: Before closing task, after unit tests pass

---

### 3. End-to-End Tests

**Scope**: Full user workflows

**Purpose**: Verify complete features work from user perspective

**Location**: `tests/e2e/`

**Running**:
```bash
# Run e2e tests (may require frontend running)
docker compose exec backend pytest tests/e2e/ -v
```

**When to run**: Phase completion, major feature completion

---

### 4. Regression Tests

**Scope**: Previously working functionality

**Purpose**: Ensure new changes don't break existing features

**Location**: `tests/regression/` or mixed throughout

**Running**:
```bash
# Run full regression pack
docker compose exec backend pytest tests/ -v

# Or run tests marked as regression
docker compose exec backend pytest -m regression -v
```

**When to run**: Before closing any task that modifies existing code

---

## Verification by Task Type

### New Feature Implementation

**Checklist**:
- [ ] Unit tests for new code pass
- [ ] Integration tests involving new feature pass
- [ ] Related existing tests still pass (no regressions)
- [ ] Manual verification (if applicable)

**Example**:
```bash
# Task: Add video upload endpoint

# 1. Run unit tests for upload functionality
docker compose exec backend pytest tests/unit/test_upload.py -v

# 2. Run integration tests for video pipeline
docker compose exec backend pytest tests/integration/test_video_pipeline.py -v

# 3. Run regression tests for video module
docker compose exec backend pytest tests/unit/test_videos.py -v

# 4. Manual verification
curl -X POST http://localhost:8000/api/videos \
  -F "file=@test.mp4" \
  -F "title=Test Video"
```

---

### Bug Fix

**Checklist**:
- [ ] Test that reproduced the bug now passes
- [ ] Related tests still pass
- [ ] No new edge cases introduced

**Process**:
1. Write test that reproduces bug (should fail)
2. Fix bug
3. Verify test now passes
4. Run related tests to check for regressions

**Example**:
```bash
# Task: Fix video playback timestamp parsing

# 1. Write test that demonstrates bug
# tests/unit/test_timestamp.py::test_parse_malformed_timestamp
# (This test should FAIL initially)

# 2. Fix the bug in code

# 3. Verify bug is fixed
docker compose exec backend pytest tests/unit/test_timestamp.py::test_parse_malformed_timestamp -v
# Should now PASS

# 4. Check for regressions
docker compose exec backend pytest tests/unit/test_timestamp.py -v
# All tests should PASS
```

---

### Refactoring

**Checklist**:
- [ ] All existing tests still pass
- [ ] No change in functionality (tests unchanged)
- [ ] Performance not degraded (if applicable)

**Example**:
```bash
# Task: Refactor video processing to use async/await

# Run full test suite before refactoring (establish baseline)
docker compose exec backend pytest tests/ -v > before.txt

# Perform refactoring

# Run full test suite after refactoring
docker compose exec backend pytest tests/ -v > after.txt

# Compare results
diff before.txt after.txt
# Should show no new failures
```

---

## Reading Test Failures

### Anatomy of a Test Failure

```
FAILED tests/unit/test_videos.py::test_upload_valid_file - AssertionError: assert 400 == 201

test_videos.py:45: AssertionError
----------------------------- Captured stdout ------------------------------
Response: {"error": "Invalid file type"}
```

**Key information**:
1. **Failed test**: `test_videos.py::test_upload_valid_file`
2. **Failure type**: `AssertionError`
3. **What went wrong**: Expected 201 (Created), got 400 (Bad Request)
4. **Additional context**: Response shows "Invalid file type" error

### Interpreting Common Failures

#### AssertionError

```python
assert response.status_code == 201
AssertionError: assert 400 == 201
```

**Meaning**: Expected value doesn't match actual value

**Action**: Check why actual differs from expected
- Is the implementation wrong?
- Is the test expectation wrong?
- Are test inputs correct?

---

#### AttributeError

```python
AttributeError: 'NoneType' object has no attribute 'id'
```

**Meaning**: Trying to access attribute on None

**Action**: Check why object is None
- Function returned None when it should return an object
- Database query returned no results
- Missing error handling

---

#### ImportError / ModuleNotFoundError

```python
ModuleNotFoundError: No module named 'app.api.routes.videos'
```

**Meaning**: Import failed

**Action**: Check if module exists and path is correct
- File not created yet?
- Typo in import path?
- Missing `__init__.py`?

---

#### Connection / Operational Errors

```python
psycopg2.OperationalError: could not connect to server
```

**Meaning**: Can't connect to external service

**Action**: Check service is running
```bash
docker compose ps
# Ensure postgres/redis/opensearch are healthy
```

---

## Manual Verification

When no automated tests exist or as additional verification:

### API Endpoints

```bash
# GET request
curl http://localhost:8000/api/videos

# POST request with JSON
curl -X POST http://localhost:8000/api/videos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "url": "https://..."}'

# POST with file upload
curl -X POST http://localhost:8000/api/videos \
  -F "file=@test.mp4" \
  -F "title=Test Video"

# Check response format
curl -s http://localhost:8000/api/videos/1 | jq .
```

---

### Database State

```bash
# Connect to database
docker compose exec postgres psql -U user -d dbname

# Check tables exist
\dt

# Check data
SELECT * FROM videos LIMIT 5;

# Check constraints
\d videos
```

---

### Python Imports

```bash
# Verify module can be imported
docker compose exec backend python -c "from app.api.routes.videos import router; print('OK')"

# Check what's exported
docker compose exec backend python -c "from app.api.routes import videos; print(dir(videos))"
```

---

### Logs

```bash
# Check application logs for errors
docker compose logs backend | tail -50

# Watch logs in real-time
docker compose logs -f backend

# Check worker logs
docker compose logs worker | grep -i error
```

---

## Quality Gates

### Before Committing

- [ ] Tests specified in task pass
- [ ] No obvious regressions (related tests pass)
- [ ] Code follows project conventions
- [ ] No debug code left in (print statements, commented code)

### Before Closing Task

- [ ] All acceptance criteria met
- [ ] All specified tests pass
- [ ] No regressions in integration tests
- [ ] Manual verification complete (if applicable)
- [ ] Code committed with clear message

### Before Phase Completion

- [ ] All phase tasks closed
- [ ] Full regression test suite passes
- [ ] Phase test specification verified (see `docs/testing/phase<N>-test-specification.md`)
- [ ] Integration with previous phases verified
- [ ] Documentation updated

---

## Test Writing Guidelines

If tests don't exist and you need to create them:

### Good Test Structure

```python
def test_upload_valid_video():
    """Test that uploading a valid video succeeds."""
    # Arrange - Set up test data
    video_file = create_test_video("test.mp4")

    # Act - Perform the action
    response = client.post("/api/videos", files={"file": video_file})

    # Assert - Check results
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["status"] == "processing"
```

### Test Naming

- **Descriptive**: `test_upload_rejects_invalid_format` not `test_upload_1`
- **Clear intent**: Name should explain what's being tested
- **Consistent**: Follow project conventions

### Test Independence

- Each test should be runnable in isolation
- Don't depend on test execution order
- Clean up after yourself (database, files, etc.)

---

## Using Pytest Effectively

### Running Specific Tests

```bash
# Single test
docker compose exec backend pytest tests/unit/test_videos.py::test_upload -v

# All tests in a file
docker compose exec backend pytest tests/unit/test_videos.py -v

# All tests in a directory
docker compose exec backend pytest tests/unit/ -v

# Tests matching a pattern
docker compose exec backend pytest -k "upload" -v
```

### Useful Pytest Flags

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# Show coverage
pytest --cov=app tests/

# Run in parallel (if pytest-xdist installed)
pytest -n auto
```

### Debugging Failed Tests

```bash
# Run with full output
docker compose exec backend pytest tests/unit/test_videos.py -v -s

# Drop into debugger on failure (if pdb installed)
docker compose exec backend pytest tests/unit/test_videos.py --pdb

# Show local variables in tracebacks
docker compose exec backend pytest tests/unit/test_videos.py -l
```

---

## Common Verification Mistakes

### ❌ Closing Task Without Running Tests

```bash
# WRONG
# ... implement feature ...
bd close <task-id>
# (never ran tests)
```

**Why wrong**: No verification that code works

**Correct**:
```bash
# Implement feature
docker compose exec backend pytest tests/unit/test_feature.py -v
# Verify tests pass
bd close <task-id>
```

---

### ❌ Modifying Tests to Make Them Pass

```python
# WRONG
def test_upload():
    response = upload_video("test.mp4")
    # Changed from 201 to 400 to match broken implementation
    assert response.status_code == 400  # WRONG!
```

**Why wrong**: Test no longer verifies correct behavior

**Correct**: Fix the implementation, not the test

---

### ❌ Ignoring Regressions

```bash
# WRONG
$ docker compose exec backend pytest tests/
# 2 new failures in unrelated tests
# (ignore and close task anyway)
```

**Why wrong**: New changes broke existing functionality

**Correct**: Fix regressions before closing task

---

### ❌ Testing in Wrong Environment

```bash
# WRONG
$ pytest tests/  # Running on host, not in container
```

**Why wrong**: May not have correct dependencies, environment variables, etc.

**Correct**: Always run tests in container environment

---

## Checklist Summary

**Before every commit**:
- [ ] Relevant tests pass
- [ ] Code is correct and complete for what you're committing

**Before closing task**:
- [ ] All acceptance criteria met
- [ ] All specified tests pass
- [ ] No new test failures (regressions)
- [ ] Manual verification (if needed)
- [ ] Code committed

**If tests fail**:
- [ ] Read error message carefully
- [ ] Understand what's expected vs actual
- [ ] Fix implementation (not test)
- [ ] Re-run until passing
- [ ] Check for regressions

**Never**:
- ❌ Close task with failing tests
- ❌ Modify tests to make them pass
- ❌ Skip regression testing
- ❌ Test in wrong environment
