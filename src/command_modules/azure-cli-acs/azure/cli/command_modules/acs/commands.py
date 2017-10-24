# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import OrderedDict

from azure.cli.core.commands import cli_command
from azure.cli.core.util import empty_on_404
from azure.cli.core.commands.arm import \
    (cli_generic_wait_command, deployment_validate_table_format)
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from ._client_factory import _acs_client_factory
from ._client_factory import _aks_client_factory


def aks_list_table_format(results):
    """"Format a list of managed clusters as summary results for display with "-o table"."""
    return [aks_show_table_format(r) for r in results]


def aks_show_table_format(result):
    """Format a managed cluster as summary results for display with "-o table"."""
    # move some nested properties up to top-level values
    properties = result.get('properties', {})
    promoted = ['kubernetesVersion', 'provisioningState', 'fqdn']
    result.update({k: properties.get(k) for k in promoted})

    columns = ['name', 'location', 'resourceGroup'] + promoted
    # put results in an ordered dict so the headers are predictable
    return OrderedDict({k: result.get(k) for k in columns})


def aks_get_versions_table_format(result):
    """Format get-versions upgrade results as a summary for display with "-o table"."""
    properties = result.get('properties', {})
    master = properties.get('controlPlaneProfile', {})
    result['masterVersion'] = master.get('kubernetesVersion', 'unknown')
    master_upgrades = master.get('upgrades', [])
    result['masterUpgrades'] = ', '.join(master_upgrades) if master_upgrades else 'None available'

    agents = properties.get('agentPoolProfiles', [])
    versions, upgrades = [], []
    for agent in agents:
        version = agent.get('kubernetesVersion', 'unknown')
        agent_upgrades = agent.get('upgrades', [])
        upgrade = ', '.join(agent_upgrades) if agent_upgrades else 'None available'
        name = agent.get('name')
        if name:  # multiple agent pools, presumably
            version = "{}: {}".format(name, version)
            upgrade = "{}: {}".format(name, upgrades)
        versions.append(version)
        upgrades.append(upgrade)

    result['agentPoolVersion'] = ', '.join(versions)
    result['agentPoolUpgrades'] = ', '.join(upgrades)

    columns = ['name', 'resourceGroup', 'masterVersion', 'masterUpgrades', 'agentPoolVersion', 'agentPoolUpgrades']
    # put results in an ordered dict so the headers are predictable
    return OrderedDict({k: result.get(k) for k in columns})


if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    cli_command(__name__, 'acs show', 'azure.mgmt.containerservice.operations.container_services_operations#ContainerServicesOperations.get', _acs_client_factory, exception_handler=empty_on_404)
    cli_command(__name__, 'acs delete', 'azure.mgmt.containerservice.operations.container_services_operations#ContainerServicesOperations.delete', _acs_client_factory)

    # Per conversation with ACS team, hide the update till we have something meaningful to tweak
    # from azure.cli.command_modules.acs.custom import update_acs
    # cli_generic_update_command(__name__, 'acs update', ContainerServicesOperations.get, ContainerServicesOperations.create_or_update, cf_acs)

    # custom commands
    cli_command(__name__, 'acs list-locations', 'azure.cli.command_modules.acs.custom#list_acs_locations')
    cli_command(__name__, 'acs scale', 'azure.cli.command_modules.acs.custom#update_acs', _acs_client_factory)
    cli_command(__name__, 'acs list', 'azure.cli.command_modules.acs.custom#list_container_services', _acs_client_factory)
    cli_command(__name__, 'acs browse', 'azure.cli.command_modules.acs.custom#acs_browse')
    cli_command(__name__, 'acs install-cli', 'azure.cli.command_modules.acs.custom#acs_install_cli')
    cli_command(__name__, 'acs dcos browse', 'azure.cli.command_modules.acs.custom#dcos_browse')
    cli_command(__name__, 'acs dcos install-cli', 'azure.cli.command_modules.acs.custom#dcos_install_cli')
    cli_command(__name__, 'acs create', 'azure.cli.command_modules.acs.custom#acs_create', no_wait_param='no_wait', table_transformer=deployment_validate_table_format)
    cli_generic_wait_command(__name__, 'acs wait', 'azure.mgmt.containerservice.operations.container_services_operations#ContainerServicesOperations.get', _acs_client_factory)
    cli_command(__name__, 'acs kubernetes browse', 'azure.cli.command_modules.acs.custom#k8s_browse')
    cli_command(__name__, 'acs kubernetes install-cli', 'azure.cli.command_modules.acs.custom#k8s_install_cli')
    cli_command(__name__, 'acs kubernetes get-credentials', 'azure.cli.command_modules.acs.custom#k8s_get_credentials')


if not supported_api_version(PROFILE_TYPE, max_api='2017-08-31-profile'):
    cli_command(__name__, 'aks browse',
                'azure.cli.command_modules.acs.custom#aks_browse', _aks_client_factory)
    cli_command(__name__, 'aks create',
                'azure.cli.command_modules.acs.custom#aks_create', _aks_client_factory, no_wait_param='no_wait')
    cli_command(__name__, 'aks delete',
                'azure.cli.command_modules.acs.custom#aks_delete', _aks_client_factory, no_wait_param='no_wait',
                confirmation='Are you sure you want to perform this operation?')
    cli_command(__name__, 'aks get-credentials',
                'azure.cli.command_modules.acs.custom#aks_get_credentials', _aks_client_factory)
    cli_command(__name__, 'aks get-versions',
                'azure.cli.command_modules.acs.custom#aks_get_versions', _aks_client_factory,
                table_transformer=aks_get_versions_table_format)
    cli_command(__name__, 'aks install-cli',
                'azure.cli.command_modules.acs.custom#k8s_install_cli')
    cli_command(__name__, 'aks list',
                'azure.cli.command_modules.acs.custom#aks_list', _aks_client_factory,
                table_transformer=aks_list_table_format)
    cli_command(__name__, 'aks scale',
                'azure.cli.command_modules.acs.custom#aks_scale', _aks_client_factory, no_wait_param='no_wait')
    cli_command(__name__, 'aks show',
                'azure.cli.command_modules.acs.custom#aks_show', _aks_client_factory,
                table_transformer=aks_show_table_format)
    cli_command(__name__, 'aks upgrade',
                'azure.cli.command_modules.acs.custom#aks_upgrade', _aks_client_factory, no_wait_param='no_wait',
                confirmation='Kubernetes may be unavailable during cluster upgrades.\n' +
                'Are you sure you want to perform this operation?')
    cli_generic_wait_command(__name__, 'aks wait',
                             'azure.mgmt.containerservice.operations.managed_clusters_operations' +
                             '#ManagedClustersOperations.get',
                             _aks_client_factory)
