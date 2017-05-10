# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import (cf_monitor,
                              cf_alert_rules,
                              get_monitor_log_profiles_operation,
                              get_monitor_autoscale_settings_operation,
                              get_monitor_diagnostic_settings_operation,
                              get_monitor_activity_log_operation,
                              get_monitor_metric_definitions_operation,
                              get_monitor_metrics_operation)
from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.sdk.util import (ServiceGroup, create_service_adapter)


# MANAGEMENT COMMANDS

custom_path = 'azure.cli.command_modules.monitor.custom#'
custom_operations = create_service_adapter('azure.cli.command_modules.monitor.custom')

# region Alerts

ar_path = 'azure.mgmt.monitor.operations.alert_rules_operations#AlertRulesOperations.'

cli_command(__name__, 'monitor alert rule create', custom_path + 'create_metric_rule', cf_alert_rules)
cli_command(__name__, 'monitor alert rule create2', custom_path + 'create_metric_rule_alt', cf_alert_rules)
cli_command(__name__, 'monitor alert rule delete', ar_path + 'delete', cf_alert_rules)
cli_command(__name__, 'monitor alert rule show', ar_path + 'get', cf_alert_rules)
cli_command(__name__, 'monitor alert rule list', ar_path + 'list_by_resource_group', cf_alert_rules)
cli_generic_update_command(__name__, 'monitor alert rule update',
                           ar_path + 'get',
                           ar_path + 'create_or_update',
                           cf_alert_rules)

ari_path = 'azure.mgmt.monitor.operations.alert_rule_incidents_operations#AlertRuleIncidentsOperations.'
cli_command(__name__, 'monitor alert incident show', ari_path + 'get', cf_monitor)
cli_command(__name__, 'monitor alert incident list', ari_path + 'list_by_alert_rule', cf_monitor)

cli_command(__name__, 'monitor alert action add-email', custom_path + 'add_email_action', cf_monitor)
cli_command(__name__, 'monitor alert action add-webhook', custom_path + 'add_webhook_action', cf_monitor)

# endregion

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
