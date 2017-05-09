# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import (get_monitor_alert_rules_operation,
                              get_monitor_alert_rule_incidents_operation,
                              get_monitor_log_profiles_operation,
                              get_monitor_autoscale_settings_operation,
                              get_monitor_diagnostic_settings_operation,
                              get_monitor_activity_log_operation,
                              get_monitor_metric_definitions_operation,
                              get_monitor_metrics_operation)
from azure.cli.core.sdk.util import (ServiceGroup, create_service_adapter)


# MANAGEMENT COMMANDS
custom_operations = create_service_adapter('azure.cli.command_modules.monitor.custom')

alert_rules_operations = create_service_adapter(
    'azure.mgmt.monitor.operations.alert_rules_operations',
    'AlertRulesOperations')

with ServiceGroup(__name__, get_monitor_alert_rules_operation, alert_rules_operations) as s:
    with s.group('monitor alert-rules') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_resource_group')
        c.generic_update_command('update', 'get', 'create_or_update')

alert_rule_incidents_operations = create_service_adapter(
    'azure.mgmt.monitor.operations.alert_rule_incidents_operations',
    'AlertRuleIncidentsOperations')

with ServiceGroup(__name__, get_monitor_alert_rule_incidents_operation,
                  alert_rule_incidents_operations) as s:
    with s.group('monitor alert-rule-incidents') as c:
        c.command('show', 'get')
        c.command('list', 'list_by_alert_rule')

log_profiles_operations = create_service_adapter(
    'azure.mgmt.monitor.operations.log_profiles_operations',
    'LogProfilesOperations')

with ServiceGroup(__name__, get_monitor_log_profiles_operation,
                  log_profiles_operations) as s:
    with s.group('monitor log-profiles') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list')
        c.generic_update_command('update', 'get', 'create_or_update')

diagnostic_settings_operations = create_service_adapter(
    'azure.mgmt.monitor.operations.service_diagnostic_settings_operations',
    'ServiceDiagnosticSettingsOperations')

with ServiceGroup(__name__, get_monitor_diagnostic_settings_operation,
                  diagnostic_settings_operations) as s:
    with s.group('monitor diagnostic-settings') as c:
        c.command('show', 'get')
        c.generic_update_command('update', 'get', 'create_or_update')

with ServiceGroup(__name__, get_monitor_diagnostic_settings_operation, custom_operations) as s:
    with s.group('monitor diagnostic-settings') as c:
        c.command('create', 'create_diagnostics_settings')

autoscale_settings_operations = create_service_adapter(
    'azure.mgmt.monitor.operations.autoscale_settings_operations',
    'AutoscaleSettingsOperations')

with ServiceGroup(__name__, get_monitor_autoscale_settings_operation,
                  autoscale_settings_operations) as s:
    with s.group('monitor autoscale-settings') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_resource_group')
        c.generic_update_command('update', 'get', 'create_or_update')

with ServiceGroup(__name__, get_monitor_autoscale_settings_operation,
                  custom_operations) as s:
    with s.group('monitor autoscale-settings') as c:
        c.command('get-parameters-template', 'scaffold_autoscale_settings_parameters')


# DATA COMMANDS
with ServiceGroup(__name__, get_monitor_activity_log_operation,
                  custom_operations) as s:
    with s.group('monitor activity-log') as c:
        c.command('list', 'list_activity_log')

with ServiceGroup(__name__, get_monitor_metric_definitions_operation,
                  custom_operations) as s:
    with s.group('monitor metric-definitions') as c:
        c.command('list', 'list_metric_definitions')

with ServiceGroup(__name__, get_monitor_metrics_operation, custom_operations) as s:
    with s.group('monitor metrics') as c:
        c.command('list', 'list_metrics')
