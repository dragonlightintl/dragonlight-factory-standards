# Dragonlight Documentation Standard

**Owner:** [REDACTED PERSONA]
**Status:** Active — applies to all Dragonlight code and generated documentation
**Origin:** Session 85e, synthesized from deep research on documentation practices
**Companion:** `dragonlight-coding-standards-v2.md`

---

## Architecture: Two Layers

### Layer 1: Coding Agent (Inline Documentation)

The coding agent writes inline documentation as part of code generation:
- Google-style docstrings on all public functions and classes
- Type hints on all function signatures (types live in annotations, not docstrings)
- Module-level docstrings describing purpose, key abstractions, and architectural context
- Inline comments for invariants, non-obvious constraints, and business rules ("why" not "what")
- Doctest examples on public API functions

### Layer 2: Documentation Agent (Generated Documentation)

The documentation agent generates human-readable documentation packages:
- API reference auto-generated from code (MkDocs + mkdocstrings)
- Usage guides generated from live specs + code
- Architecture documentation from ADRs and design documents
- Changelog from conventional commits

---

## Docstring Format: Google Style

Google style is recommended for all Dragonlight code. [EXPERT CONSENSUS]

Rationale: most readable for short-to-medium docstrings, most reliably produced by LLMs, first-class support in every major tool (Sphinx via Napoleon, MkDocs via mkdocstrings, pdoc).

### Rules

1. Every public function and class gets a docstring. No exceptions.
2. First line: what the function does (imperative mood), fits in 79 characters.
3. Args section: one line per parameter with semantic meaning. Types are in annotations, not docstrings.
4. Returns section: describe both success and failure cases for Result types.
5. Raises section: list exceptions that callers should handle. "Raises: Nothing" explicitly when using Result types.
6. Private helpers under 10 lines with obvious purpose from name+signature: docstring optional.
7. Module docstring: 2-3 sentences. What the module does and where it fits in the system.

### Standard Function Docstring

```python
def parse_envelope(raw: bytes, schema_version: int) -> Result[[REDACTED]Envelope, ParseError]:
    """Parse raw bytes into a validated [REDACTED] envelope.

    Validates structure against the specified schema version and returns
    a typed envelope on success. Does not perform deduplication.

    Args:
        raw: Wire-format bytes from the ingest pipeline.
        schema_version: Schema version to validate against (1 or 2).

    Returns:
        Ok([REDACTED]Envelope): Parsed and validated envelope.
        Err(ParseError): On failure, with specific field and expected/got values.

    Raises:
        Nothing -- all failures returned as Result.Err.
    """
```

### Documenting Result Types

Document Ok and Err cases separately with explicit variant labels:

```python
def load_config(path: Path) -> Result[Config, ConfigError]:
    """Load and validate configuration from a TOML file.

    Args:
        path: Absolute path to the TOML configuration file.

    Returns:
        Ok(Config): Fully validated configuration with defaults populated.
        Err(ConfigError): On failure, with variants:
            - FILE_NOT_FOUND: Path does not exist.
            - PARSE_ERROR: File is not valid TOML.
            - VALIDATION_ERROR: TOML valid but fails schema validation.
    """
```

### Documenting Frozen Dataclasses

Use `Attributes:` section. Document semantic meaning, constraints, and valid ranges — not types.

```python
@dataclass(frozen=True)
class TicketMetadata:
    """Immutable metadata attached to a factory ticket.

    Attributes:
        ticket_id: Unique identifier. Format: `TKT-{uuid4_short}`.
        source_spec: Path to the live spec, relative to specs/.
        priority: Scheduling priority. Range: 1 (lowest) to 10 (highest).
        created_at: UTC timestamp. Set by the registry, never manually.
    """
    ticket_id: str
    source_spec: str
    priority: int
    created_at: datetime
```

### Documenting CLI Tools

Document exit codes (not visible from type hints):

```python
def main() -> None:
    """Execute a factory run against a live specification.

    Exit codes:
        0: All tickets completed successfully.
        1: One or more tickets failed (partial success).
        2: Spec validation failed (nothing was built).
    """
```

### Documenting Pipelines (Module-Level)

```python
"""Factory build pipeline.

Processes tickets through a sequence of stages. Designed for partial
failure: individual ticket failures do not halt the pipeline.

Stages: Decompose -> Prioritize -> Generate -> Verify -> Assemble
Data flow: Spec -> [Ticket] -> [CodeArtifact] -> [VerifiedArtifact] -> Output

Failed tickets are logged and skipped; remaining tickets continue.
"""
```

