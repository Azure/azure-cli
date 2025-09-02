#!/usr/bin/env python3
"""Quick script to fix exit_code -> returncode in test_framework.py"""

with open('test_framework.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all instances
content = content.replace("'exit_code'", "'returncode'")

with open('test_framework.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all exit_code -> returncode replacements")
