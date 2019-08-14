# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def create_log_alert(cmd, client, resource_group_name, rule_name, location, frequency, timeWindow,
                     dataSourceId, alertQuery, queryType,
                     severity, thresholdOperator, threshold, throttling=None,
                     metricColumn=None, metricTriggerType=None, metricThresholdOperator=None, metricThreshold=None,
                     actionGroup=None, customWebhookPayload=None, emailSubject=None,
                     authorizedResources=None, description=None, tags=None, disable=False):
    from azure.mgmt.monitor.models import (LogSearchRuleResource, Schedule, Source,
                                           TriggerCondition, AlertingAction, AzNsActionGroup, LogMetricTrigger)
    from knack.util import CLIError

    if _get_alert_settings(client, resource_group_name, rule_name, throw_if_missing=False):
        raise CLIError('The log alert rule {} already exists in resource group {}.'.format(rule_name,
                                                                                      resource_group_name))

    if metricThreshold or metricColumn or metricTriggerType or metricThresholdOperator:
        metricTrigger = LogMetricTrigger(metric_trigger_type=metricTriggerType, metric_column=metricColumn,
                                         threshold_operator=metricThresholdOperator, threshold=metricThreshold)
        trigger = TriggerCondition(threshold_operator=thresholdOperator,
                                   threshold=threshold, metric_trigger=metricTrigger)
    else:
        trigger = TriggerCondition(threshold_operator=thresholdOperator, threshold=threshold)

    if actionGroup:
        actionGroup = _normalize_names(cmd.cli_ctx, actionGroup, resource_group_name, 'microsoft.insights',
                                       'actionGroups')

    action = AlertingAction(severity=severity, trigger=trigger, throttling_in_min=throttling,
                            azns_action=AzNsActionGroup(action_group=actionGroup, email_subject=emailSubject,
                                                        custom_webhook_payload=customWebhookPayload))

    settings = LogSearchRuleResource(location=location, tags=tags, description=description, enabled=not disable,
                                     source=Source(query_type=queryType, data_source_id=dataSourceId,
                                                   query=alertQuery, authorized_resources=authorizedResources),
                                     schedule=Schedule(frequency_in_minutes=frequency,
                                                       time_window_in_minutes=timeWindow), action=action)
    return client.create_or_update(resource_group_name, rule_name, settings)


