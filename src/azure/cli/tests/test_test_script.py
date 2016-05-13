import json
import unittest
from six import StringIO

from azure.cli.utils.command_test_script import _check_json as check_json

class Test_test_script_checks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.io = StringIO()
        
    def tearDown(self):
        self.io.close()

    def test_json_string(self):
        ''' Verify a simple string value can be used to match a property on a source object. '''
        source = json.loads(json.dumps({'a': 'b', 'c': 'd'}))
        check = {'c': 'd'}
        check_json(source, check)

    def test_json_dict(self):
        ''' Verify a dict can be used to search within child objects without having to match the
        child object exactly.'''
        source = json.loads(json.dumps({'a': {'foo': 'bar', 'fizz': 'buzz'}}))
        check = {'a': {'fizz': 'buzz'}}
        check_json(source, check)

    def test_json_list(self):
        ''' Verify that if the source is a list, the check need only pass for any element of the
        list. '''
        source = json.loads(json.dumps([{'a': {'b': 1, 'c': 2}}, {'a': {'b': 3, 'c': 5}}]))
        check = {'a': {'c': 5}}
        check_json(source, check)

if __name__ == '__main__':
    unittest.main()
