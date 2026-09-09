# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import sdk_no_wait
from ..utils.validators import validate_resource_group


def flexible_server_maintenance_event_list(client, resource_group_name, server_name, maintenance_status=None):
    validate_resource_group(resource_group_name)
    return client.list(resource_group_name=resource_group_name,
                       server_name=server_name,
                       maintenance_status=maintenance_status)


def flexible_server_maintenance_event_show(client, resource_group_name, server_name, maintenance_event_id):
    validate_resource_group(resource_group_name)
    return client.get(resource_group_name=resource_group_name,
                      server_name=server_name,
                      maintenance_event_id=maintenance_event_id)


def flexible_server_maintenance_event_reschedule(client, resource_group_name, server_name,
                                                 maintenance_event_id, start_time, no_wait=False):
    validate_resource_group(resource_group_name)
    body = {"postponeToDateTime": start_time}
    return sdk_no_wait(no_wait,
                       client.begin_reschedule,
                       resource_group_name=resource_group_name,
                       server_name=server_name,
                       maintenance_event_id=maintenance_event_id,
                       body=body)


def flexible_server_maintenance_event_apply_now(client, resource_group_name, server_name,
                                                maintenance_event_id, no_wait=False):
    validate_resource_group(resource_group_name)
    return sdk_no_wait(no_wait,
                       client.begin_apply_now,
                       resource_group_name=resource_group_name,
                       server_name=server_name,
                       maintenance_event_id=maintenance_event_id)
