# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import JMESPathCheck, ScenarioTest, ResourceGroupPreparer


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

        connection_strings = self.cmd('az cosmosdb list-connection-strings -n {acc} -g {rg}').get_output_in_json()
        assert len(connection_strings['connectionStrings']) == 1

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

        original_keys = self.cmd('az cosmosdb list-keys -n {acc} -g {rg}').get_output_in_json()
        assert 'primaryMasterKey' in original_keys
        assert 'primaryReadonlyMasterKey' in original_keys
        assert 'secondaryMasterKey' in original_keys
        assert 'secondaryReadonlyMasterKey' in original_keys

        self.cmd('az cosmosdb regenerate-key -n {acc} -g {rg} --key-kind primary')
        self.cmd('az cosmosdb regenerate-key -n {acc} -g {rg} --key-kind primaryReadonly')
        self.cmd('az cosmosdb regenerate-key -n {acc} -g {rg} --key-kind secondary')
        self.cmd('az cosmosdb regenerate-key -n {acc} -g {rg} --key-kind secondaryReadonly')

        modified_keys = self.cmd('az cosmosdb list-keys -n {acc} -g {rg}').get_output_in_json()
        assert original_keys['primaryMasterKey'] != modified_keys['primaryMasterKey']
        assert original_keys['primaryReadonlyMasterKey'] != modified_keys['primaryReadonlyMasterKey']
        assert original_keys['secondaryMasterKey'] != modified_keys['secondaryMasterKey']
        assert original_keys['secondaryReadonlyMasterKey'] != modified_keys['secondaryReadonlyMasterKey']

        original_keys = self.cmd('az cosmosdb list-read-only-keys -n {acc} -g {rg}').get_output_in_json()
        assert 'primaryReadonlyMasterKey' in original_keys
        assert 'secondaryReadonlyMasterKey' in original_keys
        assert 'primaryMasterKey' not in original_keys
        assert 'secondaryMasterKey' not in original_keys

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

        account1 = self.cmd('az cosmosdb create -n {acc} -g {rg} --locations {write_location}=0 {read_location}=1').get_output_in_json()
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
        print(account2['writeLocations'][0]['failoverPriority'])
        print(account2['writeLocations'][0]['locationName'])
        assert account2['writeLocations'][0]['failoverPriority'] == 0
        assert account2['writeLocations'][0]['locationName'] == "West US"
        assert account2['readLocations'][0]['locationName'] == "East US" or account2['readLocations'][1]['locationName'] == "East US"
        assert account2['readLocations'][0]['failoverPriority'] == 1 or account2['readLocations'][1]['failoverPriority'] == 1

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
