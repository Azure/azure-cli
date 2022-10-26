# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
import platform

from argcomplete.completers import FilesCompleter
from azure.cli.command_modules.acs._completers import (
    get_k8s_upgrades_completion_list, get_k8s_versions_completion_list,
    get_vm_size_completion_list)
from azure.cli.command_modules.acs._consts import (
    CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE,
    CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PUBLIC,
    CONST_GPU_INSTANCE_PROFILE_MIG1_G, CONST_GPU_INSTANCE_PROFILE_MIG2_G,
    CONST_GPU_INSTANCE_PROFILE_MIG3_G, CONST_GPU_INSTANCE_PROFILE_MIG4_G,
    CONST_GPU_INSTANCE_PROFILE_MIG7_G, CONST_LOAD_BALANCER_SKU_BASIC,
    CONST_LOAD_BALANCER_SKU_STANDARD, CONST_NETWORK_PLUGIN_AZURE,
    CONST_NETWORK_PLUGIN_KUBENET, CONST_NETWORK_PLUGIN_NONE,
    CONST_NODE_IMAGE_UPGRADE_CHANNEL, CONST_NODEPOOL_MODE_SYSTEM,
    CONST_NODEPOOL_MODE_USER, CONST_NONE_UPGRADE_CHANNEL,
    CONST_OS_DISK_TYPE_EPHEMERAL, CONST_OS_DISK_TYPE_MANAGED,
    CONST_OS_SKU_CBLMARINER, CONST_OS_SKU_UBUNTU, CONST_OS_SKU_WINDOWS2019,
    CONST_OS_SKU_WINDOWS2022, CONST_OUTBOUND_TYPE_LOAD_BALANCER,
    CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY,
    CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY,
    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING, CONST_PATCH_UPGRADE_CHANNEL,
    CONST_RAPID_UPGRADE_CHANNEL, CONST_SCALE_DOWN_MODE_DEALLOCATE,
    CONST_SCALE_DOWN_MODE_DELETE, CONST_SCALE_SET_PRIORITY_REGULAR,
    CONST_SCALE_SET_PRIORITY_SPOT, CONST_SPOT_EVICTION_POLICY_DEALLOCATE,
    CONST_SPOT_EVICTION_POLICY_DELETE, CONST_STABLE_UPGRADE_CHANNEL)
from azure.cli.command_modules.acs._validators import (
    validate_acr, validate_agent_pool_name, validate_assign_identity,
    validate_assign_kubelet_identity, validate_azure_keyvault_kms_key_id,
    validate_azure_keyvault_kms_key_vault_resource_id,
    validate_create_parameters, validate_credential_format,
    validate_defender_config_parameter,
    validate_defender_disable_and_enable_parameters, validate_eviction_policy,
    validate_host_group_id, validate_ip_ranges, validate_k8s_version,
    validate_keyvault_secrets_provider_disable_and_enable_parameters,
    validate_kubectl_version, validate_kubelogin_version,
    validate_linux_host_name, validate_load_balancer_idle_timeout,
    validate_load_balancer_outbound_ip_prefixes,
    validate_load_balancer_outbound_ips, validate_load_balancer_outbound_ports,
    validate_load_balancer_sku, validate_max_surge,
    validate_nat_gateway_idle_timeout,
    validate_nat_gateway_managed_outbound_ip_count, validate_network_policy,
    validate_nodepool_id, validate_nodepool_labels, validate_nodepool_name,
    validate_nodepool_tags, validate_nodes_count, validate_pod_subnet_id,
    validate_ppg, validate_priority, validate_registry_name,
    validate_snapshot_id, validate_snapshot_name, validate_spot_max_price,
    validate_ssh_key, validate_taints, validate_vm_set_type,
    validate_vnet_subnet_id)
from azure.cli.core.commands.parameters import (
    edge_zone_type, file_type, get_enum_type,
    get_resource_name_completion_list, get_three_state_flag, name_type,
    tags_type, zones_type)
from azure.cli.core.profiles import ResourceType
from knack.arguments import CLIArgumentType

# pylint: disable=line-too-long,too-many-statements

# candidates for enumeration, no longer maintained
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

