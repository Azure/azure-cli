# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.util import get_json_object

from azure.cli.core.commands.parameters import get_location_type, tags_type, get_three_state_flag, get_enum_type
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from azure.cli.command_modules.monitor.operations.actions import (
    AlertAddAction, AlertRemoveAction, ConditionAction, period_type)
from azure.cli.command_modules.monitor.util import get_operator_map, get_aggregation_map
from azure.cli.command_modules.monitor.validators import process_webhook_prop


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):

    from azure.mgmt.monitor.models.monitor_management_client_enums import ConditionOperator, TimeAggregationOperator
    from azure.mgmt.monitor.models import LogProfileResource, RetentionPolicy

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    webhook_prop_type = CLIArgumentType(validator=process_webhook_prop, nargs='*')

    with self.argument_context('monitor') as c:
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)

    # region Alerts
    with self.argument_context('monitor alert') as c:
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')

    with self.argument_context('monitor alert create') as c:
        c.resource_parameter('target', arg_group='Target Resource')
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
        c.resource_parameter('target', arg_group='Target Resource', required=False)

    with self.argument_context('monitor alert update', arg_group='Action') as c:
        c.argument('email_service_owners', arg_type=get_three_state_flag())
        c.argument('add_actions', options_list=['--add-action', '-a'], nargs='+', action=AlertAddAction,)
        c.argument('remove_actions', options_list=['--remove-action', '-r'], nargs='+', action=AlertRemoveAction)

    with self.argument_context('monitor alert update', arg_group='Condition') as c:
        c.argument('condition', action=ConditionAction, nargs='+')
        c.argument('metric')
        c.argument('operator', arg_type=get_enum_type(get_operator_map().keys()))
        c.argument('threshold')
        c.argument('aggregation', arg_type=get_enum_type(get_aggregation_map().keys()))
        c.argument('period', type=period_type)

    for scope in ['monitor alert show-incident', 'monitor alert list-incidents']:
        with self.argument_context(scope) as c:
            c.argument('rule_name', options_list=['--rule-name'], id_part='name')
            c.argument('incident_name', name_arg_type, id_part='child_name_1')

    with self.argument_context('monitor alert list-incidents') as c:
        c.argument('rule_name', options_list=['--rule-name'], id_part=None)
    # endregion

    # region Metrics
    with self.argument_context('monitor metrics list-definitions') as c:
        c.resource_parameter_context('resource_uri', arg_group='Target Resource')

    with self.argument_context('monitor metrics list') as c:
        from .validators import (process_metric_timespan, process_metric_aggregation, process_metric_result_type,
                                 process_metric_dimension)
        from azure.mgmt.monitor.models.monitor_management_client_enums import AggregationType
        c.resource_parameter_context('resource_uri', arg_group='Target Resource')
        c.extra('start_time', options_list=['--start-time'], validator=process_metric_timespan, arg_group='Time')
        c.extra('end_time', options_list=['--end-time'], arg_group='Time')
        c.extra('metadata', options_list=['--metadata'], action='store_true', validator=process_metric_result_type)
        c.extra('dimension', options_list=['--dimension'], nargs='*', validator=process_metric_dimension)
        c.argument('interval', arg_group='Time')
        c.argument('aggregation', arg_type=get_enum_type(t for t in AggregationType if t.name != 'none'), nargs='*', validator=process_metric_aggregation)
        c.ignore('timespan', 'result_type', 'top', 'orderby')
    # endregion

    # region Autoscale
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
        c.resource_parameter_context('resource_uri', required=True, arg_group='Target Resource')

    with self.argument_context('monitor diagnostic-settings list') as c:
        c.resource_parameter_context('resource_uri', required=True)

    with self.argument_context('monitor diagnostic-settings delete') as c:
        c.resource_parameter_context('resource_uri', required=True, arg_group='Target Resource')

    with self.argument_context('monitor diagnostic-settings update') as c:
        c.resource_parameter_context('resource_uri', required=True, arg_group='Target Resource')

    with self.argument_context('monitor diagnostic-settings create') as c:
        c.resource_parameter_context('resource_uri', required=True, arg_group='Target Resource', skip_validator=True)
        c.argument('logs', type=get_json_object)
        c.argument('metrics', type=get_json_object)

    with self.argument_context('monitor diagnostic-settings categories list') as c:
        c.resource_parameter_context('resource_uri', required=True)

    with self.argument_context('monitor diagnostic-settings categories show') as c:
        c.resource_parameter_context('resource_uri', required=True)
    # endregion

    # region LogProfiles
    with self.argument_context('monitor log-profiles') as c:
        c.argument('log_profile_name', options_list=['--name', '-n'])

    with self.argument_context('monitor log-profiles create') as c:
        c.argument('name', options_list=['--log-profile-name'])
        c.expand('retention_policy', RetentionPolicy)
        c.expand('parameters', LogProfileResource)
        c.argument('name', options_list=['--log-profile-resource-name'])
        c.argument('log_profile_name', options_list=['--name', '-n'])
        c.argument('categories', nargs='+', help="Space separated categories of the logs.Some values are: 'Write', 'Delete', and/or 'Action.'")
        c.argument('locations', nargs='+', help="Space separated list of regions for which Activity Log events should be stored.")
    # endregion

    # region ActivityLog
    with self.argument_context('monitor activity-log list') as c:
        c.argument('select', nargs='+')

    with self.argument_context('monitor activity-log list', arg_group='OData Filter') as c:
        c.argument('correlation_id')
        c.argument('resource_group')
        c.argument('resource_id')
        c.argument('resource_provider')
        c.argument('start_time')
        c.argument('end_time')
        c.argument('caller')
        c.argument('status')
    # endregion

    # region ActionGroup
    with self.argument_context('monitor action-group') as c:
        c.argument('action_group_name', options_list=['--name', '-n'], id_part='name')

    with self.argument_context('monitor action-group create') as c:
        from .validators import process_action_group_detail_for_creation
        from .operations.actions import ActionGroupReceiverParameterAction
        c.extra('receivers', options_list=['--action', '-a'], nargs='+', arg_group='Actions', action=ActionGroupReceiverParameterAction, validator=process_action_group_detail_for_creation)
        c.extra('short_name')
        c.extra('tags')
        c.ignore('action_group')

    with self.argument_context('monitor action-group update', arg_group='Actions') as c:
        c.extra('add_receivers', options_list=['--add-action', '-a'], nargs='+', action=ActionGroupReceiverParameterAction)
        c.extra('remove_receivers', options_list=['--remove-action', '-r'], nargs='+')
        c.ignore('action_group')

    with self.argument_context('monitor action-group enable-receiver') as c:
        c.argument('receiver_name', options_list=['--name', '-n'])
        c.argument('action_group_name', options_list=['--action-group'])
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
