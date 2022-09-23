# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import CliCommandType


# pylint: disable=line-too-long, too-many-locals, too-many-statements
def load_command_table(self, _):
    from ._client_factory import (
        cf_alert_rules, cf_metric_def, cf_log_profiles, cf_autoscale,
        cf_diagnostics, cf_activity_log, cf_action_groups, cf_activity_log_alerts, cf_event_categories,
        cf_metric_alerts, cf_metric_ns, cf_log_analytics_workspace,
        cf_diagnostics_category,
        cf_private_link_resources, cf_private_link_scoped_resources,
        cf_private_link_scopes, cf_private_endpoint_connections, cf_log_analytics_linked_storage,
        cf_subscription_diagnostics)
    from .transformers import (action_group_list_table)
    from .validators import (process_autoscale_create_namespace,
                             validate_private_endpoint_connection_id,
                             process_action_group_detail_for_creation)
    from ._exception_handler import exception_handler

    monitor_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.custom#{}',
        exception_handler=exception_handler)

    action_group_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#ActionGroupsOperations.{}',
        client_factory=cf_action_groups,
        operation_group='action_groups',
        exception_handler=exception_handler)

    action_group_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.action_groups#{}',
        client_factory=cf_action_groups,
        operation_group='action_groups',
        exception_handler=exception_handler)

    activity_log_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#EventCategoriesOperations.{}',
        client_factory=cf_event_categories,
        operation_group='event_categories',
        exception_handler=exception_handler)

    activity_log_alerts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#ActivityLogAlertsOperations.{}',
        client_factory=cf_activity_log_alerts,
        operation_group='activity_log_alerts',
        exception_handler=exception_handler)

    activity_log_alerts_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.activity_log_alerts#{}',
        client_factory=cf_activity_log_alerts,
        operation_group='activity_log_alerts',
        exception_handler=exception_handler)

    autoscale_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#AutoscaleSettingsOperations.{}',
        client_factory=cf_autoscale,
        operation_group='autoscale_settings',
        exception_handler=exception_handler)

    autoscale_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.autoscale_settings#{}',
        client_factory=cf_autoscale,
        operation_group='autoscale_settings',
        exception_handler=exception_handler)

    diagnostics_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#DiagnosticSettingsOperations.{}',
        client_factory=cf_diagnostics,
        operation_group='diagnostic_settings',
        exception_handler=exception_handler)

    diagnostics_categories_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#DiagnosticSettingsCategoryOperations.{}',
        client_factory=cf_diagnostics_category,
        operation_group='diagnostic_settings_category',
        exception_handler=exception_handler)

    diagnostics_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.diagnostics_settings#{}',
        client_factory=cf_diagnostics,
        operation_group='diagnostic_settings_category',
        exception_handler=exception_handler)

    log_profiles_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#LogProfilesOperations.{}',
        client_factory=cf_log_profiles,
        operation_group='log_profiles',
        exception_handler=exception_handler)

    log_profiles_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.log_profiles#{}',
        client_factory=cf_log_profiles,
        operation_group='log_profiles',
        exception_handler=exception_handler)

    subscription_dianostic_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#SubscriptionDiagnosticSettingsOperations.{}',
        client_factory=cf_subscription_diagnostics,
        operation_group='subscription_diagnostic_settings',
        exception_handler=exception_handler)

    subscription_dianostic_settings_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.subscription_diagnostic_settings#{}',
        client_factory=cf_subscription_diagnostics,
        operation_group='subscription_diagnostic_settings',
        exception_handler=exception_handler)

    alert_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.metric_alert#{}',
        client_factory=cf_alert_rules,
        operation_group='alert_rules',
        exception_handler=exception_handler)

    metric_alert_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#MetricAlertsOperations.{}',
        client_factory=cf_metric_alerts,
        operation_group='metric_alerts',
        exception_handler=exception_handler)

    metric_definitions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#MetricDefinitionsOperations.{}',
        client_factory=cf_metric_def,
        operation_group='metric_definitions',
        exception_handler=exception_handler)

    metric_namespaces_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#MetricNamespacesOperations.{}',
        client_factory=cf_metric_ns,
        operation_group='metric_namespaces',
        exception_handler=exception_handler
    )

    private_link_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#PrivateLinkResourcesOperations.{}',
        client_factory=cf_private_link_resources,
        operation_group='private_link_resources',
        exception_handler=exception_handler)

    private_link_scoped_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#PrivateLinkScopedResourcesOperations.{}',
        client_factory=cf_private_link_scoped_resources,
        operation_group='private_link_scoped_resources',
        exception_handler=exception_handler)

    private_link_scopes_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#PrivateLinkScopesOperations.{}',
        client_factory=cf_private_link_scopes,
        operation_group='private_link_scopes',
        exception_handler=exception_handler)

    private_endpoint_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=cf_private_endpoint_connections,
        operation_group='private_endpoint_connections',
        exception_handler=exception_handler)

    private_link_scope_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.private_link_scope#{}',
        client_factory=cf_private_link_scopes,
        exception_handler=exception_handler)

    log_analytics_workspace_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.log_analytics_workspace#{}',
        client_factory=cf_log_analytics_workspace,
        exception_handler=exception_handler)

    log_analytics_linked_storage_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.log_analytics_linked_storage_account#{}',
        client_factory=cf_log_analytics_linked_storage,
        exception_handler=exception_handler)

    monitor_general_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.general_operations#{}',
        client_factory=cf_metric_alerts,
        exception_handler=exception_handler)

    with self.command_group('monitor action-group', action_group_sdk, custom_command_type=action_group_custom) as g:
        g.show_command('show', 'get', table_transformer=action_group_list_table)
        g.command('create', 'create_or_update', table_transformer=action_group_list_table,
                  validator=process_action_group_detail_for_creation)
        g.command('delete', 'delete')
        g.custom_command('enable-receiver', 'enable_receiver', table_transformer=action_group_list_table)
        g.custom_command('list', 'list_action_groups', table_transformer=action_group_list_table)
        g.generic_update_command('update', custom_func_name='update_action_groups', setter_arg_name='action_group',
                                 table_transformer=action_group_list_table)
        g.custom_command('test-notifications create', 'post_notifications', table_transformer=action_group_list_table,
                         supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('monitor activity-log', activity_log_sdk) as g:
        g.custom_command('list', 'list_activity_log', client_factory=cf_activity_log)
        g.command('list-categories', 'list')

    with self.command_group('monitor activity-log alert', activity_log_alerts_sdk,
                            custom_command_type=activity_log_alerts_custom) as g:
        g.custom_command('list', 'list_activity_logs_alert')
        g.custom_command('create', 'create')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='update', setter_arg_name='activity_log_alert')
        g.custom_command('action-group add', 'add_action_group')
        g.custom_command('action-group remove', 'remove_action_group')
        g.custom_command('scope add', 'add_scope')
        g.custom_command('scope remove', 'remove_scope')

    with self.command_group('monitor autoscale', autoscale_sdk, custom_command_type=autoscale_custom) as g:
        g.custom_command('create', 'autoscale_create', validator=process_autoscale_create_namespace)
        g.generic_update_command('update', custom_func_name='autoscale_update', custom_func_type=autoscale_custom)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list_by_resource_group')

    with self.command_group('monitor autoscale profile', autoscale_sdk, custom_command_type=autoscale_custom) as g:
        g.custom_command('create', 'autoscale_profile_create')
        g.custom_command('list', 'autoscale_profile_list')
        g.custom_show_command('show', 'autoscale_profile_show')
        g.custom_command('delete', 'autoscale_profile_delete')
        g.custom_command('list-timezones', 'autoscale_profile_list_timezones')

    with self.command_group('monitor autoscale rule', autoscale_sdk, custom_command_type=autoscale_custom) as g:
        g.custom_command('create', 'autoscale_rule_create')
        g.custom_command('list', 'autoscale_rule_list')
        g.custom_command('delete', 'autoscale_rule_delete')
        g.custom_command('copy', 'autoscale_rule_copy')

    with self.command_group('monitor diagnostic-settings', diagnostics_sdk,
                            custom_command_type=diagnostics_custom) as g:
        from .validators import validate_diagnostic_settings
        g.custom_command('create', 'create_diagnostics_settings', validator=validate_diagnostic_settings)
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.generic_update_command('update')

    with self.command_group('monitor diagnostic-settings categories', diagnostics_categories_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('monitor log-profiles', log_profiles_sdk, custom_command_type=log_profiles_custom) as g:
        g.custom_command('create', 'create_log_profile_operations')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update')

    with self.command_group('monitor metrics') as g:
        from .transformers import metrics_table, metrics_definitions_table, metrics_namespaces_table
        g.command('list', 'list_metrics', command_type=monitor_custom, table_transformer=metrics_table)
        g.command('list-definitions', 'list', command_type=metric_definitions_sdk,
                  table_transformer=metrics_definitions_table)
        g.command('list-namespaces', 'list', is_preview=True, command_type=metric_namespaces_sdk,
                  table_transformer=metrics_namespaces_table)

    with self.command_group('monitor metrics alert', metric_alert_sdk, custom_command_type=alert_custom,
                            client_factory=cf_metric_alerts) as g:
        g.custom_command('create', 'create_metric_alert')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_metric_alerts', custom_command_type=alert_custom)
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='update_metric_alert', custom_func_type=alert_custom)

    with self.command_group('monitor metrics alert dimension', metric_alert_sdk, custom_command_type=alert_custom) as g:
        from .validators import validate_metrics_alert_dimension
        g.custom_command('create', 'create_metric_alert_dimension', custom_command_type=alert_custom,
                         validator=validate_metrics_alert_dimension, is_preview=True)

    with self.command_group('monitor metrics alert condition', metric_alert_sdk, custom_command_type=alert_custom) as g:
        from .validators import validate_metrics_alert_condition
        g.custom_command('create', 'create_metric_alert_condition', custom_command_type=alert_custom,
                         validator=validate_metrics_alert_condition, is_preview=True)

    with self.command_group('monitor log-analytics workspace', custom_command_type=log_analytics_workspace_custom) as g:
        g.custom_command('recover', 'recover_log_analytics_workspace', supports_no_wait=True)

    with self.command_group('monitor log-analytics workspace table', custom_command_type=log_analytics_workspace_custom,
                            is_preview=True) as g:
        g.custom_command('create', 'create_log_analytics_workspace_table', supports_no_wait=True)
        g.custom_command('update', 'update_log_analytics_workspace_table', supports_no_wait=True)

    with self.command_group('monitor log-analytics workspace table search-job',
                            custom_command_type=log_analytics_workspace_custom, is_preview=True) as g:
        g.custom_command('create', 'create_log_analytics_workspace_table_search_job', supports_no_wait=True)

    with self.command_group('monitor log-analytics workspace table restore',
                            custom_command_type=log_analytics_workspace_custom, is_preview=True) as g:
        g.custom_command('create', 'create_log_analytics_workspace_table_restore', supports_no_wait=True)

    from .operations.log_analytics_workspace import WorkspaceDataExportCreate, WorkspaceDataExportUpdate
    self.command_table['monitor log-analytics workspace data-export create'] = WorkspaceDataExportCreate(loader=self)
    self.command_table['monitor log-analytics workspace data-export update'] = WorkspaceDataExportUpdate(loader=self)

    with self.command_group('monitor log-analytics workspace saved-search',
                            custom_command_type=log_analytics_workspace_custom) as g:
        g.custom_command('create', 'create_log_analytics_workspace_saved_search')
        g.custom_command('update', 'update_log_analytics_workspace_saved_search')

    from .operations.log_analytics_linked_storage_account import WorkspaceLinkedStorageAccountCreate
    self.command_table['monitor log-analytics workspace linked-storage create'] = WorkspaceLinkedStorageAccountCreate(
        loader=self)
    with self.command_group('monitor log-analytics workspace linked-storage',
                            custom_command_type=log_analytics_linked_storage_custom) as g:
        g.custom_command('add', 'add_log_analytics_workspace_linked_storage_accounts')
        g.custom_command('remove', 'remove_log_analytics_workspace_linked_storage_accounts')

    with self.command_group('monitor', metric_alert_sdk, custom_command_type=monitor_general_custom) as g:
        g.custom_command('clone', 'clone_existed_settings', is_preview=True)

    with self.command_group('monitor private-link-scope', private_link_scopes_sdk,
                            custom_command_type=private_link_scope_custom, is_preview=True) as g:
        g.custom_show_command('show', 'show_private_link_scope')
        g.custom_command('list', 'list_private_link_scope')
        g.custom_command('create', 'create_private_link_scope')
        g.custom_command('update', 'update_private_link_scope')
        g.custom_command('delete', 'delete_private_link_scope', confirmation=True)

    with self.command_group('monitor private-link-scope scoped-resource', private_link_scoped_resources_sdk,
                            custom_command_type=private_link_scope_custom, is_preview=True) as g:
        g.custom_show_command('show', 'show_private_link_scope_resource',
                              client_factory=cf_private_link_scoped_resources)
        g.custom_command('list', 'list_private_link_scope_resource', client_factory=cf_private_link_scoped_resources)
        g.custom_command('create', 'create_private_link_scope_resource',
                         client_factory=cf_private_link_scoped_resources)
        g.custom_command('delete', 'delete_private_link_scope_resource',
                         client_factory=cf_private_link_scoped_resources, confirmation=True)

    with self.command_group('monitor private-link-scope private-link-resource', private_link_resources_sdk,
                            custom_command_type=private_link_scope_custom, is_preview=True) as g:
        g.custom_show_command('show', 'show_private_link_resource', client_factory=cf_private_link_resources)
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.custom_command('list', 'list_private_link_resource', client_factory=cf_private_link_resources,
                         transform=gen_dict_to_list_transform(key="value"))

    with self.command_group('monitor private-link-scope private-endpoint-connection', private_endpoint_connections_sdk,
                            custom_command_type=private_link_scope_custom, is_preview=True) as g:
        g.custom_show_command('show', 'show_private_endpoint_connection',
                              client_factory=cf_private_endpoint_connections,
                              validator=validate_private_endpoint_connection_id)
        g.custom_command('list', 'list_private_endpoint_connection', client_factory=cf_private_endpoint_connections)
        g.custom_command('approve', 'approve_private_endpoint_connection',
                         client_factory=cf_private_endpoint_connections,
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection', client_factory=cf_private_endpoint_connections,
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('delete', 'delete_private_endpoint_connection', client_factory=cf_private_endpoint_connections,
                         validator=validate_private_endpoint_connection_id, confirmation=True)

    with self.command_group('monitor diagnostic-settings subscription', subscription_dianostic_settings_sdk,
                            custom_command_type=subscription_dianostic_settings_custom) as g:
        g.custom_command('create', 'create_subscription_diagnostic_settings')
        g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', custom_func_name='update_subscription_diagnostic_settings')
