# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from io import BytesIO
from types import SimpleNamespace

from vcr.request import Request

from azure.cli.testsdk.scenario_tests.base import IntegrationTestBase, LiveTest, ReplayableTest
from azure.cli.testsdk.scenario_tests.recording_processors import (
    LargeRequestBodyProcessor, SubscriptionRecordingProcessor
)


class TestIntegrationTestBase(unittest.TestCase):
    def test_process_request_recording_with_file_body(self):
        original_subscription = '11111111-1111-1111-1111-111111111111'
        replacement_subscription = '00000000-0000-0000-0000-000000000000'
        uri = 'https://management.azure.com/subscriptions/' + original_subscription
        body = ('{"id":"/subscriptions/' + original_subscription + '"}').encode()
        for recording in (True, False):
            for stream in (True, False):
                with self.subTest(recording=recording, stream=stream):
                    request = Request('POST', uri, BytesIO(body) if stream else body,
                                      {'Content-Type': 'application/json'})
                    processor = SubscriptionRecordingProcessor(replacement_subscription)
                    test = SimpleNamespace(
                        disable_recording=False, in_recording=recording,
                        recording_processors=[processor],
                        recording_post_processors=[LargeRequestBodyProcessor()],
                        replay_processors=[processor, LargeRequestBodyProcessor()])
                    processed = ReplayableTest._process_request_recording(test, request)
                    self.assertEqual(processed.method, 'POST')
                    self.assertEqual(processed.uri, uri.replace(original_subscription, replacement_subscription))
                    self.assertEqual(processed.headers, request.headers)
                    self.assertEqual(processed.body,
                                     body.replace(original_subscription.encode(), replacement_subscription.encode()))
                    if stream:
                        self.assertEqual(request.body.getvalue(), body)
                        self.assertEqual(request.body.tell(), 0)
                    else:
                        self.assertIs(processed, request)

    def test_process_request_recording_preserves_binary_file_body(self):
        body = b'\x00\xff\x01'
        request = Request('POST', 'https://management.azure.com/upload', BytesIO(body),
                          {'Content-Type': 'application/octet-stream'})
        test = SimpleNamespace(
            disable_recording=False, in_recording=True,
            recording_processors=[SubscriptionRecordingProcessor('unused')],
            recording_post_processors=[LargeRequestBodyProcessor()])
        processed = ReplayableTest._process_request_recording(test, request)
        self.assertEqual(processed.body, body)
        self.assertEqual(request.body.getvalue(), body)

    def test_integration_test_default_constructor(self):
        class MockTest(IntegrationTestBase):
            def __init__(self):
                super().__init__('sample_test')

            def sample_test(self):
                pass

        tb = MockTest()

        random_name = tb.create_random_name('example', 90)
        self.assertEqual(len(random_name), 90)
        self.assertTrue(random_name.startswith('example'))

        random_file = tb.create_temp_file(size_kb=16, full_random=False)
        self.addCleanup(lambda: os.remove(random_file))
        self.assertTrue(os.path.isfile(random_file))
        self.assertEqual(os.path.getsize(random_file), 16 * 1024)
        self.assertEqual(len(tb._cleanups), 1)  # pylint: disable=protected-access
        with open(random_file, 'rb') as fq:
            # the file is blank
            self.assertFalse(any(b for b in fq.read(16 * 1024) if b != '\x00'))

        random_file_2 = tb.create_temp_file(size_kb=8, full_random=True)
        self.addCleanup(lambda: os.remove(random_file_2))
        self.assertTrue(os.path.isfile(random_file_2))
        self.assertEqual(os.path.getsize(random_file_2), 8 * 1024)
        self.assertEqual(len(tb._cleanups), 2)  # pylint: disable=protected-access
        with open(random_file_2, 'rb') as fq:
            # the file is blank
            self.assertTrue(any(b for b in fq.read(8 * 1024) if b != '\x00'))

        random_file_3 = tb.create_temp_file(size_kb=8.5)
        self.addCleanup(lambda: os.remove(random_file_3))
        self.assertTrue(os.path.isfile(random_file_3))
        self.assertEqual(os.path.getsize(random_file_3), 8.5 * 1024)
        self.assertEqual(len(tb._cleanups), 3)  # pylint: disable=protected-access
        with open(random_file_3, 'rb') as fq:
            # the file is blank
            self.assertTrue(any(b for b in fq.read(int(8.5 * 1024)) if b != '\x00'))

        random_dir = tb.create_temp_dir()
        self.addCleanup(lambda: os.rmdir(random_dir))
        self.assertTrue(os.path.isdir(random_dir))
        self.assertEqual(len(tb._cleanups), 4)  # pylint: disable=protected-access

    def test_live_test_default_constructor(self):
        class MockTest(LiveTest):
            def __init__(self):
                super().__init__('sample_test')

            def sample_test(self):
                pass
        result = MockTest().run()
        self.assertTrue(result.skipped)
