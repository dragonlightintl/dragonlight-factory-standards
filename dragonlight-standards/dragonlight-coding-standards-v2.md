# Dragonlight Coding Standards v2

**Owner:** [REDACTED PERSONA]
**Status:** Active — applies to all Dragonlight code
**Origin:** v1 (Session 36-37), upgraded Session 85e with empirical research
**Predecessor:** `dragonlight-coding-standards.md` (v1, retained as historical baseline)
**Companion:** `dragonlight-documentation-standard.md`, `dragonlight-security-implementation-standard.md`, `dragonlight-testing-and-mocking-standards.md`

---

## Core Values

Retained from v1. Every line of code embodies: billion-dollar quality, illegal states unrepresentable, constraints before code, rigor proportional to consequence, the ability to stop, clean, enterprise-grade but light, functional, immaculate, bulletproof, secure, stable, clear, simple, easy to read/debug/repair/scale/build upon/maintain/instrument, high availability, iconic.

See v1 for the full articulation of each value.

---

## What Changed in v2

v1 stated principles. v2 adds the mechanical shapes that enforce them. Every addition below is backed by empirical research, defect-rate data, or expert consensus from 70+ years of software engineering. Evidence tags: [RESEARCH-BACKED], [EXPERT CONSENSUS].

**Key gaps closed:**
- Conventions named concepts (railway-oriented, Result types) but not the code shapes — agents followed the letter while violating the spirit
- No canonical Result type — every build reinvented it incorrectly
- No main() decomposition — every build produced 60-75 line main functions
- No guard clause prescription — agents produced nested try-except pyramids
- No test body enforcement — 29 empty test stubs passed the build gate
- Rule priority was ambiguous — agents treated hard limits as suggestions

---

## Language & Runtime

Python 3.11+. Type annotations on every function signature. Stdlib first — external dependencies require justification. No `eval()`, `exec()`, `pickle`. No bare `except`. No `pass` in error handlers.

---

## Result Type (Canonical)

Do not reinvent. Use this exact pattern. [EXPERT CONSENSUS]

```python
@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

Result = Ok[T] | Err[E]
```

Check with `isinstance(result, Ok)` / `isinstance(result, Err)`. This is a true sum type — there is no "neither Ok nor Err" state. Do not use a single class with Optional fields. Do not use a facade that returns raw values.

For Python 3.9: `Result = Union[Ok[T], Err[E]]`.

If the project uses `dry-python/returns`, use its `Result` type instead of rolling your own.

---

## Function Design

### Length

**Hard limit: 40 lines per function.** [RESEARCH-BACKED]

Defect density follows a U-curve: highest in very small functions (<15 lines, 23% higher error density per line — Basili & Perricone 1984) and very large ones (>200 lines). The sweet spot is 20-60 lines (McConnell, NASA JPL). The 40-line limit sits in this sweet spot.

Do NOT write 3-4 line functions in the Clean Code style. Empirical data shows these have higher defect density per line than medium functions. Prefer a single well-structured function over five tiny functions that require cross-referencing.

**Exceptions:** State machines, pipeline orchestrators, and configuration setup may exceed 40 lines with a deviation record. Each case/step within the function must still be individually simple (<5 lines per branch).

### Guard Clauses (Mandatory)

Validate preconditions at function entry using guard clauses. Main logic begins at nesting depth 0-1. [EXPERT CONSENSUS]

```python
# REQUIRED pattern
def process(data):
    if data is None:
        return Err(NullInputError(...))
    if not data.is_valid():
        return Err(ValidationError(...))
    if not data.has_permission():
        return Err(PermissionError(...))

    # main logic at depth 0-1
    return do_work(data)
```

Never nest a try/except inside an if inside a try/except. Extract to a named function.

### Nesting Depth

**Hard limit: 3 levels (2 preferred).** Guard clauses are the primary tool for achieving this.

### Cyclomatic Complexity

