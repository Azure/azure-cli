# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.sdk.util import _CommandGroup

from azure.cli.command_modules.storage._validators import validate_client_parameters


class _StorageCommandGroup(_CommandGroup):

    def data_plane_command(self, name, method_name=None, command_type=None, **kwargs):
        """ Registers an Azure CLI Storage Data Plane command. These commands always include the
        four parameters which can be used to obtain a storage client: account-name, account-key,
        connection-string, and sas-token. """

        self._check_stale()
        merged_kwargs = self.group_kwargs.copy()
        group_command_type = merged_kwargs.get('command_type', None)
        if command_type:
            merged_kwargs.update(command_type.settings)
        elif group_command_type:
            merged_kwargs.update(group_command_type.settings)
        merged_kwargs.update(kwargs)

        operations_tmpl = merged_kwargs.get('operations_tmpl')
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        operation = operations_tmpl.format(method_name) if operations_tmpl else None
        self.command_loader._cli_command(command_name, operation, **merged_kwargs)  # pylint: disable=protected-access

        # add parameters required to create a storage client
        command = self.command_loader.command_table[command_name]
        group_name = 'Storage Account'
        command.add_argument('account_name', '--account-name', required=False, default=None,
                             arg_group=group_name,
                             help='Storage account name. Related environment variable: AZURE_STORAGE_ACCOUNT. Must be used '
                                  'in conjunction with either storage account key or a SAS token. If neither are present, '
                                  'the command will try to query the storage account key using the authenticated Azure '
                                  'account. If a large number of storage commands are executed the API quota may be hit')
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
