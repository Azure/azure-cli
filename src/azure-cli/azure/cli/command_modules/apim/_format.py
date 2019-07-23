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
        ('NAME', _get_value(item, 'name')),
        ('RESOURCE GROUP', _get_value(item, 'resourceGroup')),
        ('LOCATION', _get_value(item, 'location')),
        ('GATEWAY', _get_value(item, 'gatewayUrl')),
        ('VIPS', _get_value(item, 'publicIpAddresses')),
        ('SKU', _get_value(item, 'sku', 'name'))
    ])

def _get_value(item, *args):
    """Get a nested value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return str(item) if item else ' '
    except (KeyError, TypeError, IndexError):
        return ' '

def _output_format(result, format_group):
    if 'value' in result and isinstance(result['value'], list):
        result = result['value']
    obj_list = result if isinstance(result, list) else [result]
    return [format_group(item) for item in obj_list]


