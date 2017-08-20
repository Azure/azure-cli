# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys


def fix_p2p8(directory):
    import autopep8
    import multiprocessing

    # pylint: disable=protected-access
    autopep8.fix_multiple_files([directory],
                                options=autopep8._get_options(
                                    {
                                        'jobs': multiprocessing.cpu_count(),
                                        'verbose': True,
                                        'recursive': True,
                                        'in_place': True,
                                        'max_line_length': 100
                                    }, False))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python automation.style.pep8 <directory>')
        sys.exit(1)

    fix_p2p8(sys.argv[1])
