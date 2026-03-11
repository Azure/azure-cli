# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum

# consts for AgentPool
# priority
CONST_SCALE_SET_PRIORITY_REGULAR = "Regular"
CONST_SCALE_SET_PRIORITY_SPOT = "Spot"

# eviction policy
CONST_SPOT_EVICTION_POLICY_DELETE = "Delete"
CONST_SPOT_EVICTION_POLICY_DEALLOCATE = "Deallocate"

# Scale Down Mode
CONST_SCALE_DOWN_MODE_DELETE = "Delete"
CONST_SCALE_DOWN_MODE_DEALLOCATE = "Deallocate"

# os disk type
CONST_OS_DISK_TYPE_MANAGED = "Managed"
CONST_OS_DISK_TYPE_EPHEMERAL = "Ephemeral"

# mode
CONST_NODEPOOL_MODE_SYSTEM = "System"
CONST_NODEPOOL_MODE_USER = "User"
CONST_NODEPOOL_MODE_GATEWAY = "Gateway"

# os type
CONST_DEFAULT_NODE_OS_TYPE = "Linux"

# os sku
CONST_OS_SKU_UBUNTU = "Ubuntu"
CONST_OS_SKU_CBLMARINER = "CBLMariner"
CONST_OS_SKU_MARINER = "Mariner"
CONST_OS_SKU_WINDOWS2019 = "Windows2019"
CONST_OS_SKU_WINDOWS2022 = "Windows2022"
CONST_OS_SKU_AZURELINUX = "AzureLinux"
CONST_OS_SKU_AZURELINUX3 = "AzureLinux3"
CONST_OS_SKU_UBUNTU2204 = "Ubuntu2204"
CONST_OS_SKU_UBUNTU2404 = "Ubuntu2404"

# vm set type
CONST_VIRTUAL_MACHINE_SCALE_SETS = "VirtualMachineScaleSets"
CONST_AVAILABILITY_SET = "AvailabilitySet"
CONST_VIRTUAL_MACHINES = "VirtualMachines"

# vm size
CONST_DEFAULT_NODE_VM_SIZE = ""
CONST_DEFAULT_WINDOWS_NODE_VM_SIZE = ""

CONST_DEFAULT_VMS_VM_SIZE = "Standard_DS2_v2"
CONST_DEFAULT_WINDOWS_VMS_VM_SIZE = "Standard_D2s_v3"

# gpu instance
CONST_GPU_INSTANCE_PROFILE_MIG1_G = "MIG1g"
CONST_GPU_INSTANCE_PROFILE_MIG2_G = "MIG2g"
CONST_GPU_INSTANCE_PROFILE_MIG3_G = "MIG3g"
CONST_GPU_INSTANCE_PROFILE_MIG4_G = "MIG4g"
CONST_GPU_INSTANCE_PROFILE_MIG7_G = "MIG7g"

# gpu driver install
CONST_GPU_DRIVER_INSTALL = "Install"
CONST_GPU_DRIVER_NONE = "None"

# consts for ManagedCluster
# load balancer sku
CONST_LOAD_BALANCER_SKU_BASIC = "basic"
CONST_LOAD_BALANCER_SKU_STANDARD = "standard"

# ManagedClusterSKU Name
CONST_MANAGED_CLUSTER_SKU_NAME_BASE = "base"
CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC = "automatic"

# ManagedClusterSKU Tier
CONST_MANAGED_CLUSTER_SKU_TIER_FREE = "free"
CONST_MANAGED_CLUSTER_SKU_TIER_STANDARD = "standard"
CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM = "premium"

# outbound type
CONST_OUTBOUND_TYPE_LOAD_BALANCER = "loadBalancer"
CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING = "userDefinedRouting"
CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY = "managedNATGateway"
CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY = "userAssignedNATGateway"
CONST_OUTBOUND_TYPE_NONE = "none"

# load balancer backend pool type
CONST_LOAD_BALANCER_BACKEND_POOL_TYPE_NODE_IP = "nodeIP"
CONST_LOAD_BALANCER_BACKEND_POOL_TYPE_NODE_IP_CONFIGURATION = "nodeIPConfiguration"

# private dns zone mode
CONST_PRIVATE_DNS_ZONE_SYSTEM = "system"
CONST_PRIVATE_DNS_ZONE_NONE = "none"

# role assignment for kubelet
CONST_MANAGED_IDENTITY_OPERATOR_ROLE = "Managed Identity Operator"
CONST_MANAGED_IDENTITY_OPERATOR_ROLE_ID = "f1a07417-d97a-45cb-824c-7a7467783830"

# role assignment for vnet subnet
CONST_NETWORK_CONTRIBUTOR_ROLE_ID = "4d97b98b-1d4f-4787-a291-c67834d212e7"

