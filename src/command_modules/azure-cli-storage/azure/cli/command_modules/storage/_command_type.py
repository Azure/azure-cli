import inspect

from msrest.exceptions import ClientException
from msrest.paging import Paged

from azure.cli.commands import CliCommand
from azure.cli.commands._auto_command import \
    (EXCLUDED_PARAMS, _extract_args_from_signature)
from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError

from azure.cli.command_modules.storage._validators import validate_client_parameters

def cli_storage_data_plane_command(command_table, name, operation, return_type, client_factory):

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

    # add parameters required to create a storage client
    command.add_argument('account_name', *['--account-name'], required=False, default=None)
    command.add_argument('account_key', *['--account-key'], required=False, default=None)
    command.add_argument('connection_string', *['--connection-string'], required=False, default=None, validator=validate_client_parameters)
    command.add_argument('sas_token', *['--sas-token'], required=False, default=None)
    
    command_table[command.name] = command

