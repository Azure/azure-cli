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

from command_specs import TEST_DEF

logging.basicConfig()
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.ERROR)

VCR_CASSETTE_DIR = os.path.join(os.path.dirname(__file__), 'recordings')
EXPECTED_RESULTS_PATH = VCR_CASSETTE_DIR + '\\expected_results.res'

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

        def _record_expected_result(test_name, command):
            """ Runs the command and allows user to save the result as the expected result."""
            print('*** RECORDING RESULT FOR {}'.format(test_name))
            io = StringIO()
            cli(command.split(), file=io)
            actual_result = io.getvalue()
            print(actual_result)
            ans = input('Save result for command: \'{}\'? [Y/n]: '.format(command))
            if ans and ans.lower()[0] == 'n':
                result = None
            else:
                TEST_EXPECTED[test_name] = actual_result
                with open(EXPECTED_RESULTS_PATH, 'w') as file:
                    json.dump(TEST_EXPECTED, file, indent=4, sort_keys=True)
                result = actual_result
            io.close()
            return result

        def gen_test(test_name, command, expected_result):

            if not expected_result:
                def null_test(self):
                    self.fail('No expected result provided for {}.'.format(test_name))
                return null_test

            def load_subscriptions_mock(self):
                return [{"id": "00000000-0000-0000-0000-000000000000", "user": "example@example.com", "access_token": "access_token", "state": "Enabled", "name": "Example", "active": True}];

            def _test_impl(self):
                io = StringIO()
                cli(command.split(), file=io)
                actual_result = io.getvalue()
                io.close()
                self.assertEqual(actual_result, expected_result)

            cassette_path = '{}.yaml'.format(test_name)
            if os.path.isfile(cassette_path):
                # if cassette present, apply subscription patch
                @mock.patch('azure.cli._profile.Profile.load_subscriptions', load_subscriptions_mock)
                @my_vcr.use_cassette(cassette_path, filter_headers=FILTER_HEADERS)
                def test(self):
                    _test_impl(self)
                return test
            else:
                # do not patch subscription if you need to record the intial cassette
                @my_vcr.use_cassette(cassette_path, filter_headers=FILTER_HEADERS)
                def test(self):
                    _test_impl(self)
                return test
        
        try:
            with open(EXPECTED_RESULTS_PATH, 'r') as file:
                TEST_EXPECTED = json.loads(file.read())
        except FileNotFoundError:
            TEST_EXPECTED = {}

        for test_path, test_def in TEST_DEF:
            test_name = 'test_{}'.format(test_def['test_name'])
            command = test_def['command']
            try:
                expected_result = TEST_EXPECTED[test_path]
            except KeyError:
                expected_result = _record_expected_result(test_path, command)

            dict[test_name] = gen_test(test_path, command, expected_result)
        return type.__new__(mcs, name, bases, dict)

@add_metaclass(TestSequenceMeta)
class TestCommands(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
