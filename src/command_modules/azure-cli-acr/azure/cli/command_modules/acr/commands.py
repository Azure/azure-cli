# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._format import (
    registry_output_format,
    usage_output_format,
    policy_output_format,
    credential_output_format,
    webhook_output_format,
    webhook_get_config_output_format,
    webhook_list_events_output_format,
    webhook_ping_output_format,
    replication_output_format,
    build_output_format,
    task_output_format,
    run_output_format,
    helm_list_output_format,
    helm_show_output_format
)
from ._client_factory import (
    cf_acr_registries,
    cf_acr_replications,
    cf_acr_webhooks,
    cf_acr_tasks,
    cf_acr_runs
)


def load_command_table(self, _):  # pylint: disable=too-many-statements

    acr_custom_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.custom#{}',
        table_transformer=registry_output_format,
        client_factory=cf_acr_registries
    )

    acr_login_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.custom#{}'
    )

    acr_import_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.import#{}',
        client_factory=cf_acr_registries
    )

    acr_policy_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.policy#{}',
        table_transformer=policy_output_format,
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
        client_factory=cf_acr_runs
    )

    acr_run_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.run#{}',
        table_transformer=run_output_format,
        client_factory=cf_acr_runs
    )

    acr_task_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.task#{}',
        table_transformer=task_output_format,
        client_factory=cf_acr_tasks
    )

    acr_helm_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.helm#{}'
    )

    acr_network_rule_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.network_rule#{}',
        client_factory=cf_acr_registries
    )

    with self.command_group('acr', acr_custom_util) as g:
        g.command('check-name', 'acr_check_name', table_transformer=None)
        g.command('list', 'acr_list')
        g.command('create', 'acr_create')
        g.command('delete', 'acr_delete')
        g.show_command('show', 'acr_show')
        g.command('show-usage', 'acr_show_usage', table_transformer=usage_output_format)
        g.generic_update_command('update',
                                 getter_name='acr_update_get',
                                 setter_name='acr_update_set',
                                 custom_func_name='acr_update_custom',
                                 custom_func_type=acr_custom_util,
                                 client_factory=cf_acr_registries)

    with self.command_group('acr', acr_login_util) as g:
        g.command('login', 'acr_login')

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
                                 client_factory=cf_acr_webhooks)

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
                                 client_factory=cf_acr_replications)

    with self.command_group('acr', acr_build_util) as g:
        g.command('build', 'acr_build', supports_no_wait=True)

    with self.command_group('acr', acr_run_util) as g:
        g.command('run', 'acr_run', supports_no_wait=True)

    with self.command_group('acr task', acr_task_util) as g:
        g.command('create', 'acr_task_create')
        g.show_command('show', 'acr_task_show')
        g.command('list', 'acr_task_list')
        g.command('delete', 'acr_task_delete')
        g.command('update', 'acr_task_update')
        g.command('identity assign', 'acr_task_identity_assign')
        g.command('identity remove', 'acr_task_identity_remove')
        g.command('identity show', 'acr_task_identity_show')
        g.command('credential add', 'acr_task_credential_add')
        g.command('credential update', 'acr_task_credential_update')
        g.command('credential remove', 'acr_task_credential_remove')
        g.command('credential list', 'acr_task_credential_list')
        g.command('run', 'acr_task_run', client_factory=cf_acr_runs,
                  table_transformer=run_output_format, supports_no_wait=True)
        g.command('list-runs', 'acr_task_list_runs', client_factory=cf_acr_runs,
                  table_transformer=run_output_format)
        g.command('show-run', 'acr_task_show_run', client_factory=cf_acr_runs,
                  table_transformer=run_output_format)
        g.command('cancel-run', 'acr_task_cancel_run', client_factory=cf_acr_runs,
                  table_transformer=None)
        g.command('update-run', 'acr_task_update_run', client_factory=cf_acr_runs,
                  table_transformer=run_output_format)
        g.command('logs', 'acr_task_logs', client_factory=cf_acr_runs,
                  table_transformer=None)

    with self.command_group('acr config content-trust', acr_policy_util) as g:
        g.command('show', 'acr_config_content_trust_show')
        g.command('update', 'acr_config_content_trust_update')

    with self.command_group('acr helm', acr_helm_util) as g:
        g.command('list', 'acr_helm_list', table_transformer=helm_list_output_format)
        g.command('show', 'acr_helm_show', table_transformer=helm_show_output_format)
        g.command('delete', 'acr_helm_delete')
        g.command('push', 'acr_helm_push')
        g.command('repo add', 'acr_helm_repo_add')

    with self.command_group('acr network-rule', acr_network_rule_util) as g:
        g.command('list', 'acr_network_rule_list')
        g.command('add', 'acr_network_rule_add')
        g.command('remove', 'acr_network_rule_remove')
