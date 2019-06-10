# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apimanagement._client_factory import cf_apimanagement


def load_command_table(self, _):

    apimanagement_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiManagementOperations.{}',
        client_factory=cf_apimanagement)


    with self.command_group('apimanagement', apimanagement_sdk, client_factory=cf_apimanagement) as g:
        g.custom_command('create', 'create_apimanagement')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_apimanagement')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='update', custom_func_name='update_apimanagement')

    with self.command_group('apimanagement', is_preview=True):
        pass

