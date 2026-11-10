# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from vcr.request import Request

from azure.cli.command_modules.backup.tests.latest.test_sql_commands import (
    CrossRegionRestoreAccessTokenReplacer
)


class TestCrossRegionRestoreAccessTokenReplacer(unittest.TestCase):
    def test_request_and_response_tokens_match(self):
        processor = CrossRegionRestoreAccessTokenReplacer()
        for is_bytes in (False, True):
            with self.subTest(is_bytes=is_bytes):
                body = json.dumps({
                    'properties': {
                        'accessTokenString': 'sensitive-token',
                        'otherField': 'preserved'
                    }
                })
                response = {
                    'headers': {'content-type': ['application/json']},
                    'body': {'string': body.encode() if is_bytes else body}
                }
                processor.process_response(response)
                sanitized = json.loads(response['body']['string'])
                self.assertEqual(sanitized['properties']['accessTokenString'], 'fake_crr_access_token')
                self.assertEqual(sanitized['properties']['otherField'], 'preserved')
                self.assertEqual(isinstance(response['body']['string'], bytes), is_bytes)

                request = Request(
                    'POST', 'https://management.azure.com/restore',
                    json.dumps({
                        'crossRegionRestoreAccessDetails': {
                            'accessTokenString': 'sensitive-token',
                            'otherField': 'preserved'
                        }
                    }).encode(),
                    {'content-type': 'application/json'})
                processor.process_request(request)
                sanitized_request = json.loads(request.body)
                self.assertEqual(sanitized_request['crossRegionRestoreAccessDetails'],
                                 sanitized['properties'])

    def test_unrelated_fields_are_unchanged(self):
        processor = CrossRegionRestoreAccessTokenReplacer()
        body = b'{"properties":{"status":"Completed","operation":"CrossRegionRestore"}}'
        request = Request('POST', 'https://management.azure.com/restore', body,
                          {'content-type': 'application/json'})
        response = {'headers': {'content-type': ['application/json']}, 'body': {'string': body}}
        self.assertEqual(processor.process_request(request).body, body)
        self.assertEqual(processor.process_response(response)['body']['string'], body)

    def test_non_json_payload_is_unchanged(self):
        processor = CrossRegionRestoreAccessTokenReplacer()
        body = b'\x00\xff'
        request = Request('POST', 'https://management.azure.com/restore', body,
                          {'content-type': 'application/octet-stream'})
        response = {'headers': {'content-type': ['application/octet-stream']}, 'body': {'string': body}}
        self.assertEqual(processor.process_request(request).body, body)
        self.assertEqual(processor.process_response(response)['body']['string'], body)
