#pylint: disable=unused-import
from azure.mgmt.web.operations import (
    SitesOperations)

from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.command_modules.webapp.custom import ConvenienceWebCommands
from azure.cli.command_modules.webapp._params import (_web_client_factory)
from azure.cli.commands._auto_command import build_operation, CommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L
from azure.cli.command_modules.webapp.mgmt_webapp.lib \
    import (WebAppCreationClient as WebAppClient,
            WebAppCreationClientConfiguration as WebAppClientConfig)
from azure.cli.command_modules.webapp.mgmt_webapp.lib.operations import WebAppOperations


command_table = CommandTable()

build_operation(
    'webapp', 'webapps', _web_client_factory,
    [
        CommandDefinition(SitesOperations.get_sites, '[Site]'),
    ], command_table)

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        return result.properties.outputs

build_operation(
    'webapp', 'web_app', lambda **_: get_mgmt_service_client(WebAppClient, WebAppClientConfig),
    [
        CommandDefinition(
            WebAppOperations.create_or_update,
            DeploymentOutputLongRunningOperation(L('Creating web application'),
                                                 L('Web application created')),
            'create')
    ],
    command_table, {'name': {'name': '--name -n'}})
