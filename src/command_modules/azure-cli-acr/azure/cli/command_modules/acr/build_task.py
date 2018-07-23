# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.exceptions import ValidationError
from msrestazure.azure_exceptions import CloudError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    BuildTask,
    SourceRepositoryProperties,
    SourceControlAuthInfo,
    PlatformProperties,
    DockerBuildStep,
    BuildTaskBuildRequest,
    BuildTaskUpdateParameters,
    SourceRepositoryUpdateParameters,
    DockerBuildStepUpdateParameters
)
from ._utils import validate_managed_registry
from .build import acr_build_show_logs
from ._build_polling import get_build_with_polling


logger = get_logger(__name__)


BUILD_TASKS_NOT_SUPPORTED = 'Build Tasks are only supported for managed registries.'
DEFAULT_TOKEN_TYPE = 'PAT'


def acr_build_task_create(cmd,  # pylint: disable=too-many-locals
                          client,
                          build_task_name,
                          registry_name,
                          repository_url,
                          image_names,
                          git_access_token,
                          alias=None,
                          status='Enabled',
                          os_type='Linux',
                          cpu=2,
                          timeout=3600,
                          commit_trigger_enabled=True,
                          branch='master',
                          no_push=False,
                          no_cache=False,
                          docker_file_path="Dockerfile",
                          build_arg=None,
                          secret_build_arg=None,
                          base_image_trigger='Runtime',
                          resource_group_name=None):
    registry, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    source_control_type = 'VisualStudioTeamService'
    if 'GITHUB.COM' in repository_url.upper():
        source_control_type = 'GitHub'

    build_task_create_parameters = BuildTask(
        location=registry.location,
        alias=alias if alias else build_task_name,
        source_repository=SourceRepositoryProperties(
            source_control_type=source_control_type,
            repository_url=repository_url,
            is_commit_trigger_enabled=commit_trigger_enabled,
            source_control_auth_properties=SourceControlAuthInfo(
                token=git_access_token,
                token_type=DEFAULT_TOKEN_TYPE,
                refresh_token='',
                scope='repo',
                expires_in=1313141
            )
        ),
        platform=PlatformProperties(os_type=os_type, cpu=cpu),
        status=status,
        timeout=timeout
    )

    try:
        build_task = LongRunningOperation(cmd.cli_ctx)(
            client.create(resource_group_name=resource_group_name,
                          registry_name=registry_name,
                          build_task_name=build_task_name,
                          build_task_create_parameters=build_task_create_parameters))
    except ValidationError as e:
        raise CLIError(e)

    from ._client_factory import cf_acr_build_steps
    client_build_steps = cf_acr_build_steps(cmd.cli_ctx)

    docker_build_step = DockerBuildStep(
        branch=branch,
        image_names=image_names,
        is_push_enabled=not no_push,
        no_cache=no_cache,
        docker_file_path=docker_file_path,
        build_arguments=(build_arg if build_arg else []) + (secret_build_arg if secret_build_arg else []),
        base_image_trigger=base_image_trigger
    )

    try:
        build_step = LongRunningOperation(cmd.cli_ctx)(
            client_build_steps.create(resource_group_name=resource_group_name,
                                      registry_name=registry_name,
                                      build_task_name=build_task_name,
                                      step_name=_get_build_step_name(build_task_name),
                                      properties=docker_build_step))
        setattr(build_task, 'properties', build_step.properties)
    except ValidationError as e:
        raise CLIError(e)

    return build_task


