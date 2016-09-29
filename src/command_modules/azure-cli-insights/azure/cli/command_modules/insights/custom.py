#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
from datetime import datetime, timedelta

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.insights.sdk.insightsclient import InsightsClient
from azure.cli.command_modules.insights.sdk.insightsclient.operations import \
    (EventOperations)

def _insights_client_factory(client):
    return get_mgmt_service_client(client)

def _limit_results(paged, limit):
    results = []
    for index, item in enumerate(paged):
        if index < limit:
            results.append(item)
        else:
            break
    return results

def list_events(start_time=None, end_time=None, limit=50, status=None, caller=None,
                select=None, resource_group_name=None, correlation_id=None, resource_id=None,
                resource_provider=None):
    ''' List events. By default, returns a subset of properties for events which occurred over
        the past hour.
        :param start_time: The start time of the query. Defaults to one hour before current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param end_time: The end time of the query. Defaults to current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param status: Status value to query (ex: Failed).
        :param caller: Caller to query on (ex: yourname@onmicrosoft.com)
        :param select: Space-separated list of properties to return. Defaults to a reasonable
        subset of fields. Specify "*" to return all fields. Fields not selected will still appear
        with 'null' values.
        :param resource_id: Filter by resource ID.
        :param resource_provider: Filter by resource provider.
        :param correlation_id: Filter correlation ID.
        :param limit: Maximum number of events to return.
    '''
    client =  _insights_client_factory(InsightsClient).event

    count = 0
    for x in [correlation_id, resource_group_name, resource_id, resource_provider]:
        count = count + (1 if x else 0)

    if count > 1:
        raise CLIError("'--correlation-id', '--resource-group', '--resource-id' and '--resource-provider' are mutually exclusive.")

    filters = []
    # retrieve last hours worth of logs if not specified
    filters.append('eventTimestamp ge {}'.format(start_time if start_time else datetime.now() - timedelta(hours=1)))
    filters.append('eventTimestamp le {}'.format(end_time if end_time else datetime.now()))
    if caller:
        filters.append("caller eq '{}'".format(caller))
    if status:
        filters.append("status eq '{}'".format(status))
    if correlation_id:
        filters.append("correlationId eq '{}'".format(correlation_id))
    if resource_group_name:
        filters.append("resourceGroupName eq '{}'".format(resource_group_name))
    if resource_id:
        filters.append("resourceId eq '{}'".format(resource_id))
    if resource_provider:
        filters.append("resourceProvider eq '{}'".format(resource_provider))
    filter_string = ' and '.join(filters)
    default_select = ['Authorization', 'Caller', 'CorrelationId', 'EventTimestamp', 'OperationName',
                      'ResourceGroupName', 'ResourceId', 'Status', 'SubscriptionId', 'SubStatus']
    select_string = ','.join(select) if select else ','.join(default_select)
    if select and '*' in select:
        select_string = None
    return _limit_results(client.list(filter=filter_string, select=select_string), limit)

def list_digest_events(start_time=None, end_time=None, limit=50, select=None):
    ''' List digest events. By default, returns a subset of properties for events which occurred
        over the past hour.
        :param start_time: The start time of the query. Defaults to one hour before current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param end_time: The end time of the query. Defaults to current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param select: Space-separated list of properties to return. Defaults to a reasonable
        subset of fields. Specify "*" to return all fields. Fields not selected will still appear
        with 'null' values.
        :param limit: Maximum number of events to return.
    '''
    client =  _insights_client_factory(InsightsClient).digest_event

    filters = []
    # retrieve last hours worth of logs if not specified
    filters.append('eventTimestamp ge {}'.format(start_time if start_time else datetime.now() - timedelta(hours=1)))
    filters.append('eventTimestamp le {}'.format(end_time if end_time else datetime.now()))
    filter_string = ' and '.join(filters)
    default_select = ['authorization', 'caller', 'correlationid', 'eventtimestamp', 'operationname',
                      'resourcegroupname', 'resourceid', 'status', 'subscriptionid', 'substatus']
    select_string = ','.join(select) if select else ','.join(default_select)
    if select and '*' in select:
        select_string = None
    return _limit_results(client.list(filter=filter_string, select=select_string), limit)

def list_tenant_digest_events(start_time=None, end_time=None, limit=50, select=None):
    ''' List tenant digest events. By default, returns a subset of properties for events which occurred
        over the past hour.
        :param start_time: The start time of the query. Defaults to one hour before current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param end_time: The end time of the query. Defaults to current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param select: Space-separated list of properties to return. Defaults to a reasonable
        subset of fields. Specify "*" to return all fields. Fields not selected will still appear
        with 'null' values.
        :param limit: Maximum number of events to return.
    '''
    client =  _insights_client_factory(InsightsClient).tenant_digest_event

    filters = []
    # retrieve last hours worth of logs if not specified
    filters.append('eventTimestamp ge {}'.format(start_time if start_time else datetime.now() - timedelta(hours=1)))
    filters.append('eventTimestamp le {}'.format(end_time if end_time else datetime.now()))
    filter_string = ' and '.join(filters)
    default_select = ['authorization', 'caller', 'correlationid', 'eventtimestamp', 'operationname',
                      'resourcegroupname', 'resourceid', 'status', 'subscriptionid', 'substatus']
    select_string = ','.join(select) if select else ','.join(default_select)
    if select and '*' in select:
        select_string = None
    return _limit_results(client.list(filter=filter_string, select=select_string), limit)

def list_tenant_events(start_time=None, end_time=None, limit=50, select=None):
    ''' List tenant events. By default, returns a subset of properties for events which occurred
        over the past hour.
        :param start_time: The start time of the query. Defaults to one hour before current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param end_time: The end time of the query. Defaults to current time.
        ISO format with explicit indication of timezone: yyyy-mm-ddThh:mm:ssZ,
        yyyy-mm-ddThh-mm-ss-zzzz
        :param select: Space-separated list of properties to return. Defaults to a reasonable
        subset of fields. Specify "*" to return all fields. Fields not selected will still appear
        with 'null' values.
        :param limit: Maximum number of events to return.
    '''
    client =  _insights_client_factory(InsightsClient).tenant_event

    filters = []
    # retrieve last hours worth of logs if not specified
    filters.append('eventTimestamp ge {}'.format(start_time if start_time else datetime.now() - timedelta(hours=1)))
    filters.append('eventTimestamp le {}'.format(end_time if end_time else datetime.now()))
    filter_string = ' and '.join(filters)
    default_select = ['authorization', 'caller', 'correlationid', 'eventtimestamp', 'operationname',
                      'resourcegroupname', 'resourceid', 'status', 'subscriptionid', 'substatus']
    select_string = ','.join(select) if select else ','.join(default_select)
    if select and '*' in select:
        select_string = None
    return _limit_results(client.list(filter=filter_string, select=select_string), limit)
