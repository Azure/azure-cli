# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
from knack.log import get_logger


logger = get_logger(__name__)


def service_output_format(result):
    return _output_format(result, _service_format_group)


def _service_format_group(item):
    return OrderedDict([
        ('NAME', _get_value_as_str(item, 'name')),
        ('RESOURCE GROUP', _get_value_as_str(item, 'resourceGroup')),
        ('LOCATION', _get_value_as_str(item, 'location')),
        ('GATEWAY ADDR', _get_value_as_str(item, 'gatewayUrl')),
        ('PUBLIC IP', transform_string_array(_get_value_as_object(item, 'publicIpAddresses'))),
        ('PRIVATE IP', transform_string_array(_get_value_as_object(item, 'privateIpAddresses'))),
        ('STATUS', _service_status(_get_value_as_str(item, 'provisioningState'))),
        ('TIER', _get_value_as_str(item, 'sku', 'name')),
        ('UNITS', _get_value_as_str(item, 'sku', 'capacity'))
    ])


def _service_status(argument):
    d = {
        'activating': 'Activating',
        'created': 'Activating',
        'failed': 'Error',
        'stopped': 'Stopped',
        'succeeded': 'Online',
        'updating': 'Updating'
    }
    return d.get(argument.lower(), argument)


def _get_value_as_str(item, *args):
    """Get a nested value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return str(item) if item else ' '
    except (KeyError, TypeError, IndexError):
        return ' '


def _get_value_as_object(item, *args):
    """Get a nested value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return item if item else ' '
    except (KeyError, TypeError, IndexError):
        return ' '


def _output_format(result, format_group):
    if 'value' in result and isinstance(result['value'], list):
        result = result['value']
    obj_list = result if isinstance(result, list) else [result]
    return [format_group(item) for item in obj_list]


def transform_string_array(item):
    return ','.join(item)


def product_output_format(result):
    return _output_format(result, (lambda item: OrderedDict([
        ('NAME', _get_value_as_str(item, 'name')),
        ('DISPLAY NAME', _get_value_as_str(item, 'displayName')),
        ('STATE', _service_status(_get_value_as_str(item, 'state'))),
        ('SUBSCRIPTION REQUIRED', _get_value_as_str(item, 'subscriptionRequired')),
        ('APPROVAL REQUIRED', _get_value_as_str(item, 'approvalRequired'))
    ])))


def policy_output_format(result):
    return _output_format(result, (lambda item: OrderedDict([
        ('NAME', _get_value_as_str(item, 'name')),
        ('RESOURCE GROUP', _get_value_as_str(item, 'resourceGroup')),
        ('DISPLAY NAME', _get_value_as_str(item, 'displayName')),
        ('SUBSCRIPTION REQUIRED', _get_value_as_str(item, 'subscriptionRequired')),
        ('STATE', _service_status(_get_value_as_str(item, 'state')))
    ])))


def subscription_output_format(result):
    return _output_format(result, _subscription_format_group)


def _subscription_format_group(item):
    return OrderedDict([
        ('DISPLAY NAME', _get_value_as_str(item, 'displayName')),
        ('PRIMARY KEY', _get_value_as_str(item, 'primaryKey')),
        ('SECONDARY KEY', _get_value_as_str(item, 'secondaryKey')),
        ('SCOPE', _get_value_as_str(item, 'scope')),
        ('STATE', _service_status(_get_value_as_str(item, 'state'))),
        ('ALLOW TRACING', item['allowTracing'])
    ])


def api_policy_output_format(result):
    return _output_format(result, _api_policy_format_group)


def _api_policy_format_group(item):
    return OrderedDict([
        ('NAME', _get_value_as_str(item, 'name')),
        ('COUNT', _get_value_as_str(item, 'count')),
        ('VALUE', _get_value_as_str(item, 'value'))
    ])
