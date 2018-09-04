# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import uuid
import tempfile

import os

from knack.log import get_logger
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.commands import LongRunningOperation

from azure.mgmt.containerregistry.v2018_02_01_preview.operations import BuildsOperations
from .sdk.models import (
    DockerBuildRequest,
    PlatformProperties,
    Architecture,
    OS
)

from ._utils import validate_managed_registry
from ._build_polling import get_build_with_polling
from ._azure_utils import get_blob_info
from ._stream_utils import stream_logs
from ._archive_utils import upload_source_code, check_remote_source_code

from azure.storage.blob import (
    AppendBlobService,
)

logger = get_logger(__name__)


BUILD_NOT_SUPPORTED = 'Builds are only supported for managed registries.'


def acr_build_show_logs(client,
                        build_id,
                        registry_name,
                        resource_group_name,
                        no_format=False,
                        raise_error_on_failure=False):
    log_file_sas = None
    error_message = "Could not get build logs for build ID: {}".format(
        build_id)
    try:
        if isinstance(client, BuildsOperations):
            # backward compatibility for build-task
            build_log_result = client.get_log_link(
                resource_group_name=resource_group_name,
                registry_name=registry_name,
                build_id=build_id)
        else:
            build_log_result = client.get_log_sas_url(
                resource_group_name=resource_group_name,
                registry_name=registry_name,
                run_id=build_id)
        log_file_sas = build_log_result.log_link
    except (AttributeError, CloudError) as e:
        logger.debug("%s Exception: %s", error_message, e)
        raise CLIError(error_message)

    if not log_file_sas:
        logger.debug("%s Empty SAS URL.", error_message)
        raise CLIError(error_message)

    account_name, endpoint_suffix, container_name, blob_name, sas_token = get_blob_info(
        log_file_sas)

    stream_logs(no_format,
                byte_size=1024,  # 1 KiB
                timeout_in_seconds=1800,  # 30 minutes
                blob_service=AppendBlobService(
                    account_name=account_name,
                    sas_token=sas_token,
                    endpoint_suffix=endpoint_suffix),
                container_name=container_name,
                blob_name=blob_name,
                raise_error_on_failure=raise_error_on_failure)


def acr_build(cmd,
              client,
              registry_name,
              source_location,
              image_names=None,
              resource_group_name=None,
              timeout=None,
              arg=None,
              secret_arg=None,
              docker_file_path='Dockerfile',
              no_format=False,
              no_push=False,
              no_logs=False,
              os_type=OS.linux):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_NOT_SUPPORTED)

    # TODO: remove
    from ._client_factory import cf_acr_registries_build
    client_registries = cf_acr_registries_build(cmd.cli_ctx)

    if os.path.exists(source_location):
        if not os.path.isdir(source_location):
            raise CLIError(
                "Source location should be a local directory path or remote URL.")

        _check_local_docker_file(source_location, docker_file_path)

        tar_file_path = os.path.join(tempfile.gettempdir(
        ), 'source_archive_{}.tar.gz'.format(uuid.uuid4().hex))

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
                logger.debug(
                    "Deleting the archived source code from '%s'.", tar_file_path)
                os.remove(tar_file_path)
            except OSError:
                pass
    else:
        source_location = check_remote_source_code(source_location)
        logger.warning("Sending build context to ACR...")

    if no_push:
        is_push_enabled = False
    else:
        if image_names:
            is_push_enabled = True
        else:
            is_push_enabled = False
            logger.warning(
                "'--image or -t' is not provided. Skipping image push after build.")

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

    build_id = queued_build.run_id
    logger.warning("Queued a build with build ID: %s", build_id)
    logger.warning("Waiting for build agent...")

    if no_logs:
        return get_build_with_polling(client, build_id, registry_name, resource_group_name)

    return acr_build_show_logs(client, build_id, registry_name, resource_group_name, no_format, True)


def _check_local_docker_file(source_location, docker_file_path):
    if not os.path.isfile(os.path.join(source_location, docker_file_path)):
        raise CLIError("Unable to find '{}' in '{}'.".format(
            docker_file_path, source_location))
