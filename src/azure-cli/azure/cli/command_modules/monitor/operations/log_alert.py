# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def create_log_alert(  # pylint: disable=too-many-locals
        client, resource_group_name, rule_name, location, frequency, time_window,
        data_source_id, alert_query,
        severity, threshold_operator, threshold, throttling=None,
        metric_column=None, metric_trigger_type=None, metric_threshold_operator=None, metric_threshold=None,
        action_group_ids=None, email_subject=None,
        query_type="ResultCount", authorized_resources=None, description=None, tags=None, disable=False):
    from azure.mgmt.monitor.models import (LogSearchRuleResource, Schedule, Source,
                                           TriggerCondition, AlertingAction, AzNsActionGroup, LogMetricTrigger)
    from knack.util import CLIError

    if _get_alert_settings(client, resource_group_name, rule_name, throw_if_missing=False):
        raise CLIError('The log alert rule {} already exists in resource group {}.'.format(rule_name,
                                                                                           resource_group_name))

    if metric_threshold or metric_column or metric_trigger_type or metric_threshold_operator:
        metric_trigger = LogMetricTrigger(metric_trigger_type=metric_trigger_type, metric_column=metric_column,
                                          threshold_operator=metric_threshold_operator, threshold=metric_threshold)
        trigger = TriggerCondition(threshold_operator=threshold_operator,
                                   threshold=threshold, metric_trigger=metric_trigger)
    else:
        trigger = TriggerCondition(threshold_operator=threshold_operator, threshold=threshold)

    action = AlertingAction(severity=severity, trigger=trigger, throttling_in_min=throttling,
                            azns_action=AzNsActionGroup(action_group=action_group_ids, email_subject=email_subject,
                                                        custom_webhook_payload=None))

    settings = LogSearchRuleResource(location=location, tags=tags, description=description, enabled=not disable,
                                     source=Source(query_type=query_type, data_source_id=data_source_id,
                                                   query=alert_query, authorized_resources=authorized_resources),
                                     schedule=Schedule(frequency_in_minutes=frequency,
                                                       time_window_in_minutes=time_window), action=action)
    return client.create_or_update(resource_group_name, rule_name, settings)


