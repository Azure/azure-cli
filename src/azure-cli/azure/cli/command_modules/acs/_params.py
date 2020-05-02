# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-statements,no-name-in-module,import-error

import os.path
import platform

from argcomplete.completers import FilesCompleter
from azure.cli.core.commands.parameters import (
    file_type, get_enum_type, get_resource_name_completion_list, name_type, tags_type, zones_type, get_three_state_flag)
from azure.cli.core.commands.validators import validate_file_or_dict
from knack.arguments import CLIArgumentType

from ._completers import (
    get_vm_size_completion_list, get_k8s_versions_completion_list, get_k8s_upgrades_completion_list)
from ._validators import (
    validate_create_parameters, validate_k8s_client_version, validate_k8s_version, validate_linux_host_name,
    validate_list_of_integers, validate_ssh_key, validate_connector_name, validate_max_pods, validate_nodes_count,
    validate_nodepool_name, validate_vm_set_type, validate_load_balancer_sku, validate_load_balancer_outbound_ips,
    validate_load_balancer_outbound_ip_prefixes, validate_taints, validate_ip_ranges, validate_acr, validate_nodepool_tags,
    validate_load_balancer_outbound_ports, validate_load_balancer_idle_timeout, validate_vnet_subnet_id, validate_nodepool_labels)
from ._consts import CONST_OUTBOUND_TYPE_LOAD_BALANCER, CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING

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
nodepool_mode_type = ["System", "User"]


