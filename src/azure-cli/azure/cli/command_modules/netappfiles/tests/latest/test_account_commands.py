# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "westus2"

# No tidy up of tests required. The resource group is automatically removed

# As a refactoring consideration for the future, consider use of authoring patterns desribed here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer


class AzureNetAppFilesAccountServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_')
    def test_create_delete_account(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        tags = 'Tag1=Value1 Tag2=Value2'

        # create and check
        # note : active directory checks are performed in their own subgroup test
        account = self.cmd("az netappfiles account create --resource-group {rg} --account-name '%s' -l %s --tags %s" % (account_name, LOCATION, tags)).get_output_in_json()
        assert account['name'] == account_name
        assert account['tags']['Tag1'] == 'Value1'
        assert account['tags']['Tag2'] == 'Value2'

        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) > 0

        # delete and recheck
        self.cmd("az netappfiles account delete --resource-group {rg} --account-name '%s'" % account_name)
        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) == 0

        # and again with short forms and also unquoted
        account = self.cmd("az netappfiles account create -g {rg} -a %s -l %s --tags %s" % (account_name, LOCATION, tags)).get_output_in_json()
        assert account['name'] == account_name
        # note: key case must match
        assert account['activeDirectories'] is None
        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) > 0

        self.cmd("az netappfiles account delete --resource-group {rg} -a %s" % account_name)
        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_')
    def test_list_accounts(self):
        accounts = [self.create_random_name(prefix='cli', length=24), self.create_random_name(prefix='cli', length=24)]

        for account_name in accounts:
            self.cmd("az netappfiles account create -g {rg} -a %s -l %s --tags Tag1=Value1" % (account_name, LOCATION)).get_output_in_json()

        account_list = self.cmd("netappfiles account list -g {rg}").get_output_in_json()
        assert len(account_list) == 2

        for account_name in accounts:
            self.cmd("az netappfiles account delete -g {rg} -a %s" % account_name)

        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_')
    def test_get_account_by_name(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        account = self.cmd("az netappfiles account create -g {rg} -a %s -l %s" % (account_name, LOCATION)).get_output_in_json()
        account = self.cmd("az netappfiles account show --resource-group {rg} -a %s" % account_name).get_output_in_json()
        assert account['name'] == account_name
        account_from_id = self.cmd("az netappfiles account show --ids %s" % account['id']).get_output_in_json()
        assert account_from_id['name'] == account_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_')
    def test_update_account(self):
        # only tags are checked here due to complications of active directory in automated test
        account_name = self.create_random_name(prefix='cli', length=24)
        tag = "Tag1=Value1"

        account = self.cmd("az netappfiles account create -g {rg} -a %s -l %s" % (account_name, LOCATION)).get_output_in_json()
        account = self.cmd("az netappfiles account update --resource-group {rg} -a %s --tags %s" % (account_name, tag)).get_output_in_json()
        assert account['name'] == account_name
        assert account['tags']['Tag1'] == 'Value1'
        assert account['activeDirectories'] is None

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_')
    def test_active_directory(self):
        account_name = self.create_random_name(prefix='cli', length=24)

        # create an account as normal
        account = self.cmd("az netappfiles account create -g {rg} -a %s -l %s --tags Tag1=Value1" % (account_name, LOCATION)).get_output_in_json()
        assert account['name'] == account_name

        # now add an active directory
        acc_with_active_directory = self.cmd("netappfiles account ad add -g {rg} -n %s --username aduser --password aduser --smb-server-name SMBSERVER --dns '1.2.3.4' --domain westcentralus" % (account_name)).get_output_in_json()
        assert acc_with_active_directory['name'] == account_name
        assert acc_with_active_directory['activeDirectories'][0]['username'] == 'aduser'

        # now add an active directory
        active_directory = self.cmd("netappfiles account ad list -g {rg} -n %s" % (account_name)).get_output_in_json()
        assert account['name'] == account_name
        assert active_directory[0]['username'] == 'aduser'

        # now remove using the previously obtained details
        acc_with_active_directory = self.cmd("netappfiles account ad remove -g {rg} -n %s --active-directory %s" % (account_name, active_directory[0]['activeDirectoryId'])).get_output_in_json()
        assert account['name'] == account_name
        assert account['activeDirectories'] is None
