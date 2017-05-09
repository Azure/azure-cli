# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.util import get_json_object
from azure.cli.command_modules.monitor.validators import (validate_diagnostic_settings)


with ParametersContext(command='monitor alert-rules') as c:
    c.register_alias('name', ('--azure-resource-name',))
    c.register_alias('rule_name', ('--name', '-n'))

with ParametersContext(command='monitor alert-rules create') as c:
    from azure.mgmt.monitor.models.alert_rule_resource import AlertRuleResource

    c.expand('parameters', AlertRuleResource)
    c.register('condition', ('--condition',),
               type=get_json_object,
               help='JSON encoded condition configuration. Use @{file} to load from a file.')
    c.register('actions', ('--actions',),
               type=get_json_object,
               help='JSON encoded array of actions that are performed when the alert '
                    'rule becomes active, and when an alert condition is resolved. '
                    'Use @{file} to load from a file.')

with ParametersContext(command='monitor alert-rules show') as c:
    c.argument('rule_name', id_part='name')

with ParametersContext(command='monitor alert-rules delete') as c:
    c.argument('rule_name', id_part='name')

#  https://github.com/Azure/azure-rest-api-specs/issues/1017
with ParametersContext(command='monitor alert-rules list') as c:
    c.ignore('filter')

with ParametersContext(command='monitor alert-rule-incidents') as c:
    c.register_alias('incident_name', ('--name', '-n'))

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
