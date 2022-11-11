# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import json

from azure.cli.testsdk.scenario_tests.utilities import is_text_payload
from azure.cli.testsdk.scenario_tests import RecordingProcessor


class StorageSASReplacer(RecordingProcessor):
    """Replace SAS signatures with a hard-coded value"""

    SIG_REPLACEMENT = 'sig=fakeSig'
    PATTERN = r'\?sv=.*&(sig=[^&]+)&'

    def process_request(self, request):
        request.uri = self._replace_sas(request.uri)
        if request.body:
            request.body = self._replace_sas(_byte_to_str(request.body))
        return request

    def process_response(self, response):
        if is_text_payload(response) and response["body"]["string"]:
            body_string = _byte_to_str(response["body"]["string"])
            response["body"]["string"] = self._replace_sas(body_string)
        return response

    def _replace_sas(self, value):
        search_result = re.search(self.PATTERN, value, re.I)
        if search_result and search_result.group(1):
            value = value.replace(search_result.group(1), self.SIG_REPLACEMENT)
        return value


class BatchAccountKeyReplacer(RecordingProcessor):
    """Replace account keys with fake values"""

    def __init__(self):
        self._activated = False
        self._replacements = None
        self._initialize()

    def reset(self):
        self._initialize()

    def _initialize(self):
        self._activated = False
        self._replacements = {
            "primary": KeyReplacement("primary"),
            "secondary": KeyReplacement("secondary")
        }

    def _get_replacement(self, key_name):
        lckey = key_name.lower()
        if lckey not in self._replacements.keys():
            raise KeyError("No replacement for key %s" % key_name)
        return self._replacements[lckey]

    def process_request(self, request):
        body_string = None
        body = None

        if is_text_payload(request) and request.body:
            body_string = _byte_to_str(request.body)
            body = json.loads(body_string)

        pattern = r"/providers/Microsoft\.Batch/batchAccounts/[^/]+/(list|regenerate)Keys$"
        search_result = re.search(pattern, request.path, re.I)
        if search_result:
            self._activated = True
            if search_result.group(1) == "regenerate":
                if body and body["keyName"]:
                    replacement = self._get_replacement(body["keyName"])
                    replacement.should_regen = True

        if body_string:
            for replacement in self._replacements.values():
                for key in replacement.seen_keys:
                    request.body = body_string.replace(key, replacement.key_value)

        return request

    def process_response(self, response):
        if is_text_payload(response) and response['body']['string']:
            body_string = _byte_to_str(response['body']['string'])

            if self._activated:
                body = json.loads(body_string)
                self._process_key_response(body, "primary")
                self._process_key_response(body, "secondary")
                self._activated = False

            for replacement in self._replacements.values():
                for key in replacement.seen_keys:
                    response['body']['string'] = body_string.replace(key, replacement.key_value)

        return response

    def _process_key_response(self, body, key_name):
        original_key = body[key_name]
        if original_key:
            replacement = self._get_replacement(key_name)

            if replacement.should_regen:
                for seen_key in replacement.seen_keys:
                    # Assert that in the unscrubbed response we haven't seen
                    # this key before
                    assert seen_key != original_key, "Key failed to regenerate: %s" % key_name
                replacement.regenerate()

            replacement.seen_keys.add(original_key)


class KeyReplacement:
    """Helper to track individual keys which should be replaced"""

    KEY_PREFIX = 'fakeBatchAccountKey'
    KEY_SUFFIX = "=="

    def __init__(self, key_name):
        self._key_index = 0
        self.key_name = key_name
        self.seen_keys = set()
        self.key_value = self.get_key()
        self.should_regen = False

    def regenerate(self):
        """Mocks key regeneration by updating the replacement key value"""
        self._key_index += 1
        self.key_value = self.get_key()
        self.should_regen = False

    def get_key(self):
        return "".join([self.KEY_PREFIX, str(self._key_index), self.KEY_SUFFIX])


def _byte_to_str(byte_or_str):
    try:
        return str(byte_or_str, 'utf-8') if isinstance(byte_or_str, bytes) else byte_or_str
    except TypeError:  # python 2 doesn't allow decoding through str
        return str(byte_or_str)
