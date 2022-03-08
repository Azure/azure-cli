# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time
import unittest
LOCATION = "southcentralusstage"
VNET_LOCATION = "southcentralus"

# No tidy up of tests required. The resource group is automatically removed

# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer

@unittest.skip("showing class skipping")
class AzureNetAppFilesAccountBackupServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (subnet_name, vnet_name))

    def create_volume(self, account_name, pool_name, volume_name, volume_only=False, backup_id=None):
        vnet_name = self.create_random_name(prefix='cli-vnet-backup', length=24)
        subnet_name = "default"

        if not volume_only:
            # create vnet, account and pool
            self.setup_vnet(vnet_name, subnet_name)
            self.cmd("netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION))
            self.cmd("netappfiles pool create -g {rg} -a %s -p %s -l %s --service-level 'Premium' --size 4" %
                     (account_name, pool_name, LOCATION))

        # create volume
        if backup_id is None:
            return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s --vnet %s --subnet %s "
                            "--file-path %s --usage-threshold 100" %
                            (account_name, pool_name, volume_name, LOCATION, vnet_name, subnet_name, volume_name)
                            ).get_output_in_json()
        else:
            return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s --vnet %s --subnet %s "
                            "--file-path %s --usage-threshold 100 --backup-id %s" %
                            (account_name, pool_name, volume_name, LOCATION, vnet_name, subnet_name, volume_name,
                             backup_id)).get_output_in_json()

    def create_backup(self, account_name, pool_name, volume_name, backup_name, backup_only=False):
        if not backup_only:
            # create account, pool and volume
            self.create_volume(account_name, pool_name, volume_name)

            # get vault
            vaults = self.get_vaults(account_name)

            # volume update with backup policy
            self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s " %
                     (account_name, pool_name, volume_name, vaults[0]['id'], True))

        # create backup
        return self.cmd("az netappfiles volume backup create -g {rg} -a %s -p %s -v %s -l %s --backup-name %s" %
                        (account_name, pool_name, volume_name, LOCATION, backup_name)).get_output_in_json()

    def delete_backup(self, account_name, pool_name, volume_name):
        vaults = self.get_vaults(account_name)

        # Delete
        self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s " %
                 (account_name, pool_name, volume_name, vaults[0]['id'], False))

    def get_vaults(self, account_name):
        return self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()

    def wait_for_backup_created(self, account_name, pool_name, volume_name, backup_name):
        attempts = 0
        while attempts < 40:
            attempts += 1
            backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s -b %s" %
                              (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
            if backup['provisioningState'] != "Creating":
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_backup_', additional_tags={'owner': 'cli_test'})
    def test_list_account_backups(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # assert backup is returned in list account backups
        backup_list = self.cmd("az netappfiles account backup list -g {rg} -a %s" % account_name).get_output_in_json()
        assert backup_list[len(backup_list) - 1]['name'] == account_name + "/" + backup_name

        # clean up
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)
        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_backup_', additional_tags={'owner': 'cli_test'})
    def test_get_account_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # assert backup is returned in show account backup
        backup = self.cmd("az netappfiles account backup show -g {rg} -a %s --backup-name %s" %
                          (account_name, backup_name)).get_output_in_json()
        assert backup['name'] == account_name + "/" + backup_name

        # clean up
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)
        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_backup_', additional_tags={'owner': 'cli_test'})
    def test_delete_account_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # make sure the backup is created
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)
        backup_list = self.cmd("az netappfiles account backup list -g {rg} -a %s" % account_name).get_output_in_json()
        assert backup_list[len(backup_list) - 1]['name'] == account_name + "/" + backup_name

        # delete volume first to be able to call delete account backup
        self.cmd("az netappfiles volume delete -g {rg} -a %s -p %s -v %s" %
                 (account_name, pool_name, volume_name))
        self.cmd("az netappfiles account backup delete -g {rg} -a %s --backup-name %s -y" % (account_name, backup_name))

        # assert the account backup is deleted
        backup_list = self.cmd("az netappfiles account backup list -g {rg} -a %s" % account_name).get_output_in_json()
        for backup in backup_list:
            assert backup['name'] != account_name + "/" + backup_name
