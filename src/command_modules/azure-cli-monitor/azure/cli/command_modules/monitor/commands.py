# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import (cf_monitor,
                              cf_alert_rules, cf_metrics, cf_metric_def,
                              cf_alert_rule_incidents,
                              get_monitor_log_profiles_operation,
                              get_monitor_autoscale_settings_operation,
                              get_monitor_diagnostic_settings_operation,
                              get_monitor_activity_log_operation)
from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.sdk.util import (ServiceGroup, create_service_adapter)


# MANAGEMENT COMMANDS

custom_path = 'azure.cli.command_modules.monitor.custom#'
custom_operations = create_service_adapter('azure.cli.command_modules.monitor.custom')

# region Alerts

ar_path = 'azure.mgmt.monitor.operations.alert_rules_operations#AlertRulesOperations.'

cli_command(__name__, 'monitor alert create', custom_path + 'create_metric_rule', cf_alert_rules)
cli_command(__name__, 'monitor alert delete', ar_path + 'delete', cf_alert_rules)
cli_command(__name__, 'monitor alert show', ar_path + 'get', cf_alert_rules)
cli_command(__name__, 'monitor alert list', ar_path + 'list_by_resource_group', cf_alert_rules)
cli_generic_update_command(__name__, 'monitor alert update',
                           ar_path + 'get',
                           ar_path + 'create_or_update',
                           cf_alert_rules,
                           custom_function_op=custom_path + 'update_metric_rule')

ari_path = 'azure.mgmt.monitor.operations.alert_rule_incidents_operations#AlertRuleIncidentsOperations.'
cli_command(__name__, 'monitor alert show-incident', ari_path + 'get', cf_alert_rule_incidents)
cli_command(__name__, 'monitor alert list-incidents', ari_path + 'list_by_alert_rule', cf_alert_rule_incidents)

# endregion

# region Metrics

cli_command(__name__, 'monitor metrics list', custom_path + 'list_metrics', cf_metrics)
cli_command(__name__, 'monitor metrics list-definitions', custom_path + 'list_metric_definitions', cf_metric_def)

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


with ServiceGroup(__name__, get_monitor_activity_log_operation,
                  custom_operations) as s:
    with s.group('monitor activity-log') as c:
        c.command('list', 'list_activity_log')