# candidates for enumeration, under support
# consts for AgentPool
node_priorities = [CONST_SCALE_SET_PRIORITY_REGULAR, CONST_SCALE_SET_PRIORITY_SPOT]
node_eviction_policies = [CONST_SPOT_EVICTION_POLICY_DELETE, CONST_SPOT_EVICTION_POLICY_DEALLOCATE]
node_os_disk_types = [CONST_OS_DISK_TYPE_MANAGED, CONST_OS_DISK_TYPE_EPHEMERAL]
node_mode_types = [CONST_NODEPOOL_MODE_SYSTEM, CONST_NODEPOOL_MODE_USER]
node_os_skus = [CONST_OS_SKU_UBUNTU, CONST_OS_SKU_CBLMARINER, CONST_OS_SKU_WINDOWS2019, CONST_OS_SKU_WINDOWS2022]
scale_down_modes = [CONST_SCALE_DOWN_MODE_DELETE, CONST_SCALE_DOWN_MODE_DEALLOCATE]

# consts for ManagedCluster
load_balancer_skus = [CONST_LOAD_BALANCER_SKU_BASIC, CONST_LOAD_BALANCER_SKU_STANDARD]
network_plugins = [CONST_NETWORK_PLUGIN_KUBENET, CONST_NETWORK_PLUGIN_AZURE, CONST_NETWORK_PLUGIN_NONE]
outbound_types = [CONST_OUTBOUND_TYPE_LOAD_BALANCER, CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING, CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY, CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY]
auto_upgrade_channels = [
    CONST_RAPID_UPGRADE_CHANNEL,
    CONST_STABLE_UPGRADE_CHANNEL,
    CONST_PATCH_UPGRADE_CHANNEL,
    CONST_NODE_IMAGE_UPGRADE_CHANNEL,
    CONST_NONE_UPGRADE_CHANNEL,
]

dev_space_endpoint_types = ['Public', 'Private', 'None']

keyvault_network_access_types = [CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PUBLIC, CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE]

gpu_instance_profiles = [
    CONST_GPU_INSTANCE_PROFILE_MIG1_G,
    CONST_GPU_INSTANCE_PROFILE_MIG2_G,
    CONST_GPU_INSTANCE_PROFILE_MIG3_G,
    CONST_GPU_INSTANCE_PROFILE_MIG4_G,
    CONST_GPU_INSTANCE_PROFILE_MIG7_G,
]


