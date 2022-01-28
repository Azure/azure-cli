# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError

POOL_DEFAULT = "--service-level Premium --size 4"
POOL_DEFAULT_TOO_SMALL = "--service-level 'Premium' --size 3"
POOL_DEFAULT_STRING_SIZE = "--service-level 'Premium' --size a"
LOCATION = "southcentralusstage"

# No tidy up of tests required. The resource group is automatically removed

# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer


class AzureNetAppFilesPoolServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_pool(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        tags = "Tag1=Value1 Tag2=Value2"

        self.cmd("az netappfiles account create --resource-group {rg} --account-name '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()
        pool = self.cmd("az netappfiles pool create --resource-group {rg} --account-name %s --pool-name %s -l %s %s --tags %s" % (account_name, pool_name, LOCATION, POOL_DEFAULT, tags)).get_output_in_json()
        assert pool['name'] == account_name + '/' + pool_name
        assert pool['tags']['Tag1'] == 'Value1'
        assert pool['tags']['Tag2'] == 'Value2'

        pool_list = self.cmd("netappfiles pool list --resource-group {rg} --account-name %s" % account_name).get_output_in_json()
        assert len(pool_list) is 1

        self.cmd("az netappfiles pool delete --resource-group {rg} --account-name '%s' --pool-name '%s'" % (account_name, pool_name))
        pool_list = self.cmd("netappfiles pool list --resource-group {rg} --account-name %s" % account_name).get_output_in_json()
        assert len(pool_list) is 0

        # and again with short forms and also unquoted
        pool = self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s --service-level 'Premium' --size 4 --tags %s" % (account_name, pool_name, LOCATION, tags)).get_output_in_json()
        assert pool['name'] == account_name + '/' + pool_name
        assert pool['tags']['Tag1'] == 'Value1'
        assert pool['tags']['Tag2'] == 'Value2'
        assert pool['qosType'] == 'Auto'

        self.cmd("az netappfiles pool delete --resource-group {rg} -a %s -p %s" % (account_name, pool_name))
        pool_list = self.cmd("netappfiles pool list --resource-group {rg} -a %s" % account_name).get_output_in_json()
        assert len(pool_list) is 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_create_pool_too_small(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)

        self.cmd("az netappfiles account create --resource-group {rg} --account-name '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()
        with self.assertRaises(CLIError):
            self.cmd("az netappfiles pool create --resource-group {rg} --account-name %s --pool-name %s -l %s %s " % (account_name, pool_name, LOCATION, POOL_DEFAULT_TOO_SMALL)).get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_create_pool_string_size(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)

        self.cmd("az netappfiles account create --resource-group {rg} --account-name '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()
        with self.assertRaises(CLIError):
            self.cmd("az netappfiles pool create --resource-group {rg} --account-name %s --pool-name %s -l %s %s " % (account_name, pool_name, LOCATION, POOL_DEFAULT_STRING_SIZE)).get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_list_pools(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        pools = [self.create_random_name(prefix='cli', length=24), self.create_random_name(prefix='cli', length=24)]
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        for pool_name in pools:
            self.cmd("az netappfiles pool create -g {rg} -a '%s' -p '%s' -l %s %s --tags Tag1=Value1" % (account_name, pool_name, LOCATION, POOL_DEFAULT)).get_output_in_json()

        pool_list = self.cmd("netappfiles pool list -g {rg} -a '%s'" % account_name).get_output_in_json()
        assert len(pool_list) == 2

        for pool_name in pools:
            self.cmd("az netappfiles pool delete -g {rg} -a %s -p %s" % (account_name, pool_name))
        pool_list = self.cmd("netappfiles pool list --resource-group {rg} -a '%s'" % account_name).get_output_in_json()
        assert len(pool_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_get_pool_by_name(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        pool_name = self.create_random_name(prefix='cli', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s %s" % (account_name, pool_name, LOCATION, POOL_DEFAULT)).get_output_in_json()

        pool = self.cmd("az netappfiles pool show --resource-group {rg} -a %s -p %s" % (account_name, pool_name)).get_output_in_json()
        assert pool['name'] == account_name + '/' + pool_name
        pool_from_id = self.cmd("az netappfiles pool show --ids %s" % pool['id']).get_output_in_json()
        assert pool_from_id['name'] == account_name + '/' + pool_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_update_pool(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'tag': "Tag1=Value1",
            'pool_default': POOL_DEFAULT,
            'qos_type': "Manual"
        })

        self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc}", checks=[
            self.check('name', '{acc_name}')
        ])
        self.cmd("az netappfiles pool create -g {rg} -a {acc_name} -p {pool_name} -l {loc} {pool_default}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}')
        ])
        self.cmd("az netappfiles pool update -g {rg} -a {acc_name} -p {pool_name} --tags {tag} --qos-type {qos_type}", checks=[
            self.check('name', '{acc_name}/{pool_name}'),
            self.check('qosType', '{qos_type}'),
            self.check('tags.Tag1', 'Value1')
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_pool_', additional_tags={'owner': 'cli_test'})
    def test_pool_parameters(self):
        account_name = self.create_random_name(prefix='cli', length=24)
        pool_name = self.create_random_name(prefix='cli', length=24)

        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s %s --encryption-type %s" %
                 (account_name, pool_name, LOCATION, POOL_DEFAULT, "Double")).get_output_in_json()

        pool = self.cmd("az netappfiles pool show --resource-group {rg} -a %s -p %s" % (account_name, pool_name)).get_output_in_json()
        assert pool['name'] == account_name + '/' + pool_name
        assert pool['encryptionType'] == "Double"
