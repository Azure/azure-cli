# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

_registry_map = {
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
    'customHeaders': 'HEADERS'
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
    'HEADERS': 45
}


def output_format(result):
    """Returns the list of container registries each of which is an ordered dictionary.
    :param list/dict result: The (list of) container registry object(s)
    """
    obj_list = result if isinstance(result, list) else [result]
    return [_format_group(item) for item in obj_list]


def _format_group(item):
    """Returns an ordered dictionary of the container registry.
    :param dict item: The container registry object
    """
    registry_info = {_registry_map[key]: str(item[key]) for key in item if key in _registry_map}

    if 'sku' in item and 'name' in item['sku']:
        registry_info['SKU'] = item['sku']['name']
    if 'username' in item:
        registry_info['USERNAME'] = item['username']
    if 'passwords' in item:
        if item['passwords'] and 'value' in item['passwords'][0]:
            registry_info['PASSWORD'] = item['passwords'][0]['value']
        if len(item['passwords']) > 1 and 'value' in item['passwords'][1]:
            registry_info['PASSWORD2'] = item['passwords'][1]['value']

    return OrderedDict(sorted(registry_info.items(), key=lambda t: _order_map[t[0]]))
