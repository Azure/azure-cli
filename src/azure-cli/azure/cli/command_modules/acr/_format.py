# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
from datetime import datetime
from knack.log import get_logger


logger = get_logger(__name__)


def registry_output_format(result):
    return _output_format(result, _registry_format_group)


def usage_output_format(result):
    return _output_format(result, _usage_format_group)


def policy_output_format(result):
    return _output_format(result, _policy_format_group)


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


def task_output_format(result):
    return _output_format(result, _task_format_group)


def task_identity_format(result):
    return _output_format(result, _task_identity_format_group)


def taskrun_output_format(result):
    return _output_format(result, _taskrun_format_group)


def build_output_format(result):
    return _output_format(result, _build_format_group)


def run_output_format(result):
    return _output_format(result, _run_format_group)


def scope_map_output_format(result):
    return _output_format(result, _scope_map_format_group)


def token_output_format(result):
    return _output_format(result, _token_format_group)


def token_credential_output_format(result):
    return _output_format(result, _token_password_format_group)


def endpoints_output_format(result):
    info = []
    for e in result['dataEndpoints']:
        info.append(OrderedDict([
            ('loginServer', _get_value(result, 'loginServer')),
            ('region', _get_value(e, 'region')),
            ('endpoint', _get_value(e, 'endpoint'))
        ]))
    return info


def agentpool_output_format(result):
    return _output_format(result, _agentpool_format_group)


def connected_registry_output_format(result):
    return _output_format(result, _connected_registry_format_group)


def connected_registry_list_output_format(result):
    family_tree = {}
    for reg in result:
        parent_id = _get_value(reg, 'parent', 'id')
        parent_name = '' if parent_id.isspace() else parent_id.split('/connectedRegistries/')[1]
        family_tree[_get_value(reg, 'id')] = {
            "name": _get_value(reg, 'name'),
            "id": _get_value(reg, 'id'),
            "connectionState": _get_value(reg, 'connectionState'),
            "parent_name": parent_name,
            "parent_id": parent_id,
            "loginServer_host": _get_value(reg, 'loginServer', 'host'),
            "parent_syncProperties_lastSyncTime": _get_value(reg, 'parent', 'syncProperties', 'lastSyncTime'),
            "mode": _get_value(reg, 'mode'),
            "childs": []
        }

    roots = []
    for reg in result:
        parent_id = _get_value(reg, 'parent', 'id')
        if parent_id.isspace() or parent_id not in family_tree:
            roots.append(_get_value(reg, 'id'))
        else:
            family_tree[parent_id]["childs"].append(_get_value(reg, 'id'))

    result_list_format = []
    for connected_registry_id in roots:
        result_list_format.extend(_recursive_format_list_acr_childs(family_tree, connected_registry_id))

    return _output_format(result_list_format, _connected_registry_list_format_group)


def list_referrers_output_format(result):
    manifests = []
    for manifest in result['references']:
        manifests.append(OrderedDict([
            ('Digest', _get_value(manifest, 'digest')),
            ('ArtifactType', _get_value(manifest, 'artifactType')),
            ('MediaType', _get_value(manifest, 'mediaType')),
            ('Size', _get_value(manifest, 'size'))
        ]))
    return manifests


def manifest_output_format(result):
    manifests = []
    for manifest in result:
        manifests.append(OrderedDict([
            ('MediaType', _get_value(manifest, 'mediaType')),
            ('ArtifactType', _get_value(manifest, 'artifactType')),
            ('SubjectDigest', _get_value(manifest, 'subject', 'digest'))
        ]))
    return manifests


def _recursive_format_list_acr_childs(family_tree, connected_registry_id):
    connected_registry = family_tree[connected_registry_id]
    childs = connected_registry['childs']
    result = [connected_registry]
    for child_id in childs:
        result.extend(_recursive_format_list_acr_childs(family_tree, child_id))
    return result


def helm_list_output_format(result):
    if isinstance(result, dict):
        obj_list = []
        for _, item in result.items():
            obj_list += item
        return _output_format(obj_list, _helm_format_group)
    logger.debug("Unexpected output %s", result)
    return _output_format(result, _helm_format_group)


def helm_show_output_format(result):
    return _output_format(result, _helm_format_group)


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


