# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

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
        step_name,
        duration,
        location=None,
        tags=None):

    waitStepProperties = WaitStepProperties(
        attributes=WaitStepAttributes(duration=duration))

    if location is None:
        location = get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    step = StepResource(
        properties=waitStepProperties,
        location=location,
        tags=tags)

    client = cf_steps(cmd.cli_ctx)
    return client.create_or_update(
        resource_group_name=resource_group_name,
        step_name=step_name,
        step_info=step)


def cli_step_update(
        cmd,
        instance,
        duration,
        tags=None):

    instance.properties.attributes.duration = duration

    if tags is not None:
        instance.tags = tags

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
    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    group = client.resource_groups.get(resource_group_name)
    return group.location