**Hard limit: 10 per function.** [RESEARCH-BACKED]

Functions exceeding complexity 15 contain significantly more defects. The limit of 10 catches the transition from moderate to high risk. Functions at 11-15 require a deviation record.

### Parameters

**Hard limit: 4 per function.** Use a frozen dataclass for more.

---

## Railway-Oriented Error Handling

The factory already mandates Result types. The missing piece is composition — how to chain multiple fallible operations without nesting. [EXPERT CONSENSUS]

### Flat Pipeline Composition

```python
# REQUIRED: flat pipeline using and_then (if Result supports it)
def pipeline(raw):
    return (
        parse(raw)
        .and_then(validate)
        .and_then(transform)
        .and_then(save)
    )
```

### Imperative Equivalent (Guard-Clause Style)

```python
# REQUIRED: if Result doesn't support chaining
def pipeline(raw):
    parsed = parse(raw)
    if isinstance(parsed, Err):
        return parsed

    validated = validate(parsed.value)
    if isinstance(validated, Err):
        return validated

    transformed = transform(validated.value)
    if isinstance(transformed, Err):
        return transformed

    return save(transformed.value)
```

This keeps nesting at depth 1 regardless of pipeline length.

### What Is Banned

- **A function that returns Result must NOT contain try-except for business logic.** The Result return IS the error handling. try-except is only for I/O boundaries (file reads, stdin, network calls, database).
- **try-except blocks must not wrap more than 5 lines of code.** If your try block is longer, extract the risky operation into a helper function that returns Result.
- **`except Exception` is banned.** This is equivalent to bare except for convention purposes. Catch the specific exception types you expect: `json.JSONDecodeError`, `OSError`, `ValueError`.
- **Silent swallowing is banned.** `except SomeError: pass` is never acceptable. If you catch an exception, you must either: (a) return an Err result, (b) log to stderr, or (c) re-raise as a typed error.

---

## Error Types

String error messages are insufficient. Every error type is a frozen dataclass with typed fields. [EXPERT CONSENSUS]

```python
@dataclass(frozen=True)
class ParseError:
    field: str
    expected: str
    got: str
    line: int | None = None

    def __str__(self) -> str:
        loc = f" at line {self.line}" if self.line else ""
        return f"Expected {self.expected} for '{self.field}', got '{self.got}'{loc}"
```

CLI tools emit structured JSON on stderr: `{"error": "message", "field": "which"}`. Never raw stack traces.

---

## CLI Entry Point Structure

main() must follow this four-step pattern. Each step is a separate function. [EXPERT CONSENSUS, validated by build failure analysis]

```python
def main() -> None:
    args = parse_args()           # 1. Parse CLI arguments
    input_data = read_input(args) # 2. Read input (file/stdin) — may sys.exit(1)
    result = process(input_data)  # 3. Pure business logic — returns Result
    emit_output(result)           # 4. Write output (stdout/stderr) — may sys.exit

if __name__ == "__main__":
    main()
```

**main() itself must be under 15 lines.** It is a pipeline coordinator, not an implementation. Each step function is independently testable.

---

## Data & Types

All data objects: `@dataclass(frozen=True)`. Immutable by default.

Parse, don't validate — constructors return `Result[ValidType, ParseError]`. After parsing, the type guarantees validity.

Use `Literal` types for constrained string fields. Use `Union`/`Enum` for sum types. Domain model IS the type definitions.

Validate dataclass invariants in `__post_init__`.

---

## Assertions (Mandatory, Enforced)

**Minimum 2 assertions per non-trivial function.** [RESEARCH-BACKED]

Microsoft Research: statistically significant negative correlation between assertion density and fault density. NASA JPL mandates minimum 2 assertions per function. This is the single strongest empirically-validated quality predictor.

