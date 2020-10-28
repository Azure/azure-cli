# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from azure.cli.testsdk import JMESPathCheck, ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError
import uuid


class CosmosDBTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_create_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-automatic-failover --default-consistency-level ConsistentPrefix')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', True),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'ConsistentPrefix'),
            self.check('publicNetworkAccess', 'Enabled'),
        ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-automatic-failover false --default-consistency-level Session --disable-key-based-metadata-write-access --enable-public-network false')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', False),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'Session'),
            self.check('disableKeyBasedMetadataWriteAccess', True),
            self.check('publicNetworkAccess', 'Disabled'),
        ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --tags testKey=testValue --enable-public-network')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', False),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'Session'),
            self.check('publicNetworkAccess', 'Enabled')
        ]).get_output_in_json()
        assert account['tags']['testKey'] == "testValue"

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_update_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB --ip-range-filter "20.10.10.10,12.12.122.122,12.22.11.11" --server-version 3.2 --enable-analytical-storage true --enable-free-tier false')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            JMESPathCheck('kind', 'MongoDB'),
            self.check('ipRules[0].ipAddressOrRange', '20.10.10.10'),
            self.check('ipRules[1].ipAddressOrRange', '12.12.122.122'),
            self.check('ipRules[2].ipAddressOrRange', '12.22.11.11'),
            self.check('apiProperties.serverVersion', '3.2'),
            self.check('enableAnalyticalStorage', 'True'),
            self.check('enableFreeTier', 'False')
        ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --capabilities EnableAggregationPipeline')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            JMESPathCheck('kind', 'MongoDB'),
            self.check('ipRules[0].ipAddressOrRange', "20.10.10.10"),
        ]).get_output_in_json()
        assert len(account['capabilities']) == 1
        assert account['capabilities'][0]['name'] == "EnableAggregationPipeline"

        connection_strings = self.cmd('az cosmosdb keys list --type connection-strings -n {acc} -g {rg}').get_output_in_json()
        assert len(connection_strings['connectionStrings']) == 4

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_delete_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        self.cmd('az cosmosdb delete -n {acc} -g {rg} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_check_name_exists_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        result = self.cmd('az cosmosdb check-name-exists -n {acc}').get_output_in_json()
        assert not result
        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        result = self.cmd('az cosmosdb check-name-exists -n {acc}').get_output_in_json()
        assert result

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_keys_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        original_keys = self.cmd('az cosmosdb keys list -n {acc} -g {rg}').get_output_in_json()
        assert 'primaryMasterKey' in original_keys
        assert 'primaryReadonlyMasterKey' in original_keys
        assert 'secondaryMasterKey' in original_keys
        assert 'secondaryReadonlyMasterKey' in original_keys

        self.cmd('az cosmosdb keys regenerate -n {acc} -g {rg} --key-kind primary')
        self.cmd('az cosmosdb keys regenerate -n {acc} -g {rg} --key-kind primaryReadonly')
        self.cmd('az cosmosdb keys regenerate -n {acc} -g {rg} --key-kind secondary')
        self.cmd('az cosmosdb keys regenerate -n {acc} -g {rg} --key-kind secondaryReadonly')

        modified_keys = self.cmd('az cosmosdb keys list -n {acc} -g {rg}').get_output_in_json()
        assert original_keys['primaryMasterKey'] != modified_keys['primaryMasterKey']
        assert original_keys['primaryReadonlyMasterKey'] != modified_keys['primaryReadonlyMasterKey']
        assert original_keys['secondaryMasterKey'] != modified_keys['secondaryMasterKey']
        assert original_keys['secondaryReadonlyMasterKey'] != modified_keys['secondaryReadonlyMasterKey']

        original_keys = self.cmd('az cosmosdb list-read-only-keys -n {acc} -g {rg}').get_output_in_json()
        assert 'primaryReadonlyMasterKey' in original_keys
        assert 'secondaryReadonlyMasterKey' in original_keys
        assert 'primaryMasterKey' not in original_keys
        assert 'secondaryMasterKey' not in original_keys

        # make sure the deprecated command is not broken
        deprecated_keys = self.cmd('az cosmosdb list-keys -n {acc} -g {rg}').get_output_in_json()
        assert 'primaryReadonlyMasterKey' in deprecated_keys
        assert 'secondaryReadonlyMasterKey' in deprecated_keys
        assert 'primaryMasterKey' in deprecated_keys
        assert 'secondaryMasterKey' in deprecated_keys

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_list_database_accounts(self, resource_group):

        self.kwargs.update({
            'acc1': self.create_random_name(prefix='cli', length=40),
            'acc2': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc1} -g {rg}')
        self.cmd('az cosmosdb create -n {acc2} -g {rg}')
        accounts_list = self.cmd('az cosmosdb list -g {rg}').get_output_in_json()
        assert next(acc for acc in accounts_list if acc['name'] == self.kwargs['acc1'])
        assert next(acc for acc in accounts_list if acc['name'] == self.kwargs['acc2'])

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_locations_database_accounts(self, resource_group):

        write_location = 'eastus'
        read_location = 'westus'

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40),
            'write_location': write_location,
            'read_location': read_location
        })

        account1 = self.cmd('az cosmosdb create -n {acc} -g {rg} --locations regionName={write_location} failoverPriority=0 --locations regionName={read_location} failoverPriority=1').get_output_in_json()
        assert len(account1['writeLocations']) == 1
        assert len(account1['readLocations']) == 2
        assert account1['writeLocations'][0]['failoverPriority'] == 0
        assert account1['writeLocations'][0]['locationName'] == "East US"
        assert account1['readLocations'][0]['locationName'] == "West US" or account1['readLocations'][1]['locationName'] == "West US"
        assert account1['readLocations'][0]['failoverPriority'] == 1 or account1['readLocations'][1]['failoverPriority'] == 1

        self.cmd('az cosmosdb failover-priority-change -n {acc} -g {rg} --failover-policies {read_location}=0 {write_location}=1')
        account2 = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        assert len(account2['writeLocations']) == 1
        assert len(account2['readLocations']) == 2

        assert account2['writeLocations'][0]['failoverPriority'] == 0
        assert account2['writeLocations'][0]['locationName'] == "West US"
        assert account2['readLocations'][0]['locationName'] == "East US" or account2['readLocations'][1]['locationName'] == "East US"
        assert account2['readLocations'][0]['failoverPriority'] == 1 or account2['readLocations'][1]['failoverPriority'] == 1

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_locations_both_formats_database_accounts(self, resource_group):

        write_location = 'eastus'
        read_location = 'westus'

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40),
            'write_location': write_location,
            'read_location': read_location
        })

        account1 = self.cmd('az cosmosdb create -n {acc} -g {rg} --locations {write_location}=0 --locations regionName={read_location} failoverPriority=1 isZoneRedundant=false').get_output_in_json()
        assert len(account1['writeLocations']) == 1
        assert len(account1['readLocations']) == 2
        assert account1['writeLocations'][0]['failoverPriority'] == 0
        assert account1['writeLocations'][0]['locationName'] == "East US"
        assert account1['readLocations'][0]['locationName'] == "West US" or account1['readLocations'][1]['locationName'] == "West US"
        assert account1['readLocations'][0]['failoverPriority'] == 1 or account1['readLocations'][1]['failoverPriority'] == 1

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_enable_multiple_write_locations(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-multiple-write-locations --default-consistency-level ConsistentPrefix')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableMultipleWriteLocations', True),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'ConsistentPrefix'),
        ]).get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_list_databases(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        keys = self.cmd('az cosmosdb list-keys -n {acc} -g {rg}').get_output_in_json()
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()

        self.kwargs.update({
            'primary_master_key': keys["primaryMasterKey"],
            'url': account['documentEndpoint']
        })

        self.cmd('az cosmosdb database list -n {acc} -g {rg}')
        self.cmd('az cosmosdb database list -n {acc} --key {primary_master_key}')
        self.cmd('az cosmosdb database list --url-connection {url} --key {primary_master_key}')

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_cosmosdb_network_rule_list(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40),
            'vnet': self.create_random_name(prefix='cli', length=40),
            'sub': self.create_random_name(prefix='cli', length=40)
        })

        vnet_output = self.cmd('az network vnet create --name {vnet} --resource-group {rg} --subnet-name {sub}').get_output_in_json()
        self.cmd('az network vnet subnet update -g {rg} --vnet-name {vnet} -n {sub} --service-endpoints Microsoft.AzureCosmosDB')

        self.kwargs.update({
            'subnet_id': vnet_output["newVNet"]["subnets"][0]["id"]
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-virtual-network --virtual-network-rule {subnet_id}').get_output_in_json()

        vnet_rules = self.cmd('az cosmosdb network-rule list -n {acc} -g {rg}').get_output_in_json()

        assert len(vnet_rules) == 1
        assert vnet_rules[0]["id"] == vnet_output["newVNet"]["subnets"][0]["id"]

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_cosmosdb_network_rule_add(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40),
            'vnet': self.create_random_name(prefix='cli', length=40),
            'sub': self.create_random_name(prefix='cli', length=40)
        })

        vnet_output = self.cmd('az network vnet create --name {vnet} --resource-group {rg} --subnet-name {sub}').get_output_in_json()

        self.kwargs.update({
            'subnet_id': vnet_output["newVNet"]["subnets"][0]["id"]
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-virtual-network')

        with self.assertRaisesRegexp(CLIError, "usage error: --subnet ID | --subnet NAME --vnet-name NAME"):
            self.cmd('az cosmosdb network-rule add -n {acc} -g {rg} --subnet {vnet}')

        vnet_rule = self.cmd('az cosmosdb network-rule add -n {acc} -g {rg} --virtual-network {vnet} --subnet {sub} --ignore-missing-vnet-service-endpoint').get_output_in_json()

        assert vnet_rule["virtualNetworkRules"][0]["id"] == vnet_output["newVNet"]["subnets"][0]["id"]
        assert vnet_rule["virtualNetworkRules"][0]["ignoreMissingVnetServiceEndpoint"]

        existing_rule = self.cmd('az cosmosdb network-rule add -n {acc} -g {rg} --vnet-name {vnet} --subnet {sub} --ignore-missing-endpoint').get_output_in_json()
        assert len(existing_rule["virtualNetworkRules"]) == 1

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_cosmosdb_network_rule_remove(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40),
            'vnet': self.create_random_name(prefix='cli', length=40),
            'sub': self.create_random_name(prefix='cli', length=40)
        })

        vnet_output = self.cmd('az network vnet create --name {vnet} --resource-group {rg} --subnet-name {sub}').get_output_in_json()

        self.kwargs.update({
            'subnet_id': vnet_output["newVNet"]["subnets"][0]["id"]
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-virtual-network')

        vnet_rule = self.cmd('az cosmosdb network-rule add -n {acc} -g {rg} --subnet {subnet_id} --ignore-missing-vnet-service-endpoint').get_output_in_json()

        assert vnet_rule["virtualNetworkRules"][0]["id"] == vnet_output["newVNet"]["subnets"][0]["id"]
        assert vnet_rule["virtualNetworkRules"][0]["ignoreMissingVnetServiceEndpoint"]

        self.cmd('az cosmosdb network-rule remove -n {acc} -g {rg} --subnet {subnet_id}')

        vnet_rules = self.cmd('az cosmosdb network-rule list -n {acc} -g {rg}').get_output_in_json()

        assert len(vnet_rules) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_plr')
    def test_cosmosdb_private_link_resource(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('cli-test-cosmosdb-plr-', 28),
            'loc': 'centraluseuap'
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('cosmosdb private-link-resource list --account-name {acc} --resource-group {rg}',
                 checks=[self.check('length(@)', 1), self.check('[0].groupId', 'Sql')])

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_pe')
    def test_cosmosdb_private_endpoint(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('cli-test-cosmosdb-pe-', 28),
            'loc': 'eastus2',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        # Prepare cosmos db account and network
        account = self.cmd('az cosmosdb create -n {acc} -g {rg}').get_output_in_json()
        self.kwargs['acc_id'] = account['id']
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd('network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
                      '--connection-name {pe_connection} --private-connection-resource-id {acc_id} '
                      '--group-ids Sql').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        results = self.kwargs['pe_id'].split('/')
        self.kwargs['pec_id'] = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}/privateEndpointConnections/{3}'.format(results[2], results[4], self.kwargs['acc'], results[-1])
        self.cmd('cosmosdb private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd('cosmosdb private-endpoint-connection show --account-name {acc} --name {pe_name} --resource-group {rg}',
                 checks=self.check('name', '{pe_name}'))
        self.cmd('cosmosdb private-endpoint-connection show -a {acc} -n {pe_name} -g {rg}',
                 checks=self.check('name', '{pe_name}'))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd('cosmosdb private-endpoint-connection approve --account-name {acc} --resource-group {rg} --name {pe_name} '
                 '--description "{approval_desc}"', checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', '{approval_desc}')
                 ])
        self.cmd('cosmosdb private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"', checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', '{rejection_desc}')
                 ])

        # Test delete
        self.cmd('cosmosdb private-endpoint-connection delete --id {pec_id}')

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_database')
    def test_cosmosdb_database(self, resource_group):

        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        database = self.cmd('az cosmosdb database create -g {rg} -n {acc} -d {db_name}').get_output_in_json()
        assert database["id"] == db_name

        database_show = self.cmd('az cosmosdb database show -g {rg} -n {acc} -d {db_name}').get_output_in_json()
        assert database_show["id"] == db_name

        assert self.cmd('az cosmosdb database exists -g {rg} -n {acc} -d {db_name}').get_output_in_json()
        assert not self.cmd('az cosmosdb database exists -g {rg} -n {acc} -d invalid').get_output_in_json()

        database_list = self.cmd('az cosmosdb database list -g {rg} -n {acc}').get_output_in_json()
        assert len(database_list) == 1

        self.cmd('az cosmosdb database delete -g {rg} -n {acc} -d {db_name} --yes')
        assert not self.cmd('az cosmosdb database exists -g {rg} -n {acc} -d {db_name}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_collection')
    def test_cosmosdb_collection(self, resource_group):

        col = self.create_random_name(prefix='cli', length=15)
        throughput = 500
        default_ttl = 1000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'col': col,
            'throughput': throughput,
            'ttl': default_ttl,
            'indexing': "\"{\"indexingMode\": \"consistent\", \"includedPaths\": [{ \"path\": \"/*\", \"indexes\": [{ \"dataType\": \"String\", \"kind\": \"Range\" }] }], \"excludedPaths\": [{ \"path\": \"/headquarters/employees/?\" } ]}\""
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('az cosmosdb database create -g {rg} -n {acc} -d {db_name}')

        collection = self.cmd('az cosmosdb collection create -g {rg} -n {acc} -d {db_name} -c {col} --default-ttl 0').get_output_in_json()
        assert collection["collection"]["id"] == col

        collection_show = self.cmd('az cosmosdb collection show -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()
        assert collection_show["collection"]["id"] == col

        assert self.cmd('az cosmosdb collection exists -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()
        assert not self.cmd('az cosmosdb collection exists -g {rg} -n {acc} -d {db_name} -c invalid').get_output_in_json()

        collection_list = self.cmd('az cosmosdb collection list -g {rg} -n {acc} -d {db_name}').get_output_in_json()
        assert len(collection_list) == 1

        # update throughput
        throughput_update = self.cmd('az cosmosdb collection update --throughput {throughput} -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()
        assert throughput_update["offer"]["content"]["offerThroughput"] == throughput

        # update ttl
        ttl_update = self.cmd('az cosmosdb collection update --default-ttl {ttl} -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()
        assert ttl_update["collection"]["defaultTtl"] == default_ttl

        # remove ttl
        disable_ttl = self.cmd('az cosmosdb collection update --default-ttl 0 -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()
        assert "defaultTtl" not in disable_ttl["collection"]

        self.cmd('az cosmosdb collection delete -g {rg} -n {acc} -d {db_name} -c {col} --yes')
        assert not self.cmd('az cosmosdb collection exists -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_database')
    def test_cosmosdb_sql_database(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        assert not self.cmd('az cosmosdb sql database exists -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        database_create = self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_create["name"] == db_name

        database_show = self.cmd('az cosmosdb sql database show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_show["name"] == db_name

        database_list = self.cmd('az cosmosdb sql database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 1

        assert self.cmd('az cosmosdb sql database exists -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        self.cmd('az cosmosdb sql database delete -g {rg} -a {acc} -n {db_name} --yes')
        database_list = self.cmd('az cosmosdb sql database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_container')
    def test_cosmosdb_sql_container(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)
        ctn_name = self.create_random_name(prefix='cli', length=15)
        partition_key = "/thePartitionKey"
        default_ttl = 1000
        new_default_ttl = 2000
        unique_key_policy = '"{\\"uniqueKeys\\": [{\\"paths\\": [\\"/path/to/key1\\"]}, {\\"paths\\": [\\"/path/to/key2\\"]}]}"'
        conflict_resolution_policy = '"{\\"mode\\": \\"lastWriterWins\\", \\"conflictResolutionPath\\": \\"/path\\"}"'
        indexing = '"{\\"indexingMode\\": \\"consistent\\", \\"automatic\\": true, \\"includedPaths\\": [{\\"path\\": \\"/*\\"}], \\"excludedPaths\\": [{\\"path\\": \\"/headquarters/employees/?\\"}]}"'

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
            'ctn_name': ctn_name,
            'part': partition_key,
            'ttl': default_ttl,
            'nttl': new_default_ttl,
            'unique_key': unique_key_policy,
            "conflict_resolution": conflict_resolution_policy,
            "indexing": indexing
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')

        assert not self.cmd('az cosmosdb sql container exists -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()

        container_create = self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --ttl {ttl} --unique-key-policy {unique_key} --conflict-resolution-policy {conflict_resolution} --idx {indexing}').get_output_in_json()

        assert container_create["name"] == ctn_name
        assert container_create["resource"]["partitionKey"]["paths"][0] == partition_key
        assert container_create["resource"]["defaultTtl"] == default_ttl
        assert len(container_create["resource"]["uniqueKeyPolicy"]["uniqueKeys"]) == 2
        assert container_create["resource"]["conflictResolutionPolicy"]["mode"] == "lastWriterWins"
        assert container_create["resource"]["indexingPolicy"]["excludedPaths"][0]["path"] == "/headquarters/employees/?"

        container_update = self.cmd('az cosmosdb sql container update -g {rg} -a {acc} -d {db_name} -n {ctn_name} --ttl {nttl}').get_output_in_json()
        assert container_update["resource"]["defaultTtl"] == new_default_ttl

        container_show = self.cmd('az cosmosdb sql container show -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()
        assert container_show["name"] == ctn_name

        container_list = self.cmd('az cosmosdb sql container list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(container_list) == 1

        assert self.cmd('az cosmosdb sql container exists -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()

        self.cmd('az cosmosdb sql container delete -g {rg} -a {acc} -d {db_name} -n {ctn_name} --yes')
        container_list = self.cmd('az cosmosdb sql container list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(container_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_container')
    def test_cosmosdb_sql_container_analytical_ttl(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)
        ctn_name = self.create_random_name(prefix='cli', length=15)
        partition_key = "/thePartitionKey"
        ttl = 3000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
            'ctn_name': ctn_name,
            'part': partition_key,
            'ttl': ttl
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-analytical-storage true')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')

        container_create = self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --analytical-storage-ttl {ttl}').get_output_in_json()

        assert container_create["resource"]["analyticalStorageTtl"] == ttl

        self.cmd('az cosmosdb sql container delete -g {rg} -a {acc} -d {db_name} -n {ctn_name} --yes')
        container_list = self.cmd('az cosmosdb sql container list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(container_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_stored_procedure')
    def test_cosmosdb_sql_stored_procedure(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)
        ctn_name = self.create_random_name(prefix='cli', length=15)
        partition_key = "/thePartitionKey"
        sproc_name = self.create_random_name(prefix='cli', length=15)
        body = "sampleBody"
        nbody = "sampleBody2"

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
            'ctn_name': ctn_name,
            'part': partition_key,
            'sproc_name': sproc_name,
            'body': body,
            'nbody': nbody
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} ').get_output_in_json()
        sproc_create = self.cmd('az cosmosdb sql stored-procedure create --resource-group {rg} -a {acc} -d {db_name} -c {ctn_name} -n {sproc_name} -b {body}').get_output_in_json()

        assert sproc_create["name"] == sproc_name
        assert sproc_create["resource"]["body"] == body

        sproc_update = self.cmd('az cosmosdb sql stored-procedure update -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {sproc_name} -b {nbody}').get_output_in_json()
        assert sproc_update["resource"]["body"] == nbody

        sproc_show = self.cmd('az cosmosdb sql stored-procedure show -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {sproc_name}').get_output_in_json()
        assert sproc_show["name"] == sproc_name

        sproc_list = self.cmd('az cosmosdb sql stored-procedure list -g {rg} -a {acc} -d {db_name} -c {ctn_name}').get_output_in_json()
        assert len(sproc_list) == 1

        self.cmd('az cosmosdb sql stored-procedure delete -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {sproc_name} --yes')
        sproc_list = self.cmd('az cosmosdb sql stored-procedure list -g {rg} -a {acc} -d {db_name} -c {ctn_name}').get_output_in_json()
        assert len(sproc_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_user_defined_function')
    def test_cosmosdb_sql_user_defined_function(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)
        ctn_name = self.create_random_name(prefix='cli', length=15)
        partition_key = "/thePartitionKey"
        udf_name = self.create_random_name(prefix='cli', length=15)
        body = "sampleBody"
        nbody = "sampleBody2"

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
            'ctn_name': ctn_name,
            'part': partition_key,
            'udf_name': udf_name,
            'body': body,
            'nbody': nbody
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} ').get_output_in_json()
        udf_create = self.cmd('az cosmosdb sql user-defined-function create --resource-group {rg} -a {acc} -d {db_name} -c {ctn_name} -n {udf_name} -b {body}').get_output_in_json()

        assert udf_create["name"] == udf_name
        assert udf_create["resource"]["body"] == body

        udf_update = self.cmd('az cosmosdb sql user-defined-function update -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {udf_name} -b {nbody}').get_output_in_json()
        assert udf_update["resource"]["body"] == nbody

        udf_show = self.cmd('az cosmosdb sql user-defined-function show -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {udf_name}').get_output_in_json()
        assert udf_show["name"] == udf_name

        udf_list = self.cmd('az cosmosdb sql user-defined-function list -g {rg} -a {acc} -d {db_name} -c {ctn_name}').get_output_in_json()
        assert len(udf_list) == 1

        self.cmd('az cosmosdb sql user-defined-function delete -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {udf_name} --yes')
        udf_list = self.cmd('az cosmosdb sql user-defined-function list -g {rg} -a {acc} -d {db_name} -c {ctn_name}').get_output_in_json()
        assert len(udf_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_trigger')
    def test_cosmosdb_sql_trigger(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)
        ctn_name = self.create_random_name(prefix='cli', length=15)
        partition_key = "/thePartitionKey"
        trigger_name = self.create_random_name(prefix='cli', length=15)
        body = "sampleBody"
        trigger_type = "Pre"
        trigger_operation = "Delete"
        nbody = "sampleBody2"

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
            'ctn_name': ctn_name,
            'part': partition_key,
            'trigger_name': trigger_name,
            'body': body,
            'type': trigger_type,
            'op': trigger_operation,
            'nbody': nbody
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} ').get_output_in_json()
        trigger_create = self.cmd('az cosmosdb sql trigger create --resource-group {rg} -a {acc} -d {db_name} -c {ctn_name} -n {trigger_name} -b {body}').get_output_in_json()

        assert trigger_create["name"] == trigger_name
        assert trigger_create["resource"]["body"] == body

        trigger_update = self.cmd('az cosmosdb sql trigger update -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {trigger_name} -b {nbody} --operation {op} -t {type}').get_output_in_json()
        assert trigger_update["resource"]["body"] == nbody
        assert trigger_update["resource"]["triggerOperation"] == trigger_operation
        assert trigger_update["resource"]["triggerType"] == trigger_type

        trigger_show = self.cmd('az cosmosdb sql trigger show -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {trigger_name}').get_output_in_json()
        assert trigger_show["name"] == trigger_name

        trigger_list = self.cmd('az cosmosdb sql trigger list -g {rg} -a {acc} -d {db_name} -c {ctn_name}').get_output_in_json()
        assert len(trigger_list) == 1

        self.cmd('az cosmosdb sql trigger delete -g {rg} -a {acc} -d {db_name} -c {ctn_name} -n {trigger_name} --yes')
        trigger_list = self.cmd('az cosmosdb sql trigger list -g {rg} -a {acc} -d {db_name} -c {ctn_name}').get_output_in_json()
        assert len(trigger_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_role')
    def test_cosmosdb_sql_role(self, resource_group):
        acc_name = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        subscription = self.get_subscription_id()
        role_def_id = uuid.uuid4()
        role_assignment_id = uuid.uuid4()
        role_definition_create_body = ' {{ \\"Id\\": \\"{0}\\", \\"RoleName\\": \\"roleName\\", \\"Type\\": \\"CustomRole\\", \\"AssignableScopes\\": [ \\"/\\" ], \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/create\\", \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read\\" ] }} '.format(role_def_id)
        role_definition_update_body = ' {{ \\"Id\\": \\"{0}\\", \\"RoleName\\": \\"roleName2\\", \\"Type\\": \\"CustomRole\\", \\"AssignableScopes\\": [ \\"/\\" ], \\"Permissions\\": [ {{ \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/create\\" ] }}, {{ \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read\\" ] }} ] }}'.format(role_def_id)
        role_definition_create_body2 = ' { \\"RoleName\\": \\"roleName3\\", \\"AssignableScopes\\": [ \\"/\\" ], \\"Permissions\\": [ { \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/create\\" ] }, { \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read\\" ] }, { \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/replace\\" ] } ] } '
        fully_qualified_role_def_id = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}/sqlRoleDefinitions/{3}'.format(subscription, resource_group, acc_name, role_def_id)
        fully_qualified_role_assignment_id = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}/sqlRoleAssignments/{3}'.format(subscription, resource_group, acc_name, role_assignment_id)
        assignable_scope = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}'.format(subscription, resource_group, acc_name)
        scope = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}/dbs/{3}'.format(subscription, resource_group, acc_name, db_name)
        principal_id = 'ed4c2395-a18c-4018-afb3-6e521e7534d2'

        self.kwargs.update({
            'acc': acc_name,
            'db_name': db_name,
            'create_body': role_definition_create_body,
            'update_body': role_definition_update_body,
            'create_body2': role_definition_create_body2,
            'role_def_id': role_def_id,
            'fully_qualified_role_def_id': fully_qualified_role_def_id,
            'role_assignment_id': role_assignment_id,
            'fully_qualified_role_assignment_id': fully_qualified_role_assignment_id,
            'scope': scope,
            'principal_id': principal_id
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --locations regionName=eastus2')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')
        self.cmd('az cosmosdb sql role definition create -g {rg} -a {acc} -b "{create_body}"', checks=[
            self.check('id', fully_qualified_role_def_id),
            self.check('roleName', 'roleName'),
            self.check('sqlRoleDefinitionGetResultsType', 'CustomRole'),
            self.check('assignableScopes[0]', assignable_scope),
            self.check('length(permissions)', 1)
        ])

        assert self.cmd('az cosmosdb sql role definition exists -g {rg} -a {acc} -i {role_def_id}').get_output_in_json()

        role_definition_show = self.cmd('az cosmosdb sql role definition show -g {rg} -a {acc} -i {role_def_id}', checks=[
            self.check('roleName', 'roleName')
        ])

        role_definition_update = self.cmd('az cosmosdb sql role definition update -g {rg} -a {acc} -b "{update_body}"', checks=[
            self.check('id', fully_qualified_role_def_id),
            self.check('roleName', 'roleName2'),
            self.check('sqlRoleDefinitionGetResultsType', 'CustomRole'),
            self.check('assignableScopes[0]', assignable_scope),
            self.check('length(permissions)', 2)
        ])

        role_definition_create2 = self.cmd('az cosmosdb sql role definition create -g {rg} -a {acc} -b "{create_body2}"', checks=[
            self.check('roleName', 'roleName3'),
            self.check('sqlRoleDefinitionGetResultsType', 'CustomRole'),
            self.check('assignableScopes[0]', assignable_scope),
            self.check('length(permissions)', 3)
        ]).get_output_in_json()

        role_definition_list = self.cmd('az cosmosdb sql role definition list -g {rg} -a {acc}').get_output_in_json()
        assert len(role_definition_list) == 2

        role_assignment_create = self.cmd('az cosmosdb sql role assignment create -g {rg} -a {acc} -s {scope} -p {principal_id} -d {fully_qualified_role_def_id} -i {role_assignment_id}', checks=[
            self.check('id', fully_qualified_role_assignment_id),
            self.check('roleDefinitionId', fully_qualified_role_def_id),
            self.check('scope', scope),
            self.check('principalId', principal_id)
        ])

        assert self.cmd('az cosmosdb sql role assignment exists -g {rg} -a {acc} -i {role_assignment_id}').get_output_in_json()

        role_assignment_show = self.cmd('az cosmosdb sql role assignment show -g {rg} -a {acc} -i {role_assignment_id}', checks=[
            self.check('id', fully_qualified_role_assignment_id)
        ])

        self.kwargs.update({
            'fully_qualified_role_def_id2': role_definition_create2['name']
        })

        role_assignment_update = self.cmd('az cosmosdb sql role assignment update -g {rg} -a {acc} -d {fully_qualified_role_def_id2} -i {fully_qualified_role_assignment_id}', checks=[
            self.check('id', fully_qualified_role_assignment_id),
            self.check('roleDefinitionId', role_definition_create2['id']),
            self.check('scope', scope),
            self.check('principalId', principal_id)
        ])

        role_assignment_list = self.cmd('az cosmosdb sql role assignment list -g {rg} -a {acc}').get_output_in_json()
        assert len(role_assignment_list) == 1

        self.cmd('az cosmosdb sql role assignment delete -g {rg} -a {acc} -i {role_assignment_id} --yes')
        role_assignment_list = self.cmd('az cosmosdb sql role assignment list -g {rg} -a {acc}').get_output_in_json()
        assert len(role_assignment_list) == 0

        self.cmd('az cosmosdb sql role definition delete -g {rg} -a {acc} -i {role_def_id} --yes')
        self.cmd('az cosmosdb sql role definition delete -g {rg} -a {acc} -i {fully_qualified_role_def_id2} --yes')
        role_definition_list = self.cmd('az cosmosdb sql role definition list -g {rg} -a {acc}').get_output_in_json()
        assert len(role_definition_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongodb_database')
    def test_cosmosdb_mongodb_database(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB')

        assert not self.cmd('az cosmosdb mongodb database exists -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        database_create = self.cmd('az cosmosdb mongodb database create -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_create["name"] == db_name

        database_show = self.cmd('az cosmosdb mongodb database show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_show["name"] == db_name

        database_list = self.cmd('az cosmosdb mongodb database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 1

        assert self.cmd('az cosmosdb mongodb database exists -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        self.cmd('az cosmosdb mongodb database delete -g {rg} -a {acc} -n {db_name} --yes')
        database_list = self.cmd('az cosmosdb mongodb database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongodb_collection')
    def test_cosmosdb_mongodb_collection(self, resource_group):
        col_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'col_name': col_name,
            'shard_key': "theShardKey",
            'indexes': '"[{\\"key\\": {\\"keys\\": [\\"_ts\\"]},\\"options\\": {\\"expireAfterSeconds\\": 1000}}]"',
            'ttl': "3000",
            'new_ttl': "6000"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB --enable-analytical-storage true')
        self.cmd('az cosmosdb mongodb database create -g {rg} -a {acc} -n {db_name}')

        assert not self.cmd('az cosmosdb mongodb collection exists -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()

        collection_create = self.cmd(
            'az cosmosdb mongodb collection create -g {rg} -a {acc} -d {db_name} -n {col_name} --shard {shard_key} --analytical-storage-ttl {ttl}').get_output_in_json()
        assert collection_create["name"] == col_name

        collection_update = self.cmd(
            'az cosmosdb mongodb collection update -g {rg} -a {acc} -d {db_name} -n {col_name} --idx {indexes} --analytical-storage-ttl {new_ttl}').get_output_in_json()
        assert len(collection_update["resource"]["indexes"]) == 1

        collection_show = self.cmd(
            'az cosmosdb mongodb collection show -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()
        assert collection_show["name"] == col_name

        collection_list = self.cmd(
            'az cosmosdb mongodb collection list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(collection_list) == 1

        assert self.cmd('az cosmosdb mongodb collection exists -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()

        self.cmd('az cosmosdb mongodb collection delete -g {rg} -a {acc} -d {db_name} -n {col_name} --yes')
        collection_list = self.cmd(
            'az cosmosdb mongodb collection list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(collection_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_cassandra_keyspace')
    def test_cosmosdb_cassandra_keyspace(self, resource_group):
        ks_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'ks_name': ks_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableCassandra')

        assert not self.cmd('az cosmosdb cassandra keyspace exists -g {rg} -a {acc} -n {ks_name}').get_output_in_json()

        keyspace_create = self.cmd('az cosmosdb cassandra keyspace create -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert keyspace_create["name"] == ks_name

        keyspace_show = self.cmd('az cosmosdb cassandra keyspace show -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert keyspace_show["name"] == ks_name

        keyspace_list = self.cmd('az cosmosdb cassandra keyspace list -g {rg} -a {acc}').get_output_in_json()
        assert len(keyspace_list) == 1

        assert self.cmd('az cosmosdb cassandra keyspace exists -g {rg} -a {acc} -n {ks_name}').get_output_in_json()

        self.cmd('az cosmosdb cassandra keyspace delete -g {rg} -a {acc} -n {ks_name} --yes')
        keyspace_list = self.cmd('az cosmosdb cassandra keyspace list -g {rg} -a {acc}').get_output_in_json()
        assert len(keyspace_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_cassandra_table')
    def test_cosmosdb_cassandra_table(self, resource_group):
        table_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'ks_name': self.create_random_name(prefix='cli', length=15),
            'table_name': table_name,
            'schema': '"{\\"columns\\": [{\\"name\\": \\"columnA\\",\\"type\\": \\"Ascii\\"}],\\"partitionKeys\\": [{\\"name\\": \\"columnA\\"}]}"',
            'new_schema': '"{\\"columns\\": [{\\"name\\": \\"columnA\\",\\"type\\": \\"Ascii\\"}, {\\"name\\": \\"columnB\\",\\"type\\": \\"Ascii\\"}],\\"partitionKeys\\": [{\\"name\\": \\"columnA\\"}]}"',
            'ttl': "3000",
            'new_ttl': "6000"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableCassandra --enable-analytical-storage true')
        self.cmd('az cosmosdb cassandra keyspace create -g {rg} -a {acc} -n {ks_name}').get_output_in_json()

        assert not self.cmd('az cosmosdb cassandra table exists -g {rg} -a {acc} -k {ks_name} -n {table_name}').get_output_in_json()

        table_create = self.cmd('az cosmosdb cassandra table create -g {rg} -a {acc} -k {ks_name} -n {table_name} --schema {schema} --analytical-storage-ttl {ttl}').get_output_in_json()
        assert table_create["name"] == table_name
        assert len(table_create["resource"]["schema"]["columns"]) == 1

        table_update = self.cmd('az cosmosdb cassandra table update -g {rg} -a {acc} -k {ks_name} -n {table_name} --schema {new_schema} --analytical-storage-ttl {new_ttl}').get_output_in_json()
        assert len(table_update["resource"]["schema"]["columns"]) == 2

        table_show = self.cmd('az cosmosdb cassandra table show -g {rg} -a {acc} -k {ks_name} -n {table_name}').get_output_in_json()
        assert table_show["name"] == table_name

        table_list = self.cmd('az cosmosdb cassandra table list -g {rg} -a {acc} -k {ks_name}').get_output_in_json()
        assert len(table_list) == 1

        assert self.cmd('az cosmosdb cassandra table exists -g {rg} -a {acc} -k {ks_name} -n {table_name}').get_output_in_json()

        self.cmd('az cosmosdb cassandra table delete -g {rg} -a {acc} -k {ks_name} -n {table_name} --yes')
        table_list = self.cmd('az cosmosdb cassandra table list -g {rg} -a {acc} -k {ks_name}').get_output_in_json()
        assert len(table_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_gremlin_database')
    def test_cosmosdb_gremlin_database(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableGremlin')

        assert not self.cmd('az cosmosdb gremlin database exists -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        database_create = self.cmd('az cosmosdb gremlin database create -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_create["name"] == db_name

        database_show = self.cmd('az cosmosdb gremlin database show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_show["name"] == db_name

        database_list = self.cmd('az cosmosdb gremlin database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 1

        assert self.cmd('az cosmosdb gremlin database exists -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        self.cmd('az cosmosdb gremlin database delete -g {rg} -a {acc} -n {db_name} --yes')
        database_list = self.cmd('az cosmosdb gremlin database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_gremlin_graph')
    def test_cosmosdb_gremlin_graph(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)
        gp_name = self.create_random_name(prefix='cli', length=15)
        partition_key = "/thePartitionKey"
        default_ttl = 1000
        new_default_ttl = 2000
        conflict_resolution_policy = '"{\\"mode\\": \\"lastWriterWins\\", \\"conflictResolutionPath\\": \\"/path\\"}"'
        indexing = '"{\\"indexingMode\\": \\"consistent\\", \\"automatic\\": true, \\"includedPaths\\": [{\\"path\\": \\"/*\\"}], \\"excludedPaths\\": [{\\"path\\": \\"/headquarters/employees/?\\"}]}"'

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
            'gp_name': gp_name,
            'part': partition_key,
            'ttl': default_ttl,
            'nttl': new_default_ttl,
            "conflict_resolution": conflict_resolution_policy,
            "indexing": indexing
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableGremlin')
        self.cmd('az cosmosdb gremlin database create -g {rg} -a {acc} -n {db_name}')

        assert not self.cmd('az cosmosdb gremlin graph exists -g {rg} -a {acc} -d {db_name} -n {gp_name}').get_output_in_json()

        graph_create = self.cmd('az cosmosdb gremlin graph create -g {rg} -a {acc} -d {db_name} -n {gp_name} -p {part} --ttl {ttl} --conflict-resolution-policy {conflict_resolution} --idx {indexing}').get_output_in_json()
        assert graph_create["name"] == gp_name
        assert graph_create["resource"]["partitionKey"]["paths"][0] == partition_key
        assert graph_create["resource"]["defaultTtl"] == default_ttl
        assert graph_create["resource"]["conflictResolutionPolicy"]["mode"] == "lastWriterWins"
        assert graph_create["resource"]["indexingPolicy"]["excludedPaths"][0]["path"] == "/headquarters/employees/?"

        graph_update = self.cmd('az cosmosdb gremlin graph update -g {rg} -a {acc} -d {db_name} -n {gp_name} --ttl {nttl}').get_output_in_json()
        assert graph_update["resource"]["defaultTtl"] == new_default_ttl

        graph_show = self.cmd('az cosmosdb gremlin graph show -g {rg} -a {acc} -d {db_name} -n {gp_name}').get_output_in_json()
        assert graph_show["name"] == gp_name

        graph_list = self.cmd('az cosmosdb gremlin graph list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(graph_list) == 1

        assert self.cmd('az cosmosdb gremlin graph exists -g {rg} -a {acc} -d {db_name} -n {gp_name}').get_output_in_json()

        self.cmd('az cosmosdb gremlin graph delete -g {rg} -a {acc} -d {db_name} -n {gp_name} --yes')
        graph_list = self.cmd('az cosmosdb gremlin graph list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(graph_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_table')
    def test_cosmosdb_table(self, resource_group):
        table_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'table_name': table_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableTable')

        assert not self.cmd('az cosmosdb table exists -g {rg} -a {acc} -n {table_name}').get_output_in_json()

        table_create = self.cmd('az cosmosdb table create -g {rg} -a {acc} -n {table_name}').get_output_in_json()
        assert table_create["name"] == table_name

        table_show = self.cmd('az cosmosdb table show -g {rg} -a {acc} -n {table_name}').get_output_in_json()
        assert table_show["name"] == table_name

        table_list = self.cmd('az cosmosdb table list -g {rg} -a {acc}').get_output_in_json()
        assert len(table_list) == 1

        assert self.cmd('az cosmosdb table exists -g {rg} -a {acc} -n {table_name}').get_output_in_json()

        self.cmd('az cosmosdb table delete -g {rg} -a {acc} -n {table_name} --yes')
        table_list = self.cmd('az cosmosdb table list -g {rg} -a {acc}').get_output_in_json()
        assert len(table_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_resource_throughput')
    def test_cosmosdb_sql_resource_throughput(self, resource_group):
        tp1 = 1000
        tp2 = 2000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'ctn_name': self.create_random_name(prefix='cli', length=15),
            'part': "/thePartitionKey",
            'tp1': tp1,
            'tp2': tp2,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb sql database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb sql database throughput update -g {rg} -a {acc} -n {db_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["throughput"] == tp2

        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --throughput {tp1}')
        ctn_throughput_show = self.cmd('az cosmosdb sql container throughput show -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()
        assert ctn_throughput_show["resource"]["throughput"] == tp1

        ctn_througput_update = self.cmd('az cosmosdb sql container throughput update -g {rg} -a {acc} -d {db_name} -n {ctn_name} --throughput {tp2}').get_output_in_json()
        assert ctn_througput_update["resource"]["throughput"] == tp2

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_resource_throughput_autoscale')
    def test_cosmosdb_sql_resource_throughput_autoscale(self, resource_group):
        tp1 = 800
        tp2 = 8000
        tp3 = 400
        tp4 = 5000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'ctn_name': self.create_random_name(prefix='cli', length=15),
            'part': "/thePartitionKey",
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp4': tp4,
            'autoscale': "autoscale",
            'manual': "manual"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb sql database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        self.cmd('az cosmosdb sql database throughput migrate -g {rg} -a {acc} -n {db_name} -t {autoscale}').get_output_in_json()

        db_throughput_show = self.cmd('az cosmosdb sql database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"]

        db_througput_update = self.cmd('az cosmosdb sql database throughput update -g {rg} -a {acc} -n {db_name} --max-throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

        self.cmd('az cosmosdb sql database throughput migrate --throughput-type {manual} -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --throughput {tp3}')
        ctn_throughput_show = self.cmd('az cosmosdb sql container throughput show -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()
        assert ctn_throughput_show["resource"]["throughput"] == tp3

        self.cmd('az cosmosdb sql container throughput migrate -g {rg} -a {acc} -d {db_name} -n {ctn_name} --throughput-type {autoscale}').get_output_in_json()

        ctn_througput_update = self.cmd('az cosmosdb sql container throughput update -g {rg} -a {acc} -d {db_name} -n {ctn_name} --max-throughput {tp4}').get_output_in_json()
        assert ctn_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp4

        self.cmd('az cosmosdb sql container throughput migrate --throughput-type {manual} -g {rg} -a {acc} -d {db_name} -n {ctn_name}')

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongodb_resource_throughput_autoscale')
    def test_cosmosdb_mongodb_resource_throughput_autoscale(self, resource_group):
        tp1 = 800
        tp2 = 8000
        tp3 = 400
        tp4 = 5000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'col_name': self.create_random_name(prefix='cli', length=15),
            'shard_key': "theShardKey",
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp4': tp4,
            'autoscale': "autoscale",
            'manual': "manual"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB')

        self.cmd('az cosmosdb mongodb database create -g {rg} -a {acc} -n {db_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb mongodb database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        self.cmd('az cosmosdb mongodb database throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        db_throughput_show = self.cmd('az cosmosdb mongodb database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"]

        db_througput_update = self.cmd('az cosmosdb mongodb database throughput update -g {rg} -a {acc} -n {db_name} --max-throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

        self.cmd('az cosmosdb mongodb database throughput migrate --throughput-type {manual} -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        self.cmd('az cosmosdb mongodb collection create -g {rg} -a {acc} -d {db_name} -n {col_name} --throughput {tp3} --shard {shard_key}')
        col_throughput_show = self.cmd('az cosmosdb mongodb collection throughput show -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()
        assert col_throughput_show["resource"]["throughput"] == tp3

        self.cmd('az cosmosdb mongodb collection throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()

        col_througput_update = self.cmd('az cosmosdb mongodb collection throughput update -g {rg} -a {acc} -d {db_name} -n {col_name} --max-throughput {tp4}').get_output_in_json()
        assert col_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp4

        self.cmd('az cosmosdb mongodb collection throughput migrate --throughput-type {manual} -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_cassandra_resource_throughput_autoscale')
    def test_cosmosdb_cassandra_resource_throughput_autoscale(self, resource_group):
        tp1 = 800
        tp2 = 8000
        tp3 = 400
        tp4 = 5000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'ks_name': self.create_random_name(prefix='cli', length=15),
            'tb_name': self.create_random_name(prefix='cli', length=15),
            'schema': '"{\\"columns\\": [{\\"name\\": \\"columnA\\",\\"type\\": \\"Ascii\\"}],\\"partitionKeys\\": [{\\"name\\": \\"columnA\\"}]}"',
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp4': tp4,
            'manual': "manual",
            'autoscale': "autoscale"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableCassandra')

        self.cmd('az cosmosdb cassandra keyspace create -g {rg} -a {acc} -n {ks_name} --throughput {tp1}')
        ks_throughput_show = self.cmd('az cosmosdb cassandra keyspace throughput show -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert ks_throughput_show["resource"]["throughput"] == tp1

        self.cmd('az cosmosdb cassandra keyspace throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} -n {ks_name}').get_output_in_json()

        ks_throughput_show = self.cmd('az cosmosdb cassandra keyspace throughput show -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert ks_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"]

        ks_througput_update = self.cmd('az cosmosdb cassandra keyspace throughput update -g {rg} -a {acc} -n {ks_name} --max-throughput {tp2}').get_output_in_json()
        assert ks_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

        self.cmd('az cosmosdb cassandra keyspace throughput migrate --throughput-type {manual} -g {rg} -a {acc} -n {ks_name}').get_output_in_json()

        self.cmd('az cosmosdb cassandra table create -g {rg} -a {acc} --keyspace-name {ks_name} -n {tb_name} --throughput {tp3} --schema {schema}')
        tb_throughput_show = self.cmd('az cosmosdb cassandra table throughput show -g {rg} -a {acc} --keyspace-name {ks_name} -n {tb_name}').get_output_in_json()
        assert tb_throughput_show["resource"]["throughput"] == tp3

        self.cmd('az cosmosdb cassandra table throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} --keyspace-name {ks_name} -n {tb_name}').get_output_in_json()

        tb_througput_update = self.cmd('az cosmosdb cassandra table throughput update -g {rg} -a {acc} --keyspace-name {ks_name} -n {tb_name} --max-throughput {tp4}').get_output_in_json()
        assert tb_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp4

        self.cmd('az cosmosdb cassandra table throughput migrate --throughput-type {manual} -g {rg} -a {acc} --keyspace-name {ks_name} -n {tb_name}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_gremlin_resource_throughput_autoscale')
    def test_cosmosdb_gremlin_resource_throughput_autoscale(self, resource_group):
        tp1 = 800
        tp2 = 8000
        tp3 = 400
        tp4 = 5000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'graph_name': self.create_random_name(prefix='cli', length=15),
            'part': "/thePartitionKey",
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp4': tp4,
            'manual': "manual",
            'autoscale': "autoscale"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableGremlin')

        self.cmd('az cosmosdb gremlin database create -g {rg} -a {acc} -n {db_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb gremlin database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        self.cmd('az cosmosdb gremlin database throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        db_throughput_show = self.cmd('az cosmosdb gremlin database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"]

        db_througput_update = self.cmd('az cosmosdb gremlin database throughput update -g {rg} -a {acc} -n {db_name} --max-throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

        self.cmd('az cosmosdb gremlin database throughput migrate --throughput-type {manual} -g {rg} -a {acc} -n {db_name}').get_output_in_json()

        self.cmd('az cosmosdb gremlin graph create -g {rg} -a {acc} -d {db_name} -n {graph_name} -p {part} --throughput {tp3}')
        graph_throughput_show = self.cmd('az cosmosdb gremlin graph throughput show -g {rg} -a {acc} -d {db_name} -n {graph_name}').get_output_in_json()
        assert graph_throughput_show["resource"]["throughput"] == tp3

        self.cmd('az cosmosdb gremlin graph throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} -d {db_name} -n {graph_name}').get_output_in_json()

        graph_througput_update = self.cmd('az cosmosdb gremlin graph throughput update -g {rg} -a {acc} -d {db_name} -n {graph_name} --max-throughput {tp4}').get_output_in_json()
        assert graph_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp4

        self.cmd('az cosmosdb gremlin graph throughput migrate --throughput-type {manual} -g {rg} -a {acc} -d {db_name} -n {graph_name}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_table_resource_throughput_autoscale')
    def test_cosmosdb_table_resource_throughput_autoscale(self, resource_group):
        tp1 = 800
        tp2 = 8000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'table_name': self.create_random_name(prefix='cli', length=15),
            'tp1': tp1,
            'tp2': tp2,
            'manual': "manual",
            'autoscale': "autoscale"
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableTable')

        self.cmd('az cosmosdb table create -g {rg} -a {acc} -n {table_name} --throughput {tp1}')
        table_throughput_show = self.cmd('az cosmosdb table throughput show -g {rg} -a {acc} -n {table_name}').get_output_in_json()
        assert table_throughput_show["resource"]["throughput"] == tp1

        self.cmd('az cosmosdb table throughput migrate --throughput-type {autoscale} -g {rg} -a {acc} -n {table_name}').get_output_in_json()

        table_throughput_show = self.cmd('az cosmosdb table throughput show -g {rg} -a {acc} -n {table_name}').get_output_in_json()
        assert table_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"]

        table_througput_update = self.cmd('az cosmosdb table throughput update -g {rg} -a {acc} -n {table_name} --max-throughput {tp2}').get_output_in_json()
        assert table_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

        self.cmd('az cosmosdb table throughput migrate --throughput-type {manual} -g {rg} -a {acc} -n {table_name}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_resource_max_throughput')
    def test_cosmosdb_sql_resource_max_throughput(self, resource_group):
        tp1 = 6000
        tp2 = 8000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'ctn_name': self.create_random_name(prefix='cli', length=15),
            'part': "/thePartitionKey",
            'tp1': tp1,
            'tp2': tp2,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name} --max-throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb sql database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb sql database throughput update -g {rg} -a {acc} -n {db_name} --max-throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --max-throughput {tp1}')
        ctn_throughput_show = self.cmd('az cosmosdb sql container throughput show -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()
        assert ctn_throughput_show["resource"]["autoscaleSettings"]["maxThroughput"] == tp1

        ctn_througput_update = self.cmd('az cosmosdb sql container throughput update -g {rg} -a {acc} -d {db_name} -n {ctn_name} --max-throughput {tp2}').get_output_in_json()
        assert ctn_througput_update["resource"]["autoscaleSettings"]["maxThroughput"] == tp2

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongodb_resource_throughput')
    def test_cosmosdb_mongodb_resource_throughput(self, resource_group):
        tp1 = 1000
        tp2 = 2000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'col_name': self.create_random_name(prefix='cli', length=15),
            'shard_key': "theShardKey",
            'tp1': tp1,
            'tp2': tp2,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB')

        self.cmd('az cosmosdb mongodb database create -g {rg} -a {acc} -n {db_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb mongodb database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb mongodb database throughput update -g {rg} -a {acc} -n {db_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["throughput"] == tp2

        self.cmd('az cosmosdb mongodb collection create -g {rg} -a {acc} -d {db_name} -n {col_name} --shard {shard_key} --throughput {tp1}')
        col_throughput_show = self.cmd('az cosmosdb mongodb collection throughput show -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()
        assert col_throughput_show["resource"]["throughput"] == tp1

        col_througput_update = self.cmd('az cosmosdb mongodb collection throughput update -g {rg} -a {acc} -d {db_name} -n {col_name} --throughput {tp2}').get_output_in_json()
        assert col_througput_update["resource"]["throughput"] == tp2

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_cassandra_resource_throughput')
    def test_cosmosdb_cassandra_resource_throughput(self, resource_group):
        tp1 = 1000
        tp2 = 2000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'ks_name': self.create_random_name(prefix='cli', length=15),
            'tb_name': self.create_random_name(prefix='cli', length=15),
            'schema': '"{\\"columns\\": [{\\"name\\": \\"columnA\\",\\"type\\": \\"Ascii\\"}],\\"partitionKeys\\": [{\\"name\\": \\"columnA\\"}]}"',
            'tp1': tp1,
            'tp2': tp2,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableCassandra')

        self.cmd('az cosmosdb cassandra keyspace create -g {rg} -a {acc} -n {ks_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb cassandra keyspace throughput show -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb cassandra keyspace throughput update -g {rg} -a {acc} -n {ks_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["throughput"] == tp2

        self.cmd('az cosmosdb cassandra table create -g {rg} -a {acc} -k {ks_name} -n {tb_name} --throughput {tp1} --schema {schema}')
        col_throughput_show = self.cmd('az cosmosdb cassandra table throughput show -g {rg} -a {acc} -k {ks_name} -n {tb_name}').get_output_in_json()
        assert col_throughput_show["resource"]["throughput"] == tp1

        col_througput_update = self.cmd('az cosmosdb cassandra table throughput update -g {rg} -a {acc} -k {ks_name} -n {tb_name} --throughput {tp2}').get_output_in_json()
        assert col_througput_update["resource"]["throughput"] == tp2

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_gremlin_resource_throughput')
    def test_cosmosdb_gremlin_resource_throughput(self, resource_group):
        tp1 = 1000
        tp2 = 2000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': self.create_random_name(prefix='cli', length=15),
            'gp_name': self.create_random_name(prefix='cli', length=15),
            'part': "/thePartitionKey",
            'tp1': tp1,
            'tp2': tp2,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableGremlin')

        self.cmd('az cosmosdb gremlin database create -g {rg} -a {acc} -n {db_name} --throughput {tp1}')
        db_throughput_show = self.cmd(
            'az cosmosdb gremlin database throughput show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        db_througput_update = self.cmd(
            'az cosmosdb gremlin database throughput update -g {rg} -a {acc} -n {db_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["throughput"] == tp2

        self.cmd('az cosmosdb gremlin graph create -g {rg} -a {acc} -d {db_name} -n {gp_name} -p {part} --throughput {tp1}')
        col_throughput_show = self.cmd(
            'az cosmosdb gremlin graph throughput show -g {rg} -a {acc} -d {db_name} -n {gp_name}').get_output_in_json()
        assert col_throughput_show["resource"]["throughput"] == tp1

        col_througput_update = self.cmd(
            'az cosmosdb gremlin graph throughput update -g {rg} -a {acc} -d {db_name} -n {gp_name} --throughput {tp2}').get_output_in_json()
        assert col_througput_update["resource"]["throughput"] == tp2

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_table_resource_throughput')
    def test_cosmosdb_table_resource_throughput(self, resource_group):
        tp1 = 1000
        tp2 = 2000

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'tb_name': self.create_random_name(prefix='cli', length=15),
            'tp1': tp1,
            'tp2': tp2,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableTable')

        self.cmd('az cosmosdb table create -g {rg} -a {acc} -n {tb_name} --throughput {tp1}')
        db_throughput_show = self.cmd('az cosmosdb table throughput show -g {rg} -a {acc} -n {tb_name}').get_output_in_json()
        assert db_throughput_show["resource"]["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb table throughput update -g {rg} -a {acc} -n {tb_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["resource"]["throughput"] == tp2

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_key_vault_key_uri')
    def test_cosmosdb_key_vault_key_uri(self, resource_group):
        kv_name = self.create_random_name(prefix='cli', length=15)
        key_name = self.create_random_name(prefix='cli', length=15)
        key_uri = "https://{}.vault.azure.net/keys/{}".format(kv_name, key_name)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'kv_name': kv_name,
            'key_name': key_name,
            'key_uri': key_uri,
            'location': "eastus2"
        })

        self.cmd('az keyvault create --resource-group {rg} -n {kv_name} --enable-soft-delete true --enable-purge-protection true')
        self.cmd('az keyvault set-policy -n {kv_name} -g {rg} --spn a232010e-820c-4083-83bb-3ace5fc29d0b --key-permissions get unwrapKey wrapKey')
        self.cmd('az keyvault key create -n {key_name} --kty RSA --size 3072 --vault-name {kv_name}')

        cmk_output = self.cmd('az cosmosdb create -n {acc} -g {rg} --locations regionName={location} failoverPriority=0 --key-uri {key_uri}').get_output_in_json()

        assert cmk_output["keyVaultKeyUri"] == key_uri
