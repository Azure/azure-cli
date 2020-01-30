# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.util import get_file_json, shell_safe_json_parse

from azure.cli.command_modules.deploymentmanager._client_factory import (
    cf_artifact_sources,
    cf_service_topologies,
    cf_services,
    cf_service_units,
    cf_steps,
    cf_rollouts)

from azure.mgmt.deploymentmanager.models import (
    SasAuthentication,
    ArtifactSource,
    ServiceTopologyResource,
    ServiceResource,
    ServiceUnitResource,
    ServiceUnitArtifacts,
    StepResource,
    WaitStepProperties,
    WaitStepAttributes)

logger = get_logger(__name__)


# pylint: disable=unused-argument
def cli_artifact_source_create(
        cmd,
        resource_group_name,
        artifact_source_name,
        sas_uri,
        artifact_root=None,
        location=None,
        tags=None):

    if location is None:
        location = get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    sasAuthentication = SasAuthentication(sas_uri=sas_uri)
    artifact_source = ArtifactSource(
        source_type="AzureStorage",
        artifact_root=artifact_root,
        authentication=sasAuthentication,
        location=location,
        tags=tags)

    client = cf_artifact_sources(cmd.cli_ctx)
    return client.create_or_update(
        resource_group_name=resource_group_name,
        artifact_source_name=artifact_source_name,
        artifact_source_info=artifact_source)


def cli_artifact_source_update(
        cmd,
        instance,
        sas_uri=None,
        artifact_root=None,
        tags=None):

    if sas_uri:
        sasAuthentication = SasAuthentication(sas_uri=sas_uri)
        instance.authentication = sasAuthentication

    instance.artifact_root = artifact_root
    instance.tags = tags

    return instance


def cli_service_topology_create(
        cmd,
        resource_group_name,
        service_topology_name,
        artifact_source=None,
        location=None,
        tags=None):

    if location is None:
        location = get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    if artifact_source is not None:
        from azure.cli.core.commands.client_factory import get_subscription_id
        from msrestazure.tools import is_valid_resource_id, resource_id

        if not is_valid_resource_id(artifact_source):
            artifact_source = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.DeploymentManager', type='artifactSources',
                name=artifact_source)

    service_topology = ServiceTopologyResource(
        artifact_source_id=artifact_source,
        location=location,
        tags=tags)
    client = cf_service_topologies(cmd.cli_ctx)
    return client.create_or_update(
        resource_group_name=resource_group_name,
        service_topology_name=service_topology_name,
        service_topology_info=service_topology)


def cli_service_topology_update(
        cmd,
        instance,
        resource_group_name,
        artifact_source=None,
        tags=None):

    if artifact_source is not None:

        from azure.cli.core.commands.client_factory import get_subscription_id
        from msrestazure.tools import is_valid_resource_id, resource_id

        if not is_valid_resource_id(artifact_source):
            artifact_source = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.DeploymentManager', type='artifactSources',
                name=artifact_source)

        instance.artifact_source_id = artifact_source

    if tags is not None:
        instance.tags = tags

    return instance


def cli_service_create(
        cmd,
        resource_group_name,
        service_topology_name,
        service_name,
        target_location,
        target_subscription_id,
        location=None,
        tags=None):

    if location is None:
        location = get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    service = ServiceResource(
        target_location=target_location,
        target_subscription_id=target_subscription_id,
        location=location,
        tags=tags)
    client = cf_services(cmd.cli_ctx)
    return client.create_or_update(
        resource_group_name=resource_group_name,
        service_topology_name=service_topology_name,
        service_name=service_name,
        service_info=service)


def cli_service_update(
        cmd,
        instance,
        target_location=None,
        target_subscription_id=None,
        tags=None):

    if target_location is not None:
        instance.target_location = target_location

    if target_subscription_id is not None:
        instance.target_subscription_id = target_subscription_id

    if tags is not None:
        instance.tags = tags

    return instance


def cli_service_unit_create(
        cmd,
        resource_group_name,
        service_topology_name,
        service_name,
        service_unit_name,
        target_resource_group,
        deployment_mode,
        parameters_path,
        template_path,
        location=None,
        tags=None):
    parameters_uri = None
    template_uri = None
    parameters_artifact_source_relative_path = None
    template_artifact_source_relative_path = None

    if parameters_path is not None:
        if parameters_path.startswith('http'):
            parameters_uri = parameters_path
        else:
            parameters_artifact_source_relative_path = parameters_path

    if template_path is not None:
        if template_path.startswith('http'):
            template_uri = template_path
        else:
            template_artifact_source_relative_path = template_path

    if (all([template_artifact_source_relative_path, parameters_uri]) or all([parameters_artifact_source_relative_path, template_uri])):  # pylint: disable=line-too-long
        raise CLIError('usage error: specify both "--template-path" and "--parameters-path" either as relative URIs to artifact source or absolute SAS URIs.')  # pylint: disable=line-too-long

    if location is None:
        location = get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    service_unit_artifacts = ServiceUnitArtifacts(
        parameters_uri=parameters_uri,
        template_uri=template_uri,
        parameters_artifact_source_relative_path=parameters_artifact_source_relative_path,
        template_artifact_source_relative_path=template_artifact_source_relative_path)

    service_unit = ServiceUnitResource(
        target_resource_group=target_resource_group,
        deployment_mode=deployment_mode,
        artifacts=service_unit_artifacts,
        location=location,
        tags=tags)

    client = cf_service_units(cmd.cli_ctx)
    return client.create_or_update(
        resource_group_name=resource_group_name,
        service_topology_name=service_topology_name,
        service_name=service_name,
        service_unit_name=service_unit_name,
        service_unit_info=service_unit)


