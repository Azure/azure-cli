# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=unused-variable

import re

from datetime import timedelta
from isodate import parse_duration
from knack.util import CLIError

# PARAMETER VALIDATORS
# Type ISO 8061 duration

iso8601pattern = re.compile("^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+.)?(\\d+S)?)?$")
timedeltapattern = re.compile("^\\d+:\\d+:\\d+$")


def _validate_lock_duration(namespace):
    if namespace.lock_duration:
        if iso8601pattern.match(namespace.lock_duration):
            if parse_duration(namespace.lock_duration) > timedelta(days=0, minutes=6, seconds=0):
                raise CLIError(
                    '--lock-duration Value Error : {0} value, The maximum value for LockDuration is 5 minutes; the default value is 1 minute.'.format(
                        namespace.lock_duration))
        elif timedeltapattern.match(namespace.lock_duration):
            day, miniute, seconds = namespace.lock_duration.split(":")
            if int(day) > 0 or int(miniute) > 6:
                raise CLIError(
                    '--lock-duration Value Error : {0} value, The maximum value for LockDuration is 5 minutes; the default value is 1 minute.'.format(
                        namespace.lock_duration))
        else:
            raise CLIError('--lock-duration Value Error : {0} value is not in ISO 8601 timespan / duration format. e.g.'
                           ' PT10M for duration of 10 min or 00:10:00 for duration of 10 min'.format(namespace.lock_duration))


def _validate_default_message_time_to_live(namespace):
    if namespace.default_message_time_to_live:
        if not iso8601pattern.match(namespace.default_message_time_to_live) and not timedeltapattern.match(namespace.default_message_time_to_live):
            raise CLIError('--default-message-time-to-live Value Error : {0} value is not in ISO 8601 timespan / duration format. e.g. PT10M for duration of 10 min or 00:10:00 for duration of 10 min'.format(namespace.default_message_time_to_live))


def _validate_duplicate_detection_history_time_window(namespace):
    if namespace.duplicate_detection_history_time_window:
        if iso8601pattern.match(namespace.duplicate_detection_history_time_window):
            pass
        elif timedeltapattern.match(namespace.duplicate_detection_history_time_window):
            pass
        else:
            raise CLIError('--duplicate-detection-history-time-window Value Error : {0} value is not in ISO 8601 timespan / duration format. e.g. PT10M for duration of 10 min or 00:10:00 for duration of 10 min'.format(namespace.duplicate_detection_history_time_window))


def _validate_auto_delete_on_idle(namespace):
    if namespace.auto_delete_on_idle:
        if iso8601pattern.match(namespace.auto_delete_on_idle):
            pass
        elif timedeltapattern.match(namespace.auto_delete_on_idle):
            pass
        else:
            raise CLIError('--auto-delete-on-idle Value Error : {0} value is not in ISO 8601 timespan / duration format. e.g. PT10M for duration of 10 min or 00:10:00 for duration of 10 min'.format(namespace.auto_delete_on_idle))


def validate_partner_namespace(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.partner_namespace:
        if not is_valid_resource_id(namespace.partner_namespace):
            namespace.partner_namespace = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.ServiceBus',
                type='namespaces',
                name=namespace.partner_namespace)


def validate_target_namespace(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.target_namespace:
        if not is_valid_resource_id(namespace.target_namespace):
            namespace.target_namespace = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.ServiceBus',
                type='namespaces',
                name=namespace.target_namespace)


def validate_premiumsku_capacity(namespace):
    if namespace.sku and namespace.sku != 'Premium' and namespace.capacity:
        raise CLIError('--capacity - This property is only applicable to namespaces of Premium SKU')