---

## Inline Comments

Comment the WHY, never the WHAT. [EXPERT CONSENSUS]

**Valuable:**
```python
# Dedup window is 5 minutes because USB transfers can stall mid-batch
DEDUP_WINDOW_SECONDS = 300

# INVARIANT: parsed_items sorted by timestamp ascending
assert all(a.ts <= b.ts for a, b in zip(items, items[1:]))
```

**Harmful (never write these):**
```python
# Parse the envelope
parsed = parse_envelope(raw)

# Check if valid
if parsed.is_ok():
```

Every magic number gets a named constant with a comment explaining why that value.

---

## Documentation Framework: Diataxis

All generated documentation follows the Diataxis four-quadrant model:

| Type | Purpose | User Need | Factory Source |
|------|---------|-----------|----------------|
| **Tutorials** | Learning | "Teach me" | Doc agent or human |
| **How-to Guides** | Goal achievement | "Help me do X" | Doc agent from specs + code |
| **Reference** | Information | "Tell me about X" | Auto-generated from docstrings |
| **Explanation** | Understanding | "Help me understand why" | ADRs, live specs, design docs |

These four types must be kept separate. Mixing tutorial content into reference degrades both.

---

## Documentation Generation Toolchain

### Recommended Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Site generator | MkDocs + Material theme | Markdown-native, minimal config |
| API autodoc | mkdocstrings (Griffe backend) | Extract docs from code |
| CLI autodoc | mkdocs-click | Extract docs from Click commands |
| Docstring lint | Ruff (D100-D418 rules) | Format and coverage |
| Docstring-code agreement | pydoclint | Args/Returns/Raises match signature |
| Type checking | pyright strict / mypy | Type annotation correctness |
| Example testing | pytest --doctest-modules | Doctest example correctness |
| Prose lint | Vale | Style and clarity in generated docs |
| Agent-friendly output | afdocs CLI | 23-check compliance |

### CI Pipeline

```
Coding agent writes code
  -> Ruff (docstring format + coverage)
  -> pydoclint (docstring-code agreement)
  -> pyright strict (type correctness)
  -> pytest --doctest-modules (example correctness)

Documentation agent generates docs
  -> MkDocs build (site generation)
  -> Vale (prose quality)
  -> Link checker (broken references)
  -> afdocs (agent-friendly compliance)
```

---

## Agentic Documentation Generation

### Processing Order: Topological (Mandatory)

Following DocAgent (ACL 2025) and RepoAgent (EMNLP 2024):

1. AST-parse all Python modules
2. Build import dependency graph
3. Topological sort: leaves (no dependencies) first, roots last
4. Generate documentation in order — each module's docs can reference already-documented dependencies
5. Verify: completeness, helpfulness, truthfulness

This ordering produces significantly better results than random or file-order processing. [RESEARCH-BACKED]

### Quality Evaluation

| Metric | What It Measures | Method |
|--------|-----------------|--------|
| Completeness | All standard sections present | Deterministic (pydoclint) |
| Signature Agreement | Docstring params match signature | Deterministic (pydoclint) |
| Example Correctness | Doctest examples pass | Deterministic (pytest) |
| Helpfulness | Useful for a developer | LLM-as-judge or human review |
| Truthfulness | Cross-references accurate | Import check + LLM verification |
| Freshness | Reflects current code | Git diff analysis |

---

## Agent-Friendly Output

Follow the Agent-Friendly Documentation Spec (agentdocsspec.com):

- Create an `llms.txt` file under 50K characters
- Serve Markdown versions of pages via `.md` URLs
- Keep pages under 50K characters
- Break up large pages

Generated documentation should be consumable by coding agents (Claude Code, Cursor, GitHub Copilot) as well as humans.

---

## What NOT to Document

- Parameter types (type hints handle this)
- Return types (annotations handle this)
- Default values (visible in signature)
- Implementation details in docstrings (use inline comments)
- What the code does (the code says that)
- Commented-out code (use version control)

---

## Research Foundation

- Documentation quality correlates with fewer defects (2.2M-line study)
- Organizations with quality docs: 4-5x higher engineering productivity
- Developers are 50% more productive with up-to-date documentation
- DocAgent (Facebook, ACL 2025): topological multi-agent doc generation
- RepoAgent (EMNLP 2024): repository-level doc generation with git-based updates
- Stripe, Django, Rust, Go: best-in-class exemplars analyzed

Full research: `[REDACTED PERSONA]/research/documentation-standards-deep-research.md`
