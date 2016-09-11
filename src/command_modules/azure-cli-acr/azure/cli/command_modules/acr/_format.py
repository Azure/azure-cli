#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from collections import OrderedDict

from ._utils import get_resource_group_name_by_resource_id

_basic_map = {
    'name': 'NAME',
    'resourceGroup': 'RESOURCE GROUP',
    'location': 'LOCATION',
    'tags': 'TAGS'
}

_properties_map = {
    'loginServer': 'LOGIN SERVER',
    'creationDate': 'CREATION DATE',
    'adminUserEnabled': 'ADMIN USER ENABLED'
}

_storage_account_map = {
    'name': 'STORAGE ACCOUNT NAME'
}

_admin_user_map = {
    'userName': 'USERNAME',
    'passWord': 'PASSWORD'
}

_order_map = {
    'NAME': 1,
    'RESOURCE GROUP': 2,
    'LOCATION': 3,
    'TAGS': 4,
    'LOGIN SERVER': 11,
    'CREATION DATE': 12,
    'ADMIN USER ENABLED': 13,
    'STORAGE ACCOUNT NAME': 21,
    'USERNAME': 31,
    'PASSWORD': 32
}

def output_format(result):
    '''Returns the list of container registries each of which is an ordered dictionary.
    :param list/dict result: The (list of) container registry object(s)
    '''
    obj_list = result if isinstance(result, list) else [result]
    return [_format_registry(item) for item in obj_list]

def _format_registry(item):
    '''Returns an ordered dictionary of the container registry.
    :param dict item: The container registry object
    '''
    basic_info = {_basic_map[key]: str(item[key]) for key in item if key in _basic_map}

    if 'id' in item and item['id']:
        resource_group_name = get_resource_group_name_by_resource_id(item['id'])
        basic_info['RESOURCE GROUP'] = resource_group_name

    properties_info = {}
    storage_account_info = {}
    if 'properties' in item and item['properties']:
        properties = item['properties']
        properties_info = {_properties_map[key]: str(properties[key])
                           for key in properties if key in _properties_map}

        if 'storageAccount' in properties and properties['storageAccount']:
            storage_account = properties['storageAccount']
            storage_account_info = {_storage_account_map[key]: str(storage_account[key])
                                    for key in storage_account if key in _storage_account_map}

    admin_user_info = {_admin_user_map[key]: str(item[key])
                       for key in item if key in _admin_user_map}

    all_info = basic_info.copy()
    all_info.update(properties_info)
    all_info.update(storage_account_info)
    all_info.update(admin_user_info)

    return OrderedDict(sorted(all_info.items(), key=lambda t: _order_map[t[0]]))
