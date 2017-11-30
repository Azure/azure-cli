# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify package dependency compatibility (with support for allowed exceptions). """

import subprocess
import sys

ALLOWED_ERRORS = []


def init(root):
    parser = root.add_parser('dependencies', help='Run pip check')
    parser.set_defaults(func=verify_dependencies)


def verify_dependencies(_):
    try:
        subprocess.check_output(['pip', 'check'], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as err:
        pip_messages = err.output.splitlines()
        errors = []
        for msg in pip_messages:
            if not any(a in msg for a in ALLOWED_ERRORS):
                errors.append(msg)
        if errors:
            sys.stderr.write('Dependency compatibility errors found!\n')
            sys.stderr.write('\n'.join(errors))
            sys.exit(1)
        else:
            sys.stderr.write("'pip check' returned exit code {} but the errors are allowable.\n".format(err.returncode))
            sys.stderr.write("Full output from pip follows:\n")
            sys.stderr.write(err.output + '\n')
