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


def list_activity_log(client, correlation_id=None):
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

    formatter = "eventTimestamp ge {} and eventTimestamp le {}"

    end_time = datetime.datetime.utcnow()

    start_time = end_time - datetime.timedelta(seconds=DEFAULT_QUERY_TIME_RANGE)

    odata_filters = formatter.format(start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                     end_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

    if correlation_id:
        odata_filters = "{} and {} eq '{}'".format(odata_filters, 'correlationId', correlation_id)

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.monitor import MonitorClient

    activity_log = get_mgmt_service_client(MonitorClient).activity_logs.list(filter=odata_filters)
    results = []
    for index, item in enumerate(activity_log):
        if index < 50:
            results.append(item)
        else:
            break
    return list(results)

