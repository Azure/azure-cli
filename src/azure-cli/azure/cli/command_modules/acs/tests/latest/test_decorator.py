# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
from re import T
import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.acs._consts import (
    CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
    CONST_AZURE_POLICY_ADDON_NAME,
    CONST_CONFCOM_ADDON_NAME,
    CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    CONST_INGRESS_APPGW_ADDON_NAME,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME,
    CONST_INGRESS_APPGW_SUBNET_CIDR,
    CONST_INGRESS_APPGW_SUBNET_ID,
    CONST_INGRESS_APPGW_WATCH_NAMESPACE,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
    CONST_PRIVATE_DNS_ZONE_SYSTEM,
    CONST_VIRTUAL_NODE_ADDON_NAME,
    CONST_VIRTUAL_NODE_SUBNET_NAME,
)
from azure.cli.command_modules.acs.decorator import (
    AKSCreateContext,
    AKSCreateDecorator,
    AKSCreateModels,
)
from azure.cli.command_modules.acs.tests.latest.mocks import (
    MockCLI,
    MockClient,
    MockCmd,
)
from azure.cli.core.azclierror import (
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azure.cli.core.profiles import ResourceType
from knack.util import CLIError


class AKSCreateModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)

    def test_models(self):
        models = AKSCreateModels(self.cmd)

        # load models directly (instead of through the `get_sdk` method provided by the cli component)
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES

        sdk_profile = AZURE_API_PROFILES["latest"][
            ResourceType.MGMT_CONTAINERSERVICE
        ]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(
            api_version.replace("-", "_")
        )
        module = importlib.import_module(module_name)

        self.assertEqual(
            models.ManagedClusterWindowsProfile,
            getattr(module, "ManagedClusterWindowsProfile"),
        )
        self.assertEqual(
            models.ManagedClusterSKU, getattr(module, "ManagedClusterSKU")
        )
        self.assertEqual(
            models.ContainerServiceNetworkProfile,
            getattr(module, "ContainerServiceNetworkProfile"),
        )
        self.assertEqual(
            models.ContainerServiceLinuxProfile,
            getattr(module, "ContainerServiceLinuxProfile"),
        )
        self.assertEqual(
            models.ManagedClusterServicePrincipalProfile,
            getattr(module, "ManagedClusterServicePrincipalProfile"),
        )
        self.assertEqual(
            models.ContainerServiceSshConfiguration,
            getattr(module, "ContainerServiceSshConfiguration"),
        )
        self.assertEqual(
            models.ContainerServiceSshPublicKey,
            getattr(module, "ContainerServiceSshPublicKey"),
        )
        self.assertEqual(
            models.ManagedClusterAADProfile,
            getattr(module, "ManagedClusterAADProfile"),
        )
        self.assertEqual(
            models.ManagedClusterAutoUpgradeProfile,
            getattr(module, "ManagedClusterAutoUpgradeProfile"),
        )
        self.assertEqual(
            models.ManagedClusterAgentPoolProfile,
            getattr(module, "ManagedClusterAgentPoolProfile"),
        )
        self.assertEqual(
            models.ManagedClusterIdentity,
            getattr(module, "ManagedClusterIdentity"),
        )
        self.assertEqual(
            models.UserAssignedIdentity,
            getattr(
                module,
                "UserAssignedIdentity",
            ),
        )
        self.assertEqual(
            models.ManagedCluster, getattr(module, "ManagedCluster")
        )
        self.assertEqual(
            models.ManagedServiceIdentityUserAssignedIdentitiesValue,
            getattr(
                module,
                "ManagedServiceIdentityUserAssignedIdentitiesValue",
            ),
        )
        self.assertEqual(
            models.ExtendedLocation, getattr(module, "ExtendedLocation")
        )
        self.assertEqual(
            models.ExtendedLocationTypes,
            getattr(module, "ExtendedLocationTypes"),
        )
        # not directly used
        self.assertEqual(
            models.ManagedClusterAPIServerAccessProfile,
            getattr(module, "ManagedClusterAPIServerAccessProfile"),
        )
        # load balancer models
        self.assertEqual(
            models.lb_models.get("ManagedClusterLoadBalancerProfile"),
            getattr(module, "ManagedClusterLoadBalancerProfile"),
        )
        self.assertEqual(
            models.lb_models.get(
                "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
            ),
            getattr(
                module, "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
            ),
        )
        self.assertEqual(
            models.lb_models.get(
                "ManagedClusterLoadBalancerProfileOutboundIPs"
            ),
            getattr(module, "ManagedClusterLoadBalancerProfileOutboundIPs"),
        )
        self.assertEqual(
            models.lb_models.get(
                "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
            ),
            getattr(
                module, "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
            ),
        )
        self.assertEqual(
            models.lb_models.get("ResourceReference"),
            getattr(module, "ResourceReference"),
        )


class AKSCreateContextTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSCreateModels(self.cmd)

    def test_attach_mc(self):
        ctx_1 = AKSCreateContext(self.cmd, {})
        mc = self.models.ManagedCluster(location="test_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.mc.location, "test_location")

    def test_get_intermediate(self):
        ctx_1 = AKSCreateContext(self.cmd, {})
        self.assertEqual(
            ctx_1.get_intermediate("fake-intermediate", "not found"),
            "not found",
        )

    def test_set_intermediate(self):
        ctx_1 = AKSCreateContext(self.cmd, {})
        ctx_1.set_intermediate("test-intermediate", "test-intermediate-value")
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.set_intermediate(
            "test-intermediate", "new-test-intermediate-value"
        )
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.set_intermediate(
            "test-intermediate",
            "new-test-intermediate-value",
            overwrite_exists=True,
        )
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "new-test-intermediate-value",
        )

    def test_remove_intermediate(self):
        ctx_1 = AKSCreateContext(self.cmd, {})
        ctx_1.set_intermediate("test-intermediate", "test-intermediate-value")
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.remove_intermediate("test-intermediate")
        self.assertEqual(ctx_1.get_intermediate("test-intermediate"), None)

    def test_get_resource_group_name(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd, {"resource_group_name": "test_rg_name"}
        )
        self.assertEqual(ctx_1.get_resource_group_name(), "test_rg_name")

    def test_get_name(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"name": "test_name"})
        self.assertEqual(ctx_1.get_name(), "test_name")

    def test_get_ssh_key_value_and_no_ssh_key(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())

        # default
        ctx_1 = AKSCreateContext(
            self.cmd, {"ssh_key_value": public_key, "no_ssh_key": False}
        )
        self.assertEqual(
            ctx_1.get_ssh_key_value_and_no_ssh_key(), (public_key, False)
        )
        ssh_config = self.models.ContainerServiceSshConfiguration(
            public_keys=[
                self.models.ContainerServiceSshPublicKey(
                    key_data="test_mc_ssh_key_value"
                )
            ]
        )
        linux_profile = self.models.ContainerServiceLinuxProfile(
            admin_username="test_user", ssh=ssh_config
        )
        mc = self.models.ManagedCluster(
            location="test_location", linux_profile=linux_profile
        )
        ctx_1.attach_mc(mc)
        with self.assertRaises(CLIError):
            self.assertEqual(
                ctx_1.get_ssh_key_value_and_no_ssh_key(),
                "test_mc_ssh_key_value",
            )

        # invalid key with validation
        ctx_2 = AKSCreateContext(
            self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": False}
        )
        with self.assertRaises(CLIError):
            ctx_2.get_ssh_key_value_and_no_ssh_key()

        # invalid key & valid parameter with validation
        ctx_3 = AKSCreateContext(
            self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": True}
        )
        self.assertEqual(
            ctx_3.get_ssh_key_value_and_no_ssh_key(), ("fake-key", True)
        )
        ssh_config_3 = self.models.ContainerServiceSshConfiguration(
            public_keys=[
                self.models.ContainerServiceSshPublicKey(
                    key_data="test_mc_ssh_key_value"
                )
            ]
        )
        linux_profile_3 = self.models.ContainerServiceLinuxProfile(
            admin_username="test_user", ssh=ssh_config_3
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location", linux_profile=linux_profile_3
        )
        ctx_3.attach_mc(mc_3)
        with self.assertRaises(CLIInternalError):
            self.assertEqual(
                ctx_3.get_ssh_key_value_and_no_ssh_key(),
                "test_mc_ssh_key_value",
            )

    def test_get_dns_name_prefix(self):
        # default & dynamic completion
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "dns_name_prefix": None,
                "fqdn_subdomain": None,
                "name": "test_name",
                "resource_group_name": "test_rg_name",
            },
        )
        ctx_1.set_intermediate("subscription_id", "1234-5678")
        self.assertEqual(
            ctx_1.get_dns_name_prefix(), "testname-testrgname-1234-5"
        )
        mc = self.models.ManagedCluster(
            location="test_location", dns_prefix="test_mc_dns_name_prefix"
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_dns_name_prefix(), "test_mc_dns_name_prefix")

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "dns_name_prefix": "test_dns_name_prefix",
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_dns_name_prefix()

    def test_get_location(self):
        # default & dynamic completion
        ctx_1 = AKSCreateContext(self.cmd, {"location": None})
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ):
            self.assertEqual(ctx_1.get_location(), "test_location")
        mc = self.models.ManagedCluster(location="test_mc_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_location(), "test_mc_location")

    def test_get_kubernetes_version(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"kubernetes_version": ""})
        self.assertEqual(ctx_1.get_kubernetes_version(), "")
        mc = self.models.ManagedCluster(
            location="test_location",
            kubernetes_version="test_mc_kubernetes_version",
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_kubernetes_version(), "test_mc_kubernetes_version"
        )

    def test_get_vm_set_type(self):
        # default & dynamic completion
        ctx_1 = AKSCreateContext(
            self.cmd, {"vm_set_type": None, "kubernetes_version": ""}
        )
        self.assertEqual(ctx_1.get_vm_set_type(), "VirtualMachineScaleSets")
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_ap_name", type="test_mc_vm_set_type"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_vm_set_type(), "test_mc_vm_set_type")

        # custom value & dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {"vm_set_type": "availabilityset", "kubernetes_version": ""},
        )
        self.assertEqual(ctx_2.get_vm_set_type(), "AvailabilitySet")
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_ap_name", type="test_mc_vm_set_type"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_vm_set_type(), "test_mc_vm_set_type")

    def test_get_nodepool_name(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"nodepool_name": "nodepool1"})
        self.assertEqual(ctx_1.get_nodepool_name(), "nodepool1")
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_mc_nodepool_name"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_nodepool_name(), "test_mc_nodepool_name")

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd, {"nodepool_name": "test_nodepool_name"}
        )
        self.assertEqual(ctx_2.get_nodepool_name(), "test_nodepoo")
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_nodepool_name(), "test_nodepool_name")

        # dynamic completion
        ctx_3 = AKSCreateContext(self.cmd, {"nodepool_name": None})
        self.assertEqual(ctx_3.get_nodepool_name(), "nodepool1")

    def test_get_nodepool_tags(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"nodepool_tags": None})
        self.assertEqual(ctx_1.get_nodepool_tags(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", tags={}
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_nodepool_tags(), {})

    def test_get_nodepool_labels(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"nodepool_labels": None})
        self.assertEqual(ctx_1.get_nodepool_labels(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            node_labels={"key1": "value1", "key2": "value2"},
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_nodepool_labels(), {"key1": "value1", "key2": "value2"}
        )

    def test_get_node_vm_size(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"node_vm_size": "Standard_DS2_v2"})
        self.assertEqual(ctx_1.get_node_vm_size(), "Standard_DS2_v2")
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", vm_size="Standard_ABCD_v2"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_node_vm_size(), "Standard_ABCD_v2")

    def test_get_vnet_subnet_id(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"vnet_subnet_id": None})
        self.assertEqual(ctx_1.get_vnet_subnet_id(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", vnet_subnet_id="test_mc_vnet_subnet_id"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_vnet_subnet_id(), "test_mc_vnet_subnet_id")

    def test_get_ppg(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"ppg": None})
        self.assertEqual(ctx_1.get_ppg(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            proximity_placement_group_id="test_mc_ppg",
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_ppg(), "test_mc_ppg")

    def test_get_zones(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"zones": None})
        self.assertEqual(ctx_1.get_zones(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            availability_zones=["test_mc_zones1", "test_mc_zones2"],
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_zones(), ["test_mc_zones1", "test_mc_zones2"]
        )

    def test_get_enable_node_public_ip(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"enable_node_public_ip": False})
        self.assertEqual(ctx_1.get_enable_node_public_ip(), False)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", enable_node_public_ip=True
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_node_public_ip(), True)

    def test_get_node_public_ip_prefix_id(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {"node_public_ip_prefix_id": None},
        )
        self.assertEqual(
            ctx_1.get_node_public_ip_prefix_id(),
            None,
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            node_public_ip_prefix_id="test_mc_node_public_ip_prefix_id",
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_node_public_ip_prefix_id(),
            "test_mc_node_public_ip_prefix_id",
        )

    def test_get_enable_encryption_at_host(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"enable_encryption_at_host": False})
        self.assertEqual(ctx_1.get_enable_encryption_at_host(), False)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", enable_encryption_at_host=True
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_encryption_at_host(), True)

    def test_enable_ultra_ssd(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"enable_ultra_ssd": False})
        self.assertEqual(ctx_1.get_enable_ultra_ssd(), False)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", enable_ultra_ssd=True
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_ultra_ssd(), True)

    def test_get_max_pods(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"max_pods": 0})
        self.assertEqual(ctx_1.get_max_pods(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", max_pods=10
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_max_pods(), 10)

    def test_get_node_osdisk_size(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"node_osdisk_size": 0})
        self.assertEqual(ctx_1.get_node_osdisk_size(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", os_disk_size_gb=10
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_node_osdisk_size(), 10)

    def test_get_node_osdisk_type(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"node_osdisk_type": None})
        self.assertEqual(ctx_1.get_node_osdisk_type(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", os_disk_type="test_mc_node_osdisk_type"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_node_osdisk_type(), "test_mc_node_osdisk_type"
        )

    def test_get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count(
        self,
    ):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 3,
                "enable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
            },
        )
        self.assertEqual(
            ctx_1.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count(),
            (3, False, None, None),
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=5,
            enable_auto_scaling=True,
            min_count=1,
            max_count=10,
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count(),
            (5, True, 1, 10),
        )

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": True,
                "min_count": None,
                "max_count": None,
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count()

        # invalid parameter with validation
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": True,
                "min_count": 3,
                "max_count": 1,
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count()

        # invalid parameter with validation
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": True,
                "min_count": 7,
                "max_count": 10,
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count()

        # invalid parameter with validation
        ctx_5 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": False,
                "min_count": 3,
                "max_count": None,
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_5.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count()

    def test_get_admin_username(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"admin_username": "azureuser"})
        self.assertEqual(ctx_1.get_admin_username(), "azureuser")
        ssh_config = self.models.ContainerServiceSshConfiguration(
            public_keys=[]
        )
        linux_profile = self.models.ContainerServiceLinuxProfile(
            admin_username="test_mc_user", ssh=ssh_config
        )
        mc = self.models.ManagedCluster(
            location="test_location", linux_profile=linux_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_admin_username(), "test_mc_user")

    def test_get_windows_admin_username_and_password(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {"windows_admin_username": None, "windows_admin_password": None},
        )
        self.assertEqual(
            ctx_1.get_windows_admin_username_and_password(), (None, None)
        )
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin",
            admin_password="test_mc_win_admin_password",
        )
        mc = self.models.ManagedCluster(
            location="test_location", windows_profile=windows_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_windows_admin_username_and_password(),
            ("test_mc_win_admin", "test_mc_win_admin_password"),
        )

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "windows_admin_username": None,
                "windows_admin_password": "test_win_admin_pd",
            },
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.prompt",
            return_value="test_win_admin_name",
        ):
            self.assertEqual(
                ctx_2.get_windows_admin_username_and_password(),
                ("test_win_admin_name", "test_win_admin_pd"),
            )
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin_name",
            admin_password="test_mc_win_admin_pd",
        )
        mc = self.models.ManagedCluster(
            location="test_location", windows_profile=windows_profile
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(
            ctx_2.get_windows_admin_username_and_password(),
            ("test_mc_win_admin_name", "test_mc_win_admin_pd"),
        )

        # dynamic completion
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "windows_admin_username": "test_win_admin_name",
                "windows_admin_password": None,
            },
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.prompt_pass",
            return_value="test_win_admin_pd",
        ):
            self.assertEqual(
                ctx_3.get_windows_admin_username_and_password(),
                ("test_win_admin_name", "test_win_admin_pd"),
            )
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin_name",
            admin_password="test_mc_win_admin_pd",
        )
        mc = self.models.ManagedCluster(
            location="test_location", windows_profile=windows_profile
        )
        ctx_3.attach_mc(mc)
        self.assertEqual(
            ctx_3.get_windows_admin_username_and_password(),
            ("test_mc_win_admin_name", "test_mc_win_admin_pd"),
        )

    def test_get_enable_ahub(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"enable_ahub": False})
        self.assertEqual(ctx_1.get_enable_ahub(), False)
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin",
            admin_password="test_mc_win_admin_password",
            license_type="Windows_Server",
        )
        mc = self.models.ManagedCluster(
            location="test_location", windows_profile=windows_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_ahub(), True)

    def test_get_service_principal_and_client_secret(
        self,
    ):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": None,
            },
        )
        self.assertEqual(
            ctx_1.get_service_principal_and_client_secret(),
            (None, None),
        )

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
        )
        ctx_2.set_intermediate(
            "subscription_id", "1234-5678", overwrite_exists=True
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.custom.get_graph_rbac_management_client",
            return_value=None,
        ):
            self.assertEqual(
                ctx_2.get_service_principal_and_client_secret(),
                ("test_service_principal", "test_client_secret"),
            )

        # dynamic completion
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": "test_client_secret",
            },
        )
        ctx_3.set_intermediate(
            "subscription_id", "1234-5678", overwrite_exists=True
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.custom.get_graph_rbac_management_client",
            return_value=None,
        ), patch(
            "azure.cli.command_modules.acs.custom._build_service_principal",
            return_value=("test_service_principal", "test_aad_session_key"),
        ):
            self.assertEqual(
                ctx_3.get_service_principal_and_client_secret(),
                ("test_service_principal", "test_client_secret"),
            )
        service_principal_profile = (
            self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_mc_service_principal",
                secret="test_mc_client_secret",
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile,
        )
        ctx_3.attach_mc(mc)
        self.assertEqual(
            ctx_3.get_service_principal_and_client_secret(),
            ("test_mc_service_principal", "test_mc_client_secret"),
        )

        # dynamic completion
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": None,
            },
        )
        ctx_4.set_intermediate(
            "subscription_id", "1234-5678", overwrite_exists=True
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.custom.get_graph_rbac_management_client",
            return_value=None,
        ):
            with self.assertRaises(CLIError):
                ctx_4.get_service_principal_and_client_secret()

    def test_get_enable_managed_identity(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": None,
            },
        )
        self.assertEqual(ctx_1.get_enable_managed_identity(), True)
        identity = self.models.ManagedClusterIdentity()
        mc = self.models.ManagedCluster(
            location="test_location", identity=identity
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_managed_identity(), False)

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
        )
        ctx_2.set_intermediate(
            "subscription_id", "1234-5678", overwrite_exists=True
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.custom.get_graph_rbac_management_client",
            return_value=None,
        ):
            self.assertEqual(
                ctx_2.get_service_principal_and_client_secret(),
                ("test_service_principal", "test_client_secret"),
            )

    def test_get_skip_subnet_role_assignment(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd, {"skip_subnet_role_assignment": False}
        )
        self.assertEqual(ctx_1.get_skip_subnet_role_assignment(), False)

    def test_get_assign_identity(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"assign_identity": None})
        self.assertEqual(ctx_1.get_assign_identity(), None)

    def test_get_user_assigned_identity_client_id(self):
        # invalid parameter
        ctx_1 = AKSCreateContext(self.cmd, {"assign_identity": None})
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_user_assigned_identity_client_id()

    def test_get_user_assigned_identity_object_id(self):
        # custom value
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "assign_identity": "/subscriptions/1234/resourcegroups/test_rg/providers/microsoft.managedidentity/userassignedidentities/5678"
            },
        )
        identity_obj = Mock(principal_id="8765-4321")
        msi_client = Mock(
            user_assigned_identities=Mock(get=Mock(return_value=identity_obj))
        )
        with patch(
            "azure.cli.command_modules.acs.custom.get_msi_client",
            return_value=msi_client,
        ) as get_msi_client:
            self.assertEqual(
                ctx_1.get_user_assigned_identity_object_id(), "8765-4321"
            )
        get_msi_client.assert_called_once_with(self.cmd.cli_ctx, "1234")
        msi_client.user_assigned_identities.get.assert_called_once_with(
            resource_group_name="test_rg", resource_name="5678"
        )

    def test_get_yes(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"yes": False})
        self.assertEqual(ctx_1.get_yes(), False)

    def test_get_attach_acr(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"attach_acr": None})
        self.assertEqual(ctx_1.get_attach_acr(), None)

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": True,
                "no_wait": True,
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_attach_acr()

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": False,
            },
        )
        with self.assertRaises(CLIInternalError):
            ctx_3.get_attach_acr()

    def test_get_no_wait(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"no_wait": False})
        self.assertEqual(ctx_1.get_no_wait(), False)

    def test_get_load_balancer_sku(self):
        # default & dynamic completion
        ctx_1 = AKSCreateContext(
            self.cmd,
            {"load_balancer_sku": None, "kubernetes_version": ""},
        )
        self.assertEqual(ctx_1._get_load_balancer_sku(read_only=True), None)
        self.assertEqual(ctx_1.get_load_balancer_sku(), "standard")
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="test_mc_load_balancer_SKU"
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_load_balancer_sku(), "test_mc_load_balancer_sku"
        )

        # custom value & dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {"load_balancer_sku": None, "kubernetes_version": "1.12.0"},
        )
        self.assertEqual(ctx_2.get_load_balancer_sku(), "basic")
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="test_mc_load_balancer_sku"
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(
            ctx_2.get_load_balancer_sku(), "test_mc_load_balancer_sku"
        )

        # invalid parameter with validation
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_sku": "basic",
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_load_balancer_sku()

        # custom value (lower case)
        ctx_4 = AKSCreateContext(
            self.cmd,
            {"load_balancer_sku": "STANDARD"},
        )
        self.assertEqual(ctx_4.get_load_balancer_sku(), "standard")

    def test_get_load_balancer_managed_outbound_ip_count(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_managed_outbound_ip_count": None,
            },
        )
        self.assertEqual(
            ctx_1.get_load_balancer_managed_outbound_ip_count(), None
        )
        load_balancer_profile = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(
            managed_outbound_i_ps=self.models.lb_models.get(
                "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
            )(count=10)
        )
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_load_balancer_managed_outbound_ip_count(), 10
        )

    def test_get_load_balancer_outbound_ips(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_outbound_ips": None,
            },
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ips(), None)
        load_balancer_profile = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(
            outbound_i_ps=self.models.lb_models.get(
                "ManagedClusterLoadBalancerProfileOutboundIPs"
            )(
                public_i_ps=[
                    self.models.lb_models.get("ResourceReference")(
                        id="test_public_ip"
                    )
                ]
            )
        )
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_load_balancer_outbound_ips(),
            [
                self.models.lb_models.get("ResourceReference")(
                    id="test_public_ip"
                )
            ],
        )

    def test_get_load_balancer_outbound_ip_prefixes(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_outbound_ip_prefixes": None,
            },
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ip_prefixes(), None)
        load_balancer_profile = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(
            outbound_ip_prefixes=self.models.lb_models.get(
                "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
            )(
                public_ip_prefixes=[
                    self.models.lb_models.get("ResourceReference")(
                        id="test_public_ip_prefix"
                    )
                ]
            )
        )
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_load_balancer_outbound_ip_prefixes(),
            [
                self.models.lb_models.get("ResourceReference")(
                    id="test_public_ip_prefix"
                )
            ],
        )

    def test_get_load_balancer_outbound_ports(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_outbound_ports": None,
            },
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ports(), None)
        load_balancer_profile = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(allocated_outbound_ports=10)
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_load_balancer_outbound_ports(), 10)

    def test_get_load_balancer_idle_timeout(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_idle_timeout": None,
            },
        )
        self.assertEqual(ctx_1.get_load_balancer_idle_timeout(), None)
        load_balancer_profile = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(idle_timeout_in_minutes=10)
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_load_balancer_idle_timeout(), 10)

    def test_get_outbound_type(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "outbound_type": None,
            },
        )
        self.assertEqual(ctx_1.get_outbound_type(), "loadBalancer")
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            outbound_type="test_outbound_type"
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_outbound_type(), "test_outbound_type")

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                "load_balancer_sku": "basic",
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_outbound_type()

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_outbound_type()

        # invalid parameter
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                "vnet_subnet_id": "test_vnet_subnet_id",
                "load_balancer_managed_outbound_ip_count": 10,
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_4.get_outbound_type()

        # invalid parameter
        ctx_5 = AKSCreateContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                "vnet_subnet_id": "test_vnet_subnet_id",
            },
        )
        load_balancer_profile = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(
            outbound_ip_prefixes=self.models.lb_models.get(
                "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
            )(
                public_ip_prefixes=[
                    self.models.lb_models.get("ResourceReference")(
                        id="test_public_ip_prefix"
                    )
                ]
            )
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_5.get_outbound_type(
                load_balancer_profile=load_balancer_profile,
            )

    def test_get_network_plugin(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "network_plugin": None,
            },
        )
        self.assertEqual(ctx_1.get_network_plugin(), None)
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            network_plugin="test_network_plugin"
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_network_plugin(), "test_network_plugin")

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "network_plugin": "azure",
                "pod_cidr": "test_pod_cidr",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_network_plugin()

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "pod_cidr": "test_pod_cidr",
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_network_plugin()

    def test_get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
        self,
    ):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "docker_bridge_address": None,
                "network_policy": None,
            },
        )
        self.assertEqual(
            ctx_1.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(),
            (None, None, None, None, None),
        )
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            pod_cidr="test_pod_cidr",
            service_cidr="test_service_cidr",
            dns_service_ip="test_dns_service_ip",
            docker_bridge_cidr="test_docker_bridge_address",
            network_policy="test_network_policy",
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(),
            (
                "test_pod_cidr",
                "test_service_cidr",
                "test_dns_service_ip",
                "test_docker_bridge_address",
                "test_network_policy",
            ),
        )

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "network_plugin": "azure",
                "pod_cidr": "test_pod_cidr",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "pod_cidr": "test_pod_cidr",
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

        # invalid parameter
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "service_cidr": "test_service_cidr",
                "dns_service_ip": "test_dns_service_ip",
                "docker_bridge_address": "test_docker_bridge_address",
                "network_policy": "test_network_policy",
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

    def test_get_enable_addons(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": None,
            },
        )
        self.assertEqual(ctx_1.get_enable_addons(), [])

        # custom value
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": "http_application_routing,monitoring",
            },
        )
        self.assertEqual(
            ctx_2.get_enable_addons(),
            ["http_application_routing", "monitoring"],
        )

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": "test_addon_1,test_addon_2",
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_enable_addons()

        # invalid parameter
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": "test_addon_1,test_addon_2,test_addon_1,test_addon_2",
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_addons()

        # invalid parameter
        ctx_5 = AKSCreateContext(
            self.cmd,
            {
                "workspace_resource_id": "/test_workspace_resource_id",
                "enable_addons": "",
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_5.get_enable_addons()

        # invalid parameter
        ctx_6 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": "virtual-node",
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_6.get_enable_addons()

    def test_get_workspace_resource_id(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "workspace_resource_id": None,
            },
        )
        self.assertEqual(ctx_1._get_workspace_resource_id(read_only=True), None)
        addon_profiles_1 = {
            CONST_MONITORING_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: "test_workspace_resource_id"
                },
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_workspace_resource_id()

        # custom value & dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": "monitoring",
                "workspace_resource_id": "test_workspace_resource_id/",
            },
        )
        self.assertEqual(
            ctx_2.get_workspace_resource_id(), "/test_workspace_resource_id"
        )

        # dynamic completion
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "enable_addons": "monitoring",
                "resource_group_name": "test_rg_name",
                "workspace_resource_id": None,
            },
        )
        ctx_3.set_intermediate("subscription_id", "test_subscription_id")
        cf_resource_groups = Mock(check_existence=Mock(return_value=False))
        result = Mock(id="test_workspace_resource_id")
        async_poller = Mock(
            result=Mock(return_value=result), done=Mock(return_value=True)
        )
        cf_resources = Mock(
            begin_create_or_update_by_id=Mock(return_value=async_poller)
        )
        with patch(
            "azure.cli.command_modules.acs.custom._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.custom.cf_resource_groups",
            return_value=cf_resource_groups,
        ), patch(
            "azure.cli.command_modules.acs.custom.cf_resources",
            return_value=cf_resources,
        ):
            self.assertEqual(
                ctx_3.get_workspace_resource_id(), "/test_workspace_resource_id"
            )
        cf_resource_groups.check_existence.assert_called_once_with(
            "DefaultResourceGroup-EUS"
        )
        cf_resource_groups.create_or_update.assert_called_once_with(
            "DefaultResourceGroup-EUS", {"location": "eastus"}
        )
        default_workspace_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.OperationalInsights/workspaces/{2}".format(
            "test_subscription_id",
            "DefaultResourceGroup-EUS",
            "DefaultWorkspace-test_subscription_id-EUS",
        )
        # the return values are func_name, args and kwargs
        _, args, _ = cf_resources.begin_create_or_update_by_id.mock_calls[0]
        # not interested in mocking generic_resource, so we only check the first two args
        self.assertEqual(
            args[:2], (default_workspace_resource_id, "2015-11-01-preview")
        )

    def test_get_virtual_node_addon_os_type(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {})
        self.assertEqual(ctx_1.get_virtual_node_addon_os_type(), "Linux")

    def test_get_aci_subnet_name(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "aci_subnet_name": None,
            },
        )
        self.assertEqual(ctx_1.get_aci_subnet_name(), None)
        addon_profiles_1 = {
            CONST_VIRTUAL_NODE_ADDON_NAME
            + ctx_1.get_virtual_node_addon_os_type(): self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_VIRTUAL_NODE_SUBNET_NAME: "test_aci_subnet_name"},
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_aci_subnet_name(), "test_aci_subnet_name")

    def test_get_appgw_name(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "appgw_name": None,
            },
        )
        self.assertEqual(ctx_1.get_appgw_name(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME: "test_appgw_name"
                },
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_name(), "test_appgw_name")

    def test_get_appgw_subnet_cidr(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "appgw_subnet_cidr": None,
            },
        )
        self.assertEqual(ctx_1.get_appgw_subnet_cidr(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_INGRESS_APPGW_SUBNET_CIDR: "test_appgw_subnet_cidr"
                },
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_appgw_subnet_cidr(), "test_appgw_subnet_cidr"
        )

    def test_get_appgw_id(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "appgw_id": None,
            },
        )
        self.assertEqual(ctx_1.get_appgw_id(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID: "test_appgw_id"
                },
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_id(), "test_appgw_id")

    def test_get_appgw_subnet_id(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "appgw_subnet_id": None,
            },
        )
        self.assertEqual(ctx_1.get_appgw_subnet_id(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_INGRESS_APPGW_SUBNET_ID: "test_appgw_subnet_id"},
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_subnet_id(), "test_appgw_subnet_id")

    def test_get_appgw_watch_namespace(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "appgw_watch_namespace": None,
            },
        )
        self.assertEqual(ctx_1.get_appgw_watch_namespace(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_INGRESS_APPGW_WATCH_NAMESPACE: "test_appgw_watch_namespace"
                },
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_appgw_watch_namespace(), "test_appgw_watch_namespace"
        )

    def test_get_enable_sgxquotehelper(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_sgxquotehelper": False,
            },
        )
        self.assertEqual(ctx_1.get_enable_sgxquotehelper(), False)
        addon_profiles_1 = {
            CONST_CONFCOM_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "true"},
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_sgxquotehelper(), "true")

    def test_get_enable_aad(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_aad": False,
            },
        )
        self.assertEqual(ctx_1.get_enable_aad(), False)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            managed=True,
        )
        mc = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_aad(), True)

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_aad": True,
                "aad_client_app_id": "test_aad_client_app_id",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_aad()

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "enable_aad": False,
                "enable_azure_rbac": True,
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_aad()

    def test_get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(
        self,
    ):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "aad_client_app_id": None,
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
            },
        )
        self.assertEqual(
            ctx_1.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(),
            (None, None, None),
        )
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            client_app_id="test_aad_client_app_id",
            server_app_id="test_aad_server_app_id",
            server_app_secret="test_aad_server_app_secret",
        )
        mc = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(),
            (
                "test_aad_client_app_id",
                "test_aad_server_app_id",
                "test_aad_server_app_secret",
            ),
        )

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_aad": True,
                "aad_client_app_id": "test_aad_client_app_id",
                "aad_server_app_id": "test_aad_server_app_id",
                "aad_server_app_secret": "test_aad_server_app_secret",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret()

    def test_get_aad_tenant_id(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "aad_tenant_id": None,
            },
        )
        self.assertEqual(ctx_1.get_aad_tenant_id(), None)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            tenant_id="test_aad_tenant_id",
        )
        mc = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_aad_tenant_id(), "test_aad_tenant_id")

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_aad": False,
                "aad_client_app_id": "test_aad_client_app_id",
            },
        )
        profile = Mock(
            get_login_credentials=Mock(
                return_value=(None, None, "test_aad_tenant_id")
            )
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.Profile",
            return_value=profile,
        ):
            self.assertEqual(ctx_2.get_aad_tenant_id(), "test_aad_tenant_id")

    def test_get_aad_admin_group_object_ids(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "aad_admin_group_object_ids": None,
            },
        )
        self.assertEqual(ctx_1.get_aad_admin_group_object_ids(), None)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            admin_group_object_i_ds="test_aad_admin_group_object_ids",
        )
        mc = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_aad_admin_group_object_ids(),
            "test_aad_admin_group_object_ids",
        )

        # custom value
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "aad_admin_group_object_ids": "test_value_1,test_value_2",
            },
        )
        self.assertEqual(
            ctx_2.get_aad_admin_group_object_ids(),
            ["test_value_1", "test_value_2"],
        )

    def test_get_disable_rbac(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "disable_rbac": None,
            },
        )
        self.assertEqual(ctx_1.get_disable_rbac(), None)
        mc = self.models.ManagedCluster(
            location="test_location", enable_rbac=False
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_disable_rbac(), True)

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "disable_rbac": True,
                "enable_azure_rbac": True,
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_disable_rbac()

    def test_get_enable_azure_rbac(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_azure_rbac": False,
            },
        )
        self.assertEqual(ctx_1.get_enable_azure_rbac(), False)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=True,
        )
        mc = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_1
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_azure_rbac(), True)

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {},
        )
        aad_profile_2 = self.models.ManagedClusterAADProfile(
            enable_azure_rbac=True,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            enable_rbac=False,
            aad_profile=aad_profile_2,
        )
        ctx_2.attach_mc(mc_2)
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_azure_rbac()

    def test_get_api_server_authorized_ip_ranges(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {"api_server_authorized_ip_ranges": None},
        )
        self.assertEqual(
            ctx_1.get_api_server_authorized_ip_ranges(),
            [],
        )
        api_server_access_profile = (
            self.models.ManagedClusterAPIServerAccessProfile(
                authorized_ip_ranges=["test_mc_api_server_authorized_ip_ranges"]
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_api_server_authorized_ip_ranges(),
            ["test_mc_api_server_authorized_ip_ranges"],
        )

        # valid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_sku": "standard",
                "api_server_authorized_ip_ranges": "test_ip_range_1 , test_ip_range_2",
            },
        )
        self.assertEqual(
            ctx_2.get_api_server_authorized_ip_ranges(),
            ["test_ip_range_1", "test_ip_range_2"],
        )

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_sku": "basic",
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_api_server_authorized_ip_ranges()

        # invalid parameter
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_4.get_api_server_authorized_ip_ranges()

    def test_get_fqdn_subdomain(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"fqdn_subdomain": None})
        self.assertEqual(ctx_1.get_fqdn_subdomain(), None)
        mc = self.models.ManagedCluster(
            location="test_location", fqdn_subdomain="test_mc_fqdn_subdomain"
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_fqdn_subdomain(), "test_mc_fqdn_subdomain")

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "dns_name_prefix": "test_dns_name_prefix",
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_fqdn_subdomain()

    def test_get_enable_private_cluster(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": False,
            },
        )
        self.assertEqual(ctx_1.get_enable_private_cluster(), False)
        api_server_access_profile = (
            self.models.ManagedClusterAPIServerAccessProfile(
                enable_private_cluster=True,
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_private_cluster(), True)

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "load_balancer_sku": "basic",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_private_cluster()

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_enable_private_cluster()

        # invalid parameter
        ctx_4 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": False,
                "disable_public_fqdn": True,
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_private_cluster()

        # invalid parameter
        ctx_5 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": False,
                "private_dns_zone": "system",
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_5.get_enable_private_cluster()

    def test_get_disable_public_fqdn(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "disable_public_fqdn": False,
            },
        )
        self.assertEqual(ctx_1.get_disable_public_fqdn(), False)
        api_server_access_profile = (
            self.models.ManagedClusterAPIServerAccessProfile(
                enable_private_cluster_public_fqdn=False,
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_1.get_disable_public_fqdn(), True)

    def test_get_private_dns_zone(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "private_dns_zone": None,
            },
        )
        self.assertEqual(ctx_1.get_private_dns_zone(), None)
        api_server_access_profile = (
            self.models.ManagedClusterAPIServerAccessProfile(
                private_dns_zone="test_private_dns_zone",
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_1.get_private_dns_zone(), "test_private_dns_zone"
            )

        # invalid parameter
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "private_dns_zone": "test_private_dns_zone",
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_2.get_private_dns_zone(), "test_private_dns_zone"
            )

        # invalid parameter
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "private_dns_zone": CONST_PRIVATE_DNS_ZONE_SYSTEM,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_3.get_private_dns_zone(), CONST_PRIVATE_DNS_ZONE_SYSTEM
            )


class AKSCreateDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSCreateModels(self.cmd)
        self.client = MockClient()

    def test_init_mc(self):
        dec_1 = AKSCreateDecorator(
            self.cmd, self.client, self.models, {"location": "test_location"}
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.get_subscription_id",
            return_value="test_sub_id",
        ):
            dec_mc = dec_1.init_mc()
        ground_truth_mc = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc, ground_truth_mc)
        self.assertEqual(dec_mc, dec_1.context.mc)

    def test_set_up_agent_pool_profiles(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "nodepool_name": "nodepool1",
                "nodepool_tags": None,
                "nodepool_labels": None,
                "node_count": 3,
                "node_vm_size": "Standard_DS2_v2",
                "vnet_subnet_id": None,
                "ppg": None,
                "zones": None,
                "enable_node_public_ip": False,
                "node_public_ip_prefix_id": None,
                "enable_encryption_at_host": False,
                "enable_ultra_ssd": False,
                "max_pods": 0,
                "node_osdisk_size": 0,
                "node_osdisk_type": None,
                "enable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_agent_pool_profiles(mc_1)
        agent_pool_profile_1 = self.models.ManagedClusterAgentPoolProfile(
            # Must be 12 chars or less before ACS RP adds to it
            name="nodepool1",
            tags=None,
            node_labels=None,
            count=3,
            vm_size="Standard_DS2_v2",
            os_type="Linux",
            vnet_subnet_id=None,
            proximity_placement_group_id=None,
            availability_zones=None,
            enable_node_public_ip=False,
            node_public_ip_prefix_id=None,
            enable_encryption_at_host=False,
            enable_ultra_ssd=False,
            max_pods=None,
            type="VirtualMachineScaleSets",
            mode="System",
            os_disk_size_gb=None,
            os_disk_type=None,
            enable_auto_scaling=False,
            min_count=None,
            max_count=None,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        ground_truth_mc_1.agent_pool_profiles = [agent_pool_profile_1]
        self.assertEqual(
            dec_mc_1.agent_pool_profiles[0],
            ground_truth_mc_1.agent_pool_profiles[0],
        )

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "nodepool_name": "test_np_name1234",
                "nodepool_tags": {"k1": "v1"},
                "nodepool_labels": {"k1": "v1", "k2": "v2"},
                "node_count": 10,
                "node_vm_size": "Standard_DSx_vy",
                "vnet_subnet_id": "test_vnet_subnet_id",
                "ppg": "test_ppg_id",
                "zones": ["tz1", "tz2"],
                "enable_node_public_ip": True,
                "node_public_ip_prefix_id": "test_node_public_ip_prefix_id",
                "enable_encryption_at_host": True,
                "enable_ultra_ssd": True,
                "max_pods": 50,
                "node_osdisk_size": 100,
                "node_osdisk_type": "test_os_disk_type",
                "enable_cluster_autoscaler": True,
                "min_count": 5,
                "max_count": 20,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_agent_pool_profiles(mc_2)
        agent_pool_profile_2 = self.models.ManagedClusterAgentPoolProfile(
            # Must be 12 chars or less before ACS RP adds to it
            name="test_np_name",
            tags={"k1": "v1"},
            node_labels={"k1": "v1", "k2": "v2"},
            count=10,
            vm_size="Standard_DSx_vy",
            os_type="Linux",
            vnet_subnet_id="test_vnet_subnet_id",
            proximity_placement_group_id="test_ppg_id",
            availability_zones=["tz1", "tz2"],
            enable_node_public_ip=True,
            node_public_ip_prefix_id="test_node_public_ip_prefix_id",
            enable_encryption_at_host=True,
            enable_ultra_ssd=True,
            max_pods=50,
            type="VirtualMachineScaleSets",
            mode="System",
            os_disk_size_gb=100,
            os_disk_type="test_os_disk_type",
            enable_auto_scaling=True,
            min_count=5,
            max_count=20,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location")
        ground_truth_mc_2.agent_pool_profiles = [agent_pool_profile_2]
        self.assertEqual(
            dec_mc_2.agent_pool_profiles[0],
            ground_truth_mc_2.agent_pool_profiles[0],
        )

    def test_set_up_linux_profile(self):
        # default value in `aks_create`
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "admin_username": "azureuser",
                "no_ssh_key": False,
                "ssh_key_value": public_key,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_linux_profile(mc_1)

        ssh_config_1 = self.models.ContainerServiceSshConfiguration(
            public_keys=[
                self.models.ContainerServiceSshPublicKey(key_data=public_key)
            ]
        )
        linux_profile_1 = self.models.ContainerServiceLinuxProfile(
            admin_username="azureuser", ssh=ssh_config_1
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location", linux_profile=linux_profile_1
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "admin_username": "test_user",
                "no_ssh_key": True,
                "ssh_key_value": "test_key",
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_linux_profile(mc_2)

        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_windows_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "windows_admin_username": None,
                "windows_admin_password": None,
                "enable_ahub": False,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_windows_profile(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "windows_admin_username": "test_win_admin_name",
                "windows_admin_password": None,
                "enable_ahub": True,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        with patch(
            "azure.cli.command_modules.acs.decorator.prompt_pass",
            return_value="test_win_admin_pd",
        ):
            dec_mc_2 = dec_2.set_up_windows_profile(mc_2)

        windows_profile_2 = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_win_admin_name",
            admin_password="test_win_admin_pd",
            license_type="Windows_Server",
        )

        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location", windows_profile=windows_profile_2
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_service_principal_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": None,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_service_principal_profile(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.set_intermediate(
            "subscription_id", "1234-5678", overwrite_exists=True
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.custom.get_graph_rbac_management_client",
            return_value=None,
        ):
            dec_mc_2 = dec_2.set_up_service_principal_profile(mc_2)

        service_principal_profile_2 = (
            self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_service_principal", secret="test_client_secret"
            )
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_process_add_role_assignment_for_vnet_subnet(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "vnet_subnet_id": None,
                "skip_subnet_role_assignment": False,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.process_add_role_assignment_for_vnet_subnet(mc_1)
        self.assertEqual(
            dec_1.context.get_intermediate(
                "need_post_creation_vnet_permission_granting"
            ),
            False,
        )

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "skip_subnet_role_assignment": False,
                "assign_identity": None,
                "yes": True,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        with patch(
            "azure.cli.command_modules.acs.decorator.subnet_role_assignment_exists",
            return_value=False,
        ):
            dec_2.process_add_role_assignment_for_vnet_subnet(mc_2)
        self.assertEqual(
            dec_2.context.get_intermediate(
                "need_post_creation_vnet_permission_granting"
            ),
            True,
        )

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "skip_subnet_role_assignment": False,
                "assign_identity": None,
            },
        )
        service_principal_profile_3 = (
            self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_service_principal", secret="test_client_secret"
            )
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile_3,
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.subnet_role_assignment_exists",
            return_value=False,
        ), patch(
            "azure.cli.command_modules.acs.decorator._add_role_assignment",
            return_value=True,
        ) as add_role_assignment:
            dec_3.process_add_role_assignment_for_vnet_subnet(mc_3)
        add_role_assignment.assert_called_once_with(
            self.cmd,
            "Network Contributor",
            "test_service_principal",
            scope="test_vnet_subnet_id",
        )
        self.assertEqual(
            dec_3.context.get_intermediate(
                "need_post_creation_vnet_permission_granting"
            ),
            False,
        )

    def test_process_attach_acr(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "attach_acr": None,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.process_attach_acr(mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": True,
                "no_wait": True,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_2.process_attach_acr(mc_2)

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": False,
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(CLIInternalError):
            dec_3.process_attach_acr(mc_3)
        service_principal_profile_3 = (
            self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_service_principal", secret="test_client_secret"
            )
        )
        mc_3.service_principal_profile = service_principal_profile_3
        dec_3.context.attach_mc(mc_3)
        registry = Mock(id="test_registry_id")
        with patch(
            "azure.cli.command_modules.acs.custom.get_resource_by_name",
            return_value=registry,
        ), patch(
            "azure.cli.command_modules.acs.custom._ensure_aks_acr_role_assignment"
        ) as ensure_assignment:
            dec_3.process_attach_acr(mc_3)
        ensure_assignment.assert_called_once_with(
            self.cmd, "test_service_principal", "test_registry_id", False
        )

    def test_set_up_network_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": None,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": None,
                "load_balancer_idle_timeout": None,
                "outbound_type": None,
                "network_plugin": None,
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "docker_bridge_cidr": None,
                "network_policy": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_network_profile(mc_1)

        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            network_plugin="kubenet",  # default value in SDK
            pod_cidr="10.244.0.0/16",  # default value in SDK
            service_cidr="10.0.0.0/16",  # default value in SDK
            dns_service_ip="10.0.0.10",  # default value in SDK
            docker_bridge_cidr="172.17.0.1/16",  # default value in SDK
            load_balancer_sku="standard",
            outbound_type="loadBalancer",
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile_1
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": 3,
                "load_balancer_outbound_ips": "test_ip_1,test_ip_2",
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": 5,
                "load_balancer_idle_timeout": None,
                "outbound_type": None,
                "network_plugin": "kubenet",
                "pod_cidr": "10.246.0.0/16",
                "service_cidr": None,
                "dns_service_ip": None,
                "docker_bridge_cidr": None,
                "network_policy": None,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_network_profile(mc_2)

        load_balancer_profile_2 = self.models.lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )(
            managed_outbound_i_ps=self.models.lb_models.get(
                "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
            )(count=3),
            outbound_i_ps=self.models.lb_models.get(
                "ManagedClusterLoadBalancerProfileOutboundIPs"
            )(
                public_i_ps=[
                    self.models.lb_models.get("ResourceReference")(
                        id="test_ip_1"
                    ),
                    self.models.lb_models.get("ResourceReference")(
                        id="test_ip_2"
                    ),
                ]
            ),
            allocated_outbound_ports=5,
        )

        network_profile_2 = self.models.ContainerServiceNetworkProfile(
            network_plugin="kubenet",
            pod_cidr="10.246.0.0/16",
            service_cidr=None,  # overwritten to None
            dns_service_ip=None,  # overwritten to None
            docker_bridge_cidr=None,  # overwritten to None
            load_balancer_sku="standard",
            outbound_type="loadBalancer",
            load_balancer_profile=load_balancer_profile_2,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile_2
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "load_balancer_sku": "basic",
                "load_balancer_managed_outbound_ip_count": 5,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": "test_ip_prefix_1,test_ip_prefix_2",
                "load_balancer_outbound_ports": None,
                "load_balancer_idle_timeout": 20,
                "outbound_type": None,
                "network_plugin": None,
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "docker_bridge_cidr": None,
                "network_policy": None,
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_mc_3 = dec_3.set_up_network_profile(mc_3)

        network_profile_3 = self.models.ContainerServiceNetworkProfile(
            network_plugin="kubenet",  # default value in SDK
            pod_cidr="10.244.0.0/16",  # default value in SDK
            service_cidr="10.0.0.0/16",  # default value in SDK
            dns_service_ip="10.0.0.10",  # default value in SDK
            docker_bridge_cidr="172.17.0.1/16",  # default value in SDK
            load_balancer_sku="basic",
            outbound_type="loadBalancer",
            load_balancer_profile=None,  # profile dropped when lb sku is basic
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile_3
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_set_up_addon_profiles(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_addons": None,
                "workspace_resource_id": None,
                "aci_subnet_name": None,
                "appgw_name": None,
                "appgw_subnet_cidr": None,
                "appgw_id": None,
                "appgw_subnet_id": None,
                "appgw_watch_namespace": None,
                "enable_sgxquotehelper": False,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_addon_profiles(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location", addon_profiles={}
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)
        self.assertEqual(dec_1.context.get_intermediate("monitoring"), None)
        self.assertEqual(
            dec_1.context.get_intermediate("enable_virtual_node"), None
        )
        self.assertEqual(
            dec_1.context.get_intermediate("ingress_appgw_addon_enabled"), None
        )

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "enable_addons": "http_application_routing,monitoring,virtual-node,kube-dashboard,azure-policy,ingress-appgw,confcom",
                "workspace_resource_id": "test_workspace_resource_id",
                "aci_subnet_name": "test_aci_subnet_name",
                "appgw_name": "test_appgw_name",
                "appgw_subnet_cidr": "test_appgw_subnet_cidr",
                "appgw_id": "test_appgw_id",
                "appgw_subnet_id": "test_appgw_subnet_id",
                "appgw_watch_namespace": "test_appgw_watch_namespace",
                "enable_sgxquotehelper": True,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        with patch(
            "azure.cli.command_modules.acs.decorator._ensure_container_insights_for_monitoring",
            return_value=None,
        ):
            dec_mc_2 = dec_2.set_up_addon_profiles(mc_2)

        addon_profiles_2 = {
            CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
            ),
            CONST_MONITORING_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: "/test_workspace_resource_id"
                },
            ),
            CONST_VIRTUAL_NODE_ADDON_NAME
            + dec_2.context.get_virtual_node_addon_os_type(): self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_VIRTUAL_NODE_SUBNET_NAME: "test_aci_subnet_name"},
            ),
            CONST_KUBE_DASHBOARD_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
            ),
            CONST_AZURE_POLICY_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
            ),
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME: "test_appgw_name",
                    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID: "test_appgw_id",
                    CONST_INGRESS_APPGW_SUBNET_ID: "test_appgw_subnet_id",
                    CONST_INGRESS_APPGW_SUBNET_CIDR: "test_appgw_subnet_cidr",
                    CONST_INGRESS_APPGW_WATCH_NAMESPACE: "test_appgw_watch_namespace",
                },
            ),
            CONST_CONFCOM_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "true"},
            ),
        }
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location", addon_profiles=addon_profiles_2
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)
        self.assertEqual(dec_2.context.get_intermediate("monitoring"), True)
        self.assertEqual(
            dec_2.context.get_intermediate("enable_virtual_node"), True
        )
        self.assertEqual(
            dec_2.context.get_intermediate("ingress_appgw_addon_enabled"), True
        )

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_addons": "test_enable_addons",
                "workspace_resource_id": None,
                "aci_subnet_name": None,
                "appgw_name": None,
                "appgw_subnet_cidr": None,
                "appgw_id": None,
                "appgw_subnet_id": None,
                "appgw_watch_namespace": None,
                "enable_sgxquotehelper": False,
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(InvalidArgumentValueError):
            dec_3.set_up_addon_profiles(mc_3)

        # custom value
        dec_4 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_addons": "",
                "workspace_resource_id": "test_workspace_resource_id",
                "aci_subnet_name": None,
                "appgw_name": None,
                "appgw_subnet_cidr": None,
                "appgw_id": None,
                "appgw_subnet_id": None,
                "appgw_watch_namespace": None,
                "enable_sgxquotehelper": False,
            },
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(RequiredArgumentMissingError):
            dec_4.set_up_addon_profiles(mc_4)

        # custom value
        dec_5 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_addons": "virtual-node",
                "workspace_resource_id": None,
                "aci_subnet_name": None,
                "appgw_name": None,
                "appgw_subnet_cidr": None,
                "appgw_id": None,
                "appgw_subnet_id": None,
                "appgw_watch_namespace": None,
                "enable_sgxquotehelper": False,
            },
        )
        mc_5 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(RequiredArgumentMissingError):
            dec_5.set_up_addon_profiles(mc_5)

    def test_set_up_aad_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_aad": False,
                "aad_client_app_id": None,
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": None,
                "enable_azure_rbac": False,
                "disable_rbac": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_aad_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_aad": True,
                "aad_client_app_id": None,
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": "test_value_1test_value_2",
                "enable_azure_rbac": True,
                "disable_rbac": None,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_aad_profile(mc_2)

        aad_profile_2 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=True,
            admin_group_object_i_ds=["test_value_1test_value_2"],
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_2
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_aad": False,
                "aad_client_app_id": "test_aad_client_app_id",
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": None,
                "enable_azure_rbac": False,
                "disable_rbac": None,
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        profile = Mock(
            get_login_credentials=Mock(
                return_value=(None, None, "test_aad_tenant_id")
            )
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.Profile",
            return_value=profile,
        ):
            dec_mc_3 = dec_3.set_up_aad_profile(mc_3)

        aad_profile_3 = self.models.ManagedClusterAADProfile(
            client_app_id="test_aad_client_app_id",
            tenant_id="test_aad_tenant_id",
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location", aad_profile=aad_profile_3
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # custom value
        dec_4 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_aad": True,
                "aad_client_app_id": None,
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": None,
                "enable_azure_rbac": True,
                "disable_rbac": True,
            },
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_4.set_up_aad_profile(mc_4)

    def test_set_up_api_server_access_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": False,
                "disable_public_fqdn": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_mc_1 = dec_1.set_up_api_server_access_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "api_server_authorized_ip_ranges": "test_ip_1, test_ip_2",
                "enable_private_cluster": False,
                "disable_public_fqdn": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_api_server_access_profile(mc_2)

        api_server_access_profile_2 = (
            self.models.ManagedClusterAPIServerAccessProfile(
                authorized_ip_ranges=["test_ip_1", "test_ip_2"],
                enable_private_cluster=False,
            )
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": True,
                "disable_public_fqdn": True,
                "private_dns_zone": None,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_mc_3 = dec_3.set_up_api_server_access_profile(mc_3)

        api_server_access_profile_3 = (
            self.models.ManagedClusterAPIServerAccessProfile(
                authorized_ip_ranges=[],
                enable_private_cluster=True,
                enable_private_cluster_public_fqdn=False,
            )
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_3,
            fqdn_subdomain="test_fqdn_subdomain",
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # invalid value
        dec_4 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                "enable_private_cluster": True,
                "disable_public_fqdn": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
            },
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_4.set_up_api_server_access_profile(mc_4)

        # invalid value
        dec_5 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": True,
                "disable_public_fqdn": False,
                "private_dns_zone": CONST_PRIVATE_DNS_ZONE_SYSTEM,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        mc_5 = self.models.ManagedCluster(location="test_location")
        with self.assertRaises(InvalidArgumentValueError):
            dec_5.set_up_api_server_access_profile(mc_5)