def acr_build_task_show(cmd,
                        client,
                        build_task_name,
                        registry_name,
                        with_secure_properties=False,
                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    build_task = client.get(resource_group_name, registry_name, build_task_name)

    from ._client_factory import cf_acr_build_steps
    client_build_steps = cf_acr_build_steps(cmd.cli_ctx)

    try:
        build_step = client_build_steps.get(resource_group_name,
                                            registry_name,
                                            build_task_name,
                                            _get_build_step_name(build_task_name))
        setattr(build_task, 'properties', build_step.properties)
    except CloudError as e:
        if e.status_code != 404:
            raise
        logger.warning("Could not get build task details. Build task basic information is printed.")

    if not with_secure_properties:
        return build_task

    try:
        source_repository = client.list_source_repository_properties(resource_group_name,
                                                                     registry_name,
                                                                     build_task_name)
        setattr(getattr(build_task, 'source_repository'),
                'source_control_auth_properties',
                getattr(source_repository, 'source_control_auth_properties'))
    except CloudError as e:
        if e.status_code != 403:
            raise
        logger.warning("No permission to get source repository secure properties.")

    try:
        build_arguments = client_build_steps.list_build_arguments(resource_group_name=resource_group_name,
                                                                  registry_name=registry_name,
                                                                  build_task_name=build_task_name,
                                                                  step_name=_get_build_step_name(build_task_name))
        setattr(getattr(build_task, 'properties'), 'buildArguments', list(build_arguments))
    except CloudError as e:
        if e.status_code != 403:
            raise
        logger.warning("No permission to get secure build arguments.")
    return build_task


def acr_build_task_list(cmd,
                        client,
                        registry_name,
                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_build_task_delete(cmd,
                          client,
                          build_task_name,
                          registry_name,
                          resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, build_task_name)


def acr_build_task_update(cmd,  # pylint: disable=too-many-locals
                          client,
                          build_task_name,
                          registry_name,
                          resource_group_name=None,
                          # build task parameters
                          alias=None,
                          status=None,
                          os_type=None,
                          cpu=None,
                          timeout=None,
                          repository_url=None,
                          commit_trigger_enabled=None,
                          git_access_token=None,
                          # build step parameters
                          branch=None,
                          image_names=None,
                          no_push=None,
                          no_cache=None,
                          docker_file_path=None,
                          build_arg=None,
                          secret_build_arg=None,
                          base_image_trigger=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    build_task = client.get(resource_group_name, registry_name, build_task_name)
    # pylint: disable=too-many-boolean-expressions
    if alias or status or os_type or cpu or timeout or repository_url or commit_trigger_enabled or git_access_token:
        build_task_update_parameters = BuildTaskUpdateParameters()
        build_task_update_parameters.alias = alias
        build_task_update_parameters.status = status
        build_task_update_parameters.platform = PlatformProperties(os_type=os_type or build_task.platform.os_type,
                                                                   cpu=cpu)
        build_task_update_parameters.timeout = timeout
        build_task_update_parameters.source_repository = SourceRepositoryUpdateParameters(
            source_control_auth_properties=SourceControlAuthInfo(
                token=git_access_token, token_type=DEFAULT_TOKEN_TYPE) if git_access_token else None,
            is_commit_trigger_enabled=commit_trigger_enabled)
        build_task = LongRunningOperation(cmd.cli_ctx)(
            client.update(resource_group_name=resource_group_name,
                          registry_name=registry_name,
                          build_task_name=build_task_name,
                          step_name=_get_build_step_name(build_task_name),
                          build_task_update_parameters=build_task_update_parameters))

    from ._client_factory import cf_acr_build_steps
    client_build_steps = cf_acr_build_steps(cmd.cli_ctx)

    build_step = None
    # pylint: disable=too-many-boolean-expressions
    if branch or image_names or no_push is not None or no_cache is not None or \
       docker_file_path or build_arg or secret_build_arg or base_image_trigger:
        build_step_update_parameters = DockerBuildStepUpdateParameters()
        build_step_update_parameters.branch = branch
        build_step_update_parameters.image_names = image_names
        build_step_update_parameters.is_push_enabled = (not no_push) if no_push is not None else None
        build_step_update_parameters.no_cache = no_cache
        build_step_update_parameters.docker_file_path = docker_file_path
        build_step_update_parameters.build_arguments = build_arg + secret_build_arg \
            if build_arg and secret_build_arg else build_arg or secret_build_arg
        build_step_update_parameters.base_image_trigger = base_image_trigger

        try:
            build_step = LongRunningOperation(cmd.cli_ctx)(
                client_build_steps.update(resource_group_name=resource_group_name,
                                          registry_name=registry_name,
                                          build_task_name=build_task_name,
                                          step_name=_get_build_step_name(build_task_name),
                                          properties=build_step_update_parameters))
        except CloudError as e:
            if e.status_code != 404:
                raise
            logger.warning("Could not update build task details. Build task basic information is updated.")

    # If build step is not updated, get it here
    if not build_step:
        try:
            build_step = client_build_steps.get(resource_group_name,
                                                registry_name,
                                                build_task_name,
                                                _get_build_step_name(build_task_name))
        except CloudError as e:
            if e.status_code != 404:
                raise

    if build_step:
        setattr(build_task, 'properties', build_step.properties)

    return build_task


def acr_build_task_update_build(cmd,
                                client,
                                build_id,
                                registry_name,
                                no_archive=None,
                                resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    is_archive_enabled = not no_archive if no_archive is not None else None

    return client.update(resource_group_name=resource_group_name,
                         registry_name=registry_name,
                         build_id=build_id,
                         is_archive_enabled=is_archive_enabled)


def _get_build_step_name(build_task_name):
    return '{}StepName'.format(build_task_name)


def acr_build_task_run(cmd,
                       client,  # cf_acr_builds
                       build_task_name,
                       registry_name,
                       no_logs=False,
                       resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    from ._client_factory import cf_acr_registries
    client_registries = cf_acr_registries(cmd.cli_ctx)

    queued_build = LongRunningOperation(cmd.cli_ctx)(
        client_registries.queue_build(resource_group_name,
                                      registry_name,
                                      BuildTaskBuildRequest(build_task_name=build_task_name)))

    build_id = queued_build.build_id
    logger.warning("Queued a build with build ID: %s", build_id)
    logger.warning("Waiting for build agent...")

    if no_logs:
        return get_build_with_polling(client, build_id, registry_name, resource_group_name)

    return acr_build_show_logs(client, build_id, registry_name, resource_group_name, True)


def acr_build_task_show_build(cmd,
                              client,  # cf_acr_builds
                              build_id,
                              registry_name,
                              resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, build_id)


def acr_build_task_list_builds(cmd,
                               client,  # cf_acr_builds
                               registry_name,
                               top=15,
                               build_task_name=None,
                               build_status=None,
                               image=None,
                               resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    filter_str = None
    filter_str = _add_build_filter(filter_str, 'BuildTaskName', build_task_name, 'eq')
    filter_str = _add_build_filter(filter_str, 'Status', build_status, 'eq')

    if image:
        from .repository import get_image_digest
        try:
            repository, _, manifest = get_image_digest(cmd.cli_ctx, registry_name, resource_group_name, image)
            filter_str = _add_build_filter(
                filter_str, 'OutputImageManifests', '{}@{}'.format(repository, manifest), 'contains')
        except CLIError as e:
            raise CLIError("Could not find image '{}'. {}".format(image, e))

    return client.list(resource_group_name, registry_name, filter=filter_str, top=top)


def _add_build_filter(orig_filter, name, value, operator):
    if not value:
        return orig_filter

    if operator == 'contains':
        new_filter_str = "contains({}, '{}')".format(name, value)
    elif operator == 'eq':
        new_filter_str = "{} eq '{}'".format(name, value)
    else:
        raise ValueError("Allowed filter operator: {}".format(['contains', 'eq']))

    return "{} and {}".format(orig_filter, new_filter_str) if orig_filter else new_filter_str


def acr_build_task_logs(cmd,
                        client,  # cf_acr_builds
                        registry_name,
                        build_id=None,
                        build_task_name=None,
                        image=None,
                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_TASKS_NOT_SUPPORTED)

    if not build_id:
        # show logs for the last build
        paged_builds = acr_build_task_list_builds(cmd,
                                                  client,
                                                  registry_name,
                                                  top=1,
                                                  build_task_name=build_task_name,
                                                  image=image)
        try:
            build_id = paged_builds.get(0)[0].build_id
            logger.warning(_get_list_builds_message(base_message="Showing logs of the last created build",
                                                    build_task_name=build_task_name,
                                                    image=image))
            logger.warning("Build ID: %s", build_id)
        except (AttributeError, KeyError, TypeError, IndexError):
            raise CLIError(_get_list_builds_message(base_message="Could not find the last created build",
                                                    build_task_name=build_task_name,
                                                    image=image))

    return acr_build_show_logs(client, build_id, registry_name, resource_group_name)


def _get_list_builds_message(base_message, build_task_name=None, image=None):
    if build_task_name:
        base_message = "{} for build task '{}'".format(base_message, build_task_name)
    if image:
        base_message = "{} for image '{}'".format(base_message, image)
    return "{}.".format(base_message)
