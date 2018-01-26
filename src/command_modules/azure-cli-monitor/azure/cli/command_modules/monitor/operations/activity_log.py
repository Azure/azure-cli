# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor.util import validate_time_range_and_add_defaults


def list_activity_log(client, filters=None, correlation_id=None, resource_group=None, resource_id=None,
                      resource_provider=None, start_time=None, end_time=None, caller=None, status=None, max_events=50,
                      select=None):
    """Provides the list of activity log.
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
    """
    if filters:
        odata_filters = filters
    else:
        from knack.util import CLIError
        collection = [correlation_id, resource_group, resource_id, resource_provider]
        if not _single(collection):
            raise CLIError("usage error: [--correlation-id ID | --resource-group NAME | "
                           "--resource-id ID | --resource-provider PROVIDER]")

        odata_filters = _build_activity_log_odata_filter(correlation_id, resource_group, resource_id, resource_provider,
                                                         start_time, end_time, caller, status)

    if max_events:
        max_events = int(max_events)

    select_filters = _activity_log_select_filter_builder(select)
    activity_log = client.list(filter=odata_filters, select=select_filters)
    return _limit_results(activity_log, max_events)


def _build_activity_log_odata_filter(correlation_id=None, resource_group=None, resource_id=None, resource_provider=None,
                                     start_time=None, end_time=None, caller=None, status=None):
    """Builds odata filter string.
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
    """
    formatter = "eventTimestamp ge {} and eventTimestamp le {}"
    odata_filters = validate_time_range_and_add_defaults(start_time, end_time, formatter=formatter)

    if correlation_id:
        odata_filters = _build_odata_filter(odata_filters, 'correlation_id', correlation_id, 'correlationId')
    elif resource_group:
        odata_filters = _build_odata_filter(odata_filters, 'resource_group', resource_group, 'resourceGroupName')
    elif resource_id:
        odata_filters = _build_odata_filter(odata_filters, 'resource_id', resource_id, 'resourceId')
    elif resource_provider:
        odata_filters = _build_odata_filter(odata_filters, 'resource_provider', resource_provider, 'resourceProvider')
    if caller:
        odata_filters = _build_odata_filter(odata_filters, 'caller', caller, 'caller')
    if status:
        odata_filters = _build_odata_filter(odata_filters, 'status', status, 'status')

    return odata_filters


def _activity_log_select_filter_builder(events=None):
    """Build up select filter string from events"""
    if events:
        return ' , '.join(events)
    return None


def _build_odata_filter(default_filter, field_name, field_value, field_label):
    if not field_value:
        from knack.util import CLIError
        raise CLIError('Value for {} can not be empty.'.format(field_name))

    return _add_condition(default_filter, field_label, field_value)


def _add_condition(default_filter, field_label, field_value):
    if not field_value:
        return default_filter

    return "{} and {} eq '{}'".format(default_filter, field_label, field_value)


def _single(collection):
    return len([x for x in collection if x]) == 1


def _limit_results(paged, limit):
    results = []
    for index, item in enumerate(paged):
        if index < limit:
            results.append(item)
        else:
            break
    return list(results)
