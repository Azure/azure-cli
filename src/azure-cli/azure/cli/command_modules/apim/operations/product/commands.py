# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_product
from azure.cli.command_modules.apim._format import product_output_format


def load_command_table(commands_loader, _):
    product_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ProductOperations.{}',
        client_factory=cf_product
    )

    product_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.product.custom#{}',
        client_factory=cf_product
    )

    with commands_loader.command_group('apim product', product_sdk, custom_command_type=product_custom_type, is_preview=True, client_factory=cf_product) as g:
        g.custom_command('create', 'create_product', table_transformer=product_output_format)
        g.custom_command('list', 'list_product', table_transformer=product_output_format)
        g.custom_show_command('show', 'get_product', table_transformer=product_output_format)
        g.custom_command('delete', 'delete_product', table_transformer=product_output_format)
        g.generic_update_command('update', custom_func_name='update_product', getter_name='get', setter_name='create_or_update', supports_no_wait=True)
        g.wait_command('wait')
