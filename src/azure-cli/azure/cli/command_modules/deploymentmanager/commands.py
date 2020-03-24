# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

# pylint: disable=line-too-long
from azure.cli.command_modules.deploymentmanager._client_factory import (cf_artifact_sources, cf_service_topologies, cf_services, cf_service_units, cf_steps, cf_rollouts)


def load_command_table(self, _):
    service_topologies = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#ServiceTopologiesOperations.{}',
        client_factory=cf_service_topologies)

    services = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#ServicesOperations.{}',
        client_factory=cf_services)

    service_units = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#ServiceUnitsOperations.{}',
        client_factory=cf_service_units)

    artifact_sources = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#ArtifactSourcesOperations.{}',
        client_factory=cf_artifact_sources)

    steps = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#StepsOperations.{}',
        client_factory=cf_steps)

    rollouts = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#RolloutsOperations.{}',
        client_factory=cf_rollouts)

    custom_tmpl = 'azure.cli.command_modules.deploymentmanager.custom#{}'
    deployment_manager_custom = CliCommandType(operations_tmpl=custom_tmpl)

    with self.command_group('deploymentmanager artifact-source', artifact_sources) as g:
        g.custom_command('create', 'cli_artifact_source_create')
        g.command('delete', 'delete', confirmation="There might be rollouts referencing the artifact source. Do you want to delete?")
        g.command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_arg_name='artifact_source_info',
            custom_func_name='cli_artifact_source_update',
            custom_func_type=deployment_manager_custom)

    with self.command_group('deploymentmanager service-topology', service_topologies) as g:
        g.custom_command('create', 'cli_service_topology_create')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_arg_name='service_topology_info',
            custom_func_name='cli_service_topology_update',
            custom_func_type=deployment_manager_custom)

    with self.command_group('deploymentmanager service', services) as g:
        g.custom_command('create', 'cli_service_create')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_arg_name='service_info',
            custom_func_name='cli_service_update',
            custom_func_type=deployment_manager_custom)

    with self.command_group('deploymentmanager service-unit', service_units) as g:
        g.custom_command('create', 'cli_service_unit_create')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_arg_name='service_unit_info',
            custom_func_name='cli_service_unit_update',
            custom_func_type=deployment_manager_custom)

    with self.command_group('deploymentmanager step', steps) as g:
        g.custom_command('create', 'cli_step_create')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_arg_name='step_info',
            custom_func_name='cli_step_update',
            custom_func_type=deployment_manager_custom)

    with self.command_group('deploymentmanager rollout', rollouts) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('stop', 'cancel', confirmation="Do you want to cancel the rollout?")
        g.custom_command(
            'restart',
            'cli_rollout_restart',
            confirmation="Are you sure you want to restart the rollout? If you want to skip all the steps that succeeded on the previous run, use '--skip-succeeded' option.")
        g.command('delete', 'delete')

    with self.command_group('deploymentmanager', is_preview=True):
        pass
