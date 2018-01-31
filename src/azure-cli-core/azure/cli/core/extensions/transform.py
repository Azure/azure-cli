# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

import knack.events as events

from azure.cli.core.util import b64_to_hex


def register(cli_ctx):
    cli_ctx.register_event(events.EVENT_INVOKER_TRANSFORM_RESULT, _resource_group_transform)
    cli_ctx.register_event(events.EVENT_INVOKER_TRANSFORM_RESULT, _x509_from_base64_to_hex_transform)


def _parse_id(strid):
    parsed = {}
    parts = re.split('/', strid)
    if parts[3].lower() != 'resourcegroups':
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
            if item_key != 'sourceVault':
                _add_resource_group(obj[item_key])


def _add_x509_hex(obj):
    if isinstance(obj, list):
        for array_item in obj:
            _add_x509_hex(array_item)
    elif isinstance(obj, dict):
        try:
            if 'x509ThumbprintHex' not in obj:
                if obj['x509Thumbprint']:
                    obj['x509ThumbprintHex'] = b64_to_hex(obj['x509Thumbprint'])
        except (KeyError, IndexError, TypeError):
            pass
        for item_key in obj:
            _add_x509_hex(obj[item_key])


def _resource_group_transform(_, **kwargs):
    _add_resource_group(kwargs['event_data']['result'])


def _x509_from_base64_to_hex_transform(_, **kwargs):
    _add_x509_hex(kwargs['event_data']['result'])
