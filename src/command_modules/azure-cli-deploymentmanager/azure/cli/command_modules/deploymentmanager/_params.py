# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType


def load_arguments(self, _):
    # from azure.mgmt.deploymentmanager.models import RebootType, RedisKeyType, SkuName, TlsVersion, ReplicationRole
    # from azure.cli.command_modules.deploymentmanager._validators import JsonString, ScheduleEntryList
    # from azure.cli.command_modules.deploymentmanager.custom import allowed_c_family_sizes, allowed_p_family_sizes

    from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_resource_name_completion_list,
    get_three_state_flag,
    get_location_type,
    get_enum_type,
    tags_type,
    name_type
    )

    from azure.mgmt.deploymentmanager.models import (
        DeploymentMode)

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    service_topology_name_type = CLIArgumentType(options_list='--service-topology-name', metavar='NAME')
    service_name_type = CLIArgumentType(options_list='--service-name', metavar='NAME')
    service_unit_name_type = CLIArgumentType(options_list='--service-unit-name', metavar='NAME')
    service_topology_id_type = CLIArgumentType(options_list='--service-topology-id', metavar='NAME')
    service_id_type = CLIArgumentType(options_list='--service-id', metavar='NAME')
    artifact_source_id_type = CLIArgumentType(options_list='--artifact-source-id', metavar='NAME')

    with self.argument_context('deploymentmanager artifact-source') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('artifact_source_name', options_list=['--artifact-source-name', '--name', '-n'], help='The name of the artifact source')
        c.argument('sas_uri', options_list=['--sas-uri'], help='The SAS Uri to the Azure Storage container where the artifacts are stored.')
        c.argument('artifact_root', options_list=['--artifact-root'], help='The root folder under which the artifacts are to be found. This is the path relative to the Azure storage container provided in --sas-uri.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager artifact-source create') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx), required=True)
        c.argument('artifact_source_name', options_list=['--artifact-source-name', '--name', '-n'], help='The name of the artifact source')
        c.argument('sas_uri', options_list=['--sas-uri'], help='The SAS Uri to the Azure Storage container where the artifacts are stored.')
        c.argument('artifact_root', options_list=['--artifact-root'], help='The root folder under which the artifacts are to be found. This is the path relative to the Azure storage container provided in --sas-uri.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager artifact-source update') as c:
        c.argument('sas_uri', options_list=['--sas-uri'], help='The SAS Uri to the Azure Storage container where the artifacts are stored.')
        c.argument('artifact_root', options_list=['--artifact-root'], help='The root folder under which the artifacts are to be found. This is the path relative to the Azure storage container provided in --sas-uri.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-topology') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx), required=True)
        c.argument('service_topology_name', options_list=['--service-topology-name', '--name', '-n'], help='The name of the service topology')
        c.argument('artifact_source_id', artifact_source_id_type, help='The resource identifier of the artifact source.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-topology create') as c:
        c.argument('artifact_source_id', artifact_source_id_type, help='The resource identifier of the artifact source.', required=False)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-topology update') as c:
        c.argument('artifact_source_id', artifact_source_id_type, help='The resource identifier of the artifact source.', required=False)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx), required=True)
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_topology_id', service_topology_id_type, help='The identifier of the service topology')
        c.argument('service_name', options_list=['--service-name', '--name', '-n'], help='The name of the service')
        c.argument('target_location', options_list='--target-location', help='The location where the resources in the service should be deployed to.')
        c.argument('target_subscription_id', options_list='--target-subscription-id', help='The subscription to which the resources in the service should be deployed to.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service create') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_topology_id', service_topology_id_type, help='The identifier of the service topology')
        c.argument('service_name', options_list=['--service-name', '--name', '-n'], help='The name of the service')
        c.argument('target_location', options_list='--target-location', help='The location where the resources in the service should be deployed to.')
        c.argument('target_subscription_id', options_list='--target-subscription-id', help='The subscription to which the resources in the service should be deployed to.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service update') as c:
        c.argument('target_location', options_list='--target-location', help='The location where the resources in the service should be deployed to.')
        c.argument('target_subscription_id', options_list='--target-subscription-id', help='The subscription to which the resources in the service should be deployed to.')
        c.argument('tags', tags_type)

    target_resource_type = CLIArgumentType(options_list='--target-resource-group', help='The resource group where the resources in the service unit should be deployed to')
    deployment_mode_type = CLIArgumentType(options_list='--deployment-mode', arg_type=get_enum_type(DeploymentMode), default=DeploymentMode.incremental, help='The type of depoyment mode to be used when deploying the service unit. Possible values: Incremental, Complete')
    template_uri_type = CLIArgumentType(options_list='--template-uri', help='The SAS Uri of the Resource Manager template')
    parameters_uri_type = CLIArgumentType(options_list='--parameters-uri', help='The SAS Uri of the Resource Manager parameters file')
    parameters_artifact_source_relative_path_type = CLIArgumentType(options_list='--template-artifact-source-relative-path', help='The relative path of the ARM parameters file from the artifact source for this topology')
    template_artifact_source_relative_path_type = CLIArgumentType(options_list='--parameters-artifact-source-relative-path', help='The relative path of the ARM template file from the artifact source for this topology')

    with self.argument_context('deploymentmanager service-unit') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_topology_id', service_topology_id_type, help='The identifier of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_id', service_topology_id_type, help='The identifier of the service')
        c.argument('service_unit_name', service_unit_name_type, help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment-mode', deployment_mode_type)
        c.argument('template_uri', template_uri_type)
        c.argument('parameters_uri', parameters_uri_type)
        c.argument('parameters_artifact_source_relative_path', parameters_artifact_source_relative_path_type)
        c.argument('template_artifact_source_relative_path', template_artifact_source_relative_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit create', arg_group='Named') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment-mode', deployment_mode_type)
        c.argument('template_uri', template_uri_type)
        c.argument('parameters_uri', parameters_uri_type)
        c.argument('parameters_artifact_source_relative_path', parameters_artifact_source_relative_path_type)
        c.argument('template_artifact_source_relative_path', template_artifact_source_relative_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit create', arg_group='ServiceTopologyId') as c:
        c.argument('service_topology_id', service_topology_id_type, help='The identifier of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment-mode', deployment_mode_type)
        c.argument('template_uri', template_uri_type)
        c.argument('parameters_uri', parameters_uri_type)
        c.argument('parameters_artifact_source_relative_path', parameters_artifact_source_relative_path_type)
        c.argument('template_artifact_source_relative_path', template_artifact_source_relative_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit create', arg_group='ServiceId') as c:
        c.argument('service_id', service_id_type, help='The identifier of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment-mode', deployment_mode_type)
        c.argument('template_uri', template_uri_type)
        c.argument('parameters_uri', parameters_uri_type)
        c.argument('parameters_artifact_source_relative_path', parameters_artifact_source_relative_path_type)
        c.argument('template_artifact_source_relative_path', template_artifact_source_relative_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit update') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment-mode', deployment_mode_type)
        c.argument('template_uri', template_uri_type)
        c.argument('parameters_uri', parameters_uri_type)
        c.argument('parameters_artifact_source_relative_path', parameters_artifact_source_relative_path_type)
        c.argument('template_artifact_source_relative_path', template_artifact_source_relative_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit show') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager step') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx), required=True)
        c.argument('step_name', options=['--step-name', '--name', '-n'], help='The name of the step')
        c.argument('duration', options='--duration', help='The duration for the wait step.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager step create') as c:
        c.argument('duration', options='--duration', help='The duration for the wait step.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager step update') as c:
        c.argument('duration', options='--duration', help='The duration for the wait step.')
        c.argument('tags', tags_type)