def list_log_alert(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription()


def update(cmd, instance, resource_group_name, enabled=None, tags=None, description=None, frequency=None,
           timeWindow=None, alertQuery=None, severity=None,
           thresholdOperator=None, threshold=None, throttling=None,
           metricColumn=None, metricTriggerType=None, metricThresholdOperator=None, metricThreshold=None,
           resetActionGroup=None, addActionGroups=None, removeActionGroups=None,
           customWebhookPayload=None, emailSubject=None, resetEmailSubject=None,
           resetCustomWebhookPayload=None, resetMetricTrigger=None, resetAuthorizedResources=None,
           addAuthorizedResources=None, removeAuthorizedResources=None):
    # --tags "" is set as tags={}. Used for clearing tags.
    if tags or tags == {}:
        instance.tags = tags

    if description:
        instance.description = description

    if frequency:
        instance.schedule.frequency_in_minutes = frequency

    if timeWindow:
        instance.schedule.time_window_in_minutes = timeWindow

    if alertQuery:
        instance.source.query = alertQuery

    if severity:
        instance.action.severity = severity

    if throttling:
        instance.action.throttling_in_min = throttling

    if thresholdOperator:
        instance.action.trigger.threshold_operator = thresholdOperator

    if threshold:
        instance.action.trigger.threshold = threshold

    if enabled is not None:
        instance.enabled = enabled

    if customWebhookPayload:
        instance.action.azns_action.custom_webhook_payload = customWebhookPayload
    elif resetCustomWebhookPayload:
        instance.action.azns_action.custom_webhook_payload = None

    if emailSubject:
        instance.action.azns_action.email_subject = emailSubject
    elif resetEmailSubject:
        instance.action.azns_action.email_subject = None

    instance = update_action_group(cmd, instance, resource_group_name, resetActionGroup, addActionGroups,
                                   removeActionGroups)

    instance = update_metric_trigger(instance, metricColumn, metricTriggerType,
                                     metricThresholdOperator, metricThreshold, resetMetricTrigger)

    instance = update_authorized_resources(instance, resetAuthorizedResources, addAuthorizedResources,
                                           removeAuthorizedResources)

    return instance


def update_metric_trigger(instance, metricColumn=None, metricTriggerType=None, metricThresholdOperator=None,
                          metricThreshold=None, resetMetricTrigger=None):
    from azure.mgmt.monitor.models import LogMetricTrigger
    if resetMetricTrigger:
        instance.action.trigger.metric_trigger = None
    elif metricTriggerType or metricColumn or metricThresholdOperator or metricThreshold:
        if instance.action.trigger.metric_trigger is not None:
            if metricColumn:
                instance.action.trigger.metric_trigger.metric_column = metricColumn

            if metricTriggerType:
                instance.action.trigger.metric_trigger.metric_trigger_type = metricTriggerType

            if metricThresholdOperator:
                instance.action.trigger.metric_trigger.threshold_operator = metricThresholdOperator

            if metricThreshold:
                instance.action.trigger.metric_trigger.threshold = metricThreshold
        else:
            instance.action.trigger.metric_trigger = LogMetricTrigger(metric_trigger_type=metricTriggerType, metric_column=metricColumn,
                                                                      threshold_operator=metricThresholdOperator,
                                                                      threshold=metricThreshold)

    return instance


def update_action_group(cmd, instance, resource_group, resetActionGroup=None, addActionGroups=None,
                        removeActionGroups=None):
    if resetActionGroup:
        instance.action.azns_action.action_group = None

    if addActionGroups:
        addActionGroups = _normalize_names(cmd.cli_ctx, addActionGroups, resource_group, 'microsoft.insights',
                                           'actionGroups')
        if instance.action.azns_action.action_group is None:
            instance.action.azns_action.action_group = addActionGroups
        else:
            for actionGroup in addActionGroups:
                match = next(
                    (x for x in instance.action.azns_action.action_group if actionGroup.lower() == x.lower()), None
                )
                if not match:
                    instance.action.azns_action.action_group.append(actionGroup)

    if removeActionGroups:
        removeActionGroups = _normalize_names(cmd.cli_ctx, removeActionGroups, resource_group, 'microsoft.insights',
                                              'actionGroups')
        from knack.util import CLIError
        if instance.action.azns_action.action_group is None:
            raise CLIError('Error in removing action group. There are no action groups attached to alert rule.')
        else:
            for actionGroup in removeActionGroups:
                match = next(
                    (x for x in instance.action.azns_action.action_group if actionGroup.lower() == x.lower()), None
                )
                if match:
                    instance.action.azns_action.action_group.remove(actionGroup)
                else:
                    raise CLIError('Error in removing action group. Action group "{}" is not attached to alert rule.'.format(actionGroup))

    return instance


def update_authorized_resources(instance, resetAuthorizedResources=None, addAuthorizedResources=None,
                                removeAuthorizedResources=None):
    if resetAuthorizedResources:
        instance.source.authorized_resources = None

    if addAuthorizedResources:
        if instance.source.authorized_resources is None:
            instance.source.authorized_resources = addAuthorizedResources
        else:
            for authorizedResources in addAuthorizedResources:
                match = next(
                    (x for x in instance.source.authorized_resources if authorizedResources.lower() == x.lower()), None
                )
                if not match:
                    instance.source.authorized_resources.append(authorizedResources)

    if removeAuthorizedResources:
        from knack.util import CLIError
        if instance.source.authorized_resources is None:
            raise CLIError('Error in removing authorized resource. There are no authorized resources attached to alert rule.')
        else:
            for authorizedResources in removeAuthorizedResources:
                match = next(
                    (x for x in instance.source.authorized_resources if authorizedResources.lower() == x.lower()), None
                )
                if match:
                    instance.source.authorized_resources.remove(authorizedResources)
                else:
                    raise CLIError('Error in removing authorized resource. Authorized resource "{}" is not attached to alert rule.'
                                   .format(authorizedResources))

    return instance


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
