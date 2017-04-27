# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import create_command, command_table
from azure.cli.core.commands import register_cli_argument, register_extra_cli_argument, CliArgumentType



def cli_documentdb_data_plane_command(name, operation, client_factory,  # pylint: disable=too-many-arguments
                                   transform=None, table_transformer=None, exception_handler=None):
    """ Registers an Azure CLI DocumentDB Data Plane command. These commands always include the
    four parameters which can be used to obtain a documentdb client: account-name, account-key,
    connection-string, and sas-token. """
    command = create_command(__name__, name, operation, transform, table_transformer,
                             client_factory, exception_handler=exception_handler)
    # add parameters required to create a documentdb client
    group_name = 'DocumentDB Account'
     
    command.add_argument('account_key', '--account-key', required=False, default=None,
                         arg_group=group_name,
                         help='DocumentDB account key. Must be used in conjunction with documentdb '
                         'account key. Environment variable: '
                         'AZURE_DOCUMENTDB_KEY')
    
    ## TODO: this doesn't get picked up
    command.add_argument('account_name', '--account-name', required=False, default=None,
                         arg_group=group_name,
                         help='DocumentDB account name. Must be used in conjunction with documentdb '
                         'account name. Environment variable: '
                         'AZURE_DOCUMENTDB_ACCOUNT')
    command.add_argument('url_connection', '--url-connection', required=False, default=None,
                         arg_group=group_name,
                         help='DocumentDB account url connection. Environment variable: '
                         'AZURE_DOCUMENTDB_URL_CONNECTION')

    command_table[command.name] = command

