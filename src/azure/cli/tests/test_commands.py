from __future__ import print_function

import os
import json
import sys
import unittest
import re
import vcr
import logging

from six import add_metaclass, StringIO
try:
    import unittest.mock as mock
except ImportError:
    import mock

from azure.cli.main import main as cli

from command_specs import TEST_DEF, ENV_VARIABLES

logging.basicConfig()
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.ERROR)

VCR_CASSETTE_DIR = os.path.join(os.path.dirname(__file__), 'recordings')
EXPECTED_RESULTS_PATH = os.path.join(VCR_CASSETTE_DIR, 'expected_results.res')

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

def before_record_request(request):
    request.uri = re.sub('/subscriptions/([^/]+)/', '/subscriptions/00000000-0000-0000-0000-000000000000/', request.uri)
    return request

def before_record_response(response):
    def remove_entries(the_dict, entries):
        for key in entries:
            if key in the_dict:
                del the_dict[key]
    remove_entries(response['headers'], FILTER_HEADERS)
    return response

my_vcr = vcr.VCR(
    cassette_library_dir=VCR_CASSETTE_DIR,
    before_record_request=before_record_request,
    before_record_response=before_record_response
)

class TestSequenceMeta(type):

    def __new__(mcs, name, bases, dict):
    
        def gen_test(test_name, command, expected_result):
        
            def load_subscriptions_mock(self):
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

            def get_user_access_token_mock(_, _1, _2):
                return 'top-secret-token-for-you'

            def _test_impl(self, expected_result):
                """ Test implementation, augmented with prompted recording of expected result
                if not provided. """
                io = StringIO()

                cli(command.split(), file=io)
                actual_result = io.getvalue()
                if expected_result == None:
                    header = '| RECORDED RESULT FOR {} |'.format(test_name) 
                    print('-' * len(header), file=sys.stderr)
                    print(header, file=sys.stderr)
                    print('-' * len(header) + '\n', file=sys.stderr)
                    print(actual_result, file=sys.stderr)
                    ans = input('Save result for command: \'{}\'? [Y/n]: '.format(command))
                    result = None
                    if ans and ans.lower()[0] == 'y':
                        # update and save the expected_results.res file
                        TEST_EXPECTED[test_name] = actual_result
                        with open(EXPECTED_RESULTS_PATH, 'w') as file:
                            json.dump(TEST_EXPECTED, file, indent=4, sort_keys=True)
                        expected_result = actual_result
                    else:
                        # recorded result was wrong. Discard the result and the .yaml cassette
                        expected_result = None
                io.close()
                self.assertEqual(actual_result, expected_result)

            cassette_path = os.path.join(VCR_CASSETTE_DIR, '{}.yaml'.format(test_name))
            cassette_found = os.path.isfile(cassette_path)

            # if no yaml, any expected result is invalid and must be rerecorded
            expected_result = None if not cassette_found else expected_result
            
            # if no expected result, yaml file should be discarded and rerecorded
            if cassette_found and expected_result == None:
                os.remove(cassette_path)
                cassette_found = os.path.isfile(cassette_path)

            if cassette_found and expected_result != None:
                # playback mode - can be fully automated
                @mock.patch('azure.cli._profile.Profile.load_cached_subscriptions', load_subscriptions_mock)
                @mock.patch('azure.cli._profile.CredsCache.retrieve_token_for_user',get_user_access_token_mock)
                @my_vcr.use_cassette(cassette_path, filter_headers=FILTER_HEADERS)
                def test(self):
                    _test_impl(self, expected_result)
                return test
            elif not cassette_found and expected_result == None:
                # recording needed
                # if buffer specified and recording needed, automatically fail
                is_buffered = list(set(['--buffer']) & set(sys.argv))
                if is_buffered:
                    def null_test(self):
                        self.fail('No recorded result provided for {}.'.format(test_name))
                    return null_test                

                @my_vcr.use_cassette(cassette_path, filter_headers=FILTER_HEADERS)
                def test(self):
                    _test_impl(self, expected_result)
            else:
                # yaml file failed to delete or bug exists
                raise RuntimeError('Unable to generate test for {} due to inconsistent data. ' \
                    + 'Please manually remove the associated .yaml cassette and/or the test\'s ' \
                    + 'entry in expected_results.res and try again.')
            return test

        try:
            with open(EXPECTED_RESULTS_PATH, 'r') as file:
                TEST_EXPECTED = json.loads(file.read())
        except EnvironmentError:
            TEST_EXPECTED = {}

        for test_path, test_def in TEST_DEF:
            test_name = 'test_{}'.format(test_def['test_name'])
            command = test_def['command']
            expected_result = TEST_EXPECTED.get(test_path, None)
            
            dict[test_name] = gen_test(test_path, command, expected_result)
        return type.__new__(mcs, name, bases, dict)

@add_metaclass(TestSequenceMeta)
class TestCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # use default environment variables if not currently set in the system
        vars = ENV_VARIABLES.keys() if ENV_VARIABLES else []
        for var in vars:
            if not os.environ.get(var, None):
                os.environ[var] = str(ENV_VARIABLES[var])

    @classmethod
    def tearDownClass(cls):
        pass

if __name__ == '__main__':
    unittest.main()
