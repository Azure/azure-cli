# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


class StorageAccountTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_create_storage_account(self, resource_group, location):
        name = self.create_random_name(prefix='cli', length=24)

        self.cmd('az storage account create -n {} -g {} --sku {} -l {}'.format(
            name, resource_group, 'Standard_LRS', location))

        self.cmd('storage account check-name --name {}'.format(name), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])

        self.cmd('storage account list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].location', 'westus'),
            JMESPathCheck('[0].sku.name', 'Standard_LRS'),
            JMESPathCheck('[0].resourceGroup', resource_group)
        ])

        self.cmd('az storage account show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', location),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('kind', 'Storage')
        ])

        self.cmd('storage account show-connection-string -g {} -n {} --protocol http'.format(
            resource_group, name), checks=[
            JMESPathCheck("contains(connectionString, 'https')", False),
            JMESPathCheck("contains(connectionString, '{}')".format(name), True)])

        self.cmd('storage account delete -g {} -n {} --yes'.format(resource_group, name))
        self.cmd('storage account check-name --name {}'.format(name),
                 checks=JMESPathCheck('nameAvailable', True))

    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_sku(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('sku.name', 'Standard_RAGRS')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, max_api='2017-06-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_kind(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('kind', 'Storage')])

    def test_show_usage(self):
        self.cmd('storage account show-usage', checks=JMESPathCheck('name.value', 'StorageAccounts'))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account_1')
    @StorageAccountPreparer(parameter_name='account_2')
    def test_list_storage_accounts(self, account_1, account_2):
        accounts_list = self.cmd('az storage account list').get_output_in_json()
        assert len(accounts_list) >= 2
        assert next(acc for acc in accounts_list if acc['name'] == account_1)
        assert next(acc for acc in accounts_list if acc['name'] == account_2)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_renew_account_key(self, resource_group, storage_account):
        original_keys = self.cmd('storage account keys list -g {} -n {}'
                                 .format(resource_group, storage_account)).get_output_in_json()
        # key1 = keys_result[0]
        # key2 = keys_result[1]
        assert original_keys[0] and original_keys[1]

        renewed_keys = self.cmd('storage account keys renew -g {} -n {} --key primary'
                                .format(resource_group, storage_account)).get_output_in_json()
        assert renewed_keys[0] != original_keys[0]
        assert renewed_keys[1] == original_keys[1]

        original_keys = renewed_keys
        renewed_keys = self.cmd('storage account keys renew -g {} -n {} --key secondary'
                                .format(resource_group, storage_account)).get_output_in_json()
        assert renewed_keys[0] == original_keys[0]
        assert renewed_keys[1] != original_keys[1]

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_create_account_sas(self, storage_account):
        sas = self.cmd('storage account generate-sas --resource-types o --services b '
                       '--expiry 2046-12-31T08:23Z --permissions r --https-only --account-name {}'
                       .format(storage_account)).output
        self.assertIn('sig=', sas, 'SAS token {} does not contain sig segment'.format(sas))
        self.assertIn('se=', sas, 'SAS token {} does not contain se segment'.format(sas))

    def test_list_locations(self):
        self.cmd('az account list-locations',
                 checks=[JMESPathCheck("[?name=='westus'].displayName | [0]", 'West US')])
