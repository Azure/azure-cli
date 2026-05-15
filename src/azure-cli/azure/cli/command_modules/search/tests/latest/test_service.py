# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest


class AzureSearchServicesTests(ScenarioTest):

    # https://vcrpy.readthedocs.io/en/latest/configuration.html#request-matching
    def setUp(self):
        self.vcr.match_on = ['scheme', 'method', 'path', 'query'] # not 'host', 'port'
        super().setUp()

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_skus(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'sku_name': 'standard3',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
            'hosting_mode': 'highDensity'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count} --hosting-mode {hosting_mode}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}'),
                    self.check('hostingMode', '{hosting_mode}')])

    def test_service_create_supports_serverless_sku_argument(self):
        from azure.cli.command_modules.search.aaz.latest.search.service._create import Create
        from azure.cli.command_modules.search.aaz.latest.search.service._update import Update

        self.assertIn('serverless', Create._build_arguments_schema().sku.enum.items)
        self.assertIn('serverless', Update._build_arguments_schema().sku.enum.items)

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_multi_partition(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 2,
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_multi_replica(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 2,
            'partition_count': 1,
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_ip_rules(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'public_network_access': 'Enabled',
            'ip_rules': '123.4.5.6,123.5.6.7;123.6.7.8'
        })

        _search_service = self.cmd('az search service create -n {name} -g {rg} --sku {sku_name} --ip-rules {ip_rules}',
                                   checks=[self.check('name', '{name}'),
                                           self.check('sku.name', '{sku_name}'),
                                           self.check('publicNetworkAccess', '{public_network_access}')]).get_output_in_json()

        self.assertTrue(len(_search_service['networkRuleSet']['ipRules']) == 3)

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_private_endpoint(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'public_network_access': 'Disabled'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name} --public-network-access {public_network_access}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_msi(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'identity_type': 'SystemAssigned'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name} --identity-type {identity_type}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('identity.type', '{identity_type}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='westus')
    def test_service_update(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'replica_count': 2,
            'partition_count': 1,
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'replica_count': 1,
            'partition_count': 2,
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_update_ip_rules(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'public_network_access': 'Enabled',
            'ip_rules': '123.4.5.6,123.5.6.7'
        })

        _search_service = self.cmd('az search service create -n {name} -g {rg} --sku {sku_name} --ip-rules {ip_rules}',
                                   checks=[self.check('name', '{name}'),
                                           self.check('sku.name', '{sku_name}'),
                                           self.check('publicNetworkAccess', '{public_network_access}')]).get_output_in_json()

        self.assertTrue(len(_search_service['networkRuleSet']['ipRules']) == 2)

        self.kwargs.update({
            'ip_rules': '123.4.5.6,123.5.6.7;123.6.7.8'
        })

        _search_service = self.cmd('az search service update -n {name} -g {rg} --ip-rules {ip_rules}',
                                   checks=[self.check('name', '{name}'),
                                           self.check('publicNetworkAccess', '{public_network_access}')]).get_output_in_json()
        self.assertTrue(len(_search_service['networkRuleSet']['ipRules']) == 3)

        self.kwargs.update({
            'ip_rules': ','
        })

        _search_service = self.cmd(
            'az search service update -n {name} -g {rg} --ip-rules {ip_rules}',
            checks=[self.check('name', '{name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')]).get_output_in_json()
        self.assertTrue(len(_search_service['networkRuleSet']['ipRules']) == 0)

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='westus')
    def test_service_update_private_endpoint(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'public_network_access': 'Disabled'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name} --public-network-access {public_network_access}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')])

        self.kwargs.update({
            'public_network_access': 'Enabled'
        })

        self.cmd(
            'az search service update -n {name} -g {rg} --public-network-access {public_network_access}',
            checks=[self.check('name', '{name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')])

        self.kwargs.update({
            'public_network_access': 'Disabled'
        })

        self.cmd(
            'az search service update -n {name} -g {rg} --public-network-access {public_network_access}',
            checks=[self.check('name', '{name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='westcentralus')
    def test_service_update_msi(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'identity_type': 'SystemAssigned'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name} --identity-type {identity_type}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('identity.type', '{identity_type}')])

        self.kwargs.update({
            'identity_type': 'None'
        })

        self.cmd(
            'az search service update -n {name} -g {rg} --identity-type {identity_type}',
            checks=[self.check('name', '{name}'),
                    self.check('identity.type', '{identity_type}')])

        self.kwargs.update({
            'identity_type': 'SystemAssigned'
        })

        self.cmd(
            'az search service update -n {name} -g {rg} --identity-type {identity_type}',
            checks=[self.check('name', '{name}'),
                    self.check('identity.type', '{identity_type}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='westus')
    def test_service_update_service_level_encryption_key(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'key_vault_name': self.create_random_name(prefix='clisearchkv', length=24),
            'key_name': self.create_random_name(prefix='key', length=24),
            'identity_type': 'SystemAssigned'
        })

        search_service = self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name} --identity-type {identity_type}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('identity.type', '{identity_type}')]).get_output_in_json()
        self.kwargs['principal_id'] = search_service['identity']['principalId']

        self.cmd(
            'az keyvault create -g {rg} -n {key_vault_name} -l westus'
            ' --enable-purge-protection true --enable-rbac-authorization false')
        self.cmd(
            'az keyvault set-policy -n {key_vault_name} --object-id {principal_id}'
            ' --key-permissions get wrapKey unwrapKey')
        key = self.cmd(
            'az keyvault key create --vault-name {key_vault_name} -n {key_name} --protection software'
        ).get_output_in_json()
        key_id = key['key']['kid']
        self.kwargs.update({
            'key_vault_uri': 'https://{}.vault.azure.net/'.format(self.kwargs['key_vault_name']),
            'key_vault_key_version': key_id.rstrip('/').split('/')[-1]
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --encryption-with-cmk "{{enforcement:Enabled,service-level-encryption-key:'
            '{{key-vault-key-name:{key_name},key-vault-key-version:{key_vault_key_version},'
            "key-vault-uri:'{key_vault_uri}'}}}}\"",
            checks=[self.check('name', '{name}'),
                    self.check('encryptionWithCmk.enforcement', 'Enabled'),
                    self.check('encryptionWithCmk.serviceLevelEncryptionKey.keyVaultKeyName', '{key_name}'),
                    self.check('encryptionWithCmk.serviceLevelEncryptionKey.keyVaultKeyVersion',
                               '{key_vault_key_version}'),
                    self.check('encryptionWithCmk.serviceLevelEncryptionKey.keyVaultUri', '{key_vault_uri}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_delete_show(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.cmd('az search service show -n {name} -g {rg}')

        self.cmd('az search service delete -n {name} -g {rg} -y')

        self.cmd('az search service show -n {name} -g {rg}', expect_failure=True)

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_delete_list(self, resource_group):
        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 0)

        self.kwargs.update({
            'sku_name': 'standard',
            'name1': self.create_random_name(prefix='test', length=24),
            'name2': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name1} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name1}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 1)
        self.assertTrue(self.kwargs['name1'] in [x['name'] for x in _services])

        self.cmd('az search service create -n {name2} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name2}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 2)
        self.assertTrue(self.kwargs['name1'] in [x['name'] for x in _services])
        self.assertTrue(self.kwargs['name2'] in [x['name'] for x in _services])

        self.cmd('az search service delete -n {name1} -g {rg} -y')
        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 1)
        self.assertTrue(self.kwargs['name2'] in [x['name'] for x in _services])
        self.assertFalse(self.kwargs['name1'] in [x['name'] for x in _services])

        self.cmd('az search service delete -n {name2} -g {rg} -y')
        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 0)

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_auth(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
            'disable_local_auth': True
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}'
                 ' --disable-local-auth {disable_local_auth}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}'),
                         self.check('disableLocalAuth', '{disable_local_auth}')])

        self.kwargs.update({
            'disable_local_auth': False,
            'auth_options': 'apiKeyOnly'
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --disable-local-auth {disable_local_auth}'
            ' --auth-options {auth_options}',
            checks=[self.check('name', '{name}'),
                    self.check('disableLocalAuth', '{disable_local_auth}'),
                    self.check('authOptions', {'apiKeyOnly': {} })])

        self.kwargs.update({
            'disable_local_auth': False,
            'auth_options': 'aadOrApiKey',
            'aad_auth_failure_mode': 'http401WithBearerChallenge'
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --disable-local-auth {disable_local_auth}'
            ' --auth-options {auth_options}'
            ' --aad-auth-failure-mode {aad_auth_failure_mode}',
            checks=[self.check('name', '{name}'),
                    self.check('disableLocalAuth', '{disable_local_auth}'),
                    self.check('authOptions', { 'aadOrApiKey': { 'aadAuthFailureMode': 'http401WithBearerChallenge' } } )])

        self.kwargs.update({
            'disable_local_auth': False,
            'auth_options': 'aadOrApiKey',
            'aad_auth_failure_mode': 'http403'
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --disable-local-auth {disable_local_auth}'
            ' --auth-options {auth_options}'
            ' --aad-auth-failure-mode {aad_auth_failure_mode}',
            checks=[self.check('name', '{name}'),
                    self.check('disableLocalAuth', '{disable_local_auth}'),
                    self.check('authOptions', { 'aadOrApiKey': { 'aadAuthFailureMode': 'http403' } } )])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_semantic_search(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
            'semantic_search': 'disabled'
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name} '
                 '--semantic-search {semantic_search}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}'),
                         self.check('semanticSearch', '{semantic_search}')])

        self.kwargs.update({
            'semantic_search': 'free'
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name} '
                 '--semantic-search {semantic_search}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}'),
                         self.check('semanticSearch', '{semantic_search}')])

        self.kwargs.update({
            'semantic_search': 'standard'
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name} '
                 '--semantic-search {semantic_search}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}'),
                         self.check('semanticSearch', '{semantic_search}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_compute_type(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
            'compute_type': 'default'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}'
            ' --compute-type {compute_type}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}'),
                    self.check('computeType', '{compute_type}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_create_data_exfiltration_protections(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
            'dataExfiltrationProtections': 'BlockAll'
        })

        _search_service = self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}'
            ' --data-exfiltration-protections {dataExfiltrationProtections}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')]).get_output_in_json()
        self.assertTrue(len(_search_service['dataExfiltrationProtections']) == 1)
        self.assertTrue(_search_service['dataExfiltrationProtections'][0] == 'BlockAll')

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_service_knowledge_retrieval(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'standard_name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
            'knowledge_retrieval': 'free'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}'
            ' --knowledge-retrieval {knowledge_retrieval}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}'),
                    self.check('knowledgeRetrieval', '{knowledge_retrieval}')])

        self.cmd('az search service show -n {name} -g {rg}',
                 checks=[self.check('name', '{name}'),
                         self.check('knowledgeRetrieval', '{knowledge_retrieval}')])

        self.cmd('az search service list -g {rg}',
                 checks=[self.check('[0].name', '{name}')])

        self.kwargs.update({
            'knowledge_retrieval': 'standard'
        })

        self.cmd('az search service update -n {name} -g {rg} --knowledge-retrieval {knowledge_retrieval}',
                 checks=[self.check('name', '{name}')])

        self.cmd('az search service show -n {name} -g {rg}',
                 checks=[self.check('name', '{name}')])

        self.cmd(
            'az search service create -n {standard_name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}'
            ' --knowledge-retrieval {knowledge_retrieval}',
            checks=[self.check('name', '{standard_name}')])

if __name__ == '__main__':
    unittest.main()
