# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from argcomplete.completers import FilesCompleter

from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.locks.models import LockLevel
from azure.mgmt.resource.managedapplications.models import ApplicationLockLevel
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands import register_cli_argument, CliArgumentType, VersionConstraint
from azure.cli.core.commands.parameters import (ignore_type, resource_group_name_type, tag_type,
                                                tags_type, get_resource_group_completion_list,
                                                enum_choice_list, no_wait_type, file_type)
from .custom import (get_policy_completion_list, get_policy_set_completion_list,
                     get_policy_assignment_completion_list, get_resource_types_completion_list,
                     get_providers_completion_list)
from ._validators import (process_deployment_create_namespace, validate_lock_parameters, validate_subscription_lock,
                          validate_group_lock, validate_resource_lock)

# BASIC PARAMETER CONFIGURATION

resource_name_type = CliArgumentType(options_list=('--name', '-n'), help='The resource name. (Ex: myC)')
resource_type_type = CliArgumentType(help="The resource type (Ex: 'resC'). Can also accept namespace/type"
                                          " format (Ex: 'Microsoft.Provider/resC')")
resource_namespace_type = CliArgumentType(options_list=('--namespace',), completer=get_providers_completion_list,
                                          help="Provider namespace (Ex: 'Microsoft.Provider')")
resource_parent_type = CliArgumentType(required=False, options_list=('--parent',),
                                       help="The parent path (Ex: 'resA/myA/resB/myB')")
