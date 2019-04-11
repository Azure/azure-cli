from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.mymod._help import helps  # pylint: disable=unused-import

class NatGatewayLoader(AzCommandsLoader):

    def load_command_table(self, args):
      from azure.cli.core.commands import CliCommandType

      natgateway_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.maps#NatGatewayOperations.{}',
      )

      with self.command_group('network natgateway', natgateway_custom) as g:
        g.command('create', 'create_natgateway')

COMMAND_LOADER_CLS = NatGatewayLoader