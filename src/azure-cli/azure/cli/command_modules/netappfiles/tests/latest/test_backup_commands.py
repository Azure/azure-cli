# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from knack.log import get_logger
import time
import unittest
LOCATION = "eastus"
VNET_LOCATION = "eastus"

logger = get_logger(__name__)

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

    def create_backup(self, account_name, pool_name, volume_name, backup_name, backup_vault_name,backup_only=False, vnet_name=None):
        tags = "Tag1=Value1 Tag2=vault1"            
        self.kwargs.update({
            'account_name': account_name,
            'location': LOCATION,
            'tags': tags,
            'vault_name': backup_vault_name,
            'backup_name': backup_name
        })
        if not backup_only:
            # create account, vault, pool and volume
            logger.warning('create account %s, group {rg} pool %s and volume %s', account_name, pool_name, volume_name)
            volume = self.create_volume(account_name, pool_name, volume_name, vnet_name=vnet_name)
            backup_vault = self.cmd("az netappfiles account backup-vault create -g {rg} -a {account_name} -n {vault_name} -l {location} --tags {tags}").get_output_in_json()
            # volume update with backup policy
            self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --backup-vault-id %s " %
                     (account_name, pool_name, volume_name, backup_vault['id']))
        
        volume = self.cmd("netappfiles volume show -g {rg} -a {account_name} -p {pool_name} -v {volume_name} ").get_output_in_json()
        # create backup
        logger.warning('create backup %s, group {rg} pool %s and volume %s, backup_vault %s backup_name %s', account_name, pool_name, volume_name, backup_vault_name, backup_name)
        return self.cmd("az netappfiles account backup-vault backup create -g {rg} -a {account_name} --backup-vault-name {vault_name} --backup-name {backup_name} --volume-resource-id %s" %
                        ( volume['id'])).get_output_in_json()

    def delete_backup(self, account_name, backup_vault_name, backup_name):
        logger.warning('delete backup, group {rg}, account_name %s, backup_vault %s backup_name %s', account_name, backup_vault_name, backup_name)
        # Delete
        self.cmd("az netappfiles account backup-vault backup delete -g {rg} -a %s -v %s --backup-name %s --yes" %
                 (account_name, backup_vault_name, backup_name))

    def wait_for_backup_created(self, account_name, backup_vault_name, backup_name):
        attempts = 0
        while attempts < 60:
            attempts += 1
            logger.warning('wait for backup created (%s) account: %s, backup_vault_name: %s and backup_name: %s', attempts, account_name, backup_vault_name,  backup_name)
            backup = self.cmd("netappfiles account backup-vault backup show -g {rg} -a %s --backup-vault-name %s -n %s" %
                              (account_name, backup_vault_name, backup_name)).get_output_in_json()
            if backup['provisioningState'] != "Creating":
                backup = self.cmd("netappfiles account backup-vault backup show -g {rg} -a %s --backup-vault-name %s -n %s" %
                (account_name, backup_vault_name, backup_name)).get_output_in_json()
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

    def wait_for_backup_initialized(self, account_name, pool_name, volume_name):
        attempts = 0
        while attempts < 60:
            attempts += 1
            #backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s -b %s" %
             #                 (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
            status = self.cmd("az netappfiles volume latest-backup-status current show -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
            if status['mirrorState'] != "Uninitialized":
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

    def wait_for_restore(self, account_name, pool_name, volume_name):
        attempts = 0
        while attempts < 60:
            attempts += 1
            #backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s -b %s" %
             #                 (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
            status = self.cmd("az netappfiles volume latest-restore-status current show -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
            if status['mirrorState'] != "Uninitialized":
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

    # @unittest.skip('(servicedeployment) Backups has been deprecated, new backup API is in 2023-05-01-preview -> netappfiles-preview extension')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })
            
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name)
        assert backup is not None
        #assert backup['id'] is not None
        self.wait_for_backup_created(account_name, vault_name, backup_name)
        volume = self.cmd("netappfiles volume show -g {rg} -a {account_name} -p {pool_name} -v {volume_name} ").get_output_in_json()
        self.kwargs.update({
            'volume_id': volume['id']
        })
        backup_list = self.cmd("netappfiles account backup-vault backup list -g {rg} -a {account_name} -v {vault_name} " ).get_output_in_json()
        assert len(backup_list) == 1
        
        # create second backup to test delete backup
        backup_name2 = self.create_random_name(prefix='cli-backup2-', length=24)        
        self.create_backup(account_name, pool_name, volume_name, backup_name2, vault_name, backup_only=True)
        self.wait_for_backup_created(account_name, vault_name, backup_name2)
        backup_list = self.cmd("netappfiles account backup-vault backup list -g {rg} -a {account_name} -v {vault_name} " ).get_output_in_json()
        assert len(backup_list) == 2

        # delete backup
        self.cmd("az netappfiles account backup-vault backup delete -g {rg} -a {account_name} -v {vault_name} --backup-name {first_backup_name} --yes" )
        backup_list = self.cmd("netappfiles account backup-vault backup list -g {rg} -a {account_name} -v {vault_name} " ).get_output_in_json()
        assert len(backup_list) == 1

        self.delete_backup(account_name, vault_name, backup_name2)

    # @unittest.skip('(servicedeployment) Backups has been deprecated, new backup API is in 2023-05-01-preview -> netappfiles-preview extension')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_list_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })
                 
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name)
        volume = self.cmd("netappfiles volume show -g {rg} -a {account_name} -p {pool_name} -v {volume_name} ").get_output_in_json()
        self.kwargs.update({
            'volume_id': volume['id']
        })
        backup_list = self.cmd("netappfiles account backup-vault backup list -g {rg} -a {account_name} -v {vault_name} " ).get_output_in_json()

        assert len(backup_list) == 1
        self.wait_for_backup_created(account_name, vault_name, backup_name)

        # create backup 2
        backup_name2 = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name2, vault_name, backup_only=True)

        backup_list = self.cmd("netappfiles account backup-vault backup list -g {rg} -a {account_name} -v {vault_name} " ).get_output_in_json()

        assert len(backup_list) == 2

        self.wait_for_backup_created(account_name, vault_name, backup_name2)
        self.cmd("az netappfiles account backup-vault backup delete -g {rg} -a {account_name} -v {vault_name} --backup-name {first_backup_name} --yes" )
        self.delete_backup(account_name, vault_name, backup_name2)

    # @unittest.skip('(servicedeployment) Backups has been deprecated, new backup API is in 2023-05-01-preview -> netappfiles-preview extension')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_get_backup_by_name(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name)

        # get backup and validate
        backup = self.cmd("netappfiles account backup-vault backup show -g {rg} -a {account_name} -v {vault_name} -b {backup_name}").get_output_in_json()
        assert backup is not None
        assert backup['name'] == account_name + "/" + vault_name +  "/" + backup_name

        # get backup by id and validate
        backup_from_id = self.cmd("az netappfiles account backup-vault backup show --ids %s" % backup['id']).get_output_in_json()
        assert backup_from_id['name'] == account_name + "/" + vault_name + "/" + backup_name

        self.wait_for_backup_created(account_name, vault_name, backup_name)
        self.delete_backup(account_name, vault_name, backup_name)

    # @unittest.skip('(servicedeployment) Backups has been deprecated, new backup API is in 2023-05-01-preview -> netappfiles-preview extension')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_update_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name)
        self.wait_for_backup_created(account_name, vault_name, backup_name)
        # update backup
        # tags = "Tag1=Value1 Tag2=Value2"
        label = "label"
        #not working due to bug in service side for PUT updates
        #self.cmd("netappfiles account backup-vault backup update -g {rg} -a {account_name} -v {vault_name} --backup-name {backup_name} --label %s" % "label" )

        # get backup and validate
        backup = self.cmd("az netappfiles account backup-vault backup show --ids %s" % backup['id']).get_output_in_json()
        assert backup is not None
        assert backup['name'] == account_name + "/" + vault_name + "/" + backup_name
        assert backup['id'] is not None
        # there is a bug in update where the label is not updated - will be fixed later
        # assert backup['label'] == label

        self.wait_for_backup_created(account_name, vault_name, backup_name)
        self.delete_backup(account_name, vault_name, backup_name)

    # @unittest.skip('(servicedeployment) Backups has been deprecated, new backup API is in 2023-05-01-preview -> netappfiles-preview extension')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_disable_backup_for_volume(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name)
        self.wait_for_backup_created(account_name, vault_name, backup_name)
        
        backupVault = self.cmd("az netappfiles account backup-vault show -g {rg} -a {account_name} -n {vault_name}").get_output_in_json()
        
        volume = self.cmd("netappfiles volume show -g {rg} -a {account_name} -p {pool_name} -v {volume_name} ").get_output_in_json()
        logger.warning('Check updated  volume %s', volume)
        assert volume['dataProtection']['backup']['backupVaultId'] is not None
        assert volume['dataProtection']['backup']['backupVaultId'] == backupVault['id']
        
        self.delete_backup(account_name, vault_name, backup_name)
        # volume update
        volume = self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --backup-vault-id=null" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
        
        logger.warning('Check updated volume removed backupvaultid %s', volume)
        #assert not volume['dataProtection']['backup']['backupvaultid']
        assert 'backupVaultId' not in volume['dataProtection']['backup']

    # @unittest.skip('(servicedeployment) Error in service skip until fixed')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_restore_backup_to_new_volume(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vnet_name = self.create_random_name(prefix='cli-vnet-backup', length=24)

        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name, vnet_name=vnet_name)
        self.wait_for_backup_created(account_name, vault_name, backup_name)
        self.wait_for_backup_initialized(account_name, pool_name, volume_name)

        backup = self.cmd("netappfiles account backup-vault backup show -g {rg} -a {account_name} -v {vault_name} --backup-name {backup_name}").get_output_in_json()
        assert backup['provisioningState'] == "Succeeded"        
        # create new volume and restore backup
        volume2_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.create_volume(account_name, pool_name, volume2_name, volume_only=True, backup_id=backup['id'],
                           vnet_name=vnet_name)

        volume2 = self.cmd("netappfiles volume show -g {rg} -a %s -p %s -v %s" %
                           (account_name, pool_name, volume2_name)).get_output_in_json()

        #assert volume2['dataProtection']['backup']['backupEnabled']
        assert volume2['provisioningState'] == "Succeeded"
        if self.is_live or self.in_recording:
            time.sleep(60)
        #self.wait_for_backup_created(account_name, vault_name, backup_name)
        # There is an issue in generated code with deserializing this singleton GET, it will try to deserialize as list, remove comment when fixed
        # self.wait_for_restore(account_name, pool_name, volume2_name)
        if self.is_live or self.in_recording:
            time.sleep(120)

        self.delete_backup(account_name, vault_name, backup_name)

    # @unittest.skip('(servicedeployment) Backups has been deprecated, new backup API is in 2023-05-01-preview -> netappfiles-preview extension')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_', additional_tags={'owner': 'cli_test'})
    def test_get_backup_status(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        vnet_name = self.create_random_name(prefix='cli-vnet-backup', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,
            'pool_name': pool_name,
            'volume_name': volume_name,
            'location': LOCATION,            
            'vault_name': vault_name,
            'first_backup_name': backup_name
        })        
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name, vault_name, vnet_name=vnet_name)
        self.wait_for_backup_created(account_name, vault_name, backup_name)

        status = self.cmd("az netappfiles volume latest-backup-status current show -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
        # assert status['mirrorState'] == "Uninitialized"

        self.wait_for_backup_created(account_name, vault_name, backup_name)
        self.wait_for_backup_initialized(account_name, pool_name, volume_name)

        status = self.cmd("az netappfiles volume latest-backup-status current show -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
        assert status['mirrorState'] == "Mirrored"
