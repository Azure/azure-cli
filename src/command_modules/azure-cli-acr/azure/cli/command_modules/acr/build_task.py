# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
from ._utils import (
    arm_deploy_template_build_task_create,
    validate_managed_registry
)
from .build import _check_image_name

BUILD_TASKS_NOT_SUPPORTED = 'Build Tasks are only supported for managed registries.'


def acr_build_task_create(
    cmd,
    client,
    build_task_name,
    registry_name,
    source_location,            
    image_name,
    git_access_token,
    source_branch="master",  
    docker_file_path='Dockerfile',
    os_type="Linux",
    cpu=1,
    resource_group_name=None):
    
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
    return client.get(resource_group_name, registry_name, build_task_name)


def acr_build_task_show(
    cmd,
    client,
    build_task_name,
    registry_name,
    resource_group_name=None):
    
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, build_task_name)


def acr_build_task_list(
    cmd,
    client,
    registry_name,
    resource_group_name=None):
    
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_build_task_delete(
    cmd,
    client,
    build_task_name,
    registry_name,
    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, build_task_name)


def acr_build_task_list_builds(
    cmd,
    client,
    registry_name,
    build_task_name=None,
    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    from ._client_factory import cf_acr_builds
    client_builds = cf_acr_builds(cmd.cli_ctx)\

    if build_task_name is None:        
        return client_builds.list(resource_group_name, registry_name)        
    else:
        filter_str = "BuildTaskName eq '{}'".format(build_task_name)
        return client_builds.list(resource_group_name, registry_name, filter=filter_str)


def acr_build_task_run(
    cmd,
    client,
    build_task_name,
    registry_name,
    no_logs=False,
    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    from ._client_factory import cf_acr_build_registries
    client_registries = cf_acr_build_registries(cmd.cli_ctx)
    buildRequest = {
        "type": "BuildTask",
        "buildTaskName": build_task_name
    }

    queued_build = LongRunningOperation(cmd.cli_ctx)(
        client_registries.queue_build(resource_group_name, registry_name, buildRequest))        
    if no_logs:
        return queued_build
    else:
        if queued_build:
            build_id = queued_build.build_id
            print("Queued a build with build-id: {}.".format(build_id))
            print("Starting to stream the logs...")
            acr_build_task_logs(cmd, client, registry_name, build_id)


def acr_build_task_logs(
    cmd,
    client,
    registry_name,
    build_id=None,
    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    if build_id is None:     
        # show logs for the last build
        paged_builds = acr_build_task_list_builds(cmd, client, registry_name)
        if paged_builds:
            builds = paged_builds.get(0)
            if builds:
                build_id = builds[0].build_id
                print("Showing logs for the last updated build...")
                print("Build-id: {}".format(build_id))
            
    from ._client_factory import cf_acr_builds
    from .build import acr_build_show_logs
    client_builds = cf_acr_builds(cmd.cli_ctx)
    
    return acr_build_show_logs(
        cmd,
        client_builds,
        registry_name,
        build_id,
        resource_group_name
    )
