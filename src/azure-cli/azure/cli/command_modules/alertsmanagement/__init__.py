from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.alertsmanagement._help 


class AlertsManagementCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        alertsmanagement_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.alertsmanagement.custom#{}')
        print ("INIT")
        super(AlertsManagementCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=alertsmanagement_custom,  
                                                    resource_type=ResourceType.MGMT_ALERTSMANAGEMENT)
        print ("INIT complete")

    def load_command_table(self, args):
        print ("Load command")
        from azure.cli.command_modules.alertsmanagement.commands import load_command_table
        load_command_table(self, args)
        print ("Load command complete")
        return self.command_table

    def load_arguments(self, command):
        print ("Load args")
        from azure.cli.command_modules.alertsmanagement._params import load_arguments
        load_arguments(self, command)
        print ("Load args complete")
        
COMMAND_LOADER_CLS = AlertsManagementCommandsLoader