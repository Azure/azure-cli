# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-statements

import os.path
import platform

from argcomplete.completers import FilesCompleter
from azure.cli.core.commands.parameters import (
    file_type, get_enum_type, get_resource_name_completion_list, name_type, tags_type)
from azure.cli.core.commands.validators import validate_file_or_dict

from ._completers import (
    get_vm_size_completion_list, get_k8s_versions_completion_list, get_k8s_upgrades_completion_list)
from ._validators import (
    validate_create_parameters, validate_k8s_client_version, validate_k8s_version, validate_linux_host_name,
    validate_list_of_integers, validate_ssh_key, validate_connector_name, validate_max_pods)

aci_connector_os_type = ['Windows', 'Linux', 'Both']

aci_connector_chart_url = 'https://github.com/virtual-kubelet/virtual-kubelet/raw/master/charts/virtual-kubelet-for-aks-latest.tgz'

orchestrator_types = ["Custom", "DCOS", "Kubernetes", "Swarm", "DockerCE"]

regions_in_preview = [
    "canadacentral",
    "canadaeast",
    "centralindia",
    "koreasouth",
    "koreacentral",
    "southindia",
    "uksouth",
    "ukwest",
    "westcentralus",
    "westindia",
    "westus2",
]

regions_in_prod = [
    "australiaeast",
    "australiasoutheast",
    "brazilsouth",
    "centralus",
    "eastasia",
    "eastus",
    "eastus2",
    "japaneast",
    "japanwest",
    "northcentralus",
    "northeurope",
    "southcentralus",
    "southeastasia",
    "westeurope",
    "westus",
]

storage_profile_types = ["StorageAccount", "ManagedDisks"]


