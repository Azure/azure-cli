# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.util import empty_on_404

from ._constants import WEBHOOK_API_VERSION
from ._format import output_format
from ._factory import get_acr_service_client

cli_command(__name__, 'acr credential show',
            'azure.cli.command_modules.acr.credential#acr_credential_show',
            table_transformer=output_format, exception_handler=empty_on_404)
cli_command(__name__, 'acr credential renew',
            'azure.cli.command_modules.acr.credential#acr_credential_renew',
            table_transformer=output_format)

cli_command(__name__, 'acr check-name', 'azure.cli.command_modules.acr.custom#acr_check_name')
cli_command(__name__, 'acr list', 'azure.cli.command_modules.acr.custom#acr_list',
            table_transformer=output_format)
cli_command(__name__, 'acr create', 'azure.cli.command_modules.acr.custom#acr_create',
            table_transformer=output_format)
cli_command(__name__, 'acr delete', 'azure.cli.command_modules.acr.custom#acr_delete',
            table_transformer=output_format)
cli_command(__name__, 'acr show', 'azure.cli.command_modules.acr.custom#acr_show',
            table_transformer=output_format, exception_handler=empty_on_404)
cli_command(__name__, 'acr login', 'azure.cli.command_modules.acr.custom#acr_login')
cli_generic_update_command(
    __name__,
    'acr update',
    'azure.cli.command_modules.acr.custom#acr_update_get',
    'azure.cli.command_modules.acr.custom#acr_update_set',
    factory=lambda: get_acr_service_client().registries,
    custom_function_op='azure.cli.command_modules.acr.custom#acr_update_custom',
    table_transformer=output_format)

cli_command(__name__, 'acr repository list',
            'azure.cli.command_modules.acr.repository#acr_repository_list')
cli_command(__name__, 'acr repository show-tags',
            'azure.cli.command_modules.acr.repository#acr_repository_show_tags')
cli_command(__name__, 'acr repository show-manifests',
            'azure.cli.command_modules.acr.repository#acr_repository_show_manifests')
cli_command(__name__, 'acr repository delete',
            'azure.cli.command_modules.acr.repository#acr_repository_delete')

cli_command(__name__, 'acr webhook list',
            'azure.cli.command_modules.acr.webhook#acr_webhook_list',
            table_transformer=output_format)
cli_command(__name__, 'acr webhook create',
            'azure.cli.command_modules.acr.webhook#acr_webhook_create',
            table_transformer=output_format)
cli_command(__name__, 'acr webhook delete',
            'azure.cli.command_modules.acr.webhook#acr_webhook_delete',
            table_transformer=output_format)
cli_command(__name__, 'acr webhook show',
            'azure.cli.command_modules.acr.webhook#acr_webhook_show',
            table_transformer=output_format)
cli_command(__name__, 'acr webhook get-config',
            'azure.cli.command_modules.acr.webhook#acr_webhook_get_config',
            table_transformer=output_format)
cli_command(__name__, 'acr webhook list-events',
            'azure.cli.command_modules.acr.webhook#acr_webhook_list_events')
cli_command(__name__, 'acr webhook ping',
            'azure.cli.command_modules.acr.webhook#acr_webhook_ping')
cli_generic_update_command(
    __name__,
    'acr webhook update',
    'azure.cli.command_modules.acr.webhook#acr_webhook_update_get',
    'azure.cli.command_modules.acr.webhook#acr_webhook_update_set',
    factory=lambda: get_acr_service_client(WEBHOOK_API_VERSION).webhooks,
    custom_function_op='azure.cli.command_modules.acr.webhook#acr_webhook_update_custom',
    table_transformer=output_format)
