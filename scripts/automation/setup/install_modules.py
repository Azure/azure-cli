# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import subprocess
import automation.utilities.path as autmation_path

INSTALL_COMMAND = 'python -m pip install -e {}'


def install_modules():
    all_modules = list(autmation_path.get_command_modules_paths())

    print('Installing command modules')
    print('Modules: {}'.format(', '.join(name for name, _ in all_modules)))
    failures = []

    for name, path in all_modules:
        try:
            subprocess.check_call(INSTALL_COMMAND.format(path).split())
        except subprocess.CalledProcessError as err:
            # exit code is not zero
            failures.append('Failed to install {}. Error message: {}'.format(name, err.output))

    for f in failures:
        print(f)

    return not any(failures)


if __name__ == '__main__':
    sys.exit(0 if install_modules() else 1)
