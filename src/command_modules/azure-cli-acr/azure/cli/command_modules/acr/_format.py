# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from ._utils import get_resource_group_name_by_resource_id

_registry_map = {
    'name': 'NAME',
    'resourceGroup': 'RESOURCE GROUP',
    'location': 'LOCATION',
    'loginServer': 'LOGIN SERVER',
    'creationDate': 'CREATION DATE',
    'adminUserEnabled': 'ADMIN ENABLED'
}

_admin_user_map = {
    'username': 'USERNAME',
    'password': 'PASSWORD'
}

_order_map = {
    'NAME': 1,
    'RESOURCE GROUP': 2,
    'LOCATION': 3,
    'LOGIN SERVER': 11,
    'CREATION DATE': 12,
    'ADMIN ENABLED': 13,
    'USERNAME': 31,
    'PASSWORD': 32
}

def output_format(result):
    '''Returns the list of container registries each of which is an ordered dictionary.
    :param list/dict result: The (list of) container registry object(s)
    '''
    obj_list = result if isinstance(result, list) else [result]
    return [_format_group(item) for item in obj_list]

def _format_group(item):
    '''Returns an ordered dictionary of the container registry.
    :param dict item: The container registry object
    '''
    registry_info = {_registry_map[key]: str(item[key]) for key in item if key in _registry_map}

    if 'id' in item and item['id']:
        resource_group_name = get_resource_group_name_by_resource_id(item['id'])
        registry_info['RESOURCE GROUP'] = resource_group_name

    admin_user_info = {_admin_user_map[key]: str(item[key])
                       for key in item if key in _admin_user_map}

    all_info = registry_info.copy()
    all_info.update(admin_user_info)

    return OrderedDict(sorted(all_info.items(), key=lambda t: _order_map[t[0]]))
