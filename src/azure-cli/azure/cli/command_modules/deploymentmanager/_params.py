# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType


# pylint: disable=too-many-statements
def load_arguments(self, _):
    from azure.cli.core.commands.parameters import (
        resource_group_name_type,
        get_resource_name_completion_list,
        get_location_type,
        get_enum_type,
        tags_type)

    from azure.mgmt.deploymentmanager.models import (
        DeploymentMode)

    service_topology_name_type = CLIArgumentType(options_list='--service-topology-name', metavar='NAME', completer=get_resource_name_completion_list('Microsoft.DeploymentManager/servicetopologies'))
    service_name_type = CLIArgumentType(options_list='--service-name', metavar='NAME')
    artifact_source_type = CLIArgumentType(options_list='--artifact-source', metavar='NAME')

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
        c.argument('artifact_source', artifact_source_type, help='The name or resource identifier of the artifact source.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-topology create') as c:
        c.argument('artifact_source', artifact_source_type, help='The name or resource identifier of the artifact source.', required=False)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-topology update') as c:
        c.argument('artifact_source', artifact_source_type, help='The name or resource identifier of the artifact source.', required=False)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx), required=True)
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', options_list=['--service-name', '--name', '-n'], help='The name of the service')
        c.argument('target_location', options_list='--target-location', help='The location where the resources in the service should be deployed to.')
        c.argument('target_subscription_id', options_list='--target-subscription-id', help='The Id of subscription to which the resources in the service should be deployed to.')
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service create') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
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
    template_path_type = CLIArgumentType(options_list='--template-path', help='The path to the ARM template file. Either the full SAS Uri or the relative path in the artifact source for this topology.')
    parameters_path_type = CLIArgumentType(options_list='--parameters-path', help='The path to the ARM parameters file. Either the full SAS Uri or the relative path in the artifact source for this topology.')

    with self.argument_context('deploymentmanager service-unit') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment_mode', deployment_mode_type)
        c.argument('template_path', template_path_type)
        c.argument('parameters_path', parameters_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit create', arg_group='Named') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment_mode', deployment_mode_type)
        c.argument('template_uri', template_path_type)
        c.argument('parameters_uri', parameters_path_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager service-unit update') as c:
        c.argument('service_topology_name', service_topology_name_type, help='The name of the service topology')
        c.argument('service_name', service_name_type, help='The name of the service')
        c.argument('service_unit_name', options_list=['--service-unit-name', '--name', '-n'], help='The name of the service unit')
        c.argument('target_resource_group', target_resource_type)
        c.argument('deployment_mode', deployment_mode_type)
        c.argument('template_uri', template_path_type)
        c.argument('parameters_uri', parameters_path_type)
        c.argument('tags', tags_type)

    duration_type = CLIArgumentType(options_list='--duration', help='The duration of the wait step in ISO 8601 format.')
    step_name_type = CLIArgumentType(options_list=['--step-name', '--name', '-n'], help='The name of the step', completer=get_resource_name_completion_list('Microsoft.DeploymentManager/steps'))
    step_type = CLIArgumentType(options_list='--step', help='The step object, specify either the path to a json file or provide a json string that forms the step resource. The json is expected to be of the same format as the output of the relevant `az deploymentmanager step show` command')

    with self.argument_context('deploymentmanager step') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('step_name', step_name_type)
        c.argument('duration', duration_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager step create') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('step_name', step_name_type)
        c.argument('step', step_type)
        c.argument('duration', duration_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager step update') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('step_name', step_name_type)
        c.argument('step', step_type)
        c.argument('duration', duration_type)
        c.argument('tags', tags_type)

    with self.argument_context('deploymentmanager step show') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('step_name', step_name_type)

    with self.argument_context('deploymentmanager step delete') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('step_name', step_name_type)

    rollout_name_type = CLIArgumentType(options_list=['--rollout-name', '--name', '-n'], help='The name of the rollout', completer=get_resource_name_completion_list('Microsoft.DeploymentManager/rollouts'))

    with self.argument_context('deploymentmanager rollout show') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('rollout_name', rollout_name_type)

    with self.argument_context('deploymentmanager rollout delete') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('rollout_name', rollout_name_type)

    with self.argument_context('deploymentmanager rollout stop') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('rollout_name', rollout_name_type)

    with self.argument_context('deploymentmanager rollout restart') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('rollout_name', rollout_name_type)
        c.argument('skip_succeeded', options_list="--skip-succeeded", help="Skips all the steps that have succeeded in the previous retries of this rollout.")
