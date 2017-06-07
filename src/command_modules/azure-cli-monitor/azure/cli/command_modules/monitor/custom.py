# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import datetime
import os
from azure.cli.core.util import get_file_json, CLIError
from azure.mgmt.monitor.models import ConditionOperator, TimeAggregationOperator

# 1 hour in milliseconds
DEFAULT_QUERY_TIME_RANGE = 3600000

# ISO format with explicit indication of timezone
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# region Alerts

operator_map = {
    '>': ConditionOperator.greater_than.value,
    '>=': ConditionOperator.greater_than_or_equal.value,
    '<': ConditionOperator.less_than,
    '<=': ConditionOperator.less_than_or_equal
}


aggregation_map = {
    'avg': TimeAggregationOperator.average.value,
    'min': TimeAggregationOperator.minimum.value,
    'max': TimeAggregationOperator.maximum.value,
    'total': TimeAggregationOperator.total.value,
    'last': TimeAggregationOperator.last.value
}


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


def create_metric_rule(client, resource_group_name, rule_name, target, condition,
                       description=None, disabled=False, location=None, tags=None,
                       email_service_owners=False, actions=None):
    from azure.mgmt.monitor.models import AlertRuleResource, RuleEmailAction
    condition.data_source.resource_uri = target
    custom_emails, webhooks, _ = _parse_actions(actions)
    actions = [RuleEmailAction(email_service_owners, custom_emails)] + (webhooks or [])
    rule = AlertRuleResource(location, rule_name, not disabled,
                             condition, tags, description, actions)
    return client.create_or_update(resource_group_name, rule_name, rule)


def update_metric_rule(instance, target=None, condition=None, description=None, enabled=None,
                       metric=None, operator=None, threshold=None, aggregation=None, period=None,
                       tags=None, email_service_owners=None, add_actions=None, remove_actions=None):
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
        instance.condition.operator = operator_map[operator]
    if threshold is not None:
        instance.condition.threshold = threshold
    if aggregation is not None:
        instance.condition.time_aggregation = aggregation_map[aggregation]
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
    actions = [RuleEmailAction(email_service_owners, emails)] + webhooks
    instance.actions = actions

    return instance

# endregion


# pylint: disable=unused-argument
def list_metric_definitions(client, resource, resource_group_name=None, metric_names=None):
    '''Commands to manage metric definitions.
    :param str resource_id: The identifier of the resource
    :param str metric_names: The list of metric names
    '''
    odata_filter = _metric_names_filter_builder(metric_names)
    metric_definitions = client.list(resource, filter=odata_filter)
    return list(metric_definitions)


def _metric_names_filter_builder(metric_names=None):
    '''Build up OData filter string from metric_names
    '''
    filters = []
    if metric_names:
        for metric_name in metric_names:
            filters.append("name.value eq '{}'".format(metric_name))
    return ' or '.join(filters)


# pylint: disable=unused-argument
def list_metrics(client, resource, time_grain, resource_group_name=None,
                 start_time=None, end_time=None, metric_names=None):
    '''Lists the metric values for a resource.
    :param str resource_id: The identifier of the resource
    :param str time_grain: The time grain. Granularity of the metric data returned in ISO 8601
                           duration format, eg "PT1M"
    :param str start_time: The start time of the query. In ISO format with explicit indication of
                           timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500. Defaults to
                           1 Hour prior to the current time.
    :param str end_time: The end time of the query. In ISO format with explicit indication of
                         timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500. Defaults to
                         current time.
    :param str metric_names: The space separated list of metric names
    '''
    odata_filter = _metrics_odata_filter_builder(time_grain, start_time, end_time, metric_names)
    metrics = client.list(resource, filter=odata_filter)
    return list(metrics)


def _metrics_odata_filter_builder(time_grain, start_time=None, end_time=None,
                                  metric_names=None):
    '''Build up OData filter string
    '''
    filters = []
    metrics_filter = _metric_names_filter_builder(metric_names)
    if metrics_filter:
        filters.append('({})'.format(metrics_filter))

    if time_grain:
        filters.append("timeGrain eq duration'{}'".format(time_grain))

    filters.append(_validate_time_range_and_add_defaults(start_time, end_time))
    return ' and '.join(filters)


