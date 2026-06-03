# Compliance Validation

## Live Spec Format Validation

Run the spec validator to ensure structural compliance:
```bash
python tooling/spec-validator.py path/to/spec.md
```

## Dragonlight Standards Compliance

Run the standards linter to check code quality:
```bash
python tooling/standards-linter.py path/to/code/
```

## Combined Validation

For full agentic software development compliance, both validations should pass.

## Validation Examples

### Validating the Live Spec Format in this bundle:
```bash
python tooling/spec-validator.py live-spec-format/live-spec-format.jsonl
```

### Validating a search service implementation:
```bash
python tooling/standards-linter.py examples/search_service/
```
