# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_api
from azure.cli.command_modules.apim._exception_handler import default_exception_handler


def load_command_table(commands_loader, _):
    api_sdk = CliCommandType(operations_tmpl='azure.mgmt.apimanagement.operations#ApiOperations.{}', client_factory=cf_api)
    api_custom_type = CliCommandType(operations_tmpl='azure.cli.command_modules.apim.operations.api.custom#{}', client_factory=cf_api, exception_handler=default_exception_handler)

    with commands_loader.command_group('apim api', api_sdk, custom_command_type=api_custom_type, client_factory=cf_api, is_preview=True) as g:
        g.custom_command('create', 'create_api', supports_no_wait=True, table_transformer=None)
        g.custom_command('delete', 'delete_api', confirmation=True, supports_no_wait=True)
        g.custom_show_command('show', 'get_api', table_transformer=None)
        g.custom_command('list', 'list_api', table_transformer=None)
        g.generic_update_command('update', setter_name='update', custom_func_name='update_api', supports_no_wait=True)
        g.wait_command('wait')
