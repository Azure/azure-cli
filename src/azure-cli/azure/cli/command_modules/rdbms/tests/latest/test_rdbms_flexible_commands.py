import time

from datetime import datetime, timedelta
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

    location = 'northeurope'
    location_check = 'North Europe'

    def _remove_resource_group(self, resource_group_name):
        self.cmd('group delete -n {} --yes'.format(resource_group_name))
    
    def _remove_server(self, database_engine, resource_group_name, server_name):
        if server_name:
            self.cmd('{} flexible-server delete -g {} -n {} --force'.format(database_engine, resource_group_name, server_name))
    
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
            storage_size = 131072
            version = 12
        elif database_engine == 'mysql':
            sku_name =  'Standard_B1MS'
            storage_size = 10240
            version = 5.7
        backup_retention = 7

        default_list_checks = [JMESPathCheck('version', version),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('storageProfile.storageMb', storage_size),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]
        
        self.cmd('{} flexible-server create --public-access on'.format(database_engine))
        
        auto_generated_resource_group_name = self.cli_ctx.local_context.get('all', 'resource_group_name')
        location = self.cli_ctx.local_context.get('all', 'location')
        server_name = self.cli_ctx.local_context.get('{} flexible-server'.format(database_engine), 'server_name')
        self.cmd('{} flexible-server show -g {} -n {}'
                .format(database_engine, auto_generated_resource_group_name, server_name), checks=default_list_checks)

        # flexible-server create with user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword@123'
        sku_name = 'Standard_D4s_v3'
        location = self.location
        location_check = self.location_check
        tier = 'GeneralPurpose'
        storage_size = 131072

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('storageProfile.storageMb', storage_size),
                       JMESPathCheck('location', location_check),
                       JMESPathCheck('administratorLogin', admin_user)]
        
        self.cmd('{} flexible-server create -g {} -n {} --admin-user {} --admin-password {} --sku-name {} \
                --version {} --storage-size {} --l {} --tier {} --public-access on'.format(database_engine, resource_group, \
                server_name, admin_user, admin_password, sku_name, version, storage_size, location, tier))
        
        # flexible-server show
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                    checks=list_checks).get_output_in_json()

        # flexible-server update
        backup_retention = 15
        storage_size = 524288
        updated_list_checks = [JMESPathCheck('storageProfile.backupRetentionDays', backup_retention),
                                JMESPathCheck('storageProfile.storageMb', storage_size)]
        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {} --storage-size {}'
                 .format(database_engine, resource_group, server_name, backup_retention, storage_size),
                 checks=updated_list_checks)
        
        # flexible-server restart
        self.cmd('{} flexible-server restart -g {} -n {}'
                     .format(database_engine, resource_group, server_name), checks=NoneCheck())

        # flexible-server stop
        self.cmd('{} flexible-server stop -g {} -n {}'
                     .format(database_engine, resource_group, server_name), checks=NoneCheck())
        
        # flexible-server start
        self.cmd('{} flexible-server start -g {} -n {}'
                     .format(database_engine, resource_group, server_name), checks=NoneCheck())

        # flexible-server list servers
        self.cmd('{} flexible-server list -g {}'.format(database_engine, resource_group),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # flexible-server parameter
        # flexible-server parameter list
        self.cmd('{} flexible-server parameter list -g {} -s {}'
                .format(database_engine, resource_group, server_name))

        # flexible-server parameter show
        parameter_name = 'lock_timeout'
        default_value = '0'
        source = 'system-default'
        self.cmd('{} flexible-server parameter show -g {} -s {} --name {}'
                .format(database_engine, resource_group, server_name, parameter_name), 
                checks=[JMESPathCheck('defaultValue', default_value),
                        JMESPathCheck('source', source)])

        # flexible-server parameter set
        value = '2000'
        source = 'user-override'
        self.cmd('{} flexible-server parameter set -g {} -s {} --name {} -v {} --source {}'
                .format(database_engine, resource_group, server_name, parameter_name, value, source), 
                checks=[JMESPathCheck('value', value),
                        JMESPathCheck('source', source)])


        # test delete server
        self._remove_server(database_engine, resource_group, server_name)
        self._remove_server(database_engine, auto_generated_resource_group_name, server_name)
        self._remove_resource_group(auto_generated_resource_group_name)

        # test list server should be 0
        self.cmd('{} server list -g {}'.format(database_engine, resource_group), checks=NoneCheck())


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    location = 'northeurope'
    location_check = 'North Europe'

    def _remove_resource_group(self, resource_group_name):
        self.cmd('group delete --name {} --yes'.format(resource_group_name))
    
    def _remove_server(self, database_engine, resource_group_name, server_name):
        if server_name:
            self.cmd('{} flexible-server delete -g {} -n {} --force'.format(database_engine, resource_group_name, server_name))

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_postgres_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_mysql_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('mysql', resource_group)
    
    def _test_flexible_server_local_context(self, database_engine, resource_group):
        from knack.util import CLIError

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword@123'
        sku_name = 'Standard_D4s_v3'
        tier = 'GeneralPurpose'
        location = self.location
        location_check = self.location_check
        
        if database_engine == 'postgres':
            version = '12'
        elif database_engine == 'mysql':
            version =  '5.7'
        storage_size = 131072

        self.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group)
        self.cli_ctx.local_context.set(['all'], 'location', location)

        # create
        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('storageProfile.storageMb', storage_size),
                       JMESPathCheck('location', location_check),
                       JMESPathCheck('administratorLogin', admin_user)]
        
        self.cmd('{} flexible-server create --name {} --admin-user {} --admin-password {} --version {} --storage-size {} \
                --sku-name {} --tier {} --public-access on'.format(database_engine, server_name, admin_user, admin_password, version, storage_size, sku_name, tier))
        
        result = self.cmd('{} flexible-server show'.format(database_engine), checks=list_checks).get_output_in_json()

        # flexible-server update
        backup_retention = 15
        storage_size = 524288
        updated_list_checks = [JMESPathCheck('storageProfile.backupRetentionDays', 15),
                       JMESPathCheck('storageProfile.storageMb', storage_size)]

        self.cmd('{} flexible-server update --backup-retention {} --storage-size {} '.format(database_engine, backup_retention, storage_size), \
                    checks=updated_list_checks)

        # restart
        self.cmd('{} flexible-server restart'
                     .format(database_engine), checks=NoneCheck())
        
        # flexible-server stop
        self.cmd('{} flexible-server stop'
                     .format(database_engine), checks=NoneCheck())
        
        # flexible-server start
        self.cmd('{} flexible-server start'
                     .format(database_engine), checks=NoneCheck())

        # flexible-server parameter
        # list
        self.cmd('{} flexible-server parameter list'.format(database_engine))

        # show
        parameter_name = 'lock_timeout'
        default_value = '0'
        source = 'system-default'
        self.cmd('{} flexible-server parameter show --name {}'.format(database_engine, parameter_name), 
                checks=[JMESPathCheck('defaultValue', default_value),
                        JMESPathCheck('source', source)])
        # set
        value = '2000'
        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {}'.format(database_engine, parameter_name, value, source), 
                checks=[JMESPathCheck('value', value),
                        JMESPathCheck('source', source)])

        # flexible-server delete
        self.cmd('{} flexible-server delete --force'.format(database_engine), checks=NoneCheck())


