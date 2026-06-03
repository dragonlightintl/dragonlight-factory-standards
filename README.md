# Live Spec Format

The Live Spec Format is the cornerstone of the Dragonlight agentic software development methodology. It serves as the definitive handoff artifact between human operator intent and machine-executable specification, enabling the 5-stage manufacturing pipeline (test → code → audit → graft → accept).

## Purpose

The Live Spec captures the complete intent of a build request in a format that is:
- **Human-readable**: Operators can verify it matches their intent ("does this tell the same story I told you?")
- **Machine-parseable**: Multiple specialized agents consume different sections:
  - Formalization Agent extracts behavioral contracts for Lean 4 formalization
  - UX Agent extracts design contracts for prototyping
  - Decomposition Agent creates task maps with acceptance criteria
- **Pre-code confirmation**: No code is written until the Live Spec is confirmed by the operator

## Sections

### 1. Behavioral Contract
Defines "what to build" with no ambiguity, flowing to Lean 4 formalization. Includes:
- Inputs, outputs, and operations with pre/postconditions
- Edge cases and error states
- System invariants
- Concrete function signatures with full typing (v0.2.0)
- Mapping to Lean 4 constructs

### 2. System Constitution References
References to existing architectural constraints, coding standards, and security policies that bound the work. Each reference includes:
- Type (architecture, coding_standard, security, performance, etc.)
- Path to constraint definition
- Human-readable summary of applicability

### 3. Design Contract
Visual language, surfaces, and interaction model for operator-facing surfaces (required when `operator_facing = true`). Includes:
- Visual language (palette, typography, spacing)
- Surface specifications (CLI, TUI, web, desktop, mobile)
- Interaction model (navigation, selection, feedback)
- Accessibility considerations

### 4. User Stories / Narrative Frame
Stories framed as narrative arcs for operator verification. Includes:
- Role, action, outcome
- Narrative arc (setup, rising action, climax, resolution)
- Five Whys analysis for root motivations
- Edge cases as complications
- Error states as failure endings
- Acceptance criteria references

### 5. Actionable Task Map
Ordered subtask decomposition with acceptance criteria referencing the behavioral contract. Includes:
- Task ID, title, description, order, dependencies
- Build target type (standalone_module, graft, mixed)
- Build phase (test, code, graft)
- Acceptance criteria with verification methods and behavioral contract references
- Estimated complexity and target files

### 6. Discovery Provenance (v0.2.0)
Captures the context-gathering phase (divergent thinking) before formalizing requirements. Includes:
- Interview method and sessions
- Research notes and decisions
- Ideal state vision
- Open questions remaining

## Why It's the Gold Standard

The Live Spec Format is considered the gold standard for agentic software specifications because it:

1. **Bridges Human-Machine Communication**: Serves as a verified contract between operator intent and agent execution
2. **Enables Specialized Agent Pipeline**: Each section feeds specific agents in the manufacturing pipeline
3. **Ensures Traceability**: Every task maps back to behavioral contract elements, which trace to Lean 4 theorems
4. **Supports Iterative Confirmation**: Operators can validate narrative accuracy before any code is written
5. **Documents Rationale**: Captures not just what to build, but why (through Five Whys and narrative arcs)
6. **Enables Parallel Work**: Different agents can work on different sections simultaneously after confirmation
7. **Provides Complete Context**: Includes discovery provenance, constitution references, and design considerations
8. **Facilitates Quality Gates**: Each pipeline stage has clear entrance/exit criteria based on spec sections
9. **Supports Both Novelty and Consistency**: Allows innovation while referencing established constraints
10. **Creates Living Documentation**: Evolves with the project through the status flow (draft → confirmed → decomposed)

The format has been battle-tested in complex agentic software projects where traditional specifications failed due to ambiguity, miscommunication, or lack of machine-readability. By making the specification itself a first-class artifact in the development process, the Live Spec Format ensures that agentic software development remains grounded in human intent while leveraging machine precision.

---
*Live Spec Format Version: 0.2.0*
