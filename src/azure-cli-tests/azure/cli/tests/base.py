# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import unittest
import os.path
import inspect
import vcr
import subprocess
import json
import shlex

from azure.cli.tests.patches import (patch_load_cached_subscriptions, patch_main_exception_handler,
                                     patch_retrieve_token_for_user)
from azure.cli.tests.exceptions import CliExecutionError
from azure.cli.tests.const import (ENV_LIVE_TEST, ENV_SKIP_ASSERT, ENV_TEST_DIAGNOSE,
                                   MOCKED_SUBSCRIPTION_ID)
from azure.cli.tests.recording_processors import (SubscriptionRecordingProcessor,
                                                  OAuthRequestResponsesFilter,
                                                  GeneralNameReplacer)
from azure.cli.tests.utilities import create_random_name


class ScenarioTest(unittest.TestCase):
    def __init__(self, method_name):
        super(ScenarioTest, self).__init__(method_name)
        self.name_replacer = GeneralNameReplacer()
        self.recording_processors = [SubscriptionRecordingProcessor(MOCKED_SUBSCRIPTION_ID),
                                     OAuthRequestResponsesFilter(),
                                     self.name_replacer]

        test_file_path = inspect.getfile(self.__class__)
        recordings_dir = os.path.join(os.path.dirname(test_file_path), 'recordings')
        live_test = os.environ.get(ENV_LIVE_TEST, None) == 'True'

        self.vcr = vcr.VCR(
            cassette_library_dir=recordings_dir,
            before_record_request=self._process_request_recording,
            before_record_response=self._process_response_recording,
            decode_compressed_response=True,
            record_mode='once' if not live_test else 'all',
            filter_headers=['authorization'],
        )

        self.recording_file = os.path.join(recordings_dir, '{}.yaml'.format(method_name))
        if live_test and os.path.exists(self.recording_file):
            os.remove(self.recording_file)

        self.diagnose = os.environ.get(ENV_TEST_DIAGNOSE, None) == 'True'
        self.skip_assert = os.environ.get(ENV_SKIP_ASSERT, None) == 'True'
        self.in_recording = live_test or not os.path.exists(self.recording_file)
        self.test_resources_count = 0

    def setUp(self):
        super(ScenarioTest, self).setUp()

        # set up cassette
        cm = self.vcr.use_cassette(self.recording_file)
        self.cassette = cm.__enter__()
        self.addCleanup(cm.__exit__)

        # set up mock patches
        patch_main_exception_handler(self)
        if not self.in_recording:
            patch_load_cached_subscriptions(self)
            patch_retrieve_token_for_user(self)

    def create_random_name(self, prefix, length):
        self.test_resources_count += 1
        moniker = '{}{:06}'.format(prefix, self.test_resources_count)

        if self.in_recording:
            name = create_random_name(prefix, length)
            self.name_replacer.register_name_pair(name, moniker)
            return name
        else:
            return moniker

    def cmd(self, command, checks=None):
        if self.diagnose:
            begin = datetime.datetime.now()
            print('\nExecuting command: {}'.format(command))

        result = execute(command)

        if self.diagnose:
            duration = datetime.datetime.now() - begin
            print('\nCommand accomplished in {} s. Exit code {}.\n{}'.format(
                duration.total_seconds(), result.exit_code, result.output))

        if not checks:
            checks = []
        elif not isinstance(checks, list):
            checks = [checks]

        if not self.skip_assert:
            for c in checks:
                c(result)

        return result

    def _process_request_recording(self, request):
        for processor in self.recording_processors:
            request = processor.process_request(request)
            if not request:
                break

        return request

    def _process_response_recording(self, response):
        for processor in self.recording_processors:
            response = processor.process_response(response)
            if not response:
                break

        return response


class ExecutionResult(object):
    def __init__(self, command, expect_failure=False, in_process=True):
        if in_process:
            self._in_process_execute(command)
        else:
            self._out_of_process_execute(command)

        if expect_failure and self.exit_code == 0:
            raise AssertionError('The command is expected to fail but it doesn\'.')
        elif not expect_failure and self.exit_code != 0:
            raise AssertionError('The command failed. Exit code: {}'.format(self.exit_code))

        self.json_value = None

    def get_output_in_json(self):
        if not self.json_value:
            self.json_value = json.loads(self.output)

        if not self.json_value:
            raise AssertionError('The command output cannot be parsed in json.')

        return self.json_value

    def _in_process_execute(self, command):
        # from azure.cli import  as cli_main
        from azure.cli.main import main as cli_main
        from six import StringIO
        from vcr.errors import CannotOverwriteExistingCassetteException

        if command.startswith('az '):
            command = command[3:]

        output_buffer = StringIO()
        try:
            # issue: stderr cannot be redirect in this form, as a result some failure information
            # is lost when command fails.
            self.exit_code = cli_main(shlex.split(command), file=output_buffer) or 0
            self.output = output_buffer.getvalue()
        except CannotOverwriteExistingCassetteException as ex:
            raise AssertionError(ex)
        except CliExecutionError as ex:
            raise AssertionError(ex)
        except Exception as ex:  # pylint: disable=broad-except
            self.exit_code = 1
            self.output = output_buffer.getvalue()
            self.process_error = ex
        finally:
            output_buffer.close()

    def _out_of_process_execute(self, command):
        try:
            self.output = subprocess.check_output(shlex.split(command)).decode('utf-8')
            self.exit_code = 0
        except subprocess.CalledProcessError as error:
            self.exit_code, self.output = error.returncode, error.output.decode('utf-8')
            self.process_error = error


execute = ExecutionResult
