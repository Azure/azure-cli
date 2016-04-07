from __future__ import print_function

import json
import logging
import os
import re
import sys
try:
    import unittest.mock as mock
except ImportError:
    import mock

from six import StringIO
import vcr

from azure.cli.main import main as cli

class CommandTestGenerator(object):

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

    def __init__(self, vcr_cassette_dir, test_def, env_var=None):
        self.test_def = test_def
        self.expected_results_path = os.path.join(vcr_cassette_dir, 'expected_results.res')
        self.vcr_cassette_dir = vcr_cassette_dir
        logging.basicConfig()
        logging.getLogger('vcr').setLevel(logging.ERROR)
        self.my_vcr = vcr.VCR(
            cassette_library_dir=vcr_cassette_dir,
            before_record_request=CommandTestGenerator.before_record_request,
            before_record_response=CommandTestGenerator.before_record_response
        )
        # use default environment variables if not currently set in the system
        env_var = env_var or {}
        for var in env_var.keys():
            if not os.environ.get(var, None):
                os.environ[var] = str(env_var[var])

    def generate_tests(self):

        test_functions = {}

        def gen_test(test_path, command):

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

            def _test_impl(self, expected_result):
                """ Test implementation, augmented with prompted recording of expected result
                if not provided. """
                io = StringIO()

                cli(command.split(), file=io)
                actual_result = io.getvalue()
                if expected_result is None:
                    header = '| RECORDED RESULT FOR {} |'.format(test_path)
                    print('-' * len(header), file=sys.stderr)
                    print(header, file=sys.stderr)
                    print('-' * len(header) + '\n', file=sys.stderr)
                    print(actual_result, file=sys.stderr)
                    ans = input('Save result for command: \'{}\'? [Y/n]: '.format(command))
                    if ans and ans.lower()[0] == 'y':
                        # update and save the expected_results.res file
                        TEST_EXPECTED[test_path] = actual_result
                        with open(self.expected_results_path, 'w') as file:
                            json.dump(TEST_EXPECTED, file, indent=4, sort_keys=True)
                        expected_result = actual_result
                    else:
                        # recorded result was wrong. Discard the result and the .yaml cassette
                        expected_result = None
                io.close()
                self.assertEqual(actual_result, expected_result)

            expected_result = self.expected_results.get(test_path, None)

            # if no yaml, any expected result is invalid and must be rerecorded
            cassette_path = os.path.join(self.vcr_cassette_dir, '{}.yaml'.format(test_path))
            cassette_found = os.path.isfile(cassette_path)
            expected_result = None if not cassette_found else expected_result

            # if no expected result, yaml file should be discarded and rerecorded
            if cassette_found and expected_result is None:
                os.remove(cassette_path)
                cassette_found = os.path.isfile(cassette_path)

            if cassette_found and expected_result is not None:
                # playback mode - can be fully automated
                @mock.patch('azure.cli._profile.Profile.load_cached_subscriptions',
                            load_subscriptions_mock)
                @mock.patch('azure.cli._profile.CredsCache.retrieve_token_for_user',
                            get_user_access_token_mock)
                @self.my_vcr.use_cassette(cassette_path,
                                          filter_headers=CommandTestGenerator.FILTER_HEADERS)
                def test(self):
                    _test_impl(self, expected_result)
                return test
            elif not cassette_found and expected_result is None:
                # recording needed
                # if buffer specified and recording needed, automatically fail
                is_buffered = list(set(['--buffer']) & set(sys.argv))
                if is_buffered:
                    def null_test(self):
                        self.fail('No recorded result provided for {}.'.format(test_path))
                    return null_test

                @self.my_vcr.use_cassette(cassette_path,
                                          filter_headers=CommandTestGenerator.FILTER_HEADERS)
                def test(self):
                    _test_impl(self, expected_result)
            else:
                # yaml file failed to delete or bug exists
                raise RuntimeError('Unable to generate test for {} due to inconsistent data. ' \
                    + 'Please manually remove the associated .yaml cassette and/or the test\'s ' \
                    + 'entry in expected_results.res and try again.')
            return test

        try:
            with open(self.expected_results_path, 'r') as file:
                self.expected_results = json.loads(file.read())
        except EnvironmentError:
            self.expected_results = {}
        
        print('EXPECTED RESULTS: {}'.format(self.expected_results))
        for test_path, test_def in self.test_def:
            test_name = 'test_{}'.format(test_def['test_name'])
            command = test_def['command']
            test_functions[test_name] = gen_test(test_path, command)
        return test_functions

    @staticmethod
    def before_record_request(request):
        request.uri = re.sub('/subscriptions/([^/]+)/',
                             '/subscriptions/00000000-0000-0000-0000-000000000000/', request.uri)
        return request

    @staticmethod
    def before_record_response(response):
        for key in CommandTestGenerator.FILTER_HEADERS:
            if key in response['headers']:
                del response['headers'][key]
        return response
