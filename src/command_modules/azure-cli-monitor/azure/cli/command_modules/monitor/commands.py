# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.sdk.util import ServiceGroup, create_service_adapter
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from ._client_factory import (cf_alert_rules, cf_metrics, cf_metric_def, cf_alert_rule_incidents, cf_log_profiles,
                              cf_autoscale, cf_diagnostics, cf_activity_log, cf_action_groups, cf_activity_log_alerts,
                              cf_event_categories)
from ._exception_handler import monitor_exception_handler, missing_resource_handler

from .transformers import (action_group_list_table)

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
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

    action_group_operations = create_service_adapter(
        'azure.mgmt.monitor.operations.action_groups_operations', 'ActionGroupsOperations')
    ag_custom_path = '.'.join(__name__.split('.')[:-1] + ['action_groups']) + '#{}'

    with ServiceGroup(__name__, cf_action_groups, action_group_operations, ag_custom_path) as s:
        with s.group('monitor action-group') as c:
            c.command('show', 'get', table_transformer=action_group_list_table)
            c.command('create', 'create_or_update', table_transformer=action_group_list_table)
            c.command('delete', 'delete')
            c.command('enable-receiver', 'enable_receiver', table_transformer=action_group_list_table)
            c.custom_command('list', 'list_action_groups', table_transformer=action_group_list_table)
            c.generic_update_command('update', 'get', 'create_or_update', 'update_action_groups',
                                     setter_arg_name='action_group',
                                     table_transformer=action_group_list_table,
                                     exception_handler=monitor_exception_handler)

    activity_log_alerts_operations = create_service_adapter(
        'azure.mgmt.monitor.operations.activity_log_alerts_operations', 'ActivityLogAlertsOperations')
    ala_custom_path = '.'.join(__name__.split('.')[:-1] + ['activity_log_alerts']) + '#{}'

    with ServiceGroup(__name__, cf_activity_log_alerts, activity_log_alerts_operations, ala_custom_path) as s:
        with s.group('monitor activity-log alert') as c:
            c.custom_command('list', 'list_activity_logs_alert')
            c.custom_command('create', 'create', exception_handler=monitor_exception_handler)
            c.command('show', 'get', exception_handler=missing_resource_handler)
            c.command('delete', 'delete', exception_handler=missing_resource_handler)
            c.generic_update_command('update', 'get', 'create_or_update', 'update',
                                     setter_arg_name='activity_log_alert',
                                     exception_handler=monitor_exception_handler)
            c.custom_command('action-group add', 'add_action_group', exception_handler=monitor_exception_handler)
            c.custom_command('action-group remove', 'remove_action_group', exception_handler=monitor_exception_handler)
            c.custom_command('scope add', 'add_scope', exception_handler=monitor_exception_handler)
            c.custom_command('scope remove', 'remove_scope', exception_handler=monitor_exception_handler)

    with ServiceGroup(__name__, cf_event_categories,
                      create_service_adapter('azure.monitor.operations.event_categories_operations',
                                             'EventCategoriesOperations'),
                      ala_custom_path) as s:
        with s.group('monitor activity-log') as c:
            c.command('list-categories', 'list')
