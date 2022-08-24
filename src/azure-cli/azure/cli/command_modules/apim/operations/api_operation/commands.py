# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_api_operation


def load_command_table(commands_loader, _):
    sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiOperationOperations.{}',
        client_factory=cf_api_operation
    )

    custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.api_operation.custom#{}',
        client_factory=cf_api_operation
    )

    with commands_loader.command_group('apim api operation', sdk, custom_command_type=custom_type, is_preview=True) as g:
        g.custom_command('list', 'list_api_operation')
        g.custom_show_command('show', 'get_api_operation')
        g.custom_command('create', 'create_api_operation')
        g.generic_update_command('update', custom_func_name='update_api_operation')
        g.custom_command('delete', 'delete_api_operation')
