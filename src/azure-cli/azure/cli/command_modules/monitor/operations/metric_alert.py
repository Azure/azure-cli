# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor.util import get_operator_map, get_aggregation_map

from knack.log import get_logger

logger = get_logger(__name__)


def create_metric_alert(client, resource_group_name, rule_name, scopes, condition, disabled=False, description=None,
                        tags=None, actions=None, severity=2, window_size='5m', evaluation_frequency='1m',
                        auto_mitigate=None):
    from azure.mgmt.monitor.models import (MetricAlertResource,
                                           MetricAlertSingleResourceMultipleMetricCriteria,
                                           MetricAlertMultipleResourceMultipleMetricCriteria)
    # generate names for the conditions
    for i, cond in enumerate(condition):
        cond.name = 'cond{}'.format(i)
    criteria = None
    target_resource_type = None
    target_resource_region = None
    if len(scopes) == 1:
        criteria = MetricAlertSingleResourceMultipleMetricCriteria(all_of=condition)
    else:
        criteria = MetricAlertMultipleResourceMultipleMetricCriteria(all_of=condition)
        target_resource_type = _parse_resource_type(scopes)
        target_resource_region = 'global'
    kwargs = {
        'description': description,
        'severity': severity,
        'enabled': not disabled,
        'scopes': scopes,
        'evaluation_frequency': evaluation_frequency,
        'window_size': window_size,
        'criteria': criteria,
        'target_resource_type': target_resource_type,
        'target_resource_region': target_resource_region,
        'actions': actions,
        'tags': tags,
        'location': 'global',
        'auto_mitigate': auto_mitigate
    }
    return client.create_or_update(resource_group_name, rule_name, MetricAlertResource(**kwargs))


def update_metric_alert(instance, scopes=None, description=None, enabled=None, tags=None,
                        severity=None, window_size=None, evaluation_frequency=None, auto_mitigate=None,
                        add_actions=None, remove_actions=None, add_conditions=None, remove_conditions=None):
    if scopes is not None:
        instance.scopes = scopes
    if description is not None:
        instance.description = description
    if enabled is not None:
        instance.enabled = enabled
    if tags is not None:
        instance.tags = tags
    if severity is not None:
        instance.severity = severity
    if window_size is not None:
        instance.window_size = window_size
    if evaluation_frequency is not None:
        instance.evaluation_frequency = evaluation_frequency
    if auto_mitigate is not None:
        instance.auto_mitigate = auto_mitigate

    # process action removals
    if remove_actions is not None:
        instance.actions = [x for x in instance.actions if x.action_group_id.lower() not in remove_actions]

    # process action additions
    if add_actions is not None:
        for action in add_actions:
            match = next(
                (x for x in instance.actions if action.action_group_id.lower() == x.action_group_id.lower()), None
            )
            if match:
                match.webhook_properties = action.webhook_properties
            else:
                instance.actions.append(action)

    # process condition removals
    if remove_conditions is not None:
        instance.criteria.all_of = [x for x in instance.criteria.all_of if x.name not in remove_conditions]

    def _get_next_name():
        i = 0
        while True:
            possible_name = 'cond{}'.format(i)
            match = next((x for x in instance.criteria.all_of if x.name == possible_name), None)
            if match:
                i = i + 1
                continue
            return possible_name

    # process condition additions
    if add_conditions is not None:
        for condition in add_conditions:
            condition.name = _get_next_name()
            instance.criteria.all_of.append(condition)

    return instance


