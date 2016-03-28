import os
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

    def __init__(self, vcr_cassette_dir, test_specs):
        self.test_specs = test_specs
        logging.basicConfig()
        logging.getLogger('vcr').setLevel(logging.ERROR)
        self.my_vcr = vcr.VCR(
            cassette_library_dir=vcr_cassette_dir,
            before_record_request=CommandTestGenerator.before_record_request,
            before_record_response=CommandTestGenerator.before_record_response
        )

    def generate_tests(self):
        test_functions = {}
        def gen_test(test_name, command, expected_result):

            def load_subscriptions_mock(self):
                return [{"id": "00000000-0000-0000-0000-000000000000", "user": "example@example.com", "access_token": "access_token", "state": "Enabled", "name": "Example", "active": True}]

            @mock.patch('azure.cli._profile.Profile.load_subscriptions', load_subscriptions_mock)
            @self.my_vcr.use_cassette('%s.yaml'%test_name, filter_headers=CommandTestGenerator.FILTER_HEADERS)
            def test(self):
                io = StringIO()
                cli(command.split(), file=io)
                actual_result = io.getvalue()
                io.close()
                self.assertEqual(actual_result, expected_result)
            return test

        for test_spec_item in self.test_specs:
            test_name = 'test_%s' % test_spec_item['test_name']
            test_functions[test_name] = gen_test(test_name, test_spec_item['command'], test_spec_item['expected_result'])
        return test_functions

    @staticmethod
    def before_record_request(request):
        request.uri = re.sub('/subscriptions/([^/]+)/', '/subscriptions/00000000-0000-0000-0000-000000000000/', request.uri)
        return request

    @staticmethod
    def before_record_response(response):
        def remove_entries(the_dict, entries):
            for key in entries:
                if key in the_dict:
                    del the_dict[key]
        remove_entries(response['headers'], CommandTestGenerator.FILTER_HEADERS)
        return response
