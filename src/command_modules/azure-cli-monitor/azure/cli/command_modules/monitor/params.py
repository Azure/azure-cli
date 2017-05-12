# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.util import get_json_object

from azure.cli.core.commands import \
    (VersionConstraint, CliArgumentType, register_cli_argument, register_extra_cli_argument)
from azure.cli.core.commands.parameters import (location_type, get_resource_name_completion_list,
                                                enum_choice_list, tags_type, ignore_type,
                                                file_type, get_resource_group_completion_list,
                                                three_state_flag, model_choice_list)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.util import CLIError

from azure.cli.command_modules.monitor.actions import WebhookAction, ConditionAction, period_type
from azure.cli.command_modules.monitor.custom import operator_map, aggregation_map
from azure.cli.command_modules.monitor.validators import \
    (validate_diagnostic_settings, get_target_resource_validator)
from azure.mgmt.monitor.models.monitor_management_client_enums import \
    (MetricStatisticType, TimeAggregationType, ConditionOperator, TimeAggregationOperator) 


def register_resource_parameter(command, dest, arg_group=None):
    """ Helper method to add the extra parameters needed to support specifying name or ID
        for target resources. """
    register_cli_argument(command, dest, options_list=['--resource-id'], arg_group=arg_group, required=False, validator=get_target_resource_validator(dest), help="ID of the target resource. If used, do not supply other 'Target Resource' arguments.")
    register_extra_cli_argument(command, 'resource_name', arg_group=arg_group, help='Name of the target resource. (ex: myC)')
    register_extra_cli_argument(command, 'namespace', arg_group=arg_group, help="Target resource provider namespace (ex: Microsoft.Provider)")
    register_extra_cli_argument(command, 'parent', arg_group=arg_group, help="Target resource parent path, if applicable. (Ex: 'resA/myA/resB/myB')")
    register_extra_cli_argument(command, 'resource_type', arg_group=arg_group, help="Target resource type (Ex: 'resC'). Can also accept namespace/type format (Ex: 'Microsoft.Provider/resC')")


name_arg_type = CliArgumentType(options_list=['--name', '-n'], metavar='NAME')

register_cli_argument('monitor', 'location', location_type, validator=get_default_location_from_resource_group)
register_cli_argument('monitor', 'tags', tags_type)

# region Alerts

register_cli_argument('monitor alert', 'rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')

for item in ['create', 'create2']:
    register_cli_argument('monitor alert {}'.format(item), 'rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')

    register_cli_argument('monitor alert {}'.format(item), 'custom_emails', nargs='+', arg_group='Action')
    register_cli_argument('monitor alert {}'.format(item), 'email_service_owners', arg_group='Action', **three_state_flag())
    register_cli_argument('monitor alert {}'.format(item), 'webhook', nargs='+', action=WebhookAction, arg_group='Action')

    register_cli_argument('monitor alert {}'.format(item), 'condition', action=ConditionAction, nargs='+')
    register_cli_argument('monitor alert {}'.format(item), 'metric_name', arg_group='Condition')
    register_cli_argument('monitor alert {}'.format(item), 'operator', arg_group='Condition', **enum_choice_list(ConditionOperator))
    register_cli_argument('monitor alert {}'.format(item), 'threshold', arg_group='Condition')
    register_cli_argument('monitor alert {}'.format(item), 'time_aggregation', arg_group='Condition', **enum_choice_list(TimeAggregationOperator))
    register_cli_argument('monitor alert {}'.format(item), 'window_size', arg_group='Condition')

    register_resource_parameter('monitor alert {}'.format(item), 'target', 'Target Resource')

