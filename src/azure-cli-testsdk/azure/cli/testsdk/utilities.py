# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from contextlib import contextmanager

from azure_devtools.scenario_tests import (create_random_name as create_random_name_base, RecordingProcessor,
                                           GeneralNameReplacer as _BuggyGeneralNameReplacer)
from azure_devtools.scenario_tests.utilities import is_text_payload


def create_random_name(prefix='clitest', length=24):
    return create_random_name_base(prefix=prefix, length=length)


def find_recording_dir(test_file):
    """ Find the directory containing the recording of given test file based on current profile. """
    return os.path.join(os.path.dirname(test_file), 'recordings')


@contextmanager
def force_progress_logging():
    from six import StringIO
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


def _py3_byte_to_str(byte_or_str):
    import logging
    logger = logging.getLogger()
    logger.warning(type(byte_or_str))
    try:
        return str(byte_or_str, 'utf-8') if isinstance(byte_or_str, bytes) else byte_or_str
    except TypeError:  # python 2 doesn't allow decoding through str
        return str(byte_or_str)


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
                body_string = _py3_byte_to_str(request.body)
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
                response['body']['string'] = _py3_byte_to_str(body)
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
                body = _py3_byte_to_str(request.body)
                body = json.loads(body)
                for password_cred in body['passwordCredentials']:
                    if password_cred['value']:
                        body_string = _py3_byte_to_str(request.body)
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


class AADGraphUserReplacer:
    def __init__(self, test_user, mock_user):
        self.test_user = test_user
        self.mock_user = mock_user

    def process_request(self, request):
        test_user_encoded = self.test_user.replace('@', '%40')
        if test_user_encoded in request.uri:
            request.uri = request.uri.replace(test_user_encoded, self.mock_user.replace('@', '%40'))

        if request.body:
            body = _py3_byte_to_str(request.body)
            if self.test_user in body:
                request.body = body.replace(self.test_user, self.mock_user)

        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = response['body']['string'].replace(self.test_user,
                                                                            self.mock_user)
        return response


# Override until this is fixed in azure_devtools
class GeneralNameReplacer(_BuggyGeneralNameReplacer):

    def process_request(self, request):
        for old, new in self.names_name:
            request.uri = request.uri.replace(old, new)

            if is_text_payload(request) and request.body:
                try:
                    body = str(request.body, 'utf-8') if isinstance(request.body, bytes) else str(request.body)
                except TypeError:  # python 2 doesn't allow decoding through str
                    body = str(request.body)
                if old in body:
                    request.body = body.replace(old, new)

        return request
