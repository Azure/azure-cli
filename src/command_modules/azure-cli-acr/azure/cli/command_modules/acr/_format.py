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

    if 'sku' in item and 'name' in item['sku']:
        table_info['SKU'] = item['sku']['name']
    if 'username' in item:
        table_info['USERNAME'] = item['username']
    if 'passwords' in item:
        if item['passwords'] and 'value' in item['passwords'][0]:
            table_info['PASSWORD'] = item['passwords'][0]['value']
        if len(item['passwords']) > 1 and 'value' in item['passwords'][1]:
            table_info['PASSWORD2'] = item['passwords'][1]['value']
    # Parse webhook list-events
    table_info['ID'] = item['id'] if 'id' in item and item['id'] and '/subscriptions/' not in item['id'] else None
    if 'eventRequestMessage' in item and item['eventRequestMessage'] and \
       'content' in item['eventRequestMessage'] and item['eventRequestMessage']['content']:
        requestContent = item['eventRequestMessage']['content']
        if 'action' in requestContent:
            table_info['ACTION'] = requestContent['action']
        if 'target' in requestContent and requestContent['target'] and \
           'repository' in requestContent['target'] and requestContent['target']['repository']:
            tag = requestContent['target']['tag'] if 'tag' in requestContent['target'] else None
            table_info['IMAGE'] = '{}:{}'.format(requestContent['target']['repository'], tag) if tag \
            else requestContent['target']['repository']
        if 'timestamp' in requestContent:
            table_info['TIMESTAMP'] = requestContent['timestamp']
    if 'eventResponseMessage' in item and item['eventResponseMessage']:
        responseMessage = item['eventResponseMessage']
        if 'statusCode' in responseMessage or 'reasonPhrase' in responseMessage:
            table_info['RESPONSE STATUS'] = '{} {}'.format(
                responseMessage['statusCode'], responseMessage['reasonPhrase'])

    return OrderedDict(sorted(table_info.items(), key=lambda t: _order_map[t[0]]))
