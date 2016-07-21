#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
from __future__ import print_function
import os 

# Add license header to every *.py file in the repo.  Can be run multiple times without duplicating the headers.

root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

PY_LICENSE_HEADER = \
"""#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
"""

def contains_header(text):
    return PY_LICENSE_HEADER in text

def has_shebang(text):
    return text.startswith('#!')

for current_dir, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(current_dir, file), 'r') as original:
                file_text = original.read()

            if contains_header(file_text):
                continue

            with open(os.path.join(current_dir, file), 'w') as modified:
                if has_shebang(file_text):
                    lines = file_text.split('\n')
                    modified.write(lines[0])
                    modified.write('\n' + PY_LICENSE_HEADER)
                    modified.write('\n'.join(lines[1:]))
                else:
                    modified.write(PY_LICENSE_HEADER + file_text)
