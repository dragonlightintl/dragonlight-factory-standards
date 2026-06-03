# Live Spec Format Definition

**Version:** 0.2.0
**Status:** Active
**Governs:** `live_specs` table (migration 002)
**Changelog:** [v0.2.0 changes](#changelog)

---

## Purpose

The Live Spec is the handoff artifact from Phase 0 (operator engagement) to Phase 1 (formal specification). It captures the complete intent of a build request in a format that is:

- Readable by the operator ("does this tell the same story I told you?")
- Parseable by the Formalization Agent (behavioral contract extraction)
- Parseable by the UX Agent (design contract extraction)
- Decomposable by the Decomposition Agent (task map with acceptance criteria)

A Live Spec is produced through narrative interview, confirmed by the operator, then enters the agentic pipeline. No code is written until the Live Spec is confirmed.

As of v0.2.0, the Live Spec also defines the **module boundary** (public API with full signatures), **graft points** (how the module wires into the host codebase), and **call graph** (cross-references). These additions support the 5-stage manufacturing pipeline (test → code → audit → graft → accept) where each stage consumes specific Live Spec sections as its instruction set.

---

## Status Flow

```
draft → interview → review → confirmed → formalizing → formalized → decomposed
```

| Status | Meaning | Transition Rule |
|--------|---------|----------------|
| `draft` | Initial creation, may be empty or partial | Created when operator initiates a build request |
| `interview` | Narrative interview in progress | Requirements Agent begins interview process |
| `review` | Interview complete, awaiting operator confirmation | All interview checklists satisfied, completeness_score computed |
| `confirmed` | Operator has reviewed and confirmed the spec | Operator gate — human approval required |
| `formalizing` | Behavioral contract being translated to Lean 4 | Formalization Agent picks up confirmed spec |
| `formalized` | Lean 4 spec compiles, lean_spec_ref populated | Type-checker gate — compiles or does not proceed |
| `decomposed` | Tickets generated from spec | Decomposition Agent creates tickets referencing this spec |

Backward transitions are allowed only for: `review` -> `interview` (operator requests changes during review) and `formalizing` -> `confirmed` (formalization fails, needs spec revision).

---

## Sections

### 1. Behavioral Contract (`behavioral_contract JSONB`)

The "what to build" with no ambiguity. This section flows to Lean 4 formalization.

```json
{
  "inputs": [
    {
      "name": "user_query",
      "type": "string",
      "constraints": "non-empty, max 4096 chars",
      "source": "operator input"
    }
  ],
  "outputs": [
    {
      "name": "search_results",
      "type": "array<SearchResult>",
      "shape": {
        "title": "string",
        "score": "float 0.0-1.0",
        "snippet": "string"
      },
      "guarantees": "sorted by score descending, max 50 results"
    }
  ],
  "operations": [
    {
      "name": "execute_search",
      "description": "Perform full-text search across indexed documents",
      "preconditions": [
        "user_query is non-empty",
        "index has been built at least once"
      ],
      "postconditions": [
        "results contain only documents matching query terms",
        "results are sorted by relevance score descending",
        "each result has a valid snippet with highlighted terms"
      ],
      "side_effects": [
        "search query logged to analytics"
      ]
    }
  ],
  "edge_cases": [
    {
      "scenario": "query matches zero documents",
      "expected_behavior": "return empty array, not error",
      "narrative": "the operator searches for something that does not exist yet"
    },
    {
      "scenario": "index is empty (first run)",
      "expected_behavior": "return informative empty state, prompt to run indexer",
      "narrative": "the operator has just set up the system"
    }
  ],
  "error_states": [
    {
      "trigger": "database connection lost during search",
      "behavior": "return cached results if available, otherwise graceful error with retry suggestion",
      "severity": "degraded",
      "recovery": "automatic reconnection with exponential backoff"
    }
  ],
  "invariants": [
    "search results never include documents the operator does not have access to",
    "search index is eventually consistent with source data (max 60s lag)",
    "no search query mutates stored data"
  ]
}
```

#### Signatures (v0.2.0)

Concrete Python function signatures with full typing. This sub-section bridges the abstract behavioral contract to the implementation — the test agent writes tests against these signatures, the coding agent implements them.

```json
{
  "signatures": [
    {
      "name": "execute_search",
      "signature": "def execute_search(query: str, *, limit: int = 50, offset: int = 0) -> list[SearchResult]",
      "returns": "list[SearchResult] — sorted by score descending, capped at `limit`",
      "raises": [
        {"exception": "IndexNotReady", "when": "index has never been built"},
        {"exception": "QueryTooLong", "when": "len(query) > 4096"}
      ],
      "parameters": [
        {"name": "query", "type": "str", "semantics": "non-empty search phrase, supports partial matching"},
        {"name": "limit", "type": "int", "semantics": "max results to return, must be 1-50", "default": "50"},
        {"name": "offset", "type": "int", "semantics": "pagination offset into full result set", "default": "0"}
      ]
    }
  ],
  "types": [
    {
      "name": "SearchResult",
      "kind": "dataclass(frozen=True)",
      "fields": [
        {"name": "title", "type": "str", "semantics": "document title"},
        {"name": "score", "type": "float", "semantics": "relevance 0.0-1.0, higher is better"},
        {"name": "snippet", "type": "str", "semantics": "context fragment with highlighted matches"}
      ]
    }
  ],
  "error_types": [
    {
      "name": "IndexNotReady",
      "base": "Exception",
      "semantics": "raised when the search index has never been built"
    },
    {
      "name": "QueryTooLong",
      "base": "ValueError",
      "semantics": "raised when input exceeds the 4096-char limit"
    }
  ]
}
```

Each signature entry provides everything needed to write a complete test file without consulting any other source:
- **`signature`**: copy-paste-ready function definition
- **`returns`**: what the function returns and any ordering/shape guarantees
- **`raises`**: exception types with trigger conditions
- **`parameters`**: every parameter with type, semantics, and default value

#### Mapping to Lean 4

| Live Spec Element | Lean 4 Construct |
|-------------------|-----------------|
| Operations | `def` / `theorem` definitions |
| Preconditions | `requires` clauses / hypotheses |
| Postconditions | `ensures` clauses / goal statements |
| Invariants | `structure` field constraints / `theorem` statements |
| Edge cases | Additional `theorem` cases |
| Error states | `inductive` error type + handler proofs |

---

### 2. System Constitution References (`constitution_refs JSONB`)

References to existing architectural constraints, coding standards, and security policies that bound this work. These are pointers, not inline content — the constitution definitions live in the project repository.

```json
[
  {
    "type": "architecture",
    "ref": "constitution/architecture.md#data-layer",
    "constraint": "all state in PostgreSQL, no file-based state"
  },
  {
    "type": "coding_standard",
    "ref": "constitution/standards.md#error-handling",
    "constraint": "all errors return structured ErrorResult, never raw exceptions"
  },
  {
    "type": "security",
    "ref": "constitution/security.md#auth",
    "constraint": "all endpoints require authentication, no anonymous access"
  },
  {
    "type": "performance",
    "ref": "constitution/performance.md#latency",
    "constraint": "p95 response time under 200ms for read operations"
  }
]
```

Each reference has:
- `type` — category: `architecture`, `coding_standard`, `security`, `performance`, `accessibility`, `compatibility`
- `ref` — path to the constraint definition (file + optional anchor)
- `constraint` — human-readable summary of the constraint as it applies to this spec

---

### 3. Design Contract (`design_contract JSONB`)

Visual language, surfaces, prototype references, interaction model. This section flows to the prototype/design system, NOT to Lean 4.

**Required when `operator_facing = true`.** Not needed for `api`, `library`, or `script` surface types (those are agentic-consumed, not operator-facing).

Applies to ALL operator-facing surfaces:
- **CLI:** output formatting, color coding, structure of displayed information
- **TUI:** screen layout, key hint styling, navigation flow
- **Web/Mobile/Desktop:** full visual design system

```json
{
  "visual_language": {
    "palette": ["#1a1a2e", "#16213e", "#0f3460", "#e94560"],
    "typography": {
      "font_family": "JetBrains Mono",
      "scale": "1.25 major third"
    },
    "spacing_system": "8px base grid",
    "design_tokens_ref": "design/tokens.json"
  },
  "surfaces": [
    {
      "name": "search_results_view",
      "type": "tui_screen",
      "description": "displays search results with highlighted matches",
      "prototype_ref": "prototypes/search-results.html",
      "layout": {
        "structure": "header + scrollable list + status bar",
        "key_hints": "bottom bar with navigation and action keys"
      }
    }
  ],
  "interaction_model": {
    "navigation": "keyboard-driven, vim-style hjkl + arrows",
    "selection": "enter to select, space to multi-select",
    "feedback": "inline status messages, no modals",
    "empty_states": "contextual help text, not blank screens",
    "loading_states": "spinner with elapsed time"
  },
  "accessibility": {
    "contrast_ratio": "WCAG AA minimum (4.5:1)",
    "screen_reader": "all interactive elements labeled",
    "keyboard_only": "full functionality without mouse"
  }
}
```

#### Surface-Specific Design Contract Guidance

| Surface Type | Focus Areas |
|-------------|-------------|
| `cli` | Output formatting, color/no-color modes, column alignment, exit codes, piping compatibility |
| `tui` | Screen layout, keybindings, navigation graph, empty/error/loading states per screen |
| `web` | Full visual design system, responsive breakpoints, interaction patterns, page transitions |
| `desktop` | Window chrome, menu structure, keyboard shortcuts, system tray behavior |
| `mobile` | Touch targets, gesture model, offline behavior, notification patterns |

---

### 4. User Stories / Narrative Frame (`user_stories JSONB`)

Stories framed as narrative arcs. The story structure provides the operator a verification lens: "does this spec tell the same story I told you?"

```json
[
  {
    "id": "US-001",
    "role": "operator",
    "action": "search my indexed documents by keyword",
    "outcome": "find the specific document I need without remembering its exact name",
    "narrative_arc": {
      "setup": "the operator has hundreds of documents indexed across multiple projects",
      "rising_action": "they remember a concept but not which document contains it",
      "climax": "they type a partial phrase and the system surfaces the right document",
      "resolution": "they open the document and find the information they need"
    },
    "five_whys": [
      {
        "question": "Why do you need to search documents?",
        "answer": "because I have too many to browse manually"
      },
      {
        "question": "Why do you have too many to browse?",
        "answer": "because the system grows over time and I forget where things are"
      },
      {
        "question": "Why does forgetting locations matter?",
        "answer": "because I lose time looking for things instead of doing the work"
      },
      {
        "question": "Why does lost time matter here specifically?",
        "answer": "because my executive function makes context-switching expensive — if I lose flow searching, the work session may be over"
      },
      {
        "question": "Why is that the root concern?",
        "answer": "because the system exists to protect flow state, not just store data"
      }
    ],
    "root_motivation": "the system must protect flow state by making retrieval instant",
    "edge_cases_as_complications": [
      {
        "complication": "the operator misspells the search term",
        "resolution": "fuzzy matching surfaces plausible results with a 'did you mean' suggestion"
      },
      {
        "complication": "the search returns too many results to scan",
        "resolution": "results are ranked by relevance; top 5 are shown with option to expand"
      }
    ],
    "error_states_as_failure_endings": [
      {
        "failure": "the index is corrupted and search returns garbage",
        "ending": "system detects inconsistency, notifies operator, offers to rebuild index",
        "recovery_path": "automatic index rebuild from source files"
      }
    ],
    "acceptance_criteria_refs": ["BC-OP-001", "BC-INV-001"]
  }
]
```

#### Narrative Prompting Methodology

The interview process uses narrative prompting to surface completeness:

| Prompt Pattern | What It Surfaces |
|----------------|-----------------|
| "Walk me through what happens when..." | Operations, preconditions, postconditions |
| "And then what?" | Sequencing, state transitions, side effects |
| "What if that fails?" | Error states, recovery paths |
| "What does this look like with no data?" | Empty states, initialization requirements |
| "Why is that important?" (x5) | Root motivations, invariants, postconditions |
| "Does this tell the same story you told me?" | Verification — completeness check |

Five Whys traces are captured per user story. The root answer (the fifth "why") maps to postconditions and invariants — the properties that must hold for the story to make sense.

---

### 5. Actionable Task Map (`task_map JSONB`)

Ordered subtask decomposition with acceptance criteria referencing the behavioral contract.

```json
[
  {
    "id": "TM-001",
    "title": "implement full-text search index builder",
    "description": "create the indexing pipeline that processes source documents",
    "order": 1,
    "depends_on": [],
    "build_target_type": "standalone_module",
    "build_phase": "test",
    "acceptance_criteria": [
      {
        "criterion": "index builder processes all files in configured directories",
        "verification_method": "integration_test",
        "behavioral_contract_ref": "BC-OP-001.precondition.1"
      },
      {
        "criterion": "index is queryable within 60s of source file change",
        "verification_method": "integration_test",
        "behavioral_contract_ref": "BC-INV-002"
      }
    ],
    "estimated_complexity": "standard",
    "target_files": ["src/indexer.py", "src/index_schema.py"],
    "notes": "use existing pg_trgm extension for fuzzy matching"
  },
  {
    "id": "TM-002",
    "title": "implement search query executor",
    "description": "the core search operation that queries the index",
    "order": 2,
    "depends_on": ["TM-001"],
    "build_target_type": "standalone_module",
    "build_phase": "test",
    "acceptance_criteria": [
      {
        "criterion": "search returns results sorted by relevance score",
        "verification_method": "unit_test",
        "behavioral_contract_ref": "BC-OP-001.postcondition.2"
      },
      {
        "criterion": "empty query returns informative empty state",
        "verification_method": "unit_test",
        "behavioral_contract_ref": "BC-EDGE-002"
      }
    ],
    "estimated_complexity": "standard",
    "target_files": ["src/search.py"],
    "notes": null
  },
  {
    "id": "TM-003",
    "title": "wire search module into application entry point",
    "description": "graft the search module's exports into the CLI dispatcher",
    "order": 3,
    "depends_on": ["TM-002"],
    "build_target_type": "graft",
    "build_phase": "graft",
    "acceptance_criteria": [
      {
        "criterion": "CLI `search` command dispatches to execute_search",
        "verification_method": "integration_test",
        "behavioral_contract_ref": "BC-OP-001"
      },
      {
        "criterion": "no ImportError when loading the modified entry point",
        "verification_method": "unit_test",
        "behavioral_contract_ref": null
      }
    ],
    "estimated_complexity": "trivial",
    "target_files": ["src/cli.py"],
    "graft_points_ref": "GP-001",
    "notes": "graft-only task — no standalone module produced"
  }
]
```

#### build_target_type (v0.2.0)

| Value | Meaning | Manufacturing Pipeline Entry |
|-------|---------|------------------------------|
| `standalone_module` | New file produced by coding agent (whole-file write) | Stage 1 (test agent) |
| `graft` | No new file — only host-code patches via edit_file | Stage 4 (graft agent) |
| `mixed` | Produces a new file AND requires host-code patches | Stage 1 (full pipeline) |

#### build_phase (v0.2.0)

| Value | Meaning | Which Agent Starts |
|-------|---------|-------------------|
| `test` | Enters at Stage 1 — test agent writes contract tests first | Test Agent |
| `code` | Enters at Stage 2 — tests already exist (e.g. from a prior task) | Coding Agent |
| `graft` | Enters at Stage 4 — module exists, only wiring needed | Graft Agent |

Each task map entry references behavioral contract elements via `behavioral_contract_ref` strings. After formalization, these references are updated to point to the corresponding Lean 4 components, and each task map entry becomes a ticket.

---

### 6. Discovery Provenance (`discovery_provenance JSONB`) (v0.2.0)

Captures the context-gathering phase — how we understood the problem space before formalizing requirements. This is the "divergent" phase: research, exploration, 5 whys, "what happens when" scenarios, ideal state identification.

```json
{
  "method": "narrative_interview",
  "sessions": [
    {
      "session_id": "s85",
      "date": "2026-05-06",
      "duration_minutes": 45,
      "summary": "initial context gathering for search functionality",
      "topics_covered": [
        "current pain points with document retrieval",
        "how the operator currently finds things",
        "what flow-state interruption looks like"
      ],
      "prompts_used": [
        "Walk me through what happens when you need to find a specific document",
        "And then what?",
        "What does this look like with no data?",
        "Why is that important? (x5)"
      ],
      "open_questions_remaining": [
        "fuzzy matching threshold — operator deferred to implementation"
      ]
    }
  ],
  "research_notes": [
    {
      "topic": "full-text search approaches in Python",
      "findings": "pg_trgm for fuzzy, GIN index for exact, whoosh for file-based",
      "decision": "pg_trgm chosen — already have PostgreSQL, no new dependency"
    }
  ],
  "ideal_state": "operator types a partial phrase, the right document surfaces instantly, flow state never breaks",
  "what_happens_when_scenarios": [
    {
      "scenario": "operator searches with a misspelling",
      "current_behavior": "no results, operator confused",
      "desired_behavior": "fuzzy match surfaces plausible results"
    },
    {
      "scenario": "index has never been built",
      "current_behavior": "N/A — system doesn't exist yet",
      "desired_behavior": "informative empty state, prompt to run indexer"
    }
  ],
  "five_whys_traces": [
    {
      "root_question": "Why do you need to search documents?",
      "chain": [
        "because I have too many to browse manually",
        "because the system grows over time and I forget where things are",
        "because I lose time looking for things instead of doing the work",
        "because my executive function makes context-switching expensive",
        "because the system exists to protect flow state, not just store data"
      ],
      "root_motivation": "the system must protect flow state by making retrieval instant"
    }
  ]
}
```

---

### 7. Requirements Provenance (`requirements_provenance JSONB`) (v0.2.0)

Captures the formalization phase — how discovery findings were translated into acceptance criteria, user stories, behavioral contracts, and module boundaries. This is the "convergent" phase: specificity, precision, disambiguation.

```json
{
  "formalization_sessions": [
    {
      "session_id": "s86",
      "date": "2026-05-07",
      "duration_minutes": 30,
      "summary": "formalized search requirements from discovery notes",
      "outputs_produced": [
        "behavioral_contract.operations[0]",
        "user_stories[0]",
        "module_boundary.exports[0..2]"
      ],
      "decisions_made": [
        {
          "question": "should empty query return all documents or error?",
          "decision": "return informative empty state, not error",
          "rationale": "operator may accidentally submit empty, system should be forgiving"
        }
      ]
    }
  ],
  "completeness_assessment": {
    "score": 0.85,
    "gaps": [
      {
        "area": "performance under load",
        "severity": "low",
        "note": "single-user system, load testing deferred"
      }
    ],
    "checklist_results": {
      "operations_complete": true,
      "edge_cases_explored": true,
      "error_states_mapped": true,
      "empty_states_defined": true,
      "invariants_stated": true,
      "five_whys_traced": true,
      "signatures_defined": true,
      "module_boundary_complete": true,
      "graft_points_identified": true
    }
  },
  "ambiguities_resolved": [
    {
      "item": "exact fuzzy matching algorithm",
      "operator_response": "whatever works, I trust the implementation",
      "resolution": "deferred to implementation — pg_trgm as default",
      "affects": ["behavioral_contract.operations[0]"]
    }
  ],
  "traceability": {
    "discovery_to_requirements": [
      {
        "discovery_item": "five_whys_traces[0].root_motivation",
        "maps_to": "behavioral_contract.invariants[0]",
        "justification": "flow-state protection is the invariant that guards the root need"
      }
    ]
  }
}
```

#### Why Two Provenance Sections?

The design pipeline has two distinct cognitive phases with different failure modes:

| Phase | Failure Mode | Mitigation |
|-------|-------------|-----------|
| Discovery | Premature convergence — formalizing before the problem is understood | Separate section forces breadth-first exploration |
| Requirements | Ambiguity leakage — vague language surviving into specs | Completeness checklist with `signatures_defined` and `module_boundary_complete` gates |

The Requirements Agent uses discovery provenance as input — it does not interview the operator again. If discovery is insufficient, the flow returns to the Discovery Agent, not forward to formalization.

---

### 8. Interview Provenance (`interview_provenance JSONB`) — DEPRECATED

**Retained for backward compatibility with v0.1.0 specs.** New specs should use `discovery_provenance` + `requirements_provenance` instead. Existing specs with `interview_provenance` remain valid — the manufacturing pipeline reads from either format.

```json
{
  "method": "narrative_interview",
  "sessions": [
    {
      "session_id": "s85",
      "date": "2026-05-06",
      "duration_minutes": 45,
      "summary": "initial requirements capture for search functionality",
      "topics_covered": [
        "core search workflow",
        "edge cases for empty index",
        "performance expectations"
      ],
      "open_questions_remaining": [
        "fuzzy matching threshold — operator deferred to implementation"
      ]
    }
  ],
  "completeness_assessment": {
    "score": 0.85,
    "gaps": [
      {
        "area": "performance under load",
        "severity": "low",
        "note": "single-user system, load testing deferred"
      }
    ],
    "checklist_results": {
      "operations_complete": true,
      "edge_cases_explored": true,
      "error_states_mapped": true,
      "empty_states_defined": true,
      "invariants_stated": true,
      "five_whys_traced": true
    }
  },
  "ambiguities": [
    {
      "item": "exact fuzzy matching algorithm",
      "operator_response": "whatever works, I trust the implementation",
      "resolution": "deferred to implementation — pg_trgm as default"
    }
  ]
}
```

---

### 9. Module Boundary (`module_boundary JSONB`) (v0.2.0)

Defines the standalone module's public API with full, concrete Python signatures. This is what the test agent writes tests against (Stage 1) and what the coding agent implements (Stage 2). The module boundary is the single source of truth for "what does this module export."

Every entry must be concrete enough that a test file can be written against it without consulting any other source.

```json
{
  "module_name": "token_budget.py",
  "exports": [
    {
      "name": "capture_usage",
      "signature": "def capture_usage(agent_result: Any) -> TokenUsage",
      "returns": "TokenUsage(input_tokens: int, output_tokens: int)",
      "description": "Extract token usage from pydantic-ai agent result",
      "preconditions": ["agent_result has .usage() method"],
      "postconditions": ["returns non-negative integers", "returns 0 when usage is None"]
    },
    {
      "name": "build_usage_limits",
      "signature": "def build_usage_limits(budget: int, *, reserve_pct: float = 0.1) -> UsageLimits",
      "returns": "UsageLimits(request_limit=None, total_token_limit=effective_budget)",
      "description": "Construct pydantic-ai UsageLimits from a token budget integer",
      "preconditions": ["budget > 0", "0.0 <= reserve_pct < 1.0"],
      "postconditions": ["total_token_limit = int(budget * (1 - reserve_pct))", "request_limit is None"]
    },
    {
      "name": "classify_limit_exceeded",
      "signature": "def classify_limit_exceeded(exc: UsageLimitExceeded) -> str",
      "returns": "str — one of 'token_limit' | 'request_limit' | 'unknown'",
      "description": "Classify a UsageLimitExceeded exception into an error category",
      "preconditions": ["exc is an instance of UsageLimitExceeded"],
      "postconditions": ["return value is always one of the three known categories"]
    }
  ],
  "types_defined": [
    {
      "name": "TokenUsage",
      "kind": "dataclass(frozen=True)",
      "fields": [
        {"name": "input_tokens", "type": "int", "default": "0"},
        {"name": "output_tokens", "type": "int", "default": "0"}
      ]
    }
  ],
  "dependencies": ["pydantic_ai.usage.Usage", "pydantic_ai.usage.UsageLimits", "pydantic_ai.exceptions.UsageLimitExceeded"],
  "host_imports_required": ["from token_budget import capture_usage, build_usage_limits, classify_limit_exceeded, TokenUsage"]
}
```

#### Module Boundary Field Reference

| Field | Required | Semantics |
|-------|----------|-----------|
| `module_name` | Yes | Filename of the standalone module to be produced |
| `exports` | Yes | All public functions/classes — this IS the public API |
| `exports[].name` | Yes | Function/class name as it appears in `__all__` |
| `exports[].signature` | Yes | Copy-paste-ready Python `def`/`class` signature |
| `exports[].returns` | Yes | Return type with shape/guarantee annotation |
| `exports[].description` | Yes | One-line purpose statement |
| `exports[].preconditions` | Yes | What must be true before calling |
| `exports[].postconditions` | Yes | What is guaranteed after calling |
| `types_defined` | Yes | Dataclasses, TypedDicts, enums defined in this module |
| `types_defined[].kind` | Yes | `dataclass(frozen=True)` / `TypedDict` / `Enum` / `NamedTuple` |
| `types_defined[].fields` | Yes | Every field with type, semantics, and default |
| `dependencies` | Yes | External imports required (fully qualified) |
| `host_imports_required` | Yes | The exact `from X import Y` line the host code needs |

#### Relationship to Behavioral Contract Signatures

The `module_boundary` and `behavioral_contract.signatures` serve complementary purposes:

| Concern | `behavioral_contract.signatures` | `module_boundary` |
|---------|----------------------------------|-------------------|
| Scope | Abstract operations (what the system DOES) | Concrete exports (what the FILE exports) |
| Audience | Formalization agent, Lean 4 translation | Test agent, coding agent |
| Granularity | One signature per logical operation | One entry per exported symbol |
| May diverge | Yes — one operation may require multiple exports | Yes — helper exports may not map 1:1 to operations |

In simple cases they overlap. In complex cases, `module_boundary` is the superset (it includes internal helpers, types, and utilities that the behavioral contract abstracts over).

---

### 10. Graft Points (`graft_points JSONB`) (v0.2.0)

Defines exactly where and how the standalone module gets wired into the host codebase. The graft agent (Stage 4) uses this as its instruction set. Each graft point is a surgical edit — import additions, call-site wiring, registration entries.

```json
[
  {
    "id": "GP-001",
    "host_file": "scripts/coding_agent.py",
    "location": "imports",
    "anchor_text": "from factory_types import AgentRunError, Err, HandoffArtifact, Ok, Result",
    "action": "add_after",
    "content": "from token_budget import capture_usage, build_usage_limits, classify_limit_exceeded",
    "description": "Import the new module's exports into the coding agent",
    "test_coverage_exists": true
  },
  {
    "id": "GP-002",
    "host_file": "scripts/coding_agent.py",
    "location": "call_site",
    "anchor_text": "d = _ok_dict(start_ms, trace_path, git_sha)",
    "action": "replace",
    "content": "usage = capture_usage(agent_result)\nd = _ok_dict(start_ms, trace_path, git_sha, tokens_input=usage.input_tokens, tokens_output=usage.output_tokens)",
    "description": "Wire token capture into the success path after agent.run_sync completes",
    "test_coverage_exists": true
  },
  {
    "id": "GP-003",
    "host_file": "scripts/factory.py",
    "location": "registration",
    "anchor_text": "AGENT_REGISTRY: dict[str, AgentConfig] = {",
    "action": "add_inside",
    "content": "\"token_budget\": AgentConfig(module=\"token_budget\", entry=\"capture_usage\"),",
    "description": "Register the module in the agent registry for discoverability",
    "test_coverage_exists": false
  }
]
```

#### Graft Point Field Reference

| Field | Required | Semantics |
|-------|----------|-----------|
| `id` | Yes | Stable identifier referenced by `task_map[].graft_points_ref` |
| `host_file` | Yes | Relative path to the file being patched |
| `location` | Yes | Category: `imports` / `call_site` / `registration` / `config` / `type_annotation` |
| `anchor_text` | Yes | Existing text near the edit point (used as `old_text` in edit operations) |
| `action` | Yes | `add_after` / `add_before` / `replace` / `add_inside` / `remove` |
| `content` | Yes | The exact text to insert or replace with |
| `description` | Yes | Human-readable explanation of what this graft achieves |
| `test_coverage_exists` | Yes | Whether the call site already has test coverage (acceptance agent uses this) |

#### Action Semantics

| Action | Behavior |
|--------|----------|
| `add_after` | Insert `content` on the line(s) after `anchor_text` |
| `add_before` | Insert `content` on the line(s) before `anchor_text` |
| `replace` | Replace `anchor_text` with `content` |
| `add_inside` | Insert `content` inside the block that starts at `anchor_text` (e.g., inside a dict literal) |
| `remove` | Delete `anchor_text` (no `content` field needed) |

#### Graft Size Constraint

If a single graft point requires more than 20 lines of `content`, the spec is malformed. This indicates the work should be decomposed further — either the module boundary is wrong (the module should export more) or the task should be split. The graft agent will reject oversized grafts and route back to the design engine.

---

### 11. Call Graph (`call_graph JSONB`) (v0.2.0)

Cross-references documenting what calls this module and what this module calls. Inspired by the explicit "what calls this / what this calls" documentation pattern in high-quality reference specs. The call graph enables impact analysis: when a module changes, the graft agent and acceptance agent know exactly what to verify.

```json
{
  "called_by": [
    {
      "function": "_run_agent_sync",
      "file": "scripts/coding_agent.py",
      "line": 142,
      "context": "after agent.run_sync completes, captures token usage from the result"
    },
    {
      "function": "run_coding_agent",
      "file": "scripts/factory.py",
      "line": 89,
      "context": "builds UsageLimits before agent invocation to enforce token budget"
    }
  ],
  "calls": [
    {
      "function": "Usage.input_tokens",
      "module": "pydantic_ai.usage",
      "context": "reading input token count from agent result usage data"
    },
    {
      "function": "Usage.output_tokens",
      "module": "pydantic_ai.usage",
      "context": "reading output token count from agent result usage data"
    },
    {
      "function": "UsageLimits.__init__",
      "module": "pydantic_ai.usage",
      "context": "constructing limits object to pass to agent.run_sync"
    }
  ],
  "dependency_direction": "leaf",
  "notes": "This module is a leaf — it depends on pydantic-ai but nothing in the host codebase depends on it until grafted."
}
```

#### Call Graph Field Reference

| Field | Required | Semantics |
|-------|----------|-----------|
| `called_by` | Yes | Every call site in the host codebase that will invoke this module's exports |
| `called_by[].function` | Yes | Function name at the call site |
| `called_by[].file` | Yes | Relative path to the file containing the call site |
| `called_by[].line` | No | Line number (approximate — may shift after grafting) |
| `called_by[].context` | Yes | Why this call site invokes the module (semantic purpose) |
| `calls` | Yes | Every external function/class this module invokes |
| `calls[].function` | Yes | Function or method name being called |
| `calls[].module` | Yes | Fully-qualified module path of the callee |
| `calls[].context` | Yes | Why this module calls the external function |
| `dependency_direction` | Yes | `leaf` (no host-code callers yet) / `internal` (called by host code) / `hub` (many callers) |
| `notes` | No | Free-text context about the module's position in the dependency graph |

#### Relationship to Graft Points

The `call_graph.called_by` entries correspond 1:1 with `graft_points` entries of location `call_site`. The call graph documents the semantic relationship; the graft points document the mechanical edit. Both are required because the acceptance agent needs the semantic context (call graph) to verify correctness, while the graft agent needs the mechanical instructions (graft points) to execute edits.

---

## Required vs. Optional Sections

| Section | Required | Condition |
|---------|----------|-----------|
| `behavioral_contract` | Always | Core of every spec |
| `behavioral_contract.signatures` | Always | Concrete function signatures (v0.2.0) |
| `constitution_refs` | Always | May be empty array if no project constitution exists yet |
| `design_contract` | Conditional | Required when `operator_facing = true` |
| `user_stories` | Always | At least one story per spec |
| `task_map` | Always | At least one task per spec |
| `discovery_provenance` | Always | Documents how the problem space was explored (v0.2.0) |
| `requirements_provenance` | Always | Documents how requirements were formalized (v0.2.0) |
| `interview_provenance` | Deprecated | Retained for backward compat; new specs use discovery + requirements |
| `module_boundary` | Always | Defines the standalone module's public API (v0.2.0) |
| `graft_points` | Conditional | Required when `build_target_type` includes grafts (v0.2.0) |
| `call_graph` | Always | Cross-references: what calls this, what this calls (v0.2.0) |

### operator_facing Rules

| surface_type | operator_facing default | design_contract required |
|-------------|----------------------|------------------------|
| `cli` | `true` | yes |
| `tui` | `true` | yes |
| `web` | `true` | yes |
| `desktop` | `true` | yes |
| `mobile` | `true` | yes |
| `api` | `false` | no |
| `library` | `false` | no |
| `script` | `false` | no |

The `operator_facing` boolean can be overridden. An API that operators interact with directly (e.g., a REST API with a Swagger UI) could be marked `operator_facing = true`.

---

## Relationship to Tickets

One Live Spec produces many tickets after decomposition.

```
live_specs (1) ──decomposition──→ (N) tickets
```

- Each ticket's `spec_version` field references the Live Spec's `spec_version_id`
- Each ticket's `behavioral_contract` field contains the subset relevant to that ticket (extracted from the spec's behavioral contract)
- Each ticket's `acceptance_criteria` are derived from the task map entry's acceptance criteria
- Each ticket's `lean_spec_ref` points to the Lean 4 component relevant to that ticket

