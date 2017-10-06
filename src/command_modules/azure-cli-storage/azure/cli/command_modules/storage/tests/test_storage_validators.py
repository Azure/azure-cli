# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from argparse import Namespace
from six import StringIO

from azure.cli.command_modules.storage._validators import (get_permission_validator, get_datetime_type, datetime,
                                                           ipv4_range_type, resource_type_type, services_type,
                                                           process_blob_source_uri, get_char_options_validator)
from azure.cli.core.profiles import get_sdk, ResourceType, supported_api_version
from azure.cli.testsdk import api_version_constraint


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
        if supported_api_version(ResourceType.DATA_STORAGE, max_api='2016-05-31'):
            expected = "bqtf"
        else:
            expected = "bqf"
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

    def test_storage_get_char_options_validator(self):
        with self.assertRaises(ValueError) as cm:
            get_char_options_validator('abc', 'no_such_property')(object())
        self.assertEqual('Missing options --no-such-property.', str(cm.exception))

        ns = Namespace(services='bcd')
        with self.assertRaises(ValueError) as cm:
            get_char_options_validator('abc', 'services')(ns)
        self.assertEqual('--services: only valid values are: a, b, c.', str(cm.exception))

        ns = Namespace(services='ab')
        get_char_options_validator('abc', 'services')(ns)

        result = getattr(ns, 'services')
        self.assertIs(type(result), set)
        self.assertEqual(result, set('ab'))


@api_version_constraint(resource_type=ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class TestEncryptionValidators(unittest.TestCase):
    def test_validate_encryption_services(self):
        from azure.cli.command_modules.storage._validators import validate_encryption_services

        ns = Namespace(encryption_services=['blob'])
        validate_encryption_services(ns)
        self.assertIsNotNone(ns.encryption_services.blob)
        self.assertTrue(ns.encryption_services.blob.enabled)
        self.assertIsNone(ns.encryption_services.file)

        ns = Namespace(encryption_services=['file'])
        validate_encryption_services(ns)
        self.assertIsNotNone(ns.encryption_services.file)
        self.assertTrue(ns.encryption_services.file.enabled)
        self.assertIsNone(ns.encryption_services.blob)

        ns = Namespace(encryption_services=['blob', 'file'])
        validate_encryption_services(ns)
        self.assertIsNotNone(ns.encryption_services.blob)
        self.assertTrue(ns.encryption_services.blob.enabled)
        self.assertIsNotNone(ns.encryption_services.file)
        self.assertTrue(ns.encryption_services.file.enabled)

    def test_validate_encryption_source(self):
        from azure.cli.command_modules.storage._validators import validate_encryption_source

        with self.assertRaises(ValueError):
            validate_encryption_source(Namespace(encryption_key_source='Notanoption'))

        with self.assertRaises(ValueError):
            validate_encryption_source(Namespace(encryption_key_source='Microsoft.Keyvault'))

        with self.assertRaises(ValueError):
            validate_encryption_source(Namespace(encryption_key_source='Microsoft.Storage',
                                                 encryption_key_name='key_name',
                                                 encryption_key_version='key_version',
                                                 encryption_key_vault='https://example.com/key_uri'))

        ns = Namespace(encryption_key_source='Microsoft.Keyvault',
                       encryption_key_name='key_name',
                       encryption_key_version='key_version',
                       encryption_key_vault='https://example.com/key_uri')
        validate_encryption_source(ns)
        self.assertFalse(hasattr(ns, 'encryption_key_name'))
        self.assertFalse(hasattr(ns, 'encryption_key_version'))
        self.assertFalse(hasattr(ns, 'encryption_key_uri'))

        properties = ns.encryption_key_vault_properties
        self.assertEqual(properties.key_name, 'key_name')
        self.assertEqual(properties.key_version, 'key_version')
        self.assertEqual(properties.key_vault_uri, 'https://example.com/key_uri')


if __name__ == '__main__':
    unittest.main()
