# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
from ._utils import arm_deploy_template_build_task_create
from ._utils import validate_managed_registry
from .build import _check_image_name

BUILD_TASKS_NOT_SUPPORTED = 'Build Tasks are only supported for managed registries.'


def acr_build_task_create(
    cmd,
    client,
    build_task_name,
    registry_name,
    source_location,            
    source_branch,  
    image_name,
    docker_file_path,
    git_access_token,
    resource_group_name=None,
    os_type="Linux",
    cpu=2):
    
    registry, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    LongRunningOperation(cmd.cli_ctx)(
            arm_deploy_template_build_task_create(
                cmd.cli_ctx,
                build_task_name,
                registry_name,
                registry.location,
                resource_group_name,
                source_location,
                source_branch,              
                _check_image_name(image_name),
                docker_file_path,
                git_access_token,
                os_type,
                cpu)
        )

def acr_build_task_show(
    cmd,
    client,
    build_task_name,
    registry_name,
    resource_group_name=None):
    
    registry, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    return client.get(resource_group_name, registry_name, build_task_name)
