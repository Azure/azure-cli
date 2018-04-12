# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def registry_output_format(result):
    return _output_format(result, _registry_format_group)


def usage_output_format(result):
    return _output_format(result, _usage_format_group)


def credential_output_format(result):
    return _output_format(result, _credential_format_group)


def webhook_output_format(result):
    return _output_format(result, _webhook_format_group)


def webhook_get_config_output_format(result):
    return _output_format(result, _webhook_get_config_format_group)


def webhook_list_events_output_format(result):
    return _output_format(result, _webhook_list_events_format_group)


def webhook_ping_output_format(result):
    return _output_format(result, _webhook_ping_format_group)


def replication_output_format(result):
    return _output_format(result, _replication_format_group)


def _output_format(result, format_group):
    if 'value' in result and isinstance(result['value'], list):
        result = result['value']
    obj_list = result if isinstance(result, list) else [result]
    return [format_group(item) for item in obj_list]


def _registry_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('RESOURCE GROUP', _get_value(item, 'resourceGroup')),
        ('LOCATION', _get_value(item, 'location')),
        ('SKU', _get_value(item, 'sku', 'name')),
        ('LOGIN SERVER', _get_value(item, 'loginServer')),
        ('CREATION DATE', _format_datetime(_get_value(item, 'creationDate'))),
        ('ADMIN ENABLED', _get_value(item, 'adminUserEnabled'))
    ])


def _usage_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('LIMIT', _get_value(item, 'limit')),
        ('CURRENT VALUE', _get_value(item, 'currentValue')),
        ('UNIT', _get_value(item, 'unit'))
    ])


def _credential_format_group(item):
    return OrderedDict([
        ('USERNAME', _get_value(item, 'username')),
        ('PASSWORD', _get_value(item, 'passwords', 0, 'value')),
        ('PASSWORD2', _get_value(item, 'passwords', 1, 'value'))
    ])


def _webhook_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('LOCATION', _get_value(item, 'location')),
        ('ACTIONS', _get_value(item, 'actions')),
        ('SCOPE', _get_value(item, 'scope')),
        ('STATUS', _get_value(item, 'status'))
    ])


def _webhook_get_config_format_group(item):
    return OrderedDict([
        ('SERVICE URI', _get_value(item, 'serviceUri')),
        ('HEADERS', _get_value(item, 'customHeaders'))
    ])


def _webhook_list_events_format_group(item):
    repository = _get_value(item, 'eventRequestMessage', 'content', 'target', 'repository').strip()
    tag = _get_value(item, 'eventRequestMessage', 'content', 'target', 'tag').strip()
    status = _get_value(item, 'eventResponseMessage', 'statusCode').strip()
    reason = _get_value(item, 'eventResponseMessage', 'reasonPhrase').strip()

    return OrderedDict([
        ('ID', _get_value(item, 'id')),
        ('ACTION', _get_value(item, 'eventRequestMessage', 'content', 'action')),
        ('IMAGE', '{}:{}'.format(repository, tag) if repository and tag else repository or ' '),
        ('HTTP STATUS', '{} {}'.format(status, reason) if status and reason else status or reason or ' '),
        ('TIMESTAMP', _format_datetime(_get_value(item, 'eventRequestMessage', 'content', 'timestamp')))
    ])


def _webhook_ping_format_group(item):
    return OrderedDict([
        ('ID', _get_value(item, 'id'))
    ])


def _replication_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('LOCATION', _get_value(item, 'location')),
        ('PROVISIONING STATE', _get_value(item, 'provisioningState')),
        ('STATUS', _get_value(item, 'status', 'displayStatus'))
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
        return str(item) if item else ' '
    except (KeyError, TypeError, IndexError):
        return ' '
