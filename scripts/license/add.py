# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Add license header to every *.py file in the repo.  Can be run multiple times without duplicating the headers.

from _common import PY_LICENSE_HEADER, get_files_without_header, has_shebang

files_without_header = get_files_without_header()

for file_path, file_contents in files_without_header:
    with open(file_path, 'w') as modified:
        if has_shebang(file_contents):
            lines = file_contents.split('\n')
            modified.write(lines[0])
            modified.write('\n' + PY_LICENSE_HEADER)
            modified.write('\n'.join(lines[1:]))
        else:
            modified.write(PY_LICENSE_HEADER + file_contents)
