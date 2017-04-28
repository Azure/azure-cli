# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import os
import platform

from argcomplete.completers import FilesCompleter

from azure.cli.core.commands import (
    CliArgumentType,
    register_cli_argument,
    register_extra_cli_argument)
from azure.cli.core.commands.parameters import tags_type
from azure.cli.core.commands.parameters import (
    enum_choice_list,
    file_type,
    resource_group_name_type,
    get_one_of_subscription_locations,
    get_resource_name_completion_list)
from azure.mgmt.compute.containerservice.models import ContainerServiceOchestratorTypes
from azure.cli.command_modules.vm._validators import validate_ssh_key


def _compute_client_factory(**_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceType.MGMT_COMPUTE)


def get_vm_sizes(location):
    return list(_compute_client_factory().virtual_machine_sizes.list(location))


def get_vm_size_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = get_vm_sizes(location)
    return [r.name for r in result]


def _get_default_install_location(exe_name):
    system = platform.system()
    if system == 'Windows':
        program_files = os.environ.get('ProgramFiles')
        if not program_files:
            return None
        install_location = '{}\\{}.exe'.format(program_files, exe_name)
    elif system == 'Linux' or system == 'Darwin':
        install_location = '/usr/local/bin/{}'.format(exe_name)
    else:
        install_location = None
    return install_location


name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

register_cli_argument('acs', 'tags', tags_type)

register_cli_argument('acs', 'name', arg_type=name_arg_type, configured_default='acs',
                      help="ACS cluster name. You can configure the default using `az configure --defaults acs=<name>`",
                      completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'))

register_cli_argument('acs', 'resource_group', arg_type=resource_group_name_type)

register_cli_argument('acs', 'orchestrator_type', options_list=('--orchestrator-type', '-t'), **enum_choice_list(ContainerServiceOchestratorTypes))
# some admin names are prohibited in acs, such as root, admin, etc. Because we have no control on the orchestrators, so default to a safe name.
register_cli_argument('acs', 'admin_username', options_list=('--admin-username',), default='azureuser', required=False)
register_cli_argument('acs', 'dns_name_prefix', options_list=('--dns-prefix', '-d'))
register_cli_argument('acs', 'container_service_name', options_list=('--name', '-n'), help='The name of the container service', completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'))

register_cli_argument('acs', 'ssh_key_value', required=False, help='SSH key file value or key file path.', type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'), completer=FilesCompleter())
register_cli_argument('acs create', 'name', arg_type=name_arg_type, validator=validate_ssh_key)

register_extra_cli_argument('acs create', 'generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing')
register_cli_argument('acs create', 'agent_vm_size', completer=get_vm_size_completion_list)

register_cli_argument('acs create', 'windows', action='store_true', help='If true, deploy a windows container cluster.')
register_cli_argument('acs create', 'validate', action='store_true', help='Generate and validate the ARM template without creating any resources')


register_cli_argument('acs', 'disable_browser', help='Do not open browser after opening a proxy to the cluster web user interface')
register_cli_argument('acs dcos browse', 'name', name_arg_type)
register_cli_argument('acs dcos install-cli', 'install_location',
                      options_list=('--install-location',),
                      default=_get_default_install_location('dcos'))
register_cli_argument('acs kubernetes install-cli', 'install_location',
                      options_list=('--install-location',),
                      default=_get_default_install_location('kubectl'))

# TODO: Make this derive from the cluster object, instead of just preset values
register_cli_argument('acs kubernetes get-credentials', 'dns_prefix')
register_cli_argument('acs kubernetes get-credentials', 'location')
register_cli_argument('acs kubernetes get-credentials', 'path',
                      options_list=('--file', '-f',),
                      default=os.path.join(os.path.expanduser('~'), '.kube', 'config'),
                      type=file_type,
                      completer=FilesCompleter())
register_cli_argument('acs scale', 'new_agent_count', type=int, help='The number of agents for the cluster')
register_cli_argument('acs create', 'service_principal', help='Service principal for making calls into Azure APIs')
register_cli_argument('acs create', 'client_secret', help='Client secret to use with the service principal for making calls to Azure APIs')
