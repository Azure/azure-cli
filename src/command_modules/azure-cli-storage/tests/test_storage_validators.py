# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from six import StringIO
from argparse import Namespace
from azure.cli.command_modules.storage._validators import (get_permission_validator,
                                                           get_datetime_type, datetime, ipv4_range_type, resource_type_type,
                                                           services_type, process_blob_source_uri)
from azure.cli.core.profiles import get_sdk, ResourceType


class TestStorageValidators(unittest.TestCase):
    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_permission_validator(self):
        ContainerPermissions = get_sdk(ResourceType.DATA_STORAGE, 'blob.models#ContainerPermissions')

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

    def test_storage_process_blob_source_uri_redundent_parameter(self):
        with self.assertRaises(ValueError):
            process_blob_source_uri(Namespace(copy_source='https://example.com',
                                              source_sas='some_sas'))
        with self.assertRaises(ValueError):
            process_blob_source_uri(Namespace(copy_source='https://example.com',
                                              source_account_name='account_name'))


if __name__ == '__main__':
    unittest.main()
