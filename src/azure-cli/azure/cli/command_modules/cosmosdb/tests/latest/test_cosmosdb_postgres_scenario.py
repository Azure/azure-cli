# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
from azure.cli.testsdk import JMESPathCheck, ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

class CosmosDBPostgresScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='cli_test')
    def test_cosmosdb_postgres_create_cluster_with_configurations(self, resource_group):
        self.kwargs.update({
            'cluster_name': self.create_random_name(prefix='cli', length=10),
            'loc': 'eastus2',
            'storage': 131072,
            'pass': 'aBcD1234!@#$',
            'config_name': 'array_nulls'
        })

        self.cmd('az cosmosdb postgres cluster create '
                '--name {cluster_name} -g {rg} -l {loc} --coordinator-v-cores 4 '
                '--coordinator-server-edition "GeneralPurpose" --node-count "2" '
                '--node-v-cores 2 --coordinator-storage-quota-in-mb {storage} '
                '--administrator-login-password {pass} '
                '--node-server-edition "MemoryOptimized" '
                '--node-storage-quota-in-mb {storage}', checks=[
                    self.check('name', "{cluster_name}"),
                    self.check('provisioningState', 'Succeeded')
                ])
        
        self.cmd('az cosmosdb postgres configuration list --cluster-name {cluster_name} -g {rg}', checks=[
                self.check('[0].type', 'Microsoft.DBforPostgreSQL/serverGroupsv2/configurations')
            ])
        
        self.cmd('az cosmosdb postgres configuration show --cluster-name {cluster_name} -g {rg} -n {config_name}', checks=[
                self.check('type', 'Microsoft.DBforPostgreSQL/serverGroupsv2/configurations'),
                self.check('name', '{config_name}')
            ])
        
        self.cmd('az cosmosdb postgres configuration node show --cluster-name {cluster_name} -g {rg} -n {config_name}', checks=[
                self.check('type', 'Microsoft.DBforPostgreSQL/serverGroupsv2/nodeConfigurations'),
                self.check('name', '{config_name}')
            ])
        
        self.cmd('az cosmosdb postgres configuration coordinator show --cluster-name {cluster_name} -g {rg} -n {config_name}', checks=[
                self.check('type', 'Microsoft.DBforPostgreSQL/serverGroupsv2/coordinatorConfigurations'),
                self.check('name', '{config_name}')
            ])
        
        # update configurations
        self.cmd('az cosmosdb postgres configuration node update --cluster-name {cluster_name} -g {rg} -n {config_name} --value off', checks=[
                self.check('type','Microsoft.DBforPostgreSQL/serverGroupsv2/nodeConfigurations'),
                self.check('provisioningState', 'Succeeded'),
                self.check('name', '{config_name}'),
                self.check('value', 'off')
            ])
        
        self.cmd('az cosmosdb postgres configuration coordinator update --cluster-name {cluster_name} -g {rg} -n {config_name} --value off', checks=[
                self.check('type', 'Microsoft.DBforPostgreSQL/serverGroupsv2/coordinatorConfigurations'),
                self.check('provisioningState', 'Succeeded'),
                self.check('name', '{config_name}'),
                self.check('value', 'off')
            ])
        
        self.cmd('az cosmosdb postgres configuration server list --cluster-name {cluster_name} -g {rg} --server-name {cluster_name}-c', checks=[
                self.check('[0].type', 'Microsoft.DBforPostgreSQL/serverGroupsv2/servers/configurations'),
            ])
        
    @ResourceGroupPreparer(random_name_length=17, name_prefix='cli_test')
    def test_cosmosdb_postgres_create_cluster_with_roles(self, resource_group):
        self.kwargs.update({
            'cluster_name': self.create_random_name(prefix='cli', length=10),
            'loc': 'eastus2',
            'storage': 131072,
            'pass': 'aBcD1234!@#$',
            'new_pass': 'aBcD1234!@#$',
            'role_name': 'azrole'
        })

        self.cmd('az cosmosdb postgres cluster create '
                '--name {cluster_name} -g {rg} -l {loc} --coordinator-v-cores 4 '
                '--coordinator-server-edition "GeneralPurpose" --node-count "2" '
                '--node-v-cores 2 --coordinator-storage-quota-in-mb {storage} '
                '--administrator-login-password {pass} '
                '--node-server-edition "MemoryOptimized" '
                '--node-storage-quota-in-mb {storage}', checks=[
                    self.check('name', "{cluster_name}"),
                    self.check('provisioningState', 'Succeeded')
                ])
        
        self.cmd('az cosmosdb postgres role create --cluster-name {cluster_name} -n {role_name} -g {rg} --password {pass}', 
                 checks=[
                     self.check('name', "{role_name}"),
                     self.check('provisioningState', 'Succeeded')
                     ])
        
        self.cmd('az cosmosdb postgres role update --cluster-name {cluster_name} -n {role_name} -g {rg} --password {new_pass}',
            checks=[
                self.check('name', "{role_name}"),
                self.check('provisioningState', 'Succeeded')
                ])

        self.cmd('az cosmosdb postgres role list --cluster-name {cluster_name} -g {rg}',
         checks=[
            self.greater_than("length([])", 0)
        ])

        self.cmd('az cosmosdb postgres role delete --cluster-name {cluster_name} -n {role_name} -g {rg} --yes')

        self.cmd('az cosmosdb postgres role list --cluster-name {cluster_name} -g {rg}',
         checks=[
            self.check("length([])", 0)
        ])

    @ResourceGroupPreparer(random_name_length=17, name_prefix='cli_test')
    def test_cosmosdb_postgres_create_cluster_with_firewall_rules(self, resource_group):
        self.kwargs.update({
            'cluster_name': self.create_random_name(prefix='cli', length=10),
            'loc': 'eastus2',
            'storage': 131072,
            'pass': 'aBcD1234!@#$',
            'fw_name': 'fw_rule'
        })

        self.cmd('az cosmosdb postgres cluster create '
                '--name {cluster_name} -g {rg} -l {loc} --coordinator-v-cores 4 '
                '--coordinator-server-edition "GeneralPurpose" --node-count "2" '
                '--node-v-cores 2 --coordinator-storage-quota-in-mb {storage} '
                '--administrator-login-password {pass} '
                '--node-server-edition "MemoryOptimized" '
                '--node-storage-quota-in-mb {storage}', checks=[
                    self.check('name', "{cluster_name}"),
                    self.check('provisioningState', 'Succeeded')
                ])
        
        self.cmd('az cosmosdb postgres firewall-rule create --cluster-name {cluster_name} -n {fw_name} -g {rg} '
                 '--start-ip-address "0.0.0.0" --end-ip-address "255.255.255.255"', checks=[
                self.check('provisioningState', 'Succeeded')])
        
        self.cmd('az cosmosdb postgres firewall-rule update --cluster-name {cluster_name} -n {fw_name} -g {rg} --end-ip-address "255.255.255.1"',
            checks=[
                self.check('name', "{fw_name}"),
                self.check('provisioningState', 'Succeeded'),
                self.check('endIpAddress', '255.255.255.1')
                ])

        self.cmd('az cosmosdb postgres firewall-rule list --cluster-name {cluster_name} -g {rg}',
         checks=[
            self.greater_than("length([])", 0)
        ])

        self.cmd('az cosmosdb postgres firewall-rule delete --cluster-name {cluster_name} -n {fw_name} -g {rg} --yes')

        self.cmd('az cosmosdb postgres firewall-rule list --cluster-name {cluster_name} -g {rg}',
         checks=[
            self.check("length([])", 0)
        ])
    
    @ResourceGroupPreparer(random_name_length=17, name_prefix='cli_test')
    def test_cosmosdb_postgres_create_cluster(self, resource_group):
        self.kwargs.update({
            'cluster_name': self.create_random_name(prefix='cli', length=10),
            'loc': 'eastus2',
            'storage': 131072,
            'pass': 'aBcD1234!@#$',
            'new_pass': 'aBcD1234!@#$'
        })

        self.cmd('az cosmosdb postgres cluster create '
                '--name {cluster_name} -g {rg} -l {loc} --coordinator-v-cores 4 '
                '--coordinator-server-edition "GeneralPurpose" --node-count "2" '
                '--node-v-cores 2 --coordinator-storage-quota-in-mb {storage} '
                '--administrator-login-password {pass} '
                '--node-server-edition "MemoryOptimized" '
                '--node-storage-quota-in-mb {storage}'
                )
        
        self.cmd('az cosmosdb postgres cluster wait --created -n {cluster_name} -g {rg}')

        self.cmd('az cosmosdb postgres cluster show -n {cluster_name} -g {rg}', 
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('name', '{cluster_name}'),
                     self.check('nodeVCores', '2')
                     ])
        
        self.cmd('az cosmosdb postgres cluster update -n {cluster_name} -g {rg} --node-v-cores 4')

        self.cmd('az cosmosdb postgres cluster wait --updated -n {cluster_name} -g {rg}')

        self.cmd('az cosmosdb postgres cluster show -n {cluster_name} -g {rg}', 
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('name', '{cluster_name}'),
                     self.check('nodeVCores', '4')
                     ])

        self.cmd('az cosmosdb postgres cluster list -g {rg}',
         checks=[
            self.check("length([])", 1)
        ])

        self.cmd('az cosmosdb postgres cluster delete -n {cluster_name} -g {rg} --yes')
        self.cmd('az cosmosdb postgres cluster wait --deleted -n {cluster_name} -g {rg}') 

        self.cmd('az cosmosdb postgres cluster list -g {rg}',
         checks=[
            self.check("length([])", 0)
        ])

        