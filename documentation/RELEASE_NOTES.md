# Live Spec Format Release Notes

## Version 0.2.0 (2026-06-02)

### Overview
The Live Spec Format is a dual-representation specification standard designed for agentic software development. It provides both human-readable Markdown and machine-readable JSONL formats to bridge the gap between operator intent and agent execution.

### Key Features
- **Dual Representation**: Human-facing Markdown for operator engagement and machine-facing JSONL for agent consumption
- **Production-Quality**: Designed for the 5-stage manufacturing pipeline (test → code → audit → graft → accept)
- **Traceability**: Built-in provenance tracking from discovery to requirements
- **Modular**: Clear section separation for different agent roles (Formalization, Decomposition, Graft, Acceptance)

### Sections Included in Machine-Only JSONL
- behavioral_contract
- constitution_refs
- task_map
- module_boundary
- graft_points
- call_graph

### Usage
Downstream agents should consume the `live-spec-format.jsonl` file to obtain only the machine-relevant sections:
- behavioral_contract
- constitution_refs
- task_map
- module_boundary
- graft_points
- call_graph

These sections contain exactly what agents need for ticket creation, verification, and execution without human-only elements like narratives, design conversations, or provenance details that would consume context windows unnecessarily.

### Dragonlight Quality
This specification adheres to Dragonlight coding standards and represents the gold standard for agentic software specifications by ensuring:
1. Precise, unambiguous requirements
2. Machine-verifiable contracts
3. Built-in traceability and provenance
4. Pipeline-aware section mapping
5. Minimization of context window usage for machine consumers

### Open Source Release
This release makes the Live Spec Format available as an open standard for agentic software development teams.
