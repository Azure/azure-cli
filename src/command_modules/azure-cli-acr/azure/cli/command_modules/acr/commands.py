# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404

from ._format import (
    registry_output_format,
    usage_output_format,
    credential_output_format,
    webhook_output_format,
    webhook_get_config_output_format,
    webhook_list_events_output_format,
    webhook_ping_output_format,
    replication_output_format
)
from ._client_factory import cf_acr_registries, cf_acr_replications, cf_acr_webhooks


def load_command_table(self, _):

    acr_custom_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.custom#{}',
        table_transformer=registry_output_format,
        client_factory=cf_acr_registries
    )

    acr_cred_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.credential#{}',
        table_transformer=credential_output_format,
        client_factory=cf_acr_registries
    )

    acr_repo_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.repository#{}'
    )

    acr_webhook_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.webhook#{}',
        table_transformer=webhook_output_format,
        client_factory=cf_acr_webhooks
    )

    acr_replication_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.replication#{}',
        table_transformer=replication_output_format,
        client_factory=cf_acr_replications
    )

    with self.command_group('acr', acr_custom_util) as g:
        g.command('check-name', 'acr_check_name', table_transformer=None)
        g.command('list', 'acr_list')
        g.command('create', 'acr_create')
        g.command('delete', 'acr_delete')
        g.command('show', 'acr_show', exception_handler=empty_on_404)
        g.command('login', 'acr_login', table_transformer=None)
        g.command('show-usage', 'acr_show_usage', table_transformer=usage_output_format)
        g.generic_update_command('update',
                                 getter_name='acr_update_get',
                                 setter_name='acr_update_set',
                                 custom_func_name='acr_update_custom',
                                 custom_func_type=acr_custom_util,
                                 client_factory=cf_acr_registries,
                                 table_transformer=registry_output_format)

    with self.command_group('acr credential', acr_cred_util) as g:
        g.command('show', 'acr_credential_show', exception_handler=empty_on_404)
        g.command('renew', 'acr_credential_renew')

    with self.command_group('acr repository', acr_repo_util) as g:
        g.command('list', 'acr_repository_list')
        g.command('show-tags', 'acr_repository_show_tags')
        g.command('show-manifests', 'acr_repository_show_manifests')
        g.command('delete', 'acr_repository_delete')
        g.command('untag', 'acr_repository_untag')

    with self.command_group('acr webhook', acr_webhook_util) as g:
        g.command('list', 'acr_webhook_list')
        g.command('create', 'acr_webhook_create')
        g.command('delete', 'acr_webhook_delete')
        g.command('show', 'acr_webhook_show')
        g.command('get-config', 'acr_webhook_get_config', table_transformer=webhook_get_config_output_format)
        g.command('list-events', 'acr_webhook_list_events', table_transformer=webhook_list_events_output_format)
        g.command('ping', 'acr_webhook_ping', table_transformer=webhook_ping_output_format)
        g.generic_update_command('update',
                                 getter_name='acr_webhook_update_get',
                                 setter_name='acr_webhook_update_set',
                                 custom_func_name='acr_webhook_update_custom',
                                 custom_func_type=acr_webhook_util,
                                 client_factory=cf_acr_webhooks,
                                 table_transformer=webhook_output_format)

    with self.command_group('acr replication', acr_replication_util) as g:
        g.command('list', 'acr_replication_list')
        g.command('create', 'acr_replication_create')
        g.command('delete', 'acr_replication_delete')
        g.command('show', 'acr_replication_show')
        g.generic_update_command('update',
                                 getter_name='acr_replication_update_get',
                                 setter_name='acr_replication_update_set',
                                 custom_func_name='acr_replication_update_custom',
                                 custom_func_type=acr_replication_util,
                                 client_factory=cf_acr_replications,
                                 table_transformer=replication_output_format)
