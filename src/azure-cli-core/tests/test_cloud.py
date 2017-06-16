# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import unittest
import mock

from azure.cli.core.cloud import (Cloud,
                                  CloudEndpoints,
                                  CloudSuffixes,
                                  add_cloud,
                                  get_cloud,
                                  get_clouds,
                                  get_custom_clouds,
                                  remove_cloud,
                                  get_active_cloud_name,
                                  init_known_clouds,
                                  AZURE_PUBLIC_CLOUD,
                                  CloudEndpointNotSetException)
from azure.cli.core._config import get_config_parser
from azure.cli.core._profile import Profile
from azure.cli.core.util import CLIError


class TestCloud(unittest.TestCase):

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('AzureCloud'))
    def test_endpoint_none(self):
        with self.assertRaises(CloudEndpointNotSetException):
            profile = Profile()
            profile.get_login_credentials()

    @mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: [])
    def test_add_get_delete_custom_cloud(self):
        endpoint_rm = 'http://management.contoso.com'
        suffix_storage = 'core.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        suffixes = CloudSuffixes(storage_endpoint=suffix_storage)
        c = Cloud('MyOwnCloud', endpoints=endpoints, suffixes=suffixes)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            with mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: []):
                add_cloud(c)
                config = get_config_parser()
                config.read(config_file)
                self.assertTrue(c.name in config.sections())
                self.assertEqual(config.get(c.name, 'endpoint_resource_manager'), endpoint_rm)
                self.assertEqual(config.get(c.name, 'suffix_storage_endpoint'), suffix_storage)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            self.assertEqual(custom_clouds[0].suffixes.storage_endpoint,
                             c.suffixes.storage_endpoint)
            with mock.patch('azure.cli.core.cloud._get_cloud', lambda _: c):
                remove_cloud(c.name)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 0)

    def test_add_get_cloud_with_profile(self):
        endpoint_rm = 'http://management.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        profile = '2017-03-09-profile-preview'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(c)
            config = get_config_parser()
            config.read(config_file)
            self.assertTrue(c.name in config.sections())
            self.assertEqual(config.get(c.name, 'endpoint_resource_manager'), endpoint_rm)
            self.assertEqual(config.get(c.name, 'profile'), profile)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            self.assertEqual(custom_clouds[0].profile,
                             c.profile)

    def test_add_get_cloud_with_invalid_profile(self):
        ''' Cloud has profile that doesn't exist so an exception should be raised '''
        profile = 'none-existent-profile'
        c = Cloud('MyOwnCloud', profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            add_cloud(c)
            config = get_config_parser()
            config.read(config_file)
            self.assertTrue(c.name in config.sections())
            self.assertEqual(config.get(c.name, 'profile'), profile)
            with self.assertRaises(CLIError):
                get_custom_clouds()

    def test_get_default_latest_profile(self):
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            clouds = get_clouds()
            for c in clouds:
                self.assertEqual(c.profile, 'latest')

    def test_custom_cloud_management_endpoint_set(self):
        ''' We have set management endpoint so don't override it '''
        endpoint_rm = 'http://management.contoso.com'
        endpoint_mgmt = 'http://management.core.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm, management=endpoint_mgmt)
        profile = '2017-03-09-profile-preview'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            add_cloud(c)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            # CLI logic should keep our set management endpoint
            self.assertEqual(custom_clouds[0].endpoints.management,
                             c.endpoints.management)

    def test_custom_cloud_no_management_endpoint_set(self):
        ''' Use ARM 'resource manager' endpoint as 'management' (old ASM) endpoint
            if only ARM endpoint is set '''
        endpoint_rm = 'http://management.contoso.com'
        endpoints = CloudEndpoints(resource_manager=endpoint_rm)
        profile = '2017-03-09-profile-preview'
        c = Cloud('MyOwnCloud', endpoints=endpoints, profile=profile)
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]):
            add_cloud(c)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].endpoints.resource_manager,
                             c.endpoints.resource_manager)
            # CLI logic should add management endpoint to equal resource_manager as we didn't set it
            self.assertEqual(custom_clouds[0].endpoints.management,
                             c.endpoints.resource_manager)

    def test_get_active_cloud_name_default(self):
        expected = AZURE_PUBLIC_CLOUD.name
        actual = get_active_cloud_name()
        self.assertEqual(expected, actual)

    def test_known_cloud_missing_endpoint(self):
        ''' New endpoints in cloud config should be saved in config for the known clouds '''
        with mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as\
                config_file:
            # Save the clouds to config to get started
            init_known_clouds()
            cloud = get_cloud(AZURE_PUBLIC_CLOUD.name)
            self.assertEqual(cloud.endpoints.batch_resource_id,
                             AZURE_PUBLIC_CLOUD.endpoints.batch_resource_id)
            # Remove an endpoint from the cloud config (leaving other config values as is)
            config = get_config_parser()
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


if __name__ == '__main__':
    unittest.main()
