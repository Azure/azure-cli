# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from ._client_factory import \
    (cf_alert_rules, cf_metrics, cf_metric_def, cf_alert_rule_incidents, cf_log_profiles,
     cf_autoscale, cf_diagnostics, cf_activity_log)
from ._exception_handler import monitor_exception_handler


def monitor_command(*args, **kwargs):
    cli_command(*args, exception_handler=monitor_exception_handler, **kwargs)


# MANAGEMENT COMMANDS

custom_path = 'azure.cli.command_modules.monitor.custom#'

# region Alerts

ar_path = 'azure.mgmt.monitor.operations.alert_rules_operations#AlertRulesOperations.'

monitor_command(__name__, 'monitor alert create', custom_path + 'create_metric_rule', cf_alert_rules)
monitor_command(__name__, 'monitor alert delete', ar_path + 'delete', cf_alert_rules)
monitor_command(__name__, 'monitor alert show', ar_path + 'get', cf_alert_rules)
monitor_command(__name__, 'monitor alert list', ar_path + 'list_by_resource_group', cf_alert_rules)
cli_generic_update_command(__name__, 'monitor alert update',
                           ar_path + 'get', ar_path + 'create_or_update', cf_alert_rules,
                           custom_function_op=custom_path + 'update_metric_rule',
                           exception_handler=monitor_exception_handler)

ari_path = 'azure.mgmt.monitor.operations.alert_rule_incidents_operations#AlertRuleIncidentsOperations.'
monitor_command(__name__, 'monitor alert show-incident', ari_path + 'get', cf_alert_rule_incidents)
monitor_command(__name__, 'monitor alert list-incidents', ari_path + 'list_by_alert_rule', cf_alert_rule_incidents)

# endregion

# region Metrics

monitor_command(__name__, 'monitor metrics list', custom_path + 'list_metrics', cf_metrics)
monitor_command(__name__, 'monitor metrics list-definitions', custom_path + 'list_metric_definitions', cf_metric_def)

# endregion

# region Log Profiles

lp_path = 'azure.mgmt.monitor.operations.log_profiles_operations#LogProfilesOperations.'
monitor_command(__name__, 'monitor log-profiles create', lp_path + 'create_or_update', cf_log_profiles)
monitor_command(__name__, 'monitor log-profiles delete', lp_path + 'delete', cf_log_profiles)
monitor_command(__name__, 'monitor log-profiles show', lp_path + 'get', cf_log_profiles)
monitor_command(__name__, 'monitor log-profiles list', lp_path + 'list', cf_log_profiles)
cli_generic_update_command(__name__, 'monitor log-profiles update',
                           lp_path + 'get', lp_path + 'create_or_update', cf_log_profiles,
                           exception_handler=monitor_exception_handler)

# endregion

# region Diagnostic Settings

diag_path = 'azure.mgmt.monitor.operations.service_diagnostic_settings_operations#ServiceDiagnosticSettingsOperations.'
monitor_command(__name__, 'monitor diagnostic-settings create', custom_path + 'create_diagnostics_settings', cf_diagnostics)
monitor_command(__name__, 'monitor diagnostic-settings show', diag_path + 'get', cf_diagnostics)
cli_generic_update_command(__name__, 'monitor diagnostic-settings update',
                           diag_path + 'get', diag_path + 'create_or_update', cf_diagnostics,
                           exception_handler=monitor_exception_handler)

# endregion


# region Autoscale

autoscale_path = 'azure.mgmt.monitor.operations.autoscale_settings_operations#AutoscaleSettingsOperations.'

monitor_command(__name__, 'monitor autoscale-settings create', autoscale_path + 'create_or_update', cf_autoscale)
monitor_command(__name__, 'monitor autoscale-settings delete', autoscale_path + 'delete', cf_autoscale)
monitor_command(__name__, 'monitor autoscale-settings show', autoscale_path + 'get', cf_autoscale)
monitor_command(__name__, 'monitor autoscale-settings list', autoscale_path + 'list_by_resource_group', cf_autoscale)
monitor_command(__name__, 'monitor autoscale-settings get-parameters-template', custom_path + 'scaffold_autoscale_settings_parameters', cf_autoscale)
cli_generic_update_command(__name__, 'monitor autoscale-settings update',
                           autoscale_path + 'get', autoscale_path + 'create_or_update', cf_autoscale,
                           exception_handler=monitor_exception_handler)

# endregion

# region Activity Log

monitor_command(__name__, 'monitor activity-log list', custom_path + 'list_activity_log', cf_activity_log)

# endregion
