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

# os type
CONST_DEFAULT_NODE_OS_TYPE = "Linux"

# os sku
CONST_OS_SKU_UBUNTU = "Ubuntu"
CONST_OS_SKU_CBLMARINER = "CBLMariner"

# vm set type
CONST_VIRTUAL_MACHINE_SCALE_SETS = "VirtualMachineScaleSets"
CONST_AVAILABILITY_SET = "AvailabilitySet"

# vm size
CONST_DEFAULT_NODE_VM_SIZE = "Standard_DS2_v2"
CONST_DEFAULT_WINDOWS_NODE_VM_SIZE = "Standard_D2s_v3"

# consts for ManagedCluster
# outbound type
CONST_OUTBOUND_TYPE_LOAD_BALANCER = "loadBalancer"
CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING = "userDefinedRouting"
CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY = "managedNATGateway"
CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY = "userAssignedNATGateway"

# private dns zone mode
CONST_PRIVATE_DNS_ZONE_SYSTEM = "system"
CONST_PRIVATE_DNS_ZONE_NONE = "none"

# used to set identity profile (for kubelet)
CONST_MANAGED_IDENTITY_OPERATOR_ROLE = 'Managed Identity Operator'
CONST_MANAGED_IDENTITY_OPERATOR_ROLE_ID = 'f1a07417-d97a-45cb-824c-7a7467783830'

# upgrade channel
CONST_RAPID_UPGRADE_CHANNEL = "rapid"
CONST_STABLE_UPGRADE_CHANNEL = "stable"
CONST_PATCH_UPGRADE_CHANNEL = "patch"
CONST_NODE_IMAGE_UPGRADE_CHANNEL = "node-image"
CONST_NONE_UPGRADE_CHANNEL = "none"

# network plugin
CONST_NETWORK_PLUGIN_KUBENET = "kubenet"
CONST_NETWORK_PLUGIN_AZURE = "azure"

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

# all supported addons
ADDONS = {
    'http_application_routing': CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    'monitoring': CONST_MONITORING_ADDON_NAME,
    'virtual-node': CONST_VIRTUAL_NODE_ADDON_NAME,
    'kube-dashboard': CONST_KUBE_DASHBOARD_ADDON_NAME,
    'azure-policy': CONST_AZURE_POLICY_ADDON_NAME,
    'ingress-appgw': CONST_INGRESS_APPGW_ADDON_NAME,
    "confcom": CONST_CONFCOM_ADDON_NAME,
    'open-service-mesh': CONST_OPEN_SERVICE_MESH_ADDON_NAME,
    'azure-keyvault-secrets-provider': CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
}

# consts for check-acr command
CONST_CANIPULL_IMAGE = "mcr.microsoft.com/aks/canipull:0.0.4-alpha"


# consts for decorator pattern
class DecoratorMode(Enum):
    """Enumerations used to distinguish whether to handle creation or update.
    """
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
