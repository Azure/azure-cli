# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import OrderedDict

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command, cli_generic_wait_command
from azure.cli.core.util import empty_on_404

from azure.cli.command_modules.resource._client_factory import (_resource_client_factory,
                                                                cf_resource_groups,
                                                                cf_providers,
                                                                cf_features,
                                                                cf_tags,
                                                                cf_deployments,
                                                                cf_deployment_operations,
                                                                cf_policy_definitions,
                                                                cf_resource_links,
                                                                cf_resource_managedapplications,
                                                                cf_resource_managedappdefinitions)


# Resource group commands
def transform_resource_group_list(result):
    return [OrderedDict([('Name', r['name']), ('Location', r['location']), ('Status', r['properties']['provisioningState'])]) for r in result]


cli_command(__name__, 'group delete', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.delete', cf_resource_groups, no_wait_param='raw', confirmation=True)
cli_generic_wait_command(__name__, 'group wait', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get', cf_resource_groups)
cli_command(__name__, 'group show', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get', cf_resource_groups, exception_handler=empty_on_404)
cli_command(__name__, 'group exists', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.check_existence', cf_resource_groups)
cli_command(__name__, 'group list', 'azure.cli.command_modules.resource.custom#list_resource_groups', table_transformer=transform_resource_group_list)
cli_command(__name__, 'group create', 'azure.cli.command_modules.resource.custom#create_resource_group')
cli_command(__name__, 'group export', 'azure.cli.command_modules.resource.custom#export_group_as_template')


# Resource commands

def transform_resource_list(result):
    transformed = []
    for r in result:
        res = OrderedDict([('Name', r['name']), ('ResourceGroup', r['resourceGroup']), ('Location', r['location']), ('Type', r['type'])])
        try:
            res['Status'] = r['properties']['provisioningStatus']
        except TypeError:
            res['Status'] = ' '
        transformed.append(res)
    return transformed


cli_command(__name__, 'resource create', 'azure.cli.command_modules.resource.custom#create_resource')
cli_command(__name__, 'resource delete', 'azure.cli.command_modules.resource.custom#delete_resource')
cli_command(__name__, 'resource show', 'azure.cli.command_modules.resource.custom#show_resource', exception_handler=empty_on_404)
cli_command(__name__, 'resource list', 'azure.cli.command_modules.resource.custom#list_resources', table_transformer=transform_resource_list)
cli_command(__name__, 'resource tag', 'azure.cli.command_modules.resource.custom#tag_resource')
cli_command(__name__, 'resource move', 'azure.cli.command_modules.resource.custom#move_resource')

# Resource provider commands
cli_command(__name__, 'provider list', 'azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.list', cf_providers)
cli_command(__name__, 'provider show', 'azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.get', cf_providers, exception_handler=empty_on_404)
cli_command(__name__, 'provider register', 'azure.cli.command_modules.resource.custom#register_provider')
cli_command(__name__, 'provider unregister', 'azure.cli.command_modules.resource.custom#unregister_provider')
cli_command(__name__, 'provider operation list', 'azure.cli.command_modules.resource.custom#list_provider_operations')
cli_command(__name__, 'provider operation show', 'azure.cli.command_modules.resource.custom#show_provider_operations')
# Resource feature commands
cli_command(__name__, 'feature list', 'azure.cli.command_modules.resource.custom#list_features', cf_features)
cli_command(__name__, 'feature show', 'azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.get', cf_features, exception_handler=empty_on_404)
cli_command(__name__, 'feature register', 'azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.register', cf_features)

# Tag commands
cli_command(__name__, 'tag list', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.list', cf_tags)
cli_command(__name__, 'tag create', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.create_or_update', cf_tags)
cli_command(__name__, 'tag delete', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.delete', cf_tags)
cli_command(__name__, 'tag add-value', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.create_or_update_value', cf_tags)
cli_command(__name__, 'tag remove-value', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.delete_value', cf_tags)


# Resource group deployment commands
def transform_deployments_list(result):
    sort_list = sorted(result, key=lambda deployment: deployment['properties']['timestamp'])
    return [OrderedDict([('Name', r['name']), ('Timestamp', r['properties']['timestamp']), ('State', r['properties']['provisioningState'])]) for r in sort_list]


cli_command(__name__, 'group deployment create', 'azure.cli.command_modules.resource.custom#deploy_arm_template', no_wait_param='no_wait')
cli_generic_wait_command(__name__, 'group deployment wait', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.get', cf_deployments)
cli_command(__name__, 'group deployment list', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.list_by_resource_group', cf_deployments, table_transformer=transform_deployments_list)
cli_command(__name__, 'group deployment show', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.get', cf_deployments, exception_handler=empty_on_404)
cli_command(__name__, 'group deployment delete', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.delete', cf_deployments)
cli_command(__name__, 'group deployment validate', 'azure.cli.command_modules.resource.custom#validate_arm_template')
cli_command(__name__, 'group deployment export', 'azure.cli.command_modules.resource.custom#export_deployment_as_template')

# Resource group deployment operations commands
cli_command(__name__, 'group deployment operation list', 'azure.mgmt.resource.resources.operations.deployment_operations#DeploymentOperations.list', cf_deployment_operations)
cli_command(__name__, 'group deployment operation show', 'azure.cli.command_modules.resource.custom#get_deployment_operations', cf_deployment_operations, exception_handler=empty_on_404)

cli_generic_update_command(__name__, 'resource update',
                           'azure.cli.command_modules.resource.custom#show_resource',
                           'azure.cli.command_modules.resource.custom#update_resource')

cli_generic_update_command(__name__, 'group update',
                           'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get',
                           'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.create_or_update',
                           lambda: _resource_client_factory().resource_groups)

cli_command(__name__, 'policy assignment create', 'azure.cli.command_modules.resource.custom#create_policy_assignment')
cli_command(__name__, 'policy assignment delete', 'azure.cli.command_modules.resource.custom#delete_policy_assignment')
cli_command(__name__, 'policy assignment list', 'azure.cli.command_modules.resource.custom#list_policy_assignment')
cli_command(__name__, 'policy assignment show', 'azure.cli.command_modules.resource.custom#show_policy_assignment', exception_handler=empty_on_404)

cli_command(__name__, 'policy definition create', 'azure.cli.command_modules.resource.custom#create_policy_definition')
cli_command(__name__, 'policy definition delete', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.delete', cf_policy_definitions)
cli_command(__name__, 'policy definition list', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.list', cf_policy_definitions)
cli_command(__name__, 'policy definition show', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.get', cf_policy_definitions, exception_handler=empty_on_404)
cli_command(__name__, 'policy definition update', 'azure.cli.command_modules.resource.custom#update_policy_definition')

cli_command(__name__, 'lock create', 'azure.cli.command_modules.resource.custom#create_lock')
cli_command(__name__, 'lock delete', 'azure.cli.command_modules.resource.custom#delete_lock')
cli_command(__name__, 'lock list', 'azure.cli.command_modules.resource.custom#list_locks')
cli_command(__name__, 'lock show', 'azure.cli.command_modules.resource.custom#get_lock', exception_handler=empty_on_404)
cli_command(__name__, 'lock update', 'azure.cli.command_modules.resource.custom#update_lock')

cli_command(__name__, 'resource link create', 'azure.cli.command_modules.resource.custom#create_resource_link')
cli_command(__name__, 'resource link delete', 'azure.mgmt.resource.links.operations#ResourceLinksOperations.delete', cf_resource_links)
cli_command(__name__, 'resource link show', 'azure.mgmt.resource.links.operations#ResourceLinksOperations.get', cf_resource_links, exception_handler=empty_on_404)
cli_command(__name__, 'resource link list', 'azure.cli.command_modules.resource.custom#list_resource_links')
cli_command(__name__, 'resource link update', 'azure.cli.command_modules.resource.custom#update_resource_link')

cli_command(__name__, 'managedapp create', 'azure.cli.command_modules.resource.custom#create_appliance')
cli_command(__name__, 'managedapp delete', 'azure.mgmt.resource.managedapplications.operations#AppliancesOperations.delete', cf_resource_managedapplications)
cli_command(__name__, 'managedapp show', 'azure.cli.command_modules.resource.custom#show_appliance', exception_handler=empty_on_404)
cli_command(__name__, 'managedapp list', 'azure.cli.command_modules.resource.custom#list_appliances')

cli_command(__name__, 'managedapp definition create', 'azure.cli.command_modules.resource.custom#create_appliancedefinition')
cli_command(__name__, 'managedapp definition delete', 'azure.mgmt.resource.managedapplications.operations#ApplianceDefinitionsOperations.delete', cf_resource_managedappdefinitions)
cli_command(__name__, 'managedapp definition show', 'azure.cli.command_modules.resource.custom#show_appliancedefinition')
cli_command(__name__, 'managedapp definition list', 'azure.mgmt.resource.managedapplications.operations#ApplianceDefinitionsOperations.list_by_resource_group', cf_resource_managedappdefinitions, exception_handler=empty_on_404)
