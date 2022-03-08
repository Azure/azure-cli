# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import get_json_object

from azure.cli.core.commands.parameters import (
    get_location_type, tags_type, get_three_state_flag, get_enum_type, get_datetime_type, resource_group_name_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from azure.cli.command_modules.monitor.actions import (
    AlertAddAction, AlertRemoveAction, ConditionAction, AutoscaleAddAction, AutoscaleRemoveAction,
    AutoscaleScaleAction, AutoscaleConditionAction, get_period_type,
    timezone_offset_type, timezone_name_type, MetricAlertConditionAction, MetricAlertAddAction)
from azure.cli.command_modules.monitor.util import get_operator_map, get_aggregation_map
from azure.cli.command_modules.monitor.validators import (
    process_webhook_prop, validate_autoscale_recurrence, validate_autoscale_timegrain, get_action_group_validator,
    get_action_group_id_validator, validate_metric_dimension, validate_storage_accounts_name_or_id,
    process_subscription_id, process_workspace_data_export_destination)

from knack.arguments import CLIArgumentType


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):
    from azure.mgmt.monitor.models import ConditionOperator, TimeAggregationOperator, EventData
    from .grammar.metric_alert.MetricAlertConditionValidator import dim_op_conversion, agg_conversion, op_conversion, sens_conversion
    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    webhook_prop_type = CLIArgumentType(validator=process_webhook_prop, nargs='*')

    autoscale_name_type = CLIArgumentType(options_list=['--autoscale-name'], help='Name of the autoscale settings.', id_part='name')
    autoscale_profile_name_type = CLIArgumentType(options_list=['--profile-name'], help='Name of the autoscale profile.')
    autoscale_rule_name_type = CLIArgumentType(options_list=['--rule-name'], help='Name of the autoscale rule.')
    scope_name_type = CLIArgumentType(help='Name of the Azure Monitor Private Link Scope.')

    with self.argument_context('monitor') as c:
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)

    # region Alerts
    with self.argument_context('monitor alert') as c:
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')

    with self.argument_context('monitor alert create') as c:
        c.resource_parameter('target', arg_group='Target Resource', alias='target', preserve_resource_group_parameter=True)
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')
        c.argument('disabled', arg_type=get_three_state_flag())
        c.argument('condition', action=ConditionAction, nargs='+')

    with self.argument_context('monitor alert create', arg_group='Action') as c:
        c.argument('custom_emails', nargs='+')
        c.argument('email_service_owners', arg_type=get_three_state_flag())
        c.argument('actions', options_list=['--action', '-a'], action=AlertAddAction, nargs='+')

    with self.argument_context('monitor alert create', arg_group='Condition') as c:
        c.argument('metric_name')
        c.argument('operator', arg_type=get_enum_type(ConditionOperator))
        c.argument('threshold')
        c.argument('time_aggregation', arg_type=get_enum_type(TimeAggregationOperator))
        c.argument('window_size')

    with self.argument_context('monitor alert update') as c:
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')
        c.resource_parameter('target', arg_group='Target Resource', required=False, preserve_resource_group_parameter=True)

    with self.argument_context('monitor alert update', arg_group='Action') as c:
        c.argument('email_service_owners', arg_type=get_three_state_flag())
        c.argument('add_actions', options_list=['--add-action', '-a'], nargs='+', action=AlertAddAction)
        c.argument('remove_actions', options_list=['--remove-action', '-r'], nargs='+', action=AlertRemoveAction)

    with self.argument_context('monitor alert update', arg_group='Condition') as c:
        c.argument('condition', action=ConditionAction, nargs='+')
        c.argument('metric')
        c.argument('operator', arg_type=get_enum_type(get_operator_map().keys()))
        c.argument('threshold')
        c.argument('aggregation', arg_type=get_enum_type(get_aggregation_map().keys()))
        c.argument('period', type=get_period_type())

    for scope in ['monitor alert show-incident', 'monitor alert list-incidents']:
        with self.argument_context(scope) as c:
            c.argument('rule_name', options_list=['--rule-name'], id_part='name')
            c.argument('incident_name', name_arg_type, id_part='child_name_1')

    with self.argument_context('monitor alert list-incidents') as c:
        c.argument('rule_name', options_list=['--rule-name'], id_part=None)
    # endregion

    # region Metrics
    with self.argument_context('monitor metrics') as c:
        c.argument('metricnamespace', options_list=['--namespace'], help='Namespace to query metric definitions for.')

    with self.argument_context('monitor metrics list-definitions') as c:
        c.resource_parameter('resource_uri', arg_group='Target Resource')

    with self.argument_context('monitor metrics list') as c:
        from azure.mgmt.monitor.models import AggregationType
        c.resource_parameter('resource', arg_group='Target Resource')
        c.argument('metadata', action='store_true')
        c.argument('dimension', nargs='*', validator=validate_metric_dimension)
        c.argument('aggregation', arg_type=get_enum_type(t for t in AggregationType if t.name != 'none'), nargs='*')
        c.argument('metrics', nargs='+')
        c.argument('orderby', help='Aggregation to use for sorting results and the direction of the sort. Only one order can be specificed. Examples: sum asc')
        c.argument('top', help='Max number of records to retrieve. Valid only if --filter used.')
        c.argument('filters', options_list='--filter')
        c.argument('metric_namespace', options_list='--namespace')

    with self.argument_context('monitor metrics list', arg_group='Time') as c:
        c.argument('start_time', arg_type=get_datetime_type(help='Start time of the query.'))
        c.argument('end_time', arg_type=get_datetime_type(help='End time of the query. Defaults to the current time.'))
        c.argument('offset', type=get_period_type(as_timedelta=True))
        c.argument('interval', arg_group='Time', type=get_period_type())

    with self.argument_context('monitor metrics list-namespaces', arg_group='Time') as c:
        c.argument('start_time', arg_type=get_datetime_type(help='Start time of the query.'))
    # endregion

    # region MetricAlerts
    with self.argument_context('monitor metrics alert') as c:
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')
        c.argument('severity', type=int, help='Severity of the alert from 0 (critical) to 4 (verbose).')
        c.argument('window_size', type=get_period_type(), help='Time over which to aggregate metrics in "##h##m##s" format.')
        c.argument('evaluation_frequency', type=get_period_type(), help='Frequency with which to evaluate the rule in "##h##m##s" format.')
        c.argument('auto_mitigate', arg_type=get_three_state_flag(), help='Automatically resolve the alert.')
        c.argument('condition', options_list=['--condition'], action=MetricAlertConditionAction, nargs='+')
        c.argument('description', help='Free-text description of the rule.')
        c.argument('scopes', nargs='+', help='Space-separated list of scopes the rule applies to. '
                                             'The resources specified in this parameter must be of the same type and exist in the same location.')
        c.argument('disabled', arg_type=get_three_state_flag())
        c.argument('enabled', arg_type=get_three_state_flag(), help='Whether the metric alert rule is enabled.')
        c.argument('target_resource_type', options_list=['--target-resource-type', '--type'],
                   help='The resource type of the target resource(s) in scopes. '
                        'This must be provided when scopes is resource group or subscription.')
        c.argument('target_resource_region', options_list=['--target-resource-region', '--region'],
                   help='The region of the target resource(s) in scopes. '
                        'This must be provided when scopes is resource group or subscription.')

    with self.argument_context('monitor metrics alert create', arg_group=None) as c:
        c.argument('actions', options_list=['--action', '-a'], action=MetricAlertAddAction, nargs='+', validator=get_action_group_validator('actions'))

    with self.argument_context('monitor metrics alert update', arg_group='Action') as c:
        c.argument('add_actions', options_list='--add-action', action=MetricAlertAddAction, nargs='+', validator=get_action_group_validator('add_actions'))
        c.argument('remove_actions', nargs='+', validator=get_action_group_id_validator('remove_actions'))

    with self.argument_context('monitor metrics alert update', arg_group='Condition') as c:
        c.argument('add_conditions', options_list='--add-condition', action=MetricAlertConditionAction, nargs='+')
        c.argument('remove_conditions', nargs='+')

    with self.argument_context('monitor metrics alert dimension create', arg_group=None) as c:
        c.argument('dimension_name', options_list=['--name', '-n'],
                   help='Name of the dimension.')
        c.argument('operator', options_list=['--operator', '--op'],
                   arg_type=get_enum_type(dim_op_conversion.values(), default=dim_op_conversion['includes']),
                   help="Dimension operator.")
        c.argument('value_list', options_list=['--value', '-v'], nargs='+',
                   help='The values to apply on the operation.')

    with self.argument_context('monitor metrics alert condition create', arg_group=None) as c:
        c.argument('condition_type', options_list=['--type', '-t'], arg_type=get_enum_type(['static', 'dynamic']),
                   help='Type of condition threshold.')
        c.argument('metric_name', options_list=['--metric'],
                   help='Name of metric.')
        c.argument('metric_namespace', options_list=['--namespace'],
                   help='Namespace of metric.')
        c.argument('dimension_list', options_list=['--dimension'], nargs='+',
                   help='Dimension created by \'az monitor metrics alert dimension create\'.')
        c.argument('aggregation', arg_type=get_enum_type(agg_conversion.values()),
                   help='Time aggregation.')
        c.argument('operator', options_list=['--operator', '--op'], arg_type=get_enum_type(op_conversion.values()),
                   help="Operator for static threshold can be 'Equals', 'NotEquals', 'GreaterThan', 'GreaterThanOrEqual', 'LessThan' or 'LessThanOrEqual'. "
                   "Operator for dynamic threshold can be 'GreaterThan', 'LessThan', 'GreaterOrLessThan'.")
        c.argument('threshold', type=float,
                   help='Static threshold value.')
        c.argument('alert_sensitivity', options_list=['--sensitivity'],
                   arg_type=get_enum_type(sens_conversion.values(), default='Medium'),
                   help="Alert sensitivity for dynamic threshold.")
        c.argument('number_of_evaluation_periods', options_list=['--num-periods'], type=int,
                   help='The number of evaluation periods for dynamic threshold. '
                        'Range: 1-6.')
        c.argument('min_failing_periods_to_alert', options_list=['--num-violations'], type=int,
                   help='The number of violations to trigger an dynamic alert. '
                        'Range: 1-6. It should be less than or equal to --num-periods.')
        c.argument('ignore_data_before', options_list=['--since'],
                   arg_type=get_datetime_type(
                       help='The date from which to start learning the metric historical data and calculate the dynamic thresholds.'))
        c.argument('skip_metric_validation', options_list=['--skip-metric-validation'],
                   arg_type=get_three_state_flag(),
                   help='Cause the metric validation to be skipped. This allows to use a metric that has not been emitted yet.')

    # endregion

    # region Autoscale
    with self.argument_context('monitor autoscale') as c:
        c.argument('autoscale_name', arg_type=autoscale_name_type, options_list=['--name', '-n'])
        c.argument('autoscale_setting_name', arg_type=autoscale_name_type, options_list=['--name', '-n'])
        c.argument('profile_name', arg_type=autoscale_profile_name_type)
        c.argument('rule_name', arg_type=autoscale_rule_name_type)
        c.argument('enabled', arg_type=get_three_state_flag(), help='Autoscale settings enabled status.')

    with self.argument_context('monitor autoscale', arg_group='Notification') as c:
        c.argument('actions', options_list=['--action', '-a'], action=AutoscaleAddAction, nargs='+')
        c.argument('add_actions', options_list=['--add-action', '-a'], action=AutoscaleAddAction, nargs='+')
        c.argument('remove_actions', options_list=['--remove-action', '-r'], action=AutoscaleRemoveAction, nargs='+')
        c.argument('email_administrator', arg_type=get_three_state_flag(), help='Send email to subscription administrator on scaling.')
        c.argument('email_coadministrators', arg_type=get_three_state_flag(), help='Send email to subscription co-administrators on scaling.')

    with self.argument_context('monitor autoscale create') as c:
        c.resource_parameter('resource', arg_group='Target Resource')
        c.argument('disabled', arg_type=get_three_state_flag(), help='Create the autoscale settings in a disabled state.')

    with self.argument_context('monitor autoscale', arg_group='Instance Limit') as c:
        c.argument('count', type=int, help='The numer of instances to use. If used with --min/max-count, the default number of instances to use.')
        c.argument('min_count', type=int, help='The minimum number of instances.')
        c.argument('max_count', type=int, help='The maximum number of instances.')

    with self.argument_context('monitor autoscale profile') as c:
        c.argument('autoscale_name', arg_type=autoscale_name_type, id_part=None)
        c.argument('profile_name', arg_type=autoscale_profile_name_type, options_list=['--name', '-n'])
        c.argument('copy_rules', help='Name of an existing schedule from which to copy the scaling rules for the new schedule.')

    with self.argument_context('monitor autoscale profile list-timezones') as c:
        c.argument('search_query', options_list=['--search-query', '-q'], help='Query text to find.')
        c.argument('offset', help='Filter results based on UTC hour offset.', type=timezone_offset_type)

    with self.argument_context('monitor autoscale profile', arg_group='Schedule') as c:
        c.argument('timezone', type=timezone_name_type)
        c.argument('start', arg_type=get_datetime_type(help='Start time.', timezone=False))
        c.argument('end', arg_type=get_datetime_type(help='End time.', timezone=False))
        c.argument('recurrence', options_list=['--recurrence', '-r'], nargs='+', validator=validate_autoscale_recurrence)

    with self.argument_context('monitor autoscale rule') as c:
        c.argument('autoscale_name', arg_type=autoscale_name_type, id_part=None)
        c.argument('rule_name', arg_type=autoscale_rule_name_type, options_list=['--name', '-n'])
        c.argument('scale', help='The direction and amount to scale.', action=AutoscaleScaleAction, nargs='+')
        c.argument('condition', help='Condition on which to scale.', action=AutoscaleConditionAction, nargs='+')
        c.argument('timegrain', validator=validate_autoscale_timegrain, nargs='+')
        c.argument('cooldown', type=int, help='The number of minutes that must elapse before another scaling event can occur.')

    with self.argument_context('monitor autoscale rule delete') as c:
        c.argument('index', nargs='+', help="Space-separated list of rule indices to remove, or '*' to clear all rules.")

    with self.argument_context('monitor autoscale rule copy') as c:
        c.argument('index', nargs='+', help="Space-separated list of rule indices to copy, or '*' to copy all rules.")
        c.argument('source_profile', options_list=['--source-schedule'], help='Name of the profile to copy rules from.')
        c.argument('dest_profile', options_list=['--dest-schedule'], help='Name of the profile to copy rules to.')

    with self.argument_context('monitor autoscale rule create') as c:
        c.resource_parameter('source', arg_group='Source', required=False, preserve_resource_group_parameter=True)
    # endregion

    # region Autoscale (OLD)
    with self.argument_context('monitor autoscale-settings') as c:
        c.argument('name', options_list=['--azure-resource-name'])
        c.argument('autoscale_setting_name', options_list=['--name', '-n'])

    with self.argument_context('monitor autoscale-settings create') as c:
        c.argument('parameters', type=get_json_object, help='JSON encoded parameters configuration. Use @{file} to load from a file. Use az autoscale-settings get-parameters-template to export json template.')

    for scope in ['monitor autoscale-settings show', 'monitor autoscale-settings delete']:
        with self.argument_context(scope) as c:
            c.argument('autoscale_setting_name', id_part='name')

    #  https://github.com/Azure/azure-rest-api-specs/issues/1017
    with self.argument_context('monitor autoscale-settings list') as c:
        c.ignore('filter')
    # endregion

    # region Diagnostic
    with self.argument_context('monitor diagnostic-settings') as c:
        c.argument('name', options_list=('--name', '-n'))

    with self.argument_context('monitor diagnostic-settings show') as c:
        c.resource_parameter('resource_uri', required=True, arg_group='Target Resource')

    with self.argument_context('monitor diagnostic-settings list') as c:
        c.resource_parameter('resource_uri', required=True)

    with self.argument_context('monitor diagnostic-settings delete') as c:
        c.resource_parameter('resource_uri', required=True, arg_group='Target Resource')

    with self.argument_context('monitor diagnostic-settings update') as c:
        c.resource_parameter('resource_uri', required=True, arg_group='Target Resource')

    with self.argument_context('monitor diagnostic-settings create') as c:
        c.resource_parameter('resource_uri', required=True, arg_group='Target Resource', skip_validator=True)
        c.argument('logs', type=get_json_object, help=" JSON encoded list of logs settings. Use '@{file}' to load from a file."
                   'For more information, visit: https://docs.microsoft.com/rest/api/monitor/diagnosticsettings/createorupdate#logsettings')
        c.argument('metrics', type=get_json_object, help="JSON encoded list of metric settings. Use '@{file}' to load from a file. "
                   'For more information, visit: https://docs.microsoft.com/rest/api/monitor/diagnosticsettings/createorupdate#metricsettings')
        c.argument('export_to_resource_specific', arg_type=get_three_state_flag(),
                   help='Indicate that the export to LA must be done to a resource specific table, '
                        'a.k.a. dedicated or fixed schema table, '
                        'as opposed to the default dynamic schema table called AzureDiagnostics. '
                        'This argument is effective only when the argument --workspace is also given.')

    with self.argument_context('monitor diagnostic-settings categories list') as c:
        c.resource_parameter('resource_uri', required=True)

    with self.argument_context('monitor diagnostic-settings categories show') as c:
        c.resource_parameter('resource_uri', required=True)

    with self.argument_context('monitor diagnostic-settings subscription') as c:
        import argparse
        c.argument('subscription_id', validator=process_subscription_id, help=argparse.SUPPRESS, required=False)
        c.argument('logs', type=get_json_object, help="JSON encoded list of logs settings. Use '@{file}' to load from a file.")
        c.argument('name', help='The name of the diagnostic setting.', options_list=['--name', '-n'])
        c.argument('event_hub_name', help='The name of the event hub. If none is specified, the default event hub will be selected.')
        c.argument('event_hub_auth_rule', help='The resource Id for the event hub authorization rule.')
        c.argument('workspace', help='The resource id of the log analytics workspace.')
        c.argument('storage_account', help='The resource id of the storage account to which you would like to send the Activity Log.')
        c.argument('service_bus_rule', help="The service bus rule ID of the service bus namespace in which you would like to have Event Hubs created for streaming the Activity Log. The rule ID is of the format '{service bus resource ID}/authorizationrules/{key name}'.")
    # endregion

    # region LogProfiles
    with self.argument_context('monitor log-profiles') as c:
        c.argument('log_profile_name', options_list=['--name', '-n'])

    with self.argument_context('monitor log-profiles create') as c:
        c.argument('name', options_list=['--name', '-n'])
        c.argument('categories', nargs='+')
        c.argument('locations', nargs='+')
        c.argument('days', type=int, arg_group='Retention Policy')
        c.argument('enabled', arg_type=get_three_state_flag(), arg_group='Retention Policy')
    # endregion

    # region ActivityLog
    with self.argument_context('monitor activity-log list') as c:
        activity_log_props = [x['key'] for x in EventData()._attribute_map.values()]  # pylint: disable=protected-access
        c.argument('select', nargs='+', arg_type=get_enum_type(activity_log_props))
        c.argument('max_events', type=int)

    with self.argument_context('monitor activity-log list', arg_group='Time') as c:
        c.argument('start_time', arg_type=get_datetime_type(help='Start time of the query.'))
        c.argument('end_time', arg_type=get_datetime_type(help='End time of the query. Defaults to the current time.'))
        c.argument('offset', type=get_period_type(as_timedelta=True))

    with self.argument_context('monitor activity-log list', arg_group='Filter') as c:
        c.argument('filters', deprecate_info=c.deprecate(target='--filters', hide=True, expiration='3.0.0'), help='OData filters. Will ignore other filter arguments.')
        c.argument('correlation_id')
        c.argument('resource_group', resource_group_name_type)
        c.argument('resource_id')
        c.argument('resource_provider', options_list=['--namespace', c.deprecate(target='--resource-provider', redirect='--namespace', hide=True, expiration='3.0.0')])
        c.argument('caller')
        c.argument('status')
    # endregion

    # region ActionGroup
    with self.argument_context('monitor action-group') as c:
        c.argument('action_group_name', options_list=['--name', '-n'], id_part='name')

    with self.argument_context('monitor action-group create') as c:
        from .actions import ActionGroupReceiverParameterAction
        c.extra('receivers', options_list=['--action', '-a'], nargs='+', arg_group='Actions', action=ActionGroupReceiverParameterAction)
        c.extra('short_name')
        c.extra('tags')
        c.ignore('action_group')

    with self.argument_context('monitor action-group update', arg_group='Actions') as c:
        c.extra('add_receivers', options_list=['--add-action', '-a'], nargs='+', action=ActionGroupReceiverParameterAction)
        c.extra('remove_receivers', options_list=['--remove-action', '-r'], nargs='+')
        c.ignore('action_group')

    with self.argument_context('monitor action-group enable-receiver') as c:
        c.argument('receiver_name', options_list=['--name', '-n'], help='The name of the receiver to resubscribe.')
        c.argument('action_group_name', options_list=['--action-group'], help='The name of the action group.')
    # endregion

    # region ActivityLog Alerts
    with self.argument_context('monitor activity-log alert') as c:
        c.argument('activity_log_alert_name', options_list=['--name', '-n'], id_part='name')

    with self.argument_context('monitor activity-log alert create') as c:
        from .operations.activity_log_alerts import process_condition_parameter
        c.argument('disable', action='store_true')
        c.argument('scopes', options_list=['--scope', '-s'], nargs='+')
        c.argument('condition', options_list=['--condition', '-c'], nargs='+', validator=process_condition_parameter)
        c.argument('action_groups', options_list=['--action-group', '-a'], nargs='+')
        c.argument('webhook_properties', options_list=['--webhook-properties', '-w'], arg_type=webhook_prop_type)

    with self.argument_context('monitor activity-log alert update-condition') as c:
        c.argument('reset', action='store_true')
        c.argument('add_conditions', options_list=['--add-condition', '-a'], nargs='+')
        c.argument('remove_conditions', options_list=['--remove-condition', '-r'], nargs='+')

    with self.argument_context('monitor activity-log alert update') as c:
        from .operations.activity_log_alerts import process_condition_parameter
        c.argument('condition', options_list=['--condition', '-c'], nargs='+', validator=process_condition_parameter)
        c.argument('enabled', arg_type=get_three_state_flag())

    with self.argument_context('monitor activity-log alert action-group add') as c:
        c.argument('reset', action='store_true')
        c.argument('action_group_ids', options_list=['--action-group', '-a'], nargs='+')
        c.argument('webhook_properties', options_list=['--webhook-properties', '-w'], arg_type=webhook_prop_type)

    with self.argument_context('monitor activity-log alert action-group remove') as c:
        c.argument('action_group_ids', options_list=['--action-group', '-a'], nargs='+')

    with self.argument_context('monitor activity-log alert scope add') as c:
        c.argument('scopes', options_list=['--scope', '-s'], nargs='+')
        c.argument('reset', action='store_true')

    with self.argument_context('monitor activity-log alert scope remove') as c:
        c.argument('scopes', options_list=['--scope', '-s'], nargs='+')
    # endregion

    # region Log Analytics Workspace
    with self.argument_context('monitor log-analytics workspace') as c:
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('workspace_name', options_list=['--workspace-name', '-n'], help="Name of the Log Analytics Workspace.")
        c.argument('sku', help="The supported value: PerGB2018, CapacityReservation.")
        c.argument('capacity_reservation_level', options_list=['--capacity-reservation-level', '--level'], help='The capacity reservation level for this workspace, when CapacityReservation sku is selected. The maximum value is 1000 and must be in multiples of 100. If you want to increase the limit, please contact LAIngestionRate@microsoft.com.')
        c.argument('daily_quota_gb', options_list=['--quota'], help='The workspace daily quota for ingestion in gigabytes. The minimum value is 0.023 and default is -1 which means unlimited.')
        c.argument('retention_time', help="The workspace data retention in days.", type=int, default=30)
        from azure.mgmt.loganalytics.models import PublicNetworkAccessType
        c.argument('public_network_access_for_ingestion', options_list=['--ingestion-access'], help='The public network access type to access workspace ingestion.',
                   arg_type=get_enum_type(PublicNetworkAccessType))
        c.argument('public_network_access_for_query', options_list=['--query-access'], help='The public network access type to access workspace query.',
                   arg_type=get_enum_type(PublicNetworkAccessType))
        c.argument('force', options_list=['--force', '-f'], arg_type=get_three_state_flag())

    with self.argument_context('monitor log-analytics workspace update') as c:
        c.argument('default_data_collection_rule_resource_id', options_list='--data-collection-rule', help='The resource ID of the default Data Collection Rule to use for this workspace. Expected format is /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Insights/dataCollectionRules/{dcrName}.')

    with self.argument_context('monitor log-analytics workspace pack') as c:
        c.argument('intelligence_pack_name', options_list=['--name', '-n'])
        c.argument('workspace_name', options_list='--workspace-name')

    with self.argument_context('monitor log-analytics workspace saved-search') as c:
        c.argument('saved_search_id', options_list=['--name', '-n'], help="Name of the saved search and it's unique in a given workspace.")
        c.argument('workspace_name', options_list='--workspace-name')
        c.argument('category', help='The category of the saved search. This helps the user to find a saved search faster.')
        c.argument('display_name', help='Display name of the saved search.')
        c.argument('saved_query', options_list=['--saved-query', '-q'], help='The query expression for the saved search.')
        c.argument('function_alias', options_list=['--func-alias', '--fa'],
                   help='Function Aliases are short names given to Saved Searches so they can be easily referenced in query. They are required for Computer Groups.')
        c.argument('function_parameters', options_list=['--func-param', '--fp'],
                   help="The optional function parameters if query serves as a function. "
                        "Value should be in the following format: 'param-name1:type1 = default_value1, param-name2:type2 = default_value2'. "
                        "For more examples and proper syntax please refer to "
                        "https://docs.microsoft.com/azure/kusto/query/functions/user-defined-functions.")
        c.argument('tags', tags_type)
    # endregion

    # region Log Analytics Workspace table
    with self.argument_context('monitor log-analytics workspace table') as c:
        c.argument('table_name', name_arg_type, help='Name of the table.')
        c.argument('workspace_name', options_list='--workspace-name')
        c.argument('retention_in_days', type=int, options_list='--retention-time', help='The data table data retention in days, between 30 and 730. Setting this property to null will default to the workspace')
        c.argument('total_retention_in_days', type=int, options_list='--total-retention-time', help='The table data total retention in days, between 4 and 2555. Setting this property to null will default to table retention.')

    with self.argument_context('monitor log-analytics workspace table create') as c:
        from azure.mgmt.loganalytics.models import TablePlanEnum
        c.argument('columns', nargs='+', help='A list of table custom columns.Extracts multiple space-separated colunms in colunm_name=colunm_type format')
        c.argument('plan', arg_type=get_enum_type(TablePlanEnum), help='The table plan. Possible values include: "Basic", "Analytics".')
        c.argument('description', help='Schema description.')

    with self.argument_context('monitor log-analytics workspace table search-job create') as c:
        c.argument('search_query', options_list=['--search-query'], help='Search job query.')
        c.argument('limit', type=int, help='Limit the search job to return up to specified number of rows.')
        c.argument('start_search_time', arg_type=get_datetime_type(help='Datetime format.'))
        c.argument('end_search_time', arg_type=get_datetime_type(help='Datetime format.'))

    with self.argument_context('monitor log-analytics workspace table restore create') as c:
        c.argument('start_restore_time', arg_type=get_datetime_type(help='Datetime format.'))
        c.argument('end_restore_time', arg_type=get_datetime_type(help='Datetime format.'))
        c.argument('restore_source_table', help='The table to restore data from.')

    with self.argument_context('monitor log-analytics workspace table update') as c:
        from azure.mgmt.loganalytics.models import TablePlanEnum
        c.argument('columns', nargs='+', help='A list of table custom columns.Extracts multiple space-separated colunms in colunm_name=colunm_type format')
        c.argument('plan', arg_type=get_enum_type(TablePlanEnum), help='The table plan. Possible values include: "Basic", "Analytics".')
        c.argument('description', help='Table description.')
    # endregion

    # region Log Analytics Workspace Data Export
    with self.argument_context('monitor log-analytics workspace data-export') as c:
        c.argument('data_export_name', options_list=['--name', '-n'], help="Name of the data export rule")
        c.argument('workspace_name', options_list='--workspace-name')
        c.argument('table_names', nargs='+', options_list=['--tables', '-t'],
                   help='An array of tables to export.')
        c.argument('destination', validator=process_workspace_data_export_destination,
                   help='The destination resource ID. It should be a storage account, an event hub namespace or an event hub. '
                        'If event hub namespace is provided, event hub would be created for each table automatically.')
        c.ignore('data_export_type')
        c.ignore('event_hub_name')
        c.argument('enable', arg_type=get_three_state_flag(), help='Enable this data export rule.')
    # endregion

    # region Log Analytics Workspace Linked Service
    with self.argument_context('monitor log-analytics workspace linked-service') as c:
        c.argument('linked_service_name', name_arg_type, help='Name of the linkedServices resource. Supported values: cluster, automation.')
        c.argument('workspace_name', options_list='--workspace-name')
        c.argument('resource_id', help='The resource id of the resource that will be linked to the workspace. This '
                                       'should be used for linking resources which require read access.')
        c.argument('write_access_resource_id', help='The resource id of the resource that will be linked to the '
                                                    'workspace. This should be used for linking resources which '
                                                    'require write access.')
    # endregion

    # region Log Analytics Cluster
    with self.argument_context('monitor log-analytics cluster') as c:
        c.argument('cluster_name', name_arg_type, help='The name of the Log Analytics cluster.')
        c.argument('sku_name', help="The name of the SKU. Currently only support 'CapacityReservation'")
        c.argument('sku_capacity', help='The capacity of the SKU. It must be in the range of 1000-2000 per day and must'
                                        ' be in multiples of 100. If you want to increase the limit, please contact'
                                        ' LAIngestionRate@microsoft.com. It can be decreased only after 31 days.')
        c.argument('identity_type', help='The identity type. Supported values: SystemAssigned')

    with self.argument_context('monitor log-analytics cluster update') as c:
        c.argument('key_vault_uri', help='The Key Vault uri which holds the key associated with the Log Analytics cluster.')
        c.argument('key_name', help='The name of the key associated with the Log Analytics cluster.')
        c.argument('key_version', help='The version of the key associated with the Log Analytics cluster.')
    # endregion

    # region Log Analytics Linked Storage Account
    with self.argument_context('monitor log-analytics workspace linked-storage') as c:
        from azure.mgmt.loganalytics.models import DataSourceType
        c.argument('data_source_type', help='Data source type for the linked storage account.',
                   options_list=['--type'], arg_type=get_enum_type(DataSourceType))
        c.argument('storage_account_ids', nargs='+', options_list=['--storage-accounts'],
                   help='List of Name or ID of Azure Storage Account.',
                   validator=validate_storage_accounts_name_or_id)
    # endregion

    # region monitor clone
    with self.argument_context('monitor clone') as c:
        c.argument('source_resource', help="Resource ID of the source resource.")
        c.argument('target_resource', help="Resource ID of the target resource.")
        c.argument('always_clone', action='store_true',
                   help="If this argument is applied, "
                        "all monitor settings would be cloned instead of expanding its scope.")
        c.argument('monitor_types', options_list=['--types', '-t'], arg_type=get_enum_type(['metricsAlert']),
                   nargs='+', help='List of types of monitor settings which would be cloned.', default=['metricsAlert'])

    # region Private Link Resources
    for item in ['create', 'update', 'show', 'delete', 'list']:
        with self.argument_context('monitor private-link-scope {}'.format(item)) as c:
            c.argument('scope_name', scope_name_type, options_list=['--name', '-n'])
    with self.argument_context('monitor private-link-scope create') as c:
        c.ignore('location')

    with self.argument_context('monitor private-link-scope scoped-resource') as c:
        c.argument('scope_name', scope_name_type)
        c.argument('resource_name', options_list=['--name', '-n'], help='Name of the assigned resource.')
        c.argument('linked_resource_id', options_list=['--linked-resource'], help='ARM resource ID of the linked resource. It should be one of log analytics workspace or application insights component.')

    with self.argument_context('monitor private-link-scope private-link-resource') as c:
        c.argument('scope_name', scope_name_type)
        c.argument('group_name', options_list=['--name', '-n'], help='Name of the private link resource.')

    with self.argument_context('monitor private-link-scope private-endpoint-connection') as c:
        c.argument('scope_name', scope_name_type)
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'],
                   help='The name of the private endpoint connection associated with the private link scope.')
    for item in ['approve', 'reject', 'show', 'delete']:
        with self.argument_context('monitor private-link-scope private-endpoint-connection {}'.format(item)) as c:
            c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                       help='The name of the private endpoint connection associated with the private link scope.')
            c.extra('connection_id', options_list=['--id'],
                    help='The ID of the private endpoint connection associated with the private link scope. You can get '
                    'it using `az monitor private-link-scope show`.')
            c.argument('scope_name', help='Name of the Azure Monitor Private Link Scope.', required=False)
            c.argument('resource_group_name', help='The resource group name of specified private link scope.',
                       required=False)
            c.argument('description', help='Comments for {} operation.'.format(item))
    # endregion
