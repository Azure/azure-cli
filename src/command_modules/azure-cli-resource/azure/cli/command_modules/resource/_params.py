# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from argcomplete.completers import FilesCompleter

from azure.mgmt.resource.resources.models import DeploymentMode
from azure.cli.core.commands import register_cli_argument, CliArgumentType
from azure.cli.core.commands.parameters import (ignore_type, resource_group_name_type, tag_type,
                                                tags_type, get_resource_group_completion_list,
                                                enum_choice_list, no_wait_type)
from .custom import (get_policy_completion_list, get_policy_assignment_completion_list,
                     get_resource_types_completion_list, get_providers_completion_list)
from ._validators import validate_deployment_name

# BASIC PARAMETER CONFIGURATION

resource_name_type = CliArgumentType(options_list=('--name', '-n'), help='The resource name. (Ex: myC)')
_PROVIDER_HELP_TEXT = 'the resource namespace, aka \'provider\''
register_cli_argument('resource', 'no_wait', no_wait_type)
register_cli_argument('resource', 'resource_name', resource_name_type)
register_cli_argument('resource', 'api_version', help='The api version of the resource (omit for latest)', required=False)
register_cli_argument('resource', 'resource_id', options_list=('--id',), help='Resource ID')
register_cli_argument('resource', 'resource_provider_namespace', options_list=('--namespace',), completer=get_providers_completion_list,
                      help="Provider namespace (Ex: 'Microsoft.Provider')")
register_cli_argument('resource', 'resource_type',
                      completer=get_resource_types_completion_list,
                      help="The resource type (Ex: 'resC'). Can also accept namespace/type format (Ex: 'Microsoft.Provider/resC')")
register_cli_argument('resource', 'parent_resource_path', required=False, options_list=('--parent',),
                      help="The parent path (Ex: 'resA/myA/resB/myB')")
register_cli_argument('resource', 'tag', tag_type)
register_cli_argument('resource', 'tags', tags_type)
register_cli_argument('resource list', 'name', resource_name_type)
register_cli_argument('resource move', 'ids', nargs='+')

register_cli_argument('provider', 'top', ignore_type)
register_cli_argument('provider', 'resource_provider_namespace', options_list=('--namespace', '-n'), completer=get_providers_completion_list,
                      help=_PROVIDER_HELP_TEXT)

register_cli_argument('feature', 'resource_provider_namespace', options_list=('--namespace',), required=True, help=_PROVIDER_HELP_TEXT)
register_cli_argument('feature list', 'resource_provider_namespace', options_list=('--namespace',), required=False, help=_PROVIDER_HELP_TEXT)
register_cli_argument('feature', 'feature_name', options_list=('--name', '-n'), help='the feature name')

existing_policy_definition_name_type = CliArgumentType(options_list=('--name', '-n'), completer=get_policy_completion_list, help='The policy definition name')
register_cli_argument('policy', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group where the policy will be applied')
register_cli_argument('policy definition', 'policy_definition_name', arg_type=existing_policy_definition_name_type)
register_cli_argument('policy definition create', 'name', options_list=('--name', '-n'), help='name of the new policy definition')
register_cli_argument('policy definition', 'rules', help='JSON formatted string or a path to a file with such content')
register_cli_argument('policy definition', 'display_name', help='display name of policy definition')
register_cli_argument('policy definition', 'description', help='description of policy definition')
register_cli_argument('policy assignment', 'name', options_list=('--name', '-n'), completer=get_policy_assignment_completion_list, help='name of the assignment')
register_cli_argument('policy assignment create', 'name', options_list=('--name', '-n'), help='name of the new assignment')
register_cli_argument('policy assignment', 'scope', help='scope at which this policy assignment applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
register_cli_argument('policy assignment', 'disable_scope_strict_match', action='store_true', help='include assignment either inhertied from parent scope or at child scope')
register_cli_argument('policy assignment', 'display_name', help='display name of the assignment')
register_cli_argument('policy assignment', 'policy', help='policy name or fully qualified id', completer=get_policy_completion_list)

register_cli_argument('group', 'tag', tag_type)
register_cli_argument('group', 'tags', tags_type)
register_cli_argument('group', 'resource_group_name', resource_group_name_type, options_list=('--name', '-n'))
register_cli_argument('group deployment', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
register_cli_argument('group deployment', 'deployment_name', options_list=('--name', '-n'), required=True, help='The deployment name.')
register_cli_argument('group deployment', 'parameters', completer=FilesCompleter(), help="provide deployment parameter values, either json string, or use '@<file path>' to load from a file")
register_cli_argument('group deployment', 'template_file', completer=FilesCompleter(), help="a template file path in the file system")
register_cli_argument('group deployment', 'template_uri', completer=FilesCompleter(), help='a uri to a remote template file')
register_cli_argument('group deployment', 'mode', help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)', **enum_choice_list(DeploymentMode))
register_cli_argument('group deployment create', 'deployment_name', options_list=('--name', '-n'), required=False,
                      validator=validate_deployment_name, help='The deployment name. Default to template file base name')
register_cli_argument('group deployment operation show', 'operation_ids', nargs='+', help='A list of operation ids to show')
register_cli_argument('group export', 'include_comments', action='store_true')
register_cli_argument('group export', 'include_parameter_default_value', action='store_true')
register_cli_argument('group create', 'resource_group_name', completer=None)

register_cli_argument('tag', 'tag_name', options_list=('--name', '-n'))
register_cli_argument('tag', 'tag_value', options_list=('--value',))
