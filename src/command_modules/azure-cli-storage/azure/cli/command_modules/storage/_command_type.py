#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os

from azure.cli.commands import create_command, command_table

from azure.cli.command_modules.storage._validators import validate_client_parameters

def cli_storage_data_plane_command(name, operation, client_factory,
                                   transform=None, simple_output_query=None):
    """ Registers an Azure CLI Storage Data Plane command. These commands always include the
    four parameters which can be used to obtain a storage client: account-name, account-key,
    connection-string, and sas-token. """
    command = create_command(name, operation, transform, simple_output_query, client_factory)

    account_set = 'SET' if os.environ.get('AZURE_STORAGE_ACCOUNT') else 'NOT SET'
    key_set = 'SET' if os.environ.get('AZURE_STORAGE_KEY') else 'NOT SET'
    cs_set = 'SET' if os.environ.get('AZURE_STORAGE_CONNECTION_STRING') else 'NOT SET'
    sas_set = 'SET' if os.environ.get('AZURE_SAS_TOKEN') else 'NOT SET'

    # add parameters required to create a storage client
    command.add_argument('account_name', '--account-name', required=False, default=None,
                         arg_group='StorageAccount',
                         help='Storage account name. Must be used in conjunction with either '
                         'storage account key or a SAS token. Var: AZURE_STORAGE_ACCOUNT '
                         '({})'.format(account_set))
    command.add_argument('account_key', '--account-key', required=False, default=None,
                         arg_group='StorageAccount',
                         help='Storage account key. Must be used in conjunction with storage '
                         'account name. Var: AZURE_STORAGE_KEY ({})'.format(key_set))
    command.add_argument('connection_string', '--connection-string', required=False, default=None,
                         validator=validate_client_parameters, arg_group='StorageAccount',
                         help='Storage account connection string. Var: '
                         'AZURE_STORAGE_CONNECTION_STRING ({})'.format(cs_set))
    command.add_argument('sas_token', '--sas-token', required=False, default=None,
                         arg_group='StorageAccount',
                         help='A Shared Access Signature (SAS). Must be used in conjunction with '
                         'storage account name. Var: AZURE_SAS_TOKEN ({})'.format(sas_set))
    command_table[command.name] = command
