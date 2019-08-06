from azure.mgmt.alertsmanagement.models import (ActionRule, ActionGroup, Suppression, Diagnostics)
from azure.cli.command_modules.alertsmanagement._client_factory import action_rules_mgmt_client_factory


def cli_alertsmanagement_list_by_subscription(client, resource_group_name,
                             name,
                             status,
                             scope,
                             action_rule_type,
                             reccurence_type,
                             action_group_id,
                             description=None,
                             severity_condition=None,
                             monitor_service_condition=None,
                             monitor_condition=None,
                             target_resource_type_condition=None,
                             alert_ruleId_condition=None,
                             description_condition=None,
                             alert_context_condition=None,
                             suppression_start_time=None,
                             suppression_end_time=None,
                             reccurent_value=None):
    #TODO: Pass into parameters
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()

def cli_alertsmanagement_set(client, resource_group_name,
                             name,
                             status,
                             scope,
                             action_rule_type,
                             reccurence_type,
                             action_group_id,
                             description=None,
                             severity_condition=None,
                             monitor_service_condition=None,
                             monitor_condition=None,
                             target_resource_type_condition=None,
                             alert_ruleId_condition=None,
                             description_condition=None,
                             alert_context_condition=None,
                             suppression_start_time=None,
                             suppression_end_time=None,
                             reccurent_value=None):
    
    result = ActionRule()
    client = action_rules_mgmt_client_factory()
    client.action_rule

    if action_rule_type == 'ActionGroup' and (scope!=None and action_group_id!=None and description!=None and status!=None):
        action_group_AR = ActionRule(
            location="Global",
            tags={},
            properties=ActionGroup(scope=parse_scope(scope),
                                   conditions=parse_conditions(severity_condition,
                                                               monitor_service_condition,
                                                               monitor_condition,
                                                               target_resource_type_condition,
                                                               alert_ruleId_condition,
                                                               description_condition,
                                                               alert_context_condition),
                                   actionGroupId = action_group_id,
                                   description=description,
                                   status = status)
            )
        """result = this.AlertsManagementClient.ActionRules.CreateUpdateWithHttpMessagesAsync(resourceGroupName: ResourceGroupName, actionRuleName: Name, actionRule: actionGroupAR).Result.Body;
           break;"""

    # Config and check if conditional statement for scope is to be added
    if action_rule_type == 'Suppression' and (suppression_start_time!=None and suppression_end_time!=None and description!=None and status!=None and reccurence_type!=None and reccurent_value!=None):
        config = SuppressionConfig(reccurenceType = reccurence_type)
        if reccurence_type != 'Always':
            config.schedule = SuppressionSchedule(
                startDate = suppression_start_time.split(' ')[0],
                endDate = suppression_end_time.split(' ')[0],
                startTime = suppression_start_time.split(' ')[1],
                endTime = supsuppression_end_time.split(' ')[1])
        
         #   if len(reccurent_value) > 0:
         #       config.Schedule.Rec
        suppression_AR = ActionRule(
            location="Global",
            tags={},
            properties=ActionGroup(scope=parse_scope(scope),
                                   conditions=parse_conditions(severity_condition,
                                                               monitor_service_condition,
                                                               monitor_condition,
                                                               target_resource_type_condition,
                                                               alert_ruleId_condition,
                                                               description_condition,
                                                               alert_context_condition),
                                   description=description,
                                   status = status,
                                   suppressionConfig = config)
            )


    if action_rule_type == 'Diagnostics' and (description!=None and status!=None):
        diagnostics_AR = ActionRule(
            location="global",
            tags = {},
            properties=Diagnostics(scope=parse_scope(scope),
                                   conditions=parse_conditions(severity_condition,
                                                               monitor_service_condition,
                                                               monitor_condition,
                                                               target_resource_type_condition,
                                                               alert_ruleId_condition,
                                                               description_condition,
                                                               alert_context_condition),
                description=description,
                status=status
                )
            )


def parse_conditions(severity_condition=None,
                             monitor_service_condition=None,
                             monitor_condition=None,
                             target_resource_type_condition=None,
                             alert_ruleId_condition=None,
                             description_condition=None,
                             alert_context_condition=None):
    conditions = Conditions()
    if severity_condition != None:
        conditions.Severity = Conditions(
            operatorProperty = severity_condition.split(':')[0],
             values = severity_condition.split(':')[1].split(',')
            )

    if monitor_service_condition != None:
        conditions.MonitorService = Conditions(
            operatorProperty = monitor_service_condition.split(':')[0],
             values = monitor_service_condition.split(':')[1].split(',')
            )

    if monitor_condition != None:
        conditions.MonitorCondition  = Conditions(
            operatorProperty = monitor_condition.split(':')[0],
             values = monitor_condition.split(':')[1].split(',')
            )

    if target_resource_type_condition != None:
        conditions.MonitorCondition = Conditions(
            operatorProperty = target_resource_type_condition.split(':')[0],
             values = target_resource_type_condition.split(':')[1].split(',')
            )

    if description_condition != None:
        conditions.Description = Conditions(
            operatorProperty = description_condition.split(':')[0],
             values = description_condition.split(':')[1].split(',')
            )

    if alert_ruleId_condition != None:
        conditions.AlertRuleId = Conditions(
            operatorProperty = alert_ruleId_condition.split(':')[0],
             values = alert_ruleId_condition.split(':')[1].split(',')
            )

    if alert_context_condition != None:
        conditions.AlertContext = Conditions(
            operatorProperty = alert_context_condition.split(':')[0],
             values = alert_context_condition.split(':')[1].split(',')
            )

    return condition



def parse_scope(scope):
    return Scope(
        scopeType = determine_scope_type_list(scope),
        values = scope
        )


def determine_scope_type_list(scope_values):
    if scope_values == None or len(scope_values) == 0:
        raise TypeError()
    else:
        scope_type = determine_scope_type_string(scope_values[0])
        for value in scope_values:
            current = determine_scope_type_string(value)
            if current != scope_type:
                raise TypeError()
    
        return scope_type


def determine_scope_type_string(value):
    tokens = value.split('/')
    if len(tokens) == 5 or len(tokens) >= 9:
        return ScopeType.ResourceGroup
    else:
        raise TypeError()