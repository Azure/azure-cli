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

    location = 'eastus2euap'

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
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        location = self.location
        if database_engine == 'postgres':
            version = '12'
            storage_size = 128
            sku_name = 'Standard_D2s_v3'
        elif database_engine == 'mysql':
            version =  '5.7'
            storage_size = 10
            sku_name = 'Standard_B1MS'
        
        backup_retention = 7
        storage_size_mb = storage_size * 1024

        default_list_checks = [JMESPathCheck('version', version),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]
        
        result = self.cmd('{} flexible-server create -l {}'.format(database_engine, location)).get_output_in_json()
        generated_resource_group_name = result['resourceGroup']
        generated_server_name = result['id'].split('/')[-1]
        self.cmd('{} flexible-server show -g {} -n {}'
                .format(database_engine, generated_resource_group_name, generated_server_name), checks=default_list_checks)

        # flexible-server create with user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        admin_user = 'cloudsa'
        admin_password = 'SecretPassword@123'
        sku_name = 'Standard_D4s_v3'
        tier = 'GeneralPurpose'
        high_availability = 'Disabled'
        tag_key1 = 'key1'
        tag_value1 = 'val1'
        tags = tag_key1 + '=' + tag_value1
        storage_size = 64
        storage_size_mb = storage_size * 1024
        backup_retention = 10

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention),
                       JMESPathCheck('haEnabled', high_availability),
                       JMESPathCheck('tags.'+tag_key1, tag_value1),
                       JMESPathCheck('administratorLogin', admin_user)]
        
        self.cmd('{} flexible-server create -g {} -n {} --l {} --admin-user {} --admin-password {} --sku-name {} '
                '--version {} --storage-size {} --backup-retention {} --tier {} --high-availability {} --tags {} '
                .format(database_engine, resource_group, server_name, location, admin_user, admin_password, sku_name, 
                version, storage_size, backup_retention, tier,  high_availability, tags))
        
        # flexible-server show
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                    checks=list_checks).get_output_in_json()

        # flexible-server update
        # update storage profile
        backup_retention = 15
        storage_size = 128
        storage_size_mb = storage_size*1024
        high_availability = 'Enabled'
        updated_list_checks = [JMESPathCheck('storageProfile.backupRetentionDays', backup_retention),
                                JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                                JMESPathCheck('haEnabled', high_availability)]
        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {} --storage-size {} --high-availability {}'
                 .format(database_engine, resource_group, server_name, backup_retention, storage_size, high_availability),
                 checks=updated_list_checks)
        
        # update maintenance window
        maintenance_window_day = '1'
        maintenance_window_start_hour = '8'
        maintenance_window_start_minute = '30'
        maintenance_window = maintenance_window_day + ':' + maintenance_window_start_hour + ':' + maintenance_window_start_minute
        updated_list_checks = [JMESPathCheck('maintenanceWindow.dayOfWeek', maintenance_window_day),
                                JMESPathCheck('maintenanceWindow.startHour', maintenance_window_start_hour),
                                JMESPathCheck('maintenanceWindow.startMinute', maintenance_window_start_minute)]
        self.cmd('{} flexible-server update -g {} -n {}  --maintenance-window {} '
                 .format(database_engine, resource_group_name, server_name, maintenance_window),
                 checks=updated_list_checks)
        
        # update sku, password
        sku_name = 'Standard_B1ms'
        tier = 'Burstable'
        admin_password = 'newpassword@123'
        updated_list_checks = [JMESPathCheck('sku.name', sku_name),
                                JMESPathCheck('sku.tier', tier)]
                                
        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {} --admin-password {}'
                 .format(database_engine, resource_group_name, server_name, tier, sku_name, admin_password),
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

        # test delete server
        self._remove_server(database_engine, resource_group, server_name)
        self._remove_server(database_engine, generated_resource_group_name, generated_server_name)
        self._remove_resource_group(generated_resource_group_name)
        
        # test list server should be 0
        self.cmd('{} server list -g {}'.format(database_engine, resource_group), checks=NoneCheck())


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    location = 'eastus2euap'

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
        sku_name = 'Standard_D2s_v3'
        tier = 'GeneralPurpose'
        location = self.location
        
        if database_engine == 'postgres':
            version = '12'
        elif database_engine == 'mysql':
            version =  '5.7'
        storage_size = 128

        self.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group)
        self.cli_ctx.local_context.set(['all'], 'location', location)

        # create
        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('storageProfile.storageMb', storage_size),
                       JMESPathCheck('administratorLogin', admin_user)]
        
        self.cmd('{} flexible-server create --name {} --admin-user {} --admin-password {} --version {} --storage-size {} \
                --sku-name {} --tier {}'.format(database_engine, server_name, admin_user, admin_password, version, storage_size, sku_name, tier))
        
        result = self.cmd('{} flexible-server show'.format(database_engine), checks=list_checks).get_output_in_json()

        # flexible-server update
        backup_retention = 15
        storage_size = 256
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

        # flexible-server delete
        self.cmd('{} flexible-server delete --force'.format(database_engine), checks=NoneCheck())


