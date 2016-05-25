import inspect

from msrest.exceptions import ClientException
from msrest.paging import Paged

from azure.cli.commands import create_command
from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError

def cli_command(command_table, name, operation, return_type, client_factory=None):
    """ Registers a default Azure CLI command. These commands require no special parameters. """    
    command_table[name] = create_command(name, operation, return_type, client_factory)

