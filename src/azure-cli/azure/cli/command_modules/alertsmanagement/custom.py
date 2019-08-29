from azure.mgmt.alertsmanagement.models import (ActionRule,
                                                ActionGroup,
                                                Suppression,
                                                Diagnostics,
                                                Scope,
                                                Conditions,
                                                SuppressionConfig,
                                                SuppressionSchedule,
                                                )
from knack.util import CLIError


def cli_alertsmanagement_list_actionrule(client, resource_group_name=None,
                                         target_resource_group=None,
                                         target_resource_type=None,
                                         target_resource=None,
                                         severity=None,
                                         monitor_service=None,
                                         impacted_scope=None,
                                         description=None,
                                         alert_rule_id=None,
                                         action_group=None,
                                         name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name,
                                             target_resource_group,
                                             target_resource_type,
                                             target_resource,
                                             severity,
                                             monitor_service,
                                             impacted_scope,
                                             description,
                                             alert_rule_id,
                                             action_group,
                                             name)
    return client.list_by_subscription(target_resource_group,
                                       target_resource_type,
                                       target_resource,
                                       severity,
                                       monitor_service,
                                       impacted_scope,
                                       description,
                                       alert_rule_id,
                                       action_group,
                                       name)


def cli_alertsmanagement_set_actionrule(client,
                                        resource_group_name,
                                        name,
                                        status,
                                        scope,
                                        action_rule_type,
                                        recurrence_type,
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
                                        recurrence_values=None):
    if (action_rule_type not in ['ActionGroup', 'Suppression', 'Diagnostics']) or \
       (recurrence_type not in ['Always', 'Once', 'Daily', 'Weekly', 'Monthly']):
        raise CLIError("Invalid input value for --action-rule-type")

    action_rule = ActionRule(location="Global", tags={})

    if action_rule_type == 'ActionGroup' and action_group_id is not None:
        action_rule = ActionRule(
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
                                   action_group_id=action_group_id,
                                   description=description,
                                   status=status)
        )

    if action_rule_type == 'Suppression' and recurrence_type is not None:
        config = SuppressionConfig(recurrence_type=recurrence_type)
        if recurrence_type != 'Always':
            config.schedule = SuppressionSchedule(
                start_date=suppression_start_time.split(' ')[0],
                end_date=suppression_end_time.split(' ')[0],
                start_time=suppression_start_time.split(' ')[1],
                end_time=suppression_end_time.split(' ')[1])

            if recurrence_values:
                config.schedule.recurrence_values = recurrence_values.split(',')

        action_rule = ActionRule(
            location="Global",
            tags={},
            properties=Suppression(scope=parse_scope(scope),
                                   conditions=parse_conditions(severity_condition,
                                                               monitor_service_condition,
                                                               monitor_condition,
                                                               target_resource_type_condition,
                                                               alert_ruleId_condition,
                                                               description_condition,
                                                               alert_context_condition),
                                   description=description,
                                   status=status,
                                   suppression_config=config)
        )

    if action_rule_type == 'Diagnostics':
        action_rule = ActionRule(
            location="Global",
            tags={},
            properties=Diagnostics(scope=parse_scope(scope),
                                   conditions=parse_conditions(severity_condition,
                                                               monitor_service_condition,
                                                               monitor_condition,
                                                               target_resource_type_condition,
                                                               alert_ruleId_condition,
                                                               description_condition,
                                                               alert_context_condition),
                                   description=description,
                                   status=status)
        )

    return client.create_update(resource_group_name, name, action_rule)


def cli_alertsmanagement_update_actionrule(client,
                                           resource_group_name,
                                           name,
                                           status=None,
                                           tags=None):
    if status is None and tags is None:
        raise CLIError("Invalid input parameters-At least one of the properties 'status' or 'tags' need to be passed.")
    return client.update(resource_group_name, name, status, tags)


def parse_conditions(severity_condition=None,
                     monitor_service_condition=None,
                     monitor_condition=None,
                     target_resource_type_condition=None,
                     alert_ruleId_condition=None,
                     description_condition=None,
                     alert_context_condition=None):
    conditions = Conditions()
    if severity_condition is not None:
        conditions.Severity = Conditions(
            operatorProperty=severity_condition.split(':')[0],
            values=severity_condition.split(':')[1].split(',')
        )

    if monitor_service_condition is not None:
        conditions.MonitorService = Conditions(
            operatorProperty=monitor_service_condition.split(':')[0],
            values=monitor_service_condition.split(':')[1].split(',')
        )

    if monitor_condition is not None:
        conditions.MonitorCondition = Conditions(
            operatorProperty=monitor_condition.split(':')[0],
            values=monitor_condition.split(':')[1].split(',')
        )

    if target_resource_type_condition is not None:
        conditions.MonitorCondition = Conditions(
            operatorProperty=target_resource_type_condition.split(':')[0],
            values=target_resource_type_condition.split(':')[1].split(',')
        )

    if description_condition is not None:
        conditions.Description = Conditions(
            operatorProperty=description_condition.split(':')[0],
            values=description_condition.split(':')[1].split(',')
        )

    if alert_ruleId_condition is not None:
        conditions.AlertRuleId = Conditions(
            operatorProperty=alert_ruleId_condition.split(':')[0],
            values=alert_ruleId_condition.split(':')[1].split(',')
        )

    if alert_context_condition is not None:
        conditions.AlertContext = Conditions(
            operatorProperty=alert_context_condition.split(':')[0],
            values=alert_context_condition.split(':')[1].split(',')
        )

    return conditions


def parse_scope(scope):
    scope_values = scope.split(',')
    return Scope(
        scope_type=determine_scope_type_list(scope_values),
        values=scope_values
    )


def determine_scope_type_list(scope_values):
    if (scope_values is None or not scope_values):
        raise CLIError('Scope cannot be null or empty.')
    scope_type = determine_scope_type_string(scope_values[0])
    for value in scope_values:
        current = determine_scope_type_string(value)
        if current != scope_type:
            raise CLIError('Scope can either be list of Resource or ResourceGroup exclusively.')
    return scope_type


def determine_scope_type_string(value):
    tokens = value.split('/')
    scope_type = None
    if len(tokens) == 5:
        scope_type = "ResourceGroup"
    elif len(tokens) >= 9:
        scope_type = "Resource"
    else:
        raise CLIError('Scope is neither Resource or ResourceGroup type')

    return scope_type