The decomposition process:
1. Live Spec reaches `formalized` status (Lean 4 compiles)
2. Decomposition Agent reads the task map
3. Each task map entry becomes one ticket
4. Dependencies from the task map translate to ticket_links
5. Live Spec status transitions to `decomposed`

---

## Complexity and Formalization Depth

The `complexity` field determines how deep formalization goes (graduated formalization ladder):

| Complexity | Formalization Level | What Gets Formalized |
|-----------|-------------------|---------------------|
| `trivial` | Checklist validation only | Behavioral contract structure completeness |
| `standard` | Pre/postcondition extraction | LLM-generated pre/postconditions, consistency check |
| `complex` | State machine extraction | Reachability verification, state transition proofs |
| `formal` | Full Lean 4 proofs | Type-checker compilation, soundness proofs |

---

## Column Reference

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | `SERIAL` | auto | Primary key |
| `title` | `TEXT` | required | Human-readable spec title |
| `slug` | `TEXT` | null | URL-safe unique identifier |
| `description` | `TEXT` | null | Brief summary of what this spec covers |
| `status` | `TEXT` | `'draft'` | Current phase in the status flow |
| `surface_type` | `TEXT` | null | Target surface: cli, tui, web, desktop, mobile, api, library, script |
| `complexity` | `TEXT` | `'standard'` | Formalization depth: trivial, standard, complex, formal |
| `operator_facing` | `BOOLEAN` | `true` | Whether design_contract is required |
| `behavioral_contract` | `JSONB` | `'{}'` | The "what to build" — operations, pre/post, invariants, signatures |
| `constitution_refs` | `JSONB` | `'[]'` | Pointers to architectural/security/standards constraints |
| `design_contract` | `JSONB` | `'{}'` | Visual language, surfaces, interaction model |
| `user_stories` | `JSONB` | `'[]'` | Narrative arcs with Five Whys traces |
| `task_map` | `JSONB` | `'[]'` | Ordered subtask decomposition with build_target_type and build_phase |
| `discovery_provenance` | `JSONB` | `'{}'` | Context-gathering phase: research, 5 whys, scenarios (v0.2.0) |
| `requirements_provenance` | `JSONB` | `'{}'` | Formalization phase: ACs, stories, contracts (v0.2.0) |
| `interview_provenance` | `JSONB` | `'{}'` | DEPRECATED — use discovery + requirements provenance |
| `module_boundary` | `JSONB` | `'{}'` | Standalone module public API with full signatures (v0.2.0) |
| `graft_points` | `JSONB` | `'[]'` | Host-codebase wiring instructions for graft agent (v0.2.0) |
| `call_graph` | `JSONB` | `'{}'` | Cross-references: called_by and calls (v0.2.0) |
| `lean_spec_ref` | `TEXT` | null | Path to .lean file(s) after formalization |
| `spec_version_id` | `TEXT` | null | Version identifier (tracked in Git) |
| `author` | `TEXT` | null | Who authored the spec |
| `completeness_score` | `REAL` | null | 0.0-1.0 completeness assessment |
| `created_at` | `TIMESTAMPTZ` | `now()` | When the spec was created |
| `updated_at` | `TIMESTAMPTZ` | `now()` | Last modification time |
| `confirmed_at` | `TIMESTAMPTZ` | null | When the operator confirmed the spec |
| `formalized_at` | `TIMESTAMPTZ` | null | When Lean 4 compilation succeeded |

