# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Verify that all *.py files have a license header in the file.

from __future__ import print_function
import sys

from _common import get_files_without_header

files_without_header = [file_path for file_path, file_contents in get_files_without_header() if not file_path.endswith('azure_bdist_wheel.py')]

if files_without_header:
    print("Error: The following files don't have the required license headers:", file=sys.stderr)
    print('\n'.join(files_without_header), file=sys.stderr)
    print("Error: {} file(s) found without license headers.".format(len(files_without_header)), file=sys.stderr)
    sys.exit(1)
else:
    print('OK')
