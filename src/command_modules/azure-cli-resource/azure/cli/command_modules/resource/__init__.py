# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.cli.core import AzCommandsLoader
from azure.cli.core.util import empty_on_404

from azure.cli.command_modules.resource._client_factory import \
    (_resource_client_factory, cf_resource_groups, cf_providers, cf_features, cf_tags, cf_deployments,
     cf_deployment_operations, cf_policy_definitions, cf_resource_links, cf_resource_managedapplications,
     cf_resource_managedappdefinitions)
import azure.cli.command_modules.resource._help  # pylint: disable=unused-import

class ResourceCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        super(ResourceCommandsLoader, self).load_command_table(args)

        from azure.cli.core.commands.arm import \
            (handle_long_running_operation_exception, deployment_validate_table_format)

        # Resource group commands
        def transform_resource_group_list(result):
            return [OrderedDict([('Name', r['name']), ('Location', r['location']), ('Status', r['properties']['provisioningState'])]) for r in result]


        self.cli_command(__name__, 'group delete', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.delete', client_factory=cf_resource_groups, no_wait_param='raw', confirmation=True)
        self.cli_generic_wait_command(__name__, 'group wait', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get', cf_resource_groups)
        self.cli_command(__name__, 'group show', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get', client_factory=cf_resource_groups, exception_handler=empty_on_404)
        self.cli_command(__name__, 'group exists', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.check_existence', client_factory=cf_resource_groups)
        self.cli_command(__name__, 'group list', 'azure.cli.command_modules.resource.custom#list_resource_groups', table_transformer=transform_resource_group_list)
        self.cli_command(__name__, 'group create', 'azure.cli.command_modules.resource.custom#create_resource_group')
        self.cli_command(__name__, 'group export', 'azure.cli.command_modules.resource.custom#export_group_as_template')

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

        self.cli_command(__name__, 'resource create', 'azure.cli.command_modules.resource.custom#create_resource')
        self.cli_command(__name__, 'resource delete', 'azure.cli.command_modules.resource.custom#delete_resource')
        self.cli_command(__name__, 'resource show', 'azure.cli.command_modules.resource.custom#show_resource', exception_handler=empty_on_404)
        self.cli_command(__name__, 'resource list', 'azure.cli.command_modules.resource.custom#list_resources', table_transformer=transform_resource_list)
        self.cli_command(__name__, 'resource tag', 'azure.cli.command_modules.resource.custom#tag_resource')
        self.cli_command(__name__, 'resource move', 'azure.cli.command_modules.resource.custom#move_resource')

        # Resource provider commands
        self.cli_command(__name__, 'provider list', 'azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.list', client_factory=cf_providers)
        self.cli_command(__name__, 'provider show', 'azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.get', client_factory=cf_providers, exception_handler=empty_on_404)
        self.cli_command(__name__, 'provider register', 'azure.cli.command_modules.resource.custom#register_provider')
        self.cli_command(__name__, 'provider unregister', 'azure.cli.command_modules.resource.custom#unregister_provider')
        self.cli_command(__name__, 'provider operation list', 'azure.cli.command_modules.resource.custom#list_provider_operations')
        self.cli_command(__name__, 'provider operation show', 'azure.cli.command_modules.resource.custom#show_provider_operations')
        # Resource feature commands
        self.cli_command(__name__, 'feature list', 'azure.cli.command_modules.resource.custom#list_features', client_factory=cf_features)
        self.cli_command(__name__, 'feature show', 'azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.get', client_factory=cf_features, exception_handler=empty_on_404)
        self.cli_command(__name__, 'feature register', 'azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.register', client_factory=cf_features)

        # Tag commands
        self.cli_command(__name__, 'tag list', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.list', client_factory=cf_tags)
        self.cli_command(__name__, 'tag create', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.create_or_update', client_factory=cf_tags)
        self.cli_command(__name__, 'tag delete', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.delete', client_factory=cf_tags)
        self.cli_command(__name__, 'tag add-value', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.create_or_update_value', client_factory=cf_tags)
        self.cli_command(__name__, 'tag remove-value', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.delete_value', client_factory=cf_tags)


        # Resource group deployment commands
        def transform_deployments_list(result):
            sort_list = sorted(result, key=lambda deployment: deployment['properties']['timestamp'])
            return [OrderedDict([('Name', r['name']), ('Timestamp', r['properties']['timestamp']), ('State', r['properties']['provisioningState'])]) for r in sort_list]


        self.cli_command(__name__, 'group deployment create', 'azure.cli.command_modules.resource.custom#deploy_arm_template', no_wait_param='no_wait', exception_handler=handle_long_running_operation_exception)
        self.cli_generic_wait_command(__name__, 'group deployment wait', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.get', cf_deployments)
        self.cli_command(__name__, 'group deployment list', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.list_by_resource_group', client_factory=cf_deployments, table_transformer=transform_deployments_list)
        self.cli_command(__name__, 'group deployment show', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.get', client_factory=cf_deployments, exception_handler=empty_on_404)
        self.cli_command(__name__, 'group deployment delete', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.delete', client_factory=cf_deployments)
        self.cli_command(__name__, 'group deployment validate', 'azure.cli.command_modules.resource.custom#validate_arm_template', table_transformer=deployment_validate_table_format)
        self.cli_command(__name__, 'group deployment export', 'azure.cli.command_modules.resource.custom#export_deployment_as_template')

        # Resource group deployment operations commands
        self.cli_command(__name__, 'group deployment operation list', 'azure.mgmt.resource.resources.operations.deployment_operations#DeploymentOperations.list', client_factory=cf_deployment_operations)
        self.cli_command(__name__, 'group deployment operation show', 'azure.cli.command_modules.resource.custom#get_deployment_operations', client_factory=cf_deployment_operations, exception_handler=empty_on_404)

        self.cli_generic_update_command(__name__, 'resource update',
                                        'azure.cli.command_modules.resource.custom#show_resource',
                                        'azure.cli.command_modules.resource.custom#update_resource')

        self.cli_generic_update_command(__name__, 'group update',
                                        'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get',
                                        'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.create_or_update',
                                        lambda: _resource_client_factory().resource_groups)

        self.cli_command(__name__, 'policy assignment create', 'azure.cli.command_modules.resource.custom#create_policy_assignment')
        self.cli_command(__name__, 'policy assignment delete', 'azure.cli.command_modules.resource.custom#delete_policy_assignment')
        self.cli_command(__name__, 'policy assignment list', 'azure.cli.command_modules.resource.custom#list_policy_assignment')
        self.cli_command(__name__, 'policy assignment show', 'azure.cli.command_modules.resource.custom#show_policy_assignment', exception_handler=empty_on_404)

        self.cli_command(__name__, 'policy definition create', 'azure.cli.command_modules.resource.custom#create_policy_definition')
        self.cli_command(__name__, 'policy definition delete', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.delete', client_factory=cf_policy_definitions)
        self.cli_command(__name__, 'policy definition list', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.list', client_factory=cf_policy_definitions)
        self.cli_command(__name__, 'policy definition show', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.get', client_factory=cf_policy_definitions, exception_handler=empty_on_404)
        self.cli_command(__name__, 'policy definition update', 'azure.cli.command_modules.resource.custom#update_policy_definition')

        self.cli_command(__name__, 'lock create', 'azure.cli.command_modules.resource.custom#create_lock')
        self.cli_command(__name__, 'lock delete', 'azure.cli.command_modules.resource.custom#delete_lock')
        self.cli_command(__name__, 'lock list', 'azure.cli.command_modules.resource.custom#list_locks')
        self.cli_command(__name__, 'lock show', 'azure.cli.command_modules.resource.custom#get_lock', exception_handler=empty_on_404)
        self.cli_command(__name__, 'lock update', 'azure.cli.command_modules.resource.custom#update_lock')

        self.cli_command(__name__, 'resource link create', 'azure.cli.command_modules.resource.custom#create_resource_link')
        self.cli_command(__name__, 'resource link delete', 'azure.mgmt.resource.links.operations#ResourceLinksOperations.delete', client_factory=cf_resource_links)
        self.cli_command(__name__, 'resource link show', 'azure.mgmt.resource.links.operations#ResourceLinksOperations.get', client_factory=cf_resource_links, exception_handler=empty_on_404)
        self.cli_command(__name__, 'resource link list', 'azure.cli.command_modules.resource.custom#list_resource_links')
        self.cli_command(__name__, 'resource link update', 'azure.cli.command_modules.resource.custom#update_resource_link')

        self.cli_command(__name__, 'managedapp create', 'azure.cli.command_modules.resource.custom#create_appliance')
        self.cli_command(__name__, 'managedapp delete', 'azure.mgmt.resource.managedapplications.operations#AppliancesOperations.delete', client_factory=cf_resource_managedapplications)
        self.cli_command(__name__, 'managedapp show', 'azure.cli.command_modules.resource.custom#show_appliance', exception_handler=empty_on_404)
        self.cli_command(__name__, 'managedapp list', 'azure.cli.command_modules.resource.custom#list_appliances')

        self.cli_command(__name__, 'managedapp definition create', 'azure.cli.command_modules.resource.custom#create_appliancedefinition')
        self.cli_command(__name__, 'managedapp definition delete', 'azure.mgmt.resource.managedapplications.operations#ApplianceDefinitionsOperations.delete', client_factory=cf_resource_managedappdefinitions)
        self.cli_command(__name__, 'managedapp definition show', 'azure.cli.command_modules.resource.custom#show_appliancedefinition')
        self.cli_command(__name__, 'managedapp definition list', 'azure.mgmt.resource.managedapplications.operations#ApplianceDefinitionsOperations.list_by_resource_group', client_factory=cf_resource_managedappdefinitions, exception_handler=empty_on_404)

        return self.command_table

    def load_arguments(self, command):
        from argcomplete.completers import FilesCompleter

        from azure.mgmt.resource.resources.models import DeploymentMode
        from azure.mgmt.resource.locks.models import LockLevel
        from azure.mgmt.resource.managedapplications.models import ApplianceLockLevel
        from azure.cli.core.commands.parameters import \
            (resource_group_name_type, tag_type, tags_type, get_resource_group_completion_list, no_wait_type, file_type)

        from knack.arguments import enum_choice_list, ignore_type, CLIArgumentType

        from .custom import (get_policy_completion_list, get_policy_assignment_completion_list,
                             get_resource_types_completion_list, get_providers_completion_list)
        from ._validators import process_deployment_create_namespace, validate_lock_parameters

        # BASIC PARAMETER CONFIGURATION

        resource_name_type = CLIArgumentType(options_list=('--name', '-n'), help='The resource name. (Ex: myC)')
        resource_type_type = CLIArgumentType(help="The resource type (Ex: 'resC'). Can also accept namespace/type format (Ex: 'Microsoft.Provider/resC')")
        resource_namespace_type = CLIArgumentType(options_list=('--namespace',), completer=get_providers_completion_list,
                                                  help="Provider namespace (Ex: 'Microsoft.Provider')")
        resource_parent_type = CLIArgumentType(required=False, options_list=('--parent',),
                                               help="The parent path (Ex: 'resA/myA/resB/myB')")
        _PROVIDER_HELP_TEXT = 'the resource namespace, aka \'provider\''
        self.register_cli_argument('resource', 'no_wait', no_wait_type)
        self.register_cli_argument('resource', 'resource_id', ignore_type)
        self.register_cli_argument('resource', 'resource_name', resource_name_type, id_part='resource_name')
        self.register_cli_argument('resource', 'api_version', help='The api version of the resource (omit for latest)', required=False)
        self.register_cli_argument('resource', 'resource_provider_namespace', resource_namespace_type, id_part='resource_namespace')
        self.register_cli_argument('resource', 'resource_type', arg_type=resource_type_type, completer=get_resource_types_completion_list, id_part='resource_type')
        self.register_cli_argument('resource', 'parent_resource_path', resource_parent_type, id_part='resource_parent')
        self.register_cli_argument('resource', 'tag', tag_type)
        self.register_cli_argument('resource', 'tags', tags_type)

        self.register_cli_argument('resource list', 'name', resource_name_type)
        self.register_cli_argument('resource move', 'ids', nargs='+')

        self.register_cli_argument('resource create', 'resource_id', options_list=['--id'], help='Resource ID.', action=None)
        self.register_cli_argument('resource create', 'properties', options_list=('--properties', '-p'), help='a JSON-formatted string containing resource properties')
        self.register_cli_argument('resource create', 'is_full_object', action='store_true', help='Indicates that the properties object includes other options such as location, tags, sku, and/or plan.')

        self.register_cli_argument('provider', 'top', ignore_type)
        self.register_cli_argument('provider register', 'wait', action='store_true', help='wait for the registration to finish')
        self.register_cli_argument('provider unregister', 'wait', action='store_true', help='wait for unregistration to finish')
        self.register_cli_argument('provider', 'resource_provider_namespace', options_list=('--namespace', '-n'), completer=get_providers_completion_list, help=_PROVIDER_HELP_TEXT)
        self.register_cli_argument('provider operation', 'api_version', help="The api version of the 'Microsoft.Authorization/providerOperations' resource (omit for latest)")

        self.register_cli_argument('feature', 'resource_provider_namespace', options_list=('--namespace',), required=True, help=_PROVIDER_HELP_TEXT)
        self.register_cli_argument('feature list', 'resource_provider_namespace', options_list=('--namespace',), required=False, help=_PROVIDER_HELP_TEXT)
        self.register_cli_argument('feature', 'feature_name', options_list=('--name', '-n'), help='the feature name')

        existing_policy_definition_name_type = CLIArgumentType(options_list=('--name', '-n'), completer=get_policy_completion_list, help='The policy definition name')
        self.register_cli_argument('policy', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group where the policy will be applied')
        self.register_cli_argument('policy definition', 'policy_definition_name', arg_type=existing_policy_definition_name_type)
        self.register_cli_argument('policy definition create', 'name', options_list=('--name', '-n'), help='name of the new policy definition')
        self.register_cli_argument('policy definition', 'rules', help='JSON formatted string or a path to a file with such content', type=file_type, completer=FilesCompleter())
        self.register_cli_argument('policy definition', 'display_name', help='display name of policy definition')
        self.register_cli_argument('policy definition', 'description', help='description of policy definition')
        self.register_cli_argument('policy assignment', 'name', options_list=('--name', '-n'), completer=get_policy_assignment_completion_list, help='name of the assignment')
        self.register_cli_argument('policy assignment create', 'name', options_list=('--name', '-n'), help='name of the new assignment')
        self.register_cli_argument('policy assignment', 'scope', help='scope at which this policy assignment applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
        self.register_cli_argument('policy assignment', 'disable_scope_strict_match', action='store_true', help='include assignment either inhertied from parent scope or at child scope')
        self.register_cli_argument('policy assignment', 'display_name', help='display name of the assignment')
        self.register_cli_argument('policy assignment', 'policy', help='policy name or fully qualified id', completer=get_policy_completion_list)

        self.register_cli_argument('group', 'tag', tag_type)
        self.register_cli_argument('group', 'tags', tags_type)
        self.register_cli_argument('group', 'resource_group_name', resource_group_name_type, options_list=('--name', '-n'))

        self.register_cli_argument('group deployment', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
        self.register_cli_argument('group deployment', 'deployment_name', options_list=('--name', '-n'), required=True, help='The deployment name.')
        self.register_cli_argument('group deployment', 'template_file', completer=FilesCompleter(), type=file_type, help="a template file path in the file system")
        self.register_cli_argument('group deployment', 'template_uri', help='a uri to a remote template file')
        self.register_cli_argument('group deployment', 'mode', help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)', **enum_choice_list(DeploymentMode))

        self.register_cli_argument('group deployment create', 'deployment_name', options_list=('--name', '-n'), required=False,
                              validator=process_deployment_create_namespace, help='The deployment name. Default to template file base name')
        self.register_cli_argument('group deployment', 'parameters', action='append', nargs='+', completer=FilesCompleter())

        self.register_cli_argument('group deployment operation show', 'operation_ids', nargs='+', help='A list of operation ids to show')

        self.register_cli_argument('group export', 'include_comments', action='store_true')
        self.register_cli_argument('group export', 'include_parameter_default_value', action='store_true')
        self.register_cli_argument('group create', 'rg_name', options_list=('--name', '-n'), help='name of the new resource group', completer=None)

        self.register_cli_argument('tag', 'tag_name', options_list=('--name', '-n'))
        self.register_cli_argument('tag', 'tag_value', options_list=('--value',))

        self.register_cli_argument('lock', 'name', options_list=('--name', '-n'), validator=validate_lock_parameters)
        self.register_cli_argument('lock', 'level', options_list=('--lock-type', '-t'), **enum_choice_list(LockLevel))
        self.register_cli_argument('lock', 'parent_resource_path', resource_parent_type)
        self.register_cli_argument('lock', 'resource_provider_namespace', resource_namespace_type)
        self.register_cli_argument('lock', 'resource_type', arg_type=resource_type_type,
                              completer=get_resource_types_completion_list,)
        self.register_cli_argument('lock', 'resource_name', options_list=('--resource-name'))

        self.register_cli_argument('managedapp', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application', id_part='resource_group')
        self.register_cli_argument('managedapp', 'appliance_name', options_list=('--name', '-n'), id_part='name')

        self.register_cli_argument('managedapp definition', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application definition', id_part='resource_group')
        self.register_cli_argument('managedapp definition', 'appliance_definition_name', options_list=('--name', '-n'), id_part='name')

        self.register_cli_argument('managedapp create', 'name', options_list=('--name', '-n'), help='name of the new managed application', completer=None)
        self.register_cli_argument('managedapp create', 'location', help='the managed application location')
        self.register_cli_argument('managedapp create', 'managedapp_definition_id', options_list=('--managedapp-definition-id', '-d'), help='the full qualified managed application definition id')
        self.register_cli_argument('managedapp create', 'managedby_resource_group_id', options_list=('--managed-rg-id', '-m'), help='the resource group managed by the managed application')
        self.register_cli_argument('managedapp create', 'parameters', help='JSON formatted string or a path to a file with such content', type=file_type)

        self.register_cli_argument('managedapp definition create', 'lock_level', **enum_choice_list(ApplianceLockLevel))
        self.register_cli_argument('managedapp definition create', 'authorizations', options_list=('--authorizations', '-a'), nargs='+', help="space separated authorization pairs in a format of <principalId>:<roleDefinitionId>")
        super(ResourceCommandsLoader, self).load_arguments(command)
