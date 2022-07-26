# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation

from ._constants import ACR_TASK_YAML_DEFAULT_NAME
from ._stream_utils import stream_logs
from ._utils import (
    validate_managed_registry,
    get_validate_platform,
    get_custom_registry_credentials,
    get_yaml_template,
    prepare_source_location
)
from ._client_factory import cf_acr_registries_tasks

RUN_NOT_SUPPORTED = 'Run is only available for managed registries.'

logger = get_logger(__name__)


def acr_run(cmd,  # pylint: disable=too-many-locals
            client,
            registry_name,
            source_location,
            agent_pool_name=None,
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
            auth_mode=None,
            log_template=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, RUN_NOT_SUPPORTED)

    if cmd_value and file:
        raise CLIError(
            "Azure Container Registry can run with either "
            "--cmd myCommand /dev/null or "
            "-f myFile mySourceLocation, but not both.")

    client_registries = cf_acr_registries_tasks(cmd.cli_ctx)
    source_location = prepare_source_location(
        cmd, source_location, client_registries, registry_name, resource_group_name)

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, platform)

    EncodedTaskRunRequest, FileTaskRunRequest, PlatformProperties = cmd.get_models(
        'EncodedTaskRunRequest', 'FileTaskRunRequest', 'PlatformProperties', operation_group='runs')

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
            ),
            agent_pool_name=agent_pool_name,
            log_template=log_template
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
            ),
            agent_pool_name=agent_pool_name,
            log_template=log_template
        )

    queued = LongRunningOperation(cmd.cli_ctx)(client_registries.begin_schedule_run(
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

    return stream_logs(cmd, client, run_id, registry_name, resource_group_name, timeout, no_format, True)
