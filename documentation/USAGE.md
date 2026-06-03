# Using Live Spec Format and Dragonlight Coding Standards

## Overview

The Live Spec Format defines WHAT to build - the complete intent of a build request in a machine-parseable format.
The Dragonlight Coding Standards define HOW to build it with Dragonlight quality - battle-tested standards for LLM-aware software development.

## Integration Points

1. **constitution_refs** in Live Spec Format references specific standards from the Dragonlight Coding Standards
2. **Task Map** acceptance criteria can incorporate standard-compliant requirements
3. **Module Boundary** specifications should align with Dragonlight coding standards for error handling, security, etc.

## Validation

Use the provided tooling to validate both spec compliance and standard compliance:
- `tooling/spec-validator.py` - Validates Live Spec Format structure
- `tooling/standards-linter.py` - Checks code against Dragonlight standards

## Examples

See the `examples/` directory for reference implementations showing proper usage.

## Agentic Software Development Workflow

1. **Operator Engagement**: Create Live Spec through narrative interview
2. **Specification Processing**: Extract machine-relevant sections for agent consumption
3. **Formalization**: Test Agent validates behavioral contract
4. **Implementation**: Coding Agent implements module boundary
5. **Audit**: Audit Agent checks constitution_refs compliance
6. **Integration**: Graft Agent wires module using graft points
7. **Acceptance**: Acceptance Agent verifies using call_graph

## Version Compatibility

This bundle includes:
- Live Spec Format v0.2.0
- Dragonlight Coding Standards v2.0.0

Components are versioned independently but tested together in this bundle release.