---

## Manufacturing Pipeline Compatibility (v0.2.0)

How each Live Spec section maps to which manufacturing pipeline stage. Each agent consumes specific sections as its instruction set — this table is the routing contract.

### Section-to-Stage Mapping

| Live Spec Section | Stage 1 (Test) | Stage 2 (Code) | Stage 3 (Audit) | Stage 4 (Graft) | Stage 5 (Accept) |
|-------------------|:-:|:-:|:-:|:-:|:-:|
| `behavioral_contract` | READ | READ | READ | — | — |
| `behavioral_contract.signatures` | PRIMARY | READ | READ | — | — |
| `module_boundary` | PRIMARY | PRIMARY | READ | READ | — |
| `module_boundary.exports` | writes tests against these | implements these | verifies against these | — | — |
| `module_boundary.types_defined` | imports/uses in tests | defines these types | type-checks these | — | — |
| `graft_points` | awareness only | — | — | PRIMARY | READ |
| `call_graph` | — | — | cross-ref check | READ | PRIMARY |
| `call_graph.called_by` | — | — | — | verifies anchors exist | verifies call sites work |
| `task_map` | reads own entry | reads own entry | reads own entry | reads own entry | reads all entries |
| `task_map[].build_target_type` | determines if test needed | determines write mode | — | determines if graft needed | — |
| `task_map[].build_phase` | entry gate | entry gate | — | entry gate | — |
| `constitution_refs` | — | READ | PRIMARY | READ | — |
| `user_stories` | context | context | — | — | — |
| `discovery_provenance` | context | — | — | — | — |
| `requirements_provenance` | context | — | — | — | — |

