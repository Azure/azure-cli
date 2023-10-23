# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)

DEFAULT_LOCATION = "westus"

class StaticAppBasicE2ETest(ScenarioTest):
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_staticapp_appsettings(self, resource_group):
        static_site_name = self.create_random_name(prefix='swabackends', length=24)
        self.cmd('staticwebapp create -g {} -n {} --sku=Standard'.format(resource_group, static_site_name))

        # set and verify null returns
        response = self.cmd('staticwebapp appsettings set -g {} -n {} --setting-names s1=s1 s2=s2 s3=s3'.format(resource_group, static_site_name)).get_output_in_json()
        for setting in response["properties"]:
            self.assertEqual(response["properties"][setting], None)

        # list and check result
        response = self.cmd('staticwebapp appsettings list -g {} -n {}'.format(resource_group, static_site_name)).get_output_in_json()
        for setting in response["properties"]:
            self.assertEqual(response["properties"][setting], setting)
        self.assertEqual(len(response["properties"]), 3)

        response = self.cmd('staticwebapp appsettings delete -g {} -n {} --setting-names s1 s2'.format(resource_group, static_site_name)).get_output_in_json()
        self.assertEqual(response["properties"]["s3"], None)

        # list and check result
        response = self.cmd('staticwebapp appsettings list -g {} -n {}'.format(resource_group, static_site_name)).get_output_in_json()
        self.assertEqual(response["properties"]["s3"], "s3")
        self.assertEqual(len(response["properties"]), 1)