#!/usr/bin/env python3
import re

def genericize_testing_standards(text):
    # Replace specific examples in the testing standards with generic ones
    # In the Mock Design at Seams section, replace kopia and age with generic terms
    # Also replace any paths like /Users/korrigon/DAOS with generic
    
    # Replace the kopia snapshot example
    text = re.sub(r'snapshot_id=\"k1a2b3c4\",\n        source=\"/Users/korrigon/\[REDACTED\]\",\n        start_time=\"2026-04-26T18:30:00Z\",\n        end_time=\"2026-04-26T18:30:45Z\",\n        total_size=75_000_000,\n        files_hashed=2341,\n        status=\"success\"',
                  'snapshot_id=\"snapshot-id\",\n        source=\"/path/to/data\",\n        start_time=\"2026-04-26T18:30:00Z\",\n        end_time=\"2026-04-26T18:30:45Z\",\n        total_size=75_000_000,\n        files_hashed=2341,\n        status=\"success\"',
                  text)
    
    # Replace the BAD mock example that had the path
    text = re.sub(r'# BAD: Mock that returns unrealistic data\n@pytest.fixture\ndef mock_kopia_snapshot\(\):\n    return \\{\"ok\": True\\}  # Not what Kopia actually returns',
                  '# BAD: Mock that returns unrealistic data\n@pytest.fixture\ndef mock_external_tool_result\(\):\n    return {\"ok\": True}  # Not what the actual tool returns',
                  text)
    
    # Also, in the DO Mock table, replace specific tool names with generic
    # We'll replace the Dependency column examples with more generic ones
    # But note: the table is meant to be examples. We can keep the structure but make the examples generic.
    # Let's replace the specific tools with generic categories.
    
    # Replace the DO Mock table rows
    # We'll do a multi-line replacement for the table, but it's easier to replace specific lines.
    # Instead, we'll replace the specific tool names in the Dependency column.
    
    # List of specific tools to replace with generic descriptions
    tool_replacements = [
        (r'External CLI tools \(kopia, age, veracrypt, rmlint, git\)', 'External CLI tools (backup, encryption, linting, version control)'),
        (r'Heavy ML models \(spaCy, etc.\)', 'Heavy ML models (NLP, computer vision, etc.)'),
        (r'Filesystem operations on real paths', 'Filesystem operations on real paths'),
        (r'System clock', 'System clock'),
        (r'Random number generators', 'Random number generators'),
        (r'Network/HTTP calls', 'Network/HTTP calls'),
        (r'Database connections', 'Database connections'),
    ]
    
    for specific, generic in tool_replacements:
        text = re.sub(specific, generic, text)
    
    # In the DO NOT Mock table, we might want to keep as is because it's about what not to mock.
    # But we can leave it.
    
    # In the Anti-Patterns section, there are examples with specific paths and tools.
    # For example, in 1. Integration Test Masquerading as Unit Test:
    # def test_load_rules():\n    conn = sqlite3.connect(\"[REDACTED].db\")
    # We already have [REDACTED] from the sanitize_bundle.py? Actually, the sanitize_bundle.py replaced daos.db with [REDACTED DATABASE] but not [REDACTED].db.
    # Let's check: the file after sanitize_bundle.py might have "[REDACTED].db". We'll replace that with a generic path.
    text = re.sub(r'sqlite3\.connect\(\"\[REDACTED\]\.db\"', 'sqlite3.connect(\"test.db\"', text)
    
    # Also, in the same example, there might be other specifics.
    # We'll also replace any remaining [REDACTED] that are not part of the placeholder we want to keep? 
    # Actually, the [REDACTED] placeholder is from the sanitize_bundle.py for persona names. We might want to keep that as is? 
    # But the task is to remove PII, so [REDACTED] is fine.
    
    # Replace any remaining specific user paths in the examples.
    text = re.sub(r'/Users/korrigon/\[REDACTED\]', '/path/to/project', text)
    text = re.sub(r'/Users/korrigon/DAOS', '/path/to/project', text)
    
    return text

if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    file_path = Path('/Users/coryflanigan/DAOS/02-Projects/factory/dragonlight-software-factory-standards/dragonlight-standards/dragonlight-testing-and-mocking-standards.md')
    text = file_path.read_text()
    new_text = genericize_testing_standards(text)
    file_path.write_text(new_text)
    print(f'Genericized {file_path}')