**Legend:** PRIMARY = this section is the agent's primary instruction set. READ = agent reads for context/verification. "—" = not consumed by this stage.

### How the Pipeline Consumes the Spec

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  LIVE SPEC                                                              │
│  ┌──────────────────┐  ┌───────────────────┐  ┌──────────────────────┐ │
│  │ module_boundary   │  │ behavioral_contract│  │ graft_points         │ │
│  │ + signatures      │  │ + signatures       │  │                      │ │
│  └────────┬─────────┘  └────────┬──────────┘  └──────────┬───────────┘ │
│           │                      │                         │             │
│           ▼                      ▼                         ▼             │
│  ┌─────────────────┐  ┌─────────────────┐       ┌─────────────────┐    │
│  │  TEST AGENT     │  │  CODING AGENT   │       │  GRAFT AGENT    │    │
│  │  (Stage 1)      │  │  (Stage 2)      │       │  (Stage 4)      │    │
│  │                 │  │                 │       │                 │    │
│  │  Reads:         │  │  Reads:         │       │  Reads:         │    │
│  │  - signatures   │  │  - module_bound │       │  - graft_points │    │
│  │  - module_bound │  │  - signatures   │       │  - call_graph   │    │
│  │  - task_map AC  │  │  - task_map AC  │       │  - module_bound │    │
│  └─────────────────┘  └─────────────────┘       └─────────────────┘    │
│                                                                         │
│  ┌──────────────────┐                    ┌──────────────────────────┐   │
│  │ call_graph        │                    │ constitution_refs         │   │
│  └────────┬─────────┘                    └──────────┬───────────────┘   │
│           ▼                                          ▼                   │
│  ┌─────────────────┐                    ┌─────────────────┐            │
│  │ ACCEPTANCE AGENT│                    │  AUDIT AGENT    │            │
│  │  (Stage 5)      │                    │  (Stage 3)      │            │
│  │                 │                    │                 │            │
│  │  Reads:         │                    │  Reads:         │            │
│  │  - call_graph   │                    │  - constitution │            │
│  │  - graft_points │                    │  - module_bound │            │
│  │  - task_map     │                    │  - signatures   │            │
│  └─────────────────┘                    └─────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Build Target Type Routing

