from knack.arguments import CLIArgumentType


def load_arguments(self, _):
    target_resource_arg_type = CLIArgumentType(options_list=['--target-resource'], help='Filter by target resource id',
                                               metavar='TARGET_RESOURCE')
    target_resource_type_arg_type = CLIArgumentType(options_list=['--target-resource-type'],
                                                    help='Filter by target resource type',
                                                    metavar='TARGET_RESOURCE_TYPE')
    target_resource_group_arg_type = CLIArgumentType(options_list=['--target-resource-group'],
                                                     help='Filter by resource group',
                                                     metavar='TARGET_RESOURCE_GROUP')
    monitor_service_arg_type = CLIArgumentType(options_list=['--monitor-service'], help='Filter by target resource',
                                               metavar='MONITOR_SERVICE')
    monitor_condition_arg_type = CLIArgumentType(options_list=['--monitor-condition'],
                                                 help='Filter by monitor condition. Supported values – Fired, Resolved',
                                                 metavar='MONITOR_CONDITION')
    severity_arg_type = CLIArgumentType(options_list=['--severity'],
                                        help='Filter by severity. Supported values – Sev0, Sev1, Sev2, Sev3, Sev4',
                                        metavar='SEVERITY')
    state_arg_type = CLIArgumentType(options_list=['--state'],
                                     help='Filter by alert state. Supported values - New, Acknowledged, Closed',
                                     metavar='STATE')
    alert_rule_arg_type = CLIArgumentType(options_list=['--alert-rule'], help='Filter by alert rule Id',
                                          metavar='ALERT_RULE')
    smart_group_id_arg_type = CLIArgumentType(options_list=['--smart-group-id'], help='Filter by smart group Id',
                                              metavar='SMART_GROUP_ID')
    sortby_arg_type = CLIArgumentType(options_list=['--sort-by'],
                                      help='Sort the results by parameter. Supported values – name, ' +
                                      'severity, alertState, monitorCondition, targetResource, targetResourceName,' +
                                      ' targetResourceGroup, targetResourceType, startDateTime, lastModifiedDateTime',
                                      metavar='SORT_BY')
    sort_order_arg_type = CLIArgumentType(options_list=['--sort-order'],
                                          help='Sorting order. Supported values – asc, desc',
                                          metavar='SORT_ORDER')
    time_range_arg_type = CLIArgumentType(options_list=['--time-range'],
                                          help='Supported time range values – 1h, 1d, 7d, 30d (Default is 1d)',
                                          metavar='TIME_RANGE')
    custom_time_range_arg_type = CLIArgumentType(options_list=['--custom-time-range'],
                                                 help='Supported format - <start-time>/<end-time>' +
                                                 ' where time is in ISO-8601 format',
                                                 metavar='CUSTOM_TIME_RANGE')
    resource_group_name_arg_type = CLIArgumentType(options_list=['--resource-group-name'],
                                                   help='Resource group in which action rule reside',
                                                   metavar='RESOURCE_GROUP_NAME')

    with self.argument_context('alertsmanagement alert list') as c:
        c.argument('target_resource', target_resource_arg_type, required=False)
        c.argument('target_resource_type', target_resource_type_arg_type, required=False)
        c.argument('target_resource_group', target_resource_group_arg_type, required=False)
        c.argument('monitor_service', monitor_service_arg_type, required=False)
        c.argument('monitor_condition', monitor_condition_arg_type, required=False)
        c.argument('severity', severity_arg_type, required=False)
        c.argument('alert_state', state_arg_type, required=False)
        c.argument('alert_rule', alert_rule_arg_type, required=False)
        c.argument('smart_group_id', smart_group_id_arg_type, required=False)
        c.argument('include_context', options_list=['--include-context'], required=False,
                   help='Include Context in response. Supported values – true, false')
        c.argument('include_egress_config', options_list=['--include-egress-config'], required=False,
                   help='Include Egress config in response. Supported values – true, false')
        c.argument('page_count', options_list=['--page-count'], required=False,
                   help='Number of alerts returned at once.')
        c.argument('sortby', sortby_arg_type, required=False)
        c.argument('sort_order', sort_order_arg_type, required=False)
        c.argument('time_range', time_range_arg_type, required=False)
        c.argument('custom_time_range', custom_time_range_arg_type, required=False)
        c.argument('select', options_list=['--select'], required=False,
                   help='Project the required fields out of essentials. Expected input is comma-separated. ')

    with self.argument_context('alertsmanagement alert show') as c:
        c.argument('alert_id', options_list=['--alert-id'], required=True, help='Alert Id to be fetched')

    with self.argument_context('alertsmanagement alert list-summary') as c:
        c.argument('groupby', options_list=['--group-by'], required=True,
                   help='Supported values – severity, alertState,' +
                   ' monitorCondition, monitorService, signalType, alertRule')
        c.argument('include_smart_groups_count', options_list=['--include-smart-groups-count'],
                   required=False,
                   help='Supported values - true or false')
        c.argument('target_resource', target_resource_arg_type, required=False)
        c.argument('target_resource_type', target_resource_type_arg_type, required=False)
        c.argument('target_resource_group', options_list=['--target-resource-group'],
                   required=False, help='Filter by resource group')
        c.argument('monitor_service', monitor_service_arg_type, required=False)
        c.argument('monitor_condition', monitor_condition_arg_type, required=False)
        c.argument('severity', severity_arg_type, required=False)
        c.argument('state', state_arg_type, required=False)
        c.argument('alert_rule', alert_rule_arg_type, required=False)
        c.argument('time_range', time_range_arg_type, required=False)
        c.argument('custom_time_range', custom_time_range_arg_type, required=False)

    with self.argument_context('alertsmanagement alert show-history') as c:
        c.argument('alert_id', options_list=['--alert-id'], required=True, help='Id of the alert to fetch it’s history')

    with self.argument_context('alertsmanagement smart-group list') as c:
        c.argument('sort_by', sortby_arg_type, required=False)
        c.argument('sort_order', sort_order_arg_type, required=False)
        c.argument('time_range', time_range_arg_type, required=False)

    with self.argument_context('alertsmanagement  smart-group show') as c:
        c.argument('smart_group_id', smart_group_id_arg_type, required=True)

    with self.argument_context('alertsmanagement  smart-group show-history') as c:
        c.argument('smart_group_id', smart_group_id_arg_type, required=True)

    with self.argument_context('alertsmanagement action-rule list') as c:
        c.argument('resource_group_name', resource_group_name_arg_type, required=False)
        c.argument('target_resource', target_resource_arg_type, required=False)
        c.argument('target_resource_type', target_resource_type_arg_type, required=False)
        c.argument('target_resource_group', target_resource_group_arg_type, required=False)
        c.argument('severity', severity_arg_type, required=False)
        c.argument('monitor_service', monitor_service_arg_type, required=False)
        c.argument('impacted_scope', options_list=['--impacted-scope'], required=False,
                   help='Gets all actions rules in a subscription filter by impacted scope')
        c.argument('description', options_list=['--description'], required=False,
                   help='Gets all actions rules in a subscription filter by description')
        c.argument('alert_rule', alert_rule_arg_type, required=False)
        c.argument('action_group', options_list=['--action-group'], required=False,
                   help='Gets all actions rules in a subscription filter by action group')
        c.argument('name', options_list=['--name'], required=False,
                   help='Gets all actions rules in a subscription filter by action rule name')

    with self.argument_context('alertsmanagement action-rule show') as c:
        c.argument('resource_group_name', resource_group_name_arg_type, required=True)
        c.argument('action_rule_name', options_list=['--name'], required=True, help='Name of action rule')

    with self.argument_context('alertsmanagement action-rule set') as c:
        c.argument('resource_group_name', resource_group_name_arg_type, required=True)
        c.argument('name', options_list=['--name'], required=True, help='Unique name for action rule')
        c.argument('description', options_list=['--description'], required=False, help='Description of Action Rule')
        c.argument('status', options_list=['--status'], required=True, help='Status of Action Rule')
        c.argument('scope', options_list=['--scope'], required=True, help='Comma separated list of values')
        c.argument('severity_condition', options_list=['--severity-condition'], required=False,
                   help='Expected format - {<operation>:<comma separated list of values>} For eg. Equals:Sev0,Sev1')
        c.argument('monitor_service_condition', options_list=['--monitor-service-condition'], required=False,
                   help='Expected format - {<operation>:<comma separated list of values>}' +
                   ' For eg. Equals:Platform,Log Analytics')
        c.argument('monitor_condition', monitor_condition_arg_type, required=False)
        c.argument('target_resource_type_condition', options_list=['--target-resource-type-condition'], required=False,
                   help='Expected format - {<operation>:<comma separated list of values>}' +
                   ' For eg. Contains:Virtual Machines,Storage Account')
        c.argument('alert_ruleId_condition', options_list=['--alert-ruleId-condition'], required=False,
                   help='Expected format - {<operation>:<comma separated list of values>}' +
                   ' For eg. Equals:ARM_ID_1,ARM_ID_2')
        c.argument('description_condition', options_list=['--description-condition'], required=False,
                   help='Expected format - {<operation>:<comma separated list of values>}' +
                   ' For eg. Contains:Test Alert')
        c.argument('alert_context_condition', options_list=['--alert-context-condition'], required=False,
                   help='Expected format - {<operation>:<comma separated list of values>} For eg. Contains:smartgroups')
        c.argument('action_rule_type', options_list=['--action-rule-type'], required=True, help='Action rule Type')
        c.argument('recurrence_type', options_list=['--recurrence-type'], required=False,
                   help='Specifies the duration when the suppression should be applied')
        c.argument('suppression_start_time', options_list=['--suppression-start-time'], required=False,
                   help='Suppression Start Time. Format 12/09/2018 06:00:00' +
                   ' Should be mentioned in case of Reccurent Supression Schedule - Once, Daily, Weekly or Monthly')
        c.argument('suppression_end_time', options_list=['--suppression-end-time'], required=False,
                   help='Suppression End Time. Format 12/09/2018 06:00:00' +
                   ' Should be mentioned in case of Reccurent Supression Schedule - Once, Daily, Weekly or Monthly')
        c.argument('recurrence_values', options_list=['--recurrence-values'], required=False,
                   help='Reccurent values, if applicable. In case of Weekly - 1,3,5 In case of Monthly - 16,24,28')
        c.argument('action_group_id', options_list=['--action-group-id'], required=False,
                   help='Action Group Id which is to be notified')

    with self.argument_context('alertsmanagement alert update-state') as c:
        c.argument('alert_id', options_list=['--alert-id'], required=True, help='Id of alert to be updated')
        c.argument('new_state', state_arg_type, required=True)

    with self.argument_context('alertsmanagement smart-group update-state') as c:
        c.argument('smart_group_id', smart_group_id_arg_type, required=True)
        c.argument('new_state', state_arg_type, required=True)

    with self.argument_context('alertsmanagement action-rule update') as c:
        c.argument('resource_group_name', resource_group_name_arg_type, required=True)
        c.argument('action_rule_name', options_list=['--name'], required=True,
                   help='Unique name of action rule to be updated')
        c.argument('status', options_list=['--status'], required=False, help='Status of Action Rule')
        c.argument('tags', options_list=['--tags'], required=False, help='List of Azure Resource Tag')

    with self.argument_context('alertsmanagement action-rule delete') as c:
        c.argument('resource_group_name', resource_group_name_arg_type, required=True)
        c.argument('action_rule_name', options_list=['--name'], required=True,
                   help='Unique name of action rule to be deleted')