def load_arguments(self, _):

    acr_arg_type = CLIArgumentType(metavar='ACR_NAME_OR_RESOURCE_ID')

    # AKS command argument configuration
    with self.argument_context('aks', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('resource_name', name_type, help='Name of the managed cluster.',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ManagedClusters'))
        c.argument('name', name_type, help='Name of the managed cluster.',
                   completer=get_resource_name_completion_list('Microsoft.ContainerService/ManagedClusters'))
        c.argument('kubernetes_version', options_list=[
                   '--kubernetes-version', '-k'], validator=validate_k8s_version)
        c.argument('node_count', type=int, options_list=['--node-count', '-c'])
        c.argument('tags', tags_type)

    with self.argument_context('aks create', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        # managed cluster paramerters
        c.argument('name', validator=validate_linux_host_name)
        c.argument('kubernetes_version',
                   completer=get_k8s_versions_completion_list)
        c.argument('dns_name_prefix', options_list=['--dns-name-prefix', '-p'])
        c.argument('node_osdisk_diskencryptionset_id', options_list=['--node-osdisk-diskencryptionset-id', '-d'])
        c.argument('disable_local_accounts', action='store_true')
        c.argument('disable_rbac', action='store_true')
        c.argument('edge_zone', edge_zone_type)
        c.argument('admin_username', options_list=['--admin-username', '-u'], default='azureuser')
        c.argument('generate_ssh_keys', action='store_true', validator=validate_create_parameters)
        c.argument('ssh_key_value', required=False, type=file_type, default=os.path.join('~', '.ssh', 'id_rsa.pub'),
                   completer=FilesCompleter(), validator=validate_ssh_key)
        c.argument('no_ssh_key', options_list=['--no-ssh-key', '-x'])
        c.argument('dns_service_ip')
        c.argument('docker_bridge_address')
        c.argument('pod_cidr')
        c.argument('service_cidr')
        c.argument('load_balancer_sku', arg_type=get_enum_type(load_balancer_skus), validator=validate_load_balancer_sku)
        c.argument('load_balancer_managed_outbound_ip_count', type=int)
        c.argument('load_balancer_outbound_ips', validator=validate_load_balancer_outbound_ips)
        c.argument('load_balancer_outbound_ip_prefixes', validator=validate_load_balancer_outbound_ip_prefixes)
        c.argument('load_balancer_outbound_ports', type=int, validator=validate_load_balancer_outbound_ports)
        c.argument('load_balancer_idle_timeout', type=int, validator=validate_load_balancer_idle_timeout)
        c.argument('nat_gateway_managed_outbound_ip_count', type=int, validator=validate_nat_gateway_managed_outbound_ip_count)
        c.argument('nat_gateway_idle_timeout', type=int, validator=validate_nat_gateway_idle_timeout)
        c.argument('outbound_type', arg_type=get_enum_type(outbound_types))
        c.argument('network_plugin', arg_type=get_enum_type(network_plugins))
        c.argument('network_policy', validator=validate_network_policy)
        c.argument('auto_upgrade_channel', arg_type=get_enum_type(auto_upgrade_channels))
        c.argument('cluster_autoscaler_profile', nargs='+', options_list=["--cluster-autoscaler-profile", "--ca-profile"],
                   help="Space-separated list of key=value pairs for configuring cluster autoscaler. Pass an empty string to clear the profile.")
        c.argument('uptime_sla', action='store_true')
        c.argument('fqdn_subdomain')
        c.argument('api_server_authorized_ip_ranges', validator=validate_ip_ranges)
        c.argument('enable_private_cluster', action='store_true')
        c.argument('private_dns_zone')
        c.argument('disable_public_fqdn', action='store_true')
        c.argument('service_principal')
        c.argument('client_secret')
        c.argument('enable_managed_identity', action='store_true')
        c.argument('assign_identity', validator=validate_assign_identity)
        c.argument('assign_kubelet_identity', validator=validate_assign_kubelet_identity)
        c.argument('enable_aad', action='store_true')
        c.argument('enable_azure_rbac', action='store_true')
        c.argument('aad_client_app_id')
        c.argument('aad_server_app_id')
        c.argument('aad_server_app_secret')
        c.argument('aad_tenant_id')
        c.argument('aad_admin_group_object_ids')
        c.argument('enable_oidc_issuer', action='store_true')
        c.argument('windows_admin_username')
        c.argument('windows_admin_password')
        c.argument('enable_ahub', action='store_true')
        c.argument('enable_windows_gmsa', action='store_true')
        c.argument('gmsa_dns_server')
        c.argument('gmsa_root_domain_name')
        c.argument('attach_acr', acr_arg_type)
        c.argument('skip_subnet_role_assignment', action='store_true')
        c.argument('node_resource_group')
        c.argument('enable_defender', action='store_true')
        c.argument('defender_config', validator=validate_defender_config_parameter)
        c.argument('disable_disk_driver', action='store_true')
        c.argument('disable_file_driver', action='store_true')
        c.argument('enable_blob_driver', action='store_true')
        c.argument('disable_snapshot_controller', action='store_true')
        c.argument('enable_azure_keyvault_kms', action='store_true')
        c.argument('azure_keyvault_kms_key_id', validator=validate_azure_keyvault_kms_key_id)
        c.argument('azure_keyvault_kms_key_vault_network_access', arg_type=get_enum_type(keyvault_network_access_types))
        c.argument('azure_keyvault_kms_key_vault_resource_id', validator=validate_azure_keyvault_kms_key_vault_resource_id)
        # addons
        c.argument('enable_addons', options_list=['--enable-addons', '-a'])
        c.argument('workspace_resource_id')
        c.argument('enable_msi_auth_for_monitoring', arg_type=get_three_state_flag(), is_preview=True)
        c.argument('aci_subnet_name')
        c.argument('appgw_name', arg_group='Application Gateway')
        c.argument('appgw_subnet_cidr', arg_group='Application Gateway')
        c.argument('appgw_id', arg_group='Application Gateway')
        c.argument('appgw_subnet_id', arg_group='Application Gateway')
        c.argument('appgw_watch_namespace', arg_group='Application Gateway')
        c.argument('enable_secret_rotation', action='store_true')
        c.argument('rotation_poll_interval')
        c.argument('enable_sgxquotehelper', action='store_true')
        # nodepool paramerters
        c.argument('nodepool_name', default='nodepool1',
                   help='Node pool name, up to 12 alphanumeric characters', validator=validate_nodepool_name)
        c.argument('node_vm_size', options_list=['--node-vm-size', '-s'], completer=get_vm_size_completion_list)
        c.argument('os_sku', arg_type=get_enum_type(node_os_skus))
        c.argument('snapshot_id', validator=validate_snapshot_id)
        c.argument('vnet_subnet_id', validator=validate_vnet_subnet_id)
        c.argument('pod_subnet_id', validator=validate_pod_subnet_id)
        c.argument('enable_node_public_ip', action='store_true')
        c.argument('node_public_ip_prefix_id')
        c.argument('enable_cluster_autoscaler', action='store_true')
        c.argument('min_count', type=int, validator=validate_nodes_count)
        c.argument('max_count', type=int, validator=validate_nodes_count)
        c.argument('nodepool_tags', nargs='*', validator=validate_nodepool_tags,
                   help='space-separated tags: key[=value] [key[=value] ...]. Use "" to clear existing tags.')
        c.argument('nodepool_labels', nargs='*', validator=validate_nodepool_labels,
                   help='space-separated labels: key[=value] [key[=value] ...]. See https://aka.ms/node-labels for syntax of labels.')
        c.argument('node_osdisk_type', arg_type=get_enum_type(node_os_disk_types))
        c.argument('node_osdisk_size', type=int)
        c.argument('max_pods', type=int, options_list=['--max-pods', '-m'])
        c.argument('vm_set_type', validator=validate_vm_set_type)
        c.argument('zones', zones_type, options_list=['--zones', '-z'], help='Space-separated list of availability zones where agent nodes will be placed.')
        c.argument('ppg', validator=validate_ppg)
        c.argument('enable_encryption_at_host', action='store_true')
        c.argument('enable_ultra_ssd', action='store_true')
        c.argument('enable_fips_image', action='store_true')
        c.argument('kubelet_config')
        c.argument('linux_os_config')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')
        c.argument('host_group_id', validator=validate_host_group_id)
        c.argument('http_proxy_config')
        c.argument('gpu_instance_profile', arg_type=get_enum_type(gpu_instance_profiles))

    with self.argument_context('aks update') as c:
        # managed cluster paramerters
        c.argument('disable_local_accounts', action='store_true')
        c.argument('enable_local_accounts', action='store_true')
        c.argument('load_balancer_managed_outbound_ip_count', type=int)
        c.argument('load_balancer_outbound_ips', validator=validate_load_balancer_outbound_ips)
        c.argument('load_balancer_outbound_ip_prefixes', validator=validate_load_balancer_outbound_ip_prefixes)
        c.argument('load_balancer_outbound_ports', type=int, validator=validate_load_balancer_outbound_ports)
        c.argument('load_balancer_idle_timeout', type=int, validator=validate_load_balancer_idle_timeout)
        c.argument('nat_gateway_managed_outbound_ip_count', type=int, validator=validate_nat_gateway_managed_outbound_ip_count)
        c.argument('nat_gateway_idle_timeout', type=int, validator=validate_nat_gateway_idle_timeout)
        c.argument('auto_upgrade_channel', arg_type=get_enum_type(auto_upgrade_channels))
        c.argument('cluster_autoscaler_profile', nargs='+', options_list=["--cluster-autoscaler-profile", "--ca-profile"],
                   help="Space-separated list of key=value pairs for configuring cluster autoscaler. Pass an empty string to clear the profile.")
        c.argument('uptime_sla', action='store_true')
        c.argument('no_uptime_sla', action='store_true')
        c.argument('api_server_authorized_ip_ranges', validator=validate_ip_ranges)
        c.argument('enable_public_fqdn', action='store_true')
        c.argument('disable_public_fqdn', action='store_true')
        c.argument('enable_managed_identity', action='store_true')
        c.argument('assign_identity', validator=validate_assign_identity)
        c.argument('assign_kubelet_identity', validator=validate_assign_kubelet_identity)
        c.argument('enable_aad', action='store_true')
        c.argument('enable_azure_rbac', action='store_true')
        c.argument('disable_azure_rbac', action='store_true')
        c.argument('aad_tenant_id')
        c.argument('aad_admin_group_object_ids')
        c.argument('windows_admin_password')
        c.argument('enable_oidc_issuer', action='store_true')
        c.argument('enable_ahub', action='store_true')
        c.argument('disable_ahub', action='store_true')
        c.argument('enable_windows_gmsa', action='store_true')
        c.argument('gmsa_dns_server')
        c.argument('gmsa_root_domain_name')
        c.argument('attach_acr', acr_arg_type, validator=validate_acr)
        c.argument('detach_acr', acr_arg_type, validator=validate_acr)
        c.argument('enable_disk_driver', action='store_true')
        c.argument('disable_disk_driver', action='store_true')
        c.argument('enable_file_driver', action='store_true')
        c.argument('disable_file_driver', action='store_true')
        c.argument('enable_blob_driver', action='store_true')
        c.argument('disable_blob_driver', action='store_true')
        c.argument('enable_snapshot_controller', action='store_true')
        c.argument('disable_snapshot_controller', action='store_true')
        c.argument('disable_defender', action='store_true', validator=validate_defender_disable_and_enable_parameters)
        c.argument('enable_defender', action='store_true')
        c.argument('defender_config', validator=validate_defender_config_parameter)
        c.argument('enable_azure_keyvault_kms', action='store_true')
        c.argument('disable_azure_keyvault_kms', action='store_true')
        c.argument('azure_keyvault_kms_key_id', validator=validate_azure_keyvault_kms_key_id)
        c.argument('azure_keyvault_kms_key_vault_network_access', arg_type=get_enum_type(keyvault_network_access_types))
        c.argument('azure_keyvault_kms_key_vault_resource_id', validator=validate_azure_keyvault_kms_key_vault_resource_id)
        # addons
        c.argument('enable_secret_rotation', action='store_true')
        c.argument('disable_secret_rotation', action='store_true', validator=validate_keyvault_secrets_provider_disable_and_enable_parameters)
        c.argument('rotation_poll_interval')
        # nodepool paramerters
        c.argument('enable_cluster_autoscaler', options_list=[
                   "--enable-cluster-autoscaler", "-e"], action='store_true')
        c.argument('disable_cluster_autoscaler', options_list=[
                   "--disable-cluster-autoscaler", "-d"], action='store_true')
        c.argument('update_cluster_autoscaler', options_list=[
                   "--update-cluster-autoscaler", "-u"], action='store_true')
        c.argument('min_count', type=int, validator=validate_nodes_count)
        c.argument('max_count', type=int, validator=validate_nodes_count)
        c.argument('http_proxy_config')
        c.argument('nodepool_labels', nargs='*', validator=validate_nodepool_labels,
                   help='space-separated labels: key[=value] [key[=value] ...]. See https://aka.ms/node-labels for syntax of labels.')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')

    with self.argument_context('aks disable-addons', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('addons', options_list=['--addons', '-a'])

    with self.argument_context('aks enable-addons', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('addons', options_list=['--addons', '-a'])
        c.argument('subnet_name', options_list=[
                   '--subnet-name', '-s'], help='Name of an existing subnet to use with the virtual-node add-on.')
        c.argument('appgw_name', arg_group='Application Gateway')
        c.argument('appgw_subnet_cidr', arg_group='Application Gateway')
        c.argument('appgw_id', arg_group='Application Gateway')
        c.argument('appgw_subnet_id', arg_group='Application Gateway')
        c.argument('appgw_watch_namespace', arg_group='Application Gateway')
        c.argument('enable_sgxquotehelper', action='store_true')
        c.argument('enable_secret_rotation', action='store_true')
        c.argument('rotation_poll_interval')

    with self.argument_context('aks get-credentials', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('admin', options_list=['--admin', '-a'], default=False)
        c.argument('context_name', options_list=['--context'],
                   help='If specified, overwrite the default context name. The `--admin` parameter takes precedence over `--context`')
        c.argument('path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   default=os.path.join(os.path.expanduser('~'), '.kube', 'config'))
        c.argument('public_fqdn', default=False, action='store_true')
        c.argument('credential_format', options_list=['--format'], validator=validate_credential_format)

    with self.argument_context('aks install-cli') as c:
        c.argument('client_version', validator=validate_kubectl_version, help='Version of kubectl to install.')
        c.argument('install_location', default=_get_default_install_location('kubectl'), help='Path at which to install kubectl.')
        c.argument('base_src_url', help='Base download source URL for kubectl releases.')
        c.argument('kubelogin_version', validator=validate_kubelogin_version, help='Version of kubelogin to install.')
        c.argument('kubelogin_install_location', default=_get_default_install_location('kubelogin'), help='Path at which to install kubelogin.')
        c.argument('kubelogin_base_src_url', options_list=['--kubelogin-base-src-url', '-l'], help='Base download source URL for kubelogin releases.')

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

    with self.argument_context('aks upgrade', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('kubernetes_version', completer=get_k8s_upgrades_completion_list)
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')

    with self.argument_context('aks scale', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('nodepool_name', validator=validate_nodepool_name, help='Node pool name, up to 12 alphanumeric characters.')

    with self.argument_context('aks check-acr', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('acr', validator=validate_registry_name)
        c.argument('node_name')

    with self.argument_context('aks nodepool', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='managed_clusters') as c:
        c.argument('cluster_name', help='The cluster name.')
        # the following argument is declared for the wait command
        c.argument('agent_pool_name', options_list=['--nodepool-name', '--agent-pool-name'], validator=validate_agent_pool_name, help='The node pool name.')

    for sub_command in ['add', 'update', 'upgrade', 'scale', 'show', 'list', 'delete']:
        with self.argument_context('aks nodepool ' + sub_command) as c:
            c.argument('nodepool_name', options_list=['--nodepool-name', '--name', '-n'], validator=validate_nodepool_name, help='The node pool name.')

    with self.argument_context('aks nodepool add') as c:
        c.argument('node_vm_size', options_list=['--node-vm-size', '-s'], completer=get_vm_size_completion_list)
        c.argument('os_type')
        c.argument('os_sku', arg_type=get_enum_type(node_os_skus))
        c.argument('snapshot_id', validator=validate_snapshot_id)
        c.argument('vnet_subnet_id', validator=validate_vnet_subnet_id)
        c.argument('pod_subnet_id', validator=validate_pod_subnet_id)
        c.argument('enable_node_public_ip', action='store_true')
        c.argument('node_public_ip_prefix_id')
        c.argument('enable_cluster_autoscaler', options_list=["--enable-cluster-autoscaler", "-e"], action='store_true')
        c.argument('min_count', type=int, validator=validate_nodes_count)
        c.argument('max_count', type=int, validator=validate_nodes_count)
        c.argument('priority', arg_type=get_enum_type(node_priorities), validator=validate_priority)
        c.argument('eviction_policy', arg_type=get_enum_type(node_eviction_policies), validator=validate_eviction_policy)
        c.argument('spot_max_price', type=float, validator=validate_spot_max_price)
        c.argument('labels', nargs='*', validator=validate_nodepool_labels)
        c.argument('tags', tags_type)
        c.argument('node_taints', validator=validate_taints)
        c.argument('node_osdisk_type', arg_type=get_enum_type(node_os_disk_types))
        c.argument('node_osdisk_size', type=int)
        c.argument('max_surge', validator=validate_max_surge)
        c.argument('mode', get_enum_type(node_mode_types))
        c.argument('scale_down_mode', arg_type=get_enum_type(scale_down_modes))
        c.argument('max_pods', type=int, options_list=['--max-pods', '-m'])
        c.argument('zones', zones_type, options_list=['--zones', '-z'], help='Space-separated list of availability zones where agent nodes will be placed.')
        c.argument('ppg', validator=validate_ppg)
        c.argument('enable_encryption_at_host', action='store_true')
        c.argument('enable_ultra_ssd', action='store_true')
        c.argument('enable_fips_image', action='store_true')
        c.argument('kubelet_config')
        c.argument('linux_os_config')
        c.argument('host_group_id', validator=validate_host_group_id)
        c.argument('gpu_instance_profile', arg_type=get_enum_type(gpu_instance_profiles))

    with self.argument_context('aks nodepool update', resource_type=ResourceType.MGMT_CONTAINERSERVICE, operation_group='agent_pools') as c:
        c.argument('enable_cluster_autoscaler', options_list=[
                   "--enable-cluster-autoscaler", "-e"], action='store_true')
        c.argument('disable_cluster_autoscaler', options_list=[
                   "--disable-cluster-autoscaler", "-d"], action='store_true')
        c.argument('update_cluster_autoscaler', options_list=[
                   "--update-cluster-autoscaler", "-u"], action='store_true')
        c.argument('min_count', type=int, validator=validate_nodes_count)
        c.argument('max_count', type=int, validator=validate_nodes_count)
        c.argument('labels', nargs='*', validator=validate_nodepool_labels)
        c.argument('tags', tags_type)
        c.argument('node_taints', validator=validate_taints)
        c.argument('max_surge', validator=validate_max_surge)
        c.argument('mode', get_enum_type(node_mode_types))
        c.argument('scale_down_mode', arg_type=get_enum_type(scale_down_modes))

    with self.argument_context('aks nodepool upgrade') as c:
        c.argument('snapshot_id', validator=validate_snapshot_id)

    with self.argument_context('aks command invoke') as c:
        c.argument('command_string', options_list=[
                   "--command", "-c"], help='the command to run')
        c.argument('command_files', options_list=["--file", "-f"], required=False, action="append",
                   help='attach any files the command may use, or use \'.\' to upload the current folder.')

    with self.argument_context('aks command result') as c:
        c.argument('command_id', options_list=[
                   "--command-id", "-i"], help='the command ID from "aks command invoke"')

    with self.argument_context('aks use-dev-spaces') as c:
        c.argument('update', options_list=['--update'], action='store_true')
        c.argument('space_name', options_list=['--space', '-s'])
        c.argument('endpoint_type', get_enum_type(dev_space_endpoint_types, default='Public'), options_list=['--endpoint', '-e'])
        c.argument('prompt', options_list=[
                   '--yes', '-y'], action='store_true', help='Do not prompt for confirmation. Requires --space.')

    with self.argument_context('aks remove-dev-spaces') as c:
        c.argument('prompt', options_list=[
                   '--yes', '-y'], action='store_true', help='Do not prompt for confirmation')

    for scope in ['aks nodepool snapshot create', 'aks snapshot create']:
        with self.argument_context(scope) as c:
            c.argument('snapshot_name', options_list=['--name', '-n'], required=True, validator=validate_snapshot_name, help='The nodepool snapshot name.')
            c.argument('tags', tags_type)
            c.argument('nodepool_id', required=True, validator=validate_nodepool_id, help='The nodepool id.')
            c.argument('aks_custom_headers')

    for scope in ['aks nodepool snapshot show', 'aks nodepool snapshot delete', 'aks snapshot show', 'aks snapshot delete']:
        with self.argument_context(scope) as c:
            c.argument('snapshot_name', options_list=['--name', '-n'], required=True, validator=validate_snapshot_name, help='The nodepool snapshot name.')
            c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')


def _get_default_install_location(exe_name):
    system = platform.system()
    if system == 'Windows':
        home_dir = os.environ.get('USERPROFILE')
        if not home_dir:
            return None
        install_location = os.path.join(
            home_dir, r'.azure-{0}\{0}.exe'.format(exe_name))
    elif system in ('Linux', 'Darwin'):
        install_location = '/usr/local/bin/{}'.format(exe_name)
    else:
        install_location = None
    return install_location
