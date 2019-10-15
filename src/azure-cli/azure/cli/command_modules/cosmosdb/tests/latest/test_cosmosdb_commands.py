# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from azure.cli.testsdk import JMESPathCheck, ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError


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
        ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-automatic-failover false --default-consistency-level Session')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', False),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'Session')
        ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --tags testKey=testValue')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', False),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'Session')
        ]).get_output_in_json()
        assert account['tags']['testKey'] == "testValue"

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_update_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB --ip-range-filter 10.10.10.10')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            JMESPathCheck('kind', 'MongoDB'),
            self.check('ipRangeFilter', "10.10.10.10"),
        ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --capabilities EnableAggregationPipeline')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            JMESPathCheck('kind', 'MongoDB'),
            self.check('ipRangeFilter', "10.10.10.10"),
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
        self.cmd('az cosmosdb delete -n {acc} -g {rg}')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', expect_failure=True)

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

        existing_rule = self.cmd('az cosmosdb network-rule add -n {acc} -g {rg} --virtual-network {vnet} --subnet {sub} --ignore-missing-vnet-service-endpoint').get_output_in_json()
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

        self.cmd('az cosmosdb database delete -g {rg} -n {acc} -d {db_name}')
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

        self.cmd('az cosmosdb collection delete -g {rg} -n {acc} -d {db_name} -c {col}')
        assert not self.cmd('az cosmosdb collection exists -g {rg} -n {acc} -d {db_name} -c {col}').get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_database')
    def test_cosmosdb_sql_database(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        database_create = self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_create["sqlDatabaseId"] == db_name

        database_show = self.cmd('az cosmosdb sql database show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_show["sqlDatabaseId"] == db_name

        database_list = self.cmd('az cosmosdb sql database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 1

        self.cmd('az cosmosdb sql database delete -g {rg} -a {acc} -n {db_name}')
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

        container_create = self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --ttl {ttl} --unique-key-policy {unique_key} --conflict-resolution-policy {conflict_resolution} --idx {indexing}').get_output_in_json()
        assert container_create["sqlContainerId"] == ctn_name
        assert container_create["partitionKey"]["paths"][0] == partition_key
        assert container_create["defaultTtl"] == default_ttl
        assert len(container_create["uniqueKeyPolicy"]["uniqueKeys"]) == 2
        assert container_create["conflictResolutionPolicy"]["mode"] == "lastWriterWins"
        assert container_create["indexingPolicy"]["excludedPaths"][0]["path"] == "/headquarters/employees/?"

        container_update = self.cmd('az cosmosdb sql container update -g {rg} -a {acc} -d {db_name} -n {ctn_name} --ttl {nttl}').get_output_in_json()
        assert container_update["defaultTtl"] == new_default_ttl

        container_show = self.cmd('az cosmosdb sql container show -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()
        assert container_show["sqlContainerId"] == ctn_name

        container_list = self.cmd('az cosmosdb sql container list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(container_list) == 1

        self.cmd('az cosmosdb sql container delete -g {rg} -a {acc} -d {db_name} -n {ctn_name}')
        container_list = self.cmd('az cosmosdb sql container list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(container_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongodb_database')
    def test_cosmosdb_mongodb_database(self, resource_group):
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=15),
            'db_name': db_name,
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB')

        database_create = self.cmd('az cosmosdb mongodb database create -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_create["mongoDbDatabaseId"] == db_name

        database_show = self.cmd('az cosmosdb mongodb database show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_show["mongoDbDatabaseId"] == db_name

        database_list = self.cmd('az cosmosdb mongodb database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 1

        self.cmd('az cosmosdb mongodb database delete -g {rg} -a {acc} -n {db_name}')
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
            'indexes': '"[{\\"key\\": {\\"keys\\": [\\"_ts\\"]},\\"options\\": {\\"expireAfterSeconds\\": 1000}}]"'
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --kind MongoDB')
        self.cmd('az cosmosdb mongodb database create -g {rg} -a {acc} -n {db_name}')

        collection_create = self.cmd(
            'az cosmosdb mongodb collection create -g {rg} -a {acc} -d {db_name} -n {col_name} --shard {shard_key}').get_output_in_json()
        assert collection_create["mongoDbCollectionId"] == col_name

        indexes_size = len(collection_create["indexes"])
        collection_update = self.cmd(
            'az cosmosdb mongodb collection update -g {rg} -a {acc} -d {db_name} -n {col_name} --idx {indexes}').get_output_in_json()
        assert len(collection_update["indexes"]) == indexes_size + 1

        collection_show = self.cmd(
            'az cosmosdb mongodb collection show -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()
        assert collection_show["mongoDbCollectionId"] == col_name

        collection_list = self.cmd(
            'az cosmosdb mongodb collection list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(collection_list) == 1

        self.cmd('az cosmosdb mongodb collection delete -g {rg} -a {acc} -d {db_name} -n {col_name}')
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

        keyspace_create = self.cmd('az cosmosdb cassandra keyspace create -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert keyspace_create["cassandraKeyspaceId"] == ks_name

        keyspace_show = self.cmd('az cosmosdb cassandra keyspace show -g {rg} -a {acc} -n {ks_name}').get_output_in_json()
        assert keyspace_show["cassandraKeyspaceId"] == ks_name

        keyspace_list = self.cmd('az cosmosdb cassandra keyspace list -g {rg} -a {acc}').get_output_in_json()
        assert len(keyspace_list) == 1

        self.cmd('az cosmosdb cassandra keyspace delete -g {rg} -a {acc} -n {ks_name}')
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
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --capabilities EnableCassandra')
        self.cmd('az cosmosdb cassandra keyspace create -g {rg} -a {acc} -n {ks_name}').get_output_in_json()

        table_create = self.cmd('az cosmosdb cassandra table create -g {rg} -a {acc} -k {ks_name} -n {table_name} --schema {schema}').get_output_in_json()
        assert table_create["cassandraTableId"] == table_name
        assert len(table_create["schema"]["columns"]) == 1

        table_update = self.cmd('az cosmosdb cassandra table update -g {rg} -a {acc} -k {ks_name} -n {table_name} --schema {new_schema}').get_output_in_json()
        assert len(table_update["schema"]["columns"]) == 2

        table_show = self.cmd('az cosmosdb cassandra table show -g {rg} -a {acc} -k {ks_name} -n {table_name}').get_output_in_json()
        assert table_show["cassandraTableId"] == table_name

        table_list = self.cmd('az cosmosdb cassandra table list -g {rg} -a {acc} -k {ks_name}').get_output_in_json()
        assert len(table_list) == 1

        self.cmd('az cosmosdb cassandra table delete -g {rg} -a {acc} -k {ks_name} -n {table_name}')
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

        database_create = self.cmd('az cosmosdb gremlin database create -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_create["gremlinDatabaseId"] == db_name

        database_show = self.cmd('az cosmosdb gremlin database show -g {rg} -a {acc} -n {db_name}').get_output_in_json()
        assert database_show["gremlinDatabaseId"] == db_name

        database_list = self.cmd('az cosmosdb gremlin database list -g {rg} -a {acc}').get_output_in_json()
        assert len(database_list) == 1

        self.cmd('az cosmosdb gremlin database delete -g {rg} -a {acc} -n {db_name}')
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

        graph_create = self.cmd('az cosmosdb gremlin graph create -g {rg} -a {acc} -d {db_name} -n {gp_name} -p {part} --ttl {ttl} --conflict-resolution-policy {conflict_resolution} --idx {indexing}').get_output_in_json()
        assert graph_create["gremlinGraphId"] == gp_name
        assert graph_create["partitionKey"]["paths"][0] == partition_key
        assert graph_create["defaultTtl"] == default_ttl
        assert graph_create["conflictResolutionPolicy"]["mode"] == "lastWriterWins"
        assert graph_create["indexingPolicy"]["excludedPaths"][0]["path"] == "/headquarters/employees/?"

        graph_update = self.cmd('az cosmosdb gremlin graph update -g {rg} -a {acc} -d {db_name} -n {gp_name} --ttl {nttl}').get_output_in_json()
        assert graph_update["defaultTtl"] == new_default_ttl

        graph_show = self.cmd('az cosmosdb gremlin graph show -g {rg} -a {acc} -d {db_name} -n {gp_name}').get_output_in_json()
        assert graph_show["gremlinGraphId"] == gp_name

        graph_list = self.cmd('az cosmosdb gremlin graph list -g {rg} -a {acc} -d {db_name}').get_output_in_json()
        assert len(graph_list) == 1

        self.cmd('az cosmosdb gremlin graph delete -g {rg} -a {acc} -d {db_name} -n {gp_name}')
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

        table_create = self.cmd('az cosmosdb table create -g {rg} -a {acc} -n {table_name}').get_output_in_json()
        assert table_create["tableId"] == table_name

        table_show = self.cmd('az cosmosdb table show -g {rg} -a {acc} -n {table_name}').get_output_in_json()
        assert table_show["tableId"] == table_name

        table_list = self.cmd('az cosmosdb table list -g {rg} -a {acc}').get_output_in_json()
        assert len(table_list) == 1

        self.cmd('az cosmosdb table delete -g {rg} -a {acc} -n {table_name}')
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
        assert db_throughput_show["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb sql database throughput update -g {rg} -a {acc} -n {db_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["throughput"] == tp2

        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {ctn_name} -p {part} --throughput {tp1}')
        ctn_throughput_show = self.cmd('az cosmosdb sql container throughput show -g {rg} -a {acc} -d {db_name} -n {ctn_name}').get_output_in_json()
        assert ctn_throughput_show["throughput"] == tp1

        ctn_througput_update = self.cmd('az cosmosdb sql container throughput update -g {rg} -a {acc} -d {db_name} -n {ctn_name} --throughput {tp2}').get_output_in_json()
        assert ctn_througput_update["throughput"] == tp2

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
        assert db_throughput_show["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb mongodb database throughput update -g {rg} -a {acc} -n {db_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["throughput"] == tp2

        self.cmd('az cosmosdb mongodb collection create -g {rg} -a {acc} -d {db_name} -n {col_name} --shard {shard_key} --throughput {tp1}')
        col_throughput_show = self.cmd('az cosmosdb mongodb collection throughput show -g {rg} -a {acc} -d {db_name} -n {col_name}').get_output_in_json()
        assert col_throughput_show["throughput"] == tp1

        col_througput_update = self.cmd('az cosmosdb mongodb collection throughput update -g {rg} -a {acc} -d {db_name} -n {col_name} --throughput {tp2}').get_output_in_json()
        assert col_througput_update["throughput"] == tp2

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
        assert db_throughput_show["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb cassandra keyspace throughput update -g {rg} -a {acc} -n {ks_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["throughput"] == tp2

        self.cmd('az cosmosdb cassandra table create -g {rg} -a {acc} -k {ks_name} -n {tb_name} --throughput {tp1} --schema {schema}')
        col_throughput_show = self.cmd('az cosmosdb cassandra table throughput show -g {rg} -a {acc} -k {ks_name} -n {tb_name}').get_output_in_json()
        assert col_throughput_show["throughput"] == tp1

        col_througput_update = self.cmd('az cosmosdb cassandra table throughput update -g {rg} -a {acc} -k {ks_name} -n {tb_name} --throughput {tp2}').get_output_in_json()
        assert col_througput_update["throughput"] == tp2

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
        assert db_throughput_show["throughput"] == tp1

        db_througput_update = self.cmd(
            'az cosmosdb gremlin database throughput update -g {rg} -a {acc} -n {db_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["throughput"] == tp2

        self.cmd('az cosmosdb gremlin graph create -g {rg} -a {acc} -d {db_name} -n {gp_name} -p {part} --throughput {tp1}')
        col_throughput_show = self.cmd(
            'az cosmosdb gremlin graph throughput show -g {rg} -a {acc} -d {db_name} -n {gp_name}').get_output_in_json()
        assert col_throughput_show["throughput"] == tp1

        col_througput_update = self.cmd(
            'az cosmosdb gremlin graph throughput update -g {rg} -a {acc} -d {db_name} -n {gp_name} --throughput {tp2}').get_output_in_json()
        assert col_througput_update["throughput"] == tp2

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
        assert db_throughput_show["throughput"] == tp1

        db_througput_update = self.cmd('az cosmosdb table throughput update -g {rg} -a {acc} -n {tb_name} --throughput {tp2}').get_output_in_json()
        assert db_througput_update["throughput"] == tp2
