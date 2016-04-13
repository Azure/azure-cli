import unittest
from six import StringIO
from collections import namedtuple

from azure.cli.command_modules.storage.params import (
    _parse_ip_range, _parse_container_permission, _parse_services, _parse_resource_types
)

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

    def test_ip_address_single(self):
        input = "111.22.3.111"
        actual = _parse_ip_range(input)
        expected = input
        self.assertEqual(actual, expected)

    def test_ip_address_range(self):
        input = "111.22.3.111-222.11.44.111"
        actual = _parse_ip_range(input)
        expected = input
        self.assertEqual(actual, expected)

    def test_ip_address_fail(self):
        input = "111.22"
        with self.assertRaises(ValueError):        
            actual = _parse_ip_range(input)
    
    def test_ip_address_fail2(self):
        input = "111.22.33.44-"
        with self.assertRaises(ValueError):
            actual = _parse_ip_range(input)

    def test_container_permission(self):
        input = "llwrwd"
        actual = str(_parse_container_permission(input))
        expected = "rwdl"
        self.assertEqual(actual, expected)

    def test_container_permission_fail(self):
        input = "all"
        with self.assertRaises(ValueError):
            actual = str(_parse_container_permission(input))

    def test_resource_types_valid(self):
        input = "sso"
        actual = str(_parse_resource_types(input))
        expected = "so"
        self.assertEqual(actual, expected)

    def test_resource_types_invalid(self):
        input = "blob"
        with self.assertRaises(ValueError):
            actual = _parse_resource_types(input)

    def test_services_types_valid(self):
        input = "ttfqbqtf"
        actual = str(_parse_services(input))
        expected = "bqtf"
        self.assertEqual(actual, expected)

    def test_services_invalid(self):
        input = "everything"
        with self.assertRaises(ValueError):
            actual = _parse_services(input)

if __name__ == '__main__':
    unittest.main()
