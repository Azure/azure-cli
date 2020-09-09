# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def cmd_with_retry(self, *args, **kwargs):
    """Retry self.cmd and checks until success."""
    # Due to unstable role definition ARIs: https://github.com/Azure/azure-cli/issues/3187
    import time
    result = None
    while not result:
        try:
            result = self.cmd(*args, **kwargs)
        except (AssertionError, CLIError):
            time.sleep(10)
    return result
