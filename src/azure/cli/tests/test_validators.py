#pylint: skip-file
import unittest
from six import StringIO

from azure.cli.commands.validators import *

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
        expected = {}
        self.assertEqual(actual, expected)

    def test_tag(self):
        self.assertEqual(validate_tag('test'), {'test':''})
        self.assertEqual(validate_tag('a=b'), {'a':'b'})
        self.assertEqual(validate_tag('a=b;c=d'), {'a':'b;c=d'})

if __name__ == '__main__':
    unittest.main()
