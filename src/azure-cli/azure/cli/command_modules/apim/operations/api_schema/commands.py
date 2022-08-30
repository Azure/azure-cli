# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_api_schema


def load_command_table(commands_loader, _):
    api_schema_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiSchemaOperations.{}',
        client_factory=cf_api_schema
    )

    api_schema_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.api_schema.custom#{}',
        client_factory=cf_api_schema
    )

    with commands_loader.command_group('apim api schema', api_schema_sdk, custom_command_type=api_schema_custom_type, is_preview=True, client_factory=cf_api_schema) as g:
        g.custom_command('create', 'create_api_schema', supports_no_wait=True)
        g.custom_command('delete', 'delete_api_schema', confirmation=True, supports_no_wait=True)
        g.custom_show_command('show', 'get_api_schema')
        g.custom_command('list', 'list_api_schema')
        g.wait_command('wait')