register_cli_argument('monitor alert update', 'rule_name', name_arg_type, id_part='name', help='Name of the alert rule.')
register_cli_argument('monitor alert update', 'add_emails', nargs='+', arg_group='Action')
register_cli_argument('monitor alert update', 'remove_emails', nargs='+', arg_group='Action')
register_cli_argument('monitor alert update', 'email_service_owners', arg_group='Action', **three_state_flag())
register_cli_argument('monitor alert update', 'add_webhook', nargs='+', action=WebhookAction, arg_group='Action')
register_cli_argument('monitor alert update', 'remove_webhooks', nargs='+', arg_group='Action')
register_cli_argument('monitor alert update', 'condition', action=ConditionAction, nargs='+', arg_group='Condition')
register_cli_argument('monitor alert update', 'metric', arg_group='Condition')
register_cli_argument('monitor alert update', 'operator', arg_group='Condition', **enum_choice_list(operator_map.keys()))
register_cli_argument('monitor alert update', 'threshold', arg_group='Condition')
register_cli_argument('monitor alert update', 'aggregation', arg_group='Condition', **enum_choice_list(aggregation_map.keys()))
register_cli_argument('monitor alert update', 'period', type=period_type, arg_group='Condition')
register_resource_parameter('monitor alert update', 'target', 'Target Resource')

for item in ['show-incident', 'list-incidents']:
    register_cli_argument('monitor alert {}'.format(item), 'rule_name', options_list=['--rule-name'], id_part='name')
    register_cli_argument('monitor alert {}'.format(item), 'incident_name', name_arg_type, id_part='child_name')

register_cli_argument('monitor alert list-incidents', 'rule_name', options_list=['--rule-name'], id_part=None)

#  https://github.com/Azure/azure-rest-api-specs/issues/1017
register_cli_argument('monitor alert rule list', 'filter', ignore_type)

# endregion

with ParametersContext(command='monitor autoscale-settings') as c:
    c.register_alias('name', ('--azure-resource-name',))
    c.register_alias('autoscale_setting_name', ('--name', '-n'))

with ParametersContext(command='monitor autoscale-settings create') as c:
    c.register('parameters', ('--parameters',),
               type=get_json_object,
               help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                    'Use az autoscale-settings get-parameters-template to export json template.')

with ParametersContext(command='monitor autoscale-settings show') as c:
    c.argument('autoscale_setting_name', id_part='name')

with ParametersContext(command='monitor autoscale-settings delete') as c:
    c.argument('autoscale_setting_name', id_part='name')

#  https://github.com/Azure/azure-rest-api-specs/issues/1017
with ParametersContext(command='monitor autoscale-settings list') as c:
    c.ignore('filter')

with ParametersContext(command='monitor diagnostic-settings') as c:
    c.register_alias('resource_uri', ('--resource-id',))

with ParametersContext(command='monitor diagnostic-settings create') as c:
    c.register_alias('resource_group', ('--resource-group', '-g'))
    c.register_alias('target_resource_id', ('--resource-id',),
                     validator=validate_diagnostic_settings)
    c.register('logs', ('--logs',), type=get_json_object)
    c.register('metrics', ('--metrics',), type=get_json_object)
    c.argument('tags', nargs='*')

    # Service Bus argument group
    c.ignore('service_bus_rule_id')
    c.argument('namespace', arg_group='Service Bus')
    c.argument('rule_name', arg_group='Service Bus')

with ParametersContext(command='monitor log-profiles') as c:
    c.register_alias('log_profile_name', ('--name', '-n'))

with ParametersContext(command='monitor log-profiles create') as c:
    from azure.mgmt.monitor.models.log_profile_resource import LogProfileResource
    from azure.mgmt.monitor.models.retention_policy import RetentionPolicy

    c.register_alias('name', ('--log-profile-name',))
    c.expand('retention_policy', RetentionPolicy)
    c.expand('parameters', LogProfileResource)
    c.register_alias('name', ('--log-profile-resource-name',))
    c.register_alias('log_profile_name', ('--name', '-n'))
    c.argument('categories', nargs='+',
               help="Space separated categories of the logs.Some values are: "
                    "'Write', 'Delete', and/or 'Action.'")
    c.argument('locations', nargs='+',
               help="Space separated list of regions for which Activity Log events "
                    "should be stored.")

with ParametersContext(command='monitor metric-definitions list') as c:
    c.argument('metric_names', nargs='+')

with ParametersContext(command='monitor metrics list') as c:
    c.argument('metric_names', nargs='+', required=True)

with ParametersContext(command='monitor activity-log list') as c:
    c.register_alias('resource_group', ('--resource-group', '-g'))
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
