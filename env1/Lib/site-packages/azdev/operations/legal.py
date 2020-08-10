# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from knack.util import CLIError

from azdev.utilities import (
    display, heading, subheading, get_cli_repo_path, get_ext_repo_paths)


LICENSE_HEADER = """# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""

_IGNORE_SUBDIRS = ['__pycache__', 'vendored_sdks', 'site-packages', 'env']


def check_license_headers():

    heading('Verify License Headers')

    cli_path = get_cli_repo_path()
    all_paths = [cli_path]
    for path in get_ext_repo_paths():
        all_paths.append(path)

    files_without_header = []
    for path in all_paths:
        for current_dir, subdirs, files in os.walk(path):
            for i, x in enumerate(subdirs):
                if x in _IGNORE_SUBDIRS or x.startswith('.'):
                    del subdirs[i]

            # pylint: disable=line-too-long
            file_itr = (os.path.join(current_dir, p) for p in files if p.endswith('.py') and p != 'azure_bdist_wheel.py')
            for python_file in file_itr:
                with open(python_file, 'r', encoding='utf-8') as f:
                    file_text = f.read()
                    if file_text and LICENSE_HEADER not in file_text:
                        files_without_header.append(os.path.join(current_dir, python_file))

    subheading('Results')
    if files_without_header:
        raise CLIError("{}\nError: {} files don't have the required license headers.".format(
            '\n'.join(files_without_header), len(files_without_header)))
    display('License headers verified OK.')
