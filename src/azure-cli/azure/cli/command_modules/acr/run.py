# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import uuid
import tempfile
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation

from ._constants import ACR_TASK_YAML_DEFAULT_NAME
from ._stream_utils import stream_logs
from ._utils import (
    validate_managed_registry,
    get_validate_platform,
    get_custom_registry_credentials,
    get_yaml_template
)
from ._client_factory import cf_acr_registries_tasks
from ._archive_utils import upload_source_code, check_remote_source_code

RUN_NOT_SUPPORTED = 'Run is only available for managed registries.'
NULL_SOURCE_LOCATION = "/dev/null"

logger = get_logger(__name__)


def acr_run(cmd,  # pylint: disable=too-many-locals
            client,
            registry_name,
            source_location,
            file=None,
            values=None,
            set_value=None,
            set_secret=None,
            cmd_value=None,
            no_format=False,
            no_logs=False,
            no_wait=False,
            timeout=None,
            resource_group_name=None,
            platform=None,
            auth_mode=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, RUN_NOT_SUPPORTED)

    if cmd_value and file:
        raise CLIError(
            "Azure Container Registry can run with either "
            "--cmd myCommand /dev/null or "
            "-f myFile mySourceLocation, but not both.")

    client_registries = cf_acr_registries_tasks(cmd.cli_ctx)
    source_location = prepare_source_location(
        source_location, client_registries, registry_name, resource_group_name)

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, platform)

    EncodedTaskRunRequest, FileTaskRunRequest, PlatformProperties = cmd.get_models(
        'EncodedTaskRunRequest', 'FileTaskRunRequest', 'PlatformProperties')

    if source_location:
        request = FileTaskRunRequest(
            task_file_path=file if file else ACR_TASK_YAML_DEFAULT_NAME,
            values_file_path=values,
            values=(set_value if set_value else []) + (set_secret if set_secret else []),
            source_location=source_location,
            timeout=timeout,
            platform=PlatformProperties(
                os=platform_os,
                architecture=platform_arch,
                variant=platform_variant
            ),
            credentials=get_custom_registry_credentials(
                cmd=cmd,
                auth_mode=auth_mode
            )
        )
    else:
        yaml_template = get_yaml_template(cmd_value, timeout, file)
        import base64
        request = EncodedTaskRunRequest(
            encoded_task_content=base64.b64encode(yaml_template.encode()).decode(),
            values=(set_value if set_value else []) + (set_secret if set_secret else []),
            source_location=source_location,
            timeout=timeout,
            platform=PlatformProperties(
                os=platform_os,
                architecture=platform_arch,
                variant=platform_variant
            ),
            credentials=get_custom_registry_credentials(
                cmd=cmd,
                auth_mode=auth_mode
            )
        )

    queued = LongRunningOperation(cmd.cli_ctx)(client_registries.schedule_run(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        run_request=request))

    run_id = queued.run_id
    logger.warning("Queued a run with ID: %s", run_id)

    if no_wait:
        return queued

    logger.warning("Waiting for an agent...")

    if no_logs:
        from ._run_polling import get_run_with_polling
        return get_run_with_polling(cmd, client, run_id, registry_name, resource_group_name)

    return stream_logs(client, run_id, registry_name, resource_group_name, no_format, True)


def prepare_source_location(source_location, client_registries, registry_name, resource_group_name):
    if source_location.lower() == NULL_SOURCE_LOCATION:
        source_location = None
    elif os.path.exists(source_location):
        if not os.path.isdir(source_location):
            raise CLIError(
                "Source location should be a local directory path or remote URL.")

        tar_file_path = os.path.join(tempfile.gettempdir(
        ), 'run_archive_{}.tar.gz'.format(uuid.uuid4().hex))

        try:
            source_location = upload_source_code(
                client_registries, registry_name, resource_group_name,
                source_location, tar_file_path, "", "")
        except Exception as err:
            raise CLIError(err)
        finally:
            try:
                logger.debug(
                    "Deleting the archived source code from '%s'...", tar_file_path)
                os.remove(tar_file_path)
            except OSError:
                pass
    else:
        source_location = check_remote_source_code(source_location)
        logger.warning("Sending context to registry: %s...", registry_name)

    return source_location
