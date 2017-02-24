# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import datetime


# 1 hour in milliseconds
DEFAULT_QUERY_TIME_RANGE = 3600000

# ISO format with explicit indication of timezone
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def list_metric_definitions(client, resource_uri, metric_names=None):
    '''Commands to manage metric definitions.
    :param str resource_uri: The identifier of the resource
    :param str metric_names: The list of metric names
    '''
    odata_filter = _metric_names_filter_builder(metric_names)
    metric_definitions = client.list(resource_uri, filter=odata_filter)
    return list(metric_definitions)


def _metric_names_filter_builder(metric_names=None):
    '''Build up OData filter string from metric_names
    '''
    filters = []
    if metric_names:
        for metric_name in metric_names:
            filters.append("name.value eq '{}'".format(metric_name))
    return ' or '.join(filters)


def list_metrics(client, resource_uri, time_grain,
                 start_time=None, end_time=None, metric_names=None):
    '''Lists the metric values for a resource.
    :param str resource_uri: The identifier of the resource
    :param str time_grain: The time grain. Granularity of the metric data returned in ISO 8601
                           duration format, eg "PT1M"
    :param str start_time: The start time of the query. In ISO format with explicit indication of
                           timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500
    :param str end_time: The end time of the query. In ISO format with explicit indication of
                         timezone: 1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500
    :param str metric_names: The space separated list of metric names
    '''
    odata_filter = _metrics_odata_filter_builder(time_grain, start_time, end_time, metric_names)
    metrics = client.list(resource_uri, filter=odata_filter)
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


def _validate_time_range_and_add_defaults(start_time, end_time):
    end_time = _validate_end_time(end_time)
    start_time = _validate_start_time(start_time, end_time)
    time_range = "startTime eq {} and endTime eq {}".format(
        start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
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