The `build_target_type` field determines which stages a task passes through:

| `build_target_type` | Stages Executed | Rationale |
|---------------------|-----------------|-----------|
| `standalone_module` | 1 → 2 → 3 → 5 | No graft needed — module is self-contained (test utilities, libraries) |
| `graft` | 4 → 5 | Module already exists — only wiring needed |
| `mixed` | 1 → 2 → 3 → 4 → 5 | Full pipeline — new module + host-code wiring |

Note: `standalone_module` skips Stage 4 (graft) but still runs Stage 5 (acceptance) to verify no import regressions. The acceptance agent verifies that the new module's presence doesn't break existing tests.

### Build Phase Entry Points

The `build_phase` field determines where a task enters the pipeline (for tasks that pick up mid-stream):

| `build_phase` | Entry Point | Use Case |
|---------------|-------------|----------|
| `test` | Stage 1 | Normal flow — test-first development |
| `code` | Stage 2 | Tests already written (e.g., from a prior failed attempt that passed Stage 1) |
| `graft` | Stage 4 | Module already exists and is audited — only wiring remains |

---

## Changelog

### v0.2.0 (2026-05-16)

Changes from v0.1.0 to support the 5-stage manufacturing pipeline (test → code → audit → graft → accept):

**New sections:**
- `module_boundary` (Section 9) — standalone module public API with full Python signatures, types, dependencies, and host import requirements. The test agent and coding agent's primary instruction set.
- `graft_points` (Section 10) — explicit wiring instructions for the graft agent. Defines host file, anchor text, action, and content for each surgical edit.
- `call_graph` (Section 11) — cross-references documenting what calls this module and what this module calls. Enables impact analysis and acceptance verification.

