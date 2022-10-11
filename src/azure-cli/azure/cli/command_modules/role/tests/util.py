# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.testsdk.scenario_tests.recording_processors import RecordingProcessor

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


class MSGraphUpnReplacer(RecordingProcessor):
    """Replace UPN with encoded #
    """
    def __init__(self, test_name, mock_name):
        self.test_name = test_name
        self.test_name_encoded = test_name.replace('#', '%23')
        self.mock_name = mock_name
        self.mock_name_encoded = mock_name.replace('#', '%23')

    def process_request(self, request):
        request.uri = request.uri.replace(self.test_name_encoded, self.mock_name_encoded)
        return request
