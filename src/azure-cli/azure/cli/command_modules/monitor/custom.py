# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor._client_factory import cf_metrics

from knack.log import get_logger

logger = get_logger(__name__)


# region ActivityLog
def list_activity_log(client, filters=None, correlation_id=None, resource_group=None, resource_id=None,
                      resource_provider=None, start_time=None, end_time=None, caller=None, status=None, max_events=50,
                      select=None, offset='6h'):
    if filters:
        odata_filters = filters
    else:
        odata_filters = _build_activity_log_odata_filter(correlation_id, resource_group, resource_id, resource_provider,
                                                         start_time, end_time, caller, status, offset)

    select_filters = _activity_log_select_filter_builder(select)
    logger.info('OData Filter: %s', odata_filters)
    logger.info('Select Filter: %s', select_filters)
    activity_log = client.list(filter=odata_filters, select=select_filters)
    return _limit_results(activity_log, max_events)


def _build_activity_log_odata_filter(correlation_id=None, resource_group=None, resource_id=None, resource_provider=None,
                                     start_time=None, end_time=None, caller=None, status=None, offset=None):
    from datetime import datetime
    import dateutil.parser

    if not start_time and not end_time:
        # if neither value provided, end_time is now
        end_time = datetime.utcnow().isoformat()
    if not start_time:
        # if no start_time, apply offset backwards from end_time
        start_time = (dateutil.parser.parse(end_time) - offset).isoformat()
    elif not end_time:
        # if no end_time, apply offset fowards from start_time
        end_time = (dateutil.parser.parse(start_time) + offset).isoformat()

    odata_filters = 'eventTimestamp ge {} and eventTimestamp le {}'.format(start_time, end_time)

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
# endregion


# region Metrics
# pylint:disable=unused-argument
def list_metrics(cmd, resource,
                 start_time=None, end_time=None, offset='1h', interval='1m',
                 metadata=None, dimension=None, aggregation=None, metrics=None,
                 filters=None, metric_namespace=None, orderby=None, top=10):

    from azure.mgmt.monitor.models import ResultType
    from datetime import datetime
    import dateutil.parser
    from urllib.parse import quote_plus

    if not start_time and not end_time:
        # if neither value provided, end_time is now
        end_time = datetime.utcnow().isoformat()
    if not start_time:
        # if no start_time, apply offset backwards from end_time
        start_time = (dateutil.parser.parse(end_time) - offset).isoformat()
    elif not end_time:
        # if no end_time, apply offset fowards from start_time
        end_time = (dateutil.parser.parse(start_time) + offset).isoformat()

    timespan = '{}/{}'.format(start_time, end_time)

    client = cf_metrics(cmd.cli_ctx, None)
    return client.list(
        resource_uri=resource,
        timespan=quote_plus(timespan),
        interval=interval,
        metricnames=','.join(metrics) if metrics else None,
        aggregation=','.join(aggregation) if aggregation else None,
        top=top,
        orderby=orderby,
        filter=filters,
        result_type=ResultType.metadata if metadata else None,
        metricnamespace=metric_namespace)
# endregion