**New sub-sections:**
- `behavioral_contract.signatures` — concrete Python function signatures bridging abstract operations to implementation. Includes parameters with semantics, return types, exception types with trigger conditions.

**Enhanced sections:**
- `task_map` entries gain `build_target_type` (`standalone_module` | `graft` | `mixed`) and `build_phase` (`test` | `code` | `graft`) fields, routing tasks to the correct manufacturing pipeline stages.
- `discovery_provenance` (Section 6) — replaces the divergent/exploratory half of the former `interview_provenance`. Captures research, 5 whys, "what happens when" scenarios, ideal state.
- `requirements_provenance` (Section 7) — replaces the convergent/formalization half of the former `interview_provenance`. Captures decisions, completeness assessment, traceability from discovery to requirements.

**Deprecated:**
- `interview_provenance` (Section 8) — retained for backward compatibility. New specs must use `discovery_provenance` + `requirements_provenance`. The manufacturing pipeline reads from either format.

**New top-level sections:**
- "Manufacturing Pipeline Compatibility" — maps every Live Spec section to the pipeline stages that consume it, with routing rules for `build_target_type` and `build_phase`.

**Schema changes (migration required):**
- Add columns: `module_boundary JSONB DEFAULT '{}'`, `graft_points JSONB DEFAULT '[]'`, `call_graph JSONB DEFAULT '{}'`, `discovery_provenance JSONB DEFAULT '{}'`, `requirements_provenance JSONB DEFAULT '{}'`
- Existing `interview_provenance` column retained (not dropped)
- See `migrations/014_live_spec_v020.sql` for the migration

### v0.1.0 (2026-05-06)

Initial release. Defined behavioral contract, constitution refs, design contract, user stories, task map, and interview provenance.
