# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, record_only

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

    @record_only()
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

    @record_only()
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

    @record_only()
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

    @record_only()
    @ResourceGroupPreparer(name_prefix='synapse-cli', random_name_length=16)
    def test_spark_job(self, resource_group):
        self.kwargs.update({
            'spark-pool': 'testsparkpool',
            'workspace': 'testsynapseworkspace',
            'job': 'WordCount_Java',
            'main-definition-file': 'abfss://testfilesystem@adlsgen2account.dfs.core.windows.net/samples/java/wordcount/wordcount.jar',
            'main-class-name': 'WordCount',
            'arguments': [
                'abfss://testfilesystem@adlsgen2account.dfs.core.windows.net/samples/java/wordcount/shakespeare.txt',
                'abfss://testfilesystem@adlsgen2account.dfs.core.windows.net/samples/java/wordcount/result/'],
            'executors': 2,
            'executor-size': 'Medium'
        })

        # create a spark batch job
        batch_job = self.cmd('az synapse spark job submit --name {job} --workspace-name {workspace} '
                             '--spark-pool-name {spark-pool} --main-definition-file {main-definition-file} '
                             '--main-class-name {main-class-name} --arguments {arguments} '
                             '--executors {executors} --executor-size {executor-size}',
                             checks=[self.check('name', self.kwargs['job']),
                                     self.check('jobType', 'SparkBatch'),
                                     self.check('state', 'not_started')
                                     ]).get_output_in_json()

        self.kwargs['batch-id'] = batch_job['id']

        # get a spark batch job with batch id
        self.cmd('az synapse spark job show --livy-id {batch-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}', checks=[self.check('id', self.kwargs['batch-id'])])

        # list all spark batch jobs under a specific spark pool
        self.cmd('az synapse spark job list --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}',
                 checks=[
                     self.check('sessions[0].jobType', 'SparkBatch')
                 ])

        # cancel a spark batch job with batch id
        self.cmd('az synapse spark job cancel --livy-id {batch-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool} --yes')
        import time
        time.sleep(60)
        self.cmd('az synapse spark job show --livy-id {batch-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}',
                 checks=[
                     self.check('result', 'Cancelled')
                 ])

    @record_only()
    @ResourceGroupPreparer(name_prefix='synapse-cli', random_name_length=16)
    def test_spark_session_and_statements(self, resource_group):
        self.kwargs.update({
            'spark-pool': 'testsparkpool',
            'workspace': 'testsynapseworkspace',
            'job': self.create_random_name(prefix='clisession', length=14),
            'executor-size': 'Small',
            'executors': 2,
            'code': "\"import time\ntime.sleep(10)\nprint('hello from cli')\"",
            'language': 'pyspark'
        })

        # create a spark session
        create_result = self.cmd('az synapse spark session create --name {job} --workspace-name {workspace} '
                                 '--spark-pool-name {spark-pool} --executor-size {executor-size} '
                                 '--executors {executors}',
                                 checks=[
                                     self.check('jobType', 'SparkSession'),
                                     self.check('name', self.kwargs['job']),
                                     self.check('state', 'not_started')
                                 ]).get_output_in_json()

        self.kwargs['session-id'] = create_result['id']

        # wait for creating spark session
        import time
        time.sleep(360)

        # get a spark session
        self.cmd('az synapse spark session show --livy-id {session-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}',
                 checks=[
                     self.check('id', self.kwargs['session-id']),
                     self.check('state', 'idle')
                 ])

        # list all spark session jobs under a specific spark pook
        self.cmd('az synapse spark session list --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}',
                 checks=[
                     self.check('sessions[0].jobType', 'SparkSession')
                 ])

        # reset spark session's timeout time
        self.cmd('az synapse spark session reset-timeout --livy-id {session-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}')

        # create a spark session statement job
        statement = self.cmd('az synapse spark statement invoke --session-id {session-id} '
                             '--workspace-name {workspace} --spark-pool-name {spark-pool} '
                             '--code {code} --language {language}',
                             checks=[
                                 self.check('state', 'waiting')
                             ]).get_output_in_json()
        self.kwargs['statement-id'] = statement['id']
        time.sleep(10)

        # get a spark session statement
        self.cmd('az synapse spark statement show --livy-id {statement-id} --session-id {session-id} '
                 '--workspace-name {workspace} --spark-pool-name {spark-pool}',
                 checks=[
                     self.check('state', 'running')
                 ])

        # list all spark session statements under a specific spark session
        self.cmd('az synapse spark statement list --session-id {session-id} '
                 '--workspace-name {workspace} --spark-pool-name {spark-pool}',
                 checks=[
                     self.check('statements[0].state', 'running')
                 ])

        # cancel a spark session statement
        self.cmd('az synapse spark statement cancel --livy-id {statement-id} --session-id {session-id} '
                 '--workspace-name {workspace} --spark-pool-name {spark-pool}  --yes',
                 checks=[
                     self.check('msg', 'canceled')
                 ])

        # delete/cancel a spark session
        self.cmd('az synapse spark session cancel --livy-id {session-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool} --yes')
        import time
        time.sleep(120)
        self.cmd('az synapse spark session show --livy-id {session-id} --workspace-name {workspace} '
                 '--spark-pool-name {spark-pool}',
                 checks=[
                     self.check('state', 'killed')
                 ])

    @record_only()
    def test_access_control(self):
        self.kwargs.update({
            'workspace': 'testsynapseworkspace',
            'role': 'Sql Admin',
            'userPrincipal': 'username@microsoft.com',
            'servicePrincipal': 'http://username-sp'})

        self.cmd(
            'az synapse role definition list --workspace-name {workspace} ',
            checks=[
                self.check('length([])', 3)
            ])

        # get role definition
        role_definition_get = self.cmd(
            'az synapse role definition show --workspace-name {workspace} --role "{role}" ',
            checks=[
                self.check('name', self.kwargs['role'])
            ]).get_output_in_json()
        self.kwargs['roleId'] = role_definition_get['id']

        # create role assignment
        role_assignment_create = self.cmd(
            'az synapse role assignment create --workspace-name {workspace} --role "{role}" --assignee  {userPrincipal} ',
            checks=[
                self.check('roleId', self.kwargs['roleId'])
            ]).get_output_in_json()
        self.kwargs['roleAssignmentId'] = role_assignment_create['id']
        self.kwargs['roleId'] = role_assignment_create['roleId']
        self.kwargs['principalId'] = role_assignment_create['principalId']

        # get role assignment
        self.cmd(
            'az synapse role assignment show --workspace-name {workspace} --id {roleAssignmentId} ',
            checks=[
                self.check('roleId', self.kwargs['roleId']),
                self.check('principalId', self.kwargs['principalId'])
            ])

        # list role assignment by role
        self.cmd(
            'az synapse role assignment list --workspace-name {workspace} --role "{role}" ',
            checks=[
                self.check('length([])', 2)
            ])

        # list role assignment by userPrincipal
        self.cmd(
            'az synapse role assignment list --workspace-name {workspace} --assignee {userPrincipal} ',
            checks=[
                self.check('length([])', 2)
            ])

        # list role assignment by servicePrincipal
        self.cmd(
            'az synapse role assignment list --workspace-name {workspace} --assignee {servicePrincipal} ',
            checks=[
                self.check('length([])', 1)
            ])

        # list role assignment by object_id
        self.cmd(
            'az synapse role assignment list --workspace-name {workspace} --assignee {principalId} ',
            checks=[
                self.check('length([])', 2)
            ])

        # delete role assignment
        self.cmd(
            'az synapse role assignment delete --workspace-name {workspace} --ids {roleAssignmentId} -y ')
        self.cmd(
            'az synapse role assignment show --workspace-name {workspace} --id {roleAssignmentId} ',
            expect_failure=True)

    def _create_workspace(self):
        self.kwargs.update({
            'workspace': self.create_random_name(prefix='clitest', length=16),
            'file-system': 'testfilesystem',
            'login-user': 'cliuser1',
            'login-password': self.create_random_name(prefix='Pswd1', length=16)
        })

        # Create adlsgen2
        self._create_storage_account()

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

    def _create_storage_account(self):
        self.kwargs.update({
            'location': 'eastus',
            'storage-account': self.create_random_name(prefix='adlsgen2', length=16)
        })

        # Wait some time to improve robustness
        if self.is_live or self.in_recording:
            import time
            time.sleep(60)

        # create synapse workspace
        self.cmd(
            'az storage account create --name {storage-account} --resource-group {rg} --enable-hierarchical-namespace true --location {location}', checks=[
                self.check('name', self.kwargs['storage-account']),
                self.check('type', 'Microsoft.Storage/storageAccounts'),
                self.check('provisioningState', 'Succeeded')
            ])
