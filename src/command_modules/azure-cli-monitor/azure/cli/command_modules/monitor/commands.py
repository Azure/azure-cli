# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    from azure.cli.core.sdk.util import ServiceGroup, create_service_adapter
    from ._client_factory import (cf_alert_rules, cf_metrics, cf_metric_def, cf_alert_rule_incidents, cf_log_profiles,
                                  cf_autoscale, cf_diagnostics, cf_activity_log, cf_action_groups,
                                  cf_activity_log_alerts, cf_event_categories)
    from ._exception_handler import monitor_exception_handler, missing_resource_handler

    from .transformers import (action_group_list_table)

    def service_adapter(module_name, class_name):
        return create_service_adapter('azure.mgmt.monitor.operations.{}'.format(module_name), class_name)

    def custom_path(module_name):
        return '.'.join(__name__.split('.')[:-1]) + '.operations.{}#'.format(module_name) + '{}'

    with ServiceGroup(__name__, cf_action_groups, service_adapter('action_groups_operations', 'ActionGroupsOperations'),
                      custom_path('action_groups')) as s:
        with s.group('monitor action-group') as c:
            c.command('show', 'get', table_transformer=action_group_list_table)
            c.command('create', 'create_or_update', table_transformer=action_group_list_table)
            c.command('delete', 'delete')
            c.command('enable-receiver', 'enable_receiver', table_transformer=action_group_list_table,
                      exception_handler=monitor_exception_handler)
            c.custom_command('list', 'list_action_groups', table_transformer=action_group_list_table)
            c.generic_update_command('update', 'get', 'create_or_update', 'update_action_groups',
                                     setter_arg_name='action_group', table_transformer=action_group_list_table,
                                     exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_activity_log, custom_path=custom_path('activity_log')) as s:
        with s.group('monitor activity-log') as c:
            c.custom_command('list', 'list_activity_log')

    with ServiceGroup(__name__, cf_activity_log_alerts,
                      service_adapter('activity_log_alerts_operations', 'ActivityLogAlertsOperations'),
                      custom_path('activity_log_alerts')) as s:
        with s.group('monitor activity-log alert') as c:
            c.custom_command('list', 'list_activity_logs_alert')
            c.custom_command('create', 'create', exception_handler=monitor_exception_handler)
            c.command('show', 'get', exception_handler=missing_resource_handler)
            c.command('delete', 'delete', exception_handler=missing_resource_handler)
            c.generic_update_command('update', 'get', 'create_or_update', 'update',
                                     setter_arg_name='activity_log_alert', exception_handler=monitor_exception_handler)
            c.custom_command('action-group add', 'add_action_group', exception_handler=monitor_exception_handler)
            c.custom_command('action-group remove', 'remove_action_group', exception_handler=monitor_exception_handler)
            c.custom_command('scope add', 'add_scope', exception_handler=monitor_exception_handler)
            c.custom_command('scope remove', 'remove_scope', exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_event_categories,
                      service_adapter('event_categories_operations', 'EventCategoriesOperations'),
                      custom_path('activity_log_alerts')) as s:
        with s.group('monitor activity-log') as c:
            c.command('list-categories', 'list')

    with ServiceGroup(__name__, cf_alert_rules, service_adapter('alert_rules_operations', 'AlertRulesOperations'),
                      custom_path('metric_alert')) as s:
        with s.group('monitor alert') as c:
            c.custom_command('create', 'create_metric_rule')
            c.command('delete', 'delete')
            c.command('show', 'get')
            c.command('list', 'list_by_resource_group')
            c.generic_update_command('update', 'get', 'create_or_update', 'update_metric_rule',
                                     exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_alert_rule_incidents,
                      service_adapter('alert_rule_incidents_operations', 'AlertRuleIncidentsOperations'),
                      custom_path('metric_alert')) as s:
        with s.group('monitor alert') as c:
            c.command('show-incident', 'get')
            c.command('list-incidents', 'list_by_alert_rule')

    with ServiceGroup(__name__, cf_autoscale,
                      service_adapter('autoscale_settings_operations', 'AutoscaleSettingsOperations'),
                      custom_path('autoscale_settings')) as s:
        with s.group('monitor autoscale-settings') as c:
            c.command('create', 'create_or_update')
            c.command('delete', 'delete')
            c.command('show', 'get')
            c.command('list', 'list_by_resource_group')
            c.custom_command('get-parameters-template', 'scaffold_autoscale_settings_parameters')
            c.generic_update_command('update', 'get', 'create_or_update', exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_diagnostics,
                      service_adapter('diagnostic_settings_operations', 'DiagnosticSettingsOperations'),
                      custom_path('diagnostics_settings')) as s:
        with s.group('monitor diagnostic-settings') as c:
            c.custom_command('create', 'create_diagnostics_settings')
            c.command('show', 'get')
            c.generic_update_command('update', 'get', 'create_or_update', exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_log_profiles,
                      service_adapter('log_profiles_operations', 'LogProfilesOperations')) as s:
        with s.group('monitor log-profiles') as c:
            c.command('create', 'create_or_update')
            c.command('delete', 'delete')
            c.command('show', 'get')
            c.command('list', 'list')
            c.generic_update_command('update', 'get', 'create_or_update', exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_metrics, service_adapter('metrics_operations', 'MetricsOperations')) as s:
        from .transformers import metrics_table

        with s.group('monitor metrics') as c:
            c.command('list', 'list', table_transformer=metrics_table)

    with ServiceGroup(__name__, cf_metric_def,
                      service_adapter('metric_definitions_operations', 'MetricDefinitionsOperations')) as s:
        from .transformers import metrics_definitions_table

        with s.group('monitor metrics') as c:
            c.command('list-definitions', 'list', table_transformer=metrics_definitions_table)
