# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests import RecordingProcessor
from azure_devtools.scenario_tests.utilities import is_text_payload

class TimeSpanRecordingProcessor(RecordingProcessor):
    def __init__(self, replacement):
        self._replacement = replacement

    def process_request(self, request):
        request.uri = self._replace_timespan(request.uri)

        if is_text_payload(request) and request.body:
            request.body = self._replace_timespan(request.body.decode()).encode()

        return request

    def process_response(self, response):
        if is_text_payload(response) and response['body']['string']:
            response['body']['string'] = self._replace_timespan(response['body']['string'])

        return response

    def _replace_timespan(self, val):
        import re
        # subscription presents in all api call
        retval = re.sub('/providers/microsoft.insights/metrics\?timespan={.*}&'.format(self._replacement),
                        val,
                        flags=re.IGNORECASE)
        retval = re.sub('"timeStamp":"{.*}"'.format(self._replacement),
                        val,
                        flags=re.IGNORECASE)
        return retval