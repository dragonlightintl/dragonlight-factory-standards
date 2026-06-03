#!/usr/bin/env python3
import re

def genericize_security_spec(text):
    # Remove or replace Dragonlight-specific references
    
    # 1. Replace the companion reference that mentions Dragonlight Coding Standards
    text = re.sub(r'\*\*Reference\:\*\* SOUP Assessment standard in Dragonlight Coding Standards\.',
                  '',
                  text)
    
    # 2. In the Client identifier validation, replace specific clients with generic ones
    text = re.sub(r'Enum of known clients: `\{\"telegram\", \"vscode\", \"web\", \"cli\"\}`',
                  'Enum of known clients: `{\"messaging-platform\", \"ide\", \"web\", \"command-line\"}`',
                  text)
    
    # 3. In the HTML output encoding, replace "Telegram HTML responses" with generic
    text = re.sub(r'All text inserted into Telegram HTML responses is entity-encoded',
                  'All text inserted into user-facing platform responses is entity-encoded',
                  text)
    
    # 4. Also, in the same line, we might want to keep the example but make it generic? The example is about HTML entities, which is fine.
    # 5. Replace any remaining "Dragonlight" in the text? The title and owner are okay to keep as they are part of the standard's identity, but we are making it open source, so we might want to keep the Dragonlight branding? 
    # The task is to remove protected IP/PII, specific projects (including DAOS), specific threat models, etc. The Dragonlight name itself might be considered IP, but since we are open-sourcing the framework, we might keep the name? 
    # The instruction: "remove any protected IP or PII (persona names, database locations), protected secrets, references to unincluded files, specific projects (including DAOS), specific threat models, anything from DIAN CECHTS recommendation"
    # It doesn't say to remove the Dragonlight name. However, to make it generic for open source, we might want to rename it to something else? 
    # But the user said: "The updated eg security standards should specific _what_ (categories, types of attacks, vulnerability states) to check for, not _HOW_ (and, not WHERE/HOW dragonlight applies them; eg within DAOS)."
    # So we can keep the Dragonlight name as it's the name of the standard, but we should remove specific references to how Dragonlight applies them (like specific tools, internal processes).
    # We'll leave the Dragonlight name as is.
    
    return text

def genericize_testing_standards(text):
    # Remove or replace Dragonlight-specific references
    
    # 1. In the Origin line, remove the reference to Hermes plan
    text = re.sub(r'\(Hermes plan 2026-04-26\)', '', text)
    # Also, if there are extra spaces or parentheses, clean up
    text = re.sub(r'\), evolved from', '), evolved from', text)  # just in case
    
    # 2. In the Mock Design at Seams examples, replace specific tool names and paths with generic
    # We already did some replacements, but let's do a more robust one.
    # Replace the kopia snapshot example with a generic one
    # We'll replace the whole example block? Instead, we'll replace specific parts.
    
    # Replace the source path
    text = re.sub(r'source=\"/Users/korrigon/\[REDACTED\]\"', 'source=\"/path/to/data\"', text)
    text = re.sub(r'source=\"/Users/korrigon/DAOS\"', 'source=\"/path/to/data\"', text)
    
    # 3. In the DO Mock table, replace specific tool examples with generic categories
    # We'll replace the Dependency column examples
    # We do this by replacing the specific phrases in the table.
    # Since the table is in markdown, we can do:
    text = re.sub(r'External CLI tools \(kopia, age, veracrypt, rmlint, git\)', 
                  'External CLI tools (backup, encryption, linting, version control)', 
                  text)
    text = re.sub(r'Heavy ML models \(spaCy, etc.\)', 
                  'Heavy ML models (NLP, computer vision, etc.)', 
                  text)
    
    # 4. In the Anti-Patterns section, replace specific examples
    # For example, in 1. Integration Test Masquerading as Unit Test:
    # We already replaced the sqlite3.connect line, but let's do it again to be sure.
    text = re.sub(r'sqlite3\.connect\(\"\[REDACTED\]\.db\"', 'sqlite3.connect(\"test.db\"', text)
    text = re.sub(r'sqlite3\.connect\(\"[^\"]*\\.db\"', 'sqlite3.connect(\"test.db\"', text)
    
    # 5. Replace any remaining specific user paths
    text = re.sub(r'/Users/korrigon/\[REDACTED\]', '/path/to/project', text)
    text = re.sub(r'/Users/korrigon/DAOS', '/path/to/project', text)
    
    return text

if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    # Process security spec
    security_path = Path('/Users/coryflanigan/DAOS/02-Projects/factory/dragonlight-software-factory-standards/dragonlight-standards/dragonlight-security-specification.md')
    security_text = security_path.read_text()
    security_new = genericize_security_spec(security_text)
    security_path.write_text(security_new)
    print(f'Genericized {security_path}')
    
    # Process testing standards
    testing_path = Path('/Users/coryflanigan/DAOS/02-Projects/factory/dragonlight-software-factory-standards/dragonlight-standards/dragonlight-testing-and-mocking-standards.md')
    testing_text = testing_path.read_text()
    testing_new = genericize_testing_standards(testing_text)
    testing_path.write_text(testing_new)
    print(f'Genericized {testing_path}')