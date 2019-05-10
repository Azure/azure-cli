# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

POOL_DEFAULT = "--service-level 'Premium' --size 4398046511104"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 107374182400"

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesMountTargetServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name):
        self.cmd("az network vnet create -n %s --resource-group %s -l westus2" % (vnet_name, rg))
        self.cmd("az network vnet subnet create -n subnet01 --vnet-name %s --address-prefixes '10.0.0.0/24' --delegations 'Microsoft.Netapp/volumes' -g %s" % (vnet_name, rg))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None):
        vnet_name = "cli-vnet-lefr-01"
        creation_token = volume_name1
        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/subnet01" % (self.current_subscription(), rg, vnet_name)
        tag = "--tags '%s'" % tags if tags is not None else ""

        self.setup_vnet(rg, vnet_name)
        self.cmd("az netappfiles account create -g %s -a '%s' -l 'westus2'" % (rg, account_name)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l 'westus2' %s %s" % (rg, account_name, pool_name, POOL_DEFAULT, tag)).get_output_in_json()
        volume1 = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l 'westus2' %s --creation-token %s --subnet-id %s %s" % (rg, account_name, pool_name, volume_name1, VOLUME_DEFAULT, creation_token, subnet_id, tag)).get_output_in_json()

        return volume1

    @ResourceGroupPreparer()
    def test_list_mount_targets(self):
        account_name = "cli-acc-lefr-01"
        pool_name = "cli-pool-lefr-01"
        volume_name = "cli-volume-lefr-01"
        self.create_volume(account_name, pool_name, volume_name, '{rg}')

        volume_list = self.cmd("netappfiles mount-target list --resource-group {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(volume_list) == 1
