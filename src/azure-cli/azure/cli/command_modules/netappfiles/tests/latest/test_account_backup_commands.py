# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest

LOCATION = "southcentralus"

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesAccountBackupServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (vnet_name, LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (subnet_name, vnet_name))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name, volume_only=False, backup_id=None):
        vnet_name = self.create_random_name(prefix='cli-vnet-backup', length=24)
        subnet_name = "default"

        if not volume_only:
            # create vnet, account and pool
            self.setup_vnet(vnet_name, subnet_name)
            self.cmd("netappfiles account create -g {rg} -a '%s' -l %s" %
                     (account_name, LOCATION)).get_output_in_json()
            self.cmd("netappfiles pool create -g {rg} -a %s -p %s -l %s --service-level 'Premium' --size 4" %
                     (account_name, pool_name, LOCATION)).get_output_in_json()

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
            vaults = self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()

            # create backup policy
            backup_policy_name = self.create_random_name(prefix='cli-sn-pol-', length=16)
            backup_policy = self.cmd("az netappfiles account backup-policy create -g {rg} -a %s "
                                     "--backup-policy-name %s -l %s --daily-backups 1" %
                                     (account_name, backup_policy_name, LOCATION)).get_output_in_json()

            # volume update with backup policy
            self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s "
                     "--backup-policy-id %s --policy-enforced %s" %
                     (account_name, pool_name, volume_name, vaults[0]['id'], True, backup_policy['id'], True)) \
                .get_output_in_json()

        # create backup
        backup = self.cmd("az netappfiles volume backup create -g {rg} -a %s -p %s -v %s -l %s --backup-name %s" %
                          (account_name, pool_name, volume_name, LOCATION, backup_name)).get_output_in_json()
        return backup

    @unittest.skip("This function is not working as expected. Waiting on a fix.")
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_backup_')
    def test_get_account_backups(self):
        raise unittest.SkipTest("Skipping - Not working properly. Backup not found error.")
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        backup = self.cmd("az netappfiles account backup show -g {rg} -a %s --backup-name %s" %
                          (account_name, backup_name)).get_output_in_json()

        assert backup['name'] == backup_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_backup_')
    def test_list_account_backups(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        backup_list = self.cmd("az netappfiles account backup list -g {rg} -a %s" % account_name).get_output_in_json()

        assert len(backup_list) == 1
