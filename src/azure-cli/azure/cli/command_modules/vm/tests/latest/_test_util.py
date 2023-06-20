# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import RecordingProcessor


class TimeSpanProcessor(RecordingProcessor):
    def __init__(self, replacement):
        self._replacement = replacement

    def process_request(self, request):
        request.uri = self._replace_timespan(request.uri)

        return request

    def _replace_timespan(self, val):
        import re
        # subscription presents in all api call
        retval = re.sub('timespan=((.*?)(&|$))',
                        r'timespan={}\3'.format(self._replacement),
                        val,
                        flags=re.IGNORECASE)
        return retval
