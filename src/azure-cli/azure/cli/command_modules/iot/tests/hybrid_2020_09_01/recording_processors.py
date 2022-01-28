# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload

MOCK_KEY = 'mock_key'


class KeyReplacer(RecordingProcessor):

    def process_request(self, request):
        if is_text_payload(request) and isinstance(request.body, bytes):
            request.body = self._replace_byte_keys(request.body)
        elif is_text_payload(request) and isinstance(request.body, str):
            request.body = self._replace_string_keys(request.body)
        return request

    def process_response(self, response):
        if is_text_payload(response) and response['body']['string']:
            response['body']['string'] = self._replace_string_keys(response['body']['string'])
        return response

    # pylint: disable=no-self-use
    def _replace_string_keys(self, val):
        import re
        if 'primaryKey' in val:
            val = re.sub(r'"primaryKey":( ?)"([^"]+)"', r'"primaryKey":"{}"'
                         .format(MOCK_KEY), val, flags=re.IGNORECASE)
        if 'secondaryKey' in val:
            val = re.sub(r'"secondaryKey":( ?)"([^"]+)"', r'"secondaryKey":"{}"'
                         .format(MOCK_KEY), val, flags=re.IGNORECASE)
        return val

    # pylint: disable=no-self-use
    def _replace_byte_keys(self, val):
        import re
        if b'primaryKey' in val:
            val = re.sub(b'"primaryKey":( ?)"([^"]+)"', '"primaryKey":"{}"'
                         .format(MOCK_KEY).encode(), val, flags=re.IGNORECASE)
        if b'secondaryKey' in val:
            val = re.sub(b'"secondaryKey":( ?)"([^"]+)"', '"secondaryKey":"{}"'
                         .format(MOCK_KEY).encode(), val, flags=re.IGNORECASE)
        return val
