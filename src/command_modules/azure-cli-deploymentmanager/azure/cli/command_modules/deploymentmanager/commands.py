# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

# pylint: disable=line-too-long
from ._client_factory import (cf_artifact_sources, cf_service_topologies, cf_services, cf_service_units, cf_steps, cf_rollouts)

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

    artifact_sources  = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#ArtifactSourcesOperations.{}',
        client_factory=cf_artifact_sources)

    steps = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#StepsOperations.{}',
        client_factory=cf_steps)

    rollouts = CliCommandType(
        operations_tmpl='azure.mgmt.deploymentmanager.operations#RolloutsOperations.{}',
        client_factory=cf_rollouts)

    with self.command_group('deploymentmanager artifactsource', artifact_sources) as g:
        g.custom_command('create', 'cli_artifact_source_create')
        g.command('delete', 'delete', confirmation=True)
        g.command('show', 'get')
        g.generic_update_command('update', setter_name='update', custom_func_name='cli_redis_update')

    with self.command_group('deploymentmanager servicetopology', service_topologies) as g:
        g.command('create', 'create_or_update')
        g.command('update', 'create_or_update')
        g.command('delete', 'delete')
        g.command('show', 'get')

    with self.command_group('deploymentmanager service', services) as g:
        g.command('create', 'create_or_update')
        g.command('update', 'create_or_update')
        g.command('delete', 'delete')
        g.command('show', 'get')

    with self.command_group('deploymentmanager serviceunit', service_units) as g:
        g.command('create', 'create_or_update')
        g.command('update', 'create_or_update')
        g.command('delete', 'delete')
        g.command('show', 'get')

    with self.command_group('deploymentmanager step', steps) as g:
        g.command('create', 'create_or_update')
        g.command('update', 'create_or_update')
        g.command('delete', 'delete')
        g.command('show', 'get')

    with self.command_group('deploymentmanager rollout', rollouts) as g:
        g.command('show', 'get')
        g.command('stop', 'stop')
        g.command('restart', 'restart')
        g.command('delete', 'delete')