def load_arguments(self, _):

    acr_arg_type = CLIArgumentType(metavar='ACR_NAME_OR_RESOURCE_ID')

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
        c.argument('master_vm_size', completer=get_vm_size_completion_list,
                   help=_get_feature_in_preview_message())
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
        c.argument('orchestrator_version', help=_get_feature_in_preview_message() + 'Use Orchestrator Version to specify the semantic version for your choice of orchestrator.')

    with self.argument_context('acs scale') as c:
        c.argument('new_agent_count', type=int)

    for scope in ['dcos', 'kubernetes']:
        with self.argument_context('acs {} browse'.format(scope)) as c:
            c.argument('ssh_key_file', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa'),
                       completer=FilesCompleter(), help='Path to an SSH key file to use.')

    with self.argument_context('acs dcos install-cli') as c:
        c.argument('install_location', default=_get_default_install_location('dcos'))

    with self.argument_context('acs kubernetes get-credentials') as c:
        c.argument('path', options_list=['--file', '-f'])
        c.argument('overwrite_existing', action='store_true', help='If specified, overwrite any existing credentials.')

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
        c.argument('nodepool_name', type=str, default='nodepool1',
                   help='Node pool name, up to 12 alphanumeric characters', validator=validate_nodepool_name)
        c.argument('ssh_key_value', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'),
                   completer=FilesCompleter(), validator=validate_ssh_key)
        c.argument('aad_client_app_id')
        c.argument('aad_server_app_id')
        c.argument('aad_server_app_secret')
        c.argument('aad_tenant_id')
        c.argument('dns_service_ip')
        c.argument('docker_bridge_address')
        c.argument('load_balancer_sku', type=str, validator=validate_load_balancer_sku)
        c.argument('load_balancer_managed_outbound_ip_count', type=int)
        c.argument('load_balancer_outbound_ips', type=str, validator=validate_load_balancer_outbound_ips)
        c.argument('load_balancer_outbound_ip_prefixes', type=str, validator=validate_load_balancer_outbound_ip_prefixes)
        c.argument('load_balancer_outbound_ports', type=int, validator=validate_load_balancer_outbound_ports)
        c.argument('load_balancer_idle_timeout', type=int, validator=validate_load_balancer_idle_timeout)
        c.argument('outbound_type', arg_type=get_enum_type([CONST_OUTBOUND_TYPE_LOAD_BALANCER,
                                                            CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING]))
        c.argument('enable_cluster_autoscaler', action='store_true')
        c.argument('min_count', type=int, validator=validate_nodes_count)
        c.argument('max_count', type=int, validator=validate_nodes_count)
        c.argument('vm_set_type', type=str, validator=validate_vm_set_type)
        c.argument('zones', zones_type, options_list=['--zones', '-z'], help='Space-separated list of availability zones where agent nodes will be placed.')
        c.argument('uptime_sla', action='store_true')
        c.argument('enable_addons', options_list=['--enable-addons', '-a'])
        c.argument('disable_rbac', action='store_true')
        c.argument('enable_rbac', action='store_true', options_list=['--enable-rbac', '-r'],
                   deprecate_info=c.deprecate(redirect="--disable-rbac", hide="2.0.45"))
        c.argument('max_pods', type=int, options_list=['--max-pods', '-m'], validator=validate_max_pods)
        c.argument('network_plugin', arg_type=get_enum_type(['azure', 'kubenet']))
        c.argument('network_policy')
        c.argument('no_ssh_key', options_list=['--no-ssh-key', '-x'])
        c.argument('pod_cidr')
        c.argument('service_cidr')
        c.argument('vnet_subnet_id', type=str, validator=validate_vnet_subnet_id)
        c.argument('workspace_resource_id')
        c.argument('skip_subnet_role_assignment', action='store_true')
        c.argument('api_server_authorized_ip_ranges', type=str, validator=validate_ip_ranges)
        c.argument('attach_acr', acr_arg_type)
        c.argument('enable_private_cluster', action='store_true')
        c.argument('nodepool_tags', nargs='*', validator=validate_nodepool_tags, help='space-separated tags: key[=value] [key[=value] ...]. Use "" to clear existing tags.')
        c.argument('enable_managed_identity', action='store_true')
        c.argument('nodepool_labels', nargs='*', validator=validate_nodepool_labels, help='space-separated labels: key[=value] [key[=value] ...]. You can not change the node labels through CLI after creation. See https://aka.ms/node-labels for syntax of labels.')
        c.argument('enable_node_public_ip', action='store_true', is_preview=True)
        c.argument('windows_admin_username', options_list=['--windows-admin-username'])
        c.argument('windows_admin_password', options_list=['--windows-admin-password'])

    with self.argument_context('aks update') as c:
        c.argument('attach_acr', acr_arg_type, validator=validate_acr)
        c.argument('detach_acr', acr_arg_type, validator=validate_acr)

    with self.argument_context('aks update') as c:
        c.argument('enable_cluster_autoscaler', options_list=["--enable-cluster-autoscaler", "-e"], action='store_true')
        c.argument('disable_cluster_autoscaler', options_list=["--disable-cluster-autoscaler", "-d"], action='store_true')
        c.argument('update_cluster_autoscaler', options_list=["--update-cluster-autoscaler", "-u"], action='store_true')
        c.argument('min_count', type=int, validator=validate_nodes_count)
        c.argument('max_count', type=int, validator=validate_nodes_count)
        c.argument('load_balancer_managed_outbound_ip_count', type=int)
        c.argument('load_balancer_outbound_ips', type=str, validator=validate_load_balancer_outbound_ips)
        c.argument('load_balancer_outbound_ip_prefixes', type=str, validator=validate_load_balancer_outbound_ip_prefixes)
        c.argument('load_balancer_outbound_ports', type=int, validator=validate_load_balancer_outbound_ports)
        c.argument('load_balancer_idle_timeout', type=int, validator=validate_load_balancer_idle_timeout)
        c.argument('api_server_authorized_ip_ranges', type=str, validator=validate_ip_ranges)

    with self.argument_context('aks disable-addons') as c:
        c.argument('addons', options_list=['--addons', '-a'])

    with self.argument_context('aks enable-addons') as c:
        c.argument('addons', options_list=['--addons', '-a'])
        c.argument('subnet_name', options_list=['--subnet-name', '-s'], help='Name of an existing subnet to use with the virtual-node add-on.')

    with self.argument_context('aks get-credentials') as c:
        c.argument('admin', options_list=['--admin', '-a'], default=False)
        c.argument('context_name', options_list=['--context'],
                   help='If specified, overwrite the default context name.')
        c.argument('path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   default=os.path.join(os.path.expanduser('~'), '.kube', 'config'))

    for scope in ['aks', 'acs kubernetes', 'acs dcos']:
        with self.argument_context('{} install-cli'.format(scope)) as c:
            c.argument('client_version', validator=validate_k8s_client_version, help='Version of the client to install.')
            c.argument('install_location', default=_get_default_install_location('kubectl'), help='Path at which to install kubectl.')

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
        c.argument('connector_name', default='aci-connector',
                   help='The name for the ACI Connector', validator=validate_connector_name)
        c.argument('graceful', action='store_true',
                   help='Mention if you want to drain/uncordon your aci-connector to move your applications')
        c.argument('os_type', get_enum_type(aci_connector_os_type),
                   help='The OS type of the connector')

    with self.argument_context('aks update-credentials', arg_group='Service Principal') as c:
        c.argument('reset_service_principal', action='store_true')
        c.argument('service_principal')
        c.argument('client_secret')

    with self.argument_context('aks update-credentials', arg_group='AAD') as c:
        c.argument('reset_aad', action='store_true')
        c.argument('aad_client_app_id')
        c.argument('aad_server_app_id')
        c.argument('aad_server_app_secret')
        c.argument('aad_tenant_id')

    with self.argument_context('aks upgrade') as c:
        c.argument('kubernetes_version', completer=get_k8s_upgrades_completion_list)

    with self.argument_context('aks scale') as c:
        c.argument('nodepool_name', type=str,
                   help='Node pool name, up to 12 alphanumeric characters', validator=validate_nodepool_name)

    with self.argument_context('aks nodepool') as c:
        c.argument('cluster_name', type=str, help='The cluster name.')

    for scope in ['aks nodepool add']:
        with self.argument_context(scope) as c:
            c.argument('nodepool_name', type=str, options_list=['--name', '-n'], validator=validate_nodepool_name, help='The node pool name.')
            c.argument('zones', zones_type, options_list=['--zones', '-z'], help='Space-separated list of availability zones where agent nodes will be placed.')
            c.argument('node_vm_size', options_list=['--node-vm-size', '-s'], completer=get_vm_size_completion_list)
            c.argument('max_pods', type=int, options_list=['--max-pods', '-m'], validator=validate_max_pods)
            c.argument('os_type', type=str)
            c.argument('enable_cluster_autoscaler', options_list=["--enable-cluster-autoscaler", "-e"], action='store_true')
            c.argument('node_taints', type=str, validator=validate_taints)
            c.argument('tags', tags_type)
            c.argument('labels', nargs='*', validator=validate_nodepool_labels)
            c.argument('mode', get_enum_type(nodepool_mode_type))
            c.argument('enable_node_public_ip', action='store_true', is_preview=True)

    for scope in ['aks nodepool show', 'aks nodepool delete', 'aks nodepool scale', 'aks nodepool upgrade', 'aks nodepool update']:
        with self.argument_context(scope) as c:
            c.argument('nodepool_name', type=str, options_list=['--name', '-n'], validator=validate_nodepool_name, help='The node pool name.')

    with self.argument_context('aks nodepool update') as c:
        c.argument('enable_cluster_autoscaler', options_list=["--enable-cluster-autoscaler", "-e"], action='store_true')
        c.argument('disable_cluster_autoscaler', options_list=["--disable-cluster-autoscaler", "-d"], action='store_true')
        c.argument('update_cluster_autoscaler', options_list=["--update-cluster-autoscaler", "-u"], action='store_true')
        c.argument('tags', tags_type)
        c.argument('mode', get_enum_type(nodepool_mode_type))

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
        c.argument('endpoint_type', get_enum_type(['Public', 'Private', 'None'], default='Public'), options_list=['--endpoint', '-e'])
        c.argument('prompt', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation. Requires --space.')

    with self.argument_context('aks remove-dev-spaces') as c:
        c.argument('prompt', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation')

    # OpenShift command argument configuration
    with self.argument_context('openshift') as c:
        c.argument('resource_name', name_type, help='Name of the managed OpenShift cluster.',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/OpenShiftManagedClusters'))
        c.argument('name', name_type, help='Name of the managed OpenShift cluster.',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/OpenShiftManagedClusters'))
        c.argument('compute_count', options_list=['--compute-count', '-c'], type=int, default=4)
        c.argument('tags', tags_type)

    with self.argument_context('openshift create') as c:
        c.argument('name', validator=validate_linux_host_name)
        c.argument('aad_client_app_id', help='The ID of an Azure Active Directory client application. If not specified, a new Azure Active Directory client is created.')
        c.argument('aad_client_app_secret', help='The secret of an Azure Active Directory client application.')
        c.argument('aad_tenant_id', help='The ID of an Azure Active Directory tenant.')
        c.argument('compute_count', options_list=['--compute-count', '-c'], help='Number of nodes in the OpenShift node pool.')
        c.argument('compute_vm_size', options_list=['--compute-vm-size', '-s'], help='Size of Virtual Machines to create as OpenShift nodes.')
        c.argument('customer_admin_group_id',
                   help='The Object ID of an Azure Active Directory Group that memberships will get synced into the OpenShift group "osa-customer-admins".'
                        'If not specified, no cluster admin access will be granted.')
        c.argument('management_subnet_cidr', help='CIDR of subnet used to create PLS needed for management of the cluster. If provided, also set --private-cluster flag.')
        c.argument('private_cluster', arg_type=get_three_state_flag(), help='Create private Openshift cluster. If this flag is set, also supply --management-subnet-cidr.')
        c.argument('subnet_prefix', help='The CIDR used on the Subnet into which to deploy the cluster.')
        c.argument('vnet_peer',
                   help='Vnet peering is no longer supported during cluster creation, instead it is possible to edit vnet properties after cluster creation')
        c.argument('vnet_prefix', help='The CIDR used on the VNet into which to deploy the cluster.')
        c.argument('workspace_id', help='The resource id of an existing Log Analytics Workspace to use for storing monitoring data.')

    with self.argument_context('openshift update') as c:
        c.argument('refresh_cluster', arg_type=get_three_state_flag(),
                   help='Allow nodes to be rotated. Use this flag to trigger nodes rotation after DNS settings change.')

    with self.argument_context('openshift monitor enable') as c:
        c.argument('workspace_id', help='The resource ID of an existing Log Analytics Workspace to use for storing monitoring data.')


def _get_default_install_location(exe_name):
    system = platform.system()
    if system == 'Windows':
        home_dir = os.environ.get('USERPROFILE')
        if not home_dir:
            return None
        install_location = os.path.join(home_dir, r'.azure-{0}\{0}.exe'.format(exe_name))
    elif system in ('Linux', 'Darwin'):
        install_location = '/usr/local/bin/{}'.format(exe_name)
    else:
        install_location = None
    return install_location


def _get_feature_in_preview_message():
    return "Feature in preview, only in " + ", ".join(regions_in_preview) + ". "