class FlexibleServerFirewllMgmtScenarioTest(ScenarioTest):
    
    location = 'northeurope'
    location_check = 'North Europe'

    def _remove_resource_group(self, resource_group_name):
        self.cmd('group delete --name {} --yes'.format(resource_group_name))
    
    def _remove_server(self, database_engine, resource_group_name, server_name):
        if server_name:
            self.cmd('{} flexible-server delete -g {} -n {} --force'.format(database_engine, resource_group_name, server_name))

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_postgres_flexible_server_firewall_rule(self, resource_group):
        self._test_firewall_rule_mgmt('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_mysql_flexible_server_firewall_rule(self, resource_group):
        self._test_firewall_rule_mgmt('mysql', resource_group)
    
    def _test_firewall_rule_mgmt(self, database_engine, resource_group):

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword@123'
        sku_name = 'Standard_D4s_v3'
        tier = 'GeneralPurpose'
        location = self.location
        
        if database_engine == 'postgres':
            version = '12'
        elif database_engine == 'mysql':
            version =  '5.7'
        storage_size = 131072

        self.cmd('{} flexible-server create -g {} --name {} --admin-user {} --admin-password {} --version {} --storage-size {} \
                --sku-name {} --tier {} -l {} --public-access on'.format(database_engine, resource_group, server_name, admin_user, admin_password, version, storage_size, sku_name, tier, location))

        firewall_rule_name = 'firewall_test_rule'
        start_ip_address = '10.10.10.10'
        end_ip_address = '12.12.12.12'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        
        self.cmd('{} flexible-server firewall-rule create -g {} -s {} --name {} '
                '--start-ip-address {} --end-ip-address {} '
                .format(database_engine, resource_group, server_name, firewall_rule_name, start_ip_address, end_ip_address),
                checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule show -g {} -s {} --name {} '
                .format(database_engine, resource_group, server_name, firewall_rule_name, start_ip_address, end_ip_address),
                checks=firewall_rule_checks)
        
        new_start_ip_address = '9.9.9.9'
        self.cmd('{} flexible-server firewall-rule update -g {} -s {} --name {} --start-ip-address {}'
                .format(database_engine, resource_group, server_name, firewall_rule_name, new_start_ip_address),
                checks=[JMESPathCheck('startIpAddress', new_start_ip_address)])
        
        self.cmd('{} flexible-server firewall-rule delete -g {} -s {} --name {} --yes'
                .format(database_engine, resource_group, server_name, firewall_rule_name))