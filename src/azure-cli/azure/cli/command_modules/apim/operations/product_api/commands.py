# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_product_api


def load_command_table(commands_loader, _):
    sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ProductApiOperations.{}',
        client_factory=cf_product_api
    )

    custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.product_api.custom#{}',
        client_factory=cf_product_api
    )

    with commands_loader.command_group('apim product api', sdk, custom_command_type=custom_type, is_preview=True) as g:
        g.custom_command('list', 'list_product_api')
        g.custom_command('check', 'check_product_exists')
        g.custom_command('add', 'add_product_api')
        g.custom_command('delete', 'delete_product_api')
