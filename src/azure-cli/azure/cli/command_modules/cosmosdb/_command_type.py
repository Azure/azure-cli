# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import AzCommandGroup


class CosmosDbCommandGroup(AzCommandGroup):

    def _create_cosmosdb_command(self, name, method_name=None, command_type_name=None, **kwargs):
        """Registers an Azure CLI Cosmos DB Data Plane command. These commands always include the
        parameters which can be used to obtain a cosmosdb client."""
        merged_kwargs = self._flatten_kwargs(kwargs, command_type_name)
        if 'exception_handler' not in merged_kwargs:
            from ._exception_handler import generic_exception_handler
            merged_kwargs['exception_handler'] = generic_exception_handler
        if command_type_name == 'command_type':
            command_name = self.command(name, method_name, **merged_kwargs)
        else:
            command_name = self.custom_command(name, method_name, **merged_kwargs)

        command = self.command_loader.command_table[command_name]

        # add parameters required to create a cosmosdb client
        group_name = 'Cosmos DB Account'
        command.add_argument('db_resource_group_name', '--resource-group-name', '-g',
                             arg_group=group_name,
                             help='name of the resource group. Must be used in conjunction with '
                                  'cosmosdb account name.')
        command.add_argument('db_account_name', '--name', '-n', arg_group=group_name,
                             help='Cosmos DB account name. Must be used in conjunction with '
                                  'either name of the resource group or cosmosdb account key.')

        command.add_argument('db_account_key', '--key', required=False, default=None,
                             arg_group=group_name,
                             help='Cosmos DB account key. Must be used in conjunction with cosmosdb '
                                  'account name or url-connection.')

        command.add_argument('db_url_connection', '--url-connection', required=False, default=None,
                             arg_group=group_name,
                             help='Cosmos DB account url connection. Must be used in conjunction with '
                                  'cosmosdb account key.')

    def cosmosdb_command(self, name, method_name=None, command_type=None, **kwargs):
        command_type_name = 'command_type'
        if command_type:
            kwargs[command_type_name] = command_type
        self._create_cosmosdb_command(name, method_name, command_type_name, **kwargs)

    def cosmosdb_custom(self, name, method_name=None, command_type=None, **kwargs):
        command_type_name = 'custom_command_type'
        if command_type:
            kwargs[command_type_name] = command_type
        self._create_cosmosdb_command(name, method_name, command_type_name, **kwargs)
