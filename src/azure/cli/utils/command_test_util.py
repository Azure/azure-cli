from __future__ import print_function

import collections
import json
import logging
import os
import re
import sys
try:
    import unittest.mock as mock
except ImportError:
    import mock
import zlib

from six import StringIO
from six.moves import input #pylint: disable=redefined-builtin
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

    def __init__(self, recording_dir, test_def, env_var):
        self.test_def = test_def
        self.recording_dir = recording_dir
        logging.getLogger('vcr').setLevel(logging.ERROR)
        self.my_vcr = vcr.VCR(
            cassette_library_dir=recording_dir,
            before_record_request=CommandTestGenerator.before_record_request,
            before_record_response=CommandTestGenerator.before_record_response
        )
        # use default environment variables if not currently set in the system
        env_var = env_var or {}
        for var in env_var.keys():
            if not os.environ.get(var):
                os.environ[var] = str(env_var[var])

    def generate_tests(self):

        def gen_test(test_name, action, recording_dir):

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

            def _get_expected_results_from_file(recording_dir):
                expected_results_path = os.path.join(recording_dir, 'expected_results.res')
                try:
                    with open(expected_results_path, 'r') as f:
                        expected_results = json.loads(f.read())
                except EnvironmentError:
                    expected_results = {}
                return expected_results

            def _remove_expected_result(test_name, recording_dir):
                expected_results = _get_expected_results_from_file(recording_dir)
                expected_results.pop(test_name, None)
                _save_expected_results_file(recording_dir, expected_results)

            def _save_expected_results_file(recording_dir, expected_results):
                expected_results_path = os.path.join(recording_dir, 'expected_results.res')
                with open(expected_results_path, 'w') as f:
                    json.dump(expected_results, f, indent=4, sort_keys=True)

            def _test_impl(self, test_name, expected, recording_dir):
                """ Test implementation, augmented with prompted recording of expected result
                if not provided. """
                io = StringIO()
                if expected is None:
                    print('\n === RECORDING: {} ==='.format(test_name), file=sys.stderr)
                if isinstance(action, str):
                    cli(action.split(), file=io)
                    actual_result = io.getvalue()
                    display_result = actual_result
                    auto_validated = False
                    fail = False
                else:
                    test_runner = action
                    test_runner.run_test()
                    actual_result = test_runner.raw_result
                    display_result = test_runner.display_result
                    auto_validated = test_runner.auto
                    fail = test_runner.fail
                if expected is None:
                    expected_results = _get_expected_results_from_file(recording_dir)
                    header = '| RECORDED RESULT FOR {} |'.format(test_name)
                    print('\n' + ('-' * len(header)), file=sys.stderr)
                    print(header, file=sys.stderr)
                    print('-' * len(header) + '\n', file=sys.stderr)
                    print(display_result, file=sys.stderr)
                    if not auto_validated and not fail:
                        ans = input('Save result for \'{}\'? [y/N]: '.format(test_name))
                        fail = False if ans and ans.lower()[0] == 'y' else True

                    if not fail:
                        print('*** SAVING TEST {} ***'.format(test_name), file=sys.stderr)
                        expected_results = _get_expected_results_from_file(recording_dir)
                        expected_results[test_name] = actual_result
                        expected = actual_result
                        _save_expected_results_file(recording_dir, expected_results)
                    else:
                        print('*** TEST {} FAILED ***'.format(test_name), file=sys.stderr)
                        _remove_expected_result(test_name, recording_dir)

                io.close()
                self.assertEqual(actual_result, expected)

            expected_results = _get_expected_results_from_file(recording_dir)
            expected = expected_results.get(test_name, None)

            # if no yaml, any expected result is invalid and must be rerecorded
            cassette_path = os.path.join(self.recording_dir, '{}.yaml'.format(test_name))
            cassette_found = os.path.isfile(cassette_path)
            if not cassette_found:
                _remove_expected_result(test_name, recording_dir)
                expected = None

            # if no expected result, yaml file should be discarded and rerecorded
            if cassette_found and expected is None:
                os.remove(cassette_path)
                cassette_found = os.path.isfile(cassette_path)

            if cassette_found and expected is not None:
                # playback mode - can be fully automated
                @mock.patch('azure.cli._profile.Profile.load_cached_subscriptions',
                            load_subscriptions_mock)
                @mock.patch('azure.cli._profile.CredsCache.retrieve_token_for_user',
                            get_user_access_token_mock)
                @self.my_vcr.use_cassette(cassette_path,
                                          filter_headers=CommandTestGenerator.FILTER_HEADERS)
                def test(self):
                    _test_impl(self, test_name, expected, recording_dir)
                return test
            elif not cassette_found and expected is None:
                # recording needed
                # if buffer specified and recording needed, automatically fail
                if '--buffer' in sys.argv:
                    def null_test(self):
                        self.fail('No recorded result provided for {}.'.format(test_name))
                    return null_test

                @self.my_vcr.use_cassette(cassette_path,
                                          filter_headers=CommandTestGenerator.FILTER_HEADERS)
                def test(self):
                    _test_impl(self, test_name, expected, recording_dir)
            else:
                # yaml file failed to delete or bug exists
                raise RuntimeError('Unable to generate test for {} due to inconsistent data. ' \
                    + 'Please manually remove the associated .yaml cassette and/or the test\'s ' \
                    + 'entry in expected_results.res and try again.')
            return test

        test_functions = collections.OrderedDict()
        for test_def in self.test_def:
            test_name = 'test_{}'.format(test_def['test_name'])
            command = test_def.get('command')
            func = test_def.get('script')
            if command:
                test_functions[test_name] = gen_test(test_name, command, self.recording_dir)
            elif func:
                test_functions[test_name] = gen_test(test_name, func, self.recording_dir)
        return test_functions

    @staticmethod
    def before_record_request(request):
        request.uri = re.sub('/subscriptions/([^/]+)/',
                             '/subscriptions/00000000-0000-0000-0000-000000000000/', request.uri)
        return request

    @staticmethod
    def before_record_response(response):

        def _decode_body(response):
            encoding = response['headers'].get('Content-Encoding', [])
            if encoding and encoding[0] == 'gzip':
                body = response['body']['string']
                new_body = zlib.decompress(body, zlib.MAX_WBITS | 16)
                response['body']['string'] = new_body
                response['headers']['content-length'] = [str(len(new_body))]

        def _mask_sensitive_keys(response):
            SENSITIVE = ['key1', 'key2']
            body = response['body'].get('string')
            if body:
                body_json = json.loads(body.decode('utf-8'))
                for key in body_json:
                    if key in SENSITIVE:
                        body_json[key] = '0' * len(body_json[key])
                        print('MASKED {}: {}'.format(key, body_json[key]))

        for key in CommandTestGenerator.FILTER_HEADERS:
            if key in response['headers']:
                del response['headers'][key]
        #_decode_body(response)
        #_mask_sensitive_keys(response)
        return response
