# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_apim


def load_command_table(self, _):

    apim_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiManagementOperations.{}',
        client_factory=cf_apim)


    with self.command_group('apim', apim_sdk, client_factory=cf_apim) as g:
        g.custom_command('create', 'create_apim')
        #g.command('delete', 'delete')
        g.custom_command('list', 'list_apim')
        #g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='update', custom_func_name='update_apim')


    with self.command_group('apim', is_preview=True):
        pass

