# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import datetime

ARTIFACT_DIR = sys.argv[1]
ACCOUNT_KEY = sys.argv[2]
USER_LIVE = sys.argv[3]


def main():
    # Create container
    date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if USER_LIVE == '--live':
        mode = 'live'
    elif USER_LIVE == '':
        mode = 'replay'
    else:
        mode = ''
    container = date + mode
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {} --public-access container'
    os.popen(cmd.format(container, ACCOUNT_KEY))

    # Upload files
    for root, dirs, files in os.walk(ARTIFACT_DIR):
        for name in files:
            if name.endswith('html') or name.endswith('json'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac'
                os.popen(cmd.format(fullpath, container, name))


if __name__ == '__main__':
    main()
