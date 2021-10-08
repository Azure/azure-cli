# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import requests
import unittest
from unittest.mock import Mock, call, patch

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
    DecoratorMode,
)
from azure.cli.command_modules.acs.decorator import (
    AKSContext,
    AKSCreateDecorator,
    AKSModels,
    AKSUpdateDecorator,
    check_is_msi_cluster,
    format_parameter_name_to_option_name,
    safe_list_get,
    safe_lower,
    validate_counts_in_autoscaler,
    validate_decorator_mode,
)
from azure.cli.command_modules.acs.tests.latest.mocks import (
    MockCLI,
    MockClient,
    MockCmd,
)
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    NoTTYError,
    RequiredArgumentMissingError,
    UnknownError,
)
from azure.cli.core.profiles import ResourceType
from knack.prompting import NoTTYException
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError


class DecoratorFunctionsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSModels(self.cmd)

    def test_format_parameter_name_to_option_name(self):
        self.assertEqual(
            format_parameter_name_to_option_name("abc_xyz"), "--abc-xyz"
        )

    def test_safe_list_get(self):
        list_1 = [1, 2, 3]
        self.assertEqual(safe_list_get(list_1, 0), 1)
        self.assertEqual(safe_list_get(list_1, 10), None)

        tuple_1 = (1, 2, 3)
        self.assertEqual(safe_list_get(tuple_1, 0), None)

    def test_safe_lower(self):
        self.assertEqual(safe_lower(None), None)
        self.assertEqual(safe_lower("ABC"), "abc")

    def test_validate_decorator_mode(self):
        self.assertEqual(validate_decorator_mode(DecoratorMode.CREATE), True)
        self.assertEqual(validate_decorator_mode(DecoratorMode.UPDATE), True)
        self.assertEqual(validate_decorator_mode(DecoratorMode), False)
        self.assertEqual(validate_decorator_mode(1), False)
        self.assertEqual(validate_decorator_mode("1"), False)
        self.assertEqual(validate_decorator_mode(True), False)
        self.assertEqual(validate_decorator_mode({}), False)

    def test_check_is_msi_cluster(self):
        self.assertEqual(check_is_msi_cluster(None), False)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
        )
        self.assertEqual(check_is_msi_cluster(mc_1), True)

        mc_2 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="UserAssigned"),
        )
        self.assertEqual(check_is_msi_cluster(mc_2), True)

        mc_3 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="Test"),
        )
        self.assertEqual(check_is_msi_cluster(mc_3), False)

    def test_validate_counts_in_autoscaler(self):
        # default
        validate_counts_in_autoscaler(
            3, False, None, None, DecoratorMode.CREATE
        )

        # custom value
        validate_counts_in_autoscaler(5, True, 1, 10, DecoratorMode.CREATE)

        # fail on min_count/max_count not specified
        with self.assertRaises(RequiredArgumentMissingError):
            validate_counts_in_autoscaler(
                5, True, None, None, DecoratorMode.CREATE
            )

        # fail on min_count > max_count
        with self.assertRaises(InvalidArgumentValueError):
            validate_counts_in_autoscaler(5, True, 3, 1, DecoratorMode.CREATE)

        # fail on node_count < min_count in create mode
        with self.assertRaises(InvalidArgumentValueError):
            validate_counts_in_autoscaler(5, True, 7, 10, DecoratorMode.CREATE)

        # skip node_count check in update mode
        validate_counts_in_autoscaler(5, True, 7, 10, DecoratorMode.UPDATE)
        validate_counts_in_autoscaler(None, True, 7, 10, DecoratorMode.UPDATE)

        # fail on enable_cluster_autoscaler not specified
        with self.assertRaises(RequiredArgumentMissingError):
            validate_counts_in_autoscaler(
                5, False, 3, None, DecoratorMode.UPDATE
            )


class AKSModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)

    def test_models(self):
        models = AKSModels(self.cmd)

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
            models.ManagedCluster, getattr(module, "ManagedCluster")
        )
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
            models.ManagedServiceIdentityUserAssignedIdentitiesValue,
            getattr(
                module,
                "ManagedServiceIdentityUserAssignedIdentitiesValue",
            ),
        )
        self.assertEqual(
            models.ManagedClusterAddonProfile,
            getattr(module, "ManagedClusterAddonProfile"),
        )
        self.assertEqual(
            models.ManagedClusterAPIServerAccessProfile,
            getattr(module, "ManagedClusterAPIServerAccessProfile"),
        )
        self.assertEqual(
            models.ExtendedLocation, getattr(module, "ExtendedLocation")
        )
        self.assertEqual(
            models.ExtendedLocationTypes,
            getattr(module, "ExtendedLocationTypes"),
        )
        self.assertEqual(
            models.ManagedClusterAPIServerAccessProfile,
            getattr(module, "ManagedClusterAPIServerAccessProfile"),
        )
        # not directly used
        self.assertEqual(
            models.ManagedClusterPropertiesAutoScalerProfile,
            getattr(module, "ManagedClusterPropertiesAutoScalerProfile"),
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


class AKSContextTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSModels(self.cmd)

    def test__init__(self):
        # fail on not passing dictionary-like parameters
        with self.assertRaises(CLIInternalError):
            AKSContext(self.cmd, [], decorator_mode=DecoratorMode.CREATE)
        # fail on not passing decorator_mode with Enum type DecoratorMode
        with self.assertRaises(CLIInternalError):
            AKSContext(self.cmd, {}, decorator_mode=1)

    def test_attach_mc(self):
        ctx_1 = AKSContext(self.cmd, {}, decorator_mode=DecoratorMode.CREATE)
        mc = self.models.ManagedCluster(location="test_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.mc, mc)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_mc(mc)

    def test_get_intermediate(self):
        ctx_1 = AKSContext(self.cmd, {}, decorator_mode=DecoratorMode.CREATE)
        self.assertEqual(
            ctx_1.get_intermediate("fake-intermediate", "not found"),
            "not found",
        )

    def test_set_intermediate(self):
        ctx_1 = AKSContext(self.cmd, {}, decorator_mode=DecoratorMode.CREATE)
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
        ctx_1 = AKSContext(self.cmd, {}, decorator_mode=DecoratorMode.CREATE)
        ctx_1.set_intermediate("test-intermediate", "test-intermediate-value")
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.remove_intermediate("test-intermediate")
        self.assertEqual(ctx_1.get_intermediate("test-intermediate"), None)

    def test_get_subscription_id(self):
        ctx_1 = AKSContext(self.cmd, {}, decorator_mode=DecoratorMode.CREATE)
        ctx_1.set_intermediate("subscription_id", "test_subscription_id")
        self.assertEqual(
            ctx_1.get_subscription_id(),
            "test_subscription_id",
        )
        ctx_1.remove_intermediate("subscription_id")
        self.assertEqual(ctx_1.get_intermediate("subscription_id"), None)
        mock_profile = Mock(
            get_subscription_id=Mock(return_value="test_subscription_id")
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.Profile",
            return_value=mock_profile,
        ):
            self.assertEqual(
                ctx_1.get_subscription_id(),
                "test_subscription_id",
            )
            mock_profile.get_subscription_id.assert_called_once()

    def test_get_resource_group_name(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"resource_group_name": "test_rg_name"},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_resource_group_name(), "test_rg_name")

    def test_get_name(self):
        # default
        ctx_1 = AKSContext(
            self.cmd, {"name": "test_name"}, decorator_mode=DecoratorMode.CREATE
        )
        self.assertEqual(ctx_1.get_name(), "test_name")

    def test_get_location(self):
        # default & dynamic completion
        ctx_1 = AKSContext(
            self.cmd, {"location": None}, decorator_mode=DecoratorMode.CREATE
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ):
            self.assertEqual(ctx_1._get_location(read_only=True), None)
            self.assertEqual(ctx_1.get_location(), "test_location")
        mc = self.models.ManagedCluster(location="test_mc_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_location(), "test_mc_location")

    def test_get_ssh_key_value_and_no_ssh_key(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"ssh_key_value": public_key, "no_ssh_key": False},
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on invalid key
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_1.get_ssh_key_value_and_no_ssh_key(),
                "test_mc_ssh_key_value",
            )

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {"ssh_key_value": "fake-key", "no_ssh_key": False},
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid key
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_ssh_key_value_and_no_ssh_key()

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {"ssh_key_value": "fake-key", "no_ssh_key": True},
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            self.assertEqual(
                ctx_3.get_ssh_key_value_and_no_ssh_key(),
                "test_mc_ssh_key_value",
            )

    def test_get_dns_name_prefix(self):
        # default & dynamic completion
        ctx_1 = AKSContext(
            self.cmd,
            {
                "dns_name_prefix": None,
                "fqdn_subdomain": None,
                "name": "1234_test_name",
                "resource_group_name": "test_rg_name",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        ctx_1.set_intermediate("subscription_id", "1234-5678")
        self.assertEqual(ctx_1._get_dns_name_prefix(read_only=True), None)
        self.assertEqual(
            ctx_1.get_dns_name_prefix(), "a1234testn-testrgname-1234-5"
        )
        mc = self.models.ManagedCluster(
            location="test_location", dns_prefix="test_mc_dns_name_prefix"
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_dns_name_prefix(), "test_mc_dns_name_prefix")

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "dns_name_prefix": "test_dns_name_prefix",
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive dns_name_prefix and fqdn_subdomain
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_dns_name_prefix()

    def test_get_kubernetes_version(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"kubernetes_version": ""},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"vm_set_type": None, "kubernetes_version": ""},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1._get_vm_set_type(read_only=True), None)
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
        ctx_2 = AKSContext(
            self.cmd,
            {"vm_set_type": "availabilityset", "kubernetes_version": ""},
            decorator_mode=DecoratorMode.CREATE,
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

        # custom value & dynamic completion
        ctx_3 = AKSContext(
            self.cmd,
            {"vm_set_type": None, "kubernetes_version": "1.12.8"},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_vm_set_type(), "AvailabilitySet")

    def test_get_nodepool_name(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"nodepool_name": "nodepool1"},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_2 = AKSContext(
            self.cmd,
            {"nodepool_name": "test_nodepool_name"},
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_3 = AKSContext(
            self.cmd,
            {"nodepool_name": None},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_nodepool_name(), "nodepool1")

    def test_get_nodepool_tags(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"nodepool_tags": None},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"nodepool_labels": None},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"node_vm_size": "Standard_DS2_v2"},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"vnet_subnet_id": None},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd, {"ppg": None}, decorator_mode=DecoratorMode.CREATE
        )
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
        ctx_1 = AKSContext(
            self.cmd, {"zones": None}, decorator_mode=DecoratorMode.CREATE
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"enable_node_public_ip": False},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"node_public_ip_prefix_id": None},
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {"enable_encryption_at_host": False},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"enable_ultra_ssd": False},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd, {"max_pods": 0}, decorator_mode=DecoratorMode.CREATE
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"node_osdisk_size": 0},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"node_osdisk_type": None},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "node_count": 3,
                "enable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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

    def test_get_update_enable_disable_cluster_autoscaler_and_min_max_count(
        self,
    ):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=3,
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_update_enable_disable_cluster_autoscaler_and_min_max_count(),
            (False, False, False, None, None),
        )

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "update_cluster_autoscaler": True,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        agent_pool_profile_2 = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=3,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[agent_pool_profile_2, agent_pool_profile_2],
        )
        ctx_2.attach_mc(mc_2)
        # fail on multi-agent pool
        with self.assertRaises(ArgumentUsageError):
            ctx_2.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": True,
                "disable_cluster_autoscaler": True,
                "min_count": None,
                "max_count": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        agent_pool_profile_3 = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=3,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile_3]
        )
        ctx_3.attach_mc(mc_3)
        # fail on mutually exclusive update_cluster_autoscaler, enable_cluster_autoscaler and disable_cluster_autoscaler
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_4 = AKSContext(
            self.cmd,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": True,
                "disable_cluster_autoscaler": False,
                "min_count": 1,
                "max_count": 5,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        agent_pool_profile_4 = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=3,
            enable_auto_scaling=True,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile_4]
        )
        ctx_4.attach_mc(mc_4)
        # fail on cluster autoscaler already enabled
        with self.assertRaises(SystemExit):
            ctx_4.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_5 = AKSContext(
            self.cmd,
            {
                "update_cluster_autoscaler": True,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": 1,
                "max_count": 5,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        agent_pool_profile_5 = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=3,
            enable_auto_scaling=False,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile_5]
        )
        ctx_5.attach_mc(mc_5)
        # fail on cluster autoscaler not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_5.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_6 = AKSContext(
            self.cmd,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": True,
                "min_count": None,
                "max_count": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )

        agent_pool_profile_6 = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name",
            count=3,
            enable_auto_scaling=False,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile_6]
        )
        ctx_6.attach_mc(mc_6)
        # fail on cluster autoscaler already disabled
        with self.assertRaises(SystemExit):
            ctx_6.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

    def test_get_admin_username(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"admin_username": "azureuser"},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {"windows_admin_username": None, "windows_admin_password": None},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_1.get_windows_admin_username_and_password(), (None, None)
        )
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin",
        )
        mc = self.models.ManagedCluster(
            location="test_location", windows_profile=windows_profile
        )
        ctx_1.attach_mc(mc)
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            self.assertEqual(
                ctx_1.get_windows_admin_username_and_password(),
                ("test_mc_win_admin", "test_mc_win_admin_password"),
            )

        # dynamic completion
        ctx_2 = AKSContext(
            self.cmd,
            {
                "windows_admin_username": None,
                "windows_admin_password": "test_win_admin_pd",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on no tty
        with patch(
            "knack.prompting.verify_is_a_tty",
            side_effect=NoTTYException,
        ), self.assertRaises(NoTTYError):
            ctx_2.get_windows_admin_username_and_password()
        with patch(
            "azure.cli.command_modules.acs.decorator.prompt",
            return_value="test_win_admin_name",
        ):
            self.assertEqual(
                ctx_2._get_windows_admin_username_and_password(read_only=True),
                (None, "test_win_admin_pd"),
            )
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
        ctx_3 = AKSContext(
            self.cmd,
            {
                "windows_admin_username": "test_win_admin_name",
                "windows_admin_password": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on no tty
        with patch(
            "knack.prompting.verify_is_a_tty",
            side_effect=NoTTYException,
        ), self.assertRaises(NoTTYError):
            ctx_3.get_windows_admin_username_and_password()
        with patch(
            "azure.cli.command_modules.acs.decorator.prompt_pass",
            return_value="test_win_admin_pd",
        ):
            self.assertEqual(
                ctx_3.get_windows_admin_username_and_password(),
                ("test_win_admin_name", "test_win_admin_pd"),
            )

    def test_get_enable_ahub(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"enable_ahub": False},
            decorator_mode=DecoratorMode.CREATE,
        )
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_1.get_service_principal_and_client_secret(),
            (None, None),
        )

        # dynamic completion
        ctx_2 = AKSContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_3 = AKSContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": "test_client_secret",
            },
            decorator_mode=DecoratorMode.CREATE,
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
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile,
        )
        ctx_3.attach_mc(mc)
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            self.assertEqual(
                ctx_3.get_service_principal_and_client_secret(),
                ("test_mc_service_principal", "test_mc_client_secret"),
            )

        # dynamic completion
        ctx_4 = AKSContext(
            self.cmd,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
            # fail on client_secret not specified
            with self.assertRaises(CLIError):
                ctx_4.get_service_principal_and_client_secret()

    def test_get_enable_managed_identity(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_managed_identity(), True)
        identity = self.models.ManagedClusterIdentity()
        mc = self.models.ManagedCluster(
            location="test_location", identity=identity
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_managed_identity(), False)

        # dynamic completion
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_enable_managed_identity(), False)

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_managed_identity": False,
                "assign_identity": "test_assign_identity",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_managed_identity()

    def test_get_skip_subnet_role_assignment(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"skip_subnet_role_assignment": False},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_skip_subnet_role_assignment(), False)

    def test_get_assign_identity(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"assign_identity": None},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_assign_identity(), None)
        user_assigned_identity = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity = self.models.ManagedClusterIdentity(
            type="UserAssigned", user_assigned_identities=user_assigned_identity
        )
        mc = self.models.ManagedCluster(
            location="test_location", identity=identity
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_assign_identity(), "test_assign_identity")

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_managed_identity": False,
                "assign_identity": "test_assign_identity",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_assign_identity()

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {
                "assign_identity": None,
                "assign_kubelet_identity": "test_assign_kubelet_identity",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on assign_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_assign_identity()

    def test_get_identity_by_msi_client(self):
        # custom value
        ctx_1 = AKSContext(
            self.cmd,
            {
                "assign_identity": "/subscriptions/1234/resourcegroups/test_rg/providers/microsoft.managedidentity/userassignedidentities/5678",
                "enable_managed_identity": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        identity_obj = Mock(client_id="1234-5678", principal_id="8765-4321")
        msi_client = Mock(
            user_assigned_identities=Mock(get=Mock(return_value=identity_obj))
        )
        with patch(
            "azure.cli.command_modules.acs.custom.get_msi_client",
            return_value=msi_client,
        ) as get_msi_client:
            identity = ctx_1.get_identity_by_msi_client(
                ctx_1.get_assign_identity()
            )
            self.assertEqual(identity.client_id, "1234-5678")
            self.assertEqual(identity.principal_id, "8765-4321")
            get_msi_client.assert_called_once_with(self.cmd.cli_ctx, "1234")
            msi_client.user_assigned_identities.get.assert_called_once_with(
                resource_group_name="test_rg", resource_name="5678"
            )

    def test_get_user_assigned_identity_client_id(self):
        ctx_1 = AKSContext(
            self.cmd,
            {"assign_identity": None},
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on assign_identity not provided
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_user_assigned_identity_client_id()

        # custom value
        identity_obj = Mock(
            client_id="test_client_id",
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.AKSContext.get_identity_by_msi_client",
            return_value=identity_obj,
        ):
            ctx_2 = AKSContext(
                self.cmd,
                {
                    "assign_identity": "test_assign_identity",
                    "enable_managed_identity": True,
                },
                decorator_mode=DecoratorMode.CREATE,
            )
            self.assertEqual(
                ctx_2.get_user_assigned_identity_client_id(), "test_client_id"
            )

    def test_get_user_assigned_identity_object_id(self):
        ctx_1 = AKSContext(
            self.cmd,
            {"assign_identity": None},
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on assign_identity not provided
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_user_assigned_identity_object_id()

        # custom value
        identity_obj = Mock(
            principal_id="test_principal_id",
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.AKSContext.get_identity_by_msi_client",
            return_value=identity_obj,
        ):
            ctx_2 = AKSContext(
                self.cmd,
                {
                    "assign_identity": "test_assign_identity",
                    "enable_managed_identity": True,
                },
                decorator_mode=DecoratorMode.CREATE,
            )
            self.assertEqual(
                ctx_2.get_user_assigned_identity_object_id(),
                "test_principal_id",
            )

    def test_get_yes(self):
        # default
        ctx_1 = AKSContext(
            self.cmd, {"yes": False}, decorator_mode=DecoratorMode.CREATE
        )
        self.assertEqual(ctx_1.get_yes(), False)

    def test_get_no_wait(self):
        # default
        ctx_1 = AKSContext(
            self.cmd, {"no_wait": False}, decorator_mode=DecoratorMode.CREATE
        )
        self.assertEqual(ctx_1.get_no_wait(), False)

    def test_get_attach_acr(self):
        # default
        ctx_1 = AKSContext(
            self.cmd, {"attach_acr": None}, decorator_mode=DecoratorMode.CREATE
        )
        self.assertEqual(ctx_1.get_attach_acr(), None)

        # invalid parameter
        ctx_2 = AKSContext(
            self.cmd,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": True,
                "no_wait": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_managed_identity and no_wait
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_attach_acr()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": False,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on service_principal/client_secret not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_attach_acr()

        # custom value (update mode)
        ctx_4 = AKSContext(
            self.cmd,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": True,
                "no_wait": True,
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        ctx_4.get_attach_acr()

    def test_get_detach_acr(self):
        # default
        ctx_1 = AKSContext(
            self.cmd, {"detach_acr": None}, decorator_mode=DecoratorMode.UPDATE
        )
        self.assertEqual(ctx_1.get_detach_acr(), None)

    def test_get_load_balancer_sku(self):
        # default & dynamic completion
        ctx_1 = AKSContext(
            self.cmd,
            {"load_balancer_sku": None, "kubernetes_version": ""},
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {"load_balancer_sku": None, "kubernetes_version": "1.12.0"},
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_3 = AKSContext(
            self.cmd,
            {
                "load_balancer_sku": "basic",
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when api_server_authorized_ip_ranges is assigned
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_load_balancer_sku()

        # invalid parameter with validation
        ctx_4 = AKSContext(
            self.cmd,
            {
                "load_balancer_sku": "basic",
                "enable_private_cluster": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when enable_private_cluster is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_load_balancer_sku()

        # custom value (lower case)
        ctx_5 = AKSContext(
            self.cmd,
            {"load_balancer_sku": "STANDARD"},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_5.get_load_balancer_sku(), "standard")

    def test_get_load_balancer_managed_outbound_ip_count(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "load_balancer_managed_outbound_ip_count": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "load_balancer_outbound_ips": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "load_balancer_outbound_ip_prefixes": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "load_balancer_outbound_ports": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "load_balancer_idle_timeout": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "outbound_type": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1._get_outbound_type(read_only=True), None)
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                "load_balancer_sku": "basic",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when outbound_type is CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_outbound_type()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on vnet_subnet_id not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_outbound_type()

        # invalid parameter
        ctx_4 = AKSContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                "vnet_subnet_id": "test_vnet_subnet_id",
                "load_balancer_managed_outbound_ip_count": 10,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive outbound_type and managed_outbound_ip_count/outbound_ips/outbound_ip_prefixes of
        # load balancer
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_4.get_outbound_type()

        # invalid parameter
        ctx_5 = AKSContext(
            self.cmd,
            {
                "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                "vnet_subnet_id": "test_vnet_subnet_id",
            },
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on mutually exclusive outbound_type and managed_outbound_ip_count/outbound_ips/outbound_ip_prefixes of
        # load balancer
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_5.get_outbound_type(
                load_balancer_profile=load_balancer_profile,
            )

    def test_get_network_plugin(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "network_plugin": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "network_plugin": "azure",
                "pod_cidr": "test_pod_cidr",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid network_plugin (azure) when pod_cidr is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_network_plugin()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "pod_cidr": "test_pod_cidr",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on network_plugin not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_network_plugin()

    def test_get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
        self,
    ):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "docker_bridge_address": None,
                "network_policy": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "network_plugin": "azure",
                "pod_cidr": "test_pod_cidr",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid network_plugin (azure) when pod_cidr is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "pod_cidr": "test_pod_cidr",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on network_plugin not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

        # invalid parameter
        ctx_4 = AKSContext(
            self.cmd,
            {
                "service_cidr": "test_service_cidr",
                "dns_service_ip": "test_dns_service_ip",
                "docker_bridge_address": "test_docker_bridge_address",
                "network_policy": "test_network_policy",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on network_plugin not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

    def test_get_enable_addons(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_addons": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_addons(), [])

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_addons": "http_application_routing,monitoring",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_enable_addons(),
            ["http_application_routing", "monitoring"],
        )

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_addons": "test_addon_1,test_addon_2",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid enable_addons
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_enable_addons()

        # invalid parameter
        ctx_4 = AKSContext(
            self.cmd,
            {
                "enable_addons": "test_addon_1,test_addon_2,test_addon_1,test_addon_2",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid/duplicate enable_addons
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_addons()

        # invalid parameter
        ctx_5 = AKSContext(
            self.cmd,
            {
                "workspace_resource_id": "/test_workspace_resource_id",
                "enable_addons": "",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on enable_addons (monitoring) not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_5.get_enable_addons()

        # invalid parameter
        ctx_6 = AKSContext(
            self.cmd,
            {
                "enable_addons": "virtual-node",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on aci_subnet_name/vnet_subnet_id not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_6.get_enable_addons()

    def test_get_workspace_resource_id(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "workspace_resource_id": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on enable_addons (monitoring) not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_workspace_resource_id()

        # custom value & dynamic completion
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_addons": "monitoring",
                "workspace_resource_id": "test_workspace_resource_id/",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_workspace_resource_id(), "/test_workspace_resource_id"
        )

        # dynamic completion
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_addons": "monitoring",
                "resource_group_name": "test_rg_name",
                "workspace_resource_id": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(self.cmd, {}, decorator_mode=DecoratorMode.CREATE)
        self.assertEqual(ctx_1.get_virtual_node_addon_os_type(), "Linux")

    def test_get_aci_subnet_name(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "aci_subnet_name": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "appgw_name": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "appgw_subnet_cidr": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "appgw_id": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "appgw_subnet_id": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "appgw_watch_namespace": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_sgxquotehelper": False,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        self.assertEqual(ctx_1.get_enable_sgxquotehelper(), True)

    def test_get_enable_aad(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_aad": False,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_aad": True,
                "aad_client_app_id": "test_aad_client_app_id",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_aad and aad_client_app_id/aad_server_app_id/aad_server_app_secret
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_aad()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_aad": False,
                "enable_azure_rbac": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on enable_aad not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_aad()

    def test_get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(
        self,
    ):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "aad_client_app_id": None,
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_aad": True,
                "aad_client_app_id": "test_aad_client_app_id",
                "aad_server_app_id": "test_aad_server_app_id",
                "aad_server_app_secret": "test_aad_server_app_secret",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_aad and aad_client_app_id/aad_server_app_id/aad_server_app_secret
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret()

    def test_get_aad_tenant_id(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "aad_tenant_id": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1._get_aad_tenant_id(read_only=True), None)
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_aad": False,
                "aad_client_app_id": "test_aad_client_app_id",
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_1 = AKSContext(
            self.cmd,
            {
                "aad_admin_group_object_ids": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "aad_admin_group_object_ids": "test_value_1,test_value_2",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_aad_admin_group_object_ids(),
            ["test_value_1", "test_value_2"],
        )

    def test_get_disable_rbac(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "disable_rbac": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_rbac(), None)
        mc = self.models.ManagedCluster(
            location="test_location", enable_rbac=False
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_disable_rbac(), True)

        # invalid parameter
        ctx_2 = AKSContext(
            self.cmd,
            {
                "disable_rbac": True,
                "enable_azure_rbac": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive disable_rbac and enable_azure_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_disable_rbac()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "disable_rbac": True,
                "enable_rbac": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive disable_rbac and enable_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_disable_rbac()

    def test_get_enable_rbac(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_rbac": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_rbac(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            enable_rbac=True,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_rbac(), True)

        # invalid parameter
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_rbac": True,
                "disable_rbac": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive disable_rbac and enable_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_rbac()

    def test_get_enable_azure_rbac(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_azure_rbac": False,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {},
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on mutually exclusive enable_azure_rbac and disable_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_azure_rbac()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_azure_rbac": True,
                "enable_aad": False,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on enable_aad not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_azure_rbac()

    def test_get_api_server_authorized_ip_ranges(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"api_server_authorized_ip_ranges": None},
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "load_balancer_sku": "standard",
                "api_server_authorized_ip_ranges": "test_ip_range_1 , test_ip_range_2",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_api_server_authorized_ip_ranges(),
            ["test_ip_range_1", "test_ip_range_2"],
        )

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "load_balancer_sku": "basic",
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when api_server_authorized_ip_ranges is assigned
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_api_server_authorized_ip_ranges()

        # invalid parameter
        ctx_4 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_private_cluster and api_server_authorized_ip_ranges
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_4.get_api_server_authorized_ip_ranges()

        # default (update mode)
        ctx_5 = AKSContext(
            self.cmd,
            {
                "api_server_authorized_ip_ranges": None,
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_5.get_api_server_authorized_ip_ranges(), None)

        # custom value (update mode)
        ctx_6 = AKSContext(
            self.cmd,
            {
                "api_server_authorized_ip_ranges": "",
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_6.get_api_server_authorized_ip_ranges(), [])

    def test_get_fqdn_subdomain(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {"fqdn_subdomain": None},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_fqdn_subdomain(), None)
        mc = self.models.ManagedCluster(
            location="test_location", fqdn_subdomain="test_mc_fqdn_subdomain"
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_fqdn_subdomain(), "test_mc_fqdn_subdomain")

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "dns_name_prefix": "test_dns_name_prefix",
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutually exclusive dns_name_prefix and fqdn_subdomain
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_fqdn_subdomain()

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "fqdn_subdomain": "test_fqdn_subdomain",
                "private_dns_zone": "system",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on fqdn_subdomain specified and private_dns_zone equals to CONST_PRIVATE_DNS_ZONE_SYSTEM
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_fqdn_subdomain()

        # custom value
        ctx_4 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "fqdn_subdomain": "test_fqdn_subdomain",
                "private_dns_zone": "test_private_dns_zone",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid private_dns_zone when fqdn_subdomain is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_fqdn_subdomain()

    def test_get_enable_private_cluster(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": False,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "load_balancer_sku": "basic",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when enable_private_cluster is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_enable_private_cluster()

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on mutially exclusive enable_private_cluster and api_server_authorized_ip_ranges
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_enable_private_cluster()

        # invalid parameter
        ctx_4 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": False,
                "disable_public_fqdn": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on disable_public_fqdn specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_private_cluster()

        # invalid parameter
        ctx_5 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": False,
                "private_dns_zone": "system",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on private_dns_zone specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_5.get_enable_private_cluster()

    def test_get_disable_public_fqdn(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "disable_public_fqdn": False,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on disable_public_fqdn specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_1.get_disable_public_fqdn(), True)

    def test_get_private_dns_zone(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "private_dns_zone": None,
            },
            decorator_mode=DecoratorMode.CREATE,
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
        # fail on private_dns_zone specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_1.get_private_dns_zone(), "test_private_dns_zone"
            )

        # invalid parameter
        ctx_2 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "private_dns_zone": "test_private_dns_zone",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid private_dns_zone
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_2.get_private_dns_zone(), "test_private_dns_zone"
            )

        # invalid parameter
        ctx_3 = AKSContext(
            self.cmd,
            {
                "enable_private_cluster": True,
                "private_dns_zone": CONST_PRIVATE_DNS_ZONE_SYSTEM,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid private_dns_zone when fqdn_subdomain is specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_3.get_private_dns_zone(), CONST_PRIVATE_DNS_ZONE_SYSTEM
            )

    def test_get_assign_kubelet_identity(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "assign_identity": "test_assign_identity",
                "assign_kubelet_identity": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_assign_kubelet_identity(), None)
        identity_profile = {
            "kubeletidentity": self.models.UserAssignedIdentity(
                resource_id="test_assign_kubelet_identity",
            )
        }
        mc = self.models.ManagedCluster(
            location="test_location",
            identity_profile=identity_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_assign_kubelet_identity(), "test_assign_kubelet_identity"
        )

        # invalid parameter
        ctx_2 = AKSContext(
            self.cmd,
            {
                "assign_identity": None,
                "assign_kubelet_identity": "test_assign_kubelet_identity",
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on assign_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            self.assertEqual(
                ctx_2.get_assign_kubelet_identity(),
                "test_assign_kubelet_identity",
            )

    def test_get_auto_upgrade_channel(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "auto_upgrade_channel": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_auto_upgrade_channel(), None)
        auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile(
            upgrade_channel="test_auto_upgrade_channel"
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            auto_upgrade_profile=auto_upgrade_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_auto_upgrade_channel(), "test_auto_upgrade_channel"
        )

    def test_get_node_osdisk_diskencryptionset_id(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "node_osdisk_diskencryptionset_id": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_node_osdisk_diskencryptionset_id(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            disk_encryption_set_id="test_node_osdisk_diskencryptionset_id",
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_node_osdisk_diskencryptionset_id(),
            "test_node_osdisk_diskencryptionset_id",
        )

    def test_get_cluster_autoscaler_profile(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "cluster_autoscaler_profile": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_cluster_autoscaler_profile(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile="test_cluster_autoscaler_profile",
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_cluster_autoscaler_profile(),
            "test_cluster_autoscaler_profile",
        )

        # custom value (update mode)
        ctx_2 = AKSContext(
            self.cmd,
            {
                "cluster_autoscaler_profile": {
                    "scan-interval": "30s",
                    "expander": "least-waste",
                },
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        auto_scaler_profile_2 = (
            self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
                expander="random",
            )
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile=auto_scaler_profile_2,
        )
        ctx_2.attach_mc(mc_2)
        self.assertEqual(
            ctx_2.get_cluster_autoscaler_profile(),
            {
                "additional_properties": {},
                "balance_similar_node_groups": None,
                "expander": "least-waste",
                "max_empty_bulk_delete": None,
                "max_graceful_termination_sec": None,
                "max_node_provision_time": None,
                "max_total_unready_percentage": None,
                "new_pod_scale_up_delay": None,
                "ok_total_unready_count": None,
                "scan_interval": "30s",
                "scale_down_delay_after_add": None,
                "scale_down_delay_after_delete": None,
                "scale_down_delay_after_failure": None,
                "scale_down_unneeded_time": None,
                "scale_down_unready_time": None,
                "scale_down_utilization_threshold": None,
                "skip_nodes_with_local_storage": None,
                "skip_nodes_with_system_pods": None,
            },
        )

    def test_get_uptime_sla(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "uptime_sla": False,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_uptime_sla(), False)
        sku = self.models.ManagedClusterSKU(
            name="Basic",
            tier="Paid",
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            sku=sku,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_uptime_sla(), True)

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "uptime_sla": False,
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        sku_2 = self.models.ManagedClusterSKU(
            name="Basic",
            tier="Paid",
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=sku_2,
        )
        ctx_2.attach_mc(mc_2)
        self.assertEqual(ctx_2.get_uptime_sla(), False)

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {
                "uptime_sla": True,
                "no_uptime_sla": True,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        sku_3 = self.models.ManagedClusterSKU(
            name="Basic",
            tier="Free",
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            sku=sku_3,
        )
        ctx_3.attach_mc(mc_3)
        self.assertEqual(ctx_3.get_uptime_sla(), False)

    def test_get_no_uptime_sla(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "no_uptime_sla": False,
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_no_uptime_sla(), False)
        sku = self.models.ManagedClusterSKU(
            name="Basic",
            tier="Paid",
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            sku=sku,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_no_uptime_sla(), False)

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "uptime_sla": True,
                "no_uptime_sla": True,
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        sku_2 = self.models.ManagedClusterSKU(
            name="Basic",
            tier="Free",
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=sku_2,
        )
        ctx_2.attach_mc(mc_2)
        # fail on mutually exclusive uptime_sla and no_uptime_sla
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_uptime_sla()
        # fail on mutually exclusive uptime_sla and no_uptime_sla
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_no_uptime_sla()

    def test_get_tags(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "tags": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_tags(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            tags={},
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_tags(), {})

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {
                "tags": {"xyz": "100"},
            },
            decorator_mode=DecoratorMode.UPDATE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            tags={},
        )
        ctx_2.attach_mc(mc_2)
        self.assertEqual(ctx_2.get_tags(), {"xyz": "100"})

    def test_get_edge_zone(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {
                "tags": None,
            },
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_edge_zone(), None)
        extended_location = self.models.ExtendedLocation(
            name="test_edge_zone",
            type=self.models.ExtendedLocationTypes.EDGE_ZONE,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            extended_location=extended_location,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_edge_zone(), "test_edge_zone")

    def test_get_client_id_from_identity_or_sp_profile(self):
        # default
        ctx_1 = AKSContext(
            self.cmd,
            {},
            decorator_mode=DecoratorMode.UPDATE,
        )
        # fail on no mc attached and no client id found
        with self.assertRaises(UnknownError):
            ctx_1.get_client_id_from_identity_or_sp_profile()

        # custom value
        ctx_2 = AKSContext(
            self.cmd,
            {},
            decorator_mode=DecoratorMode.UPDATE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
        )
        ctx_2.attach_mc(mc_2)
        # fail on kubelet identity not found
        with self.assertRaises(UnknownError):
            ctx_2.get_client_id_from_identity_or_sp_profile()

        # custom value
        ctx_3 = AKSContext(
            self.cmd,
            {},
            decorator_mode=DecoratorMode.UPDATE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="UserAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id"
                )
            },
        )
        ctx_3.attach_mc(mc_3)
        self.assertEqual(
            ctx_3.get_client_id_from_identity_or_sp_profile(), "test_client_id"
        )

        # custom value
        ctx_4 = AKSContext(
            self.cmd,
            {},
            decorator_mode=DecoratorMode.UPDATE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_client_id"
            ),
        )
        ctx_4.attach_mc(mc_4)
        self.assertEqual(
            ctx_4.get_client_id_from_identity_or_sp_profile(), "test_client_id"
        )


class AKSCreateDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSModels(self.cmd)
        self.client = MockClient()

    def test_init_mc(self):
        mock_profile = Mock(
            get_subscription_id=Mock(return_value="1234-5678-9012")
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.Profile",
            return_value=mock_profile,
        ):
            dec_1 = AKSCreateDecorator(
                self.cmd,
                self.client,
                self.models,
                {
                    "name": "test_cluster",
                    "resource_group_name": "test_rg_name",
                    "location": "test_location",
                },
            )
            dec_mc = dec_1.init_mc()
            ground_truth_mc = self.models.ManagedCluster(
                location="test_location",
                dns_prefix="testcluste-testrgname-1234-5",
                enable_rbac=True,
            )
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_agent_pool_profiles(None)
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
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

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
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_linux_profile(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())
        # default value in `aks_create`
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_linux_profile(None)
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_windows_profile(None)
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_service_principal_profile(None)
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.process_add_role_assignment_for_vnet_subnet(None)
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
                "yes": False,
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        with patch(
            "azure.cli.command_modules.acs.decorator.subnet_role_assignment_exists",
            return_value=False,
        ), patch(
            "azure.cli.command_modules.acs.decorator.prompt_y_n",
            return_value=False,
        ):
            dec_3.process_add_role_assignment_for_vnet_subnet(mc_3)
        self.assertEqual(
            dec_3.context.get_intermediate(
                "need_post_creation_vnet_permission_granting"
            ),
            None,
        )

        # custom value
        dec_4 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "skip_subnet_role_assignment": False,
                "assign_identity": None,
            },
        )
        service_principal_profile_4 = (
            self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_service_principal", secret="test_client_secret"
            )
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile_4,
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.subnet_role_assignment_exists",
            return_value=False,
        ), patch(
            "azure.cli.command_modules.acs.decorator._add_role_assignment",
            return_value=True,
        ) as add_role_assignment:
            dec_4.process_add_role_assignment_for_vnet_subnet(mc_4)
        add_role_assignment.assert_called_once_with(
            self.cmd,
            "Network Contributor",
            "test_service_principal",
            scope="test_vnet_subnet_id",
        )
        self.assertEqual(
            dec_4.context.get_intermediate(
                "need_post_creation_vnet_permission_granting"
            ),
            False,
        )

        # custom value
        identity_obj = Mock(
            client_id="test_client_id",
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.AKSContext.get_identity_by_msi_client",
            return_value=identity_obj,
        ):
            dec_5 = AKSCreateDecorator(
                self.cmd,
                self.client,
                self.models,
                {
                    "enable_managed_identity": True,
                    "vnet_subnet_id": "test_vnet_subnet_id",
                    "skip_subnet_role_assignment": False,
                    "assign_identity": "test_assign_identity",
                },
            )
            mc_5 = self.models.ManagedCluster(
                location="test_location",
            )
            with patch(
                "azure.cli.command_modules.acs.decorator.subnet_role_assignment_exists",
                return_value=False,
            ), patch(
                "azure.cli.command_modules.acs.decorator._add_role_assignment",
                return_value=False,
            ) as add_role_assignment:
                dec_5.process_add_role_assignment_for_vnet_subnet(mc_5)
            add_role_assignment.assert_called_once_with(
                self.cmd,
                "Network Contributor",
                "test_client_id",
                scope="test_vnet_subnet_id",
            )
            self.assertEqual(
                dec_5.context.get_intermediate(
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.process_attach_acr(None)
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
        # fail on mutually exclusive attach_acr, enable_managed_identity and no_wait
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
        # fail on service_principal/client_secret not specified
        with self.assertRaises(RequiredArgumentMissingError):
            dec_3.process_attach_acr(mc_3)
        service_principal_profile_3 = (
            self.models.ManagedClusterServicePrincipalProfile(
                client_id="test_service_principal", secret="test_client_secret"
            )
        )
        mc_3.service_principal_profile = service_principal_profile_3
        dec_3.context.attach_mc(mc_3)
        dec_3.context.set_intermediate(
            "subscription_id", "test_subscription_id"
        )
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_network_profile(None)
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_addon_profiles(None)
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
        # fail on invalid enable_addons
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
        # fail on enable_addons (monitoring) not specified
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
        # fail on aci_subnet_name/vnet_subnet_id not specified
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_aad_profile(None)
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
        # fail on mutually exclusive enable_azure_rbac and disable_rbac
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
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_api_server_access_profile(None)
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
                enable_private_cluster=None,
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
        # fail on mutually exclusive enable_private_cluster and api_server_authorized_ip_ranges
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
        # fail on invalid private_dns_zone when fqdn_subdomain is specified
        with self.assertRaises(InvalidArgumentValueError):
            dec_5.set_up_api_server_access_profile(mc_5)

    def test_set_up_identity(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_managed_identity": False,
                "assign_identity": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_identity(None)
        dec_mc_1 = dec_1.set_up_identity(mc_1)
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
                "enable_managed_identity": True,
                "assign_identity": None,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_identity(mc_2)

        identity_2 = self.models.ManagedClusterIdentity(
            type="SystemAssigned",
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_managed_identity": True,
                "assign_identity": "test_assign_identity",
            },
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_mc_3 = dec_3.set_up_identity(mc_3)

        user_assigned_identity_3 = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity_3 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=user_assigned_identity_3,
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_3,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # invalid value
        dec_4 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "enable_managed_identity": False,
                "assign_identity": "test_assign_identity",
            },
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            dec_4.set_up_identity(mc_4)

    def test_set_up_identity_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "assign_identity": None,
                "assign_kubelet_identity": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_identity_profile(None)
        dec_mc_1 = dec_1.set_up_identity_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        identity_obj_1 = Mock(
            client_id="test_assign_kubelet_identity_client_id",
            principal_id="test_assign_kubelet_identity_object_id",
        )
        identity_obj_2 = Mock(
            client_id="test_assign_identity_client_id",
            principal_id="test_assign_identity_object_id",
        )
        mock_ensure_method = Mock()
        with patch(
            "azure.cli.command_modules.acs.decorator.AKSContext.get_identity_by_msi_client",
            side_effect=[identity_obj_1, identity_obj_2],
        ), patch(
            "azure.cli.command_modules.acs.decorator._ensure_cluster_identity_permission_on_kubelet_identity"
        ) as mock_ensure_method:
            dec_2 = AKSCreateDecorator(
                self.cmd,
                self.client,
                self.models,
                {
                    "enable_managed_identity": True,
                    "assign_identity": "test_assign_identity",
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                },
            )
            mc_2 = self.models.ManagedCluster(location="test_location")
            dec_mc_2 = dec_2.set_up_identity_profile(mc_2)

            identity_profile_2 = {
                "kubeletidentity": self.models.UserAssignedIdentity(
                    resource_id="test_assign_kubelet_identity",
                    client_id="test_assign_kubelet_identity_client_id",
                    object_id="test_assign_kubelet_identity_object_id",
                )
            }
            ground_truth_mc_2 = self.models.ManagedCluster(
                location="test_location",
                identity_profile=identity_profile_2,
            )
            self.assertEqual(dec_mc_2, ground_truth_mc_2)
            mock_ensure_method.assert_called_once_with(
                self.cmd,
                "test_assign_identity_object_id",
                "test_assign_kubelet_identity",
            )

    def test_set_up_auto_upgrade_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "auto_upgrade_channel": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_auto_upgrade_profile(None)
        dec_mc_1 = dec_1.set_up_auto_upgrade_profile(mc_1)
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
                "auto_upgrade_channel": "test_auto_upgrade_channel",
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_auto_upgrade_profile(mc_2)

        auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile(
            upgrade_channel="test_auto_upgrade_channel",
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_upgrade_profile=auto_upgrade_profile,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_auto_scaler_profile(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "cluster_autoscaler_profile": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_auto_scaler_profile(None)
        dec_mc_1 = dec_1.set_up_auto_scaler_profile(mc_1)
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
                "cluster_autoscaler_profile": "test_cluster_autoscaler_profile",
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_auto_scaler_profile(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile="test_cluster_autoscaler_profile",
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_sku(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "uptime_sla": False,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_sku(None)
        dec_mc_1 = dec_1.set_up_sku(mc_1)
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
                "uptime_sla": True,
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_sku(mc_2)
        sku = self.models.ManagedClusterSKU(
            name="Basic",
            tier="Paid",
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=sku,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_extended_location(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "edge_zone": None,
            },
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_extended_location(None)
        dec_mc_1 = dec_1.set_up_extended_location(mc_1)
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
                "edge_zone": "test_edge_zone",
            },
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_mc_2 = dec_2.set_up_extended_location(mc_2)
        extended_location = self.models.ExtendedLocation(
            name="test_edge_zone",
            type=self.models.ExtendedLocationTypes.EDGE_ZONE,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            extended_location=extended_location,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_build_custom_headers(self):
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "service_principal": None,
                "client_secret": None,
            },
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.build_custom_headers(None)
        dec_1.build_custom_headers(mc_1)
        self.assertEqual(
            dec_1.context.get_intermediate("custom_headers"),
            None,
        )

        # custom value
        dec_2 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "name": "test_name",
                "resource_group_name": "test_rg_name",
                "location": "test_location",
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
        )
        dec_2.context.set_intermediate("subscription_id", "1234-5678")
        mc_2 = self.models.ManagedCluster(location="test_location")
        with patch(
            "azure.cli.command_modules.acs.custom.get_graph_rbac_management_client"
        ):
            mc_2 = dec_2.set_up_service_principal_profile(mc_2)
        dec_2.build_custom_headers(mc_2)
        self.assertEqual(
            dec_2.context.get_intermediate("custom_headers"),
            {"Ocp-Aad-Session-Key": None},
        )

    def test_construct_default_mc_profile(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())
        # default value in `aks_create`
        dec_1 = AKSCreateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "resource_group_name": "test_rg_name",
                "name": "test_name",
                "ssh_key_value": public_key,
                "dns_name_prefix": None,
                "location": None,
                "admin_username": "azureuser",
                "windows_admin_username": None,
                "windows_admin_password": None,
                "enable_ahub": False,
                "kubernetes_version": "",
                "node_vm_size": "Standard_DS2_v2",
                "node_osdisk_type": None,
                "node_osdisk_size": 0,
                "node_osdisk_diskencryptionset_id": None,
                "node_count": 3,
                "nodepool_name": "nodepool1",
                "nodepool_tags": None,
                "nodepool_labels": None,
                "service_principal": None,
                "client_secret": None,
                "no_ssh_key": False,
                "disable_rbac": None,
                "enable_rbac": None,
                "vm_set_type": None,
                "skip_subnet_role_assignment": False,
                "os_sku": None,
                "enable_cluster_autoscaler": False,
                "cluster_autoscaler_profile": None,
                "network_plugin": None,
                "network_policy": None,
                "uptime_sla": False,
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "docker_bridge_address": None,
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": None,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": None,
                "load_balancer_idle_timeout": None,
                "outbound_type": None,
                "auto_upgrade_channel": None,
                "enable_addons": None,
                "workspace_resource_id": None,
                "vnet_subnet_id": None,
                "ppg": None,
                "max_pods": 0,
                "min_count": None,
                "max_count": None,
                "aad_client_app_id": None,
                "aad_server_app_id": None,
                "aad_server_app_secret": None,
                "aad_tenant_id": None,
                "tags": None,
                "zones": None,
                "enable_node_public_ip": False,
                "node_public_ip_prefix_id": None,
                "generate_ssh_keys": False,
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
                "disable_public_fqdn": False,
                "enable_managed_identity": True,
                "assign_identity": None,
                "attach_acr": None,
                "enable_aad": False,
                "aad_admin_group_object_ids": None,
                "aci_subnet_name": None,
                "appgw_name": None,
                "appgw_subnet_cidr": None,
                "appgw_id": None,
                "appgw_subnet_id": None,
                "appgw_watch_namespace": None,
                "enable_sgxquotehelper": False,
                "enable_encryption_at_host": False,
                "assign_kubelet_identity": None,
                "enable_ultra_ssd": False,
                "edge_zone": None,
                "disable_local_accounts": False,
                "no_wait": False,
                "yes": False,
                "enable_azure_rbac": False,
            },
        )

        mock_profile = Mock(
            get_subscription_id=Mock(return_value="1234-5678-9012")
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.decorator.Profile",
            return_value=mock_profile,
        ):
            dec_mc_1 = dec_1.construct_default_mc_profile()

        agent_pool_profile_1 = self.models.ManagedClusterAgentPoolProfile(
            # Must be 12 chars or less before ACS RP adds to it
            name="nodepool1",
            # tags=None,
            # node_labels=None,
            count=3,
            vm_size="Standard_DS2_v2",
            os_type="Linux",
            enable_node_public_ip=False,
            enable_encryption_at_host=False,
            enable_ultra_ssd=False,
            type="VirtualMachineScaleSets",
            mode="System",
            enable_auto_scaling=False,
        )
        ssh_config_1 = self.models.ContainerServiceSshConfiguration(
            public_keys=[
                self.models.ContainerServiceSshPublicKey(key_data=public_key)
            ]
        )
        linux_profile_1 = self.models.ContainerServiceLinuxProfile(
            admin_username="azureuser", ssh=ssh_config_1
        )
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="standard",
        )
        identity_1 = self.models.ManagedClusterIdentity(type="SystemAssigned")
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            dns_prefix="testname-testrgname-1234-5",
            kubernetes_version="",
            addon_profiles={},
            enable_rbac=True,
            agent_pool_profiles=[agent_pool_profile_1],
            linux_profile=linux_profile_1,
            network_profile=network_profile_1,
            identity=identity_1,
            disable_local_accounts=False,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_create_mc(self):
        # default value in `aks_create`
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1 = AKSCreateDecorator(self.cmd, self.client, self.models, {})
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.create_mc(None)
        mock_profile = Mock(
            get_subscription_id=Mock(return_value="test_subscription_id")
        )
        resp = requests.Response()
        resp.status_code = 500
        err = CloudError(resp)
        err.message = "not found in Active Directory tenant"
        # fail on mock CloudError
        with self.assertRaises(CloudError), patch("time.sleep",), patch(
            "azure.cli.command_modules.acs.decorator.Profile",
            return_value=mock_profile,
        ), patch(
            "azure.cli.command_modules.acs.decorator._put_managed_cluster_ensuring_permission",
            side_effect=err,
        ):
            dec_1.create_mc(mc_1)

    def test_get_disable_local_accounts(self):
        ctx_1 = AKSContext(
            self.cmd,
            {"disable_local_accounts": False},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_local_accounts(), False)
        ctx_2 = AKSContext(
            self.cmd,
            {"disable_local_accounts": True},
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_disable_local_accounts(), True)


class AKSUpdateDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSModels(self.cmd)
        self.client = MockClient()

    def test_check_raw_parameters(self):
        # default value in `aks_create`
        dec_1 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {},
        )
        # fail on no updated parameter provided
        with self.assertRaises(RequiredArgumentMissingError):
            dec_1.check_raw_parameters()

        # custom value
        dec_2 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "cluster_autoscaler_profile": "",
                "api_server_authorized_ip_ranges": "",
            },
        )
        dec_2.check_raw_parameters()

    def test_fetch_mc(self):
        mock_mc = self.models.ManagedCluster(
            location="test_location",
        )
        self.client.get = Mock(return_value=mock_mc)
        dec_1 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "name": "test_cluster",
                "resource_group_name": "test_rg_name",
            },
        )
        dec_mc = dec_1.fetch_mc()
        ground_truth_mc = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc, ground_truth_mc)
        self.assertEqual(dec_mc, dec_1.context.mc)
        self.client.get.assert_called_once_with("test_rg_name", "test_cluster")

    def test_update_tags(self):
        # default value in `aks_create`
        dec_1 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "tags": None,
            },
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            tags={"abc": "xyz"},
        )
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_tags(None)
        dec_mc_1 = dec_1.update_tags(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            tags={"abc": "xyz"},
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom_value
        dec_2 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "tags": {},
            },
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            tags={"abc": "xyz"},
        )
        dec_2.context.attach_mc(mc_2)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_2.update_tags(None)
        dec_mc_2 = dec_2.update_tags(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            tags={},
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_update_auto_scaler_profile(self):
        # default value in `aks_update`
        dec_1 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
                "cluster_autoscaler_profile": None,
            },
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[
                self.models.ManagedClusterAgentPoolProfile(name="nodepool1")
            ],
        )
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_auto_scaler_profile(None)
        dec_mc_1 = dec_1.update_auto_scaler_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[
                self.models.ManagedClusterAgentPoolProfile(name="nodepool1")
            ],
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "update_cluster_autoscaler": True,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": 3,
                "max_count": 10,
                "cluster_autoscaler_profile": {},
            },
        )
        agent_pool_profile_2 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            count=3,
            enable_auto_scaling=True,
            min_count=1,
            max_count=5,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[agent_pool_profile_2],
            auto_scaler_profile=self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
            ),
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_auto_scaler_profile(mc_2)
        ground_truth_agent_pool_profile_2 = (
            self.models.ManagedClusterAgentPoolProfile(
                name="nodepool1",
                count=3,
                enable_auto_scaling=True,
                min_count=3,
                max_count=10,
            )
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[ground_truth_agent_pool_profile_2],
            auto_scaler_profile={},
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": True,
                "min_count": None,
                "max_count": None,
                "cluster_autoscaler_profile": None,
            },
        )
        agent_pool_profile_3 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            count=3,
            enable_auto_scaling=True,
            min_count=1,
            max_count=5,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[agent_pool_profile_3],
            auto_scaler_profile=self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
            ),
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_auto_scaler_profile(mc_3)
        ground_truth_agent_pool_profile_3 = (
            self.models.ManagedClusterAgentPoolProfile(
                name="nodepool1",
                count=3,
                enable_auto_scaling=False,
                min_count=None,
                max_count=None,
            )
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[ground_truth_agent_pool_profile_3],
            auto_scaler_profile=self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
            ),
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_process_attach_detach_acr(self):
        # default value in `aks_update`
        dec_1 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "attach_acr": None,
                "detach_acr": None,
            },
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id",
                )
            },
        )
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate(
            "subscription_id", "test_subscription_id"
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.process_attach_detach_acr(None)
        dec_1.process_attach_detach_acr(mc_1)

        # custom value
        dec_2 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "attach_acr": "test_attach_acr",
                "detach_acr": "test_detach_acr",
            },
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id",
                )
            },
        )
        dec_2.context.attach_mc(mc_2)
        dec_2.context.set_intermediate(
            "subscription_id", "test_subscription_id"
        )
        with patch(
            "azure.cli.command_modules.acs.decorator._ensure_aks_acr"
        ) as ensure_acr:
            dec_2.process_attach_detach_acr(mc_2)
            ensure_acr.assert_has_calls(
                [
                    call(
                        self.cmd,
                        client_id="test_client_id",
                        acr_name_or_id="test_attach_acr",
                        subscription_id="test_subscription_id",
                    ),
                    call(
                        self.cmd,
                        client_id="test_client_id",
                        acr_name_or_id="test_detach_acr",
                        subscription_id="test_subscription_id",
                        detach=True,
                    )
                ]
            )

    def test_update_sku(self):
        # default value in `aks_update`
        dec_1 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "uptime_sla": False,
                "no_uptime_sla": False,
            },
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Free",
            )
        )
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_sku(None)
        dec_mc_1 = dec_1.update_sku(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Free",
            )
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "uptime_sla": True,
                "no_uptime_sla": True,
            },
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Free",
            )
        )
        dec_2.context.attach_mc(mc_2)
        # fail on mutually exclusive uptime_sla and no_uptime_sla
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_2.update_sku(mc_2)

        # custom value
        dec_3 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "uptime_sla": False,
                "no_uptime_sla": True,
            },
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Paid",
            )
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_sku(mc_3)
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Free",
            )
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # custom value
        dec_4 = AKSUpdateDecorator(
            self.cmd,
            self.client,
            self.models,
            {
                "uptime_sla": True,
                "no_uptime_sla": False,
            },
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Free",
            )
        )
        dec_4.context.attach_mc(mc_4)
        dec_mc_4 = dec_4.update_sku(mc_4)
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Basic",
                tier="Paid",
            )
        )
        self.assertEqual(dec_mc_4, ground_truth_mc_4)

    def test_update_default_mc_profile(self):
        pass

    def test_update_mc(self):
        pass
