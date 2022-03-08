# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from argparse import Namespace
from io import StringIO

from knack import CLI

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.profiles import get_sdk, ResourceType, supported_api_version

from azure.cli.command_modules.storage._validators import (get_permission_validator, get_datetime_type,
                                                           ipv4_range_type, resource_type_type, services_type,
                                                           process_blob_source_uri, get_char_options_validator)
from azure.cli.testsdk import api_version_constraint
from azure.cli.command_modules.storage._validators import get_source_file_or_blob_service_client


class MockCLI(CLI):
    def __init__(self):
        super(MockCLI, self).__init__(cli_name='mock_cli', config_dir=GLOBAL_CONFIG_DIR,
                                      config_env_var_prefix=ENV_VAR_PREFIX, commands_loader_cls=MockLoader)
        self.cloud = get_active_cloud(self)


class MockLoader(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def get_models(self, *attr_args, **_):
        from azure.cli.core.profiles import get_sdk
        return get_sdk(self.ctx, ResourceType.DATA_STORAGE, *attr_args, mod='models')


class MockCmd(object):
    def __init__(self, ctx):
        self.cli_ctx = ctx
        self.loader = MockLoader(self.cli_ctx)

    def get_models(self, *attr_args, **kwargs):
        return get_sdk(self.cli_ctx, ResourceType.DATA_STORAGE, *attr_args, **kwargs)


class TestStorageValidators(unittest.TestCase):
    def setUp(self):
        self.io = StringIO()
        self.cli = MockCLI()
        self.loader = MockLoader(self.cli)

    def tearDown(self):
        self.io.close()

    def test_permission_validator(self):
        t_container_permissions = get_sdk(self.cli, ResourceType.DATA_STORAGE, 'blob.models#ContainerPermissions')

        ns1 = Namespace(permission='rwdl')
        ns2 = Namespace(permission='abc')
        get_permission_validator(t_container_permissions)(ns1)
        self.assertTrue(isinstance(ns1.permission, t_container_permissions))
        with self.assertRaises(ValueError):
            get_permission_validator(t_container_permissions)(ns2)

    def test_datetime_string_type(self):
        input = "2017-01-01T12:30Z"
        actual = get_datetime_type(True)(input)
        expected = "2017-01-01T12:30Z"
        self.assertEqual(actual, expected)

        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            get_datetime_type(True)(input)

    def test_datetime_type(self):
        import datetime
        input = "2017-01-01T12:30Z"
        actual = get_datetime_type(False)(input)
        expected = datetime.datetime(2017, 1, 1, 12, 30, 0)
        self.assertEqual(actual, expected)

        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            actual = get_datetime_type(False)(input)

    def test_ipv4_range_type(self):
        from knack.util import CLIError
        input = "111.22.3.111"
        actual = ipv4_range_type(input)
        expected = input
        self.assertEqual(actual, expected)

        input = "111.22.3.111-222.11.44.111"
        actual = ipv4_range_type(input)
        expected = input
        self.assertEqual(actual, expected)

        input = "111.22"
        with self.assertRaises(CLIError):
            actual = ipv4_range_type(input)

        input = "111.22.33.44-"
        with self.assertRaises(CLIError):
            actual = ipv4_range_type(input)

    def test_resource_types_type(self):
        input = "sso"
        actual = str(resource_type_type(self.loader)(input))
        expected = "so"
        self.assertEqual(actual, expected)

        input = "blob"
        with self.assertRaises(ValueError):
            actual = resource_type_type(self.loader)(input)

    def test_services_type(self):
        input = "ttfqbqtf"
        actual = str(services_type(self.loader)(input))
        if supported_api_version(self.cli, ResourceType.DATA_STORAGE, max_api='2016-05-31') or \
           supported_api_version(self.cli, ResourceType.DATA_STORAGE, min_api='2017-07-29'):
            expected = "bqtf"
        else:
            expected = "bqf"
        self.assertEqual(actual, expected)

        input = "everything"
        with self.assertRaises(ValueError):
            services_type(self.loader)(input)

    def test_storage_process_blob_source_uri_redundent_parameter(self):
        with self.assertRaises(ValueError):
            process_blob_source_uri(MockCmd(self.cli),
                                    Namespace(copy_source='https://example.com', source_sas='some_sas'))
        with self.assertRaises(ValueError):
            process_blob_source_uri(MockCmd(self.cli),
                                    Namespace(copy_source='https://example.com', source_account_name='account_name'))

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


class TestGetSourceClientValidator(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    def test_validate_with_container_name_blob(self):
        # source container name given, validator does not change namespace aside from ensuring source-client none
        ns = self._create_namespace(source_container='container2', destination_container='container1')
        get_source_file_or_blob_service_client(MockCmd(self.cli), ns)
        self.assertIsNone(ns.source_client)

    def test_validate_with_source_uri_blob(self):
        # source given in form of uri, source_container parsed from uri, source and dest account are the same
        ns = self._create_namespace(source_uri='https://storage_name.blob.core.windows.net/container2',
                                    destination_container='container1')
        with mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value="fake_key"):
            get_source_file_or_blob_service_client(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_container, 'container2')
        self.assertIsNone(ns.source_client)

    def test_validate_with_different_source_uri_sas_blob(self):
        # source given in form of uri, source_container parsed from uri, source and dest account are different
        ns = self._create_namespace(source_uri='https://other_name.blob.core.windows.net/container2?some_sas_token',
                                    destination_container='container1')
        get_source_file_or_blob_service_client(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_container, 'container2')
        self.assertIsNotNone(ns.source_client)
        self.assertEqual(ns.source_client.account_name, 'other_name')

    def test_validate_with_share_name_file(self):
        # source share name given, validator does not change namespace aside from ensuring source-client none
        ns = self._create_namespace(source_share='share2', destination_share='share1')
        get_source_file_or_blob_service_client(MockCmd(self.cli), ns)
        self.assertIsNone(ns.source_client)

    def test_validate_with_source_uri_file(self):
        # source given in form of uri, source_share parsed from uri, source and dest account are the same
        ns = self._create_namespace(source_uri='https://storage_name.file.core.windows.net/share2',
                                    destination_share='share1')
        with mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value="fake_key"):
            get_source_file_or_blob_service_client(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_share, 'share2')
        self.assertIsNone(ns.source_client)

    def test_validate_with_different_source_uri_sas_file(self):
        # source given in form of uri, source_share parsed from uri, source and dest account are different
        ns = self._create_namespace(source_uri='https://other_name.file.core.windows.net/share2?some_sas_token',
                                    destination_share='share1')
        get_source_file_or_blob_service_client(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_share, 'share2')
        self.assertIsNotNone(ns.source_client)
        self.assertEqual(ns.source_client.account_name, 'other_name')

    def test_validate_negatives(self):
        # bad argument combinations
        with self.assertRaises(ValueError):
            get_source_file_or_blob_service_client(
                MockCmd(self.cli),
                self._create_namespace(source_uri='https://storage_name.file.core.windows.net/share2',
                                       source_account_name='some_name'))

        with self.assertRaises(ValueError):
            get_source_file_or_blob_service_client(MockCmd(self.cli), self._create_namespace(source_uri='faulty_uri'))

        with self.assertRaises(ValueError):
            get_source_file_or_blob_service_client(
                MockCmd(self.cli),
                self._create_namespace(source_container='container_name', source_share='share_name'))

    def _create_namespace(self, **kwargs):
        ns = Namespace(account_key='my_storage_key', account_name='storage_name', connection_string=None, dryrun=False,
                       pattern='*', sas_token=None, source_account_key=None, source_account_name=None,
                       source_client=None, source_container=None, source_sas=None, source_share=None, source_uri=None,
                       destination_container=None, destination_share=None)

        for key in kwargs:
            setattr(ns, key, kwargs[key])
        return ns


if __name__ == '__main__':
    unittest.main()
