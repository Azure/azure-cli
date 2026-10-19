# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
from contextlib import contextmanager

from .scenario_tests import (create_random_name as create_random_name_base, RecordingProcessor)
from .scenario_tests.utilities import is_text_payload


def create_random_name(prefix='clitest', length=24):
    return create_random_name_base(prefix=prefix, length=length)


def find_recording_dir(test_file):
    """ Find the directory containing the recording of given test file based on current profile. """
    return os.path.join(os.path.dirname(test_file), 'recordings')


@contextmanager
def force_progress_logging():
    from io import StringIO
    import logging
    from knack.log import get_logger
    from .reverse_dependency import get_commands_loggers

    cmd_logger = get_commands_loggers()

    # register a progress logger handler to get the content to verify
    test_io = StringIO()
    test_handler = logging.StreamHandler(test_io)
    cmd_logger.addHandler(test_handler)
    old_cmd_level = cmd_logger.level
    cmd_logger.setLevel(logging.INFO)

    # this tells progress logger we are under verbose, so should log
    az_logger = get_logger()
    old_az_level = az_logger.handlers[0].level
    az_logger.handlers[0].level = logging.INFO

    yield test_io

    # restore old logging level and unplug the test handler
    cmd_logger.removeHandler(test_handler)
    cmd_logger.setLevel(old_cmd_level)
    az_logger.handlers[0].level = old_az_level


def _byte_to_str(byte_or_str):
    return str(byte_or_str, 'utf-8') if isinstance(byte_or_str, bytes) else byte_or_str


class StorageAccountKeyReplacer(RecordingProcessor):
    """Replace the access token for service principal authentication in a response body."""

    KEY_REPLACEMENT = 'veryFakedStorageAccountKey=='

    def __init__(self):
        self._activated = False
        self._candidates = []

    def reset(self):
        self._activated = False
        self._candidates = []

    def process_request(self, request):  # pylint: disable=no-self-use
        import re
        try:
            pattern = r"/providers/Microsoft\.Storage/storageAccounts/[^/]+/listKeys$"
            if re.search(pattern, request.path, re.I):
                self._activated = True
        except AttributeError:
            pass
        for candidate in self._candidates:
            if request.body:
                body_string = _byte_to_str(request.body)
                request.body = body_string.replace(candidate, self.KEY_REPLACEMENT)
        return request

    def process_response(self, response):
        if self._activated:
            import json
            try:
                body = json.loads(response['body']['string'])
                keys = body['keys']
                for key_entry in keys:
                    self._candidates.append(key_entry['value'])
                self._activated = False
            except (KeyError, ValueError, TypeError):
                pass
        for candidate in self._candidates:
            if response['body']['string']:
                body = response['body']['string']
                response['body']['string'] = _byte_to_str(body)
                response['body']['string'] = response['body']['string'].replace(candidate, self.KEY_REPLACEMENT)
        return response


class GraphClientPasswordReplacer(RecordingProcessor):
    """Replace the access token for service principal authentication in a response body."""

    PWD_REPLACEMENT = 'ReplacedSPPassword123*'

    def __init__(self):
        self._activated = False

    def reset(self):
        self._activated = False

    def process_request(self, request):  # pylint: disable=no-self-use
        import re
        import json

        try:
            # issue with how vcr.Request.body adds b' to text types if self.body is used.
            if request.body and self.PWD_REPLACEMENT in str(request.body):
                return request

            pattern = r"[^/]+/applications$"
            if re.search(pattern, request.path, re.I) and request.method.lower() == 'post':
                self._activated = True
                body = _byte_to_str(request.body)
                body = json.loads(body)
                for password_cred in body['passwordCredentials']:
                    if password_cred['value']:
                        body_string = _byte_to_str(request.body)
                        request.body = body_string.replace(password_cred['value'], self.PWD_REPLACEMENT)

        except (AttributeError, KeyError):
            pass

        return request

    def process_response(self, response):
        if self._activated:
            try:
                import json

                body = json.loads(response['body']['string'])
                for password_cred in body['passwordCredentials']:
                    password_cred['value'] = password_cred['value'] or self.PWD_REPLACEMENT

                response['body']['string'] = json.dumps(body)
                self._activated = False

            except (AttributeError, KeyError):
                pass

        return response


class MSGraphClientPasswordReplacer(RecordingProcessor):
    """Replace 'secretText' property in 'addPassword' API's response."""

    PWD_REPLACEMENT = 'replaced-microsoft-graph-password'

    def __init__(self):
        self._activated = False

    def reset(self):
        self._activated = False

    def process_request(self, request):
        if request.path.endswith('/addPassword') and request.method.lower() == 'post':
            self._activated = True
        return request

    def process_response(self, response):
        if self._activated:
            import json

            body = json.loads(response['body']['string'])
            body['secretText'] = self.PWD_REPLACEMENT

            response['body']['string'] = json.dumps(body)
            self._activated = False

        return response


class MSGraphNameReplacer(RecordingProcessor):
    """If a name appears in URL, it should be percent-encoded, e.g.
      - test-name+/ is encoded as test-name%2B%2F
      - example@example.com is encoded as example%40example.com

    Theoretically, GeneralNameReplacer should also follow this pattern, but since we haven't seen any ARM name that
    is percent-encoded, we only replace percent-encoded names for MS Graph for better test performance.
    """
    def __init__(self, test_name, mock_name):
        from urllib.parse import quote
        self.test_name = test_name
        self.test_name_encoded = quote(test_name, safe='')
        self.mock_name = mock_name
        self.mock_name_encoded = quote(mock_name, safe='')

    def process_request(self, request):
        request.uri = request.uri.replace(self.test_name_encoded, self.mock_name_encoded)

        if request.body:
            body = _byte_to_str(request.body)
            request.body = body.replace(self.test_name, self.mock_name)

        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = response['body']['string'].replace(self.test_name, self.mock_name)
        return response


