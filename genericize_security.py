#!/usr/bin/env python3
import re

def genericize_security_spec(text):
    # Replace specific attack surface examples with generic ones
    # We'll do a series of replacements
    
    # In the Threat Model section, line 59: change the primary attack surface for malicious user input
    text = re.sub(r'User message → Processing Engine → Core → LLM pipeline', 
                  'User input → Application processing → Core logic → LLM interface', 
                  text)
    
    # In the Attack Surfaces table (around line 115-124), replace specific examples with generic
    # But note: the sanitize_bundle.py might have already changed some? Let's check the current content.
    # We'll do a safe replacement by looking for the table and replacing the specific strings.
    
    # Replace Telegram bot webhook / polling -> User-facing webhook/polling interfaces (already done by sanitize?)
    # Replace Claude API dispatch -> Outbound API calls with credentials (already done?)
    # Replace Google Workspace OAuth -> Third-party service OAuth integrations (already done?)
    # Replace VPS SSH -> Remote administration interfaces (already done?)
    # Replace SQLite database file -> Local database storage (already done?)
    # Replace Self-healing pipeline -> Automated code generation and deployment systems (already done?)
    # Replace MCP tool interface -> Tool execution interfaces (already done?)
    # Replace Dependency supply chain -> Package dependency management (already done?)
    
    # However, we want to make sure the table is generic. Let's replace the entire table with a generic version?
    # Instead, we'll do specific replacements for any remaining Dragonlight-specific terms.
    
    # List of specific terms to replace with generic
    replacements = [
        (r'Telegram bot webhook / polling', 'User-facing webhook/polling interfaces'),
        (r'Claude API dispatch', 'Outbound API calls with credentials'),
        (r'Google Workspace OAuth', 'Third-party service OAuth integrations'),
        (r'VPS SSH', 'Remote administration interfaces'),
        (r'SQLite database file', 'Local database storage'),
        (r'Self-healing pipeline', 'Automated code generation and deployment systems'),
        (r'MCP tool interface', 'Tool execution interfaces'),
        (r'Dependency supply chain', 'Package dependency management'),
        (r'DNS resolution', 'DNS resolution'),  # already generic
        (r'Log files', 'Log files'),  # already generic
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Additionally, we might want to remove any remaining Dragonlight-specific references in the text.
    # But note: the document is about Dragonlight, so we cannot remove all mentions of "Dragonlight" because it's the title and owner.
    # The task is to remove protected IP/PII, specific projects (including DAOS), specific threat models, etc.
    # We have already removed DAOS and persona names via sanitize_bundle.py.
    # We should also remove any mention of specific Dragonlight internal processes or tools that are not generic.
    
    # Let's also replace any remaining specific tool names in the text (like kopia, age, etc.) in the testing standards later.
    # For now, we focus on the security spec.
    
    return text

if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    file_path = Path('/Users/coryflanigan/DAOS/02-Projects/factory/dragonlight-software-factory-standards/dragonlight-standards/dragonlight-security-specification.md')
    text = file_path.read_text()
    new_text = genericize_security_spec(text)
    file_path.write_text(new_text)
    print(f'Genericized {file_path}')