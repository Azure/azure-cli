# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

ROLE_COMMAND_MAX_RETRY = 20
ROLE_COMMAND_SLEEP_DURATION = 10


def retry(func, sleep_duration=ROLE_COMMAND_SLEEP_DURATION, max_retry=ROLE_COMMAND_MAX_RETRY):
    """Retry func until success."""
    # Due to unstable role definition ARIs: https://github.com/Azure/azure-cli/issues/3187
    import time
    while True:
        try:
            return func()
        except (AssertionError, CLIError):
            # AssertionError is raised by checks in self.cmd or self.assert*
            # CLIError is raised by failed command execution
            if max_retry > 0:
                max_retry -= 1
                time.sleep(sleep_duration)
            else:
                raise


def escape_apply_kwargs(val):
    """Replace {} as {{}} so that val is preserved after _apply_kwargs."""
    return val.replace('{', "{{").replace('}', "}}")
