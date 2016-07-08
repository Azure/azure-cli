from azure.cli.commands import CliArgumentType, register_cli_argument
import azure.cli.commands.parameters #pylint: disable=unused-import

from azure.mgmt.web import WebSiteManagementClient
from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.cli.commands.template_create import register_folded_cli_argument

# FACTORIES

def _web_client_factory(**_):
    return get_mgmt_service_client(WebSiteManagementClient)

# PARAMETER REGISTRATION

register_cli_argument('webapp', 'name', CliArgumentType(options_list=('--name', '-n')))

register_folded_cli_argument('webapp create', 'hosting_plan', 'Microsoft.Web/serverfarms',
                             help='Name or ID of the web application\'s hosting plan.'
                             '  Creates if resource doesn\'t exist.')
