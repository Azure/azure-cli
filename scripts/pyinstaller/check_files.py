# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import json


def check(source_dir, pyinstaller_dir):
    source_dir = source_dir.strip(os.sep)
    pyinstaller_dir = pyinstaller_dir.strip(os.sep)
    missed_files = []
    for root, dirs, files in os.walk(source_dir):
        parent_dirs = root.split(os.sep)
        source_dirs = source_dir.split(os.sep)
        if len(parent_dirs) > len(source_dirs) and not parent_dirs[len(source_dirs)].endswith('dist-info') \
                and not parent_dirs[len(source_dirs)].endswith('egg-info') and '__pycache__' not in parent_dirs \
                and 'test' not in parent_dirs and 'tests' not in parent_dirs:
            for f in files:
                relpath = os.path.relpath(os.path.join(root, f), source_dir)
                pyi_path = os.path.join(pyinstaller_dir, relpath)
                if pyi_path.endswith('.py'):  # we use source code(.py) for pip in MSI build
                    pyi_path = pyi_path + 'c'
                if not os.path.exists(pyi_path):
                    missed_files.append(relpath)
    
    print(json.dumps(missed_files, indent=4))
    print('\n\nTotal missed file count: {}'.format(len(missed_files)))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(1)
    check(sys.argv[1], sys.argv[2])
