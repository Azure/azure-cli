#pylint: disable=unused-import
from azure.mgmt.web.operations import (
    SitesOperations)

from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.command_modules.webapp.custom import ConvenienceWebCommands
from azure.cli.command_modules.webapp._params import (_web_client_factory)
from azure.cli.commands._auto_command import build_operation, CommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L

command_table = CommandTable()

build_operation(
    'webapp', 'webapps', _web_client_factory,
    [
        CommandDefinition(SitesOperations.get_sites, '[Site]'),
    ], command_table)
