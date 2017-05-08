# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import create_command, command_table
from ._validators import validate_client_parameters


def cli_storage_data_plane_command(name, operation, client_factory,
                                   transform=None, table_transformer=None, exception_handler=None):
    """ Registers an Azure CLI Storage Data Plane command. These commands always include the
    four parameters which can be used to obtain a storage client: account-name, account-key,
    connection-string, and sas-token. """
    command = create_command(__name__, name, operation, transform, table_transformer,
                             client_factory, exception_handler=exception_handler)
    # add parameters required to create a storage client
    group_name = 'Storage Account'
    command.add_argument('account_name', '--account-name', required=False, default=None,
                         arg_group=group_name,
                         help='Storage account name. Must be used in conjunction with either '
                         'storage account key or a SAS token. Environment variable: '
                         'AZURE_STORAGE_ACCOUNT')
    command.add_argument('account_key', '--account-key', required=False, default=None,
                         arg_group=group_name,
                         help='Storage account key. Must be used in conjunction with storage '
                         'account name. Environment variable: '
                         'AZURE_STORAGE_KEY')
    command.add_argument('connection_string', '--connection-string', required=False, default=None,
                         validator=validate_client_parameters, arg_group=group_name,
                         help='Storage account connection string. Environment variable: '
                         'AZURE_STORAGE_CONNECTION_STRING')
    command.add_argument('sas_token', '--sas-token', required=False, default=None,
                         arg_group=group_name,
                         help='A Shared Access Signature (SAS). Must be used in conjunction with '
                         'storage account name. Environment variable: '
                         'AZURE_STORAGE_SAS_TOKEN')
    command_table[command.name] = command
