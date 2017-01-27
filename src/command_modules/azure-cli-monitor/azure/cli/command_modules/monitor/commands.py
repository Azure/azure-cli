# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import (get_monitor_alert_rules_operation, get_monitor_alert_rule_incidents_operation,
                    get_monitor_log_profiles_operation, get_monitor_autoscale_settings_operation,
                    get_monitor_service_diagnostic_settings_operation,
                    get_monitor_usage_metrics_operation, get_monitor_event_categories_operation,
                    get_monitor_events_operation, get_monitor_tenant_events_operation,
                    get_monitor_metric_definitions_operation, get_monitor_metrics_operation,
                    ServiceGroup, create_service_adapter)

# MANAGEMENT COMMANDS
alert_rules_operations = create_service_adapter(
    'azure.cli.command_modules.monitor.sdk.operations.alert_rules_operations',
    'AlertRulesOperations')

with ServiceGroup(__name__, get_monitor_alert_rules_operation, alert_rules_operations) as s:
    with s.group('monitor alert-rules') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_resource_group')
        c.generic_update_command('update', 'get', 'create_or_update')

alert_rule_incidents_operations = create_service_adapter(
    'azure.cli.command_modules.monitor.sdk.operations.alert_rule_incidents_operations',
    'AlertRuleIncidentsOperations')

with ServiceGroup(__name__, get_monitor_alert_rule_incidents_operation,
                  alert_rule_incidents_operations) as s:
    with s.group('monitor alert-rule-incidents') as c:
        c.command('show', 'get')
        c.command('list', 'list_by_alert_rule')

log_profiles_operations = create_service_adapter(
    'azure.cli.command_modules.monitor.sdk.operations.log_profiles_operations',
    'LogProfilesOperations')

with ServiceGroup(__name__, get_monitor_log_profiles_operation,
                  log_profiles_operations) as s:
    with s.group('monitor log-profiles') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list')
        c.generic_update_command('update', 'get', 'create_or_update')

service_diagnostic_settings_operations = create_service_adapter(
    'azure.cli.command_modules.monitor.sdk.operations.service_diagnostic_settings_operations',
    'ServiceDiagnosticSettingsOperations')

with ServiceGroup(__name__, get_monitor_service_diagnostic_settings_operation,
                  service_diagnostic_settings_operations) as s:
    with s.group('monitor service-diagnostic-settings') as c:
        c.command('create', 'create_or_update')
        c.command('show', 'get')
        c.generic_update_command('update', 'get', 'create_or_update')

autoscale_settings_operations = create_service_adapter(
    'azure.cli.command_modules.monitor.sdk.operations.autoscale_settings_operations',
    'AutoscaleSettingsOperations')

with ServiceGroup(__name__, get_monitor_autoscale_settings_operation,
                  autoscale_settings_operations) as s:
    with s.group('monitor autoscale-settings') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_resource_group')
        c.generic_update_command('update', 'get', 'create_or_update')


# DATA COMMANDS
usage_metrics_operations = create_service_adapter(
    'azure.monitor.operations.usage_metrics_operations', 'UsageMetricsOperations')

with ServiceGroup(__name__, get_monitor_usage_metrics_operation, usage_metrics_operations) as s:
    with s.group('monitor usage-matrics') as c:
        c.command('list', 'list')

event_categories_operations = create_service_adapter(
    'azure.monitor.operations.event_categories_operations', 'EventCategoriesOperations')

with ServiceGroup(__name__, get_monitor_event_categories_operation,
                  event_categories_operations) as s:
    with s.group('monitor event-categories') as c:
        c.command('list', 'list')

events_operations = create_service_adapter(
    'azure.monitor.operations.events_operations', 'EventsOperations')

with ServiceGroup(__name__, get_monitor_events_operation, events_operations) as s:
    with s.group('monitor events') as c:
        c.command('list', 'list')

tenant_events_operations = create_service_adapter(
    'azure.monitor.operations.tenant_events_operations', 'TenantEventsOperations')

with ServiceGroup(__name__, get_monitor_tenant_events_operation,
                  tenant_events_operations) as s:
    with s.group('monitor tenant-events') as c:
        c.command('list', 'list')

metric_definitions_operations = create_service_adapter(
    'azure.monitor.operations.metric_definitions_operations', 'MetricDefinitionsOperations')

with ServiceGroup(__name__, get_monitor_metric_definitions_operation,
                  metric_definitions_operations) as s:
    with s.group('monitor metric-definitions') as c:
        c.command('list', 'list')

metrics_operations = create_service_adapter(
    'azure.monitor.operations.metrics_operations', 'MetricsOperations')

with ServiceGroup(__name__, get_monitor_metrics_operation, metrics_operations) as s:
    with s.group('monitor metrics') as c:
        c.command('list', 'list')