class FlexibleServerProxyResourceMgmtScenarioTest(ScenarioTest):
    
    location = 'eastus2euap'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_postgres_flexible_server_firewall_rule(self, resource_group):
        self._test_firewall_rule_mgmt('postgres', resource_group)
        self._test_parameter_mgmt('postgres', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=location)
    def test_mysql_flexible_server_firewall_rule(self, resource_group):
        self._test_firewall_rule_mgmt('mysql', resource_group)
        self._test_parameter_mgmt('mysql', resource_group)
    
    def _test_firewall_rule_mgmt(self, database_engine, resource_group):

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        location = self.location

        self.cmd('{} flexible-server create -g {} --name {} -l {}'.format(database_engine, resource_group, server_name, location))

        firewall_rule_name = 'firewall_test_rule'
        start_ip_address = '10.10.10.10'
        end_ip_address = '12.12.12.12'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        
        # firewall-rule create
        self.cmd('{} flexible-server firewall-rule create -g {} -s {} --name {} '
                '--start-ip-address {} --end-ip-address {} '
                .format(database_engine, resource_group, server_name, firewall_rule_name, start_ip_address, end_ip_address),
                checks=firewall_rule_checks)

        # firewall-rule show
        self.cmd('{} flexible-server firewall-rule show -g {} -s {} --name {} '
                .format(database_engine, resource_group, server_name, firewall_rule_name, start_ip_address, end_ip_address),
                checks=firewall_rule_checks)
        
        # firewall-rule update
        new_start_ip_address = '9.9.9.9'
        self.cmd('{} flexible-server firewall-rule update -g {} -s {} --name {} --start-ip-address {}'
                .format(database_engine, resource_group, server_name, firewall_rule_name, new_start_ip_address),
                checks=[JMESPathCheck('startIpAddress', new_start_ip_address)])
        
        new_end_ip_address = '13.13.13.13'
        self.cmd('{} flexible-server firewall-rule update -g {} -s {} --name {} --end-ip-address {}'
                .format(database_engine, resource_group, server_name, firewall_rule_name, new_end_ip_address))
        
        # Add second firewall-rule
        new_firewall_rule_name = 'firewall_test_rule2'
        firewall_rule_checks = [JMESPathCheck('name', new_firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        self.cmd('{} flexible-server firewall-rule create -g {} -s {} --name {} '
                '--start-ip-address {} --end-ip-address {} '
                .format(database_engine, resource_group, server_name, new_firewall_rule_name, start_ip_address, end_ip_address),
                checks=firewall_rule_checks)
        
        # firewall-rule list
        self.cmd('{} flexible-server firewall-rule list -g {} -s {}'
                 .format(database_engine, resource_group, server_name), checks=[JMESPathCheck('length(@)', 2)])
        
        # firewall-rule delete
        self.cmd('{} flexible-server firewall-rule delete --name {} -g {} --server {} --prompt no'
                 .format(database_engine, firewall_rule_name, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server firewall-rule list -g {} --server {}'
                 .format(database_engine, resource_group, server_name), checks=[JMESPathCheck('length(@)', 1)])
        
        self.cmd('{} flexible-server firewall-rule delete -g {} -s {} --name {} --prompt no'
                .format(database_engine, resource_group, server_name, new_firewall_rule_name))
        
        self.cmd('{} flexible-server firewall-rule list -g {} -s {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())
        
    
    def _test_parameter_mgmt(self, database_engine, resource_group):

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        location = self.location

        self.cmd('{} flexible-server create -g {} --name {} -l {}'.format(database_engine, resource_group, server_name, location))

        # list
        self.cmd('{} flexible-server parameter list -g {} -s {}'.format(database_engine, resource_group, server_name), checks=[JMESPathCheck('type(@)', 'array')])

        if database_engine == 'mysql':
            parameter_name = 'wait_timeout'
            default_value = '28800'
            value = '30000'
        elif database_engine == 'postgres':
            parameter_name = 'lock_timeout'
            default_value = '0'
            value = '2000'

        # show
        source = 'system-default'
        self.cmd('{} flexible-server parameter show --name {} -g {} -s {}'.format(database_engine, parameter_name, resource_group, server_name), 
                checks=[JMESPathCheck('defaultValue', default_value),
                        JMESPathCheck('source', source)])
        # set
        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(database_engine, parameter_name, value, source, server_name, resource_group), 
                checks=[JMESPathCheck('value', value),
                        JMESPathCheck('source', source)])
