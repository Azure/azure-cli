# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.command_modules.monitor.util import get_operator_map, get_aggregation_map


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
    flattened = list(set([x for sublist in actions for x in sublist]))
    emails = []
    webhooks = []
    for item in flattened:
        if item.startswith('http://') or item.startswith('https://'):
            webhooks.append(item)
        else:
            emails.append(item)
    return emails, webhooks
