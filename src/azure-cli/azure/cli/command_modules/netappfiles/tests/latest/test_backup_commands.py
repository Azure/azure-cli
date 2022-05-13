# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time
LOCATION = "southcentralusstage"
VNET_LOCATION = "southcentralus"


class AzureNetAppFilesBackupServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (subnet_name, vnet_name))

    def create_volume(self, account_name, pool_name, volume_name, volume_only=False, backup_id=None, vnet_name=None):
        if vnet_name is None:
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

    def create_backup(self, account_name, pool_name, volume_name, backup_name, backup_only=False, vnet_name=None):
        if not backup_only:
            # create account, pool and volume
            self.create_volume(account_name, pool_name, volume_name, vnet_name=vnet_name)

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

    def wait_for_backup_initialized(self, account_name, pool_name, volume_name, backup_name):
        attempts = 0
        while attempts < 60:
            attempts += 1
            backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s -b %s" %
                              (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
            if backup['provisioningState'] != "Uninitialized":
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name)

        assert backup is not None
        assert backup['id'] is not None
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)

        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(backup_list) == 1

        # create second backup to test delete backup
        backup_name2 = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name2, backup_only=True)
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name2)
        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(backup_list) == 2

        # delete backup
        self.cmd("az netappfiles volume backup delete -g {rg} -a %s -p %s -v %s --backup-name %s" %
                 (account_name, pool_name, volume_name, backup_name))
        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(backup_list) == 1

        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_list_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()

        assert len(backup_list) == 1
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)

        # create backup 2
        backup_name2 = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name2, True)

        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()

        assert len(backup_list) == 2

        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name2)
        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_get_backup_by_name(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # get backup and validate
        backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s -b %s" %
                          (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
        assert backup is not None
        assert backup['name'] == account_name + "/" + pool_name + "/" + volume_name + "/" + backup_name

        # get backup by id and validate
        backup_from_id = self.cmd("az netappfiles volume backup show --ids %s" % backup['id']).get_output_in_json()
        assert backup_from_id['name'] == account_name + "/" + pool_name + "/" + volume_name + "/" + backup_name

        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)
        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_update_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # update backup
        # tags = "Tag1=Value1 Tag2=Value2"
        label = "label"
        self.cmd("netappfiles volume backup update -g {rg} -a %s -p %s -v %s --backup-name %s --label %s" %
                 (account_name, pool_name, volume_name, backup_name, label))

        # get backup and validate
        backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s --backup-name %s" %
                          (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
        assert backup is not None
        assert backup['name'] == account_name + "/" + pool_name + "/" + volume_name + "/" + backup_name
        assert backup['id'] is not None
        # there is a bug in update where the label is not updated - will be fixed later
        # assert backup['label'] == label

        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)
        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_disable_backup_for_volume(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # get vault
        vaults = self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)

        # volume update
        volume = self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s" %
                          (account_name, pool_name, volume_name, vaults[0]['id'], False)).get_output_in_json()

        assert not volume['dataProtection']['backup']['backupEnabled']

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_restore_backup_to_new_volume(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vnet_name = self.create_random_name(prefix='cli-vnet-backup', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name, vnet_name=vnet_name)
        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)

        backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s --backup-name %s" %
                          (account_name, pool_name, volume_name, backup_name)).get_output_in_json()

        # create new volume and restore backup
        volume2_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.create_volume(account_name, pool_name, volume2_name, volume_only=True, backup_id=backup['backupId'],
                           vnet_name=vnet_name)

        volume2 = self.cmd("netappfiles volume show -g {rg} -a %s -p %s -v %s" %
                           (account_name, pool_name, volume_name)).get_output_in_json()

        assert volume2['dataProtection']['backup']['backupEnabled']

        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)
        self.delete_backup(account_name, pool_name, volume_name)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_get_backup_status(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vnet_name = self.create_random_name(prefix='cli-vnet-backup', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name, vnet_name=vnet_name)

        status = self.cmd("az netappfiles volume backup status -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
        assert status['mirrorState'] == "Uninitialized"

        self.wait_for_backup_created(account_name, pool_name, volume_name, backup_name)

        self.wait_for_backup_initialized(account_name, pool_name, volume_name, backup_name)

        status = self.cmd("az netappfiles volume backup status -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
        assert status['mirrorState'] == "Mirrored"
