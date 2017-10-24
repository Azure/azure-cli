# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (enum_choice_list,
                                                location_type,
                                                resource_group_name_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.util import CLIError
import azure.cli.core.commands.arm  # pylint: disable=unused-import

# pylint: disable=line-too-long

IP_ADDRESS_TYPES = ['Public']
OS_TYPES = ['Windows', 'Linux']


def environment_variables_format(value):
    """Space separated values in 'key=value' format."""
    try:
        env_name, env_value = value.split('=', 1)
    except ValueError:
        message = ("Incorrectly formatted environment settings. "
                   "Argument values should be in the format a=b c=d")
        raise CLIError(message)
    return {'name': env_name, 'value': env_value}


register_cli_argument('container', 'resource_group_name', resource_group_name_type)
register_cli_argument('container', 'name', options_list=('--name', '-n'), help="The name of the container group", id_part='name')
register_cli_argument('container', 'location', location_type)

register_cli_argument('container create', 'location', location_type, validator=get_default_location_from_resource_group)
register_cli_argument('container create', 'image', help='The container image name')
register_cli_argument('container create', 'cpu', type=int, help='The required number of CPU cores of the containers')
register_cli_argument('container create', 'memory', type=float, help='The required memory of the containers in GB')
register_cli_argument('container create', 'os_type', help='The OS type of the containers', **enum_choice_list(OS_TYPES))
register_cli_argument('container create', 'ip_address', help='The IP address type of the container group', **enum_choice_list(IP_ADDRESS_TYPES))
register_cli_argument('container create', 'command_line', help='The command line to run when the container is started, e.g. \'/bin/bash -c myscript.sh\'')
register_cli_argument('container create', 'environment_variables', nargs='+', options_list=('--environment-variables', '-e'), type=environment_variables_format, help='A list of environment variable for the container. Space separated values in \'key=value\' format.')
register_cli_argument('container create', 'registry_login_server', arg_group='Image Registry', help='The container image registry login server')
register_cli_argument('container create', 'registry_username', arg_group='Image Registry', help='The username to log in container image registry server')
register_cli_argument('container create', 'registry_password', arg_group='Image Registry', help='The password to log in container image registry server')

register_cli_argument('container logs', 'container_name', help='The container name to tail the logs')
