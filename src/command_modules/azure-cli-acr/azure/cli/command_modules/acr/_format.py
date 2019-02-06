# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
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


def build_output_format(result):
    return _output_format(result, _build_format_group)


def run_output_format(result):
    return _output_format(result, _run_format_group)


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
        ('SOURCE TRIGGER', _get_value(item, 'trigger', 'sourceTriggers', 0, 'status')),
        ('BASE IMAGE TRIGGER', _get_value(item, 'trigger', 'baseImageTrigger', 'baseImageTriggerType'))
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
        ('DURATION', _get_duration(_get_value(item, 'startTime'), _get_value(item, 'finishTime')))
    ])


def _run_format_group(item):
    return OrderedDict([
        ('RUN ID', _get_value(item, 'runId')),
        ('TASK', _get_value(item, 'task')),
        ('PLATFORM', _get_value(item, 'platform', 'os')),
        ('STATUS', _get_value(item, 'status')),
        ("TRIGGER", _get_build_trigger(_get_value(item, 'imageUpdateTrigger'),
                                       _get_value(item, 'sourceTrigger', 'eventType'))),
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


def _get_value(item, *args):
    """Get a nested value from a dict.
    :param dict item: The dict object
    """
    try:
        for arg in args:
            item = item[arg]
        return str(item) if item else ' '
    except (KeyError, TypeError, IndexError):
        return ' '


def _get_build_trigger(image_update_trigger, git_source_trigger):
    if git_source_trigger.strip():
        return git_source_trigger
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
