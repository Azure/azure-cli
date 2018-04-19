# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from collections import OrderedDict

from azure.cli.core.util import empty_on_404
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.resource._client_factory import (
    cf_resource_groups, cf_providers, cf_features, cf_tags, cf_deployments,
    cf_deployment_operations, cf_policy_definitions, cf_policy_set_definitions, cf_resource_links,
    cf_resource_managedapplications, cf_resource_managedappdefinitions)
from azure.cli.command_modules.resource._validators import process_deployment_create_namespace


# Resource group commands
def transform_resource_group_list(result):
    return [OrderedDict([
        ('Name', r['name']), ('Location', r['location']), ('Status', r['properties']['provisioningState'])]) for r in result]


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


# Resource group deployment commands
def transform_deployments_list(result):
    sort_list = sorted(result, key=lambda deployment: deployment['properties']['timestamp'])
    return [OrderedDict([('Name', r['name']), ('Timestamp', r['properties']['timestamp']), ('State', r['properties']['provisioningState'])]) for r in sort_list]


# pylint: disable=too-many-statements
def load_command_table(self, _):
    from azure.cli.core.commands.arm import deployment_validate_table_format

    resource_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.resource.custom#{}')

    resource_group_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.{}',
        client_factory=cf_resource_groups,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    resource_provider_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.{}',
        client_factory=cf_providers,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    resource_feature_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.{}',
        client_factory=cf_features,
        resource_type=ResourceType.MGMT_RESOURCE_FEATURES
    )

    resource_tag_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.{}',
        client_factory=cf_tags,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    resource_deployment_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.{}',
        client_factory=cf_deployments,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    resource_deployment_operation_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.resources.operations.deployment_operations#DeploymentOperations.{}',
        client_factory=cf_deployment_operations,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    resource_policy_definitions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.{}',
        client_factory=cf_policy_definitions,
        resource_type=ResourceType.MGMT_RESOURCE_POLICY
    )

    resource_policy_set_definitions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.policy.operations#PolicySetDefinitionsOperations.{}',
        client_factory=cf_policy_set_definitions,
        resource_type=ResourceType.MGMT_RESOURCE_POLICY
    )

    resource_lock_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.locks.operations#ManagementLocksOperations.{}',
        resource_type=ResourceType.MGMT_RESOURCE_LOCKS
    )

    resource_link_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.links.operations#ResourceLinksOperations.{}',
        client_factory=cf_resource_links,
        resource_type=ResourceType.MGMT_RESOURCE_LINKS
    )
    resource_managedapp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.managedapplications.operations#ApplicationsOperations.{}',
        client_factory=cf_resource_managedapplications,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    resource_managedapp_def_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.resource.managedapplications.operations#ApplicationDefinitionsOperations.{}',
        client_factory=cf_resource_managedappdefinitions,
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )

    with self.command_group('account lock', resource_lock_sdk, resource_type=ResourceType.MGMT_RESOURCE_LOCKS) as g:
        g.custom_command('create', 'create_lock')
        g.custom_command('delete', 'delete_lock')
        g.custom_command('list', 'list_locks')
        g.custom_command('show', 'get_lock', exception_handler=empty_on_404)
        g.custom_command('update', 'update_lock')

    with self.command_group('group', resource_group_sdk, resource_type=ResourceType.MGMT_RESOURCE_RESOURCES) as g:
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('exists', 'check_existence')
        g.custom_command('list', 'list_resource_groups', table_transformer=transform_resource_group_list)
        g.custom_command('create', 'create_resource_group')
        g.custom_command('export', 'export_group_as_template')
        g.generic_update_command('update')
        g.generic_wait_command('wait')

    with self.command_group('group lock', resource_type=ResourceType.MGMT_RESOURCE_LOCKS) as g:
        g.custom_command('create', 'create_lock')
        g.custom_command('delete', 'delete_lock')
        g.custom_command('list', 'list_locks')
        g.custom_command('show', 'get_lock', exception_handler=empty_on_404)
        g.custom_command('update', 'update_lock')

    with self.command_group('resource', resource_custom, resource_type=ResourceType.MGMT_RESOURCE_RESOURCES) as g:
        g.custom_command('create', 'create_resource')
        g.custom_command('delete', 'delete_resource')
        g.custom_command('show', 'show_resource', exception_handler=empty_on_404)
        g.custom_command('list', 'list_resources', table_transformer=transform_resource_list)
        g.custom_command('tag', 'tag_resource')
        g.custom_command('move', 'move_resource')
        g.custom_command('invoke-action', 'invoke_resource_action')
        g.generic_update_command('update', getter_name='show_resource', setter_name='update_resource',
                                 client_factory=None)

    with self.command_group('resource lock', resource_type=ResourceType.MGMT_RESOURCE_LOCKS) as g:
        g.custom_command('create', 'create_lock')
        g.custom_command('delete', 'delete_lock')
        g.custom_command('list', 'list_locks')
        g.custom_command('show', 'get_lock', exception_handler=empty_on_404)
        g.custom_command('update', 'update_lock')

    # Resource provider commands
    with self.command_group('provider', resource_provider_sdk, resource_type=ResourceType.MGMT_RESOURCE_RESOURCES) as g:
        g.command('list', 'list')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.custom_command('register', 'register_provider')
        g.custom_command('unregister', 'unregister_provider')
        g.custom_command('operation list', 'list_provider_operations')
        g.custom_command('operation show', 'show_provider_operations')

    # Resource feature commands
    with self.command_group('feature', resource_feature_sdk, client_factory=cf_features, resource_type=ResourceType.MGMT_RESOURCE_FEATURES) as g:
        feature_table_transform = '{Name:name, RegistrationState:properties.state}'
        g.custom_command('list', 'list_features', table_transformer='[].' + feature_table_transform)
        g.command('show', 'get', exception_handler=empty_on_404, table_transformer=feature_table_transform)
        g.custom_command('register', 'register_feature')

    # Tag commands
    with self.command_group('tag', resource_tag_sdk) as g:
        g.command('list', 'list')
        g.command('create', 'create_or_update')
        g.command('delete', 'delete')
        g.command('add-value', 'create_or_update_value')
        g.command('remove-value', 'delete_value')

    with self.command_group('group deployment', resource_deployment_sdk) as g:
        g.custom_command('create', 'deploy_arm_template', supports_no_wait=True, validator=process_deployment_create_namespace)
        g.command('list', 'list_by_resource_group', table_transformer=transform_deployments_list, min_api='2017-05-10')
        g.command('list', 'list', table_transformer=transform_deployments_list, max_api='2016-09-01')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.custom_command('validate', 'validate_arm_template', table_transformer=deployment_validate_table_format)
        g.custom_command('export', 'export_deployment_as_template')
        g.generic_wait_command('wait')

    with self.command_group('group deployment operation', resource_deployment_operation_sdk) as g:
        g.command('list', 'list')
        g.custom_command('show', 'get_deployment_operations', client_factory=cf_deployment_operations, exception_handler=empty_on_404)

    with self.command_group('policy assignment', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as g:
        g.custom_command('create', 'create_policy_assignment')
        g.custom_command('delete', 'delete_policy_assignment')
        g.custom_command('list', 'list_policy_assignment')
        g.custom_command('show', 'show_policy_assignment', exception_handler=empty_on_404)

    with self.command_group('policy definition', resource_policy_definitions_sdk, resource_type=ResourceType.MGMT_RESOURCE_POLICY) as g:
        g.custom_command('create', 'create_policy_definition')
        g.command('delete', 'delete')
        g.command('list', 'list')
        g.custom_command('show', 'get_policy_definition', exception_handler=empty_on_404)
        g.generic_update_command('update', custom_func_name='update_policy_definition', custom_func_type=resource_custom)

    with self.command_group('policy set-definition', resource_policy_set_definitions_sdk, resource_type=ResourceType.MGMT_RESOURCE_POLICY, min_api='2017-06-01-preview') as g:
        g.custom_command('create', 'create_policy_setdefinition')
        g.command('delete', 'delete')
        g.command('list', 'list')
        g.custom_command('show', 'get_policy_setdefinition', exception_handler=empty_on_404)
        g.custom_command('update', 'update_policy_setdefinition')

    with self.command_group('lock', resource_type=ResourceType.MGMT_RESOURCE_LOCKS) as g:
        g.custom_command('create', 'create_lock')
        g.custom_command('delete', 'delete_lock')
        g.custom_command('list', 'list_locks')
        g.custom_command('show', 'get_lock', exception_handler=empty_on_404)
        g.custom_command('update', 'update_lock')

    with self.command_group('resource link', resource_link_sdk, resource_type=ResourceType.MGMT_RESOURCE_LINKS) as g:
        g.custom_command('create', 'create_resource_link')
        g.command('delete', 'delete')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.custom_command('list', 'list_resource_links')
        g.custom_command('update', 'update_resource_link')

    with self.command_group('managedapp', resource_managedapp_sdk, min_api='2017-05-10', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES) as g:
        g.custom_command('create', 'create_application')
        g.command('delete', 'delete')
        g.custom_command('show', 'show_application', exception_handler=empty_on_404)
        g.custom_command('list', 'list_applications')

    with self.command_group('managedapp definition', resource_managedapp_def_sdk, min_api='2017-05-10', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES) as g:
        g.custom_command('create', 'create_applicationdefinition')
        g.command('delete', 'delete')
        g.custom_command('show', 'show_applicationdefinition')
        g.command('list', 'list_by_resource_group', exception_handler=empty_on_404)
