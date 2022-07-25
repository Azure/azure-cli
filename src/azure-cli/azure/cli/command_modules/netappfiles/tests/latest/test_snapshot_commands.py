# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test
from knack.util import CLIError

POOL_DEFAULT = "--service-level 'Premium' --size 4"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 100"
LOCATION = "southcentralusstage"
VNET_LOCATION = "southcentralus"

# No tidy up of tests required. The resource group is automatically removed

# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer


class AzureNetAppFilesSnapshotServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (subnet_name, vnet_name))

    def create_volume(self, account_name, pool_name, volume_name1, tags=None, snapshot_id=None, volume_only=False):
        file_path = volume_name1  # creation_token
        vnet_name = "cli-vnet-lefr-02"
        subnet_name = "cli-subnet-lefr-02"
        tag = "--tags %s" % tags if tags is not None else ""

        if not volume_only:
            self.setup_vnet(vnet_name, subnet_name)
            self.cmd("netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION))
            self.cmd("netappfiles pool create -g {rg} -a %s -p %s -l %s %s %s" %
                     (account_name, pool_name, LOCATION, POOL_DEFAULT, tag))

        if snapshot_id:
            return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s %s --file-path %s --vnet %s "
                            "--subnet %s %s --snapshot-id %s" %
                            (account_name, pool_name, volume_name1, LOCATION, VOLUME_DEFAULT, file_path, vnet_name,
                             subnet_name, tag, snapshot_id)).get_output_in_json()
        else:
            return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s %s --file-path %s --vnet %s "
                            "--subnet %s %s" % (account_name, pool_name, volume_name1, LOCATION, VOLUME_DEFAULT,
                                                file_path, vnet_name, subnet_name, tag)).get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_snapshots(self):
        # create volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create snapshot
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        snapshot = self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s " %
                            (account_name, pool_name, volume_name, snapshot_name, LOCATION)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        assert snapshot['created'] is not None
        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" %
                                 (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

        # delete snapshot
        self.cmd("az netappfiles snapshot delete -g {rg} -a %s -p %s -v %s -s %s" %
                 (account_name, pool_name, volume_name, snapshot_name))
        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" %
                                 (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', additional_tags={'owner': 'cli_test'})
    def test_create_volume_from_snapshot(self):
        # create volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create snapshot
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        snapshot = self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" %
                            (account_name, pool_name, volume_name, snapshot_name, LOCATION)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        assert snapshot['created'] is not None
        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" %
                                 (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

        # create second volume and restore from snapshot
        restored_volume_name = self.create_random_name(prefix='cli-sn-2', length=24)
        volume_only = True
        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" %
                            (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        restored_volume = self.create_volume(account_name, pool_name, restored_volume_name,
                                             snapshot_id=snapshot["snapshotId"], volume_only=volume_only)
        assert restored_volume['name'] == account_name + '/' + pool_name + '/' + restored_volume_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', additional_tags={'owner': 'cli_test'})
    def test_revert_volume_from_snapshot(self):
        # create volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create snapshot
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        snapshot = self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" %
                            (account_name, pool_name, volume_name, snapshot_name, LOCATION)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name
        assert snapshot['created'] is not None
        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" %
                                 (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

        # revert volume to snapshot
        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" %
                            (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        self.cmd("az netappfiles volume revert -g {rg} -a %s -p %s -v %s -s %s" %
                 (account_name, pool_name, volume_name, snapshot["snapshotId"]))
        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" %
                                 (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 1

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', additional_tags={'owner': 'cli_test'})
    def test_list_snapshots(self):
        # create volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create 2 snapshots
        snapshot_name1 = self.create_random_name(prefix='cli-sn-', length=24)
        snapshot_name2 = self.create_random_name(prefix='cli-sn-', length=24)
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" %
                 (account_name, pool_name, volume_name, snapshot_name1, LOCATION)).get_output_in_json()
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" %
                 (account_name, pool_name, volume_name, snapshot_name2, LOCATION)).get_output_in_json()

        snapshot_list = self.cmd("az netappfiles snapshot list -g {rg} -a %s -p %s -v %s" %
                                 (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(snapshot_list) == 2

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', additional_tags={'owner': 'cli_test'})
    def test_get_snapshot(self):
        # create volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create snapshot
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" %
                 (account_name, pool_name, volume_name, snapshot_name, LOCATION))

        # get snapshot
        snapshot = self.cmd("az netappfiles snapshot show -g {rg} -a %s -p %s -v %s -s %s" %
                            (account_name, pool_name, volume_name, snapshot_name)).get_output_in_json()
        assert snapshot['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name

        # get snapshot from id
        snapshot_from_id = self.cmd("az netappfiles snapshot show --ids %s" % snapshot['id']).get_output_in_json()
        assert snapshot_from_id['name'] == account_name + '/' + pool_name + '/' + volume_name + '/' + snapshot_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_', additional_tags={'owner': 'cli_test'})
    def test_restore_file_returns_not_found(self):
        # create volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume = self.create_volume(account_name, pool_name, volume_name)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create snapshot
        snapshot_name = self.create_random_name(prefix='cli-sn-', length=24)
        self.cmd("az netappfiles snapshot create -g {rg} -a %s -p %s -v %s -s %s -l %s" %
                 (account_name, pool_name, volume_name, snapshot_name, LOCATION))

        snapshot_file_path = "'/snap_file_path_1.txt' '/snap_file_path_2.txt'"

        with self.assertRaisesRegex(CLIError, "The specified filePath /snap_file_path_1.txt does not exist"):
            self.cmd("az netappfiles snapshot restore-files -g {rg} -a %s -p %s -v %s -s %s --file-paths %s" %
                     (account_name, pool_name, volume_name, snapshot_name, snapshot_file_path))
