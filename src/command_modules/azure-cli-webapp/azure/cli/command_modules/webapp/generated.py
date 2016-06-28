#pylint: disable=unused-import
from azure.mgmt.web.operations import SitesOperations

from azure.cli.commands import LongRunningOperation, cli_command
from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.webapp._params import _web_client_factory
from azure.cli.command_modules.webapp.mgmt_webapp.lib \
    import (WebappCreationClient as WebAppClient)
from azure.cli.command_modules.webapp.mgmt_webapp.lib.operations import WebappOperations

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        return result.properties.outputs

factory = lambda _: _web_client_factory()
cli_command('webapp get-sites', SitesOperations.get_sites, factory)

factory = lambda _: get_mgmt_service_client(WebAppClient).webapp
cli_command('webapp create', WebappOperations.create_or_update, factory,
            transform=DeploymentOutputLongRunningOperation('Creating webapp'))
