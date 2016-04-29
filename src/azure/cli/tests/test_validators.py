import unittest
from six import StringIO

from azure.cli.commands._validators import *

class Test_storage_validators(unittest.TestCase):

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

    def test_key_value_pairs_valid(self):
        input = 'a=b;c=d'
        actual = validate_key_value_pairs(input)
        expected = {'a':'b', 'c':'d'}
        self.assertEqual(actual, expected)

    def test_key_value_pairs_invalid(self):
        input = 'a=b;c=d;e'
        actual = validate_key_value_pairs(input)
        expected = {'a':'b', 'c':'d'}
        self.assertEqual(actual, expected)

    def test_tags_valid(self):
        input = 'a=b;c=d;e'
        actual = validate_tags(input)
        expected = {'a':'b', 'c':'d', 'e':''}
        self.assertEqual(actual, expected)

    def test_tags_invalid(self):
        input = ''
        actual = validate_tags(input)
        expected = None
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
