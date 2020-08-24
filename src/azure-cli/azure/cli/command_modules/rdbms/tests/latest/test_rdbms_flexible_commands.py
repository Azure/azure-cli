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
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)


# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 63
GROUP_NAME_PREFIX = 'azuredbclitest-'
GROUP_NAME_MAX_LENGTH = 20

class FlexibleServerMgmtScenarioTest(ScenarioTest):

    def _remove_resource_group(self, resource_group_name):
        self.cmd(self.cli_ctx, 'az group delete --name {} --yes --no-wait'.format(resource_group_name))
    
    def _remove_server(self, database_engine, resource_group_name, server_name):
        if server_name:
            self.cmd(self.cli_ctx, 'az {} flexible-server delete -g {} -n {} --yes --no-wait'.format(database_engine, resource_group_name, server_name))
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location='southeastasia')
    def test_postgres_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location='southeastasia')
    def test_mysql_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('mysql', resource_group)

    def _test_flexible_server_mgmt(self, database_engine, resource_group):
        from knack.util import CLIError

        # flexible-server create
        # flexible-server create auto-generate, no local context
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        auto_generated_output = self.cmd('{} flexible-server create'.format(database_engine))
        with self.assertRaises(CLIError):
            self._remove_resource_group(self.cli_ctx.local_context.get('all', 'server_name'))

        resource_group_name = self.cli_ctx.local_context.get('all', 'server_name')
        location = self.cli_ctx.local_context.get('all', 'location')
        server_name = self.cli_ctx.local_context.get(database_engine + ' flexible-server', 'server_name')
        self._remove_server(database_engine, resource_group_name, server_name)
        self._remove_resource_group(self.cli_ctx.local_context.get('all', 'server_name'))

        # 1-2) user input generate
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword123'
        cu = 2; family = 'Gen5'
        skuname = 'Standard_D4s_v3' 
        loc = 'eastus2'

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('administratorLogin', admin_user),,
                       JMESPathCheck('location', loc)]
        
        self.cmd('{} flexible-server create -g {} --name {} --admin-user {} --admin-password {} --sku-name {}'
                .format(database_engine, resource_group, server_name, admin_user, admin_password, skuname),
                checks=list_checks)

        # flexible-server create failure
        admin_user = 'root'
        self.cmd('{} flexible-server create -g {} --admin-user {}'.format(database_engine, resource_group, admin_user),
                 checks=list_checks, expect_failure=True)
        
        # flexible-server show
        result = self.cmd('{} flexible-server show -g {} --name {}'
                          .format(database_engine, resource_group, server_name),
                          checks=list_checks).get_output_in_json()

        # flexible-server update
        self.cmd('{} server update -g {} --name {} --admin-password {} '
                 '--ssl-enforcement Disabled --tags key=2'
                 .format(database_engine, resource_group, server_name, admin_password),
                 checks=[
                     JMESPathCheck('name', server_name),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])
        
        # flexible-server restart
        self.cmd('{} server restart -g {} --name {}'
                     .format(database_engine, resource_group, server), checks=NoneCheck())

        # flexible-server 
        self._remove_server(self, database_engine, resource_group, server_name)


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='southeastasia')
    def test_postgres_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location='southeastasia')
    def test_mysql_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('mysql', resource_group)
    
    def _test_flexible_server_local_context(self, database_engine, resource_group):
        from knack.util import CLIError
        
        location = 'southeastasia'

        # create
        self.cmd('{} flexible-server create'.format(database_engine),
                checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('location', location)])
        server_name = self.cli_ctx.local_context.get('{} flexible-server'.format(database_engine), 'server_name')
        list_checks = [JMESPathCheck("resourceGroup", resource_group),
                    JMESPathCheck("location", location),
                    JMESPathCheck("name", server_name)]

        self.cmd('local-context show', checks=[
            JMESPathCheck("all.resource_group_name", group_name),
            JMESPathCheck("all.location", location),
        ])

        self.cmd('{} flexible-server show'.format(database), checks=list_checks)
        self.cmd('{} flexible-server update --tags k1=v1'.format(database), checks=list_checks + [JMESPathCheck('tags.key', '2')])
        self.cmd('{} flexible-server delete'.format(database))            
