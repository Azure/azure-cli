from azure.cli.testsdk.base import execute
from azure.cli.testsdk.preparers import AbstractPreparer, SingleValueReplacer
from azure.cli.testsdk import (
    ResourceGroupPreparer,
     ScenarioTest)
DEFAULT_LOCATION = "eastus2euap"
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20

class ServerPreparer(AbstractPreparer, SingleValueReplacer):

    def __init__(self, engine_type, location, engine_parameter_name='database_engine',
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server',
                 resource_group_parameter_name='resource_group'):
        super(ServerPreparer, self).__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.engine_type = engine_type
        self.engine_parameter_name = engine_parameter_name
        self.location = location
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az {} flexible-server create -l {} -g {} -n {} --public-access none'
        execute(self.cli_ctx, template.format(self.engine_type,
                                              self.location,
                                              group, name))
        return {self.parameter_name: name,
                self.engine_parameter_name: self.engine_type}

    def remove_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        execute(self.cli_ctx, 'az {} flexible-server delete -g {} -n {} --yes'.format(self.engine_type, group, name))

    def _get_resource_group(self, **kwargs):
        return kwargs.get(self.resource_group_parameter_name)
    
class AdvancedThreatProtectionTest(ScenarioTest):
     
   # @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @ServerPreparer(engine_type='mysql', location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_threat_protection_mgmt(self, resource_group, server):
        self._test_flexible_server_threat_model_update_mgmt('mysql', resource_group, server)

    def _test_flexible_server_threat_model_update_mgmt(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server threat-protection update -g {} -s {} \
                    '.format(database_engine, resource_group, server))
        
        basic_info = self.cmd('{} flexible-server threat-protection list -g {} -s {}'
                             .format(database_engine, resource_group, server)).get_output_in_json()

        self.assertEqual(basic_info['name'], server)
        self.assertEqual(basic_info['resourceGroup'], resource_group)

        # Enable advanced threat protection for the flexible server
        self.cmd('{} flexible-server threat-protection update -g {} -s {} --defender_state enable'.format(database_engine, resource_group, server))       
        # Verifing that advanced threat protection is enabled
        advanced_threat_protection_settings = self.cmd('{} flexible-server threat-protection show -g {} -s {}'.format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(advanced_threat_protection_settings['state'], 'Enabled')
        # Disable advanced threat protection for the flexible server
        self.cmd('{} flexible-server threat-protection update -g {} -s {} --defender_state disable'.format(database_engine, resource_group, server))
        # Verifing that advanced threat protection is disabled
        advanced_threat_protection_settings = self.cmd('{} flexible-server advanced-threat-protection show -g {} -s {}'.format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(advanced_threat_protection_settings['state'], 'Disabled')