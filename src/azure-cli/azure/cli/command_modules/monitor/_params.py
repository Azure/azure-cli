# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import get_json_object

from azure.cli.core.commands.parameters import (
    get_location_type, tags_type, get_three_state_flag, get_enum_type, get_datetime_type, resource_group_name_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from azure.cli.command_modules.monitor.actions import (
    AutoscaleScaleAction, AutoscaleConditionAction, get_period_type, AutoscaleCreateAction,
    timezone_offset_type, timezone_name_type, MetricAlertConditionAction, MetricAlertAddAction)
from azure.cli.command_modules.monitor.validators import (
    validate_loganalytics_workspace_search_table_name, validate_loganalytics_workspace_restore_table_name,
    validate_autoscale_recurrence, validate_autoscale_timegrain, get_action_group_validator,
    get_action_group_id_validator, validate_metric_dimension, validate_storage_accounts_name_or_id)
from azure.cli.command_modules.monitor.actions import get_date_midnight_type

from knack.arguments import CLIArgumentType


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):
    from azure.mgmt.monitor.models import EventData, PredictiveAutoscalePolicyScaleMode
    from .grammar.metric_alert.MetricAlertConditionValidator import dim_op_conversion, agg_conversion, op_conversion, sens_conversion
    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')

    autoscale_name_type = CLIArgumentType(options_list=['--autoscale-name'], help='Name of the autoscale settings.', id_part='name')
    autoscale_profile_name_type = CLIArgumentType(options_list=['--profile-name'], help='Name of the autoscale profile.')
    autoscale_rule_name_type = CLIArgumentType(options_list=['--rule-name'], help='Name of the autoscale rule.')

    with self.argument_context('monitor') as c:
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)

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
        c.argument('top', type=int, help='Max number of records to retrieve.')
        c.argument('filters', options_list='--filter')
        c.argument('metric_namespace', options_list='--namespace')

    with self.argument_context('monitor metrics list', arg_group='Time') as c:
        c.argument('start_time', arg_type=get_datetime_type(help='Start time of the query.'))
        c.argument('end_time', arg_type=get_datetime_type(help='End time of the query. Defaults to the current time.'))
        c.argument('offset', type=get_period_type(as_timedelta=True))
        c.argument('interval', arg_group='Time', type=get_period_type())

    with self.argument_context('monitor metrics list-namespaces') as c:
        c.argument("resource_uri", help="The identifier of the resource.")
        c.argument('start_time', arg_type=get_datetime_type(help='Start time of the query.'), arg_group='Time')
    # endregion

    # region MetricAlerts
    with self.argument_context('monitor metrics alert') as c:
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')
        c.argument('severity', type=int, help='Severity of the alert from 0 (critical) to 4 (verbose).')
        c.argument('window_size', help='Time over which to aggregate metrics in "##h##m##s" format.')
        c.argument('evaluation_frequency', help='Frequency with which to evaluate the rule in "##h##m##s" format.')
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

    with self.argument_context('monitor autoscale create', arg_group='Notification') as c:
        c.argument('actions', options_list=['--action', '-a'], action=AutoscaleCreateAction, nargs='+')

    with self.argument_context('monitor autoscale', arg_group='Notification') as c:
        c.argument('email_administrator', arg_type=get_three_state_flag(), help='Send email to subscription administrator on scaling.')
        c.argument('email_coadministrators', arg_type=get_three_state_flag(), help='Send email to subscription co-administrators on scaling.')

    with self.argument_context('monitor autoscale create') as c:
        c.resource_parameter('resource', arg_group='Target Resource')
        c.argument('disabled', arg_type=get_three_state_flag(), help='Create the autoscale settings in a disabled state.')

    with self.argument_context('monitor autoscale', arg_group='Instance Limit') as c:
        c.argument('count', type=int, help='The numer of instances to use. If used with --min/max-count, the default number of instances to use.')
        c.argument('min_count', type=int, help='The minimum number of instances.')
        c.argument('max_count', type=int, help='The maximum number of instances.')

    with self.argument_context('monitor autoscale', arg_group='Predictive Policy') as c:
        c.argument('scale_look_ahead_time', help='The amount of time to specify by which instances are launched in advance. '
                                                 'It must be between 1 minute and 60 minutes in ISO 8601 format '
                                                 '(for example, 100 days would be P100D).')
        c.argument('scale_mode', arg_type=get_enum_type(PredictiveAutoscalePolicyScaleMode), help='The predictive autoscale mode')

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
        c.argument('correlation_id')
        c.argument('resource_group', resource_group_name_type)
        c.argument('resource_id')
        c.argument('resource_provider', options_list=['--namespace'])
        c.argument('caller')
        c.argument('status')
    # endregion

    # region ActionGroup
    with self.argument_context('monitor action-group') as c:
        c.argument('action_group_name', options_list=['--name', '-n'], id_part='name')
        c.argument('location', get_location_type(self.cli_ctx), validator=None)
    # endregion

    # region ActivityLog Alerts
    with self.argument_context('monitor activity-log alert') as c:
        c.argument('activity_log_alert_name', options_list=['--name', '-n'], id_part='name')
    # endregion

    # region Log Analytics Workspace
    with self.argument_context('monitor log-analytics workspace') as c:
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('workspace_name', options_list=['--workspace-name', '-n'], help="Name of the Log Analytics Workspace.")
        c.argument('sku', help="The supported value: PerGB2018, CapacityReservation.")
        c.argument('capacity_reservation_level', options_list=['--capacity-reservation-level', '--level'], help='The capacity reservation level for this workspace, when CapacityReservation sku is selected. The maximum value is 1000 and must be in multiples of 100. If you want to increase the limit, please contact LAIngestionRate@microsoft.com.')
        c.argument('daily_quota_gb', options_list=['--quota'], help='The workspace daily quota for ingestion in gigabytes. The minimum value is 0.023 and default is -1 which means unlimited.')
        c.argument('retention_time', help="The workspace data retention in days.", type=int, default=30)
        c.argument('force', options_list=['--force', '-f'], arg_type=get_three_state_flag())

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
                        "https://learn.microsoft.com/azure/kusto/query/functions/user-defined-functions.")
        c.argument('tags', tags_type)
    # endregion

    # region Log Analytics Workspace table
    with self.argument_context('monitor log-analytics workspace table') as c:
        c.argument('table_name', name_arg_type, help='Name of the table.')
        c.argument('workspace_name', options_list='--workspace-name')
        c.argument('retention_in_days', type=int, options_list='--retention-time', help='The table retention in days, between 4 and 730. Setting this property to -1 will default to the workspace retention.')
        c.argument('total_retention_in_days', type=int, options_list='--total-retention-time', help='The table total retention in days, between 4 and 2556. Setting this property to -1 will default to table retention.')

    with self.argument_context('monitor log-analytics workspace table create') as c:
        c.argument('columns', nargs='+', help='A list of table custom columns.Extracts multiple space-separated columns in column_name=column_type format')
        c.argument('plan', arg_type=get_enum_type(["Basic", "Analytics"]), help='The table plan. Possible values include: "Basic", "Analytics".')
        c.argument('description', help='Schema description.')

    with self.argument_context('monitor log-analytics workspace table search-job create') as c:
        c.argument('table_name', name_arg_type, help='Name of the table. The table name needs to end with _SRCH',
                   validator=validate_loganalytics_workspace_search_table_name)
        c.argument('search_query', options_list=['--search-query'], help='Search job query.')
        c.argument('limit', type=int, help='Limit the search job to return up to specified number of rows.')
        c.argument('start_search_time', arg_type=get_datetime_type(help='Datetime format.'))
        c.argument('end_search_time', arg_type=get_datetime_type(help='Datetime format.'))

    with self.argument_context('monitor log-analytics workspace table restore create') as c:
        c.argument('table_name', name_arg_type, help='Name of the table. The table name needs to end with _RST',
                   validator=validate_loganalytics_workspace_restore_table_name)
        c.argument('start_restore_time', arg_type=get_date_midnight_type(help='Datetime format.'))
        c.argument('end_restore_time', arg_type=get_date_midnight_type(help='Datetime format.'))
        c.argument('restore_source_table', help='The table to restore data from.')

    with self.argument_context('monitor log-analytics workspace table update') as c:
        c.argument('columns', nargs='+', help='A list of table custom columns.Extracts multiple space-separated columns in column_name=column_type format')
        c.argument('plan', arg_type=get_enum_type(["Basic", "Analytics"]), help='The table plan. Possible values include: "Basic", "Analytics".')
        c.argument('description', help='Table description.')
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

    # region Log Analytics Linked Storage Account
    with self.argument_context('monitor log-analytics workspace linked-storage') as c:
        c.argument('data_source_type', help='Data source type for the linked storage account.',
                   options_list=['--type'], arg_type=get_enum_type(["Alerts", "AzureWatson", "CustomLogs", "Ingestion", "Query"]))
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
    # endregion
