# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
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


class MSGraphUserReplacer(RecordingProcessor):
    def __init__(self, test_user, mock_user):
        self.test_user = test_user
        self.mock_user = mock_user

    def process_request(self, request):
        if self.test_user in request.uri:
            request.uri = request.uri.replace(self.test_user, self.mock_user)

        if request.body:
            body = _byte_to_str(request.body)
            if self.test_user in body:
                request.body = body.replace(self.test_user, self.mock_user)

        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = response['body']['string'].replace(self.test_user,
                                                                            self.mock_user)
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
