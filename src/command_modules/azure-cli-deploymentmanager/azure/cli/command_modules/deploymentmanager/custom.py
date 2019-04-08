# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id

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
    location, 
    artifact_source_name, 
    sas_uri, 
    artifact_root=None, 
    tags=None):
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
    location, 
    service_topology_name, 
    artifact_source_id=None, 
    tags=None):

    service_topology = ServiceTopologyResource(
        artifact_source_id=artifact_source_id,
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
    artifact_source_id=None, 
    tags=None):

    if artifact_source_id is not None:
        instance.artifact_source_id = artifact_source_id

    if tags is not None:
        instance.tags = tags

    return instance

def cli_service_create(
    cmd, 
    resource_group_name, 
    location, 
    service_topology_name, 
    service_name,
    target_location,
    target_subscription_id,
    tags=None):

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
    location, 
    service_topology_name, 
    service_name, 
    service_unit_name,
    target_resource_group,
    deployment_mode,
    parameters_artifact_source_relative_path=None,
    template_artifact_source_relative_path=None,
    parameters_uri=None,
    template_uri=None,
    tags=None):

    if all([template_artifact_source_relative_path, template_uri]):
        raise CLIError('usage error: specify either "--template-uri" or "--template-artifact-source-relative-path"')

    if all([parameters_artifact_source_relative_path, parameters_uri]):
        raise CLIError('usage error: specify either "--parameters-uri" or "--parameters-artifact-source-relative-path"')

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
    parameters_artifact_source_relative_path=None,
    template_artifact_source_relative_path=None,
    parameters_uri=None,
    template_uri=None,
    tags=None):

    if target_resource_group is not None:
        instance.target_resource_group = target_resource_group

    if deployment_mode is not None:
        instance.deployment_mode = deployment_mode

    if parameters_artifact_source_relative_path is not None:
        instance.parameters_artifact_source_relative_path = parameters_artifact_source_relative_path

    if template_artifact_source_relative_path  is not None:
        instance.template_artifact_source_relative_path = template_artifact_source_relative_path

    if parameters_uri is not None:
        instance.parameters_uri = parameters_uri

    if template_uri is not None:
        instance.template_uri = template_uri

    if tags is not None:
        instance.tags = tags

    return instance

def cli_step_create(
    cmd, 
    resource_group_name, 
    location, 
    step_name, 
    duration, 
    tags=None):

    waitStepProperties = WaitStepProperties(
        attributes = WaitStepAttributes(duration=duration))

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
    skip_succeeded):

    client = cf_rollouts(cmd.cli_ctx)
    return client.restart(
        resource_group_name=resource_group_name,
        rollout_name=rollout_name,
        skip_succeeded=skip_succeeded)