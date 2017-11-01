# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import _cli_generic_update_command
from azure.cli.core.util import empty_on_404
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE

from ._format import output_format
from ._factory import get_acr_service_client

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
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
    cli_command(__name__, 'acr show-usage', 'azure.cli.command_modules.acr.custom#acr_show_usage',
                table_transformer=output_format)
    _cli_generic_update_command(
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
                'azure.cli.command_modules.acr.webhook#acr_webhook_list_events',
                table_transformer=output_format)
    cli_command(__name__, 'acr webhook ping',
                'azure.cli.command_modules.acr.webhook#acr_webhook_ping',
                table_transformer=output_format)
    _cli_generic_update_command(
        __name__,
        'acr webhook update',
        'azure.cli.command_modules.acr.webhook#acr_webhook_update_get',
        'azure.cli.command_modules.acr.webhook#acr_webhook_update_set',
        factory=lambda: get_acr_service_client().webhooks,
        custom_function_op='azure.cli.command_modules.acr.webhook#acr_webhook_update_custom',
        table_transformer=output_format)

    cli_command(__name__, 'acr replication list',
                'azure.cli.command_modules.acr.replication#acr_replication_list',
                table_transformer=output_format)
    cli_command(__name__, 'acr replication create',
                'azure.cli.command_modules.acr.replication#acr_replication_create',
                table_transformer=output_format)
    cli_command(__name__, 'acr replication delete',
                'azure.cli.command_modules.acr.replication#acr_replication_delete',
                table_transformer=output_format)
    cli_command(__name__, 'acr replication show',
                'azure.cli.command_modules.acr.replication#acr_replication_show',
                table_transformer=output_format)
    cli_generic_update_command(
        __name__,
        'acr replication update',
        'azure.cli.command_modules.acr.replication#acr_replication_update_get',
        'azure.cli.command_modules.acr.replication#acr_replication_update_set',
        factory=lambda: get_acr_service_client().replications,
        custom_function_op='azure.cli.command_modules.acr.replication#acr_replication_update_custom',
        table_transformer=output_format)
