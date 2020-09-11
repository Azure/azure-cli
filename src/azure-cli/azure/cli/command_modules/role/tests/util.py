# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

ROLE_COMMAND_MAX_RETRY = 20
ROLE_COMMAND_SLEEP_DURATION = 10


def cmd_with_retry(self, *args, sleep_duration=ROLE_COMMAND_SLEEP_DURATION, max_retry=ROLE_COMMAND_MAX_RETRY, **kwargs):
    """Retry self.cmd and checks until success."""
    # Due to unstable role definition ARIs: https://github.com/Azure/azure-cli/issues/3187
    import time
    result = None
    while not result:
        try:
            result = self.cmd(*args, **kwargs)
        except (AssertionError, CLIError):
            if max_retry > 0:
                max_retry -= 1
                time.sleep(sleep_duration)
            else:
                raise
    return result


def escape_apply_kwargs(val):
    """Replace {} as {{}} so that val is preserved after _apply_kwargs."""
    return val.replace('{', "{{").replace('}', "}}")

