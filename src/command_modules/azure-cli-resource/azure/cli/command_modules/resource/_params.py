# pylint: disable=line-too-long
import argparse

from argcomplete.completers import FilesCompleter

from azure.cli.commands import register_cli_argument, CliArgumentType
from azure.cli.commands.parameters import (resource_group_name_type,
                                           tag_type,
                                           tags_type,
                                           get_resource_group_completion_list)

from ._validators import validate_resource_type, validate_parent, resolve_resource_parameters

# BASIC PARAMETER CONFIGURATION

resource_type_type = CliArgumentType(
    help='The resource type in <namespace>/<type> format.',
    type=validate_resource_type,
    validator=resolve_resource_parameters
)

register_cli_argument('resource', 'resource_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('resource', 'api_version', CliArgumentType(help='The api version of the resource (omit for latest)', required=False))
register_cli_argument('resource', 'resource_provider_namespace', CliArgumentType(help=argparse.SUPPRESS, required=False))
register_cli_argument('resource', 'resource_type', resource_type_type)
register_cli_argument('resource', 'parent_resource_path', CliArgumentType(help='The parent resource type in <type>/<name> format.', type=validate_parent, required=False, options_list=('--parent',)))
register_cli_argument('resource', 'tag', tag_type)
register_cli_argument('resource', 'tags', tags_type)

register_cli_argument('resource deploy', 'mode', CliArgumentType(
    choices=['incremental', 'complete'], default='incremental',
    help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)'))
register_cli_argument('resource deploy', 'resource_group', completer=get_resource_group_completion_list)
register_cli_argument('resource deploy', 'parameters_file_path', completer=FilesCompleter())
register_cli_argument('resource deploy', 'template_file_path', completer=FilesCompleter())

register_cli_argument('resource provider', 'top', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('resource provider', 'resource_provider_namespace', CliArgumentType(options_list=('--namespace', '-n'), help='the resource provider namespace to retrieve'))

register_cli_argument('resource group', 'resource_group_name', resource_group_name_type, options_list=('--name', '-n'))
register_cli_argument('resource group deployment', 'resource_group_name', arg_type=resource_group_name_type)
register_cli_argument('resource group deployment', 'deployment_name', CliArgumentType(options_list=('--name', '-n'), required=True))
register_cli_argument('resource group export', 'include_comments', CliArgumentType(action='store_true'))
register_cli_argument('resource group export', 'include_parameter_default_value', CliArgumentType(action='store_true'))
register_cli_argument('resource group create', 'resource_group_name', completer=None)

register_cli_argument('tag', 'tag_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('tag', 'tag_value', CliArgumentType(options_list=('--value',)))
