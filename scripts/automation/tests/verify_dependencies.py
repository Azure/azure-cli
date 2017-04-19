# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify package dependency compatibility (with support for allowed exceptions). """

from __future__ import print_function

import subprocess
import sys

ALLOWED_ERRORS = [
    "has requirement azure-common[autorest]==1.1.4, but you have azure-common 1.1.5.",
    "has requirement azure-common~=1.1.5, but you have azure-common 1.1.4."
]

def verify_dependencies():
    try:
        subprocess.check_output(['pip', 'check'], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as err:
        pip_messages = err.output.splitlines()
        errors = []
        for msg in pip_messages:
            if not any(a in msg for a in ALLOWED_ERRORS):
                errors.append(msg)
        if errors:
            print('Dependency compatibility errors found!', file=sys.stderr)
            print('\n'.join(errors), file=sys.stderr)
            sys.exit(1)
        else:
            print("'pip check' returned exit code {} but the errors are allowable.".format(err.returncode), file=sys.stderr)
            print("Full output from pip follows:", file=sys.stderr)
            print(err.output, file=sys.stderr)

if __name__ == '__main__':
    verify_dependencies()
