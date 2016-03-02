import os
import sys
import unittest
import re
import vcr
import logging

from six import add_metaclass

try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO

from azure.cli.main import main as cli

from command_specs import *

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.ERROR)

VCR_CASSETTE_DIR = os.path.join(os.path.dirname(__file__), 'recordings')

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

        def gen_test(test_name, args_string, expected_result):
            @my_vcr.use_cassette('%s.yaml'%test_name, filter_headers=FILTER_HEADERS)
            def test(self):
                with StringIO() as io:
                    cli(args_string.split(), file=io)
                    self.assertEqual(io.getvalue(), expected_result)
            return test

        def load_test_specs():
            test_specs = []
            test_spec_modules = [(key, sys.modules[key]) for key in sys.modules if key.startswith('command_specs.test_spec')]
            for mname, m in test_spec_modules:
                test_specs.append((mname, m.SPEC))
            return test_specs

        for module_name, test_specs in load_test_specs():
            for tname, cmd_args, expected_result in test_specs:
                test_name = "test_%s" % tname
                full_test_name = "%s.%s"%(module_name, test_name)
                dict[test_name] = gen_test(full_test_name, cmd_args, expected_result)
        return type.__new__(mcs, name, bases, dict)

@add_metaclass(TestSequenceMeta)
class TestCommands(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
