# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import unittest
from unittest import mock
import multiprocessing
import configparser

from azure.cli.core.cloud import (Cloud,
                                  CloudEndpoints,
                                  CloudSuffixes,
                                  add_cloud,
                                  get_cloud,
                                  get_clouds,
                                  get_custom_clouds,
                                  remove_cloud,
                                  get_active_cloud_name,
                                  update_cloud,
                                  cloud_is_registered,
                                  AZURE_PUBLIC_CLOUD,
                                  KNOWN_CLOUDS,
                                  update_cloud,
                                  CloudEndpointNotSetException,
                                  CannotUnregisterCloudException,
                                  switch_active_cloud,
                                  get_known_clouds,
                                  HARD_CODED_CLOUD_LIST)

from azure.cli.core._profile import Profile

from azure.cli.core.mock import DummyCli

from knack.util import CLIError


def _helper_get_clouds(_):
    """ Helper method for multiprocessing.Pool.map func that uses throwaway arg """
    get_clouds(DummyCli())


class TestCloud(unittest.TestCase):

    def test_endpoint_none(self):
        with self.assertRaises(CloudEndpointNotSetException):
            cli = DummyCli()
            cli.cloud = Cloud('AzureCloud')
            profile = Profile(cli_ctx=cli)
            profile.get_login_credentials()

    @mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: [])
    def test_add_get_delete_custom_cloud(self):
        cli = DummyCli()
        endpoint_rm = 'http://management.contoso.com'
        suffix_storage = 'core.contoso.com'
        suffix_acr_login_server = '.azurecr-test.io'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        suffixes = CloudSuffixes(storage_endpoint=suffix_storage,
                                 acr_login_server_endpoint=suffix_acr_login_server)
        c = Cloud('MyOwnCloud', endpoints=endpoints, suffixes=suffixes)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            with mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: []):
                add_cloud(cli, c)
                config = configparser.ConfigParser()
                config.read(config_file)
                self.assertTrue(c.name in config.sections())
                self.assertEqual(config.get(c.name, 'endpoint_resource_manager'), endpoint_rm)
                self.assertEqual(config.get(c.name, 'suffix_storage_endpoint'), suffix_storage)
                self.assertEqual(config.get(c.name, 'suffix_acr_login_server_endpoint'), suffix_acr_login_server)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            self.assertEqual(custom_clouds[0].suffixes.storage_endpoint,
                             c.suffixes.storage_endpoint)
            self.assertEqual(custom_clouds[0].suffixes.acr_login_server_endpoint,
                             c.suffixes.acr_login_server_endpoint)
            with mock.patch('azure.cli.core.cloud._get_cloud', lambda _, _1: c):
                remove_cloud(cli, c.name)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 0)

    def test_add_get_cloud_with_profile(self):
        cli = DummyCli()
        endpoint_rm = 'http://management.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        profile = '2017-03-09-profile'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(cli, c)
            config = configparser.ConfigParser()
            config.read(config_file)
            self.assertTrue(c.name in config.sections())
            self.assertEqual(config.get(c.name, 'endpoint_resource_manager'), endpoint_rm)
            self.assertEqual(config.get(c.name, 'profile'), profile)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager, c.endpoints.resource_manager)
            self.assertEqual(custom_clouds[0].profile, c.profile)

    def test_add_get_cloud_with_hybrid_profile(self):
        cli = DummyCli()
        endpoint_rm = 'http://management.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        profile = '2018-03-01-hybrid'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(cli, c)
            config = configparser.ConfigParser()
            config.read(config_file)
            self.assertTrue(c.name in config.sections())
            self.assertEqual(config.get(c.name, 'endpoint_resource_manager'), endpoint_rm)
            self.assertEqual(config.get(c.name, 'profile'), profile)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager, c.endpoints.resource_manager)
            self.assertEqual(custom_clouds[0].profile, c.profile)

    def test_add_get_cloud_with_invalid_profile(self):
        # Cloud has profile that doesn't exist so an exception should be raised
        cli = DummyCli()
        profile = 'none-existent-profile'
        c = Cloud('MyOwnCloud', profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(cli, c)
            config = configparser.ConfigParser()
            config.read(config_file)
            self.assertTrue(c.name in config.sections())
            self.assertEqual(config.get(c.name, 'profile'), profile)
            with self.assertRaises(CLIError):
                get_custom_clouds(cli)

    def test_get_default_latest_profile(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            cli = DummyCli()
            clouds = get_clouds(cli)
            for c in clouds:
                self.assertEqual(c.profile, 'latest')

    def test_custom_cloud_management_endpoint_set(self):
        # We have set management endpoint so don't override it
        cli = DummyCli()
        endpoint_rm = 'http://management.contoso.com'
        endpoint_mgmt = 'http://management.core.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm, management=endpoint_mgmt)
        profile = '2017-03-09-profile'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            add_cloud(cli, c)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            # CLI logic should keep our set management endpoint
            self.assertEqual(custom_clouds[0].endpoints.management,
                             c.endpoints.management)

    def test_custom_cloud_no_management_endpoint_set(self):
        # Use ARM 'resource manager' endpoint as 'management' (old ASM) endpoint if only ARM endpoint is set
        cli = DummyCli()
        endpoint_rm = 'http://management.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        profile = '2017-03-09-profile'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            add_cloud(cli, c)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            # CLI logic should add management endpoint to equal resource_manager as we didn't set it
            self.assertEqual(custom_clouds[0].endpoints.management,
                             c.endpoints.resource_manager)

    def test_get_active_cloud_name_default(self):
        cli = DummyCli()
        expected = AZURE_PUBLIC_CLOUD.name
        actual = get_active_cloud_name(cli)
        self.assertEqual(expected, actual)

    def test_get_known_clouds(self):
        cli = DummyCli()
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            # Check that we can get all the known clouds without any exceptions
            for kc in KNOWN_CLOUDS:
                get_cloud(cli, kc.name)

    def test_modify_known_cloud(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as config_file:
            cli = DummyCli()
            config = configparser.ConfigParser()
            cloud_name = AZURE_PUBLIC_CLOUD.name
            cloud = get_cloud(cli, cloud_name)
            self.assertEqual(cloud.name, cloud_name)
            mcloud = Cloud(cloud_name)
            mcloud.endpoints.gallery = 'https://mynewcustomgallery.azure.com'
            update_cloud(cli, mcloud)
            cloud = get_cloud(cli, cloud_name)
            self.assertEqual(cloud.endpoints.gallery, 'https://mynewcustomgallery.azure.com')
            # Check that the config file only has what we changed, not the full cloud info.
            config.read(config_file)
            items = config.items(cloud_name)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0], ('endpoint_gallery', 'https://mynewcustomgallery.azure.com'))

    def test_remove_known_cloud(self):
        cli = DummyCli()
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            with self.assertRaises(CannotUnregisterCloudException):
                remove_cloud(cli, AZURE_PUBLIC_CLOUD.name)

    def test_get_clouds_concurrent(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as config_file:
            # Max pool_size is 61, otherwise exception will be thrown on Python 3.8 Windows:
            #     File "...Python38\lib\multiprocessing\connection.py", line 810, in _exhaustive_wait
            #       res = _winapi.WaitForMultipleObjects(L, False, timeout)
            #   ValueError: need at most 63 handles, got a sequence of length 102
            pool_size = 20
            p = multiprocessing.Pool(pool_size)
            p.map(_helper_get_clouds, range(pool_size))
            p.close()
            p.join()
            # Check we can read the file with no exceptions
            cli = DummyCli()
            configparser.ConfigParser().read(config_file)
            for kc in KNOWN_CLOUDS:
                get_cloud(cli, kc.name)

    def test_cloud_is_registered(self):
        cli = DummyCli()
        self.assertTrue(cloud_is_registered(cli, AZURE_PUBLIC_CLOUD.name))
        self.assertFalse(cloud_is_registered(cli, 'MyUnknownCloud'))

    @mock.patch('azure.cli.core.cloud._set_active_subscription', autospec=True)
    def test_switch_active_cloud(self, subscription_setter):
        cli = mock.MagicMock()
        switch_active_cloud(cli, 'AzureGermanCloud')
        self.assertEqual(cli.cloud.name, 'AzureGermanCloud')

        switch_active_cloud(cli, 'AzureChinaCloud')
        self.assertEqual(cli.cloud.name, 'AzureChinaCloud')

    @unittest.skip('Blocks CI. Skip until arm service team fix vmImageAliasDoc url in metadata.')
    @mock.patch.dict('os.environ', {'ARM_CLOUD_METADATA_URL': 'https://management.azure.com/metadata/endpoints?api-version=2019-05-01'})
    def test_metadata_url_endpoints(self):
        clouds = get_known_clouds(refresh=True)
        for cloud in HARD_CODED_CLOUD_LIST:
            metadata_url_cloud = next(c for c in clouds if c.name == cloud.name)
            for k, v1 in cloud.endpoints.__dict__.items():
                v2 = metadata_url_cloud.endpoints.__dict__[k]
                if v1:
                    self.assertEqual(v1.strip('/'), v2.strip('/'))
                else:
                    self.assertEqual(v1, v2)
            for k, v1 in cloud.suffixes.__dict__.items():
                v2 = metadata_url_cloud.suffixes.__dict__[k]
                self.assertEqual(v1, v2)


if __name__ == '__main__':
    unittest.main()
