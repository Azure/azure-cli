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
    get_yaml_and_values
)
from ._client_factory import cf_acr_registries
from ._archive_utils import upload_source_code, check_remote_source_code
from .run import prepare_source_location

RUN_NOT_SUPPORTED = 'Run is only available for managed registries.'

logger = get_logger(__name__)


def acr_pack(cmd,  # pylint: disable=too-many-locals
            client,
            registry_name,
            source_location,
            file=None,
            values=None,
            set_value=None,
            set_secret=None,
            no_format=False,
            no_logs=False,
            no_wait=False,
            timeout=None,
            resource_group_name=None,
            os_type=None,
            platform=None,
            auth_mode=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, RUN_NOT_SUPPORTED)

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, os_type, platform)
    OS = cmd.get_models('OS')
    if platform_os != OS.linux.value:
        raise CLIError('Building with Buildpacks is only supported on Linux.')

    client_registries = cf_acr_registries(cmd.cli_ctx)
    source_location = prepare_source_location(
        source_location, client_registries, registry_name, resource_group_name)

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
        yaml_template, values_content = get_yaml_and_values(cmd_value, timeout, file)
        import base64
        request = EncodedTaskRunRequest(
            encoded_task_content=base64.b64encode(yaml_template.encode()).decode(),
            encoded_values_content=base64.b64encode(values_content.encode()).decode(),
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
