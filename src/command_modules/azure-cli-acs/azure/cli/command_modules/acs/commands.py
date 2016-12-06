# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from collections import OrderedDict

from azure.cli.core.commands import cli_command

#Remove the hack after https://github.com/Azure/azure-rest-api-specs/issues/352 fixed
from azure.mgmt.compute.models import ContainerService#pylint: disable=wrong-import-position
for a in ['id', 'name', 'type', 'location']:
    ContainerService._attribute_map[a]['type'] = 'str'#pylint: disable=protected-access
ContainerService._attribute_map['tags']['type'] = '{str}'#pylint: disable=protected-access
######

def cf_acs_create(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.acs.mgmt_acs.lib import AcsCreationClient as AcsCreateClient
    return get_mgmt_service_client(AcsCreateClient).acs

def cf_acs(_):
    from azure.mgmt.compute import ComputeManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ComputeManagementClient).container_services

# standard commands

# ACS

def transform_acs_list(result):
    transformed = []
    for r in result:
        orchestratorType = 'Unknown'
        orchestratorProfile = r.get('orchestratorProfile')
        if orchestratorProfile:
            orchestratorType = orchestratorProfile.get('orchestratorType')
        res = OrderedDict([('Name', r['name']), ('ResourceGroup', r['resourceGroup']), \
            ('Orchestrator', orchestratorType), ('Location', r['location']), \
            ('ProvisioningState', r['provisioningState'])])
        transformed.append(res)
    return transformed

cli_command(__name__, 'acs show', 'azure.mgmt.compute.operations.container_services_operations#ContainerServicesOperations.get', cf_acs)
cli_command(__name__, 'acs list', 'azure.cli.command_modules.acs.custom#list_container_services', cf_acs)
cli_command(__name__, 'acs delete', 'azure.mgmt.compute.operations.container_services_operations#ContainerServicesOperations.delete', cf_acs)
cli_command(__name__, 'acs scale', 'azure.cli.command_modules.acs.custom#update_acs')
#Per conversation with ACS team, hide the update till we have something meaningful to tweak
# from azure.cli.command_modules.vm.custom import update_acs
# cli_generic_update_command(__name__, 'acs update', ContainerServicesOperations.get, ContainerServicesOperations.create_or_update, cf_acs)


# custom commands

cli_command(__name__, 'acs browse', 'azure.cli.command_modules.acs.custom#acs_browse')
cli_command(__name__, 'acs install-cli', 'azure.cli.command_modules.acs.custom#acs_install_cli')
cli_command(__name__, 'acs dcos browse', 'azure.cli.command_modules.acs.custom#dcos_browse')
cli_command(__name__, 'acs dcos install-cli', 'azure.cli.command_modules.acs.custom#dcos_install_cli')
cli_command(__name__, 'acs create', 'azure.cli.command_modules.acs.custom#acs_create')
cli_command(__name__, 'acs kubernetes browse', 'azure.cli.command_modules.acs.custom#k8s_browse')
cli_command(__name__, 'acs kubernetes install-cli', 'azure.cli.command_modules.acs.custom#k8s_install_cli')
cli_command(__name__, 'acs kubernetes get-credentials', 'azure.cli.command_modules.acs.custom#k8s_get_credentials')