```python
def dedup_envelopes(envelopes: list[Envelope], window: int) -> list[Envelope]:
    # PRECONDITION
    assert isinstance(envelopes, list), "envelopes must be a list"
    assert window > 0, f"window must be positive, got {window}"

    seen: dict[str, float] = {}
    result: list[Envelope] = []
    for env in envelopes:
        key = compute_dedup_key(env)
        last = seen.get(key)
        if last is None or (env.timestamp - last) > window:
            seen[key] = env.timestamp
            result.append(env)

    # POSTCONDITION
    assert len(result) <= len(envelopes), "dedup cannot produce more items than input"
    return result
```

Assertions verify invariants, remain active in production. The assertion message IS the documentation: `assert condition, "brief invariant description"`.

---

## Anti-Repetition (Mandatory)

**No duplicated logic blocks.** If the same pattern appears twice, extract to a named function. [RESEARCH-BACKED]

LLM-generated code has 3-10x the code repetition rate of human-written code (arxiv 2504.12608). This is a measured, specific quality defect. Actively counteract it.

---

## Naming

Functions describe actions: `parse_envelope`, `compute_dedup_key`.
Types describe data: `[REDACTED]Envelope`, `ParseError`.
Errors describe what went wrong: `BudgetExceededError`.

Imports at top level, explicit, no wildcards. No imports inside function bodies.

---

## Testing (TDD-First, Always)

Write tests BEFORE implementation. Every `Result` type has success AND failure test cases.

### Hard Gates

- **Every test function body must contain at least one `assert` statement or a `pytest.raises` context.** A test with only `pass`, `return`, or bare function calls is a build failure.
- **No `assert True` as the sole assertion** — it proves nothing.
- **Smoke tests that use subprocess MUST assert on returncode AND at least one output property.**

### Test Isolation

- No module-level mutable state in implementation files that tests import. If shared state is needed for dedup/caching, inject it via a parameter with a default, not a module global.
- Each test function must be independently runnable. Running tests in any order must produce the same results.
- Use `tmp_path` or `tmp_path_factory` fixtures for file-based state.
- Never rely on side effects from a previous test function.

### Property-Based Testing

Parsing and transformation functions require Hypothesis tests. [RESEARCH-BACKED: PBT finds 50x more mutations per test than unit tests — ACM OOPSLA 2025]

Key properties: roundtrip (deserialize(serialize(x)) == x), subset (output is subset of input), idempotency (f(x) == f(f(x))), ordering preservation.

### Mock Discipline

Mock at the seam only — the boundary where your code calls something it does not own (filesystem, network, DB). Never mock internal functions. Call them directly.

### Import Convention for Test Files

```python
SCRIPT_DIR = Path(__file__).resolve().parents[N] / "00-System" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
```

Where N is the number of directory levels between the test file and the repo root. Never use relative paths like `sys.path.append('00-System/scripts')`.

---

## Security

Validate all external input at system boundaries. No string interpolation in SQL or shell commands. Read-only access unless write is explicitly required by the spec. No user-supplied paths without validation.

40% of LLM-generated code contains security vulnerabilities (multiple studies, 2024). [RESEARCH-BACKED] Conventions must actively counteract, not just forbid.

---

## Observability

Use structured logging with JSON output. Every log entry includes: event name (snake_case), correlation ID, and typed fields. Log at function entry and exit. Never log sensitive data.

```python
import structlog
logger = structlog.get_logger()

logger.info("processing_envelope", envelope_id=env.id, size_bytes=len(env.payload))
```

---

## Pipeline & Orchestration Patterns

Every pipeline stage is a pure function: `(Input) -> Result[Output, StageError]`. Stages do not modify shared state. The orchestrator composes stages.

All pipeline operations must be idempotent. Running the same operation twice produces the same result. Use dedup keys, upserts, and atomic file writes (write to .tmp, rename to final).

Configuration is a frozen dataclass with validated defaults. Validate at startup, not at point of use.

---

## Rule Priority

