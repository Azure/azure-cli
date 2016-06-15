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
from azure.cli._util import CLIError

TRACK_COMMANDS = os.environ.get('AZURE_CLI_TEST_TRACK_COMMANDS')
COMMAND_COVERAGE_FILENAME = 'command_coverage.txt'

# MOCK METHODS

def _mock_generate_deployment_name(value):
    return value if value != '_GENERATE_' else 'mock-deployment'

def _mock_handle_exceptions(ex):
    raise ex

def _mock_subscriptions(self): #pylint: disable=unused-argument
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

def _mock_user_access_token(_, _1, _2): #pylint: disable=unused-argument
    return 'top-secret-token-for-you'

def _mock_operation_delay(_):
    # don't run time.sleep()
    return

# TEST CHECKS

class JMESPathCheckAssertionError(AssertionError):

    def __init__(self, comparator, actual_result, json_data):
        message = "Actual value '{}' != Expected value '{}'. ".format(
            actual_result,
            comparator.expected_result)
        message += "Query '{}' used on json data '{}'".format(comparator.query, json_data)
        super(JMESPathCheckAssertionError, self).__init__(message)

class JMESPathCheck(object): # pylint: disable=too-few-public-methods

    def __init__(self, query, expected_result):
        self.query = query
        self.expected_result = expected_result

    def compare(self, json_data):
        if not json_data:
            json_data = '{}'
        json_val = json.loads(json_data)
        actual_result = jmespath.search(
            self.query,
            json_val,
            jmespath.Options(collections.OrderedDict))
        if not actual_result == self.expected_result:
            raise JMESPathCheckAssertionError(self, actual_result, json_data)

class BooleanCheck(object): # pylint: disable=too-few-public-methods

    def __init__(self, expected_result):
        self.expected_result = expected_result

    def compare(self, data):
        result = str(str(data).lower() in ['yes', 'true', '1'])
        try:
            assert result == str(self.expected_result)
        except AssertionError:
            raise AssertionError("Actual value '{}' != Expected value {}".format(
                result, self.expected_result))

class NoneCheck(object): # pylint: disable=too-few-public-methods

    def __init__(self):
        pass

    def compare(self, data): # pylint: disable=no-self-use
        try:
            assert not data
        except AssertionError:
            raise AssertionError("Actual value '{}' != Expected value falsy (None, '', [])".format(
                data))

class StringCheck(object): # pylint: disable=too-few-public-methods

    def __init__(self, expected_result):
        self.expected_result = expected_result

    def compare(self, data):
        try:
            result = data.replace('"', '')
            assert result == self.expected_result
        except AssertionError:
            raise AssertionError("Actual value '{}' != Expected value {}".format(
                data, self.expected_result))

# HELPER METHODS

def _scrub_deployment_name(uri):
    return re.sub('/deployments/([^/?]+)', '/deployments/mock-deployment', uri)

# MAIN CLASS

