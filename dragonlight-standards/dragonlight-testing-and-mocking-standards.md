# Dragonlight Testing & Mocking Standards

**Owner:** [REDACTED PERSONA]
**Status:** Active — applies to all Dragonlight code
**Origin:** Session 75e, evolved from enforcement engine mocking strategy (Hermes plan 2026-04-26)
**Companion:** `dragonlight-coding-standards.md`, `dragonlight-development-pipeline.md`, `dragonlight-property-based-testing-strategy.md`, `dragonlight-integration-verification-strategy.md`, `dragonlight-security-specification.md`, `dragonlight-security-implementation-standard.md`

---

## Core Principle

Tests verify that the system does what the spec says it does. Unit tests verify logic in isolation. Integration tests verify that components work together. The boundary between them is the **interface seam** — the point where your code calls an external dependency.

---

## Test Types

### Unit Tests

**Purpose:** Fast feedback on logic correctness. Run in <10ms per test.

**What they test:** Internal logic, data transformations, state machines, business rules, type construction, error handling paths.

**What they mock:** External dependencies AT THE SEAM — the function boundary where your code calls out to something it doesn't own. Databases, filesystems, network services, external CLI tools, system clock, random number generators.

**What they do NOT mock:** Internal functions, pure functions, standard library operations that are stable and deterministic (string manipulation, math, collections). Test these directly.

**The rule:** If you're mocking an internal function to test another internal function, you're testing implementation, not behavior. Stop. Call the function directly.

### Integration Tests

**Purpose:** Verify that components work together through real interfaces.

**What they test:** The actual tool interface. Call the real tool (database, CLI tool, API client). Use temporary directories, disposable databases, test fixtures.

**What they mock:** Nothing in the happy path. Mock only truly external services that can't be spun up locally (third-party APIs). For everything else — real tool, real interface, real behavior.

**Speed:** Expected to be slower (100ms-5s per test). That's acceptable.

### Smoke Tests

**Purpose:** End-to-end verification that the full pipeline works.

**What they test:** Golden path through the entire system. Create real data, run real operations, verify real output.

**What they mock:** Nothing. These exercise the real system.

### Property-Based Tests

Comprehensive property-based testing strategy — including property taxonomy, consequence classification requirements, Hypothesis configuration, domain strategy library patterns, build pipeline integration, and agent-generated code verification protocol — is specified in `dragonlight-property-based-testing-strategy.md`. That document is the authoritative reference for all property-based testing in Dragonlight code.

---

## The Interface Seam Pattern

The seam is where your code meets code you don't own. This is the ONLY place mocks belong in unit tests.

```
YOUR CODE              SEAM              EXTERNAL
┌──────────┐     ┌──────────────┐     ┌──────────┐
│ business │ ──> │  interface   │ ──> │  sqlite3  │
│  logic   │     │  function    │     │  kopia    │
│          │     │  (mock here) │     │  age      │
└──────────┘     └──────────────┘     └──────────┘
     ^                                     
  test this              don't test this
  directly               in unit tests
```

### Identifying Seams

A function is a seam when it:
- Calls `subprocess.run()` or `os.system()` (external CLI tool)
- Opens a database connection (`sqlite3.connect()`, connection pool)
- Makes a network request (HTTP, gRPC, WebSocket)
- Reads/writes the filesystem beyond the test's temp directory
- Calls `time.time()`, `datetime.now()`, `random.*` for non-deterministic behavior
- Imports and calls a heavy external library (spaCy, ML models)

### Mock Design at Seams

Mocks at seams must be **realistic** — they return the same shape of data the real dependency returns, and they fail in the same ways.

```python
# GOOD: Realistic mock that returns real-shaped data
@pytest.fixture
def mock_kopia_snapshot():
    return KopiaSnapshotResult(
        snapshot_id="snapshot-id",
        source="/path/to/data",
        start_time="2026-04-26T18:30:00Z",
        end_time="2026-04-26T18:30:45Z",
        total_size=75_000_000,
        files_hashed=2341,
        status="success",
    )

# BAD: Mock that returns unrealistic data
@pytest.fixture
def mock_kopia_snapshot():
    return {"ok": True}  # Not what Kopia actually returns
```

---

## Mocking Rules

### DO Mock

| Dependency | Why | How |
|---|---|---|
| Database connections | Slow, stateful, test-order-dependent | In-memory SQLite for integration; Mock connection for unit |
| External CLI tools (backup, encryption, linting, version control) | Not available in CI, slow, side effects | Mock `subprocess.run` at the seam function |
| Network/HTTP calls | Flaky, slow, requires running services | `respx` (async) or `responses` (sync) |
| System clock | Non-deterministic | `freezegun` or mock `time.time`/`datetime.now` |
| Random number generators | Non-deterministic | Mock `random.choice`/`random.randint` with fixed seed or mock |
| Heavy ML models (NLP, computer vision, etc.) | 500ms+ load time | Interface + mock pattern (SpacyInterface/SpacyMock) |
| Filesystem operations on real paths | Side effects outside test dir | Mock or use `tmp_path` fixture |

### DO NOT Mock

| Dependency | Why |
|---|---|
| Pure functions in your own code | Test them directly — they're deterministic |
| Standard library string/math/collections | Stable, fast, deterministic |
| Frozen dataclasses and type constructors | Test construction directly — that's the point |
| Result type operations (map, bind, flow) | Part of the logic under test |
| Internal helper functions | If you need to mock an internal to test another internal, the design needs refactoring, not more mocks |

---

## Anti-Patterns

### 1. Integration Test Masquerading as Unit Test