def cli_service_unit_update(
        cmd,
        instance,
        target_resource_group=None,
        deployment_mode=None,
        parameters_path=None,
        template_path=None,
        tags=None):

    if target_resource_group is not None:
        instance.target_resource_group = target_resource_group

    if deployment_mode is not None:
        instance.deployment_mode = deployment_mode

    if parameters_path is not None:
        if parameters_path.startswith('http'):
            instance.parameters_uri = parameters_path
        else:
            instance.parameters_artifact_source_relative_path = parameters_path

    if template_path is not None:
        if template_path.startswith('http'):
            instance.template_uri = template_path
        else:
            instance.template_artifact_source_relative_path = template_path

    if tags is not None:
        instance.tags = tags

    return instance


def cli_step_create(
        cmd,
        resource_group_name,
        step_name=None,
        step=None,
        duration=None,
        location=None,
        tags=None):

    if step is None and duration is None:
        raise CLIError('usage error: specify either step or duration. \
                        If step is specified, it can either be a wait step or health check step.')

    if step is not None and duration is not None:
        raise CLIError('usage error: specify only one of step or duration. \
            If step is specified, it can either be a wait step or health check step.')

    client = cf_steps(cmd.cli_ctx)
    if step is not None:
        step_resource = get_step_from_json(client, step)
        step_name = step_resource.name

    elif duration is not None:
        if step_name is None:
            raise CLIError('usage error: step name is not specified.')

        waitStepProperties = WaitStepProperties(attributes=WaitStepAttributes(duration=duration))

        if location is None:
            if resource_group_name is not None:
                location = get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

        step_resource = StepResource(
            properties=waitStepProperties,
            location=location,
            tags=tags)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        step_name=step_name,
        step_info=step_resource)


def cli_step_update(
        cmd,
        instance,
        step=None,
        duration=None,
        tags=None):

    if (step is None and duration is None):
        raise CLIError('usage error: specify either step or duration. \
            If step is specified, it can either be a wait step or health check step.')

    if (step is not None and duration is not None):
        raise CLIError('usage error: specify only one of step or duration. \
            If step is specified, it can either be a wait step or health check step.')

    if duration is not None:
        instance.properties.attributes.duration = duration

        # only update tags if updating duration property. If updating step from a file, read everything from file.
        if tags is not None:
            instance.tags = tags

    elif step is not None:
        client = cf_steps(cmd.cli_ctx)
        step_resource = get_step_from_json(client, step)
        instance = step_resource

    return instance


def cli_rollout_restart(
        cmd,
        resource_group_name,
        rollout_name,
        skip_succeeded=False):

    client = cf_rollouts(cmd.cli_ctx)
    return client.restart(
        resource_group_name=resource_group_name,
        rollout_name=rollout_name,
        skip_succeeded=bool(skip_succeeded))


def get_location_from_resource_group(cli_ctx, resource_group_name):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def get_step_from_json(client, health_check_step):
    return get_object_from_json(client, health_check_step, 'StepResource')


def get_or_read_json(json_or_file):
    json_obj = None
    if is_json(json_or_file):
        json_obj = shell_safe_json_parse(json_or_file)
    elif os.path.exists(json_or_file):
        json_obj = get_file_json(json_or_file)
    if json_obj is None:
        raise ValueError(
            """
            The variable passed should be in valid JSON format and be supplied by az deploymentmanager step CLI command.
            Make sure that you use output of relevant 'az deploymentmanager step show' command and the --out is 'json'
            """)
    return json_obj


def get_object_from_json(client, json_or_file, class_name):
    # Determine if input is json or file
    json_obj = get_or_read_json(json_or_file)

    # Deserialize json to object
    param = client._deserialize(class_name, json_obj)  # pylint: disable=protected-access
    if param is None:
        raise ValueError(
            """
            The variable passed should be in valid JSON format and be supplied by az deploymentmanager step CLI command.
            Make sure that you use output of relevant 'az deploymentmanager step show' commands and the --out is 'json'
            """)
    return param


def is_json(content):
    try:
        json.loads(content)
    except ValueError:
        return False
    return True
