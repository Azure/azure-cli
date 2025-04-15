# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload

MOCK_GUID = '00000000-0000-0000-0000-000000000001'
MOCK_SECRET = 'fake-secret'


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
        if 'secret' in val:
            val = re.sub(r'"secret":( ?)"([^"]+)"', r'"secret":"{}"'
                         .format(MOCK_SECRET), val, flags=re.IGNORECASE)
        if 'clientId' in val:
            val = re.sub(r'"clientId":( ?)"([^"]+)"', r'"clientId":"{}"'
                         .format(MOCK_GUID), val, flags=re.IGNORECASE)
        if 'objectId' in val:
            val = re.sub(r'"objectId":( ?)"([^"]+)"', r'"objectId":"{}"'
                         .format(MOCK_GUID), val, flags=re.IGNORECASE)
        if 'principalId' in val:
            val = re.sub(r'"principalId":( ?)"([^"]+)"', r'"principalId":"{}"'
                         .format(MOCK_GUID), val, flags=re.IGNORECASE)
        return val

    # pylint: disable=no-self-use
    def _replace_byte_keys(self, val):
        import re
        if b'secret' in val:
            val = re.sub(b'"secret":( ?)"([^"]+)"',
                         ('"secret":"{}"'.format(MOCK_SECRET)).encode('utf-8'),
                         val, flags=re.IGNORECASE)
        if b'clientId' in val:
            val = re.sub(b'"clientId":( ?)"([^"]+)"',
                         ('"clientId":"{}"'.format(MOCK_GUID)).encode('utf-8'),
                         val, flags=re.IGNORECASE)
        if b'objectId' in val:
            val = re.sub(b'"objectId":( ?)"([^"]+)"',
                         ('"objectId":"{}"'.format(MOCK_GUID)).encode('utf-8'),
                         val, flags=re.IGNORECASE)
        if b'principalId' in val:
            val = re.sub(b'"principalId":( ?)"([^"]+)"',
                         ('"principalId":"{}"'.format(MOCK_GUID)).encode('utf-8'),
                         val, flags=re.IGNORECASE)
        return val
