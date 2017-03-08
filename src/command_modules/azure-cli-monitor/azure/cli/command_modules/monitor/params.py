# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from ._util import ParametersContext

with ParametersContext(command='monitor alert-rules') as c:
    c.register_alias('name', ('--azure-resource-name',))
    c.register_alias('rule_name', ('--name', '-n'))

with ParametersContext(command='monitor alert-rule-incidents') as c:
    c.register_alias('incident_name', ('--name', '-n'))

with ParametersContext(command='monitor autoscale-settings') as c:
    c.register_alias('name', ('--azure-resource-name',))
    c.register_alias('autoscale_setting_name', ('--name', '-n'))

with ParametersContext(command='monitor alert-rules create') as c:
    from azure.mgmt.monitor.models.alert_rule_resource import AlertRuleResource

    c.expand('parameters', AlertRuleResource)
    c.register('condition', ('--condition',),
               type=json.loads,
               help='JSON encoded condition configuration. Use @{file} to load from a file.')

with ParametersContext(command='monitor service-diagnostic-settings') as c:
    c.register_alias('resource_uri', ('--resource-id',))

with ParametersContext(command='monitor service-diagnostic-settings create') as c:
    from azure.mgmt.monitor.models.service_diagnostic_settings_resource import \
        (ServiceDiagnosticSettingsResource)

    c.expand('parameters', ServiceDiagnosticSettingsResource)
    c.register_alias('resource_uri', ('--resource-id',))
    c.register('logs', ('--logs',),
               type=json.loads,
               help='JSON encoded list of logs settings. Use @{file} to load from a file.')
    c.register('metrics', ('--metrics',),
               type=json.loads,
               help='JSON encoded list of metric settings. Use @{file} to load from a file.')


with ParametersContext(command='monitor log-profiles') as c:
    c.register_alias('log_profile_name', ('--name', '-n'))

with ParametersContext(command='monitor log-profiles create') as c:
    from azure.mgmt.monitor.models.log_profile_resource import LogProfileResource

    c.register_alias('name', ('--log-profile-name',))
    c.expand('parameters', LogProfileResource)
    c.register('retention_policy', ('--retention-policy',),
               type=json.loads,
               help='JSON encoded retention policy settings. Use @{file} to load from a file.')
    c.register_alias('name', ('--log-profile-resource-name',))
    c.register_alias('log_profile_name', ('--name', '-n'))
    c.argument('categories', nargs='+',
               help="Space separated categories of the logs.Some values are: "
                    "'Write', 'Delete', and/or 'Action.'")
    c.argument('locations', nargs='+',
               help="Space separated list of regions for which Activity Log events "
                    "should be stored.")

with ParametersContext(command='monitor autoscale-settings create') as c:
    c.register('parameters', ('--parameters',),
               type=json.loads,
               help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                    'Use az autoscale-settings get-parameters-template to export json template.')

with ParametersContext(command='monitor metric-definitions list') as c:
    c.argument('metric_names', nargs='+')

with ParametersContext(command='monitor metrics list') as c:
    c.argument('metric_names', nargs='+')
    c.argument('metric_names', None, nargs='+')

with ParametersContext(command='monitor metrics list') as c:
    c.argument('metric_names', None, nargs='+')

with ParametersContext(command='monitor activity-logs list') as c:
    c.register_alias('resource_group', ('--resource-group', '-g'))
    c.argument('select', None, nargs='+')

with ParametersContext(command='monitor tenant-activity-logs list') as c:
    c.register_alias('resource_group', ('--resource-group', '-g'))
    c.argument('select', None, nargs='+')
