# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._utils import (
    validate_managed_registry
)


TASK_NOT_SUPPORTED = 'Task is only supported for managed registries.'

def acr_taskrun_show(cmd,
                     client,
                     taskrun_name,
                     registry_name,
                     resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, taskrun_name)

def acr_taskrun_list(cmd,
                     client,
                     registry_name,
                     resource_group_name=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)

def acr_taskrun_delete(cmd,
                       client,
                       taskrun_name,
                       registry_name,
                       resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, taskrun_name)