_PROVIDER_HELP_TEXT = 'the resource namespace, aka \'provider\''
register_cli_argument('resource', 'no_wait', no_wait_type)
register_cli_argument('resource', 'resource_name', resource_name_type)
register_cli_argument('resource', 'api_version', help='The api version of the resource (omit for latest)', required=False)
register_cli_argument('resource', 'resource_provider_namespace', resource_namespace_type)
register_cli_argument('resource', 'resource_type', arg_type=resource_type_type, completer=get_resource_types_completion_list)
register_cli_argument('resource', 'parent_resource_path', resource_parent_type)
register_cli_argument('resource', 'tag', tag_type)
register_cli_argument('resource', 'tags', tags_type)
register_cli_argument('resource', 'resource_ids', nargs='+', options_list=('--ids'), help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.')

register_cli_argument('resource list', 'name', resource_name_type)
register_cli_argument('resource move', 'ids', nargs='+')
register_cli_argument('resource invoke-action', 'action', help='The action that will be invoked on the specified resource')
register_cli_argument('resource invoke-action', 'request_body', help='JSON encoded parameter arguments for the action that will be passed along in the post request body. Use @{file} to load from a file.')

register_cli_argument('resource create', 'resource_id', options_list=['--id'], help='Resource ID.', action=None)
register_cli_argument('resource create', 'properties', options_list=('--properties', '-p'),
                      help='a JSON-formatted string containing resource properties')
register_cli_argument('resource create', 'is_full_object', action='store_true',
                      help='Indicates that the properties object includes other options such as location, tags, sku, and/or plan.')

register_cli_argument('provider', 'top', ignore_type)
register_cli_argument('provider register', 'wait', action='store_true', help='wait for the registration to finish')
register_cli_argument('provider unregister', 'wait', action='store_true', help='wait for unregistration to finish')
register_cli_argument('provider', 'resource_provider_namespace', options_list=('--namespace', '-n'), completer=get_providers_completion_list,
                      help=_PROVIDER_HELP_TEXT)
register_cli_argument('provider operation', 'api_version', help="The api version of the 'Microsoft.Authorization/providerOperations' resource (omit for latest)")

register_cli_argument('feature', 'resource_provider_namespace', options_list=('--namespace',), required=True, help=_PROVIDER_HELP_TEXT)
register_cli_argument('feature list', 'resource_provider_namespace', options_list=('--namespace',), required=False, help=_PROVIDER_HELP_TEXT)
register_cli_argument('feature', 'feature_name', options_list=('--name', '-n'), help='the feature name')

existing_policy_definition_name_type = CliArgumentType(options_list=('--name', '-n'), completer=get_policy_completion_list, help='The policy definition name')
register_cli_argument('policy', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group where the policy will be applied')
register_cli_argument('policy definition', 'policy_definition_name', arg_type=existing_policy_definition_name_type)
register_cli_argument('policy definition create', 'name', options_list=('--name', '-n'), help='name of the new policy definition')
register_cli_argument('policy definition', 'rules',
                      help='JSON formatted string or a path to a file or uri with such content',
                      type=file_type, completer=FilesCompleter())

with VersionConstraint(ResourceType.MGMT_RESOURCE_POLICY, min_api='2016-12-01') as c:
    from azure.mgmt.resource.policy.models import PolicyMode
    c.register_cli_argument('policy definition', 'params',
                            help='JSON formatted string or a path to a file or uri with parameter definitions',
                            type=file_type, completer=FilesCompleter())
    c.register_cli_argument('policy definition create', 'mode',
                            options_list=('--mode', '-m'),
                            help='mode of the new policy definition.',
                            **enum_choice_list(PolicyMode))

register_cli_argument('policy definition', 'display_name', help='display name of policy definition')
register_cli_argument('policy definition', 'description', help='description of policy definition')
register_cli_argument('policy assignment', 'name', options_list=('--name', '-n'), completer=get_policy_assignment_completion_list, help='name of the assignment')
register_cli_argument('policy assignment create', 'name', options_list=('--name', '-n'), help='name of the new assignment')

with VersionConstraint(ResourceType.MGMT_RESOURCE_POLICY, min_api='2016-12-01') as c:
    c.register_cli_argument('policy assignment create', 'params', options_list=('--params', '-p'),
                            help='JSON formatted string or path to file with parameter values of policy rule')

with VersionConstraint(ResourceType.MGMT_RESOURCE_POLICY, min_api='2017-06-01-preview') as c:
    existing_policy_set_definition_name_type = CliArgumentType(options_list=('--name', '-n'), completer=get_policy_set_completion_list, help='The policy set definition name')
    c.register_cli_argument('policy set-definition', 'policy_set_definition_name', arg_type=existing_policy_set_definition_name_type)
    c.register_cli_argument('policy set-definition create', 'name', options_list=('--name', '-n'), help='name of the new policy set definition')
    c.register_cli_argument('policy set-definition', 'display_name', help='display name of policy set definition')
    c.register_cli_argument('policy set-definition', 'description', help='description of policy set definition')
    c.register_cli_argument('policy set-definition', 'params',
                            help='JSON formatted string or a path to a file or uri with parameter definitions',
                            type=file_type, completer=FilesCompleter())
    c.register_cli_argument('policy set-definition', 'definitions',
                            help='JSON formatted string or a path to a file or uri with such content',
                            type=file_type, completer=FilesCompleter())
    c.register_cli_argument('policy assignment create', 'policy_set_definition', options_list=('--policy-set-definition', '-d'),
                            help='name or id of the policy set definition.')
    c.register_cli_argument('policy assignment create', 'sku', options_list=('--sku', '-s'),
                            help='policy sku.', **enum_choice_list(['free', 'standard']))
    c.register_cli_argument('policy assignment create', 'notscopes', options_list=('--not-scopes'), nargs='+')

register_cli_argument('policy assignment', 'scope', help='scope at which this policy assignment applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
register_cli_argument('policy assignment', 'disable_scope_strict_match', action='store_true', help='include assignment either inhertied from parent scope or at child scope')
register_cli_argument('policy assignment', 'display_name', help='display name of the assignment')
register_cli_argument('policy assignment', 'policy', help='name or id of the policy definition.', completer=get_policy_completion_list)

register_cli_argument('group', 'tag', tag_type)
register_cli_argument('group', 'tags', tags_type)
register_cli_argument('group', 'resource_group_name', resource_group_name_type, options_list=['--name', '--resource-group', '-n', '-g'])

register_cli_argument('group deployment', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
register_cli_argument('group deployment', 'deployment_name', options_list=('--name', '-n'), required=True, help='The deployment name.')
register_cli_argument('group deployment', 'template_file', completer=FilesCompleter(), type=file_type, help="a template file path in the file system")
register_cli_argument('group deployment', 'template_uri', help='a uri to a remote template file')
register_cli_argument('group deployment', 'mode', help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)', **enum_choice_list(DeploymentMode))

register_cli_argument('group deployment create', 'deployment_name', options_list=('--name', '-n'), required=False,
                      validator=process_deployment_create_namespace, help='The deployment name. Default to template file base name')
register_cli_argument('group deployment', 'parameters', action='append', nargs='+', completer=FilesCompleter())

register_cli_argument('group deployment operation show', 'operation_ids', nargs='+', help='A list of operation ids to show')

register_cli_argument('group export', 'include_comments', action='store_true')
register_cli_argument('group export', 'include_parameter_default_value', action='store_true')
register_cli_argument('group create', 'rg_name', options_list=['--name', '--resource-group', '-n', '-g'], help='name of the new resource group', completer=None)

register_cli_argument('tag', 'tag_name', options_list=('--name', '-n'))
register_cli_argument('tag', 'tag_value', options_list=('--value',))

register_cli_argument('managedapp', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application', id_part='resource_group')
register_cli_argument('managedapp', 'application_name', options_list=('--name', '-n'), id_part='name')

register_cli_argument('managedapp definition', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application definition', id_part='resource_group')
register_cli_argument('managedapp definition', 'application_definition_name', options_list=('--name', '-n'), id_part='name')

register_cli_argument('managedapp create', 'name', options_list=('--name', '-n'), help='name of the new managed application', completer=None)
register_cli_argument('managedapp create', 'location', help='the managed application location')
register_cli_argument('managedapp create', 'managedapp_definition_id', options_list=('--managedapp-definition-id', '-d'), help='the full qualified managed application definition id')
register_cli_argument('managedapp create', 'managedby_resource_group_id', options_list=('--managed-rg-id', '-m'), help='the resource group managed by the managed application')
register_cli_argument('managedapp create', 'parameters', help='JSON formatted string or a path to a file with such content', type=file_type, completer=FilesCompleter())

register_cli_argument('managedapp definition create', 'lock_level', **enum_choice_list(ApplicationLockLevel))
register_cli_argument('managedapp definition create', 'authorizations', options_list=('--authorizations', '-a'), nargs='+', help="space separated authorization pairs in a format of <principalId>:<roleDefinitionId>")
register_cli_argument('managedapp definition create', 'createUiDefinition', options_list=('--create-ui-definition', '-c'), help='JSON formatted string or a path to a file with such content', type=file_type, completer=FilesCompleter())
register_cli_argument('managedapp definition create', 'mainTemplate', options_list=('--main-template', '-t'), help='JSON formatted string or a path to a file with such content', type=file_type, completer=FilesCompleter())

register_cli_argument('lock', 'parent_resource_path', resource_parent_type)
register_cli_argument('lock', 'resource_provider_namespace', resource_namespace_type)
register_cli_argument('lock', 'resource_type', arg_type=resource_type_type, completer=get_resource_types_completion_list)
register_cli_argument('lock', 'resource_name', options_list=('--resource-name'), help='Name of the resource being locked.')
register_cli_argument('lock', 'resource_group', resource_group_name_type, validator=validate_lock_parameters)

register_cli_argument('resource lock', 'resource_group', resource_group_name_type)
register_cli_argument('resource lock', 'resource_name', options_list=('--resource-name'), validator=validate_resource_lock)

register_cli_argument('group lock', 'resource_group', resource_group_name_type, validator=validate_group_lock)

register_cli_argument('account lock', 'resource_group', ignore_type, validator=validate_subscription_lock)

for scope in ['account', 'group']:
    register_cli_argument('{} lock'.format(scope), 'resource_provider_namespace', ignore_type)
    register_cli_argument('{} lock'.format(scope), 'parent_resource_path', ignore_type)
    register_cli_argument('{} lock'.format(scope), 'resource_type', ignore_type)
    register_cli_argument('{} lock'.format(scope), 'resource_name', ignore_type)

for command_name in ['lock', 'account lock', 'group lock', 'resource lock']:
    register_cli_argument(command_name, 'lock_name', options_list=('--name', '-n'), help='Name of the lock')
    register_cli_argument(command_name, 'level', options_list=('--lock-type', '-t'), **enum_choice_list([LockLevel.can_not_delete, LockLevel.read_only]))
    register_cli_argument(command_name, 'ids', nargs='+', options_list=('--ids'), help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.')
    register_cli_argument(command_name, 'notes', help='Notes about this lock.')
