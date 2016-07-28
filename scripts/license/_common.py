#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'))

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

def get_files_without_header():
    files_without_header = []
    for current_dir, _, files in os.walk(ROOT_DIR):
        for a_file in files:
            if a_file.endswith('.py'):
                cur_file_path = os.path.join(current_dir, a_file)
                with open(cur_file_path, 'r') as f:
                    file_text = f.read()

                if not contains_header(file_text):
                    files_without_header.append((cur_file_path, file_text))
    return files_without_header
