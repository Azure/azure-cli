# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# ISO format with explicit indication of timezone
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def get_resource_group_location(cli_ctx, name):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType

    # pylint: disable=no-member
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).resource_groups.get(name).location


# region Autoscale Maps
def get_autoscale_statistic_map():
    from azure.mgmt.monitor.models import MetricStatisticType
    return {'avg': MetricStatisticType.average, 'min': MetricStatisticType.min,
            'max': MetricStatisticType.max, 'sum': MetricStatisticType.sum}


def get_autoscale_operator_map():
    from azure.mgmt.monitor.models import ComparisonOperationType
    return {'==': ComparisonOperationType.equals, '!=': ComparisonOperationType.not_equals,
            '>': ComparisonOperationType.greater_than, '>=': ComparisonOperationType.greater_than_or_equal,
            '<': ComparisonOperationType.less_than, '<=': ComparisonOperationType.less_than_or_equal}


def get_autoscale_aggregation_map():
    from azure.mgmt.monitor.models import TimeAggregationType
    return {'avg': TimeAggregationType.average, 'min': TimeAggregationType.minimum,
            'max': TimeAggregationType.maximum, 'total': TimeAggregationType.total,
            'count': TimeAggregationType.count}


def get_autoscale_scale_direction_map():
    from azure.mgmt.monitor.models import ScaleDirection
    return {'to': ScaleDirection.none, 'out': ScaleDirection.increase,
            'in': ScaleDirection.decrease}


def gen_guid():
    import uuid
    return uuid.uuid4()
# endregion
