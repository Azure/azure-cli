import time

from datetime import datetime
from time import sleep
from dateutil.tz import tzutc   # pylint: disable=import-error
from azure_devtools.scenario_tests import AllowLargeResponse
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.local_context import AzCLILocalContext, ALL, LOCAL_CONTEXT_FILE
from azure.cli.core.util import CLIError
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError   # pylint: disable=unused-import
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    LocalContextScenarioTest,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)


# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20
GROUP_NAME_PREFIX = 'azuredbclitest-'
GROUP_NAME_MAX_LENGTH = 20

class FlexibleServerMgmtScenarioTest(ScenarioTest):

    location = 'southeastasia'

    def _remove_resource_group(self, resource_group_name):
        self.cmd('group delete --name {} --yes'.format(resource_group_name))
    
    def _remove_server(self, database_engine, resource_group_name, server_name):
        if server_name:
            self.cmd('{} flexible-server delete -g {} -n {} --yes --no-wait'.format(database_engine, resource_group_name, server_name))
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_postgres_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_mysql_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('mysql', resource_group)

    def _test_flexible_server_mgmt(self, database_engine, resource_group):
        from knack.util import CLIError

        # flexible-server create
        # flexible-server create auto-generate, no local context
        if not self.cli_ctx.local_context.is_on:
            self.cmd('local-context on')

        if database_engine == 'postgres':
            sku_name = 'Standard_D4s_v3'
            storage_size = 128000
            version = 12
        elif database_engine == 'mysql':
            sku_name =  'Standard_B1MS'
            storage_size = 10000
            version = 5.7
        backup_retension = 7

        location = self.location
        default_list_checks = [JMESPathCheck('storageProfile.storageSizeMb', storage_size),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retension)]
        
        self.cmd('{} flexible-server create'.format(database_engine), checks=default_list_checks)
        with self.assertRaises(CLIError):
            self._remove_resource_group(self.cli_ctx.local_context.get('all', 'resource_group_name'))

        auto_generated_resource_group_name = self.cli_ctx.local_context.get('all', 'resource_group_name')
        location = self.cli_ctx.local_context.get('all', 'location')
        server_name = self.cli_ctx.local_context.get('{} flexible-server'.format(database_engine), 'server_name')
        self._remove_server(database_engine, auto_generated_resource_group_name, server_name)
        self._remove_resource_group(auto_generated_resource_group_name)

        # flexible-server create user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword123'
        if database_engine == 'postgres':
            skuname = 'Standard_D4s_v3'
        elif database_engine == 'mysql':
            skuname =  'Standard_B1MS'
        location = self.location

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('administratorLogin', admin_user),
                       JMESPathCheck('location', location)]
        
        self.cmd('{} flexible-server create -g {} -n {} --admin-user {} --admin-password {} --sku-name {}'
                .format(database_engine, resource_group, server_name, admin_user, admin_password, skuname),
                checks=list_checks)

        # flexible-server create failure
        failing_admin_user = 'root'
        self.cmd('{} flexible-server create -g {} --admin-user {}'.format(database_engine, resource_group, failing_admin_user),
                 expect_failure=True)
        
        # flexible-server show
        self.cmd('{} flexible-server show -g {} -n {}'
                    .format(database_engine, resource_group, server_name),
                    checks=list_checks)

        # flexible-server update
        self.cmd('{} server update -g {} -n {} --admin-password {} '
                 '--ssl-enforcement Disabled --tags key=2'
                 .format(database_engine, resource_group, server_name, admin_password),
                 checks=[
                     JMESPathCheck('name', server_name),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_user)])
        
        # flexible-server restart
        self.cmd('{} server restart -g {} -n {}'
                     .format(database_engine, resource_group, server_name), checks=NoneCheck())

        # flexible-server 
        self._remove_server(self, database_engine, resource_group, server_name)


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    location = 'southeastasia'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus2')
    def test_postgres_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_mysql_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('mysql', resource_group)
    
    def _test_flexible_server_local_context(self, database_engine, resource_group):
        from knack.util import CLIError

        self.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group)
        self.cli_ctx.local_context.set(['all'], 'location', self.location)
        
        local_context_output = self.cmd('local-context show').get_output_in_json()
        print(local_context_output)

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword123'
        if database_engine == 'postgres':
            skuname = 'Standard_D4s_v3'
        elif database_engine == 'mysql':
            skuname =  'Standard_B1MS'
        location = self.location

        # create
        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('administratorLogin', admin_user),
                       JMESPathCheck('location', location)]
        
        self.cmd('{} flexible-server create --name {} --admin-user {} --admin-password {} --sku-name {}'
                .format(database_engine, server_name, admin_user, admin_password, skuname),
                checks=list_checks)

        self.cmd('local-context show', checks=[
            JMESPathCheck("all.resource_group_name", group_name),
            JMESPathCheck("all.location", location),
        ])

        self.cmd('{} flexible-server show'.format(database), checks=list_checks)
        self.cmd('{} flexible-server update --tags k1=v1'.format(database), checks=list_checks + [JMESPathCheck('tags.key', '2')])
        self.cmd('{} flexible-server delete'.format(database))            