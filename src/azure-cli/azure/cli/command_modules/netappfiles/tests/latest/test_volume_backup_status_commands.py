# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest

LOCATION = "eastus2euap"
VNET_LOCATION = "southcentralus"
VNET_NAME = "cli-vnet-backup-status"
BACKUP_POLICY_NAME = "cli-bp-pol-bp-status"


@unittest.skip("Backup unstable so these tests need to be skipped for this version")
class AzureNetAppFilesVolumeBackupStatusServiceScenarioTest(ScenarioTest):
    def setup_vnet(self):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (VNET_NAME, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n default --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % VNET_NAME)

    def get_vaults(self, account_name):
        return self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()

    def create_volume(self, account_name, pool_name, volume_name, backup_id=None):
        # create vnet, account and pool
        self.setup_vnet()
        self.cmd("netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()
        self.cmd("netappfiles pool create -g {rg} -a %s -p %s -l %s --service-level 'Premium' --size 4" %
                 (account_name, pool_name, LOCATION)).get_output_in_json()

        # create volume
        return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s --vnet %s --subnet %s "
                        "--file-path %s --usage-threshold 100" %
                        (account_name, pool_name, volume_name, LOCATION, VNET_NAME, 'default', volume_name)).get_output_in_json()

    def create_backup(self, account_name, pool_name, volume_name, backup_name):
        self.create_volume(account_name, pool_name, volume_name)

        # get vault
        vaults = self.get_vaults(account_name)

        # create backup policy
        backup_policy = self.cmd("az netappfiles account backup-policy create -g {rg} -a %s "
                                 "--backup-policy-name %s -l %s --daily-backups 1 --enabled true" %
                                 (account_name, BACKUP_POLICY_NAME, LOCATION)).get_output_in_json()

        # volume update with backup policy
        self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s "
                 "--backup-policy-id %s --policy-enforced %s" % (account_name, pool_name, volume_name, vaults[0]['id'],
                                                                 True, backup_policy['id'], True)).get_output_in_json()

        # create backup
        return self.cmd("az netappfiles volume backup create -g {rg} -a %s -p %s -v %s -l %s --backup-name %s" %
                        (account_name, pool_name, volume_name, LOCATION, backup_name)).get_output_in_json()

    def delete_backup(self, account_name, pool_name, volume_name):
        vaults = self.get_vaults(account_name)

        backup_policy = self.cmd("az netappfiles account backup-policy get -g {rg} -a %s --backup-policy-name %s" %
                                 account_name, BACKUP_POLICY_NAME).get_output_in_json()

        # Delete
        self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s "
                 "--backup-policy-id %s" %
                 (account_name, pool_name, volume_name, vaults[0]['id'], False, backup_policy['id']))
        self.cmd("az netappfiles account backup-policy delete -g {rg} -a %s --backup-policy-name %s" %
                 (account_name, BACKUP_POLICY_NAME))

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_vault_')
    def test_get_volume_backup_status(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        status = self.cmd("az netappfiles volume backup status show -g {rg} -a %s" % account_name).get_output_in_json()
        assert status['healthy'] is True

        self.delete_backup(account_name, pool_name, volume_name)
