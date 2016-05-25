import inspect

from msrest.exceptions import ClientException
from msrest.paging import Paged

from azure.cli.commands import CliCommand
from azure.cli.commands._auto_command import \
    (EXCLUDED_PARAMS, _extract_args_from_signature)
from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError

def cli_command(command_table, name, operation, return_type, client_factory=None):
    """ Registers a default Azure CLI command. These commands require no special parameters. """
    def call_client(kwargs):
        client = client_factory(kwargs) if client_factory else None
        try:
            result = operation(client, **kwargs)
            if not return_type:
                return {}
            if callable(return_type):
                return return_type(result)
            if isinstance(return_type, str):
                return list(result) if isinstance(result, Paged) else result
        except TypeError as exception:
            raise IncorrectUsageError(exception)
        except ClientException as client_exception:
            message = getattr(client_exception, 'message', client_exception)
            raise CLIError(message)

    name = ' '.join(name.split())
    command = CliCommand(name, call_client)
    _extract_args_from_signature(command, operation)
    
    command_table[command.name] = command