```python
# BAD: Hits real database in a "unit" test
def test_load_rules():
    conn = sqlite3.connect("test.db")
    rules = load_rules(conn)
    assert len(rules) > 0
```

If it touches a real database, real filesystem, or real external tool — it's an integration test. Label it correctly and put it in the right directory.

### 2. Mocking Too Much (Testing the Mock, Not the Code)

```python
# BAD: Three layers of mocks, testing that mocks were called
with patch('module.func1') as m1, \
     patch('module.func2') as m2, \
     patch('module.func3') as m3:
    result = module.pipeline()
    assert m1.called and m2.called and m3.called
```

If your test only asserts that mocks were called, it verifies wiring, not behavior. Test the output, not the call graph.

### 3. Complex Mock with Its Own Logic

```python
# BAD: Mock that reimplements the dependency
class SmartMock:
    def analyze(self, text):
        if "question" in text:
            return {"type": "question"}
        elif "!" in text:
            return {"type": "exclamation"}
        else:
            return {"type": "statement"}
```

A mock with branching logic can have its own bugs. Mocks should be simple and stupid — return fixed data, raise fixed errors.

### 4. Mocking Internals Instead of Seams

```python
# BAD: Mocking an internal helper to test the caller
def test_process():
    with patch('mymodule._validate_input', return_value=True):
        result = mymodule.process(data)
```

If `_validate_input` is an internal function, test it directly. Don't mock it to test `process()`. If `process()` is hard to test without mocking its internals, the function is doing too much — split it.

### 5. Not Mocking Unstable Dependencies

```python
# BAD: Real external service in unit test
def test_backup():
    result = subprocess.run(["kopia", "snapshot", "create", "/path"])
    assert result.returncode == 0
```

This fails when Kopia isn't installed, when the path doesn't exist, when the repository isn't initialized. It belongs in integration tests.

---

## Test Structure

### Directory Layout

```
tests/
├── unit/                    # Fast, mocked at seams, <10ms per test
│   ├── test_types.py
│   ├── test_logic.py
│   └── conftest.py          # Shared mock fixtures
├── integration/             # Real tools, real interfaces, slower
│   ├── test_kopia.py
│   ├── test_sqlite.py
│   └── conftest.py          # Real resource fixtures (tmp_path, temp db)
├── smoke/                   # End-to-end golden path
│   └── test_full_pipeline.py
└── conftest.py              # Top-level shared fixtures
```

### Naming Conventions

- `test_<module>_<behavior>.py` — file names describe what's tested
- `test_<action>_<condition>` — function names describe action and condition
- `Test<Component>` — class names group related tests
- Fixtures named for what they provide, not how: `populated_db` not `setup_test_database`

### Fixture Design

```python
@pytest.fixture
def populated_db(tmp_path):
    """In-memory database with seed data for testing."""
    conn = sqlite3.connect(":memory:")
    # ... setup schema and seed data ...
    yield conn
    conn.close()

@pytest.fixture
def mock_kopia_engine(mocker):
    """Kopia engine mock that returns realistic snapshot results."""
    mock = mocker.patch("[REDACTED]_dds.backup.engine.run_kopia")
    mock.return_value = Success(KopiaSnapshotResult(...))
    return mock
```

---

## Coverage Targets

Per the Dragonlight development pipeline, coverage targets are consequence-classified:

| Consequence Level | Coverage Target | Verification Method |
|---|---|---|
| Critical | MC/DC (Modified Condition/Decision Coverage) | Every condition independently affects the decision |
| Standard | Branch coverage (100% of branches exercised) | Every if/else, match arm, error path |
| Utility | Statement coverage (100% of statements executed) | Every line runs at least once |

The consequence classification comes from the hazard analysis (Stage 1 of the pipeline). It is not a blanket percentage — it is targeted based on what the code does and what happens if it's wrong.

---

## Traceability

Every test must trace back to a requirement in the specification:

```python
class TestBudgetCheck:
    """Spec: DDS-001 Section 5.3 — Budget Verification"""

    def test_remaining_budget_with_usage(self, populated_db):
        """Req DDS-001-5.3.1: remaining_budget returns limit minus usage."""
        ...

    def test_remaining_budget_null_limit(self, populated_db):
        """Req DDS-001-5.3.2: NULL limit means unlimited — returns None."""
        ...
```

No orphan tests (tests without a requirement). No orphan requirements (requirements without a test).

---

## Recommended Libraries

| Library | Purpose | Notes |
|---|---|---|
| pytest | Test runner | Standard. Use fixtures, parametrize, markers. |
| pytest-mock | Mocker fixture | Cleaner syntax than `unittest.mock.patch` |
| freezegun | Time mocking | `@freeze_time("2026-04-26")` for deterministic timestamps |
| respx | HTTP mocking (async) | For httpx-based clients |
| responses | HTTP mocking (sync) | For requests-based clients |
| hypothesis | Property-based testing | For discovering edge cases |
| tmp_path (pytest built-in) | Temp directory fixture | For filesystem isolation |

All are lightweight, well-maintained, and replaceable (per coding standards: "minimal dependency surface").

---

## Checklist for New Test Files

Before submitting tests:

- [ ] Unit tests mock only at interface seams
- [ ] No unit test hits a real database, filesystem, network, or external tool
- [ ] Mocks return realistic data shapes (not `{"ok": True}`)
- [ ] Mock error paths return realistic error shapes
- [ ] Integration tests use real tools with disposable resources
- [ ] Every test function references a spec requirement
- [ ] Fixtures are named for what they provide, not how they work
- [ ] No test has more than 2 levels of mocking depth
- [ ] No mock contains branching logic
- [ ] Coverage meets the consequence-classified target for the module

---

*[REDACTED] — 2026*
