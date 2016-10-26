#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import tempfile
import unittest
import mock

#pylint: disable=line-too-long

from azure.cli.core.cloud import (Cloud,
                                  CloudEndpoints,
                                  CloudSuffixes,
                                  add_cloud,
                                  get_custom_clouds,
                                  remove_cloud,
                                  CloudEndpointNotSetException)
from azure.cli.core._profile import Profile

class TestCloud(unittest.TestCase):

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('AzureCloud'))
    def test_endpoint_none(self):
        with self.assertRaises(CloudEndpointNotSetException):
            profile = Profile()
            profile.get_login_credentials()

    @mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: [])
    def test_add_get_delete_custom_cloud(self):
        endpoints = CloudEndpoints(management='http://management.contoso.com')
        suffixes = CloudSuffixes(storage_endpoint='core.contoso.com')
        c = Cloud('MyOwnCloud', endpoints=endpoints, suffixes=suffixes)
        expected_config_file_result = "[MyOwnCloud]\nendpoint_management = http://management.contoso.com\nsuffix_storage_endpoint = core.contoso.com\n\n"
        with mock.patch('azure.cli.core.cloud.CUSTOM_CLOUD_CONFIG_FILE', tempfile.mkstemp()[1]) as config_file:
            with mock.patch('azure.cli.core.cloud.get_custom_clouds', lambda: []):
                add_cloud(c)
                with open(config_file, 'r') as cf:
                    self.assertEqual(cf.read(), expected_config_file_result)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 1)
            self.assertEqual(custom_clouds[0].name, c.name)
            self.assertEqual(custom_clouds[0].endpoints.management, c.endpoints.management)
            self.assertEqual(custom_clouds[0].suffixes.storage_endpoint, c.suffixes.storage_endpoint)
            with mock.patch('azure.cli.core.cloud._get_cloud', lambda _: c):
                remove_cloud(c.name)
            custom_clouds = get_custom_clouds()
            self.assertEqual(len(custom_clouds), 0)

if __name__ == '__main__':
    unittest.main()