def _policy_format_group(item):
    return OrderedDict([
        ('STATUS', _get_value(item, 'status')),
        ('TYPE', _get_value(item, 'type'))
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


def _task_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('PLATFORM', _get_value(item, 'platform', 'os')),
        ('STATUS', _get_value(item, 'status')),
        ('SOURCE REPOSITORY', _get_value(item, 'step', 'contextPath')),
        ('TRIGGERS', _get_triggers(item))
    ])


def _task_identity_format_group(item):
    identities = _get_array_value(item, 'userAssignedIdentities')
    identities_by_line = str('\n'.join(identities)) if identities else ' '

    return OrderedDict([
        ('PRINCIPAL ID', _get_value(item, 'principalId')),
        ('TENANT ID', _get_value(item, 'tenantId')),
        ('TYPE', _get_value(item, 'type')),
        ('USER ASSIGNED IDENTITIES', identities_by_line)
    ])


def _taskrun_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('RUN ID', _get_value(item, 'runResult', 'runId')),
        ('TASK', _get_value(item, 'runResult', 'task')),
        ('PLATFORM', _get_value(item, 'runResult', 'platform', 'os')),
        ('STATUS', _get_value(item, 'runResult', 'status')),
        ('STARTED', _format_datetime(_get_value(item, 'runResult', 'startTime'))),
        ('DURATION', _get_duration(_get_value(item, 'runResult', 'startTime'),
                                   _get_value(item, 'runResult', 'finishTime')))
    ])


def _agentpool_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('COUNT', _get_value(item, 'count')),
        ('TIER', _get_value(item, 'tier')),
        ('STATE', _get_value(item, 'provisioningState')),
        ('VNET', _get_value(item, 'virtualNetworkSubnetResourceId')),
        ('OS', _get_value(item, 'os'))
    ])


def _connected_registry_format_group(item):
    parent_id = _get_value(item, 'parent', 'id')
    parent_name = '' if parent_id.isspace() else parent_id.split('/connectedRegistries/')[1]
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('MODE', _get_value(item, 'mode')),
        ('CONNECTION STATE', _get_value(item, 'connectionState')),
        ('PARENT', parent_name),
        ('LOGIN SERVER', _get_value(item, 'loginServer', 'host')),
        ('LAST SYNC (UTC)', _get_value(item, 'parent', 'syncProperties', 'lastSyncTime')),
        ('SYNC SCHEDULE', _get_value(item, 'parent', 'syncProperties', 'schedule')),
        ('SYNC WINDOW', _get_value(item, 'parent', 'syncProperties', 'syncWindow'))
    ])


def _connected_registry_list_format_group(item):
    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('MODE', _get_value(item, 'mode')),
        ('CONNECTION STATE', _get_value(item, 'connectionState')),
        ('PARENT', _get_value(item, 'parent_name')),
        ('LOGIN SERVER', _get_value(item, 'loginServer_host')),
        ('LAST SYNC (UTC)', _get_value(item, 'parent_syncProperties_lastSyncTime'))
    ])


def _build_format_group(item):
    return OrderedDict([
        ('BUILD ID', _get_value(item, 'buildId')),
        ('TASK', _get_value(item, 'buildTask')),
        ('PLATFORM', _get_value(item, 'platform', 'osType')),
        ('STATUS', _get_value(item, 'status')),
        ("TRIGGER", _get_build_trigger(_get_value(item, 'imageUpdateTrigger'),
                                       _get_value(item, 'sourceTrigger', 'eventType'))),
        ('STARTED', _format_datetime(_get_value(item, 'startTime'))),
        ('DURATION', _get_duration(_get_value(item, 'startTime'),
                                   _get_value(item, 'finishTime')))
    ])


def _run_format_group(item):
    return OrderedDict([
        ('RUN ID', _get_value(item, 'runId')),
        ('TASK', _get_value(item, 'task')),
        ('PLATFORM', _get_value(item, 'platform', 'os')),
        ('STATUS', _get_value(item, 'status')),
        ("TRIGGER", _get_build_trigger(_get_value(item, 'imageUpdateTrigger'),
                                       _get_value(item, 'sourceTrigger', 'eventType'),
                                       _get_value(item, 'timerTrigger'))),
        ('STARTED', _format_datetime(_get_value(item, 'startTime'))),
        ('DURATION', _get_duration(_get_value(item, 'startTime'), _get_value(item, 'finishTime')))
    ])


def _helm_format_group(item):
    description = _get_value(item, 'description')
    if len(description) > 57:  # Similar to helm client
        description = description[:57] + '...'

    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('CHART VERSION', _get_value(item, 'version')),
        ('APP VERSION', _get_value(item, 'appVersion')),
        ('DESCRIPTION', description)
    ])


