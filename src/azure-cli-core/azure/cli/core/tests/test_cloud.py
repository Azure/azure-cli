# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import unittest
import mock
import multiprocessing

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
                                  AZURE_PUBLIC_CLOUD,
                                  KNOWN_CLOUDS,
                                  init_known_clouds,
                                  CloudEndpointNotSetException,
                                  CannotUnregisterCloudException)

from azure.cli.core._profile import Profile

from azure.cli.testsdk import TestCli

from knack.util import CLIError


def _helper_get_clouds(_):
    """ Helper method for multiprocessing.Pool.map func that uses throwaway arg """
    get_clouds(TestCli())


class TestCloud(unittest.TestCase):

    def test_endpoint_none(self):
        with self.assertRaises(CloudEndpointNotSetException):
            cli = TestCli()
            cli.cloud = Cloud('AzureCloud')
            profile = Profile(cli)
            profile.get_login_credentials()

    @mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: [])
    def test_add_get_delete_custom_cloud(self):
        cli = TestCli()
        endpoint_rm = 'http://management.contoso.com'
        suffix_storage = 'core.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        suffixes = CloudSuffixes(storage_endpoint=suffix_storage)
        c = Cloud('MyOwnCloud', endpoints=endpoints, suffixes=suffixes)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            with mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: []):
                add_cloud(cli, c)
                config = cli.config.config_parser
                config.read(config_file)
                self.assertTrue(c.name in config.sections())
                self.assertEqual(config.get(c.name, 'endpoint_resource_manager'), endpoint_rm)
                self.assertEqual(config.get(c.name, 'suffix_storage_endpoint'), suffix_storage)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            self.assertEqual(custom_clouds[0].suffixes.storage_endpoint,
                             c.suffixes.storage_endpoint)
            with mock.patch('azure.cli.core.cloud._get_cloud', lambda _, _1: c):
                remove_cloud(cli, c.name)
            custom_clouds = get_custom_clouds(cli)
            self.assertEqual(len(custom_clouds), 0)

    def test_add_get_cloud_with_profile(self):
        cli = TestCli()
        endpoint_rm = 'http://management.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        profile = '2017-03-09-profile'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(cli, c)
            config = cli.config.config_parser
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
        cli = TestCli()
        profile = 'none-existent-profile'
        c = Cloud('MyOwnCloud', profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(cli, c)
            config = cli.config.config_parser
            config.read(config_file)
            self.assertTrue(c.name in config.sections())
            self.assertEqual(config.get(c.name, 'profile'), profile)
            with self.assertRaises(CLIError):
                get_custom_clouds(cli)

    def test_get_default_latest_profile(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            cli = TestCli()
            clouds = get_clouds(cli)
            for c in clouds:
                self.assertEqual(c.profile, 'latest')

    def test_custom_cloud_management_endpoint_set(self):
        # We have set management endpoint so don't override it
        cli = TestCli()
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
        cli = TestCli()
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
        cli = TestCli()
        expected = AZURE_PUBLIC_CLOUD.name
        actual = get_active_cloud_name(cli)
        self.assertEqual(expected, actual)

    def test_known_cloud_missing_endpoint(self):
        cli = TestCli()
        # New endpoints in cloud config should be saved in config for the known clouds
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            # Save the clouds to config to get started
            init_known_clouds()
            cloud = get_cloud(cli, AZURE_PUBLIC_CLOUD.name)
            self.assertEqual(cloud.endpoints.batch_resource_id,
                             AZURE_PUBLIC_CLOUD.endpoints.batch_resource_id)
            # Remove an endpoint from the cloud config (leaving other config values as is)
            config = cli.config.config_parser
            config.read(config_file)
            config.remove_option(AZURE_PUBLIC_CLOUD.name, 'endpoint_batch_resource_id')
            with open(config_file, 'w') as cf:
                config.write(cf)
            # Verify that it was removed
            config.read(config_file)
            self.assertFalse(config.has_option(AZURE_PUBLIC_CLOUD.name,
                                               'endpoint_batch_resource_id'))
            # Init the known clouds again (this should add the missing endpoint)
            init_known_clouds(force=True)
            config.read(config_file)
            # The missing endpoint should have been added by init_known_clouds as 'force' was used.
            self.assertTrue(config.has_option(AZURE_PUBLIC_CLOUD.name,
                                              'endpoint_batch_resource_id'),
                            'Expected the missing endpoint to be added but it was not.')
            actual_val = config.get(AZURE_PUBLIC_CLOUD.name, 'endpoint_batch_resource_id')
            expected_val = AZURE_PUBLIC_CLOUD.endpoints.batch_resource_id
            self.assertEqual(actual_val, expected_val)

    def test_get_known_clouds(self):
        cli = TestCli()
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            # Check that we can get all the known clouds without any exceptions
            for kc in KNOWN_CLOUDS:
                get_cloud(cli, kc.name)

    def test_modify_known_cloud(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as config_file:
            pool_size = 100
            p = multiprocessing.Pool(pool_size)
            p.map(init_known_clouds, [True] * pool_size)
            p.close()
            p.join()
            # Check we can read the file with no exceptions
            cli = TestCli()
            config = cli.config.config_parser
            cloud_name = AZURE_PUBLIC_CLOUD.name
            cloud = get_cloud(cli, cloud_name)
            self.assertEqual(cloud.name, cloud_name)
            mcloud = Cloud(cloud_name)
            mcloud.endpoints.gallery = 'https://mynewcustomgallery.azure.com'
            update_cloud(cli, mcloud)
            cloud = get_cloud(cli, cloud_name)
            self.assertEqual(cloud.endpoints.gallery, 'https://mynewcustomgallery.azure.com')
            # Check that the config file only has what we changed, not the full cloud info.
            config = cli.config
            config.config_parser.read(config_file)
            items = config.config_parser.items(cloud_name)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0], ('endpoint_gallery', 'https://mynewcustomgallery.azure.com'))

    def test_remove_known_cloud(self):
        cli = TestCli()
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            with self.assertRaises(CannotUnregisterCloudException):
                remove_cloud(cli, AZURE_PUBLIC_CLOUD.name)

    def test_get_clouds_concurrent(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as config_file:
            pool_size = 100
            p = multiprocessing.Pool(pool_size)
            p.map(_helper_get_clouds, range(pool_size))
            p.close()
            p.join()
            # Check we can read the file with no exceptions
            cli = TestCli()
            config = cli.config
            config.config_parser.read(config_file)
            for kc in KNOWN_CLOUDS:
                get_cloud(cli, kc.name)


if __name__ == '__main__':
    unittest.main()