# upgrade channel
CONST_RAPID_UPGRADE_CHANNEL = "rapid"
CONST_STABLE_UPGRADE_CHANNEL = "stable"
CONST_PATCH_UPGRADE_CHANNEL = "patch"
CONST_NODE_IMAGE_UPGRADE_CHANNEL = "node-image"
CONST_NONE_UPGRADE_CHANNEL = "none"

# consts for node os upgrade channel
CONST_NODE_OS_CHANNEL_NODE_IMAGE = "NodeImage"
CONST_NODE_OS_CHANNEL_NONE = "None"
CONST_NODE_OS_CHANNEL_UNMANAGED = "Unmanaged"
CONST_NODE_OS_CHANNEL_SECURITY_PATCH = "SecurityPatch"

# consts for nrg-lockdown restriction level
CONST_NRG_LOCKDOWN_RESTRICTION_LEVEL_READONLY = "ReadOnly"
CONST_NRG_LOCKDOWN_RESTRICTION_LEVEL_UNRESTRICTED = "Unrestricted"

# network plugin
CONST_NETWORK_PLUGIN_KUBENET = "kubenet"
CONST_NETWORK_PLUGIN_AZURE = "azure"
CONST_NETWORK_PLUGIN_NONE = "none"

# network plugin mode
CONST_NETWORK_PLUGIN_MODE_OVERLAY = "overlay"

# network dataplane
CONST_NETWORK_DATAPLANE_AZURE = "azure"
CONST_NETWORK_DATAPLANE_CILIUM = "cilium"

# network policy
CONST_NETWORK_POLICY_AZURE = "azure"
CONST_NETWORK_POLICY_CILIUM = "cilium"
CONST_NETWORK_POLICY_CALICO = "calico"
CONST_NETWORK_POLICY_NONE = "none"

# ACNS advanced network policies
CONST_ADVANCED_NETWORKPOLICIES_NONE = "None"
CONST_ADVANCED_NETWORKPOLICIES_FQDN = "FQDN"
CONST_ADVANCED_NETWORKPOLICIES_L7 = "L7"

# network pod ip allocation mode
CONST_NETWORK_POD_IP_ALLOCATION_MODE_DYNAMIC_INDIVIDUAL = "DynamicIndividual"
CONST_NETWORK_POD_IP_ALLOCATION_MODE_STATIC_BLOCK = "StaticBlock"

# consts for addons
# http application routing
CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME = "httpApplicationRouting"

# monitoring
CONST_MONITORING_ADDON_NAME = "omsagent"
CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID = "logAnalyticsWorkspaceResourceID"
CONST_MONITORING_USING_AAD_MSI_AUTH = "useAADAuth"

# virtual node
CONST_VIRTUAL_NODE_ADDON_NAME = "aciConnector"
CONST_VIRTUAL_NODE_SUBNET_NAME = "SubnetName"

# dashboard
CONST_KUBE_DASHBOARD_ADDON_NAME = "kubeDashboard"

# azure policy
CONST_AZURE_POLICY_ADDON_NAME = "azurepolicy"

# Managed Namespace
CONST_NAMESPACE_ADOPTION_POLICY_NEVER = "Never"
CONST_NAMESPACE_ADOPTION_POLICY_IFIDENTICAL = "IfIdentical"
CONST_NAMESPACE_ADOPTION_POLICY_ALWAYS = "Always"
CONST_NAMESPACE_NETWORK_POLICY_RULE_DENYALL = "DenyAll"
CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWALL = "AllowAll"
CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWSAMENAMESPACE = "AllowSameNamespace"
CONST_NAMESPACE_DELETE_POLICY_KEEP = "Keep"
CONST_NAMESPACE_DELETE_POLICY_DELETE = "Delete"

# ingress application gateway
CONST_INGRESS_APPGW_ADDON_NAME = "ingressApplicationGateway"
CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME = "applicationGatewayName"
CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID = "applicationGatewayId"
CONST_INGRESS_APPGW_SUBNET_ID = "subnetId"
CONST_INGRESS_APPGW_SUBNET_CIDR = "subnetCIDR"
CONST_INGRESS_APPGW_WATCH_NAMESPACE = "watchNamespace"

# confcom
CONST_CONFCOM_ADDON_NAME = "ACCSGXDevicePlugin"
CONST_ACC_SGX_QUOTE_HELPER_ENABLED = "ACCSGXQuoteHelperEnabled"

# open service mesh
CONST_OPEN_SERVICE_MESH_ADDON_NAME = "openServiceMesh"

# azure keyvault secrets provider
CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = "azureKeyvaultSecretsProvider"
CONST_SECRET_ROTATION_ENABLED = "enableSecretRotation"
CONST_ROTATION_POLL_INTERVAL = "rotationPollInterval"

