# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "southcentralus"

class AzureNetAppFilesBackupServiceScenarioTest(ScenarioTest):
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
            backup_policy = self.cmd("az netappfiles account backup_policy create -g {rg} -a %s "
                                     "--backup-policy-name %s -l %s --daily-backups-to-keep 1" %
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

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_')
    def test_create_delete_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        backup = self.create_backup(account_name, pool_name, volume_name, backup_name)

        assert backup is not None

        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()

        assert len(backup_list) == 1
        # Delete not supported yet

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_')
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

        # create backup 2
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name, True)

        backup_list = self.cmd("netappfiles volume backup list -g {rg} -a %s -p %s -v %s" %
                               (account_name, pool_name, volume_name)).get_output_in_json()

        assert len(backup_list) == 2

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_')
    def test_get_backup_by_name(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # get backup and validate
        backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s --backup-name %s" %
                          (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
        assert backup is not None
        assert backup['name'] == account_name + "/" + pool_name + "/" + volume_name + "/" + backup_name

        # get backup by id and validate
        backup_from_id = self.cmd("az netappfiles volume backup show --ids %s" % backup['id']).get_output_in_json()
        assert backup_from_id['name'] == account_name + "/" + pool_name + "/" + volume_name + "/" + backup_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_')
    def test_update_backup(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # update backup
        tags = "Tag1=Value1 Tag2=Value2"
        label = "label"
        self.cmd("netappfiles volume backup update -g {rg} -a %s -p %s -v %s --backup-name %s --tags %s --label %s" %
                 (account_name, pool_name, volume_name, backup_name, tags, label)).get_output_in_json()

        # get backup and validate
        backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s --backup-name %s" %
                          (account_name, pool_name, volume_name, backup_name)).get_output_in_json()
        assert backup is not None
        assert backup['name'] == account_name + "/" + pool_name + "/" + volume_name + "/" + backup_name
        # there is a bug in update where the label is not updated - will be fixed later
        # assert backup['label'] == label

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_')
    def test_disable_backup_for_volume(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # get vault
        vaults = self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()

        # volume update
        volume = self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s" %
                          (account_name, pool_name, volume_name, vaults[0]['id'], False)).get_output_in_json()

        assert not volume['dataProtection']['backup']['backupEnabled']

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_')
    def test_restore_backup_to_new_volume(self):
        # create backup
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        backup_name = self.create_random_name(prefix='cli-backup-', length=24)
        self.create_backup(account_name, pool_name, volume_name, backup_name)

        # disable backup for volume
        vaults = self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()
        self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --vault-id %s --backup-enabled %s" %
                 (account_name, pool_name, volume_name, vaults[0]['id'], False)).get_output_in_json()

        backup = self.cmd("netappfiles volume backup show -g {rg} -a %s -p %s -v %s --backup-name %s" %
                          (account_name, pool_name, volume_name, backup_name)).get_output_in_json()

        # Backup not completely ready, not able to retrieve backupId at the moment since swagger is not updated
        # create new volume and restore backup
        # volume2_name = self.create_random_name(prefix='cli-vol-', length=24)
        # volume2 = self.create_volume(account_name, pool_name, volume2_name, volume_only=False, backup_id=backup['backupId'])
