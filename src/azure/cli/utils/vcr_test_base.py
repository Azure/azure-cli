from __future__ import print_function

import json
import os
import collections
import shlex
import re
import sys

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

import vcr
import jmespath
from six import StringIO

from azure.cli.main import main as cli
from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError

TRACK_COMMANDS = os.environ.get('AZURE_CLI_TEST_TRACK_COMMANDS')
COMMAND_COVERAGE_FILENAME = 'command_coverage.txt'

class JMESPathComparatorAssertionError(AssertionError):

    def __init__(self, comparator, actual_result, json_data):
        message = "Actual value '{}' != Expected value '{}'. ".format(
            actual_result,
            comparator.expected_result)
        message += "Query '{}' used on json data '{}'".format(comparator.query, json_data)
        super(JMESPathComparatorAssertionError, self).__init__(message)

class JMESPathComparator(object): #pylint: disable=too-few-public-methods

    def __init__(self, query, expected_result):
        self.query = query
        self.expected_result = expected_result

    def compare(self, json_data):
        json_val = json.loads(json_data)
        actual_result = jmespath.search(
            self.query,
            json_val,
            jmespath.Options(collections.OrderedDict))
        if not actual_result == self.expected_result:
            raise JMESPathComparatorAssertionError(self, actual_result, json_data)

def _check_json(source, checks):

    def _check_json_child(item, checks):
        if not item:
            return not checks
        for check in checks.keys():
            if isinstance(checks[check], dict) and check in item:
                return _check_json_child(item[check], checks[check])
            else:
                return item[check] == checks[check]

    if not isinstance(source, list):
        source = [source]
    passed = False
    for item in source:
        passed = _check_json_child(item, checks)
        if passed:
            break
    return passed

def load_subscriptions_mock(self): #pylint: disable=unused-argument
    return [{
        "id": "00000000-0000-0000-0000-000000000000",
        "user": {
            "name": "example@example.com",
            "type": "user"
            },
        "state": "Enabled",
        "name": "Example",
        "tenantId": "123",
        "isDefault": True}]

def get_user_access_token_mock(_, _1, _2): #pylint: disable=unused-argument
    return 'top-secret-token-for-you'

def operation_delay_mock(_):
    # don't run time.sleep()
    return