def list_log_alert(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription()


def update_log_alert(  # pylint: disable=too-many-locals
        instance, enabled=None, tags=None, description=None, frequency=None,
        time_window=None, alert_query=None, severity=None,
        threshold_operator=None, threshold=None, throttling=None,
        metric_column=None, metric_trigger_type=None, metric_threshold_operator=None, metric_threshold=None,
        email_subject=None, reset_email_subject=None, reset_metric_trigger=None):
    # --tags "" is set as tags={}. Used for clearing tags.
    if tags or tags == {}:
        instance.tags = tags

    if description:
        instance.description = description

    if frequency:
        instance.schedule.frequency_in_minutes = frequency

    if time_window:
        instance.schedule.time_window_in_minutes = time_window

    if alert_query:
        instance.source.query = alert_query

    if severity:
        instance.action.severity = severity

    if throttling:
        instance.action.throttling_in_min = throttling

    if threshold_operator:
        instance.action.trigger.threshold_operator = threshold_operator

    if threshold:
        instance.action.trigger.threshold = threshold

    if enabled is not None:
        instance.enabled = enabled

    if email_subject:
        instance.action.azns_action.email_subject = email_subject
    elif reset_email_subject:
        instance.action.azns_action.email_subject = None

    instance = update_metric_trigger(instance, metric_column, metric_trigger_type,
                                     metric_threshold_operator, metric_threshold, reset_metric_trigger)

    return instance


def update_metric_trigger(instance, metric_column=None, metric_trigger_type=None, metric_threshold_operator=None,
                          metric_threshold=None, reset_metric_trigger=None):
    from azure.mgmt.monitor.models import LogMetricTrigger
    if reset_metric_trigger:
        instance.action.trigger.metric_trigger = None
    elif metric_trigger_type or metric_column or metric_threshold_operator or metric_threshold:
        if instance.action.trigger.metric_trigger is not None:
            if metric_column:
                instance.action.trigger.metric_trigger.metric_column = metric_column

            if metric_trigger_type:
                instance.action.trigger.metric_trigger.metric_trigger_type = metric_trigger_type

            if metric_threshold_operator:
                instance.action.trigger.metric_trigger.threshold_operator = metric_threshold_operator

            if metric_threshold:
                instance.action.trigger.metric_trigger.threshold = metric_threshold
        else:
            instance.action.trigger.metric_trigger = LogMetricTrigger(metric_trigger_type=metric_trigger_type,
                                                                      metric_column=metric_column,
                                                                      threshold_operator=metric_threshold_operator,
                                                                      threshold=metric_threshold)

    return instance


def reset_action_group(client, resource_group_name, rule_name):
    settings = _get_alert_settings(client, resource_group_name, rule_name)
    settings.action.azns_action.action_group = None
    return client.create_or_update(resource_group_name, rule_name, settings)


def add_action_group(client, resource_group_name, rule_name, action_group_ids):
    settings = _get_alert_settings(client, resource_group_name, rule_name)

    if settings.action.azns_action.action_group is None:
        settings.action.azns_action.action_group = action_group_ids
    else:
        for action_group in action_group_ids:
            match = next(
                (x for x in settings.action.azns_action.action_group if action_group.lower() == x.lower()), None
            )
            if not match:
                settings.action.azns_action.action_group.append(action_group)

    return client.create_or_update(resource_group_name, rule_name, settings)


def remove_action_group(client, resource_group_name, rule_name, action_group_ids):
    from knack.util import CLIError

    settings = _get_alert_settings(client, resource_group_name, rule_name)

    if settings.action.azns_action.action_group is None:
        raise CLIError('Error in removing action group. There are no action groups attached to alert rule.')

    for action_group in action_group_ids:
        match = next(
            (x for x in settings.action.azns_action.action_group if action_group.lower() == x.lower()), None
        )
        if match:
            settings.action.azns_action.action_group.remove(action_group)
        else:
            raise CLIError(
                'Error in removing action group. Action group "{}" is not attached to alert rule.'
                .format(action_group))

    return client.create_or_update(resource_group_name, rule_name, settings)


def reset_authorized_resource(client, resource_group_name, rule_name):
    settings = _get_alert_settings(client, resource_group_name, rule_name)
    settings.action.azns_action.action_group = None
    return client.create_or_update(resource_group_name, rule_name, settings)


def add_authorized_resource(client, resource_group_name, rule_name, authorized_resources):
    settings = _get_alert_settings(client, resource_group_name, rule_name)

    if settings.source.authorized_resources is None:
        settings.source.authorized_resources = authorized_resources
    else:
        for authorized_resource in authorized_resources:
            match = next(
                (x for x in settings.source.authorized_resources if authorized_resource.lower() == x.lower()), None
            )
            if not match:
                settings.source.authorized_resources.append(authorized_resource)

    return client.create_or_update(resource_group_name, rule_name, settings)


def remove_authorized_resource(client, resource_group_name, rule_name, authorized_resources):
    from knack.util import CLIError
    settings = _get_alert_settings(client, resource_group_name, rule_name)
    if settings.source.authorized_resources is None:
        raise CLIError(
            'Error in removing authorized resource. There are no authorized resources attached to alert rule.')

    for authorized_resource in authorized_resources:
        match = next(
            (x for x in settings.source.authorized_resources if authorized_resource.lower() == x.lower()), None
        )
        if match:
            settings.source.authorized_resources.remove(authorized_resource)
        else:
            raise CLIError(
                'Error in removing authorized resource. Authorized resource "{}" is not attached to alert rule.'
                .format(authorized_resource))

    return client.create_or_update(resource_group_name, rule_name, settings)


def validate_action_group(cmd, namespace):
    """Normalize a group of resource names. Returns a set of resource ids. Throws if any of the name can't be correctly
    converted to a resource id."""
    from msrestazure.tools import is_valid_resource_id, resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    if namespace.action_group_ids:
        rids = set()
        # normalize the action group ids
        for name in namespace.action_group_ids:
            if is_valid_resource_id(name):
                rids.add(name)
            else:
                rid = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                  resource_group=namespace.resource_group_name,
                                  namespace='microsoft.insights',
                                  type='actionGroups',
                                  name=name)
                if not is_valid_resource_id(rid):
                    raise ValueError('The resource name {} is not valid.'.format(name))
                rids.add(rid)

        setattr(namespace, 'action_group_ids', rids)


def _get_alert_settings(client, resource_group_name, rule_name, throw_if_missing=True):
    from azure.mgmt.monitor.models import ErrorResponseException

    try:
        return client.get(resource_group_name=resource_group_name, rule_name=rule_name)
    except ErrorResponseException as ex:
        from knack.util import CLIError
        if ex.response.status_code == 404:
            if throw_if_missing:
                raise CLIError('Can\'t find log alert rule {} in resource group {}.'.format(rule_name,
                                                                                            resource_group_name))
            return None
        raise CLIError(ex.message)
