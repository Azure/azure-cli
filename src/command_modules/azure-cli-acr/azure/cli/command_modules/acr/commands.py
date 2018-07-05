# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._format import (
    registry_output_format,
    usage_output_format,
    credential_output_format,
    webhook_output_format,
    webhook_get_config_output_format,
    webhook_list_events_output_format,
    webhook_ping_output_format,
    replication_output_format,
    build_task_output_format,
    build_task_detail_output_format,
    build_output_format
)
from ._client_factory import (
    cf_acr_registries,
    cf_acr_replications,
    cf_acr_webhooks,
    cf_acr_build_tasks,
    cf_acr_builds
)


def load_command_table(self, _):  # pylint: disable=too-many-statements

    acr_custom_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.custom#{}',
        table_transformer=registry_output_format,
        client_factory=cf_acr_registries
    )

    acr_import_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.import#{}',
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

    acr_build_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.build#{}',
        table_transformer=build_output_format,
        client_factory=cf_acr_builds
    )

    acr_build_task_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.build_task#{}',
        table_transformer=build_task_detail_output_format,
        client_factory=cf_acr_build_tasks
    )

    with self.command_group('acr', acr_custom_util) as g:
        g.command('check-name', 'acr_check_name', table_transformer=None)
        g.command('list', 'acr_list')
        g.command('create', 'acr_create')
        g.command('delete', 'acr_delete')
        g.show_command('show', 'acr_show')
        g.command('login', 'acr_login', table_transformer=None)
        g.command('show-usage', 'acr_show_usage', table_transformer=usage_output_format)
        g.generic_update_command('update',
                                 getter_name='acr_update_get',
                                 setter_name='acr_update_set',
                                 custom_func_name='acr_update_custom',
                                 custom_func_type=acr_custom_util,
                                 client_factory=cf_acr_registries,
                                 table_transformer=registry_output_format)

    with self.command_group('acr', acr_import_util) as g:
        g.command('import', 'acr_import')

    with self.command_group('acr credential', acr_cred_util) as g:
        g.show_command('show', 'acr_credential_show')
        g.command('renew', 'acr_credential_renew')

    with self.command_group('acr repository', acr_repo_util) as g:
        g.command('list', 'acr_repository_list')
        g.command('show-tags', 'acr_repository_show_tags')
        g.command('show-manifests', 'acr_repository_show_manifests')
        g.command('show', 'acr_repository_show')
        g.command('update', 'acr_repository_update')
        g.command('delete', 'acr_repository_delete')
        g.command('untag', 'acr_repository_untag')

    with self.command_group('acr webhook', acr_webhook_util) as g:
        g.command('list', 'acr_webhook_list')
        g.command('create', 'acr_webhook_create')
        g.command('delete', 'acr_webhook_delete')
        g.show_command('show', 'acr_webhook_show')
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
        g.show_command('show', 'acr_replication_show')
        g.generic_update_command('update',
                                 getter_name='acr_replication_update_get',
                                 setter_name='acr_replication_update_set',
                                 custom_func_name='acr_replication_update_custom',
                                 custom_func_type=acr_replication_util,
                                 client_factory=cf_acr_replications,
                                 table_transformer=replication_output_format)

    with self.command_group('acr', acr_build_util) as g:
        g.command('build', 'acr_build')

    with self.command_group('acr build-task', acr_build_task_util) as g:
        g.command('create', 'acr_build_task_create')
        g.show_command('show', 'acr_build_task_show')
        g.command('list', 'acr_build_task_list', table_transformer=build_task_output_format)
        g.command('delete', 'acr_build_task_delete')
        g.command('update', 'acr_build_task_update')
        g.command('run', 'acr_build_task_run', client_factory=cf_acr_builds,
                  table_transformer=build_output_format)
        g.command('list-builds', 'acr_build_task_list_builds', client_factory=cf_acr_builds,
                  table_transformer=build_output_format)
        g.command('show-build', 'acr_build_task_show_build', client_factory=cf_acr_builds,
                  table_transformer=build_output_format)
        g.command('update-build', 'acr_build_task_update_build', client_factory=cf_acr_builds,
                  table_transformer=build_output_format)
        g.command('logs', 'acr_build_task_logs', client_factory=cf_acr_builds,
                  table_transformer=None)
