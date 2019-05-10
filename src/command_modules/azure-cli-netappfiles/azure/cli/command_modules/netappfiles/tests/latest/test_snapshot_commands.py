# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

POOL_DEFAULT = "--service-level 'Premium' --size 4398046511104"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 107374182400"

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesSnapshotServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s --resource-group %s -l westcentralus --address-prefix 10.5.0.0/16" % (vnet_name, rg))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' --delegations 'Microsoft.Netapp/volumes' -g %s" % (subnet_name, vnet_name, rg))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        creation_token = volume_name1
        subnet_name = "subnet02"
        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (self.current_subscription(), rg, vnet_name, subnet_name)
        tag = "--tags '%s'" % tags if tags is not None else ""

        self.setup_vnet(rg, vnet_name, subnet_name)
        self.cmd("netappfiles account create -g %s -a '%s' -l 'westcentralus'" % (rg, account_name)).get_output_in_json()
        self.cmd("netappfiles pool create -g %s -a %s -p %s -l 'westcentralus' %s %s" % (rg, account_name, pool_name, POOL_DEFAULT, tag)).get_output_in_json()
        volume1 = self.cmd("netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l 'westcentralus' %s --creation-token %s --subnet-id %s %s" % (rg, account_name, pool_name, volume_name1, VOLUME_DEFAULT, creation_token, subnet_id, tag)).get_output_in_json()

        return volume1

    @ResourceGroupPreparer()
    def test_create_delete_snapshots(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        rg = '{rg}'

        volume = self.create_volume(account_name, pool_name, volume_name, rg)
        snapshot = self.cmd("az netappfiles snapshot create -g %s -a %s -p %s -v %s -s %s -l 'westcentralus' --file-system-id %s" % (rg, account_name, pool_name, volume_name, snapshot_name, volume['fileSystemId'])).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name

        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

        self.cmd("az netappfiles snapshot delete -g %s -a %s -p %s -v %s -s %s" % (rg, account_name, pool_name, volume_name, snapshot_name))
        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 0

    @ResourceGroupPreparer()
    def test_list_snapshots(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name1 = self.create_random_name(prefix='cli-sn-', length=24)
        snapshot_name2 = self.create_random_name(prefix='cli-sn-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l 'westcentralus' --file-system-id %s" % (account_name, pool_name, volume_name, snapshot_name1, volume['fileSystemId'])).get_output_in_json()
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l 'westcentralus' --file-system-id %s" % (account_name, pool_name, volume_name, snapshot_name2, volume['fileSystemId'])).get_output_in_json()

        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 2

    @ResourceGroupPreparer()
    def test_get_snapshot(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        snapshot = self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l 'westcentralus' --file-system-id %s" % (account_name, pool_name, volume_name, snapshot_name, volume['fileSystemId'])).get_output_in_json()

        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" % (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name

        snapshot_from_id = self.cmd("az netappfiles snapshot show --ids %s" % snapshot['id']).get_output_in_json()
        assert snapshot_from_id['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
