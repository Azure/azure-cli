# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import unittest
import os
import inspect
import tempfile
import shutil
import logging
import threading
import vcr

from .config import TestConfig
from .const import ENV_TEST_DIAGNOSE
from .utilities import create_random_name
from .decorators import live_only
from .recording_processors import ContentLengthProcessor


class IntegrationTestBase(unittest.TestCase):
    def __init__(self, method_name):
        super(IntegrationTestBase, self).__init__(method_name)
        self.diagnose = os.environ.get(ENV_TEST_DIAGNOSE, None) == 'True'
        self.logger = logging.getLogger('azure.cli.testsdk.scenario_tests')

    def create_random_name(self, prefix, length):  # pylint: disable=no-self-use
        return create_random_name(prefix=prefix, length=length)

    def create_temp_file(self, size_kb, full_random=False):
        """
        Create a temporary file for testing. The test harness will delete the file during tearing down.
        :param float size_kb: specify the generated file size in kb.
        """
        fd, path = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(lambda: os.remove(path))

        with open(path, mode='r+b') as f:
            if full_random:
                chunk = os.urandom(1024)
            else:
                chunk = bytearray([0] * 1024)
            for _ in range(int(size_kb)):
                f.write(chunk)
            chunk = os.urandom(int(1024 * (size_kb % 1)))
            f.write(chunk)

        return path

    def create_temp_dir(self):
        """
        Create a temporary directory for testing. The test harness will delete the directory during tearing down.
        """
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        return temp_dir

    @classmethod
    def set_env(cls, key, val):
        os.environ[key] = val

    @classmethod
    def pop_env(cls, key):
        return os.environ.pop(key, None)


@live_only()
class LiveTest(IntegrationTestBase):
    pass


class ReplayableTest(IntegrationTestBase):  # pylint: disable=too-many-instance-attributes
    FILTER_HEADERS = [
        'authorization',
        'client-request-id',
        'retry-after',
        'x-ms-client-request-id',
        'x-ms-correlation-request-id',
        'x-ms-ratelimit-remaining-subscription-reads',
        'x-ms-request-id',
        'x-ms-routing-request-id',
        'x-ms-gateway-service-instanceid',
        'x-ms-ratelimit-remaining-tenant-reads',
        'x-ms-served-by',
        'x-ms-authorization-auxiliary'
    ]

    def __init__(self,  # pylint: disable=too-many-arguments
                 method_name, config_file=None, recording_dir=None, recording_name=None, recording_processors=None,
                 replay_processors=None, recording_patches=None, replay_patches=None):
        super(ReplayableTest, self).__init__(method_name)

        self.recording_processors = recording_processors or []
        # Processors that will be called when all self.recording_processors finishes
        self.recording_post_processors = [ContentLengthProcessor()]
        self.replay_processors = replay_processors or []

        self.recording_patches = recording_patches or []
        self.replay_patches = replay_patches or []

        self.config = TestConfig(config_file=config_file)

        self.disable_recording = False

        test_file_path = inspect.getfile(self.__class__)
        recording_dir = recording_dir or os.path.join(os.path.dirname(test_file_path), 'recordings')
        self.is_live = self.config.record_mode

        self.vcr = vcr.VCR(
            cassette_library_dir=recording_dir,
            before_record_request=self._process_request_recording,
            before_record_response=self._process_response_recording,
            decode_compressed_response=True,
            record_mode='once' if not self.is_live else 'all',
            filter_headers=self.FILTER_HEADERS
        )
        self.vcr.register_matcher('query', self._custom_request_query_matcher)

        self.recording_file = os.path.join(
            recording_dir,
            '{}.yaml'.format(recording_name or method_name)
        )
        self.temp_recording_file = os.path.join(
            recording_dir,
            '{}.temp.yaml'.format(recording_name or method_name)
        )

        self.in_recording = self.is_live or not os.path.exists(self.recording_file)
        self.test_resources_count = 0
        self.original_env = os.environ.copy()

    def setUp(self):
        super(ReplayableTest, self).setUp()

        # set up cassette
        cm = self.vcr.use_cassette(self.temp_recording_file if self.in_recording else self.recording_file)
        self.cassette = cm.__enter__()
        self.addCleanup(cm.__exit__)
        if self.in_recording:
            self.addCleanup(self._save_recording_file)

        # set up mock patches
        if self.in_recording:
            for patch in self.recording_patches:
                patch(self)
        else:
            for patch in self.replay_patches:
                patch(self)

    def tearDown(self):
        os.environ = self.original_env
        # Autorest.Python 2.x
        assert not [t for t in threading.enumerate() if t.name.startswith("AzureOperationPoller")], \
            "You need to call 'result' or 'wait' on all AzureOperationPoller you have created"
        # Autorest.Python 3.x
        assert not [t for t in threading.enumerate() if t.name.startswith("LROPoller")], \
            "You need to call 'result' or 'wait' on all LROPoller you have created"

    def _save_recording_file(self, *args):  # pylint: disable=unused-argument
        if self.in_recording and self.cassette.dirty:
            self.cassette._save()  # pylint: disable=protected-access

            # Since Python 3.11, unittest.case._Outcome no longer has 'errors' attribute.
            # The below statements only work in Python <= 3.10.
            # https://github.com/Azure/azure-cli/issues/27641
            if hasattr(self._outcome, 'errors') and (self._outcome.errors or self._outcome.skipped):   # pylint: disable=protected-access
                # remove temp file
                # to keep the temp_recording_file for debug, a switch logic can add here
                os.remove(self.temp_recording_file)
                return

            # replace recording_file by temp_recording_file
            if os.path.exists(self.recording_file):
                os.remove(self.recording_file)
            os.rename(self.temp_recording_file, self.recording_file)

    def _process_request_recording(self, request):
        if self.disable_recording:
            return None

        if self.in_recording:
            for processor in self.recording_processors + self.recording_post_processors:
                request = processor.process_request(request)
                if not request:
                    break
        else:
            for processor in self.replay_processors:
                request = processor.process_request(request)
                if not request:
                    break

        return request

    def _process_response_recording(self, response):
        from .utilities import is_text_payload
        if self.in_recording:
            # make header name lower case and filter unwanted headers
            headers = {}
            for key in response['headers']:
                if key.lower() not in self.FILTER_HEADERS:
                    headers[key.lower()] = response['headers'][key]
            response['headers'] = headers

            body = response['body']['string']
            if is_text_payload(response) and body and not isinstance(body, str):
                response['body']['string'] = body.decode('utf-8')

            for processor in self.recording_processors + self.recording_post_processors:
                response = processor.process_response(response)
                if not response:
                    break
        else:
            for processor in self.replay_processors:
                response = processor.process_response(response)
                if not response:
                    break

        return response

    @classmethod
    def _custom_request_query_matcher(cls, r1, r2):
        """ Ensure method, path, and query parameters match. """
        from urllib.parse import urlparse, parse_qs

        url1 = urlparse(r1.uri)
        url2 = urlparse(r2.uri)

        q1 = parse_qs(url1.query)
        q2 = parse_qs(url2.query)
        shared_keys = set(q1.keys()).intersection(set(q2.keys()))

        if len(shared_keys) != len(q1) or len(shared_keys) != len(q2):
            return False

        for key in shared_keys:
            if q1[key][0].lower() != q2[key][0].lower():
                return False

        return True