class VCRTestBase(unittest.TestCase):#pylint: disable=too-many-instance-attributes

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

    def __init__(self, test_file, test_name, run_live=False, debug=False):
        super(VCRTestBase, self).__init__(test_name)
        self.test_name = test_name
        self.recording_dir = os.path.join(os.path.dirname(test_file), 'recordings')
        self.cassette_path = os.path.join(self.recording_dir, '{}.yaml'.format(test_name))
        self.playback = os.path.isfile(self.cassette_path)
        self.run_live = run_live
        self.success = False
        self.exception = None
        self.track_commands = False
        self._debug = debug

        if not self.playback and ('--buffer' in sys.argv) and not run_live:
            self.exception = CLIError('No recorded result provided for {}.'.format(self.test_name))

        self.my_vcr = vcr.VCR(
            cassette_library_dir=self.recording_dir,
            before_record_request=VCRTestBase._before_record_request,
            before_record_response=VCRTestBase._before_record_response,
        )

    def _track_executed_commands(self, command):
        if not self.track_commands:
            return
        filename = COMMAND_COVERAGE_FILENAME
        with open(filename, 'a+') as f:
            f.write(' '.join(command))
            f.write('\n')

    @staticmethod
    def _before_record_request(request):
        # scrub subscription from the uri
        request.uri = re.sub('/subscriptions/([^/]+)/',
                             '/subscriptions/00000000-0000-0000-0000-000000000000/', request.uri)
        request.uri = re.sub('/sig=([^/]+)&', '/sig=0000&', request.uri)
        request.uri = _scrub_deployment_name(request.uri)
        # prevents URI mismatch between Python 2 and 3 if request URI has extra / chars
        request.uri = re.sub('//', '/', request.uri)
        request.uri = re.sub('/', '//', request.uri, count=1)
        # do not record requests sent for token refresh'
        if (request.body and 'grant-type=refresh_token' in str(request.body)) or \
            '/oauth2/token' in request.uri:
            request = None
        return request

    @staticmethod
    def _before_record_response(response):
        for key in VCRTestBase.FILTER_HEADERS:
            if key in response['headers']:
                del response['headers'][key]
        return response

    @mock.patch('azure.cli.main._handle_exception', _mock_handle_exceptions)
    def _execute_live_or_recording(self):
        #pylint: disable=no-member
        try:
            set_up = getattr(self, "set_up", None)
            if callable(set_up):
                self.set_up()

            if self.run_live:
                self.body()
            else:
                with self.my_vcr.use_cassette(self.cassette_path):
                    self.body()
            self.success = True
        except Exception as ex:
            raise ex
        finally:
            tear_down = getattr(self, "tear_down", None)
            if callable(tear_down):
                self.tear_down()

    @mock.patch('azure.cli._profile.Profile.load_cached_subscriptions', _mock_subscriptions)
    @mock.patch('azure.cli._profile.CredsCache.retrieve_token_for_user', _mock_user_access_token)
    @mock.patch('azure.cli.main._handle_exception', _mock_handle_exceptions)
    @mock.patch('msrestazure.azure_operation.AzureOperationPoller._delay', _mock_operation_delay)
    @mock.patch('time.sleep', _mock_operation_delay)
    @mock.patch('azure.cli.commands.LongRunningOperation._delay', _mock_operation_delay)
    @mock.patch('azure.cli.commands.parameters.generate_deployment_name',
                _mock_generate_deployment_name)
    def _execute_playback(self):
        # pylint: disable=no-member
        with self.my_vcr.use_cassette(self.cassette_path):
            self.body()
        self.success = True

    # COMMAND METHODS

    def cmd(self, command, checks=None, allowed_exceptions=None, debug=False): #pylint: disable=no-self-use
        allowed_exceptions = allowed_exceptions or []
        if self._debug or debug:
            print('\n\tRUNNING: {}'.format(command))
        command_list = shlex.split(command)
        output = StringIO()
        try:
            cli(command_list, file=output)
        except Exception as ex: # pylint: disable=broad-except
            if not isinstance(allowed_exceptions, list):
                allowed_exceptions = [allowed_exceptions]
            if str(ex) not in allowed_exceptions:
                raise ex
        self._track_executed_commands(command_list)
        result = output.getvalue().strip()
        output.close()

        if self._debug or debug:
            print('\tRESULT: {}\n'.format(result))

        if checks:
            checks = [checks] if not isinstance(checks, list) else checks
            for check in checks:
                check.compare(result)

        result = result or '{}'
        try:
            return json.loads(result)
        except Exception: # pylint: disable=broad-except
            return result

    def set_env(self, key, val): #pylint: disable=no-self-use
        os.environ[key] = val

    def pop_env(self, key): #pylint: disable=no-self-use
        return os.environ.pop(key, None)

    def execute(self):
        ''' Method to actually start execution of the test. Must be called from the test_<name>
        method of the test class. '''
        try:
            if self.run_live:
                print('RUN LIVE: {}'.format(self.test_name))
                self._execute_live_or_recording()
            elif self.playback:
                print('PLAYBACK: {}'.format(self.test_name))
                self._execute_playback()
            else:
                print('RECORDING: {}'.format(self.test_name))
                self._execute_live_or_recording()
        except Exception as ex:
            raise ex
        finally:
            if not self.success and not self.playback and os.path.isfile(self.cassette_path):
                print('DISCARDING RECORDING: {}'.format(self.cassette_path))
                os.remove(self.cassette_path)

class ResourceGroupVCRTestBase(VCRTestBase):
    def __init__(self, test_file, test_name, run_live=False, debug=False):
        super(ResourceGroupVCRTestBase, self).__init__(test_file, test_name,
                                                       run_live=run_live, debug=debug)
        self.resource_group = 'vcr_resource_group'
        self.location = 'westus'

    def set_up(self):
        self.cmd('resource group create --location {} --name {}'.format(
            self.location, self.resource_group))
        #self.cmd('resource group create --location {} --name {}'.format(
        #    self.location, self.resource_group),
        #    allowed_exceptions="resource group {} already exists".format(self.resource_group))

    def tear_down(self):
        self.cmd('resource group delete --name {}'.format(self.resource_group))
        #pass
