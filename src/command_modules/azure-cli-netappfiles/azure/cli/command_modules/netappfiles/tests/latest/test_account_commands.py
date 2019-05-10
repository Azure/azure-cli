# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesAccountServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_tests_rg_')
    def test_create_delete_account(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        tags = 'Tag1=Value1 Tag2=Value2'
        # active_directories = '[{"username": "aduser", "password": "aduser", "smbservername": "SMBSERVER", "dns": "1.2.3.4", "domain": "westcentralus"}]'

        # create and check
        # account = self.cmd("az netappfiles account create --resource-group {rg} --account-name '%s' -l 'westus2' --tags '%s' --active-directories %s" % (account_name, tags, active_directories)).get_output_in_json()
        account = self.cmd("az netappfiles account create --resource-group {rg} --account-name '%s' -l 'westus2' --tags '%s'" % (account_name, tags)).get_output_in_json()
        assert account['name'] == account_name
        assert account['tags']['Tag1'] == 'Value1'
        assert account['tags']['Tag2'] == 'Value2'
        # not provided in call - interpreted as kwargs. Tested at command line instead.
        # assert account['active_directories'][0]['username'] == 'aduser'
        # assert account['active_directories'][0]['smbservername'] == 'SMBSERVER'

        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) > 0

        # delete and recheck
        self.cmd("az netappfiles account delete --resource-group {rg} --account-name '%s'" % account_name)
        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) == 0

        # and again with short forms and also unquoted
        account = self.cmd("az netappfiles account create -g {rg} -a %s -l westus2 --tags '%s'" % (account_name, tags)).get_output_in_json()
        assert account['name'] == account_name
        # note: key case must match
        assert account['activeDirectories'] is None
        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) > 0

        self.cmd("az netappfiles account delete --resource-group {rg} -a %s" % account_name)
        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_tests_rg_')
    def test_list_accounts(self):
        accounts = [self.create_random_name(prefix='cli', length=24), self.create_random_name(prefix='cli', length=24)]

        for account_name in accounts:
            self.cmd("az netappfiles account create -g {rg} -a %s -l 'westus2' --tags 'Tag1=Value1'" % account_name).get_output_in_json()

        account_list = self.cmd("netappfiles account list -g {rg}").get_output_in_json()
        assert len(account_list) == 2

        for account_name in accounts:
            self.cmd("az netappfiles account delete -g {rg} -a %s" % account_name)

        account_list = self.cmd("netappfiles account list --resource-group {rg}").get_output_in_json()
        assert len(account_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_tests_rg_')
    def test_get_account_by_name(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        account = self.cmd("az netappfiles account create -g {rg} -a %s -l 'westus2'" % account_name).get_output_in_json()
        account = self.cmd("az netappfiles account show --resource-group {rg} -a %s" % account_name).get_output_in_json()
        assert account['name'] == account_name
        account_from_id = self.cmd("az netappfiles account show --ids %s" % account['id']).get_output_in_json()
        assert account_from_id['name'] == account_name

    @ResourceGroupPreparer(name_prefix='cli_tests_rg_')
    def test_set_account(self):
        # only tags are checked here due to complications of active directory in automated test
        account_name = self.create_random_name(prefix='cli', length=24)
        tag = "Tag1=Value1"

        account = self.cmd("az netappfiles account create -g {rg} -a %s -l 'westus2'" % account_name).get_output_in_json()
        account = self.cmd("az netappfiles account set --resource-group {rg} -a %s -l 'westus2' --tags %s" % (account_name, tag)).get_output_in_json()
        assert account['name'] == account_name
        assert account['tags']['Tag1'] == 'Value1'
        assert account['activeDirectories'] is None

    @ResourceGroupPreparer(name_prefix='cli_tests_rg_')
    def test_update_account(self):
        # only tags are checked here due to complications of active directory in automated test
        account_name = self.create_random_name(prefix='cli', length=24)
        tag = "Tag1=Value1"

        account = self.cmd("az netappfiles account create -g {rg} -a %s -l 'westus2'" % account_name).get_output_in_json()
        account = self.cmd("az netappfiles account update --resource-group {rg} -a %s --tags %s -l westus2" % (account_name, tag)).get_output_in_json()
        assert account['name'] == account_name
        assert account['tags']['Tag1'] == 'Value1'
        assert account['activeDirectories'] is None
