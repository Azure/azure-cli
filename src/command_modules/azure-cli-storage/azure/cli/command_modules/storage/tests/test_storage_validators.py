import unittest
from six import StringIO
from collections import namedtuple

from azure.cli.command_modules.storage._validators import *

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

    def test_date_as_string_valid(self):
        input = "2017-01-01T12:30Z"
        actual = validate_datetime_as_string(input)
        expected = "2017-01-01T12:30Z"
        self.assertEqual(actual, expected)

    def test_date_as_string_invalid(self):
        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            actual = validate_datetime_as_string(input)

    def test_date_valid(self):
        input = "2017-01-01T12:30Z"
        actual = validate_datetime(input)
        expected = datetime(2017, 1, 1, 12, 30, 0)
        self.assertEqual(actual, expected)

    def test_date_invalid(self):
        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            actual = validate_datetime(input)

    def test_ip_address_single(self):
        input = "111.22.3.111"
        actual = validate_ip_range(input)
        expected = input
        self.assertEqual(actual, expected)

    def test_ip_address_range(self):
        input = "111.22.3.111-222.11.44.111"
        actual = validate_ip_range(input)
        expected = input
        self.assertEqual(actual, expected)

    def test_ip_address_fail(self):
        input = "111.22"
        with self.assertRaises(ValueError):        
            actual = validate_ip_range(input)
    
    def test_ip_address_fail2(self):
        input = "111.22.33.44-"
        with self.assertRaises(ValueError):
            actual = validate_ip_range(input)

    def test_lease_duration_valid(self):
        self.assertEqual(validate_lease_duration('15'), 15)
        self.assertEqual(validate_lease_duration('45'), 45)
        self.assertEqual(validate_lease_duration('60'), 60)
        self.assertEqual(validate_lease_duration('-1'), -1)

    def test_lease_duration_invalid(self):
        with self.assertRaises(ValueError):
            validate_lease_duration('14')
        with self.assertRaises(ValueError):
            validate_lease_duration('61')
        with self.assertRaises(ValueError):
            validate_lease_duration('-10')

    def test_container_permission(self):
        input = "llwrwd"
        actual = str(validate_container_permission(input))
        expected = "rwdl"
        self.assertEqual(actual, expected)

    def test_container_permission_fail(self):
        input = "all"
        with self.assertRaises(ValueError):
            actual = str(validate_container_permission(input))

    def test_resource_types_valid(self):
        input = "sso"
        actual = str(validate_resource_types(input))
        expected = "so"
        self.assertEqual(actual, expected)

    def test_resource_types_invalid(self):
        input = "blob"
        with self.assertRaises(ValueError):
            actual = validate_resource_types(input)

    def test_services_types_valid(self):
        input = "ttfqbqtf"
        actual = str(validate_services(input))
        expected = "bqtf"
        self.assertEqual(actual, expected)

    def test_services_invalid(self):
        input = "everything"
        with self.assertRaises(ValueError):
            actual = validate_services(input)

    def test_id_invalid(self):
        input = "x" * 65
        with self.assertRaises(ValueError):
            actual = validate_id(input)

if __name__ == '__main__':
    unittest.main()
