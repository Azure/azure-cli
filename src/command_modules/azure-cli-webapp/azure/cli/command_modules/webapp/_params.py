#pylint: disable=unused-import
import argparse

from azure.cli.commands.argument_types import CliArgumentType, register_cli_argument

from azure.mgmt.web import WebSiteManagementClient, WebSiteManagementClientConfiguration
from azure.cli.commands._command_creation import get_mgmt_service_client

# FACTORIES

def _web_client_factory(**_):
    return get_mgmt_service_client(WebSiteManagementClient, WebSiteManagementClientConfiguration)

# PARAMETER REGISTRATIOn

register_cli_argument('webapp', 'name', CliArgumentType(options_list=('--name', '-n')))
