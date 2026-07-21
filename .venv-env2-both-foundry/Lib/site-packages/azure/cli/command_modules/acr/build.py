# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import uuid
import tempfile

import os

from knack.log import get_logger
from knack.util import CLIError

from ._utils import validate_managed_registry, get_validate_platform, get_source_and_custom_registry_credentials
from ._stream_utils import stream_logs
from ._archive_utils import upload_source_code, check_remote_source_code

logger = get_logger(__name__)

BUILD_NOT_SUPPORTED = 'Builds are only supported for managed registries.'


def acr_build(cmd,  # pylint: disable=too-many-locals
              client,
              registry_name,
              source_location,
              image_names=None,
              resource_group_name=None,
              agent_pool_name=None,
              timeout=None,
              arg=None,
              secret_arg=None,
              docker_file_path='',
              no_format=False,
              no_push=False,
              no_logs=False,
              no_wait=False,
              platform=None,
              target=None,
              auth_mode=None,
              log_template=None,
              source_acr_auth_id=None):
    registry, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, BUILD_NOT_SUPPORTED)

    from ._client_factory import cf_acr_registries_tasks
    client_registries = cf_acr_registries_tasks(cmd.cli_ctx)

    if os.path.exists(source_location):
        if not os.path.isdir(source_location):
            raise CLIError("Source location should be a local directory path or remote URL.")

        # NOTE: If docker_file_path is not specified, the default is Dockerfile in source_location.
        # Otherwise, it's based on current working directory.
        if not docker_file_path:
            docker_file_path = os.path.join(source_location, "Dockerfile")
            logger.info("'--file or -f' is not provided. '%s' is used.", docker_file_path)

        _check_local_docker_file(docker_file_path)

        tar_file_path = os.path.join(tempfile.gettempdir(
        ), 'build_archive_{}.tar.gz'.format(uuid.uuid4().hex))

        try:
            # NOTE: os.path.basename is unable to parse "\" in the file path
            original_docker_file_name = os.path.basename(
                docker_file_path.replace("\\", "/"))
            docker_file_in_tar = '{}_{}'.format(
                uuid.uuid4().hex, original_docker_file_name)

            source_location = upload_source_code(
                cmd, client_registries, registry_name, resource_group_name,
                source_location, tar_file_path,
                docker_file_path, docker_file_in_tar)
            # For local source, the docker file is added separately into tar as the new file name (docker_file_in_tar)
            # So we need to update the docker_file_path
            docker_file_path = docker_file_in_tar
        except Exception as err:
            raise CLIError(err)
        finally:
            try:
                logger.debug("Deleting the archived source code from '%s'...", tar_file_path)
                os.remove(tar_file_path)
            except OSError:
                pass
    else:
        # NOTE: If docker_file_path is not specified, the default is Dockerfile. It's the same as docker build command.
        if not docker_file_path:
            docker_file_path = "Dockerfile"
            logger.info("'--file or -f' is not provided. '%s' is used.", docker_file_path)

        source_location = check_remote_source_code(source_location)
        logger.warning("Sending context to registry: %s...", registry_name)

    is_push_enabled = _get_push_enabled_status(no_push, image_names)

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, platform)

    DockerBuildRequest, PlatformProperties, RoleAssignmentMode = cmd.get_models(
        'DockerBuildRequest',
        'PlatformProperties',
        'RoleAssignmentMode',
        operation_group='runs')

    registry_abac_enabled = registry.role_assignment_mode == RoleAssignmentMode.ABAC_REPOSITORY_PERMISSIONS

    docker_build_request = DockerBuildRequest(
        agent_pool_name=agent_pool_name,
        image_names=image_names,
        is_push_enabled=is_push_enabled,
        source_location=source_location,
        platform=PlatformProperties(
            os=platform_os,
            architecture=platform_arch,
            variant=platform_variant
        ),
        docker_file_path=docker_file_path,
        timeout=timeout,
        arguments=(arg if arg else []) + (secret_arg if secret_arg else []),
        target=target,
        credentials=get_source_and_custom_registry_credentials(
            cmd=cmd,
            auth_mode=auth_mode,
            source_acr_auth_id=source_acr_auth_id,
            registry_abac_enabled=registry_abac_enabled,
            deprecate_auth_mode=True
        ),
        log_template=log_template
    )

    queued = client_registries.schedule_run(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        run_request=docker_build_request)

    run_id = queued.run_id
    logger.warning("Queued a build with ID: %s", run_id)

    if no_wait:
        return queued

    logger.warning("Waiting for an agent...")

    if no_logs:
        from ._run_polling import get_run_with_polling
        return get_run_with_polling(cmd, client, run_id, registry_name, resource_group_name)

    return stream_logs(cmd, client, run_id, registry_name, resource_group_name, timeout, no_format, True)


def _warn_unsupported_image_name(image_names):
    for img in image_names:
        if ".Build.ID" in img:
            logger.warning(".Build.ID is no longer supported as a valid substitution, use .Run.ID instead.")
            break


def _get_push_enabled_status(no_push, image_names):
    if no_push:
        is_push_enabled = False
    else:
        if image_names:
            is_push_enabled = True
            _warn_unsupported_image_name(image_names)
        else:
            is_push_enabled = False
            logger.warning("'--image or -t' is not provided. Skipping image push after build.")
    return is_push_enabled


def _check_local_docker_file(docker_file_path):
    if not os.path.isfile(docker_file_path):
        raise CLIError("Unable to find '{}'.".format(docker_file_path))
