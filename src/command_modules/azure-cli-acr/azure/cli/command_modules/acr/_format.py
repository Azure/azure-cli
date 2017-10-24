# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

_property_map = {
    'name': 'NAME',
    'resourceGroup': 'RESOURCE GROUP',
    'location': 'LOCATION',
    'loginServer': 'LOGIN SERVER',
    'creationDate': 'CREATION DATE',
    'adminUserEnabled': 'ADMIN ENABLED',
    'status': 'STATUS',
    'scope': 'SCOPE',
    'actions': 'ACTIONS',
    'serviceUri': 'SERVICE URI',
    'customHeaders': 'HEADERS',
    'limit': 'LIMIT',
    'currentValue': 'CURRENT VALUE',
    'unit': 'UNIT'
}

_order_map = {
    'NAME': 1,
    'RESOURCE GROUP': 2,
    'LOCATION': 3,
    'SKU': 4,
    'LOGIN SERVER': 11,
    'CREATION DATE': 12,
    'ADMIN ENABLED': 13,
    'USERNAME': 31,
    'PASSWORD': 32,
    'PASSWORD2': 33,
    'STATUS': 41,
    'SCOPE': 42,
    'ACTIONS': 43,
    'SERVICE URI': 44,
    'HEADERS': 45,
    'LIMIT': 51,
    'CURRENT VALUE': 52,
    'UNIT': 53,
    'ID': 61,
    'ACTION': 62,
    'IMAGE': 63,
    'RESPONSE STATUS': 64,
    'TIMESTAMP': 65
}


def output_format(result):
    """Returns the list of container registries each of which is an ordered dictionary.
    :param list/dict result: The (list of) container registry object(s)
    """
    if 'value' in result and isinstance(result['value'], list):
        result = result['value']
    obj_list = result if isinstance(result, list) else [result]
    return [_format_group(item) for item in obj_list]


def _format_group(item):
    """Returns an ordered dictionary of the container registry.
    :param dict item: The container registry object
    """
    table_info = {_property_map[key]: str(item[key]) for key in item if key in _property_map}

    try:
        table_info['SKU'] = item['sku']['name']
    except (KeyError, TypeError):
        pass

    try:
        table_info['USERNAME'] = item['username']
    except (KeyError, TypeError):
        pass

    try:
        table_info['PASSWORD'] = item['passwords'][0]['value']
    except (KeyError, TypeError, IndexError):
        pass

    try:
        table_info['PASSWORD2'] = item['passwords'][1]['value']
    except (KeyError, TypeError, IndexError):
        pass

    try:
        # Only show ID if it is not an ARM resource ID
        table_info['ID'] = item['id'] if '/subscriptions/' not in item['id'].lower() else None
    except (KeyError, TypeError):
        pass

    # Parse webhook list-events
    try:
        table_info['ACTION'] = item['eventRequestMessage']['content']['action']
    except (KeyError, TypeError):
        pass

    try:
        table_info['IMAGE'] = item['eventRequestMessage']['content']['target']['repository']
    except (KeyError, TypeError):
        pass

    try:
        tag = item['eventRequestMessage']['content']['target']['tag']
        if table_info['IMAGE'] and tag:
            table_info['IMAGE'] = '{}:{}'.format(table_info['IMAGE'], tag)
    except (KeyError, TypeError):
        pass

    try:
        table_info['TIMESTAMP'] = item['eventRequestMessage']['content']['timestamp']
    except (KeyError, TypeError):
        pass

    try:
        table_info['RESPONSE STATUS'] = item['eventResponseMessage']['statusCode']
    except (KeyError, TypeError):
        pass

    try:
        status_code = item['eventResponseMessage']['statusCode']
        reason_phrase = item['eventResponseMessage']['reasonPhrase']
        table_info['RESPONSE STATUS'] = '{} {}'.format(status_code, reason_phrase)
    except (KeyError, TypeError):
        pass

    return OrderedDict(sorted(table_info.items(), key=lambda t: _order_map[t[0]]))
