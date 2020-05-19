# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation

from ._constants import ACR_CACHED_BUILDER_IMAGES
from ._stream_utils import stream_logs
from ._utils import (
    get_registry_by_name,
    get_validate_platform,
    get_custom_registry_credentials
)
from ._client_factory import cf_acr_registries_tasks
from .run import prepare_source_location

PACK_TASK_YAML_FMT = '''version: v1.1.0
steps:
  - cmd: mcr.microsoft.com/oryx/pack:{pack_image_tag} build {image_name} --builder {builder} {no_pull} --env REGISTRY_NAME=$Registry -p .
    timeout: 28800
  - push: ["{image_name}"]
    timeout: 1800
'''

logger = get_logger(__name__)


def acr_pack_build(cmd,  # pylint: disable=too-many-locals
                   client,
                   registry_name,
                   image_name,
                   source_location,
                   builder,
                   pack_image_tag='stable',
                   agent_pool_name=None,
                   pull=False,
                   no_format=False,
                   no_logs=False,
                   no_wait=False,
                   timeout=None,
                   resource_group_name=None,
                   platform=None,
                   auth_mode=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name)

    client_registries = cf_acr_registries_tasks(cmd.cli_ctx)
    source_location = prepare_source_location(
        cmd, source_location, client_registries, registry_name, resource_group_name)
    if not source_location:
        raise CLIError('Building with Buildpacks requires a valid source location.')

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, platform)
    OS = cmd.get_models('OS')
    if platform_os != OS.linux.value.lower():
        raise CLIError('Building with Buildpacks is only supported on Linux.')

    if builder not in ACR_CACHED_BUILDER_IMAGES and not pull:
        logger.warning('Using a non-cached builder image; `--pull` is probably needed as well')

    registry_prefixes = '$Registry/', registry.login_server + '/'
    # If the image name doesn't have any required prefix, add it
    if all((not image_name.startswith(prefix) for prefix in registry_prefixes)):
        original_image_name = image_name
        image_name = registry_prefixes[0] + image_name
        logger.debug('Modified image name from %s to %s', original_image_name, image_name)

    yaml_body = PACK_TASK_YAML_FMT.format(
        image_name=image_name,
        builder=builder,
        pack_image_tag=pack_image_tag,
        no_pull='--no-pull' if not pull else '')

    EncodedTaskRunRequest, PlatformProperties = cmd.get_models('EncodedTaskRunRequest', 'PlatformProperties')

    request = EncodedTaskRunRequest(
        encoded_task_content=base64.b64encode(yaml_body.encode()).decode(),
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
        agent_pool_name=agent_pool_name
    )

    queued = LongRunningOperation(cmd.cli_ctx)(client_registries.schedule_run(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        run_request=request))

    run_id = queued.run_id
    logger.warning('Queued a run with ID: %s', run_id)

    if no_wait:
        return queued

    logger.warning('Waiting for an agent...')

    if no_logs:
        from ._run_polling import get_run_with_polling
        return get_run_with_polling(cmd, client, run_id, registry_name, resource_group_name)

    return stream_logs(cmd, client, run_id, registry_name, resource_group_name, no_format, True)
