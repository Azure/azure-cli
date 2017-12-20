# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):  # pylint: disable=too-many-locals, too-many-statements
    from azure.cli.core.commands.parameters import tags_type, get_location_type, get_enum_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group
    from knack.arguments import CLIArgumentType
    from .validators import process_webhook_prop

    webhook_prop_type = CLIArgumentType(validator=process_webhook_prop, nargs='*')

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')

    with self.argument_context('monitor') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx),
                   validator=get_default_location_from_resource_group)
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('monitor action-group') as c:
        c.argument('action_group_name', options_list=('--name', '-n'), id_part='name')

    with self.argument_context('monitor action-group create') as c:
        from .operations.actions import ActionGroupReceiverParameterAction
        from .validators import process_action_group_detail_for_creation

        c.extra('receivers', options_list=('--action', '-a'), nargs='+', arg_group='Actions',
                action=ActionGroupReceiverParameterAction, validator=process_action_group_detail_for_creation)
        c.extra('short_name')
        c.extra('tags')
        c.ignore('action_group')

    with self.argument_context('monitor action-group update') as c:
        c.extra('add_receivers', options_list=('--add-action', '-a'), nargs='+', arg_group='Actions',
                action=ActionGroupReceiverParameterAction)
        c.extra('remove_receivers', options_list=('--remove-action', '-r'), nargs='+', arg_group='Actions')
        c.ignore('action_group')

    with self.argument_context('monitor action-group enable-receiver') as c:
        c.argument('receiver_name', options_list=('--name', '-n'))
        c.argument('action_group_name', options_list='--action-group')

    with self.argument_context('monitor activity-log list') as c:
        c.argument('resource_group', options_list=('--resource-group', '-g'))
        c.argument('select', None, nargs='+')

        filter_arg_group_name = 'OData Filter'
        c.argument('correlation_id', arg_group=filter_arg_group_name)
        c.argument('resource_group', arg_group=filter_arg_group_name)
        c.argument('resource_id', arg_group=filter_arg_group_name)
        c.argument('resource_provider', arg_group=filter_arg_group_name)
        c.argument('start_time', arg_group=filter_arg_group_name)
        c.argument('end_time', arg_group=filter_arg_group_name)
        c.argument('caller', arg_group=filter_arg_group_name)
        c.argument('status', arg_group=filter_arg_group_name)

    with self.argument_context('monitor activity-log alert') as c:
        c.argument('activity_log_alert_name', options_list=('--name', '-n'), id_part='name')

    with self.argument_context('monitor activity-log alert create') as c:
        from .operations.activity_log_alerts import process_condition_parameter
        c.argument('scopes', options_list=('--scope', '-s'), nargs='+')
        c.argument('disable', options_list='--disable', action='store_true')
        c.argument('condition', options_list=('--condition', '-c'), nargs='+',
                   validator=process_condition_parameter)
        c.argument('action_groups', options_list=('--action-group', '-a'), nargs='+')
        c.argument('webhook_properties', options_list=('--webhook-properties', '-w'), arg_type=webhook_prop_type)

    with self.argument_context('monitor activity-log alert update-condition') as c:
        c.argument('reset', options_list='--reset', action='store_true')
        c.argument('add_conditions', options_list=('--add-condition', '-a'), nargs='+')
        c.argument('remove_conditions', options_list=('--remove-condition', '-r'), nargs='+')

    with self.argument_context('monitor activity-log alert update') as c:
        from azure.cli.core.commands.parameters import get_three_state_flag
        from .operations.activity_log_alerts import process_condition_parameter

        c.argument('enabled', options_list='--enabled', arg_type=get_three_state_flag())
        c.argument('condition', options_list=('--condition', '-c'), nargs='+',
                   validator=process_condition_parameter)

    with self.argument_context('monitor activity-log alert action-group add') as c:
        c.argument('reset', options_list='--reset', action='store_true')
        c.argument('action_group_ids', options_list=('--action-group', '-a'), nargs='+')
        c.argument('webhook_properties', options_list=('--webhook-properties', '-w'), arg_type=webhook_prop_type)

    with self.argument_context('monitor activity-log alert action-group remove') as c:
        c.argument('action_group_ids', options_list=('--action-group', '-a'), nargs='+')

    with self.argument_context('monitor activity-log alert scope add') as c:
        c.argument('scopes', options_list=('--scope', '-s'), nargs='+')
        c.argument('reset', options_list='--reset', action='store_true')

    with self.argument_context('monitor activity-log alert scope remove') as c:
        c.argument('scopes', options_list=('--scope', '-s'), nargs='+')

    with self.argument_context('monitor alert') as c:
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')

    with self.argument_context('monitor alert create') as c:
        from azure.mgmt.monitor.models import ConditionOperator, TimeAggregationOperator
        from .operations.actions import AlertAddAction, ConditionAction

        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')
        c.argument('custom_emails', nargs='+', arg_group='Action')
        c.argument('disabled', arg_type=get_three_state_flag())
        c.argument('email_service_owners', arg_group='Action', arg_type=get_three_state_flag())
        c.argument('actions', options_list=['--action', '-a'], action=AlertAddAction, nargs='+', arg_group='Action')
        c.argument('condition', action=ConditionAction, nargs='+')
        c.argument('metric_name', arg_group='Condition')
        c.argument('operator', arg_group='Condition', arg_type=get_enum_type(ConditionOperator))
        c.argument('threshold', arg_group='Condition')
        c.argument('time_aggregation', arg_group='Condition', arg_type=get_enum_type(TimeAggregationOperator))
        c.argument('window_size', arg_group='Condition')
        c.resource_parameter('target', 'Target Resource')

    with self.argument_context('monitor alert update') as c:
        from .operations.actions import AlertAddAction, AlertRemoveAction, ConditionAction, period_type
        from .util import get_operator_map, get_aggregation_map
        c.argument('rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')

        c.argument('email_service_owners', arg_group='Action', arg_type=get_three_state_flag())
        c.argument('add_actions', options_list=['--add-action', '-a'], nargs='+', action=AlertAddAction,
                   arg_group='Action')
        c.argument('remove_actions', options_list=['--remove-action', '-r'], nargs='+', action=AlertRemoveAction,
                   arg_group='Action')

        c.argument('condition', action=ConditionAction, nargs='+', arg_group='Condition')
        c.argument('metric', arg_group='Condition')
        c.argument('operator', arg_group='Condition', arg_type=get_enum_type(get_operator_map().keys()))
        c.argument('threshold', arg_group='Condition')
        c.argument('aggregation', arg_group='Condition', arg_type=get_enum_type(get_aggregation_map().keys()))
        c.argument('period', type=period_type, arg_group='Condition')
        c.resource_parameter('target', 'Target Resource', required=False)

    with self.argument_context('monitor alert list-incidents') as c:
        c.argument('rule_name', options_list=['--rule-name'], id_part=None)

    for item in ['show-incident', 'list-incidents']:
        with self.argument_context('monitor alert {}'.format(item)) as c:
            c.argument('rule_name', options_list=['--rule-name'], id_part='name')
            c.argument('incident_name', name_arg_type, id_part='child_name_1')

    with self.argument_context('monitor metrics list-definitions') as c:
        c.resource_parameter_context('resource_uri', 'Target Resource')

    with self.argument_context('monitor metrics list') as c:
        from .validators import (process_metric_timespan, process_metric_aggregation, process_metric_result_type,
                                 process_metric_dimension)
        from azure.mgmt.monitor.models.monitor_management_client_enums import AggregationType

        c.resource_parameter_context('resource_uri', 'Target Resource')
        c.extra('start_time', options_list='--start-time', validator=process_metric_timespan, arg_group='Time')
        c.extra('end_time', options_list='--end-time', arg_group='Time')
        c.extra('metadata', options_list='--metadata', action='store_true', validator=process_metric_result_type)
        c.extra('dimension', options_list='--dimension', nargs='*', validator=process_metric_dimension)
        c.argument('interval', arg_group='Time')
        c.argument('aggregation', nargs='*', validator=process_metric_aggregation,
                   arg_type=get_enum_type(t for t in AggregationType if t.name != 'none'))
        c.ignore('timespan', 'result_type', 'top', 'orderby')

    with self.argument_context('monitor autoscale-settings') as c:
        c.argument('name', options_list=('--azure-resource-name',))
        c.argument('autoscale_setting_name', options_list=('--name', '-n'))

    with self.argument_context('monitor autoscale-settings create') as c:
        from azure.cli.core.util import get_json_object
        c.argument('parameters', ('--parameters',),
                   type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                        'Use az autoscale-settings get-parameters-template to export json template.')

    with self.argument_context('monitor autoscale-settings show') as c:
        c.argument('autoscale_setting_name', id_part='name')

    with self.argument_context('monitor autoscale-settings delete') as c:
        c.argument('autoscale_setting_name', id_part='name')

    #  https://github.com/Azure/azure-rest-api-specs/issues/1017
    with self.argument_context('monitor autoscale-settings list') as c:
        c.ignore('filter')

    with self.argument_context('monitor diagnostic-settings') as c:
        c.argument('resource_uri', options_list='--resource-id')

    with self.argument_context('monitor diagnostic-settings create') as c:
        from azure.cli.core.util import get_json_object
        from .validators import validate_diagnostic_settings

        c.argument('resource_group', options_list=('--resource-group', '-g'))
        c.argument('target_resource_id', options_list='--resource-id', validator=validate_diagnostic_settings)
        c.argument('logs', options_list='--logs', type=get_json_object)
        c.argument('metrics', options_list='--metrics', type=get_json_object)
        c.argument('tags', nargs='*')

        # Service Bus argument group
        c.ignore('service_bus_rule_id')
        c.argument('namespace', arg_group='Service Bus')
        c.argument('rule_name', arg_group='Service Bus')

    with self.argument_context('monitor log-profiles') as c:
        c.argument('log_profile_name', options_list=('--name', '-n'))

    with self.argument_context('monitor log-profiles create') as c:
        from azure.mgmt.monitor.models import LogProfileResource, RetentionPolicy
        c.argument('name', options_list='--log-profile-name')
        c.expand('retention_policy', RetentionPolicy)
        c.expand('parameters', LogProfileResource)
        c.argument('name', options_list='--log-profile-resource-name')
        c.argument('log_profile_name', options_list=('--name', '-n'))
        c.argument('categories', nargs='+',
                   help="Space separated categories of the logs.Some values are: "
                        "'Write', 'Delete', and/or 'Action.'")
        c.argument('locations', nargs='+',
                   help="Space separated list of regions for which Activity Log events "
                        "should be stored.")