def _validate_time_range_and_add_defaults(start_time, end_time,
                                          formatter='startTime eq {} and endTime eq {}'):
    end_time = _validate_end_time(end_time)
    start_time = _validate_start_time(start_time, end_time)
    time_range = formatter.format(start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                  end_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
    return time_range


def _validate_end_time(end_time):
    result_time = datetime.datetime.utcnow()
    if isinstance(end_time, str):
        result_time = datetime.datetime.strptime(end_time, DATE_TIME_FORMAT)
    return result_time


def _validate_start_time(start_time, end_time):
    if not isinstance(end_time, datetime.datetime):
        raise ValueError("Input '{}' is not valid datetime. Valid example: 2000-12-31T12:59:59Z"
                         .format(end_time))

    result_time = end_time - datetime.timedelta(seconds=DEFAULT_QUERY_TIME_RANGE)

    if isinstance(start_time, str):
        result_time = datetime.datetime.strptime(start_time, DATE_TIME_FORMAT)

    now = datetime.datetime.utcnow()
    if result_time > now:
        raise ValueError("start_time '{}' is later than Now {}.".format(start_time, now))

    return result_time


def list_activity_log(client, filters=None, correlation_id=None, resource_group=None,
                      resource_id=None, resource_provider=None, start_time=None, end_time=None,
                      caller=None, status=None, max_events=50, select=None):
    '''Provides the list of activity log.
    :param str filters: The OData filter for the list activity logs. If this argument is provided
                        OData Filter Arguments will be ignored
    :param str correlation_id: The correlation id of the query
    :param str resource_group: The resource group
    :param str resource_id: The identifier of the resource
    :param str resource_provider: The resource provider
    :param str start_time: The start time of the query. In ISO format with explicit indication of
                           timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500. Defaults to
                           1 Hour prior to the current time.
    :param str end_time: The end time of the query. In ISO format with explicit indication of
                         timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500. Defaults to
                         current time.
    :param str caller: The caller to look for when querying
    :param str status: The status value to query (ex: Failed)
    :param str max_events: The maximum number of records to be returned by the command
    :param str select: The list of event names
    '''
    if filters:
        odata_filters = filters
    else:
        collection = [correlation_id, resource_group, resource_id, resource_provider]
        if not _single(collection):
            raise CLIError("usage error: [--correlation-id ID | --resource-group NAME | "
                           "--resource-id ID | --resource-provider PROVIDER]")

        odata_filters = _build_activity_log_odata_filter(correlation_id, resource_group,
                                                         resource_id, resource_provider,
                                                         start_time, end_time,
                                                         caller, status)

    if max_events:
        max_events = int(max_events)

    select_filters = _activity_log_select_filter_builder(select)
    activity_log = client.list(filter=odata_filters, select=select_filters)
    return _limit_results(activity_log, max_events)


def _single(collection):
    return len([x for x in collection if x]) == 1


def _build_activity_log_odata_filter(correlation_id=None, resource_group=None, resource_id=None,
                                     resource_provider=None, start_time=None, end_time=None,
                                     caller=None, status=None):
    '''Builds odata filter string.
    :param str correlation_id: The correlation id of the query
    :param str resource_group: The resource group
    :param str resource_id: The identifier of the resource
    :param str resource_provider: The resource provider
    :param str start_time: The start time of the query. In ISO format with explicit indication of
                           timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500
    :param str end_time: The end time of the query. In ISO format with explicit indication of
                         timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500.
    :param str caller: The caller to look for when querying
    :param str status: The status value to query (ex: Failed)
    '''
    formatter = "eventTimestamp ge {} and eventTimestamp le {}"
    odata_filters = _validate_time_range_and_add_defaults(start_time, end_time,
                                                          formatter=formatter)

    if correlation_id:
        odata_filters = _build_odata_filter(odata_filters, 'correlation_id',
                                            correlation_id, 'correlationId')
    elif resource_group:
        odata_filters = _build_odata_filter(odata_filters, 'resource_group',
                                            resource_group, 'resourceGroupName')
    elif resource_id:
        odata_filters = _build_odata_filter(odata_filters, 'resource_id',
                                            resource_id, 'resourceId')
    elif resource_provider:
        odata_filters = _build_odata_filter(odata_filters, 'resource_provider',
                                            resource_provider, 'resourceProvider')
    if caller:
        odata_filters = _build_odata_filter(odata_filters, 'caller',
                                            caller, 'caller')
    if status:
        odata_filters = _build_odata_filter(odata_filters, 'status',
                                            status, 'status')

    return odata_filters


def _activity_log_select_filter_builder(events=None):
    '''Build up select filter string from events
    '''
    if events:
        return ' , '.join(events)
    return None


def _build_odata_filter(default_filter, field_name, field_value, field_label):
    if not field_value:
        raise CLIError('Value for {} can not be empty.'.format(field_name))

    return _add_condition(default_filter, field_label, field_value)


def _add_condition(default_filter, field_label, field_value):
    if not field_value:
        return default_filter

    return "{} and {} eq '{}'".format(default_filter, field_label, field_value)


def _limit_results(paged, limit):
    results = []
    for index, item in enumerate(paged):
        if index < limit:
            results.append(item)
        else:
            break
    return list(results)


def scaffold_autoscale_settings_parameters(client):  # pylint: disable=unused-argument
    '''Scaffold fully formed autoscale-settings' parameters as json template
    '''
    # Autoscale settings parameter scaffold file path
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    autoscale_settings_parameter_file_path = os.path.join(
        curr_dir, 'autoscale-parameters-template.json')

    return _load_autoscale_settings_parameters(autoscale_settings_parameter_file_path)


def _load_autoscale_settings_parameters(file_path):
    if not os.path.exists(file_path):
        raise CLIError('File {} not found.'.format(file_path))

    return get_file_json(file_path)


# pylint: disable=unused-argument
def create_diagnostics_settings(client, target_resource_id, resource_group=None, logs=None,
                                metrics=None, namespace=None, rule_name=None, tags=None,
                                service_bus_rule_id=None, storage_account=None, workspace=None):
    from azure.mgmt.monitor.models.service_diagnostic_settings_resource import \
        ServiceDiagnosticSettingsResource

    # https://github.com/Azure/azure-rest-api-specs/issues/1058
    parameters = ServiceDiagnosticSettingsResource(location='',
                                                   storage_account_id=storage_account,
                                                   service_bus_rule_id=service_bus_rule_id,
                                                   metrics=metrics,
                                                   logs=logs,
                                                   workspace_id=workspace,
                                                   tags=tags)

    return client.create_or_update(target_resource_id, parameters)