class EmailAddressReplacer(RecordingProcessor):
    """Replace email address like xxx@microsoft.com with test@example.com"""

    EMAIL_REPLACEMENT = 'test@example.com'

    def _replace_email_address(self, text):
        pattern = r'[\w.%#+-]+[%40|@|_]microsoft.com'
        return re.sub(pattern, self.EMAIL_REPLACEMENT, text)

    def process_request(self, request):
        request.uri = self._replace_email_address(request.uri)
        if request.body:
            try:
                body = _byte_to_str(request.body)
                request.body = self._replace_email_address(body)
            except UnicodeDecodeError:
                # If the body is not a string, we cannot decode it, so we skip the replacement
                pass
        return request

    def process_response(self, response):
        if response['body']['string']:
            try:
                body = _byte_to_str(response['body']['string'])
                response['body']['string'] = self._replace_email_address(body)
            except UnicodeDecodeError:
                # If the body is not a string, we cannot decode it, so we skip the replacement
                pass
        return response


class MSGraphUserProfileReplacer(RecordingProcessor):
    """Remove personal profile data of Microsoft Graph user objects from JSON responses.

    - Contact fields (phones, job title, office location, address) are cleared on every Graph user object.
    - The signed-in user is learned from the `/me` response of any built-in cloud's Graph endpoint. Its name fields
      are replaced with mock values, and so is any later JSON string value that exactly equals one of its names.

    Only decoded JSON values are changed; keys, other values and non-JSON bodies are left untouched.
    """

    MOCKED_DISPLAY_NAME = 'Test User'
    MOCKED_GIVEN_NAME = 'Test'
    MOCKED_SURNAME = 'User'
    _NAME_FIELDS = (('displayName', MOCKED_DISPLAY_NAME), ('givenName', MOCKED_GIVEN_NAME),
                    ('surname', MOCKED_SURNAME))
    _CLEARED_FIELDS = {'businessPhones': [], 'mobilePhone': None, 'faxNumber': None, 'jobTitle': None,
                       'officeLocation': None, 'department': None, 'companyName': None, 'streetAddress': None,
                       'city': None, 'state': None, 'postalCode': None, 'country': None}
    # Hosts of `microsoft_graph_resource_id` for the built-in clouds in azure.cli.core.cloud
    GRAPH_HOSTS = ('graph.microsoft.com', 'graph.microsoft.us', 'dod-graph.microsoft.us',
                   'microsoftgraph.chinacloudapi.cn', 'graph.microsoft.de', 'graph.svc.sovcloud.fr')

    def __init__(self):
        self._is_me_request = False
        self._me_id = None
        self._names = {}

    def reset(self):
        self._is_me_request = False
        self._me_id = None
        self._names = {}

    def process_request(self, request):
        from urllib.parse import urlparse
        url = urlparse(request.uri)
        self._is_me_request = ((url.hostname or '').lower() in self.GRAPH_HOSTS and
                               url.path.rstrip('/').lower().endswith('/me') and request.method.upper() == 'GET')
        return request

    def _learn_me(self, me):
        if not isinstance(me, dict):
            return
        if isinstance(me.get('id'), str):
            self._me_id = me['id']
        for key, mock in self._NAME_FIELDS:
            if isinstance(me.get(key), str) and me[key]:
                self._names[me[key]] = mock

    def _scrub(self, obj):
        if isinstance(obj, list):
            return [self._scrub(item) for item in obj]
        if isinstance(obj, dict):
            result = {key: self._scrub(value) for key, value in obj.items()}
            if 'userPrincipalName' in obj:
                for key, value in self._CLEARED_FIELDS.items():
                    if key in result:
                        result[key] = value
                if self._me_id is not None and obj.get('id') == self._me_id:
                    for key, mock in self._NAME_FIELDS:
                        if result.get(key):
                            result[key] = mock
            return result
        if isinstance(obj, str):
            return self._names.get(obj, obj)
        return obj

    def process_response(self, response):
        import json

        is_me_response, self._is_me_request = self._is_me_request, False
        body = response['body']['string']
        if not body:
            return response
        try:
            body = _byte_to_str(body)
            data = json.loads(body)
        except (UnicodeDecodeError, ValueError):
            return response

        if is_me_response:
            self._learn_me(data)
        if not self._names and '"userPrincipalName"' not in body:
            return response

        scrubbed = self._scrub(data)
        if scrubbed != data:
            response['body']['string'] = json.dumps(scrubbed)
        return response


class AADAuthRequestFilter(RecordingProcessor):
    """Remove oauth authentication requests and responses from recording.
    This is derived from OAuthRequestResponsesFilter.
    """
    def process_request(self, request):
        # filter AAD requests like:
        # Tenant discovery: GET
        # https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a/v2.0/.well-known/openid-configuration
        # Get access token: POST
        # https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a/oauth2/v2.0/token
        if request.uri.startswith('https://login.microsoftonline.com'):
            return None
        return request
