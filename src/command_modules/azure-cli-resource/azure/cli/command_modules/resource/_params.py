#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse

from argcomplete.completers import FilesCompleter

from azure.mgmt.resource.resources.models import DeploymentMode
from azure.cli.commands import register_cli_argument, CliArgumentType
from azure.cli.commands.parameters import (resource_group_name_type,
                                           tag_type,
                                           tags_type,
                                           get_resource_group_completion_list)
from .custom import get_policy_completion_list, get_policy_assignment_completion_list
from ._validators import validate_resource_type, validate_parent, resolve_resource_parameters

# BASIC PARAMETER CONFIGURATION

choices_deployment_mode = [e.value.lower() for e in DeploymentMode]

resource_type_type = CliArgumentType(
    help='The resource type in <namespace>/<type> format.',
    type=validate_resource_type,
    validator=resolve_resource_parameters
)

resource_name_type = CliArgumentType(options_list=('--name', '-n'))
register_cli_argument('resource', 'resource_name', resource_name_type)
register_cli_argument('resource', 'api_version', CliArgumentType(help='The api version of the resource (omit for latest)', required=False))
register_cli_argument('resource', 'resource_provider_namespace', CliArgumentType(help=argparse.SUPPRESS, required=False))
register_cli_argument('resource', 'resource_type', resource_type_type)
register_cli_argument('resource', 'parent_resource_path', CliArgumentType(help='The parent resource type in <type>/<name> format.', type=validate_parent, required=False, options_list=('--parent',)))
register_cli_argument('resource', 'tag', tag_type)
register_cli_argument('resource', 'tags', tags_type)
register_cli_argument('resource list', 'name', resource_name_type)
register_cli_argument('resource move', 'ids', nargs='+')

_PROVIDER_HELP_TEXT = 'the resource namespace, aka \'provider\''
register_cli_argument('resource provider', 'top', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('resource provider', 'resource_provider_namespace', CliArgumentType(options_list=('--namespace', '-n'), help=_PROVIDER_HELP_TEXT))

register_cli_argument('resource feature', 'resource_provider_namespace', CliArgumentType(options_list=('--namespace',), required=True, help=_PROVIDER_HELP_TEXT))
register_cli_argument('resource feature list', 'resource_provider_namespace', CliArgumentType(options_list=('--namespace',), required=False, help=_PROVIDER_HELP_TEXT))
register_cli_argument('resource feature', 'feature_name', CliArgumentType(options_list=('--name', '-n'), help='the feature name'))

register_cli_argument('resource policy', 'resource_group_name', arg_type=resource_group_name_type, help='the resource group where the policy will be applied')
register_cli_argument('resource policy', 'policy_definition_name', options_list=('--name', '-n'), completer=get_policy_completion_list, help='name of policy definition')
register_cli_argument('resource policy create', 'policy_definition_name', completer=None)
register_cli_argument('resource policy create', 'rules', help='JSON formatted string or a path to a file with such content')
register_cli_argument('resource policy create', 'display_name', help='display name of policy definition')
register_cli_argument('resource policy create', 'description', help='description of policy definition')
register_cli_argument('resource policy assignment', 'policy_assignment_name', options_list=('--name', '-n'), completer=get_policy_assignment_completion_list, help='name of the assignment')
register_cli_argument('resource policy assignment', 'resource_id', help='id of the associated resource where the policy will be applied')
register_cli_argument('resource policy assignment', 'show_all', action='store_true', help='show all the assignment under the current subscription')
register_cli_argument('resource policy assignment', 'include_inherited', action='store_true', help='show assignments from parent scopes')
register_cli_argument('resource policy assignment', 'display_name', help='display name of the assignment')
register_cli_argument('resource policy assignment', 'policy', help='policy name or fully qualified id', completer=get_policy_completion_list)
register_cli_argument('resource policy assignment create', 'policy_assignment_name', completer=None)

register_cli_argument('resource group', 'resource_group_name', resource_group_name_type, options_list=('--name', '-n'))
register_cli_argument('resource group deployment', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
register_cli_argument('resource group deployment', 'deployment_name', CliArgumentType(options_list=('--name', '-n'), required=True, help='The deployment name.'))
register_cli_argument('resource group deployment', 'parameters_file_path', completer=FilesCompleter())
register_cli_argument('resource group deployment', 'template_file_path', completer=FilesCompleter())
register_cli_argument('resource group deployment', 'mode', CliArgumentType(
    choices=choices_deployment_mode, type=str.lower,
    help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)'))
register_cli_argument('resource group export', 'include_comments', CliArgumentType(action='store_true'))
register_cli_argument('resource group export', 'include_parameter_default_value', CliArgumentType(action='store_true'))
register_cli_argument('resource group create', 'resource_group_name', completer=None)

register_cli_argument('tag', 'tag_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('tag', 'tag_value', CliArgumentType(options_list=('--value',)))