def load_arguments(self, _):

    # ACS command argument configuration
    with self.argument_context('acs') as c:
        c.argument('resource_name', name_type,
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'),
                   help='Name of the container service. You can configure the default using `az configure --defaults acs=<name>`')
        c.argument('name', name_type,
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'),
                   help='Name of the container service. You can configure the default using `az configure --defaults acs=<name>`')
        c.argument('container_service_name', name_type, help='Name of the container service. You can configure the default using `az configure --defaults acs=<name>`',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'))
        c.argument('admin_username', options_list=['--admin-username', '-u'], default='azureuser')
        c.argument('api_version',
                   help=_get_feature_in_preview_message() + 'Use API version of ACS to perform az acs operations. Available options: 2017-01-31, 2017-07-01. Default: the latest version for the location')
        c.argument('dns_name_prefix', options_list=['--dns-prefix', '-d'])
        c.argument('orchestrator_type', get_enum_type(orchestrator_types), options_list=['--orchestrator-type', '-t'])
        c.argument('ssh_key_value', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'),
                   completer=FilesCompleter(), validator=validate_ssh_key)
        c.argument('tags', tags_type)
        c.argument('disable_browser', help='Do not open browser after opening a proxy to the cluster web user interface')

    with self.argument_context('acs create') as c:
        c.argument('ssh_key_value', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'),
                   completer=FilesCompleter(), validator=validate_ssh_key)
        c.argument('master_profile', options_list=['--master-profile', '-m'], type=validate_file_or_dict,
                   help=_get_feature_in_preview_message() + 'The file or dictionary representation of the master profile. Note it will override any master settings once set')
        c.argument('master_vm_size', completer=get_vm_size_completion_list, help=_get_feature_in_preview_message())
        c.argument('agent_count', type=int)
        c.argument('generate_ssh_keys', action='store_true', validator=validate_create_parameters,
                   help='Generate SSH public and private key files if missing')
        c.argument('master_osdisk_size', type=int,
                   help=_get_feature_in_preview_message() + 'The disk size for master pool vms. Unit in GB. Default: corresponding vmsize disk size')
        c.argument('master_vnet_subnet_id', type=str,
                   help=_get_feature_in_preview_message() + 'The custom vnet subnet id. Note agent need to used the same vnet if master set. Default: ""')
        c.argument('master_first_consecutive_static_ip', type=str,
                   help=_get_feature_in_preview_message() + 'The first consecutive ip used to specify static ip block.')
        c.argument('master_storage_profile', get_enum_type(storage_profile_types),
                   help=_get_feature_in_preview_message() + 'Default: varies based on Orchestrator')
        c.argument('agent_profiles', options_list=['--agent-profiles', '-a'], type=validate_file_or_dict,
                   help=_get_feature_in_preview_message() + 'The file or dictionary representation of the agent profiles. Note it will override any agent settings once set')
        c.argument('agent_vm_size', completer=get_vm_size_completion_list,
                   help='Set the default size for agent pools vms.')
        c.argument('agent_osdisk_size', type=int,
                   help=_get_feature_in_preview_message() + 'Set the default disk size for agent pools vms. Unit in GB. Default: corresponding vmsize disk size')
        c.argument('agent_vnet_subnet_id', type=str,
                   help=_get_feature_in_preview_message() + 'Set the default custom vnet subnet id for agent pools. Note agent need to used the same vnet if master set. Default: ""')
        c.argument('agent_ports', type=validate_list_of_integers,
                   help=_get_feature_in_preview_message() + 'Set the default ports exposed on the agent pools. Only usable for non-Kubernetes. Default: 8080,4000,80')
        c.argument('agent_storage_profile', get_enum_type(storage_profile_types),
                   help=_get_feature_in_preview_message() + 'Set default storage profile for agent pools. Default: varies based on Orchestrator')
        c.argument('windows', action='store_true',
                   help='If true, set the default osType of agent pools to be Windows.')
        c.argument('validate', action='store_true',
                   help='Generate and validate the ARM template without creating any resources')
        c.argument('orchestrator_version',
                   help=_get_feature_in_preview_message() + 'Use Orchestrator Version to specify the semantic version for your choice of orchestrator.')

    with self.argument_context('acs scale') as c:
        c.argument('new_agent_count', type=int)

    with self.argument_context('acs dcos browse') as c:
        c.argument('ssh_key_file', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa'),
                   completer=FilesCompleter(), help='Path to an SSH key file to use.')

    with self.argument_context('acs dcos install-cli') as c:
        c.argument('install_location', default=_get_default_install_location('dcos'))

    with self.argument_context('acs kubernetes get-credentials') as c:
        c.argument('path', options_list=['--file', '-f'])

    with self.argument_context('acs kubernetes install-cli') as c:
        c.argument('install_location', type=file_type, completer=FilesCompleter(),
                   default=_get_default_install_location('kubectl'))
        c.argument('ssh_key_file', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa'),
                   completer=FilesCompleter(), help='Path to an SSH key file to use.')

    # AKS command argument configuration
    with self.argument_context('aks') as c:
        c.argument('resource_name', name_type, help='Name of the managed cluster.',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ManagedClusters'))
        c.argument('name', name_type, help='Name of the managed cluster.',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ManagedClusters'))
        c.argument('kubernetes_version', options_list=['--kubernetes-version', '-k'], validator=validate_k8s_version)
        c.argument('node_count', options_list=['--node-count', '-c'], type=int)
        c.argument('tags', tags_type)

    with self.argument_context('aks create') as c:
        c.argument('name', validator=validate_linux_host_name)
        c.argument('kubernetes_version', completer=get_k8s_versions_completion_list)
        c.argument('admin_username', options_list=['--admin-username', '-u'], default='azureuser')
        c.argument('dns_name_prefix', options_list=['--dns-name-prefix', '-p'])
        c.argument('generate_ssh_keys', action='store_true', validator=validate_create_parameters)
        c.argument('node_vm_size', options_list=['--node-vm-size', '-s'], completer=get_vm_size_completion_list)
        c.argument('ssh_key_value', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'),
                   completer=FilesCompleter(), validator=validate_ssh_key)
        c.argument('aad_client_app_id')
        c.argument('aad_server_app_id')
        c.argument('aad_server_app_secret')
        c.argument('aad_tenant_id')
        c.argument('dns_service_ip')
        c.argument('docker_bridge_address')
        c.argument('enable_addons', options_list=['--enable-addons', '-a'])
        c.argument('disable_rbac', action='store_true')
        c.argument('enable_rbac', action='store_true', options_list=['--enable-rbac', '-r'],
                   deprecate_info=c.deprecate(redirect="--disable-rbac", hide="2.0.45"))
        c.argument('max_pods', type=int, options_list=['--max-pods', '-m'], validator=validate_max_pods)
        c.argument('network_plugin')
        c.argument('no_ssh_key', options_list=['--no-ssh-key', '-x'])
        c.argument('pod_cidr')
        c.argument('service_cidr')
        c.argument('vnet_subnet_id')
        c.argument('workspace_resource_id')
        c.argument('skip_subnet_role_assignment', action='store_true')

    with self.argument_context('aks disable-addons') as c:
        c.argument('addons', options_list=['--addons', '-a'])

    with self.argument_context('aks enable-addons') as c:
        c.argument('addons', options_list=['--addons', '-a'])

    with self.argument_context('aks get-credentials') as c:
        c.argument('admin', options_list=['--admin', '-a'], default=False)
        c.argument('path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   default=os.path.join(os.path.expanduser('~'), '.kube', 'config'))

    with self.argument_context('aks install-cli') as c:
        c.argument('client_version', validator=validate_k8s_client_version)
        c.argument('install_location', default=_get_default_install_location('kubectl'))

    with self.argument_context('aks install-connector') as c:
        c.argument('aci_resource_group', help='The resource group to create the ACI container groups')
        c.argument('chart_url', default=aci_connector_chart_url, help='URL to the chart')
        c.argument('client_secret', help='Client secret to use with the service principal for making calls to Azure APIs')
        c.argument('connector_name', default='aci-connector', help='The name for the ACI Connector', validator=validate_connector_name)
        c.argument('image_tag', help='The image tag of the virtual kubelet')
        c.argument('location', help='The location to create the ACI container groups')
        c.argument('os_type', get_enum_type(aci_connector_os_type), help='The OS type of the connector')
        c.argument('service_principal',
                   help='Service principal for making calls into Azure APIs. If not set, auto generate a new service principal of Contributor role, and save it locally for reusing')

    with self.argument_context('aks remove-connector') as c:
        c.argument('connector_name', default='aci-connector', help='The name for the ACI Connector', validator=validate_connector_name)
        c.argument('graceful', action='store_true',
                   help='Mention if you want to drain/uncordon your aci-connector to move your applications')
        c.argument('os_type', get_enum_type(aci_connector_os_type), help='The OS type of the connector')

    with self.argument_context('aks upgrade') as c:
        c.argument('kubernetes_version', completer=get_k8s_upgrades_completion_list)

    with self.argument_context('aks upgrade-connector') as c:
        c.argument('aci_resource_group')
        c.argument('chart_url', default=aci_connector_chart_url)
        c.argument('client_secret')
        c.argument('connector_name', default='aci-connector', validator=validate_connector_name)
        c.argument('image_tag')
        c.argument('location')
        c.argument('os_type', get_enum_type(aci_connector_os_type))
        c.argument('service_principal')

    with self.argument_context('aks use-dev-spaces') as c:
        c.argument('update', options_list=['--update'], action='store_true')
        c.argument('space_name', options_list=['--space', '-s'])
        c.argument('prompt', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation. Requires --space.')

    with self.argument_context('aks remove-dev-spaces') as c:
        c.argument('prompt', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation')


def _get_default_install_location(exe_name):
    system = platform.system()
    if system == 'Windows':
        home_dir = os.environ.get('USERPROFILE')
        if not home_dir:
            return None
        install_location = os.path.join(home_dir, r'.azure-{0}\{0}.exe'.format(exe_name))
    elif system == 'Linux' or system == 'Darwin':
        install_location = '/usr/local/bin/{}'.format(exe_name)
    else:
        install_location = None
    return install_location


def _get_feature_in_preview_message():
    return "Feature in preview, only in " + ", ".join(regions_in_preview) + ". "
