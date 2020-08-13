# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class SynapseScenarioTests(ScenarioTest):
    location = "northeurope"

    @ResourceGroupPreparer(name_prefix='synapse-cli', random_name_length=16)
    def test_workspaces(self, resource_group):
        # create a workspace
        self._create_workspace()

        # check workspace name
        self.cmd('az synapse workspace check-name --name {workspace}', checks=[
            self.check('available', False)
        ])

        # get workspace with workspace name
        workspace = self.cmd('az synapse workspace show --name {workspace} --resource-group {rg}', checks=[
            self.check('name', self.kwargs['workspace']),
            self.check('type', 'Microsoft.Synapse/workspaces'),
            self.check('provisioningState', 'Succeeded')
        ]).get_output_in_json()

        self.kwargs["workspace-id"] = workspace['id']

        # list all workspaces under a specific resource group
        self.cmd('az synapse workspace list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.Synapse/workspaces')
        ])

        # update workspace
        self.cmd('az synapse workspace update --ids {workspace-id} --tags key1=value1', checks=[
            self.check('tags.key1', 'value1'),
            self.check('name', self.kwargs['workspace']),
            self.check('id', self.kwargs['workspace-id']),
            self.check('type', 'Microsoft.Synapse/workspaces'),
            self.check('provisioningState', 'Succeeded')
        ])

        # delete workspace with workspace name
        self.cmd('az synapse workspace delete --name {workspace} --resource-group {rg} --yes')
        import time
        time.sleep(120)
        self.cmd('az synapse workspace show --name {workspace} --resource-group {rg}', expect_failure=True)

    def test_spark_pool(self):
        self.kwargs.update({
            'location': 'eastus',
            'workspace': 'testsynapseworkspace',
            'rg': 'rg',
            'spark-pool': self.create_random_name(prefix='testpool', length=15),
            'spark-version': '2.4'
        })
        # create spark pool
        spark_pool = self.cmd('az synapse spark pool create --name {spark-pool} --spark-version {spark-version}'
                              ' --workspace {workspace} --resource-group {rg} --node-count 3 --node-size Medium',
                              checks=[
                                  self.check('name', self.kwargs['spark-pool']),
                                  self.check('type', 'Microsoft.Synapse/workspaces/bigDataPools'),
                                  self.check('provisioningState', 'Succeeded')
                              ]).get_output_in_json()

        self.kwargs['pool-id'] = spark_pool['id']

        # get spark pool with spark pool name
        self.cmd('az synapse spark pool show --name {spark-pool} --workspace {workspace} --resource-group {rg}',
                 checks=[
                     self.check('name', self.kwargs['spark-pool']),
                     self.check('type', 'Microsoft.Synapse/workspaces/bigDataPools'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        # list all spark pools under the workspace
        self.cmd('az synapse spark pool list --workspace {workspace} --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.Synapse/workspaces/bigDataPools')
        ])

        # update spark pool
        self.cmd('az synapse spark pool update --ids {pool-id} --tags key1=value1', checks=[
            self.check('tags.key1', 'value1'),
            self.check('name', self.kwargs['spark-pool']),
            self.check('type', 'Microsoft.Synapse/workspaces/bigDataPools'),
            self.check('provisioningState', 'Succeeded')
        ])

        # delete spark pool with spark pool name
        self.cmd(
            'az synapse spark pool delete --name {spark-pool} --workspace {workspace} --resource-group {rg} --yes')
        self.cmd('az synapse spark pool show --name {spark-pool} --workspace {workspace} --resource-group {rg}',
                 expect_failure=True)

    def test_sql_pool(self):
        self.kwargs.update({
            'location': 'eastus',
            'workspace': 'testsynapseworkspace',
            'rg': 'rg',
            'sql-pool': self.create_random_name(prefix='testsqlpool', length=15),
            'performance-level': 'DW1000c'
        })
        # create sql pool
        sql_pool = self.cmd(
            'az synapse sql pool create --name {sql-pool} --performance-level {performance-level} '
            '--workspace {workspace} --resource-group {rg}', checks=[
                self.check('name', self.kwargs['sql-pool']),
                self.check('type', 'Microsoft.Synapse/workspaces/sqlPools'),
                self.check('provisioningState', 'Succeeded'),
                self.check('status', 'Online')
            ]).get_output_in_json()

        self.kwargs['pool-id'] = sql_pool['id']

        # get sql pool with sql pool name
        self.cmd('az synapse sql pool show --name {sql-pool} --workspace {workspace} --resource-group {rg}',
                 checks=[
                     self.check('name', self.kwargs['sql-pool']),
                     self.check('type', 'Microsoft.Synapse/workspaces/sqlPools'),
                     self.check('provisioningState', 'Succeeded'),
                     self.check('status', 'Online')
                 ])

        # list all sql pools under the workspace
        self.cmd('az synapse sql pool list --workspace {workspace} --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.Synapse/workspaces/sqlPools')
        ])

        # update sql pool
        self.cmd('az synapse sql pool update --ids {pool-id} --tags key1=value1')

        # get sql pool with sql pool id
        self.cmd('az synapse sql pool show --ids {pool-id}',
                 checks=[
                     self.check('name', self.kwargs['sql-pool']),
                     self.check('type', 'Microsoft.Synapse/workspaces/sqlPools'),
                     self.check('tags.key1', 'value1'),
                     self.check('provisioningState', 'Succeeded'),
                     self.check('status', 'Online')
                 ])

        # pause sql pool
        self.cmd('az synapse sql pool pause --name {sql-pool} --workspace {workspace} --resource-group {rg}', checks=[])
        self.cmd('az synapse sql pool show --name {sql-pool} --workspace {workspace} --resource-group {rg}',
                 checks=[
                     self.check('name', self.kwargs['sql-pool']),
                     self.check('type', 'Microsoft.Synapse/workspaces/sqlPools'),
                     self.check('status', 'Paused')
                 ])

        # resume sql pool
        self.cmd('az synapse sql pool resume --name {sql-pool} --workspace {workspace} --resource-group {rg}', checks=[])
        self.cmd('az synapse sql pool show --name {sql-pool} --workspace {workspace} --resource-group {rg}',
                 checks=[
                     self.check('name', self.kwargs['sql-pool']),
                     self.check('type', 'Microsoft.Synapse/workspaces/sqlPools'),
                     self.check('status', 'Online')
                 ])

        # delete sql pool with sql pool name
        self.cmd(
            'az synapse sql pool delete --name {sql-pool} --workspace {workspace} --resource-group {rg} --yes')

        self.cmd('az synapse sql pool show --name {sql-pool} --workspace {workspace} --resource-group {rg}',
                 expect_failure=True)

    @ResourceGroupPreparer(name_prefix='synapse-cli', random_name_length=16)
    def test_ip_firewall_rules(self, resource_group):
        self.kwargs.update({
            'workspace': 'testsynapseworkspace',
            'rg': 'rg',
            'ruleName': self.create_random_name(prefix='rule', length=8),
            'startIpAddress': "0.0.0.0",
            'endIpAddress': "255.255.255.255"
        })

        # create a firewall rule
        self.cmd(
            'az synapse workspace firewall-rule create --name {ruleName} --workspace-name {workspace} '
            '--resource-group {rg} --start-ip-address {startIpAddress} --end-ip-address {endIpAddress}',
            checks=[
                self.check('name', self.kwargs['ruleName']),
                self.check('type', 'Microsoft.Synapse/workspaces/firewallRules'),
                self.check('provisioningState', 'Succeeded')
            ])

        # get a firewall rule
        self.cmd(
            'az synapse workspace firewall-rule show --name {ruleName} --workspace-name {workspace} '
            '--resource-group {rg}',
            checks=[
                self.check('name', self.kwargs['ruleName']),
                self.check('type', 'Microsoft.Synapse/workspaces/firewallRules'),
                self.check('provisioningState', 'Succeeded')
            ])

        # list all firewall rules under a specific workspace
        self.cmd('az synapse workspace firewall-rule list --workspace-name {workspace} --resource-group {rg}',
                 checks=[
                     self.check('[0].type', 'Microsoft.Synapse/workspaces/firewallRules')
                 ])

        # delete a firewall rule
        self.cmd(
            'az synapse workspace firewall-rule delete --name {ruleName} --workspace-name {workspace} '
            '--resource-group {rg} --yes')
        import time
        time.sleep(20)
        self.cmd('az synapse workspace firewall-rule show --name {ruleName} --workspace-name {workspace} '
                 '--resource-group {rg}', expect_failure=True)

    def _create_workspace(self):
        self.kwargs.update({
            'location': self.location,
            'workspace': self.create_random_name(prefix='clitest', length=16),
            'file-system': 'testfilesystem',
            'storage-account': 'adlsgen2account',
            'login-user': 'cliuser1',
            'login-password': 'password'
        })

        # Wait some time to improve robustness
        if self.is_live or self.in_recording:
            import time
            time.sleep(60)

        # create synapse workspace
        self.cmd(
            'az synapse workspace create --name {workspace} --resource-group {rg} --storage-account {storage-account} '
            '--file-system {file-system} --sql-admin-login-user {login-user} '
            '--sql-admin-login-password {login-password}'
            ' --location {location}', checks=[
                self.check('name', self.kwargs['workspace']),
                self.check('type', 'Microsoft.Synapse/workspaces'),
                self.check('provisioningState', 'Succeeded')
            ])
