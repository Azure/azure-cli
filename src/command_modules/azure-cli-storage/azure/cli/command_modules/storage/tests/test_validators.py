# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file
import unittest

from six import StringIO

from azure.cli.command_modules.storage._validators import (get_permission_validator,
                                                           get_datetime_type, datetime, ipv4_range_type, resource_type_type,
                                                           services_type)


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

    def test_permission_validator(self):
        from azure.storage.blob.models import ContainerPermissions
        from argparse import Namespace

        ns1 = Namespace(permission='rwdl')
        ns2 = Namespace(permission='abc')
        get_permission_validator(ContainerPermissions)(ns1)
        self.assertTrue(isinstance(ns1.permission, ContainerPermissions))
        with self.assertRaises(ValueError):
            get_permission_validator(ContainerPermissions)(ns2)

    def test_datetime_string_type(self):
        input = "2017-01-01T12:30Z"
        actual = get_datetime_type(True)(input)
        expected = "2017-01-01T12:30Z"
        self.assertEqual(actual, expected)

        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            actual = get_datetime_type(True)(input)

    def test_datetime_type(self):
        input = "2017-01-01T12:30Z"
        actual = get_datetime_type(False)(input)
        expected = datetime(2017, 1, 1, 12, 30, 0)
        self.assertEqual(actual, expected)

        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            actual = get_datetime_type(False)(input)

    def test_ipv4_range_type(self):
        input = "111.22.3.111"
        actual = ipv4_range_type(input)
        expected = input
        self.assertEqual(actual, expected)

        input = "111.22.3.111-222.11.44.111"
        actual = ipv4_range_type(input)
        expected = input
        self.assertEqual(actual, expected)

        input = "111.22"
        with self.assertRaises(ValueError):
            actual = ipv4_range_type(input)

        input = "111.22.33.44-"
        with self.assertRaises(ValueError):
            actual = ipv4_range_type(input)

    def test_resource_types_type(self):
        input = "sso"
        actual = str(resource_type_type(input))
        expected = "so"
        self.assertEqual(actual, expected)

        input = "blob"
        with self.assertRaises(ValueError):
            actual = resource_type_type(input)

    def test_services_type(self):
        input = "ttfqbqtf"
        actual = str(services_type(input))
        expected = "bqtf"
        self.assertEqual(actual, expected)

        input = "everything"
        with self.assertRaises(ValueError):
            actual = services_type(input)


if __name__ == '__main__':
    unittest.main()
