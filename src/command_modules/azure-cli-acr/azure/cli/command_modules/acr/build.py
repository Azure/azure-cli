# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import uuid
import tempfile

import os

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation

from azure.mgmt.containerregistry.v2018_09_01.models import (
    DockerBuildRequest,
    PlatformProperties,
    Architecture,
    OS
)

from ._utils import validate_managed_registry
from ._run_polling import get_run_with_polling
from ._stream_utils import stream_logs
from ._archive_utils import upload_source_code, check_remote_source_code

logger = get_logger(__name__)


BUILD_NOT_SUPPORTED = 'Builds are only supported for managed registries.'


def acr_build(cmd,
              client,
              registry_name,
              source_location,
              image_names=None,
              resource_group_name=None,
              timeout=None,
              arg=None,
              secret_arg=None,
              docker_file_path='',
              no_format=False,
              no_push=False,
              no_logs=False,
              os_type=OS.linux.value):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_NOT_SUPPORTED)

    from ._client_factory import cf_acr_registries
    client_registries = cf_acr_registries(cmd.cli_ctx)

    if os.path.exists(source_location):
        if not os.path.isdir(source_location):
            raise CLIError("Source location should be a local directory path or remote URL.")

        # NOTE: If docker_file_path is not specified, the default is Dockerfile in source_location.
        # Otherwise, it's based on current working directory.
        if not docker_file_path:
            docker_file_path = os.path.join(source_location, "Dockerfile")

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
                client_registries, registry_name, resource_group_name,
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
        source_location = check_remote_source_code(source_location)
        logger.warning("Sending context to registry: %s...", registry_name)

    if no_push:
        is_push_enabled = False
    else:
        if image_names:
            is_push_enabled = True
        else:
            is_push_enabled = False
            logger.warning("'--image or -t' is not provided. Skipping image push after build.")

    docker_build_request = DockerBuildRequest(
        image_names=image_names,
        is_push_enabled=is_push_enabled,
        source_location=source_location,
        platform=PlatformProperties(
            os=os_type, architecture=Architecture.amd64.value),
        docker_file_path=docker_file_path,
        timeout=timeout,
        arguments=(arg if arg else []) + (secret_arg if secret_arg else []))

    queued_build = LongRunningOperation(cmd.cli_ctx)(client_registries.schedule_run(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        run_request=docker_build_request))

    run_id = queued_build.run_id
    logger.warning("Queued a build with ID: %s", run_id)
    logger.warning("Waiting for agent...")

    if no_logs:
        return get_run_with_polling(client, run_id, registry_name, resource_group_name)

    return stream_logs(client, run_id, registry_name, resource_group_name, no_format, True)


def _check_local_docker_file(docker_file_path):
    if not os.path.isfile(docker_file_path):
        raise CLIError("Unable to find '{}'.".format(docker_file_path))