class VCRTestBase(unittest.TestCase):#pylint: disable=too-many-instance-attributes

    def __init__(self, test_file, test_name, debug=False):
        super(VCRTestBase, self).__init__(test_name)
        self.test_name = test_name
        self.recording_dir = os.path.join(os.path.dirname(test_file), 'recordings')
        self.cassette_path = os.path.join(self.recording_dir, '{}.yaml'.format(test_name))
        self.my_vcr = vcr.VCR(
            cassette_library_dir=self.recording_dir,
            before_record_request=VCRTestBase.before_record_request,
            before_record_response=VCRTestBase.before_record_response,
        )
        expected_results = self._get_expected_results_from_file()
        self.expected = expected_results.get(self.test_name, None)

        self.playback = True
        # if no yaml, any expected result is invalid and must be rerecorded
        cassette_found = os.path.isfile(self.cassette_path)
        if not cassette_found:
            self._remove_expected_result()
            self.expected = None
            self.playback = False

        # if no expected result, yaml file should be discarded and rerecorded
        if cassette_found and self.expected is None:
            os.remove(self.cassette_path)
            cassette_found = False
            self.playback = False

        if not self.playback and ('--buffer' in sys.argv):
            raise CLIError('No recorded result provided for {}.'.format(self.test_name))

        self._display = StringIO()
        self._raw = StringIO()
        self.debug = debug
        self.auto = True
        self.track_commands = False

    def _track_executed_commands(self, command):
        if not self.track_commands:
            return
        filename = COMMAND_COVERAGE_FILENAME
        with open(filename, 'a+') as f:
            f.write(' '.join(command))
            f.write('\n')

    def run_command_no_verify(self, command, debug=False): #pylint: disable=no-self-use
        ''' Run a command without recording the output as part of expected results. Useful if you
        need to run a command for branching logic or just to reset back to a known condition. '''
        if self.debug or debug:
            print('\n\tRUNNING: {}'.format(command))
        command_list = shlex.split(command)
        result = self._core_vcr_test(command_list, record_output=False)
        self._track_executed_commands(command_list)
        if self.debug or debug:
            print('\tRESULT: {}\n'.format(result))
        # if json output was specified, return result as json object
        if isinstance(command, str) and '-o json' in command:
            result = json.loads(result) if result else []
        return result

    def run_command_and_verify(self, command, checks, debug=False):
        ''' Runs a command with the json output format and validates the input against the provided
        checks. Multiple JSON properties can be submitted as a dictionary and are treated as an AND
        condition. '''

        if self.debug or debug:
            print('\n\tTESTING: {}'.format(command))
        command_list = shlex.split(command)
        command_list += ['-o', 'json']

        result = self._core_vcr_test(command_list, record_output=True)
        if self.debug or debug:
            print('\tRESULT: {}\n'.format(result))
        try:
            if result is None or result == '':
                assert checks is None or checks is False
            elif isinstance(checks, list):
                if all(isinstance(comparator, JMESPathComparator) for comparator in checks):
                    for comparator in checks:
                        comparator.compare(result)
                else:
                    result_set = set(json.loads(result))
                    assert result_set == set(checks)
            elif isinstance(checks, JMESPathComparator):
                checks.compare(result)
            elif isinstance(checks, bool):
                result_val = str(result).lower().replace('"', '')
                result = result_val in ('yes', 'true', 't', '1')
                assert result == checks
            elif isinstance(checks, str):
                assert result.replace('"', '') == checks
            elif isinstance(checks, dict):
                json_val = json.loads(result)
                assert _check_json(json_val, checks)
            else:
                raise IncorrectUsageError(
                    'unsupported type \'{}\' in test'.format(type(checks)))
        except AssertionError:
            if self.debug:
                print('\tFAILED: {}'.format(checks))
            raise CLIError('COMMAND {} FAILED.\nResult: {}\nChecks: {}'.format(
                command, result, checks))

    def set_env(self, key, val): #pylint: disable=no-self-use
        os.environ[key] = val

    def pop_env(self, key): #pylint: disable=no-self-use
        return os.environ.pop(key, None)

    def display(self, string):
        ''' Write free text to the display output only. This text will not be included in the
        raw saved output and using this command does not flag a test as requiring manual
        verification. '''
        self._display.write('\n{}'.format(string))

    def _core_vcr_test(self, command_list, record_output):
        output = StringIO()
        cli(command_list, file=output)

        self._track_executed_commands(command_list)
        result = output.getvalue().strip()
        if self.debug:
            print('\tRESULT: {}\n'.format(result))
        if record_output:
            self._raw.write(result)
        output.close()
        return result

    def verify_test_output(self):
        raw_result = self._raw.getvalue()
        self.assertEqual(raw_result, self.expected)

    def execute(self, verify_test_output):
        if self.playback:
            self._execute_playback()
        else:
            self._execute_recording()

        if verify_test_output and self.playback:
            raw_result = self._raw.getvalue()
            self.assertEqual(raw_result, self.expected)
        self._raw.close()

    def _execute_recording(self):
        #pylint: disable=no-member
        set_up = getattr(self, "set_up", None)
        if callable(set_up):
            if self.debug:
                print('\n==ENTERING TEST SET UP==')
            self.set_up()

        with self.my_vcr.use_cassette(self.cassette_path):
            if self.debug:
                print('\n==ENTERING TEST BODY==')
            self.body()

        tear_down = getattr(self, "tear_down", None)
        if callable(tear_down):
            if self.debug:
                print('\n==ENTERING TEST TEAR DOWN==')
            self.tear_down()

        expected_results = self._get_expected_results_from_file()
        expected_results[self.test_name] = self._raw.getvalue()
        self._save_expected_results_file(expected_results)

    @mock.patch('azure.cli._profile.Profile.load_cached_subscriptions', load_subscriptions_mock)
    @mock.patch('azure.cli._profile.CredsCache.retrieve_token_for_user', get_user_access_token_mock)
    @mock.patch('msrestazure.azure_operation.AzureOperationPoller._delay', operation_delay_mock)
    @mock.patch('time.sleep', operation_delay_mock)
    @mock.patch('azure.cli.commands.LongRunningOperation._delay', operation_delay_mock)
    def _execute_playback(self):
        #pylint: disable=no-member
        with self.my_vcr.use_cassette(self.cassette_path):
            self.body()

    @staticmethod
    def before_record_request(request):
        request.uri = re.sub('/subscriptions/([^/]+)/',
                             '/subscriptions/00000000-0000-0000-0000-000000000000/', request.uri)
        # prevents URI mismatch between Python 2 and 3 if request URI has extra / chars
        request.uri = re.sub('//', '/', request.uri)
        request.uri = re.sub('/', '//', request.uri, count=1)

        # do not record requests sent for token refresh'
        if (request.body and 'grant-type=refresh_token' in str(request.body)) or \
            '/oauth2/token' in request.uri:
            request = None

        return request

    @staticmethod
    def before_record_response(response):
        for key in VCRTestBase.FILTER_HEADERS:
            if key in response['headers']:
                del response['headers'][key]
        return response

    FILTER_HEADERS = [
        'authorization',
        'client-request-id',
        'x-ms-client-request-id',
        'x-ms-correlation-request-id',
        'x-ms-ratelimit-remaining-subscription-reads',
        'x-ms-request-id',
        'x-ms-routing-request-id',
        'x-ms-gateway-service-instanceid',
        'x-ms-ratelimit-remaining-tenant-reads',
        'x-ms-served-by',
    ]

    def _get_expected_results_from_file(self):
        expected_results_path = os.path.join(self.recording_dir, 'expected_results.res')
        try:
            with open(expected_results_path, 'r') as f:
                expected_results = json.loads(f.read())
        except EnvironmentError:
            expected_results = {}
        return expected_results

    def _remove_expected_result(self):
        expected_results = self._get_expected_results_from_file()
        expected_results.pop(self.test_name, None)
        self._save_expected_results_file(expected_results)

    def _save_expected_results_file(self, expected_results):
        expected_results_path = os.path.join(self.recording_dir, 'expected_results.res')
        with open(expected_results_path, 'w') as f:
            json.dump(expected_results, f, indent=4, sort_keys=True)