def list_metric_alerts(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()


def create_metric_rule(client, resource_group_name, rule_name, target, condition, description=None, disabled=False,
                       location=None, tags=None, email_service_owners=False, actions=None):
    from azure.mgmt.monitor.models import AlertRuleResource, RuleEmailAction
    condition.data_source.resource_uri = target
    custom_emails, webhooks, _ = _parse_actions(actions)
    actions = [
        RuleEmailAction(send_to_service_owners=email_service_owners, custom_emails=custom_emails)
    ] + (webhooks or [])
    rule = AlertRuleResource(
        location=location, alert_rule_resource_name=rule_name, is_enabled=not disabled,
        condition=condition, tags=tags, description=description, actions=actions)
    return client.create_or_update(resource_group_name, rule_name, rule)


def update_metric_rule(instance, target=None, condition=None, description=None, enabled=None, metric=None,
                       operator=None, threshold=None, aggregation=None, period=None, tags=None,
                       email_service_owners=None, add_actions=None, remove_actions=None):
    # Update general properties
    if description is not None:
        instance.description = description
    if enabled is not None:
        instance.is_enabled = enabled
    if tags is not None:
        instance.tags = tags

    # Update conditions
    if condition is not None:
        target = target or instance.condition.data_source.resource_uri
        instance.condition = condition

    if metric is not None:
        instance.condition.data_source.metric_name = metric
    if operator is not None:
        instance.condition.operator = get_operator_map()[operator]
    if threshold is not None:
        instance.condition.threshold = threshold
    if aggregation is not None:
        instance.condition.time_aggregation = get_aggregation_map()[aggregation]
    if period is not None:
        instance.condition.window_size = period

    if target is not None:
        instance.condition.data_source.resource_uri = target

    # Update actions
    emails, webhooks, curr_email_service_owners = _parse_actions(instance.actions)

    # process removals
    if remove_actions is not None:
        removed_emails, removed_webhooks = _parse_action_removals(remove_actions)
        emails = [x for x in emails if x not in removed_emails]
        webhooks = [x for x in webhooks if x.service_uri not in removed_webhooks]

    # process additions
    if add_actions is not None:
        added_emails, added_webhooks, _ = _parse_actions(add_actions)
        emails = list(set(emails) | set(added_emails))
        webhooks = webhooks + added_webhooks

    # Replace the existing actions array. This potentially restructures rules that were created
    # via other methods (Portal, ARM template). However, the functionality of these rules should
    # be the same.
    from azure.mgmt.monitor.models import RuleEmailAction
    if email_service_owners is None:
        email_service_owners = curr_email_service_owners
    actions = [RuleEmailAction(send_to_service_owners=email_service_owners, custom_emails=emails)] + webhooks
    instance.actions = actions

    return instance


def _parse_actions(actions):
    """ Actions come in as a combined list. This method separates the webhook actions into a
        separate collection and combines any number of email actions into a single email collection
        and a single value for `email_service_owners`. If any email action contains a True value
        for `send_to_service_owners` then it is assumed the entire value should be True. """
    from azure.mgmt.monitor.models import RuleEmailAction, RuleWebhookAction
    actions = actions or []
    email_service_owners = None
    webhooks = [x for x in actions if isinstance(x, RuleWebhookAction)]
    custom_emails = set()
    for action in actions:
        if isinstance(action, RuleEmailAction):
            if action.send_to_service_owners:
                email_service_owners = True
            custom_emails = custom_emails | set(action.custom_emails)
    return list(custom_emails), webhooks, email_service_owners


def _parse_action_removals(actions):
    """ Separates the combined list of keys to remove into webhooks and emails. """
    flattened = list({x for sublist in actions for x in sublist})
    emails = []
    webhooks = []
    for item in flattened:
        if item.startswith('http://') or item.startswith('https://'):
            webhooks.append(item)
        else:
            emails.append(item)
    return emails, webhooks


def _parse_resource_type(scopes):
    from msrestazure.tools import parse_resource_id
    from azure.cli.core import CLIError
    namespace = None
    resource_type = None
    for item in scopes:
        item_namespace = parse_resource_id(item)['namespace']
        item_resource_type = parse_resource_id(item)['resource_type']
        if namespace is None and resource_type is None:
            namespace = item_namespace
            resource_type = item_resource_type
        else:
            if namespace != item_namespace or resource_type != item_resource_type:
                raise CLIError('Multiple scopes should be the same resource type.')
    return namespace + '/' + resource_type
