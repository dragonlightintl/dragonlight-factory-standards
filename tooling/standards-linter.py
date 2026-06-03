#!/usr/bin/env python3
"""
Lint code against Dragonlight Coding Standards.
Basic implementation - in practice this would be more comprehensive.
"""

import os
import sys
import re
from pathlib import Path

def lint_file(file_path):
    """Lint a single file for basic Dragonlight standards compliance."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        issues = []
        lines = content.split('\n')
        
        # Basic checks for Dragonlight standards
        for i, line in enumerate(lines, 1):
            line_num = i
            
            # Check for bare exceptions (should be structured ErrorResult)
            if 'raise Exception(' in line or 'raise ValueError(' in line:
                issues.append(f"L{line_num}: Bare exception detected - use structured ErrorResult")
            
            # Check for missing authentication (if it looks like an endpoint)
            if 'def ' in line and ('endpoint' in line.lower() or 'api' in line.lower() or 'route' in line.lower()):
                # This is a simplified check - real implementation would be more sophisticated
                pass
                
            # Check for potential performance issues
            if 'time.sleep(' in line and not '# TODO' in line and not '# FIXME' in line:
                issues.append(f"L{line_num}: Blocking sleep detected - consider async alternative")
        
        return issues
        
    except Exception as e:
        return [f"Error reading file: {e}"]

def lint_directory(dir_path):
    """Lint all Python files in a directory."""
    issues_found = False
    
    for root, dirs, files in os.walk(dir_path):
        # Skip __pycache__ and similar directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                issues = lint_file(file_path)
                
                if issues:
                    issues_found = True
                    print(f"\n{file_path}:")
                    for issue in issues:
                        print(f"  {issue}")
    
    if not issues_found:
        print("No Dragonlight standards violations found.")
    
    return not issues_found

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python standards-linter.py <file-or-directory>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isfile(path):
        issues = lint_file(path)
        if issues:
            print(f"Issues found in {path}:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)
        else:
            print(f"No issues found in {path}")
            sys.exit(0)
    elif os.path.isdir(path):
        if lint_directory(path):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)