Rules marked **(hard)** are build-fail gates. The factory runner rejects code that violates them.
Rules marked **(advisory)** are quality targets. Deviation records are required for violations.

**Hard rules:** function length (40 lines), nesting depth (3), parameter count (4), cyclomatic complexity (10), main() length (15 lines), test body assertions, no bare except, no except Exception, no pass in error handlers, no module-level mutable state in imported modules, type annotations on all function signatures.

**Advisory rules:** assertion density (2 per function), Hypothesis tests for parsing functions, structured logging, docstring coverage.

---

## Deviation Records

Every standard violation requires a deviation record:

- **Rule violated:** which standard, which threshold
- **Justification:** why this case is an exception
- **Approved by:** operator or architect
- **Mitigations:** what compensating controls are in place
- **Scope:** which specific code is covered
- **Expiration:** when the deviation should be revisited

---

## Traceability

Bidirectional: code references the acceptance criteria it implements (`# AC-01`). Tests reference the criteria they verify. No orphan code, no orphan tests.

Target files are listed in the ticket. Do not create files outside that list.

---

## LLM-Specific Quality Countermeasures

LLM-generated code has measured, specific defects that conventions must actively counteract. [RESEARCH-BACKED]

| Defect | Rate | Countermeasure |
|--------|------|----------------|
| Security vulnerabilities | 40% of output | Explicit security rules in conventions + static analysis |
| Code repetition | 3-10x human rate | Anti-repetition rule: extract on second occurrence |
| Memory consumption | 2x baseline | Avoid unnecessary data copying; prefer generators for large datasets |
| Static analysis issues | 1.77 per passing task | Zero warnings from pyright strict + ruff |
| Empty test stubs | Observed in factory builds | Test body assertion gate |
| Incorrect Result implementations | Every build | Canonical Result type provided |
| Giant main() functions | Every build | 15-line main() decomposition pattern |

---

## Static Analysis

**Zero warnings from pyright strict + ruff. Run on every build.** No suppressions without deviation record.

Recommended ruff rules: E (pycodestyle errors), F (pyflakes), I (isort), D (pydocstyle), S (bandit security), UP (pyupgrade), B (flake8-bugbear).

---

## Modern Python Patterns (3.11+)

| Pattern | Use |
|---------|-----|
| `X \| None` union syntax | Replace Optional[X] |
| `match/case` structural pattern matching | Result dispatch, data shape detection |
| `@dataclass(frozen=True)` | All data objects |
| Protocol classes | Structural subtyping for testability |
| `type` statement (3.12+) | Type aliases |
| `ExceptionGroup` (3.11+) | Batch error reporting |

Type annotations: annotate signatures, not locals. Let the type checker infer local variable types.

Always include a `case _:` default in match statements.

---

## Sources

### Research Papers
- Basili & Perricone (1984): Function length and error density
- Microsoft Research (2006): Assertion density and fault density correlation
- Chen et al. (2019, arxiv 1912.01142): Code complexity and bugs
- Code quality of LLM output (2025, arxiv 2511.10271): Security, memory, static analysis metrics
- Code repetition in LLM output (2025, arxiv 2504.12608): 3-10x human baseline
- Property-based testing effectiveness (ACM OOPSLA 2025): 50x mutation detection
- Prompt engineering for code quality (2026, arxiv 2601.13118): Adoption vs perceived value gaps

### Books
- McConnell, "Code Complete" (2nd ed., 2004)
- Ousterhout, "A Philosophy of Software Design" (2nd ed., 2021)
- Meyer, "Object-Oriented Software Construction" (2nd ed., 1997)

### Standards
- NASA JPL Power of 10 Rules (Holzmann, 2006)
- Google Python Style Guide
- PEP 760 (bare except ban, proposed Python 3.14+)

### Factory Build Analysis
- 13 builds across 4 tickets analyzed (2026-05-08)
- Specific violations cataloged in `[REDACTED PERSONA]/research/factory-build-failure-analysis.md`
