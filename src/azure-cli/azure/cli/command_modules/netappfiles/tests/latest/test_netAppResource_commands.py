# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "westus2"

class AzureNetAppFilesResourceServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name, ip_pre, location):
        self.cmd("az network vnet create -n %s --resource-group %s -l %s --address-prefix %s/16" % (vnet_name, rg, location, ip_pre))
        subnet = self.cmd("az network vnet subnet create -n %s -g %s --vnet-name %s --address-prefixes '%s/24' --delegations 'Microsoft.Netapp/volumes'" % (subnet_name, rg, vnet_name, ip_pre)).get_output_in_json()
        subnetId = subnet['id']
        return subnetId

    #@unittest.skip('(servicefailure) locations/regionInfo is not deployed yet enable when fixed')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_get_region_info(self):
        self.kwargs.update({
            'loc': LOCATION,
        })

        self.cmd("az netappfiles resource query-region-info -l {loc}", checks=[
            self.check("length(@)", 2)
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_check_file_path_availability(self):
        self.kwargs.update({
            'loc': LOCATION,
            'filePath': 'newPath'
        })
        rg = '{rg}'
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        self.kwargs.update({
            'vnet_name': vnet_name
        })

        _subnetId = self.setup_vnet(rg, vnet_name, 'default', '10.0.0.0', LOCATION)
        self.kwargs.update({
            '_subnetId': _subnetId
        })
        self.cmd("az netappfiles check-file-path-availability -l {loc} --name testFile --subnet-id {_subnetId}", checks=[
            self.check('isAvailable', True),
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_check_name_availability(self):
        self.kwargs.update({
            'loc': LOCATION,
            'resourceType':'Microsoft.NetApp/netAppAccounts',
            'resourceName': 'testName'
        })

        self.cmd("az netappfiles check-name-availability -g {rg} -l {loc} --type {resourceType} --name {resourceName}", checks=[
            self.check('isAvailable', True),
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_check_quota_availability(self):
        self.kwargs.update({
            'loc': LOCATION,
            'resourceType':'Microsoft.NetApp/netAppAccounts',
            'resourceName': 'testName'
        })

        self.cmd("az netappfiles check-quota-availability -g {rg} -l {loc} --type {resourceType} --name {resourceName}", checks=[
            self.check('isAvailable', True),
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_region_info_list(self):
        self.kwargs.update({
            'loc': LOCATION
        })

        region_info_list = self.cmd("az netappfiles resource region-info list -l {loc}").get_output_in_json()
        assert len(region_info_list) == 1

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_region_info_show(self):
        self.kwargs.update({
            'loc': LOCATION
        })

        region_info = self.cmd("az netappfiles resource region-info default show -l {loc}").get_output_in_json()
        assert region_info['name'] == "{loc}/default"