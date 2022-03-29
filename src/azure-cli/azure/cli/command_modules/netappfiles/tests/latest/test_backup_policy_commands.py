# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "southcentralusstage"

# No tidy up of tests required. The resource group is automatically removed

# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer


class AzureNetAppFilesBackupPolicyServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_policy_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_backup_policies(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create backup policy using long parameter names and validate result
        backup_policy_name = self.create_random_name(prefix='cli-ba-pol-', length=16)
        daily_backups_to_keep = 1
        weekly_backups_to_keep = 2
        monthly_backups_to_keep = 3
        enabled = True
        tags = "Tag1=Value1 Tag2=Value2"
        backup_policy = self.cmd("az netappfiles account backup-policy create -g {rg} -a %s --backup-policy-name %s "
                                 "--location %s --daily-backups %s --weekly-backups %s "
                                 "--monthly-backups %s --enabled %s --tags %s" %
                                 (account_name, backup_policy_name, LOCATION, daily_backups_to_keep,
                                  weekly_backups_to_keep, monthly_backups_to_keep, enabled, tags)).get_output_in_json()
        assert backup_policy['name'] == account_name + "/" + backup_policy_name
        assert backup_policy['dailyBackupsToKeep'] == daily_backups_to_keep
        assert backup_policy['weeklyBackupsToKeep'] == weekly_backups_to_keep
        assert backup_policy['monthlyBackupsToKeep'] == monthly_backups_to_keep
        assert backup_policy['enabled'] == enabled
        assert backup_policy['tags']['Tag1'] == 'Value1'
        assert backup_policy['tags']['Tag2'] == 'Value2'
        assert backup_policy['etag'] is not None
        assert backup_policy['backupPolicyId'] is not None

        # validate backup policy exist
        backup_policy_list = self.cmd("az netappfiles account backup-policy list -g {rg} -a '%s'" %
                                      account_name).get_output_in_json()
        assert len(backup_policy_list) == 1

        # delete backup policy
        self.cmd("az netappfiles account backup-policy delete -g {rg} -a %s --backup-policy-name %s" %
                 (account_name, backup_policy_name))

        # create backup policy using short parameter names and validate result
        backup_policy = self.cmd("az netappfiles account backup-policy create -g {rg} -a %s -b %s "
                                 "-l %s -d %s -w %s -m %s -e %s --tags %s" %
                                 (account_name, backup_policy_name, LOCATION, daily_backups_to_keep,
                                  weekly_backups_to_keep, monthly_backups_to_keep, enabled, tags)).get_output_in_json()
        assert backup_policy['name'] == account_name + "/" + backup_policy_name
        assert backup_policy['dailyBackupsToKeep'] == daily_backups_to_keep
        assert backup_policy['weeklyBackupsToKeep'] == weekly_backups_to_keep
        assert backup_policy['monthlyBackupsToKeep'] == monthly_backups_to_keep
        assert backup_policy['enabled'] == enabled
        assert backup_policy['tags']['Tag1'] == 'Value1'
        assert backup_policy['tags']['Tag2'] == 'Value2'

        # delete backup policy
        self.cmd("az netappfiles account backup-policy delete -g {rg} -a %s --backup-policy-name %s" %
                 (account_name, backup_policy_name))

        # validate backup policy doesn't exist
        backup_policy_list = self.cmd("az netappfiles account backup-policy list -g {rg} -a '%s'" %
                                      account_name).get_output_in_json()
        assert len(backup_policy_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_policy_', additional_tags={'owner': 'cli_test'})
    def test_list_backup_policy(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create 3 backup policies
        backup_policies = [self.create_random_name(prefix='cli', length=16),
                           self.create_random_name(prefix='cli', length=16),
                           self.create_random_name(prefix='cli', length=16)]
        for backup_policy_name in backup_policies:
            self.cmd("az netappfiles account backup-policy create -g {rg} -a %s --backup-policy-name %s -l %s "
                     "--daily-backups 1 --enabled true" % (account_name, backup_policy_name, LOCATION))

        # validate that both backup policies exist
        backup_policy_list = self.cmd("az netappfiles account backup-policy list -g {rg} -a '%s'" %
                                      account_name).get_output_in_json()
        assert len(backup_policy_list) == 3

        # delete all backup policies
        for backup_policy_name in backup_policies:
            self.cmd("az netappfiles account backup-policy delete -g {rg} -a %s --backup-policy-name %s" %
                     (account_name, backup_policy_name))

        # validate that no backup policies exist
        backup_policy_list = self.cmd("az netappfiles account backup-policy list -g {rg} -a '%s'" %
                                      account_name).get_output_in_json()
        assert len(backup_policy_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_policy_', additional_tags={'owner': 'cli_test'})
    def test_get_backup_policy_by_name(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create backup policy
        backup_policy_name = self.create_random_name(prefix='cli-ba-pol-', length=16)
        self.cmd("az netappfiles account backup-policy create -g {rg} -a %s --backup-policy-name %s -l %s "
                 "--daily-backups 1 --enabled true" % (account_name, backup_policy_name, LOCATION)).get_output_in_json()

        # get backup policy by name and validate
        backup_policy = self.cmd("az netappfiles account backup-policy show -g {rg} -a %s --backup-policy-name %s" %
                                 (account_name, backup_policy_name)).get_output_in_json()
        assert backup_policy['name'] == account_name + '/' + backup_policy_name
        assert backup_policy['dailyBackupsToKeep'] == 1

        # get backup policy by resource id and validate
        backup_policy_from_id = self.cmd("az netappfiles account backup-policy show --ids %s" %
                                         backup_policy['id']).get_output_in_json()
        assert backup_policy_from_id['name'] == account_name + '/' + backup_policy_name
        assert backup_policy['dailyBackupsToKeep'] == 1

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_backup_policy_', additional_tags={'owner': 'cli_test'})
    def test_update_backup_policy(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create backup policy
        backup_policy_name = self.create_random_name(prefix='cli-ba-pol-', length=16)
        daily_backups_to_keep = 1
        weekly_backups_to_keep = 2
        monthly_backups_to_keep = 3
        enabled = True
        tags = "Tag1=Value1"
        self.cmd("az netappfiles account backup-policy create -g {rg} -a %s --backup-policy-name %s "
                 "-l %s -d %s -w %s -m %s -e %s --tags %s" %
                 (account_name, backup_policy_name, LOCATION, daily_backups_to_keep,
                  weekly_backups_to_keep, monthly_backups_to_keep, enabled, tags)).get_output_in_json()

        # update backup policy
        daily_backups_to_keep = 4
        weekly_backups_to_keep = 5
        monthly_backups_to_keep = 6
        enabled = False
        tags = "Tag1=Value2"
        self.cmd("az netappfiles account backup-policy update -g {rg} -a %s --backup-policy-name %s -l %s -d %s -w %s "
                 "-m %s -e %s --tags %s" % (account_name, backup_policy_name, LOCATION, daily_backups_to_keep,
                                            weekly_backups_to_keep, monthly_backups_to_keep, enabled, tags)).get_output_in_json()

        # get updated backup policy and validate update
        backup_policy = self.cmd("az netappfiles account backup-policy show -g {rg} -a %s --backup-policy-name %s" %
                                 (account_name, backup_policy_name)).get_output_in_json()
        assert backup_policy['dailyBackupsToKeep'] == daily_backups_to_keep
        assert backup_policy['weeklyBackupsToKeep'] == weekly_backups_to_keep
        assert backup_policy['monthlyBackupsToKeep'] == monthly_backups_to_keep
        assert backup_policy['enabled'] == enabled
        assert backup_policy['tags']['Tag1'] == 'Value2'
