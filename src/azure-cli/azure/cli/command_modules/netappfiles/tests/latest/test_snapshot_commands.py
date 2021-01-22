# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test

POOL_DEFAULT = "--service-level 'Premium' --size 4"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 100"
RG_LOCATION = "westus2"
ANF_LOCATION = "westus2"

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesSnapshotServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s --resource-group %s -l %s --address-prefix 10.5.0.0/16" % (vnet_name, rg, RG_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' --delegations 'Microsoft.Netapp/volumes' -g %s" % (subnet_name, vnet_name, rg))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None, snapshot_id=None, volume_only=False):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        file_path = volume_name1  # creation_token
        vnet_name = "cli-vnet-lefr-02"
        subnet_name = "cli-subnet-lefr-02"
        tag = "--tags %s" % tags if tags is not None else ""

        if not volume_only:
            self.setup_vnet(rg, vnet_name, subnet_name)
            self.cmd("netappfiles account create -g %s -a '%s' -l %s" % (rg, account_name, ANF_LOCATION)).get_output_in_json()
            self.cmd("netappfiles pool create -g %s -a %s -p %s -l %s %s %s" % (rg, account_name, pool_name, ANF_LOCATION, POOL_DEFAULT, tag)).get_output_in_json()

        if snapshot_id:
            volume1 = self.cmd("netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s %s --snapshot-id %s" % (rg, account_name, pool_name, volume_name1, ANF_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_name, tag, snapshot_id)).get_output_in_json()
        else:
            volume1 = self.cmd("netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s %s" % (rg, account_name, pool_name, volume_name1, ANF_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_name, tag)).get_output_in_json()

        return volume1

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_')
    def test_create_delete_snapshots(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        rg = '{rg}'

        volume = self.create_volume(account_name, pool_name, volume_name, rg)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        snapshot = self.cmd("az netappfiles snapshot create -g %s -a %s -p %s -v %s -s %s -l %s " % (rg, account_name, pool_name, volume_name, snapshot_name, ANF_LOCATION)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        # check the created fields is populated. Checking exact dates are a little harder due to session records
        assert snapshot['created'] is not None

        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

        self.cmd("az netappfiles snapshot delete -g %s -a %s -p %s -v %s -s %s" % (rg, account_name, pool_name, volume_name, snapshot_name))
        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 0

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netapp_test_snap_')
    def test_create_volume_from_snapshot(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        restored_volume_name = self.create_random_name(prefix='cli-vol-restored', length=24)
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        restored_volume_name = self.create_random_name(prefix='cli-sn-2', length=24)
        rg = '{rg}'

        volume = self.create_volume(account_name, pool_name, volume_name, rg)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        snapshot = self.cmd("az netappfiles snapshot create -g %s -a %s -p %s -v %s -s %s -l %s" % (rg, account_name, pool_name, volume_name, snapshot_name, ANF_LOCATION)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        # check the created fields is populated. Checking exact dates are a little harder due to session records
        assert snapshot['created'] is not None

        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1
        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" % (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        volume_only = True
        restored_volume = self.create_volume(account_name, pool_name, restored_volume_name, rg, snapshot_id=snapshot["snapshotId"], volume_only=volume_only)
        assert restored_volume['name'] == account_name + '/' + pool_name + '/' + restored_volume_name

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', parameter_name='rg', random_name_length=63)
    def test_revert_volume_from_snapshot(self, rg):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)

        volume = self.create_volume(account_name, pool_name, volume_name, rg)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        snapshot = self.cmd("az netappfiles snapshot create -g %s -a %s -p %s -v %s -s %s -l %s" % (rg, account_name, pool_name, volume_name, snapshot_name, ANF_LOCATION)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        # check the created fields is populated. Checking exact dates are a little harder due to session records
        assert snapshot['created'] is not None

        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1
        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" % (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        volume = self.cmd("az netappfiles volume revert --resource-group {rg} -a %s -p %s -v %s -s %s" % (account_name, pool_name, volume_name, snapshot["snapshotId"]))
        snapshot_list = self.cmd("az netappfiles snapshot list --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_')
    def test_list_snapshots(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name1 = self.create_random_name(prefix='cli-sn-', length=24)
        snapshot_name2 = self.create_random_name(prefix='cli-sn-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" % (account_name, pool_name, volume_name, snapshot_name1, ANF_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" % (account_name, pool_name, volume_name, snapshot_name2, ANF_LOCATION)).get_output_in_json()

        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 2

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_')
    def test_get_snapshot(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        snapshot = self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" % (account_name, pool_name, volume_name, snapshot_name, ANF_LOCATION)).get_output_in_json()

        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" % (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name

        snapshot_from_id = self.cmd("az netappfiles snapshot show --ids %s" % snapshot['id']).get_output_in_json()
        assert snapshot_from_id['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
