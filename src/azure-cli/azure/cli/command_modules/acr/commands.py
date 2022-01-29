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
    endpoints_output_format,
    build_output_format,
    task_output_format,
    task_identity_format,
    taskrun_output_format,
    run_output_format,
    helm_list_output_format,
    helm_show_output_format,
    scope_map_output_format,
    token_output_format,
    token_credential_output_format,
    agentpool_output_format,
    connected_registry_output_format,
    connected_registry_list_output_format,
    list_references_output_format,
    manifest_output_format,
)
from ._client_factory import (
    cf_acr_registries,
    cf_acr_replications,
    cf_acr_webhooks,
    cf_acr_tasks,
    cf_acr_taskruns,
    cf_acr_runs,
    cf_acr_scope_maps,
    cf_acr_tokens,
    cf_acr_token_credentials,
    cf_acr_private_endpoint_connections,
    cf_acr_agentpool,
    cf_acr_connected_registries
)


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def load_command_table(self, _):

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

    acr_manifest_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.manifest#{}'
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

    acr_pack_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.pack#{}',
        table_transformer=run_output_format,
        client_factory=cf_acr_runs
    )

    acr_task_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.task#{}',
        table_transformer=task_output_format,
        client_factory=cf_acr_tasks
    )

    acr_taskrun_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.taskrun#{}',
        table_transformer=taskrun_output_format,
        client_factory=cf_acr_taskruns
    )

    acr_helm_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.helm#{}'
    )

    acr_network_rule_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.network_rule#{}',
        client_factory=cf_acr_registries
    )

    acr_check_health_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.check_health#{}'
    )

    acr_scope_map_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.scope_map#{}',
        table_transformer=scope_map_output_format,
        client_factory=cf_acr_scope_maps
    )

    acr_token_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.token#{}',
        table_transformer=token_output_format,
        client_factory=cf_acr_tokens
    )

    acr_token_credential_generate_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.token#{}',
        table_transformer=token_credential_output_format,
        client_factory=cf_acr_token_credentials
    )

    acr_agentpool_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.agentpool#{}',
        table_transformer=agentpool_output_format,
        client_factory=cf_acr_agentpool
    )

    acr_connected_registry_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.connected_registry#{}',
        table_transformer=connected_registry_output_format,
        client_factory=cf_acr_connected_registries
    )

    acr_private_endpoint_connection_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.acr.private_endpoint_connection#{}',
        client_factory=cf_acr_private_endpoint_connections
    )

    with self.command_group('acr', acr_custom_util) as g:
        g.command('check-name', 'acr_check_name', table_transformer=None)
        g.command('list', 'acr_list')
        g.command('create', 'acr_create')
        g.command('delete', 'acr_delete')
        g.show_command('show', 'acr_show')
        g.command('show-usage', 'acr_show_usage', table_transformer=usage_output_format)
        g.command('show-endpoints', 'acr_show_endpoints', table_transformer=endpoints_output_format)
        g.generic_update_command('update',
                                 getter_name='acr_update_get',
                                 setter_name='acr_update_set',
                                 custom_func_name='acr_update_custom',
                                 custom_func_type=acr_custom_util,
                                 client_factory=cf_acr_registries)

    with self.command_group('acr', acr_login_util) as g:
        g.command('login', 'acr_login')

    with self.command_group('acr', acr_import_util) as g:
        g.command('import', 'acr_import', supports_no_wait=True)

    with self.command_group('acr credential', acr_cred_util) as g:
        g.show_command('show', 'acr_credential_show')
        g.command('renew', 'acr_credential_renew')

    with self.command_group('acr repository', acr_repo_util) as g:
        g.command('list', 'acr_repository_list')
        g.command('show-tags', 'acr_repository_show_tags')
        g.command('show-manifests', 'acr_repository_show_manifests',
                  deprecate_info=self.deprecate(redirect='acr manifest metadata list', hide=True))
        g.show_command('show', 'acr_repository_show')
        g.command('update', 'acr_repository_update')
        g.command('delete', 'acr_repository_delete')
        g.command('untag', 'acr_repository_untag')

    with self.command_group('acr manifest', acr_manifest_util, is_preview=True) as g:
        g.show_command('show', 'acr_manifest_show', table_transformer=manifest_output_format)
        g.command('list', 'acr_manifest_list', table_transformer=manifest_output_format)
        g.command('delete', 'acr_manifest_delete')
        g.command('list-referrers', 'acr_manifest_list_referrers', table_transformer=list_references_output_format)

    with self.command_group('acr manifest metadata', acr_manifest_util, is_preview=True) as g:
        g.show_command('show', 'acr_manifest_metadata_show')
        g.command('list', 'acr_manifest_metadata_list')
        g.command('update', 'acr_manifest_metadata_update')

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

    with self.command_group('acr pack', acr_pack_util, is_preview=True) as g:
        g.command('build', 'acr_pack_build', supports_no_wait=True)

    with self.command_group('acr task', acr_task_util) as g:
        g.command('create', 'acr_task_create')
        g.show_command('show', 'acr_task_show')
        g.command('list', 'acr_task_list')
        g.command('delete', 'acr_task_delete')
        g.command('update', 'acr_task_update')
        g.command('identity assign', 'acr_task_identity_assign')
        g.command('identity remove', 'acr_task_identity_remove')
        g.command('identity show', 'acr_task_identity_show', table_transformer=task_identity_format)
        g.command('credential add', 'acr_task_credential_add')
        g.command('credential update', 'acr_task_credential_update')
        g.command('credential remove', 'acr_task_credential_remove')
        g.command('credential list', 'acr_task_credential_list')
        g.command('timer add', 'acr_task_timer_add')
        g.command('timer update', 'acr_task_timer_update')
        g.command('timer remove', 'acr_task_timer_remove')
        g.command('timer list', 'acr_task_timer_list')
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

    with self.command_group('acr taskrun', acr_taskrun_util, is_preview=True) as g:
        g.command('list', 'acr_taskrun_list')
        g.command('delete', 'acr_taskrun_delete')
        g.show_command('show', 'acr_taskrun_show')
        g.command('logs', 'acr_taskrun_logs', client_factory=cf_acr_runs,
                  table_transformer=None)

    with self.command_group('acr config content-trust', acr_policy_util) as g:
        g.show_command('show', 'acr_config_content_trust_show')
        g.command('update', 'acr_config_content_trust_update')

    with self.command_group('acr config retention', acr_policy_util, is_preview=True) as g:
        g.show_command('show', 'acr_config_retention_show')
        g.command('update', 'acr_config_retention_update')

    def _helm_deprecate_message(self):
        msg = "This {} has been deprecated and will be removed in future release.".format(self.object_type)
        msg += " Use '{}' instead.".format(self.redirect)
        msg += " For more information go to"
        msg += " https://aka.ms/acr/helm"
        return msg

    with self.command_group('acr helm', acr_helm_util,
                            deprecate_info=self.deprecate(redirect="helm v3",
                                                          message_func=_helm_deprecate_message)) as g:
        g.command('list', 'acr_helm_list', table_transformer=helm_list_output_format)
        g.show_command('show', 'acr_helm_show', table_transformer=helm_show_output_format)
        g.command('delete', 'acr_helm_delete')
        g.command('push', 'acr_helm_push')
        g.command('repo add', 'acr_helm_repo_add')
        g.command('install-cli', 'acr_helm_install_cli', is_preview=True)

    with self.command_group('acr network-rule', acr_network_rule_util) as g:
        g.command('list', 'acr_network_rule_list')
        g.command('add', 'acr_network_rule_add')
        g.command('remove', 'acr_network_rule_remove')

    with self.command_group('acr', acr_check_health_util) as g:
        g.command('check-health', 'acr_check_health')

    with self.command_group('acr scope-map', acr_scope_map_util, is_preview=True) as g:
        g.command('create', 'acr_scope_map_create')
        g.command('delete', 'acr_scope_map_delete')
        g.command('update', 'acr_scope_map_update')
        g.show_command('show', 'acr_scope_map_show')
        g.command('list', 'acr_scope_map_list')

    with self.command_group('acr token', acr_token_util, is_preview=True) as g:
        g.command('create', 'acr_token_create')
        g.command('delete', 'acr_token_delete')
        g.command('update', 'acr_token_update')
        g.show_command('show', 'acr_token_show')
        g.command('list', 'acr_token_list')
        g.command('credential delete', 'acr_token_credential_delete')

    with self.command_group('acr token credential', acr_token_credential_generate_util) as g:
        g.command('generate', 'acr_token_credential_generate')

    with self.command_group('acr agentpool', acr_agentpool_util, is_preview=True) as g:
        g.command('create', 'acr_agentpool_create', supports_no_wait=True)
        g.command('update', 'acr_agentpool_update', supports_no_wait=True)
        g.command('delete', 'acr_agentpool_delete', supports_no_wait=True)
        g.command('list', 'acr_agentpool_list')
        g.show_command('show', 'acr_agentpool_show')

    with self.command_group('acr private-endpoint-connection', acr_private_endpoint_connection_util) as g:
        g.command('delete', 'delete')
        g.show_command('show', 'show')
        g.command('list', 'list_connections')
        g.command('approve', 'approve')
        g.command('reject', 'reject')

    with self.command_group('acr private-link-resource', acr_custom_util) as g:
        g.command('list', 'list_private_link_resources')

    with self.command_group('acr identity', acr_custom_util) as g:
        g.show_command('show', 'show_identity')
        g.command('assign', 'assign_identity')
        g.command('remove', 'remove_identity')

    with self.command_group('acr encryption', acr_custom_util) as g:
        g.show_command('show', 'show_encryption')
        g.command('rotate-key', "rotate_key")

    with self.command_group('acr connected-registry', acr_connected_registry_util, is_preview=True) as g:
        g.command('create', 'acr_connected_registry_create')
        g.command('delete', 'acr_connected_registry_delete')
        g.show_command('show', 'acr_connected_registry_show')
        g.command('deactivate', 'acr_connected_registry_deactivate')
        g.command('update', 'acr_connected_registry_update')
        g.command('get-settings', 'acr_connected_registry_get_settings')
        g.command('permissions update', 'acr_connected_registry_permissions_update')
        g.show_command('permissions show', 'acr_connected_registry_permissions_show',
                       table_transformer=scope_map_output_format)
        g.command('list', 'acr_connected_registry_list',
                  table_transformer=connected_registry_list_output_format)
        g.command('list-client-tokens', 'acr_connected_registry_list_client_tokens',
                  table_transformer=token_output_format)
        g.command('repo', 'acr_connected_registry_permissions_update',
                  deprecate_info=self.deprecate(redirect='permissions update', hide=True))

    with self.command_group('acr connected-registry install', acr_connected_registry_util,
                            deprecate_info=self.deprecate(redirect='acr connected-registry get-settings',
                                                          hide=True)) as g:
        g.command('info', 'acr_connected_registry_install_info')
        g.command('renew-credentials', 'acr_connected_registry_install_renew_credentials')
