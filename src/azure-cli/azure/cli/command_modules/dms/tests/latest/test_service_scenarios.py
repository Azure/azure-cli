# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import json

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, VirtualNetworkPreparer, JMESPathCheck, JMESPathCheckGreaterThan


class DmsServiceTests(ScenarioTest):
    service_random_name_prefix = 'dmsclitest'
    location_name = 'centralus'
    sku_name = 'Premium_4vCores'
    vsubnet_id = '/subscriptions/{}/resourceGroups/ERNetwork/providers/Microsoft.Network/virtualNetworks/AzureDMS-CORP-USC-VNET-5044/subnets/Subnet-1'
    name_exists_checks = [JMESPathCheck('nameAvailable', False),
                          JMESPathCheck('reason', 'AlreadyExists')]
    name_available_checks = [JMESPathCheck('nameAvailable', True)]

    @ResourceGroupPreparer(name_prefix='dms_cli_test', location=location_name)
    @VirtualNetworkPreparer(name_prefix='dms.clitest.vn')
    def test_service_commands(self, resource_group):
        service_name = self.create_random_name(self.service_random_name_prefix, 15)
        subnet = self.cmd('az network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()
        self.kwargs.update({
            'lname': self.location_name,
            'skuname': self.sku_name,
            'vnetid': subnet['id'],
            'sname': service_name
        })

        skus_checks = [JMESPathCheckGreaterThan('length(@)', 0)]
        self.cmd('az dms list-skus', checks=skus_checks)

        self.cmd('az dms show -g {rg} -n {sname}', expect_failure=True)

        create_checks = [JMESPathCheck('location', self.location_name),
                         JMESPathCheck('name', service_name),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('sku.name', self.sku_name),
                         JMESPathCheck('virtualSubnetId', self.kwargs['vnetid']),
                         JMESPathCheck('provisioningState', 'Succeeded'),
                         JMESPathCheck('tags.area', 'cli'),
                         JMESPathCheck('tags.env', 'test'),
                         JMESPathCheck('type', 'Microsoft.DataMigration/services')]
        self.cmd('az dms create -l {lname} -n {sname} -g {rg} --sku-name {skuname} --subnet {vnetid} --tags area=cli env=test', checks=create_checks)

        self.cmd('az dms show -g {rg} -n {sname}', checks=create_checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.cmd('az dms list -g {rg}', checks=list_checks)

        status_online_checks = [JMESPathCheck('status', 'Online'),
                                JMESPathCheck('vmSize', 'Standard_F4')]
        self.cmd('az dms check-status -g {rg} -n {sname}', checks=status_online_checks)

        self.cmd('az dms stop -g {rg} -n {sname}')

        status_offline_checks = [JMESPathCheck('status', 'Stopped'),
                                 JMESPathCheck('vmSize', None)]
        self.cmd('az dms check-status -g {rg} -n {sname}', checks=status_offline_checks)

        self.cmd('az dms start -g {rg} -n {sname}')

        self.cmd('az dms check-status -g {rg} -n {sname}', checks=status_online_checks)

        self.cmd('az dms check-name -l {lname} -n {sname}', checks=self.name_exists_checks)

        self.cmd('az dms delete -g {rg} -n {sname} -y')

        self.cmd('az dms check-name -l {lname} -n {sname}', checks=self.name_available_checks)

    @ResourceGroupPreparer(name_prefix='dms_cli_test_', location=location_name)
    @VirtualNetworkPreparer(name_prefix='dms.clitest.vn')
    def test_project_commands(self, resource_group):
        service_name = self.create_random_name(self.service_random_name_prefix, 15)
        project_name1 = self.create_random_name('project1', 15)
        project_name2 = self.create_random_name('project2', 15)
        project_name_mysql = self.create_random_name('projectmysql', 20)
        project_name_pg = self.create_random_name('projectpg', 20)
        subnet = self.cmd('az network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()

        self.kwargs.update({
            'lname': self.location_name,
            'skuname': self.sku_name,
            'vnetid': subnet['id'],
            'sname': service_name,
            'pname1': project_name1,
            'pname2': project_name2,
            'pnamemysql': project_name_mysql,
            'pnamepg': project_name_pg
        })

        # Set up container service
        self.cmd('az dms create -l {lname} -n {sname} -g {rg} --sku-name {skuname} --subnet {vnetid} --tags area=cli env=test')

        self.cmd('az dms project show -g {rg} --service-name {sname} -n {pname1}', expect_failure=True)

        create_checks = [JMESPathCheck('location', self.location_name),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('name', project_name1),
                         JMESPathCheck('sourcePlatform', 'SQL'),
                         JMESPathCheck('targetPlatform', 'SQLDB'),
                         JMESPathCheck('provisioningState', 'Succeeded'),
                         JMESPathCheck('tags.Cli', ''),
                         JMESPathCheck('tags.Type', 'test'),
                         JMESPathCheck('type', 'Microsoft.DataMigration/services/projects')]
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pname1} --source-platform SQL --target-platform SQLDB --tags Type=test Cli', checks=create_checks)

        self.cmd('az dms project show -g {rg} --service-name {sname} -n {pname1}', create_checks)

        # Test MySQL project creation and deletion
        create_checks_mysql = [JMESPathCheck('location', self.location_name),
                               JMESPathCheck('resourceGroup', resource_group),
                               JMESPathCheck('name', project_name_mysql),
                               JMESPathCheck('sourcePlatform', 'MySQL'),
                               JMESPathCheck('targetPlatform', 'AzureDbForMySQL'),
                               JMESPathCheck('provisioningState', 'Succeeded'),
                               JMESPathCheck('tags.Cli', ''),
                               JMESPathCheck('tags.Type', 'test'),
                               JMESPathCheck('type', 'Microsoft.DataMigration/services/projects')]
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pnamemysql} --source-platform MySQL --target-platform AzureDbForMySql --tags Type=test Cli', checks=create_checks_mysql)
        self.cmd('az dms project show -g {rg} --service-name {sname} -n {pnamemysql}', create_checks_mysql)

        # Test PostgreSQL project creation and deletion
        create_checks_pg = [JMESPathCheck('location', self.location_name),
                            JMESPathCheck('resourceGroup', resource_group),
                            JMESPathCheck('name', project_name_pg),
                            JMESPathCheck('sourcePlatform', 'PostgreSQL'),
                            JMESPathCheck('targetPlatform', 'AzureDbForPostgreSQL'),
                            JMESPathCheck('provisioningState', 'Succeeded'),
                            JMESPathCheck('tags.Cli', ''),
                            JMESPathCheck('tags.Type', 'test'),
                            JMESPathCheck('type', 'Microsoft.DataMigration/services/projects')]
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pnamepg} --source-platform PostgreSQL --target-platform AzureDbForPostgreSQL --tags Type=test Cli', checks=create_checks_pg)
        self.cmd('az dms project show -g {rg} --service-name {sname} -n {pnamepg}', create_checks_pg)

        create_checks_notags = [JMESPathCheck('tags', None)]
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pname2} --source-platform SQL --target-platform SQLDB', checks=create_checks_notags)

        list_checks = [JMESPathCheck('length(@)', 4),
                       JMESPathCheck("length([?name == '{}'])".format(project_name1), 1)]
        self.cmd('az dms project list -g {rg} --service-name {sname}', list_checks)

        self.cmd('az dms project check-name -g {rg} --service-name {sname} -n {pname2}', checks=self.name_exists_checks)

        self.cmd('az dms project delete -g {rg} --service-name {sname} -n {pname2} -y')

        self.cmd('az dms project check-name -g {rg} --service-name {sname} -n {pname2}', checks=self.name_available_checks)

        # Clean up service for live runs
        self.cmd('az dms delete -g {rg} -n {sname} --delete-running-tasks true -y')

    @ResourceGroupPreparer(name_prefix='dms_cli_test_', location=location_name)
    @VirtualNetworkPreparer(name_prefix='dms.clitest.vn')
    def test_task_commands(self, resource_group):
        from azure.cli.testsdk.checkers import JMESPathPatternCheck
        service_name = self.create_random_name(self.service_random_name_prefix, 15)

        project_name = self.create_random_name('project', 15)
        task_name1 = self.create_random_name('task1', 15)
        task_name2 = self.create_random_name('task2', 15)
        database_options1 = "[ { 'name': 'SourceDatabase1', 'target_database_name': 'TargetDatabase1', 'make_source_db_read_only': False, 'table_map': { 'dbo.TestTableSource1': 'dbo.TestTableTarget1', 'dbo.TestTableSource2': 'dbo.TestTableTarget2' } } ]"
        database_options2 = "[ { 'name': 'SourceDatabase2', 'target_database_name': 'TargetDatabase2', 'make_source_db_read_only': False, 'table_map': { 'dbo.TestTableSource1': 'dbo.TestTableTarget1', 'dbo.TestTableSource2': 'dbo.TestTableTarget2' } } ]"
        source_connection_info = "{ 'userName': 'testuser', 'password': 'testpassword', 'dataSource': 'notarealsourceserver', 'authentication': 'SqlAuthentication', 'encryptConnection': True, 'trustServerCertificate': True }"
        target_connection_info = "{ 'userName': 'testuser', 'password': 'testpassword', 'dataSource': 'notarealtargetserver', 'authentication': 'SqlAuthentication', 'encryptConnection': True, 'trustServerCertificate': True }"
        subnet = self.cmd('az network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()

        project_name_mysql = self.create_random_name('projectmysql', 20)
        task_name_mysql = self.create_random_name('taskmysql', 20)
        source_connection_info_mysql = "{ 'userName': 'testuser', 'password': 'testpassword', 'serverName': 'notarealsourceserver', 'databaseName': 'notarealdatabasename'}"
        target_connection_info_mysql = "{ 'userName': 'testuser', 'password': 'testpassword', 'serverName': 'notarealtargetserver', 'databaseName': 'notarealdatabasename'}"
        database_options_mysql = "[ { 'name': 'SourceDatabase1', 'target_database_name': 'TargetDatabase1', 'tableMap': { 'SourceDatabase1.TestTableSource1': 'TargetDatabase1.TestTableTarget1', 'SourceDatabase1.TestTableSource2': 'TargetDatabase1.TestTableTarget2' } } ]"

        project_name_pg = self.create_random_name('projectpg', 20)
        task_name_pg = self.create_random_name('taskpg', 20)
        source_connection_info_pg = "{ 'userName': 'testuser', 'password': 'testpassword', 'serverName': 'notarealsourceserver', 'databaseName': 'notarealdatabasename', 'encryptConnection': False, 'trustServerCertificate': True }"
        target_connection_info_pg = "{ 'userName': 'testuser', 'password': 'testpassword', 'serverName': 'notarealtargetserver', 'databaseName': 'notarealdatabasename'}"
        database_options_pg = "[ { 'name': 'SourceDatabase1', 'target_database_name': 'TargetDatabase1', 'selectedTables': [ 'public.TestTableSource1', 'public.TestTableSource2'] } ]"

        self.kwargs.update({
            'lname': self.location_name,
            'skuname': self.sku_name,
            'vnetid': subnet['id'],
            'sname': service_name,
            'pname': project_name,
            'pnamemysql': project_name_mysql,
            'pnamepg': project_name_pg,
            'tname1': task_name1,
            'tname2': task_name2,
            'tnamemysql': task_name_mysql,
            'tnamepg': task_name_pg,
            'dboptions1': database_options1,
            'dboptions2': database_options2,
            'dboptionsmysql': database_options_mysql,
            'dboptionspg': database_options_pg,
            'sconn': source_connection_info,
            'sconnmysql': source_connection_info_mysql,
            'sconnpg': source_connection_info_pg,
            'tconn': target_connection_info,
            'tconnmysql': target_connection_info_mysql,
            'tconnpg': target_connection_info_pg
        })

        # Set up container service and project
        self.cmd('az dms create -l {lname} -n {sname} -g {rg} --sku-name {skuname} --subnet {vnetid} --tags area=cli env=test')
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pname} --source-platform SQL --target-platform SQLDB')
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pnamemysql} --source-platform MySQL --target-platform AzureDbForMySql')
        self.cmd('az dms project create -g {rg} --service-name {sname} -l {lname} -n {pnamepg} --source-platform PostgreSQL --target-platform AzureDbForPostgreSQL')

        self.cmd('az dms project task show -g {rg} --service-name {sname} --project-name {pname} -n {tname1}', expect_failure=True)
        self.cmd('az dms project task show -g {rg} --service-name {sname} --project-name {pnamemysql} -n {tnamemysql}', expect_failure=True)
        self.cmd('az dms project task show -g {rg} --service-name {sname} --project-name {pnamepg} -n {tnamepg}', expect_failure=True)

        create_checks = [JMESPathCheck('name', task_name1),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('type', 'Microsoft.DataMigration/services/projects/tasks'),
                         JMESPathCheck('length(properties.input.selectedDatabases[0].tableMap)', 2),
                         JMESPathCheck('properties.input.sourceConnectionInfo.dataSource', 'notarealsourceserver'),
                         JMESPathCheck('properties.input.targetConnectionInfo.dataSource', 'notarealtargetserver'),
                         JMESPathCheck('properties.taskType', 'Migrate.SqlServer.SqlDb'),
                         JMESPathCheck('properties.input.validationOptions.enableDataIntegrityValidation', False),
                         JMESPathCheck('properties.input.validationOptions.enableQueryAnalysisValidation', False),
                         JMESPathCheck('properties.input.validationOptions.enableSchemaValidation', False)]
        cancel_checks = [JMESPathCheck('name', task_name1),
                         JMESPathPatternCheck('properties.state', 'Cancel(?:ed|ing)')]
        create_checks_mysql = [JMESPathCheck('name', task_name_mysql),
                               JMESPathCheck('resourceGroup', resource_group),
                               JMESPathCheck('type', 'Microsoft.DataMigration/services/projects/tasks'),
                               JMESPathCheck('length(properties.input.selectedDatabases[0].tableMap)', 2),
                               JMESPathCheck('properties.input.sourceConnectionInfo.serverName', 'notarealsourceserver'),
                               JMESPathCheck('properties.input.targetConnectionInfo.serverName', 'notarealtargetserver'),
                               JMESPathCheck('properties.taskType', 'Migrate.MySql.AzureDbForMySql.Sync')]
        cancel_checks_mysql = [JMESPathCheck('name', task_name_mysql),
                               JMESPathPatternCheck('properties.state', 'Cancel(?:ed|ing)')]
        create_checks_pg = [JMESPathCheck('name', task_name_pg),
                            JMESPathCheck('resourceGroup', resource_group),
                            JMESPathCheck('type', 'Microsoft.DataMigration/services/projects/tasks'),
                            JMESPathCheck('length(properties.input.selectedDatabases[0].selectedTables)', 2),
                            JMESPathCheck('properties.input.sourceConnectionInfo.serverName', 'notarealsourceserver'),
                            JMESPathCheck('properties.input.sourceConnectionInfo.encryptConnection', False),
                            JMESPathCheck('properties.input.sourceConnectionInfo.trustServerCertificate', True),
                            JMESPathCheck('properties.input.targetConnectionInfo.serverName', 'notarealtargetserver'),
                            JMESPathCheck('properties.input.targetConnectionInfo.encryptConnection', True),
                            JMESPathCheck('properties.input.targetConnectionInfo.trustServerCertificate', False),
                            JMESPathCheck('properties.taskType', 'Migrate.PostgreSql.AzureDbForPostgreSql.SyncV2')]
        cancel_checks_pg = [JMESPathCheck('name', task_name_pg),
                            JMESPathPatternCheck('properties.state', 'Cancel(?:ed|ing)')]

        # SQL Tests
        self.cmd('az dms project task create --task-type OfflineMigration --database-options-json "{dboptions1}" -n {tname1} --project-name {pname} -g {rg} --service-name {sname} --source-connection-json "{sconn}" --target-connection-json "{tconn}"', checks=create_checks)
        self.cmd('az dms project task show -g {rg} --service-name {sname} --project-name {pname} -n {tname1}', checks=create_checks)
        self.cmd('az dms project task cancel -g {rg} --service-name {sname} --project-name {pname} -n {tname1}', checks=cancel_checks)

        # MySQL Tests
        self.cmd('az dms project task create --task-type OnlineMigration --database-options-json "{dboptionsmysql}" -n {tnamemysql} --project-name {pnamemysql} -g {rg} --service-name {sname} --source-connection-json "{sconnmysql}" --target-connection-json "{tconnmysql}"', checks=create_checks_mysql)
        self.cmd('az dms project task show -g {rg} --service-name {sname} --project-name {pnamemysql} -n {tnamemysql}', checks=create_checks_mysql)
        self.cmd('az dms project task cancel -g {rg} --service-name {sname} --project-name {pnamemysql} -n {tnamemysql}', checks=cancel_checks_mysql)

        # PG Tests
        self.cmd('az dms project task create --task-type OnlineMigration --database-options-json "{dboptionspg}" -n {tnamepg} --project-name {pnamepg} -g {rg} --service-name {sname} --source-connection-json "{sconnpg}" --target-connection-json "{tconnpg}"', checks=create_checks_pg)
        self.cmd('az dms project task show -g {rg} --service-name {sname} --project-name {pnamepg} -n {tnamepg}', checks=create_checks_pg)
        self.cmd('az dms project task cancel -g {rg} --service-name {sname} --project-name {pnamepg} -n {tnamepg}', checks=cancel_checks_pg)

        self.cmd('az dms project task create --task-type OfflineMigration --database-options-json "{dboptions2}" -n {tname2} --project-name {pname} -g {rg} --service-name {sname} --source-connection-json "{sconn}" --target-connection-json "{tconn}"')

        list_checks = [JMESPathCheck('length(@)', 2),
                       JMESPathCheck("length([?name == '{}'])".format(task_name1), 1)]
        self.cmd('az dms project task list -g {rg} --service-name {sname} --project-name {pname} --task-type "Migrate.SqlServer.SqlDb"', checks=list_checks)

        self.cmd('az dms project task check-name -g {rg} --service-name {sname} --project-name {pname} -n {tname1}', checks=self.name_exists_checks)

        self.cmd('az dms project task delete -g {rg} --service-name {sname} --project-name {pname} -n {tname1} --delete-running-tasks true -y')

        self.cmd('az dms project task check-name -g {rg} --service-name {sname} --project-name {pname} -n {tname1}', checks=self.name_available_checks)

        # Clean up service for live runs
        self.cmd('az dms delete -g {rg} -n {sname} --delete-running-tasks true -y')
