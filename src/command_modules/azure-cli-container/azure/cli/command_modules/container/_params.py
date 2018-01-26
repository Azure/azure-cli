# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core.commands.parameters import (get_enum_type,
                                                get_location_type,
                                                resource_group_name_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.mgmt.containerinstance.models import (ContainerGroupRestartPolicy, OperatingSystemTypes)
from ._validators import validate_volume_mount_path

# pylint: disable=line-too-long

IP_ADDRESS_TYPES = ['Public']


def _environment_variables_type(value):
    """Space separated values in 'key=value' format."""
    try:
        env_name, env_value = value.split('=', 1)
    except ValueError:
        message = ("Incorrectly formatted environment settings. "
                   "Argument values should be in the format a=b c=d")
        raise CLIError(message)
    return {'name': env_name, 'value': env_value}


def load_arguments(self, _):
    with self.argument_context('container') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('name', options_list=['--name', '-n'], help="The name of the container group", id_part='name')
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('container create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('image', help='The container image name')
        c.argument('cpu', type=int, help='The required number of CPU cores of the containers')
        c.argument('memory', type=float, help='The required memory of the containers in GB')
        c.argument('os_type', arg_type=get_enum_type(OperatingSystemTypes), help='The OS type of the containers')
        c.argument('ip_address', arg_type=get_enum_type(IP_ADDRESS_TYPES), help='The IP address type of the container group')
        c.argument('ports', type=int, nargs='+', default=[80], help='The ports to open')
        c.argument('restart_policy', arg_type=get_enum_type(ContainerGroupRestartPolicy), help='Restart policy for all containers within the container group')
        c.argument('command_line', help='The command line to run when the container is started, e.g. \'/bin/bash -c myscript.sh\'')
        c.argument('environment_variables', nargs='+', options_list=['--environment-variables', '-e'], type=_environment_variables_type, help='A list of environment variable for the container. Space separated values in \'key=value\' format.')

    with self.argument_context('container create', arg_group='Image Registry') as c:
        c.argument('registry_login_server', help='The container image registry login server')
        c.argument('registry_username', help='The username to log in container image registry server')
        c.argument('registry_password', help='The password to log in container image registry server')

    with self.argument_context('container create', arg_group='Azure File Volume') as c:
        c.argument('azure_file_volume_share_name', help='The name of the Azure File share to be mounted as a volume')
        c.argument('azure_file_volume_account_name', help='The name of the storage account that contains the Azure File share')
        c.argument('azure_file_volume_account_key', help='The storage account access key used to access the Azure File share')
        c.argument('azure_file_volume_mount_path', validator=validate_volume_mount_path, help='The path within the container where the volume should be mounted. Must not contain colon (:).')

    with self.argument_context('container logs') as c:
        c.argument('container_name', help='The container name to tail the logs')
