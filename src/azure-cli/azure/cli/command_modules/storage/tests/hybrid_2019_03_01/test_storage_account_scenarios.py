# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint, live_only)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin
from knack.util import CLIError
from azure_devtools.scenario_tests import AllowLargeResponse


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageAccountTests(StorageScenarioMixin, ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_service_endpoints')
    @StorageAccountPreparer()
    def test_storage_account_service_endpoints(self, resource_group, storage_account):
        kwargs = {
            'rg': resource_group,
            'acc': storage_account,
            'vnet': 'vnet1',
            'subnet': 'subnet1'
        }
        self.cmd('storage account create -g {rg} -n {acc} --bypass Metrics --default-action Deny --https-only '
                 .format(**kwargs),
                 checks=[
                     JMESPathCheck('networkRuleSet.bypass', 'Metrics'),
                     JMESPathCheck('networkRuleSet.defaultAction', 'Deny')])
        self.cmd('storage account update -g {rg} -n {acc} --bypass Logging --default-action Allow'.format(**kwargs),
                 checks=[
                     JMESPathCheck('networkRuleSet.bypass', 'Logging'),
                     JMESPathCheck('networkRuleSet.defaultAction', 'Allow')])
        self.cmd('storage account update -g {rg} -n {acc} --set networkRuleSet.default_action=deny'.format(**kwargs),
                 checks=[
                     JMESPathCheck('networkRuleSet.bypass', 'Logging'),
                     JMESPathCheck('networkRuleSet.defaultAction', 'Deny')])

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}'.format(**kwargs))
        self.cmd(
            'network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints Microsoft.Storage'.format(
                **kwargs))

        self.cmd('storage account network-rule add -g {rg} --account-name {acc} --ip-address 25.1.2.3'.format(**kwargs))
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {acc} --ip-address 25.2.0.0/24'.format(**kwargs))
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {acc} --vnet-name {vnet} --subnet {subnet}'.format(
                **kwargs))
        self.cmd('storage account network-rule list -g {rg} --account-name {acc}'.format(**kwargs), checks=[
            JMESPathCheck('length(ipRules)', 2),
            JMESPathCheck('length(virtualNetworkRules)', 1)
        ])
        self.cmd(
            'storage account network-rule remove -g {rg} --account-name {acc} --ip-address 25.1.2.3'.format(**kwargs))
        self.cmd(
            'storage account network-rule remove -g {rg} --account-name {acc} --vnet-name {vnet} --subnet {subnet}'.format(
                **kwargs))
        self.cmd('storage account network-rule list -g {rg} --account-name {acc}'.format(**kwargs), checks=[
            JMESPathCheck('length(ipRules)', 1),
            JMESPathCheck('length(virtualNetworkRules)', 0)
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_create_storage_account_with_assigned_identity(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        cmd = 'az storage account create -n {} -g {} --sku Standard_LRS --assign-identity --https-only '.format(name, resource_group)
        result = self.cmd(cmd).get_output_in_json()

        self.assertIn('identity', result)
        self.assertTrue(result['identity']['principalId'])
        self.assertTrue(result['identity']['tenantId'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_update_storage_account_with_assigned_identity(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --sku Standard_LRS --https-only '.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('identity', None)])

        update_cmd = 'az storage account update -n {} -g {} --assign-identity'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('identity', result)
        self.assertTrue(result['identity']['principalId'])
        self.assertTrue(result['identity']['tenantId'])

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_create_storage_account(self, resource_group, location):
        name = self.create_random_name(prefix='cli', length=24)

        self.cmd('az storage account create -n {} -g {} --sku {} -l {} --https-only '.format(
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

        self.cmd('az storage account show -n {}'.format(name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', location),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('kind', 'Storage')
        ])

        self.cmd('storage account show-connection-string -g {} -n {} --protocol http'.format(
            resource_group, name), checks=[
                JMESPathCheck("contains(connectionString, 'https')", False),
                JMESPathCheck("contains(connectionString, '{}')".format(name), True)])

        self.cmd('storage account update -g {} -n {} --tags foo=bar cat'
                 .format(resource_group, name),
                 checks=JMESPathCheck('tags', {'cat': '', 'foo': 'bar'}))
        self.cmd('storage account update -g {} -n {} --sku Standard_GRS --tags'
                 .format(resource_group, name),
                 checks=[JMESPathCheck('tags', {}),
                         JMESPathCheck('sku.name', 'Standard_GRS')])
        self.cmd('storage account update -g {} -n {} --set tags.test=success'
                 .format(resource_group, name),
                 checks=JMESPathCheck('tags', {'test': 'success'}))
        self.cmd('storage account delete -g {} -n {} --yes'.format(resource_group, name))
        self.cmd('storage account check-name --name {}'.format(name),
                 checks=JMESPathCheck('nameAvailable', True))

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-10-01')
    @ResourceGroupPreparer(parameter_name_for_location='location', location='southcentralus')
    def test_create_storage_account_v2(self, resource_group, location):
        self.kwargs.update({
            'name': self.create_random_name(prefix='cli', length=24),
            'loc': location
        })

        self.cmd('storage account create -n {name} -g {rg} -l {loc} --kind StorageV2 --https-only ',
                 checks=[JMESPathCheck('kind', 'StorageV2')])

        self.cmd('storage account check-name --name {name}', checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-10-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_sku(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --https-only '.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('sku.name', 'Standard_RAGRS')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-10-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_kind(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --https-only'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('kind', 'Storage')])

    def test_show_usage(self):
        self.cmd('storage account show-usage', checks=JMESPathCheck('name.value', 'StorageAccounts'))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_logging_operations(self, resource_group, storage_account):
        connection_string = self.cmd(
            'storage account show-connection-string -g {} -n {} -otsv'.format(resource_group, storage_account)).output

        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('blob.read', False),
            JMESPathCheck('blob.retentionPolicy.enabled', False)
        ])

        self.cmd('storage logging update --services b --log r --retention 1 '
                 '--service b --connection-string {}'.format(connection_string))

        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('blob.read', True),
            JMESPathCheck('blob.retentionPolicy.enabled', True),
            JMESPathCheck('blob.retentionPolicy.days', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_metrics_operations(self, resource_group, storage_account_info):
        self.storage_cmd('storage metrics show', storage_account_info) \
            .assert_with_checks(JMESPathCheck('file.hour.enabled', True),
                                JMESPathCheck('file.minute.enabled', False))

        self.storage_cmd('storage metrics update --services f --api true --hour true --minute true --retention 1 ',
                         storage_account_info)

        self.storage_cmd('storage metrics show', storage_account_info).assert_with_checks(
            JMESPathCheck('file.hour.enabled', True),
            JMESPathCheck('file.minute.enabled', True))

    @AllowLargeResponse()
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
        print(renewed_keys)
        print(original_keys)
        assert renewed_keys[0] != original_keys[0]
        assert renewed_keys[1] == original_keys[1]

        original_keys = renewed_keys
        renewed_keys = self.cmd('storage account keys renew -g {} -n {} --key secondary'
                                .format(resource_group, storage_account)).get_output_in_json()
        assert renewed_keys[0] == original_keys[0]
        assert renewed_keys[1] != original_keys[1]

    @AllowLargeResponse()
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

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_account_show_exit_codes(self, resource_group, storage_account):
        self.kwargs = {'rg': resource_group, 'sa': storage_account}

        self.assertEqual(self.cmd('storage account show -g {rg} -n {sa}').exit_code, 0)

        with self.assertRaises(SystemExit) as ex:
            self.cmd('storage account show text_causing_parsing_error')
        self.assertEqual(ex.exception.code, 2)

        with self.assertRaises(SystemExit) as ex:
            self.cmd('storage account show -g fake_group -n {sa}')
        self.assertEqual(ex.exception.code, 3)

        with self.assertRaises(SystemExit) as ex:
            self.cmd('storage account show -g {rg} -n fake_account')
        self.assertEqual(ex.exception.code, 3)
