# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import glob
import os.path
import sys

from automation.utilities.path import get_command_modules_paths_with_tests


def check_recordings():
    """Scan VCR recordings for access tokens"""
    result = []
    for name, _, test_folder in get_command_modules_paths_with_tests():
        print(test_folder)
        for recording_file in glob.glob(os.path.join(test_folder, 'recordings', '*.yaml')):
            print('Scanning: {}'.format(recording_file))
            with open(recording_file, 'r') as f:
                for line in f:
                    line = line.lower()
                    if 'grant_type=refresh_token' in line or '/oauth2/token' in line \
                            or 'authorization:' in line:
                        result.append(recording_file)
                        break

    if result:
        print('Following VCR recording files contain tokens:')
        for f in result:
            print('  {}'.format(f))
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    check_recordings()
