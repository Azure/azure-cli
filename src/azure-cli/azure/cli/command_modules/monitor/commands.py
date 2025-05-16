# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import CliCommandType


# pylint: disable=line-too-long, too-many-locals, too-many-statements
def load_command_table(self, _):
    from ._client_factory import (
        cf_autoscale,
        cf_action_groups, cf_event_categories,
        cf_metric_alerts, cf_log_analytics_workspace, cf_log_analytics_linked_storage)
    from .transformers import (action_group_list_table)
    from .validators import (process_autoscale_create_namespace)

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

    alert_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.operations.metric_alert#{}',
        exception_handler=exception_handler)

    metric_alert_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#MetricAlertsOperations.{}',
        client_factory=cf_metric_alerts,
        operation_group='metric_alerts',
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
        g.wait_command('wait')

    from .operations.action_groups import ActionGroupCreate, ActionGroupUpdate, ActionGroupTestNotificationCreate
    from .aaz.latest.monitor.action_group import Show, List, EnableReceiver
    self.command_table['monitor action-group create'] = ActionGroupCreate(loader=self,
                                                                          table_transformer=action_group_list_table)
    self.command_table['monitor action-group show'] = Show(loader=self,
                                                           table_transformer=action_group_list_table)
    self.command_table['monitor action-group list'] = List(loader=self,
                                                           table_transformer=action_group_list_table)
    self.command_table['monitor action-group update'] = ActionGroupUpdate(loader=self,
                                                                          table_transformer=action_group_list_table)
    self.command_table['monitor action-group enable-receiver'] = \
        EnableReceiver(loader=self, table_transformer=action_group_list_table)

    self.command_table['monitor action-group test-notifications create'] = \
        ActionGroupTestNotificationCreate(loader=self, table_transformer=action_group_list_table)

    from .operations.action_groups_identity import AGIdentityAssign, AGIdentityRemove, AGIdentityShow
    self.command_table['monitor action-group identity assign'] = AGIdentityAssign(loader=self)
    self.command_table['monitor action-group identity remove'] = AGIdentityRemove(loader=self)
    self.command_table['monitor action-group identity show'] = AGIdentityShow(loader=self)

    with self.command_group('monitor activity-log', activity_log_sdk) as g:
        g.custom_command('list', 'list_activity_log')

    from .operations.activity_log_alerts import ActivityLogAlertCreate, ActivityLogAlertUpdate, \
        ActivityLogAlertActionGroupAdd, ActivityLogAlertActionGroupRemove, \
        ActivityLogAlertScopeAdd, ActivityLogAlertScopeRemove
    self.command_table['monitor activity-log alert create'] = ActivityLogAlertCreate(loader=self)
    self.command_table['monitor activity-log alert update'] = ActivityLogAlertUpdate(loader=self)
    self.command_table['monitor activity-log alert action-group add'] = ActivityLogAlertActionGroupAdd(loader=self)
    self.command_table['monitor activity-log alert action-group remove'] = \
        ActivityLogAlertActionGroupRemove(loader=self)
    self.command_table['monitor activity-log alert scope add'] = ActivityLogAlertScopeAdd(loader=self)
    self.command_table['monitor activity-log alert scope remove'] = ActivityLogAlertScopeRemove(loader=self)

    with self.command_group('monitor autoscale', autoscale_sdk, custom_command_type=autoscale_custom) as g:
        g.custom_command('create', 'autoscale_create', validator=process_autoscale_create_namespace)
        # g.generic_update_command('update', custom_func_name='autoscale_update', custom_func_type=autoscale_custom)
        from .operations.autoscale_settings import AutoScaleShow, AutoScaleList, AutoScaleUpdate
        self.command_table['monitor autoscale show'] = AutoScaleShow(loader=self)
        self.command_table['monitor autoscale list'] = AutoScaleList(loader=self)
        self.command_table['monitor autoscale update'] = AutoScaleUpdate(loader=self)

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

    from .operations.diagnostics_settings import DiagnosticSettingsCreate, DiagnosticSettingsShow, \
        DiagnosticSettingsList, DiagnosticSettingsDelete, DiagnosticSettingsUpdate
    self.command_table['monitor diagnostic-settings create'] = DiagnosticSettingsCreate(loader=self)
    self.command_table['monitor diagnostic-settings show'] = DiagnosticSettingsShow(loader=self)
    self.command_table['monitor diagnostic-settings list'] = DiagnosticSettingsList(loader=self)
    self.command_table['monitor diagnostic-settings delete'] = DiagnosticSettingsDelete(loader=self)
    self.command_table['monitor diagnostic-settings update'] = DiagnosticSettingsUpdate(loader=self)

    from .operations.diagnostics_settings import DiagnosticSettingsCategoryShow, DiagnosticSettingsCategoryList
    self.command_table['monitor diagnostic-settings categories show'] = DiagnosticSettingsCategoryShow(loader=self)
    self.command_table['monitor diagnostic-settings categories list'] = DiagnosticSettingsCategoryList(loader=self)

    with self.command_group('monitor metrics') as g:
        from .transformers import metrics_table, metrics_definitions_table, metrics_namespaces_table
        g.command('list', 'list_metrics', command_type=monitor_custom, table_transformer=metrics_table)
        g.custom_command('list-definitions', 'list_definations', command_type=monitor_custom, table_transformer=metrics_definitions_table)
        g.command('list-namespaces', 'list_namespaces', is_preview=True, command_type=monitor_custom, table_transformer=metrics_namespaces_table)

    with self.command_group("monitor metrics alert") as g:
        from .operations.metric_alert import MetricsAlertUpdate
        self.command_table["monitor metrics alert update"] = MetricsAlertUpdate(loader=self)
        g.custom_command("create", "create_metric_alert", custom_command_type=alert_custom)

    with self.command_group('monitor metrics alert dimension') as g:
        from .validators import validate_metrics_alert_dimension
        g.custom_command('create', 'create_metric_alert_dimension', custom_command_type=alert_custom,
                         validator=validate_metrics_alert_dimension, is_preview=True)

    with self.command_group('monitor metrics alert condition') as g:
        from .validators import validate_metrics_alert_condition
        g.custom_command('create', 'create_metric_alert_condition', custom_command_type=alert_custom,
                         validator=validate_metrics_alert_condition, is_preview=True)

    with self.command_group('monitor log-analytics workspace', custom_command_type=log_analytics_workspace_custom) as g:
        g.custom_command('recover', 'recover_log_analytics_workspace', supports_no_wait=True)

    with self.command_group('monitor log-analytics workspace table', custom_command_type=log_analytics_workspace_custom) as g:
        g.custom_command('create', 'create_log_analytics_workspace_table', supports_no_wait=True)
        g.custom_command('update', 'update_log_analytics_workspace_table', supports_no_wait=True)

    with self.command_group('monitor log-analytics workspace table search-job',
                            custom_command_type=log_analytics_workspace_custom) as g:
        g.custom_command('create', 'create_log_analytics_workspace_table_search_job', supports_no_wait=True)
        from .operations.log_analytics_workspace import WorkspaceTableSearchJobCancel
        self.command_table['monitor log-analytics workspace table search-job cancel'] = \
            WorkspaceTableSearchJobCancel(loader=self)

    with self.command_group('monitor log-analytics workspace table restore',
                            custom_command_type=log_analytics_workspace_custom) as g:
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

    from .operations.private_link_scope import PrivateLinkScopeCreate, ConnectionDelete, ConnectionShow, ConnectionApprove, ConnectionReject
    self.command_table["monitor private-link-scope create"] = PrivateLinkScopeCreate(loader=self)
    self.command_table["monitor private-link-scope private-endpoint-connection delete"] = ConnectionDelete(loader=self)
    self.command_table["monitor private-link-scope private-endpoint-connection show"] = ConnectionShow(loader=self)
    self.command_table["monitor private-link-scope private-endpoint-connection approve"] = ConnectionApprove(loader=self)
    self.command_table["monitor private-link-scope private-endpoint-connection reject"] = ConnectionReject(loader=self)
