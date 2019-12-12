# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint, live_only, LiveScenarioTest)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin
from knack.util import CLIError
from datetime import datetime, timedelta
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
        self.cmd('storage account create -g {rg} -n {acc} --bypass Metrics --default-action Deny'.format(**kwargs),
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
        cmd = 'az storage account create -n {} -g {} --sku Standard_LRS --assign-identity'.format(name, resource_group)
        result = self.cmd(cmd).get_output_in_json()

        self.assertIn('identity', result)
        self.assertTrue(result['identity']['principalId'])
        self.assertTrue(result['identity']['tenantId'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_update_storage_account_with_assigned_identity(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --sku Standard_LRS'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('identity', None)])

        update_cmd = 'az storage account update -n {} -g {} --assign-identity'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('identity', result)
        self.assertTrue(result['identity']['principalId'])
        self.assertTrue(result['identity']['tenantId'])

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

        large_file_name = self.create_random_name(prefix='cli', length=24)
        self.cmd('storage account create -g {} -n {} --sku {} --enable-large-file-share'.format(
            resource_group, large_file_name, 'Standard_LRS'))
        self.cmd('az storage account show -n {} -g {}'.format(large_file_name, resource_group), checks=[
            JMESPathCheck('name', large_file_name),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('largeFileSharesState', 'Enabled')
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-10-01')
    @ResourceGroupPreparer(parameter_name_for_location='location', location='southcentralus')
    def test_create_storage_account_v2(self, resource_group, location):
        self.kwargs.update({
            'name': self.create_random_name(prefix='cli', length=24),
            'loc': location
        })

        self.cmd('storage account create -n {name} -g {rg} -l {loc} --kind StorageV2',
                 checks=[JMESPathCheck('kind', 'StorageV2')])

        self.cmd('storage account check-name --name {name}', checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-01-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_sku(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('sku.name', 'Standard_RAGRS')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2018-02-01')
    @ResourceGroupPreparer(location='southcentralus', name_prefix='cli_storage_account_hns')
    def test_storage_create_with_hns(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 --hns'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('isHnsEnabled', True)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2018-02-01')
    @ResourceGroupPreparer(location='southcentralus', name_prefix='cli_storage_account_hns')
    def test_storage_create_with_hns_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 --hns true'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('isHnsEnabled', True)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2018-02-01')
    @ResourceGroupPreparer(location='southcentralus', name_prefix='cli_storage_account_hns')
    def test_storage_create_with_hns_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 --hns false'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('isHnsEnabled', False)])

    def test_show_usage(self):
        self.cmd('storage account show-usage -l westus', checks=JMESPathCheck('name.value', 'StorageAccounts'))

    def test_show_usage_no_location(self):
        with self.assertRaises(SystemExit):
            self.cmd('storage account show-usage')

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

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_renew_account_kerb_key(self, resource_group):
        name = self.create_random_name(prefix='clistoragekerbkey', length=24)
        self.kwargs = {'sc': name, 'rg': resource_group}
        self.cmd('storage account create -g {rg} -n {sc} -l eastus2euap --enable-files-aadds')
        self.cmd('storage account keys list -g {rg} -n {sc}', checks=JMESPathCheck('length(@)', 2))
        original_keys = self.cmd('storage account keys list -g {rg} -n {sc} --expand-key-type kerb',
                                 checks=JMESPathCheck('length(@)', 4)).get_output_in_json()

        renewed_access_keys = self.cmd('storage account keys renew -g {rg} -n {sc} --key secondary').get_output_in_json()
        assert renewed_access_keys[0] == original_keys[0]
        assert renewed_access_keys[1] != original_keys[1]
        renewed_kerb_keys = self.cmd(
            'storage account keys renew -g {rg} -n {sc} --key primary --key-type kerb').get_output_in_json()
        assert renewed_kerb_keys[2] != original_keys[2]
        assert renewed_kerb_keys[3] == original_keys[3]

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

    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_customer_managed_key(self, resource_group, storage_account):
        self.kwargs = {'rg': resource_group, 'sa': storage_account, 'vt': self.create_random_name('clitest', 24)}

        self.kwargs['vid'] = self.cmd('az keyvault create -n {vt} -g {rg} '
                                      '-otsv --query id').output.rstrip('\n')
        self.kwargs['vtn'] = self.cmd('az keyvault show -n {vt} -g {rg} '
                                      '-otsv --query properties.vaultUri').output.strip('\n')
        self.kwargs['ver'] = self.cmd("az keyvault key create -n testkey -p software --vault-name {vt} "
                                      "-otsv --query 'key.kid'").output.rsplit('/', 1)[1].rstrip('\n')
        self.kwargs['oid'] = self.cmd("az storage account update -n {sa} -g {rg} --assign-identity "
                                      "-otsv --query 'identity.principalId'").output.strip('\n')

        self.cmd('az keyvault set-policy -n {vt} --object-id {oid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')
        self.cmd('az keyvault update -n {vt} -g {rg} --set properties.enableSoftDelete=true')
        self.cmd('az resource update --id {vid} --set properties.enablePurgeProtection=true')
        self.cmd('az storage account update -n {sa} -g {rg} '
                 '--encryption-key-source Microsoft.Keyvault '
                 '--encryption-key-vault {vtn} '
                 '--encryption-key-name testkey '
                 '--encryption-key-version {ver} ')

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

    @ResourceGroupPreparer()
    def test_management_policy(self, resource_group):
        import os
        from msrestazure.azure_exceptions import CloudError
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        policy_file = os.path.join(curr_dir, 'mgmt_policy.json').replace('\\', '\\\\')

        storage_account = self.create_random_name(prefix='cli', length=24)

        self.kwargs = {'rg': resource_group, 'sa': storage_account, 'policy': policy_file}
        self.cmd('storage account create -g {rg} -n {sa} --kind StorageV2')
        self.cmd('storage account management-policy create --account-name {sa} -g {rg} --policy @"{policy}"')
        self.cmd('storage account management-policy update --account-name {sa} -g {rg}'
                 ' --set "policy.rules[0].name=newname"')
        self.cmd('storage account management-policy show --account-name {sa} -g {rg}',
                 checks=JMESPathCheck('policy.rules[0].name', 'newname'))
        self.cmd('storage account management-policy delete --account-name {sa} -g {rg}')
        self.cmd('storage account management-policy show --account-name {sa} -g {rg}', expect_failure=True)

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_aadds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-aadds'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_aadds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-aadds false'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_aadds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-aadds true'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_aadds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --enable-files-aadds'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_aadds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --enable-files-aadds false'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_aadds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --enable-files-aadds true'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_adds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        create_cmd = """storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds --domain-name
        {domain_name} --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid
        {domain_guid} --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_adds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'sc': name
        })
        result = self.cmd("storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds false").get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_adds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        create_cmd = """storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds true --domain-name
        {domain_name} --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid
        {domain_guid} --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_adds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} -l eastus2euap'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        update_cmd = """storage account update -n {sc} -g {rg} --enable-files-adds --domain-name {domain_name}
        --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}
        --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_adds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} -l eastus2euap'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-adds false'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_adds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} -l eastus2euap'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        update_cmd = """storage account update -n {sc} -g {rg} --enable-files-adds true --domain-name {domain_name}
        --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}
        --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])


