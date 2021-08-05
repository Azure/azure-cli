# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json

reserved_policy_list = [
  "36e07b214d59455886a2b76b",
  "5b5ec388a1b6480391640d13",
  "5d00856604b74b80927cca6e",
  "8805e4466db647d1beda40e2",
  "DataProtectionSecurityCenter",
  "SecurityCenterBuiltIn"
]


def main():
    print('Clean policy tool 0.1')

    cmd = 'az policy assignment list --query [].name'
    print(cmd)
    result = os.popen(cmd).read()
    for name in json.loads(result):
        if name not in reserved_policy_list:
            cmd = 'az policy assignment delete -n {}'.format(name)
            print(cmd)
            os.popen(cmd)


if __name__ == '__main__':
    main()
