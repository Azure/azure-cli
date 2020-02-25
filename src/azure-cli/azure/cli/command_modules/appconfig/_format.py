# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from collections import OrderedDict
from knack.log import get_logger

logger = get_logger(__name__)


def configstore_output_format(result):
    return _output_format(result, _configstore_format_group)


def configstore_identity_format(result):
    return _output_format(result, _configstore_identity_format_group)


def configstore_credential_format(result):
    return _output_format(result, _configstore_credential_format_group)


def keyvalue_entry_format(result):
    return _output_format(result, _keyvalue_entry_format_group)


def featureflag_entry_format(result):
    return _output_format(result, _featureflag_entry_format_group)


def featurefilter_entry_format(result):
    return _output_format(result, _featurefilter_entry_format_group)


def _output_format(result, format_group):
    if 'value' in result and isinstance(result['value'], list):
        result = result['value']
    obj_list = result if isinstance(result, list) else [result]
    return [format_group(item) for item in obj_list]


def _configstore_format_group(item):
    sku_value = _get_value(item, 'sku')

    try:
        sku = json.loads(sku_value.replace("\'", "\"")).get('name')
    except ValueError:
        logger.debug("No valid sku %s found", sku_value)
        sku = ""

    return OrderedDict([
        ('CREATION DATE', _format_datetime(_get_value(item, 'creationDate'))),
        ('ENDPOINT', _get_value(item, 'endpoint')),
        ('LOCATION', _get_value(item, 'location')),
        ('NAME', _get_value(item, 'name')),
        ('PROVISIONING STATE', _get_value(item, 'provisioningState')),
        ('RESOURCE GROUP', _get_value(item, 'resourceGroup')),
        ('SKU', sku)
    ])


def _configstore_identity_format_group(item):
    return OrderedDict([
        ('PRINCIPAL ID', _format_datetime(_get_value(item, 'principalId'))),
        ('TENANT ID', _get_value(item, 'tenantId')),
        ('TYPE', _get_value(item, 'type'))
    ])


def _configstore_credential_format_group(item):
    return OrderedDict([
        ('CONNECTION STRING', _get_value(item, 'connectionString')),
        ('ID', _get_value(item, 'id')),
        ('LAST MODIFIED', _format_datetime(_get_value(item, 'lastModified'))),
        ('NAME', _get_value(item, 'name')),
        ('READ ONLY', _get_value(item, 'readOnly')),
        ('VALUE', _get_value(item, 'value'))
    ])


def _keyvalue_entry_format_group(item):
    return OrderedDict([
        ('CONTENT TYPE', _get_value(item, 'contentType')),
        ('KEY', _get_value(item, 'key')),
        ('VALUE', _get_value(item, 'value')),
        ('LAST MODIFIED', _format_datetime(_get_value(item, 'lastModified'))),
        ('TAGS', _get_value(item, 'tags')),
        ('LABEL', _get_value(item, 'label')),
        ('LOCKED', _get_value(item, 'locked'))
    ])


def _featureflag_entry_format_group(item):
    return OrderedDict([
        ('KEY', _get_value(item, 'key')),
        ('LABEL', _get_value(item, 'label')),
        ('STATE', _get_value(item, 'state')),
        ('LOCKED', _get_value(item, 'locked')),
        ('DESCRIPTION', _get_value(item, 'description')),
        ('LAST MODIFIED', _format_datetime(_get_value(item, 'lastModified'))),
        ('CONDITIONS', _get_value(item, 'conditions'))
    ])


def _featurefilter_entry_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('PARAMETERS', _get_value(item, 'parameters'))
    ])


def _format_datetime(date_string):
    from dateutil.parser import parse
    try:
        return parse(date_string).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return date_string or ' '


def _get_value(item, *args):
    """Recursively get a nested value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return _EvenLadder(item) if item is not None else ' '
    except (KeyError, TypeError, IndexError):
        return ' '


def _EvenLadder(item):
    formated_item = ''
    item = str(item)
    if len(item) < 70:
        return item
    for i in range(0, len(item), 70):
        formated_item += str(item[i: i + 70]) + "\n"
    return formated_item
