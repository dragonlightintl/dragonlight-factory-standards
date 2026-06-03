#!/usr/bin/env python3
"""
Validate Live Spec Format structure.
Checks that the file contains the required machine-relevant sections.
"""

import json
import sys
import os

def validate_live_spec(file_path):
    """Validate that a Live Spec file has the required structure."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to parse as JSONL (machine-only format)
        lines = content.strip().split('\n')
        sections_found = []
        
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    sections_found.extend(data.keys())
                except json.JSONDecodeError:
                    # If not JSONL, might be markdown - check for sections
                    pass
        
        required_sections = {
            'behavioral_contract', 'constitution_refs', 'task_map', 
            'module_boundary', 'graft_points', 'call_graph'
        }
        
        missing_sections = required_sections - set(sections_found)
        
        if missing_sections:
            print(f"ERROR: Missing required sections: {missing_sections}")
            return False
        else:
            print(f"SUCCESS: All required sections found: {sections_found}")
            return True
            
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        return False
    except Exception as e:
        print(f"ERROR: Validation failed: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python spec-validator.py <live-spec-file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if validate_live_spec(file_path):
        sys.exit(0)
    else:
        sys.exit(1)
