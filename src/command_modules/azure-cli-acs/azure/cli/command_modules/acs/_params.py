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
from azure.cli.core.commands.validators import validate_file_or_dict
from azure.cli.core.commands.parameters import (
    enum_choice_list,
    file_type,
    resource_group_name_type,
    get_one_of_subscription_locations,
    get_resource_name_completion_list)
from azure.cli.command_modules.acs._validators import validate_create_parameters, validate_ssh_key, validate_list_of_integers


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


def _get_feature_in_preview_message():
    return "Feature in preview, only in " + ", ".join(regionsInPreview) + ". "


regionsInPreview = ["ukwest", "uksouth", "eastus", "westcentralus", "westus2", "canadaeast", "canadacentral", "westindia", "southindia", "centralindia"]

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

orchestratorTypes = ["Custom", "DCOS", "Kubernetes", "Swarm", "DockerCE"]

storageProfileTypes = ["StorageAccount", "ManagedDisks"]

register_cli_argument('acs', 'tags', tags_type)

register_cli_argument('acs', 'name', arg_type=name_arg_type, configured_default='acs',
                      help="ACS cluster name. You can configure the default using `az configure --defaults acs=<name>`",
                      completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'))

register_cli_argument('acs', 'resource_group', arg_type=resource_group_name_type)

register_cli_argument('acs', 'orchestrator_type', options_list=('--orchestrator-type', '-t'), help='DockerCE - ' + _get_feature_in_preview_message(), **enum_choice_list(orchestratorTypes))
# some admin names are prohibited in acs, such as root, admin, etc. Because we have no control on the orchestrators, so default to a safe name.
register_cli_argument('acs', 'admin_username', options_list=('--admin-username',), default='azureuser', required=False)
register_cli_argument('acs', 'api_version', options_list=('--api-version',), required=False, help=_get_feature_in_preview_message() + 'Use API version of ACS to perform az acs operations. Available options: 2017-01-31, 2017-07-01. Default to use the latest version for the location')
register_cli_argument('acs', 'dns_name_prefix', options_list=('--dns-prefix', '-d'))
register_cli_argument('acs', 'container_service_name', options_list=('--name', '-n'), help='The name of the container service', completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'))

register_cli_argument('acs', 'ssh_key_value', required=False, help='SSH key file value or key file path.', type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'), completer=FilesCompleter())
register_cli_argument('acs create', 'name', arg_type=name_arg_type, validator=validate_ssh_key)

register_extra_cli_argument('acs create', 'generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing', validator=validate_create_parameters)
register_cli_argument('acs create', 'master_profile', options_list=('--master-profile', '-m'), type=validate_file_or_dict, help=_get_feature_in_preview_message() + 'The file or dictionary representation of the master profile. Note it will override any master settings once set')
register_cli_argument('acs create', 'master_vm_size', completer=get_vm_size_completion_list, help=_get_feature_in_preview_message())
register_cli_argument('acs create', 'master_osdisk_size', type=int, help=_get_feature_in_preview_message() + 'The disk size for master pool vms. Unit in GB. If not specified, the corresponding vmsize disk size will apply')
register_cli_argument('acs create', 'master_vnet_subnet_id', type=str, help=_get_feature_in_preview_message() + 'The custom vnet subnet id. Note agent need to used the same vnet if master set')
register_cli_argument('acs create', 'master_first_consecutive_static_ip', type=str, help=_get_feature_in_preview_message() + 'The first consecutive ip used to specify static ip block')
register_cli_argument('acs create', 'master_storage_profile', help=_get_feature_in_preview_message(), **enum_choice_list(storageProfileTypes))
register_cli_argument('acs create', 'agent_profiles', options_list=('--agent-profiles', '-a'), type=validate_file_or_dict, help=_get_feature_in_preview_message() + 'The file or dictionary representation of the agent profiles. Note it will override any agent settings once set')
register_cli_argument('acs create', 'agent_vm_size', completer=get_vm_size_completion_list)
register_cli_argument('acs create', 'agent_osdisk_size', type=int, help=_get_feature_in_preview_message() + 'The disk size for agent pool vms. Unit in GB. If not specified, the corresponding vmsize disk size will apply')
register_cli_argument('acs create', 'agent_vnet_subnet_id', type=str, help=_get_feature_in_preview_message() + 'The custom vnet subnet id. Note agent need to used the same vnet if master set')
register_cli_argument('acs create', 'agent_ports', type=validate_list_of_integers, help=_get_feature_in_preview_message() + 'The ports exposed on the agent pool, such as 8080,4000,80')
register_cli_argument('acs create', 'agent_storage_profile', help=_get_feature_in_preview_message(), **enum_choice_list(storageProfileTypes))

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
