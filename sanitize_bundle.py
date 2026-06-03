#!/usr/bin/env python3
import os
import re
from pathlib import Path

# Directory to process
BASE_DIR = Path('/Users/coryflanigan/DAOS/02-Projects/factory/dragonlight-software-factory-standards')

# Patterns to remove/replace
PERSONAS = [
    'DIAN CECHT', 'MORANN', 'CINAED', 'GOIBNIU', 'LUGH',
    'Dian Cecht', 'Morann', 'Cinaed', 'Goibniu', 'Lugh',
    'DIAN CÉCHT', 'DIAN CECHT’',  # variations
]

# Specific phrases to remove
REMOVE_PHRASES = [
    r'Retain specific threat models, advanced defensive techniques, and active vulnerability patterns as INTERNAL',
    r'Apply three-gate review to any future updates',
    r'CLEARED WITH CONDITIONS',
    r'Open source the framework and basic tooling, but retain specific threat models',
    r'specific threat models, advanced defensive techniques, and active vulnerability patterns',
    r'three-gate review',
    r'Phase 1 implementation checklist',  # might be too broad, but we'll see
    r'Dragonlight International',
    r'DAOS',
    r'daos\.db',
    r'daos db',
    r'/Users/coryflanigan/DAOS',
    r'daos-',
    r'daos_',
    r'daos/',
]

# Files to process (markdown files)
MD_FILES = list(BASE_DIR.rglob('*.md'))

def sanitize_text(text):
    # Remove persona names
    for persona in PERSONAS:
        text = re.sub(re.escape(persona), '[REDACTED PERSONA]', text, flags=re.IGNORECASE)
    
    # Remove specific phrases
    for phrase in REMOVE_PHRASES:
        text = re.sub(phrase, '[REDACTED]', text, flags=re.IGNORECASE)
    
    # Remove specific file paths and references
    # Replace paths like /Users/coryflanigan/DAOS/... with [REDACTED PATH]
    text = re.sub(r'/Users/coryflanigan/DAOS[^\s]*', '[REDACTED PATH]', text)
    # Replace daos.db anywhere
    text = re.sub(r'daos\.db', '[REDACTED DATABASE]', text, flags=re.IGNORECASE)
    # Replace any mention of daos as a project
    text = re.sub(r'\bdaos\b', '[REDACTED PROJECT]', text, flags=re.IGNORECASE)
    
    # Remove specific threat model details? We'll instead keep the structure but make generic.
    # For now, we'll just remove lines that look like they contain specific threat actor details.
    # We'll do line-by-line processing for certain sections.
    
    return text

def process_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        content = sanitize_text(content)
        
        # Additional line-based filtering for threat model specifics
        lines = content.split('\n')
        new_lines = []
        skip_section = False
        for line in lines:
            # Skip lines that look like they contain specific threat actor tables or details
            if re.search(r'Threat Actor|Actor.*Capability|Motivation|Primary Attack Surface', line, re.IGNORECASE):
                # We'll keep the header but maybe we want to replace the table with a generic note?
                # For safety, let's replace the whole section later. For now, we'll mark to skip until next header.
                # We'll implement a simple state machine: when we see a header like "### 1.2 Threat Actors", we skip until next "##"
                pass  # We'll do a different approach
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f'Sanitized: {filepath}')
        else:
            print(f'No changes: {filepath}')
    except Exception as e:
        print(f'Error processing {filepath}: {e}')

if __name__ == '__main__':
    for md_file in MD_FILES:
        # Skip the script itself
        if md_file.name == 'sanitize_bundle.py':
            continue
        process_file(md_file)
    
    print('Sanitization complete.')