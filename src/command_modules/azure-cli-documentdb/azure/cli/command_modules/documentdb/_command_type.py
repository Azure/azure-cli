# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import create_command, command_table


def cli_documentdb_data_plane_command(name,  # pylint: disable=too-many-arguments
                                      operation, client_factory, transform=None,
                                      table_transformer=None, exception_handler=None):
    """Registers an Azure CLI DocumentDB Data Plane command. These commands always include the
    parameters which can be used to obtain a documentdb client."""

    if not exception_handler:
        from ._exception_handler import generic_exception_handler
        exception_handler = generic_exception_handler

    command = create_command(__name__, name, operation, transform, table_transformer,
                             client_factory, exception_handler=exception_handler)

    # add parameters required to create a documentdb client
    group_name = 'DocumentDB Account'

    command.add_argument('db_resource_group_name', '--resource-group-name', '-g',
                         arg_group=group_name,
                         help='name of the resource group. Must be used in conjunction with '
                              'documentdb account name.')
    command.add_argument('db_account_name', '--name', '-n', arg_group=group_name,
                         help='DocumentDB account name. Must be used in conjunction with '
                              'either name of the resource group or documentdb account key.')

    command.add_argument('db_account_key', '--key', required=False, default=None,
                         arg_group=group_name,
                         help='DocumentDB account key. Must be used in conjunction with documentdb '
                              'account name or url-connection.')

    command.add_argument('db_url_connection', '--url-connection', required=False, default=None,
                         arg_group=group_name,
                         help='DocumentDB account url connection. Must be used in conjunction with '
                              'documentdb account key.')

    command_table[command.name] = command
