# Dragonlight Software Factory Standards

This repository contains the open-source release of the Dragonlight Software Factory Standards, a comprehensive framework for agentic software development that enables the 5-stage manufacturing pipeline (test → code → audit → graft → accept). Each standard has been sanitized and genericized for open-source release, removing all protected IP, PII, specific threat models, and Dragonlight-specific implementation details while preserving the structural value and generic principles.

## Contents

- **[Live Spec Format](./live-spec-format/)**: The definitive handoff artifact between human operator intent and machine-executable specification
- **[Dragonlight Standards](./dragonlight-standards/)**: 
  - [Security Specification](./dragonlight-standards/dragonlight-security-specification.md): Focuses on WHAT to check for (security categories, attack types, vulnerability states)
  - [Testing & Mocking Standards](./dragonlight-standards/dragonlight-testing-and-mocking-standards.md): Genericized testing principles and methodologies
  - [Coding Standards](./dragonlight-standards/dragonlight-coding-standards-v2.md): Dragonlight Quality (TM) coding standards
  - [Documentation Standards](./dragonlight-standards/dragonlight-documentation-standard.md): Guidelines for documentation
  - [Security Implementation Standards](./dragonlight-standards/dragonlight-security-implementation-standard.md): Mandatory implementation patterns (genericized)
- **[Examples](./examples/)**: Reference implementations demonstrating the standards
- **[Documentation](./documentation/)**: Usage, compliance, and release notes
- **[Tooling](./tooling/)**: Scripts for sanitization, genericization, validation, and live spec processing

## Purpose

The Dragonlight Software Factory Standards provide a complete framework for agentic software development, enabling:
- **Human-Machine Communication**: Live Spec Format bridges operator intent and agent execution
- **Specialized Agent Pipeline**: Each section feeds specific agents in the manufacturing pipeline
- **Traceability**: Every task maps back to behavioral contract elements
- **Iterative Confirmation**: Operators can validate narrative accuracy before any code is written
- **Rationale Documentation**: Captures not just what to build, but why
- **Parallel Work**: Different agents can work on different sections simultaneously
- **Complete Context**: Includes discovery provenance, constitution references, and design considerations
- **Quality Gates**: Each pipeline stage has clear entrance/exit criteria
- **Novelty and Consistency**: Allows innovation while referencing established constraints
- **Living Documentation**: Evolves with the project through the status flow

## Usage

Each standard can be used independently or as part of the complete factory methodology. Refer to the individual standard documents for detailed usage instructions.

## Sanitization & Genericization

All Dragonlight-specific IP, PII, protected secrets, references to unincluded files, specific projects (including DAOS), specific threat models, and implementation details have been removed or replaced with generic equivalents. The standards now focus on:
- **WHAT to check for**: Categories of threats, attack surfaces, vulnerability states
- **Generic principles**: Rather than Dragonlight-specific implementation details
- **Open-source suitability**: Safe for public consumption and adaptation

## License

MIT License - see the [LICENSE](./LICENSE) file for details.

--- 

*Dragonlight Software Factory Standards Version: 1.0.0*