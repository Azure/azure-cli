from azure.cli.commands import create_command

from azure.cli.command_modules.storage._validators import validate_client_parameters

def cli_storage_data_plane_command(command_table, name, operation, client_factory,
                                   transform=None):
    """ Registers an Azure CLI Storage Data Plane command. These commands always include the
    four parameters which can be used to obtain a storage client: account-name, account-key,
    connection-string, and sas-token. """
    command = create_command(name, operation, transform, client_factory)

    # add parameters required to create a storage client
    command.add_argument('account_name', *['--account-name'], required=False, default=None)
    command.add_argument('account_key', *['--account-key'], required=False, default=None)
    command.add_argument('connection_string', *['--connection-string'], required=False,
                         default=None, validator=validate_client_parameters)
    command.add_argument('sas_token', *['--sas-token'], required=False, default=None)

    command_table[command.name] = command
