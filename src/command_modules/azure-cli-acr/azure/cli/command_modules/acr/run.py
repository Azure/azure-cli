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

from ._stream_utils import stream_logs
from ._utils import validate_managed_registry, get_validate_platform
from ._client_factory import cf_acr_registries
from ._archive_utils import upload_source_code, check_remote_source_code

RUN_NOT_SUPPORTED = 'Run is only available for managed registries.'

logger = get_logger(__name__)


def acr_run(cmd,  # pylint: disable=too-many-locals
            client,
            registry_name,
            source_location,
            file='acb.yaml',
            values=None,
            set_value=None,
            set_secret=None,
            no_format=False,
            no_logs=False,
            no_wait=False,
            timeout=None,
            resource_group_name=None,
            os_type=None,
            platform=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, RUN_NOT_SUPPORTED)

    client_registries = cf_acr_registries(cmd.cli_ctx)

    if os.path.exists(source_location):
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

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, os_type, platform)

    FileTaskRunRequest, PlatformProperties = cmd.get_models('FileTaskRunRequest', 'PlatformProperties')
    request = FileTaskRunRequest(
        task_file_path=file,
        values_file_path=values,
        values=(set_value if set_value else []) + (set_secret if set_secret else []),
        source_location=source_location,
        timeout=timeout,
        platform=PlatformProperties(
            os=platform_os,
            architecture=platform_arch,
            variant=platform_variant
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
