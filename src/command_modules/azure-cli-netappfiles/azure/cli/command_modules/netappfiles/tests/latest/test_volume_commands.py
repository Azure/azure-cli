# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

POOL_DEFAULT = "--service-level 'Premium' --size 4398046511104"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 107374182400"

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesExtVolumeServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name, ip_pre):
        self.cmd("az network vnet create -n %s --resource-group %s -l eastus2 --address-prefix %s/16" % (vnet_name, rg, ip_pre))
        self.cmd("az network vnet subnet create -n %s -g %s --vnet-name %s --address-prefixes '%s/24' --delegations 'Microsoft.Netapp/volumes'" % (subnet_name, rg, vnet_name, ip_pre))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None, volume_name2=None):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        creation_token = volume_name1
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (self.current_subscription(), rg, vnet_name, subnet_name)
        tag = "--tags '%s'" % tags if tags is not None else ""

        self.setup_vnet(rg, vnet_name, subnet_name, '10.12.0.0')
        self.cmd("az netappfiles account create -g %s -a '%s' -l 'eastus2'" % (rg, account_name)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l 'eastus2' %s %s" % (rg, account_name, pool_name, POOL_DEFAULT, tag)).get_output_in_json()
        volume1 = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l 'eastus2' %s --creation-token %s --subnet-id %s %s" % (rg, account_name, pool_name, volume_name1, VOLUME_DEFAULT, creation_token, subnet_id, tag)).get_output_in_json()

        if volume_name2:
            creation_token = volume_name2
            self.cmd("az netappfiles volume create -g %s -a %s -p %s -v %s -l 'eastus2' %s --creation-token %s --subnet-id %s --tags '%s'" % (rg, account_name, pool_name, volume_name2, VOLUME_DEFAULT, creation_token, subnet_id, tags)).get_output_in_json()

        return volume1

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_create_delete_volumes(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1 Tag2=Value2"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', tags)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['tags']['Tag1'] == 'Value1'
        assert volume['tags']['Tag2'] == 'Value2'
        # default export policy still present
        assert volume['exportPolicy']['rules'][0]['allowedClients'] == '0.0.0.0/0'
        assert not volume['exportPolicy']['rules'][0]['cifs']
        assert volume['exportPolicy']['rules'][0]['ruleIndex'] == 1

        volume_list = self.cmd("netappfiles volume list --resource-group {rg} --account-name %s --pool-name %s" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 1

        self.cmd("az netappfiles volume delete --resource-group {rg} --account-name %s --pool-name %s --volume-name %s" % (account_name, pool_name, volume_name))
        volume_list = self.cmd("netappfiles volume list --resource-group {rg} -a %s -p %s" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_list_volumes(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name1 = self.create_random_name(prefix='cli-vol-', length=24)
        volume_name2 = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1"
        self.create_volume(account_name, pool_name, volume_name1, '{rg}', tags, volume_name2)

        volume_list = self.cmd("netappfiles volume list --resource-group {rg} -a '%s' -p '%s'" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 2

        self.cmd("az netappfiles volume delete -g {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name1))
        volume_list = self.cmd("netappfiles volume list -g {rg} -a '%s' -p '%s'" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 1

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_get_volume_by_name(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag2=Value1"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', tags)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        volume = self.cmd("az netappfiles volume show --resource-group {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['tags']['Tag2'] == 'Value1'

        volume_from_id = self.cmd("az netappfiles volume show --ids %s" % volume['id']).get_output_in_json()
        assert volume_from_id['name'] == account_name + '/' + pool_name + '/' + volume_name

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_update_volume(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value2"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        volume = self.cmd("az netappfiles volume update --resource-group {rg} -a %s -p %s -v %s --tags %s --service-level 'Standard'" % (account_name, pool_name, volume_name, tags)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['serviceLevel'] == "Standard"
        assert volume['tags']['Tag1'] == 'Value2'
        # default export policy still present
        assert volume['exportPolicy']['rules'][0]['allowedClients'] == '0.0.0.0/0'
        assert not volume['exportPolicy']['rules'][0]['cifs']
        assert volume['exportPolicy']['rules'][0]['ruleIndex'] == 1
