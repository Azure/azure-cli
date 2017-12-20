# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):  # pylint: disable=too-many-statements
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import (cf_action_groups, cf_activity_log, cf_activity_log_alerts, cf_event_categories,
                                  cf_alert_rules, cf_alert_rule_incidents, cf_autoscale, cf_diagnostics,
                                  cf_log_profiles, cf_metrics, cf_metric_def)
    from ._exception_handler import monitor_exception_handler, missing_resource_handler
    from .transformers import action_group_list_table

    if self.supported_api_version(max_api='2017-03-09-profile'):
        # skip loading monitor commands for older profile
        return self.command_table

    with self.monitor_command_group('monitor action-group', cf_action_groups, 'action_groups_operations',
                                    'ActionGroupsOperations', table_transformer=action_group_list_table) as g:
        g.command('show', 'get')
        g.command('create', 'create_or_update')
        g.command('delete', 'delete')
        g.command('enable-receiver', 'enable_receiver', exception_handler=monitor_exception_handler)
        g.command('list', 'list_action_groups', operations_tmpl=self._get_custom_module_path('action_groups'))
        g.generic_update_command(
            'update', custom_func_name='update_action_groups',
            custom_func_type=CliCommandType(operations_tmpl=self._get_custom_module_path('action_groups')),
            setter_arg_name='action_group',
            exception_handler=monitor_exception_handler)

    with self.monitor_command_group('monitor activity-log', cf_activity_log, custom_module='activity_log') as g:
        g.custom_command('list', 'list_activity_log')

    with self.monitor_command_group('monitor activity-log', cf_event_categories, 'event_categories_operations',
                                    'EventCategoriesOperations') as g:
        g.command('list-categories', 'list')

    with self.monitor_command_group('monitor activity-log alert', cf_activity_log_alerts,
                                    'activity_log_alerts_operations', 'ActivityLogAlertsOperations',
                                    custom_module='activity_log_alerts') as g:
        g.custom_command('list', 'list_activity_logs_alert')
        g.custom_command('create', 'create', exception_handler=monitor_exception_handler)
        g.command('show', 'get', exception_handler=missing_resource_handler)
        g.command('delete', 'delete', exception_handler=missing_resource_handler)
        g.custom_command('action-group add', 'add_action_group', exception_handler=monitor_exception_handler)
        g.custom_command('action-group remove', 'remove_action_group', exception_handler=monitor_exception_handler)
        g.custom_command('scope add', 'add_scope', exception_handler=monitor_exception_handler)
        g.custom_command('scope remove', 'remove_scope', exception_handler=monitor_exception_handler)
        g.generic_update_command('update', custom_func_name='update', setter_arg_name='activity_log_alert',
                                 exception_handler=monitor_exception_handler)

    with self.monitor_command_group('monitor alert', cf_alert_rules, 'alert_rules_operations',
                                    'AlertRulesOperations', custom_module='metric_alert') as g:
        g.custom_command('create', 'create_metric_rule')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list_by_resource_group')
        g.generic_update_command('update', custom_func_name='update_metric_rule',
                                 exception_handler=monitor_exception_handler)

    with self.monitor_command_group('monitor alert', cf_alert_rule_incidents, 'alert_rule_incidents_operations',
                                    'AlertRuleIncidentsOperations', custom_module='metric_alert') as g:
        g.command('show-incident', 'get')
        g.command('list-incidents', 'list_by_alert_rule')

    with self.monitor_command_group('monitor autoscale-settings', cf_autoscale, 'autoscale_settings_operations',
                                    'AutoscaleSettingsOperations', custom_module='autoscale_settings') as g:
        g.command('create', 'create_or_update')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list_by_resource_group')
        g.custom_command('get-parameters-template', 'scaffold_autoscale_settings_parameters')
        g.generic_update_command('update', exception_handler=monitor_exception_handler)

    with self.monitor_command_group('monitor diagnostic-settings', cf_diagnostics, 'diagnostic_settings_operations',
                                    'DiagnosticSettingsOperations', custom_module='diagnostics_settings') as g:
        g.custom_command('create', 'create_diagnostics_settings')
        g.command('show', 'get')
        g.generic_update_command('update', exception_handler=monitor_exception_handler)

    with self.monitor_command_group('monitor log-profiles', cf_log_profiles, 'log_profiles_operations',
                                    'LogProfilesOperations') as g:
        g.command('create', 'create_or_update')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', exception_handler=monitor_exception_handler)

    with self.command_group('monitor metrics') as g:
        from .transformers import metrics_table, metrics_definitions_table

        g.command('list', 'list', client_factory=cf_metrics,
                  operations_tmpl=self._get_sdk_path('metrics_operations', 'MetricsOperations'),
                  table_transformer=metrics_table)

        g.command('list-definitions', 'list', client_factory=cf_metric_def,
                  operations_tmpl=self._get_sdk_path('metric_definitions_operations',
                                                     'MetricDefinitionsOperations'),
                  table_transformer=metrics_definitions_table)

    return self.command_table
