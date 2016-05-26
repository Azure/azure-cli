#pylint: disable=unused-import
from azure.mgmt.web.operations import SitesOperations

from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.commands.command_types import cli_command
from azure.cli.command_modules.webapp._params import _web_client_factory
from azure.cli.command_modules.webapp.mgmt_webapp.lib \
    import (WebAppCreationClient as WebAppClient,
            WebAppCreationClientConfiguration as WebAppClientConfig)
from azure.cli.command_modules.webapp.mgmt_webapp.lib.operations import WebAppOperations

command_table = CommandTable()

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        return result.properties.outputs

factory = lambda _: _web_client_factory()
cli_command(command_table, 'webapp get-sites', SitesOperations.get_sites, '[Site]', factory)

factory = lambda _: get_mgmt_service_client(WebAppClient, WebAppClientConfig).web_app
cli_command(command_table, 'webapp create', WebAppOperations.create_or_update,
            DeploymentOutputLongRunningOperation(), factory)