# azure keyvault kms
CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PUBLIC = "Public"
CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE = "Private"

# app routing nginx config options
CONST_WEB_APPLICATION_ROUTING_KEY_NAME = "ingress/webApplicationRouting"
CONST_APP_ROUTING_ANNOTATION_CONTROLLED_NGINX = "AnnotationControlled"
CONST_APP_ROUTING_EXTERNAL_NGINX = "External"
CONST_APP_ROUTING_INTERNAL_NGINX = "Internal"
CONST_APP_ROUTING_NONE_NGINX = "None"

# all supported addons
ADDONS = {
    "http_application_routing": CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    "monitoring": CONST_MONITORING_ADDON_NAME,
    "virtual-node": CONST_VIRTUAL_NODE_ADDON_NAME,
    "kube-dashboard": CONST_KUBE_DASHBOARD_ADDON_NAME,
    "azure-policy": CONST_AZURE_POLICY_ADDON_NAME,
    "ingress-appgw": CONST_INGRESS_APPGW_ADDON_NAME,
    "confcom": CONST_CONFCOM_ADDON_NAME,
    "open-service-mesh": CONST_OPEN_SERVICE_MESH_ADDON_NAME,
    "azure-keyvault-secrets-provider": CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
    "web_application_routing": CONST_WEB_APPLICATION_ROUTING_KEY_NAME,
}

# consts for check-acr command
CONST_CANIPULL_IMAGE = "mcr.microsoft.com/aks/canipull:v0.1.0"

# consts for maintenance configuration schedule type
CONST_DAILY_MAINTENANCE_SCHEDULE = "Daily"
CONST_WEEKLY_MAINTENANCE_SCHEDULE = "Weekly"
CONST_ABSOLUTEMONTHLY_MAINTENANCE_SCHEDULE = "AbsoluteMonthly"
CONST_RELATIVEMONTHLY_MAINTENANCE_SCHEDULE = "RelativeMonthly"

CONST_WEEKINDEX_FIRST = "First"
CONST_WEEKINDEX_SECOND = "Second"
CONST_WEEKINDEX_THIRD = "Third"
CONST_WEEKINDEX_FOURTH = "Fourth"
CONST_WEEKINDEX_LAST = "Last"

CONST_DEFAULT_CONFIGURATION_NAME = "default"
CONST_AUTOUPGRADE_CONFIGURATION_NAME = "aksManagedAutoUpgradeSchedule"
CONST_NODEOSUPGRADE_CONFIGURATION_NAME = "aksManagedNodeOSUpgradeSchedule"

# consts for azure service mesh
CONST_AZURE_SERVICE_MESH_MODE_DISABLED = "Disabled"
CONST_AZURE_SERVICE_MESH_MODE_ISTIO = "Istio"
CONST_AZURE_SERVICE_MESH_INGRESS_MODE_EXTERNAL = "External"
CONST_AZURE_SERVICE_MESH_INGRESS_MODE_INTERNAL = "Internal"
CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START = "Start"
CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE = "Complete"
CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK = "Rollback"
CONST_AZURE_SERVICE_MESH_DEFAULT_EGRESS_NAMESPACE = "aks-istio-egress"
CONST_AZURE_SERVICE_MESH_MAX_EGRESS_NAME_LENGTH = 63

# Dns zone contributor role
CONST_PRIVATE_DNS_ZONE_CONTRIBUTOR_ROLE = "Private DNS Zone Contributor"
CONST_DNS_ZONE_CONTRIBUTOR_ROLE = "DNS Zone Contributor"

# consts for network isolated cluster
CONST_ARTIFACT_SOURCE_DIRECT = "Direct"
CONST_ARTIFACT_SOURCE_CACHE = "Cache"

# node provisioning mode
CONST_NODE_PROVISIONING_MODE_MANUAL = "Manual"
CONST_NODE_PROVISIONING_MODE_AUTO = "Auto"

# node provisioning default pools
CONST_NODE_PROVISIONING_DEFAULT_POOLS_NONE = "None"
CONST_NODE_PROVISIONING_DEFAULT_POOLS_AUTO = "Auto"

# consts for workloadruntime
CONST_WORKLOAD_RUNTIME_KATA_VM_ISOLATION = "KataVmIsolation"


# consts for decorator pattern
class DecoratorMode(Enum):
    """Enumerations used to distinguish whether to handle creation or update."""

    CREATE = 1
    UPDATE = 2


class AgentPoolDecoratorMode(Enum):
    """Enumerations used to distinguish whether to deal with the default system agentpool in the context of the cluster
    or any specific agentpool.
    """

    MANAGED_CLUSTER = 1
    STANDALONE = 2


# custom exception for decorator pattern, used for gracefully exit
class DecoratorEarlyExitException(Exception):
    pass