def _scope_map_format_group(item):
    description = _get_value(item, 'description')
    if len(description) > 57:
        description = description[:57] + '...'

    return OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('TYPE', _get_value(item, 'scopeMapType')),
        ('CREATION DATE', _format_datetime(_get_value(item, 'creationDate'))),
        ('DESCRIPTION', description),
    ])


def _token_format_group(item):
    scope_map_id = _get_value(item, 'scopeMapId')
    output = OrderedDict([
        ('NAME', _get_value(item, 'name')),
        ('SCOPE MAP', scope_map_id.split('/')[-1]),
        ('PASSWORD1 EXPIRY', ''),
        ('PASSWORD2 EXPIRY', ''),
        ('STATUS', _get_value(item, 'status').title()),
        ('PROVISIONING STATE', _get_value(item, 'provisioningState')),
        ('CREATION DATE', _format_datetime(_get_value(item, 'creationDate')))
    ])

    passwords = _get_array_value(item, 'credentials', 'passwords')
    for password in passwords:
        password_name = _get_value(password, 'name').upper()
        # _get_value returns ' ' if item is none.
        expiry_value = _get_value(password, 'expiry')
        expiry_value = 'Never' if expiry_value == ' ' else _format_datetime(expiry_value)
        output_password_column = '{} EXPIRY'.format(password_name)
        if output_password_column in output:
            output[output_password_column] = expiry_value

    return output


def _token_password_format_group(item):
    username = _get_value(item, 'username')
    passwords = _get_array_value(item, 'passwords')

    output = [('USERNAME', username)]
    for password in passwords:
        password_name = _get_value(password, 'name').upper()
        password_value = _get_value(password, 'value')
        expiry_value = _get_value(password, 'expiry')
        # _get_value returns ' ' if item is none.
        expiry_value = 'Never' if expiry_value == ' ' else _format_datetime(expiry_value)
        output.append((password_name, password_value))
        output.append(('{} EXPIRY'.format(password_name), expiry_value))

    return OrderedDict(output)


def _get_triggers(item):
    """Get a nested value from a dict.
    :param dict item: The dict object
    """
    triggers = []
    if _get_value(item, 'trigger', 'sourceTriggers', 0, 'status').lower() == 'enabled':
        triggers.append('SOURCE')
    if _get_trigger_status(item, 'trigger', 'timerTriggers'):
        triggers.append('TIMER')
    if _get_value(item, 'trigger', 'baseImageTrigger', 'status').lower() == 'enabled':
        triggers.append('BASE_IMAGE')
    triggers.sort()
    return ' ' if not triggers else str(', '.join(triggers))


def _get_value(item, *args):
    """Get a nested value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return str(item) if item or item == 0 else ' '
    except (KeyError, TypeError, IndexError):
        return ' '


def _get_array_value(item, *args):
    """Get a nested array value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return list(item) if item else []
    except (KeyError, TypeError, IndexError):
        return []


def _get_trigger_status(item, *args):
    """Check if at least one enabled trigger exists in a list.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        enabled = False
        if item:
            for trigger in item:
                if trigger['status'].lower() == "enabled":
                    enabled = True
                    break
        return enabled
    except (KeyError, TypeError, IndexError):
        return False


def _get_build_trigger(image_update_trigger, git_source_trigger, timer_trigger=None):
    if git_source_trigger.strip():
        return git_source_trigger
    if timer_trigger.strip():
        return 'Timer'
    if image_update_trigger.strip():
        return 'Image Update'
    return 'Manual'


def _format_datetime(date_string):
    from dateutil.parser import parse
    try:
        return parse(date_string).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        logger.debug("Unable to parse date_string '%s'", date_string)
        return date_string or ' '


def _get_duration(start_time, finish_time):
    from dateutil.parser import parse
    try:
        duration = parse(finish_time) - parse(start_time)
        hours = "{0:02d}".format((24 * duration.days) + (duration.seconds // 3600))
        minutes = "{0:02d}".format((duration.seconds % 3600) // 60)
        seconds = "{0:02d}".format(duration.seconds % 60)
        return "{0}:{1}:{2}".format(hours, minutes, seconds)
    except ValueError:
        logger.debug("Unable to get duration with start_time '%s' and finish_time '%s'", start_time, finish_time)
        return ' '


def add_timestamp(message):
    return "{} {}".format(datetime.utcnow(), message)
