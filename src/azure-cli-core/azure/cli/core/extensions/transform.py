#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import re

def register(application):
    application.register(application.TRANSFORM_RESULT, _resource_group_transform)

def _parse_id(strid):
    parsed = {}
    parts = re.split('/', strid)
    if parts[3] != 'resourceGroups':
        raise KeyError()

    parsed['resource-group'] = parts[4]
    parsed['name'] = parts[8]
    return parsed

def _add_resource_group(obj):
    if isinstance(obj, list):
        for array_item in obj:
            _add_resource_group(array_item)
    elif isinstance(obj, dict):
        try:
            if 'resourceGroup' not in obj:
                if obj['id']:
                    obj['resourceGroup'] = _parse_id(obj['id'])['resource-group']
        except (KeyError, IndexError, TypeError):
            pass
        for item_key in obj:
            _add_resource_group(obj[item_key])

def _resource_group_transform(**kwargs):
    _add_resource_group(kwargs['event_data']['result'])

