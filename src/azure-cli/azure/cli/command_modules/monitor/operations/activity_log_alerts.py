# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def process_condition_parameter(namespace):
    from azure.mgmt.monitor.models import ActivityLogAlertAllOfCondition
    from knack.util import CLIError

    try:
        expression = namespace.condition
        if expression is None:
            return
    except AttributeError:
        return

    error = 'incorrect usage: --condition requires an expression in the form of FIELD=VALIE[ and FIELD=VALUE...]'

    if not expression:
        raise CLIError(error)

    if len(expression) == 1:
        expression = [each.strip() for each in expression[0].split(' ')]
    elif isinstance(expression, list):
        expression = [each.strip() for each in expression]
    else:
        raise CLIError(error)

    if not expression or not len(expression) % 2:
        raise CLIError(error)

    # This is a temporary approach built on the assumption that there is only AND operators. Eventually, a proper
    # YACC will be created to parse complex condition expression.

    # Ensure all the string at even options are AND operator
    operators = [expression[i] for i in range(1, len(expression), 2)]
    if any([op != 'and' for op in operators]):
        raise CLIError(error)

    # Pick the strings at odd position and convert them into condition leaf.
    conditions = dict(_normalize_condition(expression[i]) for i in range(0, len(expression), 2))
    setattr(namespace, 'condition', ActivityLogAlertAllOfCondition(all_of=list(conditions.values())))


def list_activity_logs_alert(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription_id()


def create(cmd, client, resource_group_name, activity_log_alert_name, scopes=None, condition=None,
           action_groups=frozenset(), tags=None, disable=False, description=None, webhook_properties=None):
    from msrestazure.tools import resource_id
    from azure.mgmt.monitor.models import (ActivityLogAlertResource, ActivityLogAlertAllOfCondition,
                                           ActivityLogAlertLeafCondition, ActivityLogAlertActionList)
    from azure.mgmt.monitor.models import ActivityLogAlertActionGroup as ActionGroup
    from azure.cli.core.commands.client_factory import get_subscription_id
    from knack.util import CLIError

    if not scopes:
        scopes = [resource_id(subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name)]

    if _get_alert_settings(client, resource_group_name, activity_log_alert_name, throw_if_missing=False):
        raise CLIError('The activity log alert {} already exists in resource group {}.'.format(activity_log_alert_name,
                                                                                               resource_group_name))

    # Add alert conditions
    condition = condition or ActivityLogAlertAllOfCondition(
        all_of=[ActivityLogAlertLeafCondition(field='category', equals='ServiceHealth')])

    # Add action groups
    action_group_rids = _normalize_names(cmd.cli_ctx, action_groups, resource_group_name, 'microsoft.insights',
                                         'actionGroups')
    action_groups = [ActionGroup(action_group_id=i, webhook_properties=webhook_properties) for i in action_group_rids]
    alert_actions = ActivityLogAlertActionList(action_groups=action_groups)

    settings = ActivityLogAlertResource(location='global', scopes=scopes, condition=condition,
                                        actions=alert_actions, enabled=not disable, description=description, tags=tags)

    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name, activity_log_alert=settings)


def add_scope(client, resource_group_name, activity_log_alert_name, scopes, reset=False):
    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    new_scopes = set() if reset else set(settings.scopes)
    for scope in scopes:
        new_scopes.add(scope)

    settings.scopes = list(new_scopes)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def remove_scope(client, resource_group_name, activity_log_alert_name, scopes):
    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    new_scopes = set(settings.scopes)
    for scope in scopes:
        try:
            new_scopes.remove(scope)
        except KeyError:
            pass

    settings.scopes = list(new_scopes)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def add_action_group(cmd, client, resource_group_name, activity_log_alert_name, action_group_ids, reset=False,
                     webhook_properties=None, strict=False):
    from azure.mgmt.monitor.models import ActivityLogAlertActionGroup as ActionGroup

    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    # normalize the action group ids
    rids = _normalize_names(cmd.cli_ctx, action_group_ids, resource_group_name, 'microsoft.insights', 'actionGroups')

    if reset:
        action_groups = [ActionGroup(action_group_id=rid, webhook_properties=webhook_properties) for rid in rids]
    else:
        action_groups = dict((each.action_group_id, each) for each in settings.actions.action_groups)

        for rid in rids:
            if rid in action_groups and webhook_properties != action_groups[rid].webhook_properties and strict:
                raise ValueError('Fails to override webhook properties of action group {} in strict mode.'.format(rid))

            action_groups[rid] = ActionGroup(action_group_id=rid, webhook_properties=webhook_properties)
        action_groups = list(action_groups.values())

    settings.actions.action_groups = action_groups
    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def remove_action_group(cmd, client, resource_group_name, activity_log_alert_name, action_group_ids):
    settings = _get_alert_settings(client, resource_group_name, activity_log_alert_name)

    if len(action_group_ids) == 1 and action_group_ids[0] == '*':
        settings.actions.action_groups = []
    else:
        # normalize the action group ids
        rids = _normalize_names(cmd.cli_ctx, action_group_ids, resource_group_name, 'microsoft.insights',
                                'actionGroups')
        action_groups = [each for each in settings.actions.action_groups if each.action_group_id not in rids]
        settings.actions.action_groups = action_groups

    return client.create_or_update(resource_group_name=resource_group_name,
                                   activity_log_alert_name=activity_log_alert_name,
                                   activity_log_alert=settings)


def update(instance, condition=None, enabled=None, tags=None, description=None):
    if tags:
        instance.tags = tags

    if description:
        instance.description = description

    if enabled is not None:
        instance.enabled = enabled

    if condition is not None:
        instance.condition = condition

    return instance


# pylint: disable=inconsistent-return-statements
def _normalize_condition(condition_instance):
    from azure.mgmt.monitor.models import ActivityLogAlertLeafCondition

    if isinstance(condition_instance, str):
        try:
            field, value = condition_instance.split('=')
            return '{}={}'.format(field.lower(), value), ActivityLogAlertLeafCondition(field=field, equals=value)
        except ValueError:
            # too many values to unpack or not enough values to unpack
            raise ValueError('Condition "{}" does not follow format FIELD=VALUE'.format(condition_instance))
    elif isinstance(condition_instance, ActivityLogAlertLeafCondition):
        return '{}={}'.format(condition_instance.field.lower(), condition_instance.equals), condition_instance


def _normalize_names(cli_ctx, resource_names, resource_group, namespace, resource_type):
    """Normalize a group of resource names. Returns a set of resource ids. Throws if any of the name can't be correctly
    converted to a resource id."""
    from msrestazure.tools import is_valid_resource_id, resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    rids = set()
    # normalize the action group ids
    for name in resource_names:
        if is_valid_resource_id(name):
            rids.add(name)
        else:
            rid = resource_id(subscription=get_subscription_id(cli_ctx),
                              resource_group=resource_group,
                              namespace=namespace,
                              type=resource_type,
                              name=name)
            if not is_valid_resource_id(rid):
                raise ValueError('The resource name {} is not valid.'.format(name))
            rids.add(rid)

    return rids


def _get_alert_settings(client, resource_group_name, activity_log_alert_name, throw_if_missing=True):
    from azure.core.exceptions import HttpResponseError

    try:
        return client.get(resource_group_name=resource_group_name, activity_log_alert_name=activity_log_alert_name)
    except HttpResponseError as ex:
        from knack.util import CLIError
        if ex.status_code == 404:
            if throw_if_missing:
                raise CLIError('Can\'t find activity log alert {} in resource group {}.'.format(activity_log_alert_name,
                                                                                                resource_group_name))
            return None
        raise CLIError(ex.message)