class RoleScenarioTest(LiveScenarioTest):
    def run_under_service_principal(self):
        account_info = self.cmd('account show').get_output_in_json()
        return account_info['user']['type'] == 'servicePrincipal'


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
class RevokeStorageAccountTests(StorageScenarioMixin, RoleScenarioTest, LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_storage_revoke_keys')
    @StorageAccountPreparer()
    def test_storage_account_revoke_delegation_keys(self, resource_group, storage_account):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...
        from datetime import datetime, timedelta
        import time

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        account_info = self.get_account_info(resource_group, storage_account)
        c = self.create_container(account_info)
        b = self.create_random_name('blob', 24)
        local_file = self.create_temp_file(128, full_random=False)
        self.kwargs.update({
            'expiry': expiry,
            'account': storage_account,
            'container': c,
            'local_file': local_file,
            'blob': b,
            'rg': resource_group
        })
        result = self.cmd('storage account show -n {account} -g {rg}').get_output_in_json()
        self.kwargs['sc_id'] = result['id']

        user = self.create_random_name('testuser', 15)
        self.kwargs['upn'] = user + '@azuresdkteam.onmicrosoft.com'
        self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

        self.cmd('role assignment create --assignee {upn} --role "Storage Blob Data Contributor" --scope {sc_id}')

        container_sas = self.cmd('storage blob generate-sas --account-name {account} -n {blob} -c {container} --expiry {expiry} --permissions '
                                 'rw --https-only --as-user --auth-mode login -otsv').output
        self.kwargs['container_sas'] = container_sas
        self.cmd('storage blob upload -c {container} -n {blob} -f "{local_file}" --account-name {account} --sas-token {container_sas}')

        blob_sas = self.cmd('storage blob generate-sas --account-name {account} -n {blob} -c {container} --expiry {expiry} --permissions '
                            'r --https-only --as-user --auth-mode login -otsv').output
        self.kwargs['blob_sas'] = blob_sas
        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}') \
            .assert_with_checks(JMESPathCheck('name', b))

        self.cmd('storage account revoke-delegation-keys -n {account} -g {rg}')
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}', expect_failure=True)


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
class BlobServicePropertiesTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_account_update_change_feed(self):
        result = self.cmd('storage account blob-service-properties update --enable-change-feed true -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], True)

        result = self.cmd('storage account blob-service-properties update --enable-change-feed false -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], False)

        result = self.cmd('storage account blob-service-properties update --enable-change-feed -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], True)

        result = self.cmd('storage account blob-service-properties show -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], True)
