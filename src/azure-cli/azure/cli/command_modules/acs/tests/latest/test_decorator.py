# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
from re import T
from knack import CLI
from knack.util import CLIError
import tempfile
import unittest
from unittest.mock import patch

from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import (
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
    InvalidArgumentValueError,
)
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from azure.cli.core._config import ENV_VAR_PREFIX

from azure.cli.command_modules.acs.decorator import (
    AKSCreateModels,
    AKSCreateContext,
    AKSCreateDecorator,
)


MOCK_CLI_CONFIG_DIR = tempfile.mkdtemp()
MOCK_CLI_ENV_VAR_PREFIX = "MOCK_" + ENV_VAR_PREFIX


class MockClient(object):
    def __init__(self):
        pass


class MockCLI(CLI):
    def __init__(self):
        super(MockCLI, self).__init__(
            cli_name="mock_cli",
            config_dir=MOCK_CLI_CONFIG_DIR,
            config_env_var_prefix=MOCK_CLI_ENV_VAR_PREFIX,
        )
        self.cloud = get_active_cloud(self)


class MockCmd(object):
    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.cmd = AzCliCommand(AzCommandsLoader(cli_ctx), "mock-cmd", None)

    def supported_api_version(
        self,
        resource_type=None,
        min_api=None,
        max_api=None,
        operation_group=None,
        parameter_name=None,
    ):
        return self.cmd.supported_api_version(
            resource_type=resource_type,
            min_api=min_api,
            max_api=max_api,
            operation_group=operation_group,
            parameter_name=parameter_name,
        )

    def get_models(self, *attr_args, **kwargs):
        return self.cmd.get_models(*attr_args, **kwargs)


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

    def test_get_ssh_key_value(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())

        # default
        ctx_1 = AKSCreateContext(self.cmd, {"ssh_key_value": public_key})
        self.assertEqual(
            ctx_1.get_ssh_key_value(enable_validation=True), public_key
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
        self.assertEqual(ctx_1.get_ssh_key_value(), "test_mc_ssh_key_value")

        # invalid key with validation
        ctx_2 = AKSCreateContext(
            self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": False}
        )
        with self.assertRaises(CLIError):
            ctx_2.get_ssh_key_value(enable_validation=True)

        # invalid key & valid parameter with validation
        ctx_3 = AKSCreateContext(
            self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": True}
        )
        self.assertEqual(
            ctx_3.get_ssh_key_value(enable_validation=True), "fake-key"
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
            ctx_2.get_dns_name_prefix(enable_validation=True)

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

    def test_get_no_ssh_key(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"no_ssh_key": False})
        self.assertEqual(ctx_1.get_no_ssh_key(), False)

        # invalid key & valid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": True}
        )
        self.assertEqual(
            ctx_2.get_ssh_key_value(enable_validation=True), "fake-key"
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

    def test_get_load_balancer_sku(self):
        # default & dynamic completion
        ctx_1 = AKSCreateContext(
            self.cmd,
            {"load_balancer_sku": None, "kubernetes_version": ""},
        )
        self.assertEqual(ctx_1.get_load_balancer_sku(), "standard")
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="test_mc_load_balancer_sku"
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
            ctx_3.get_load_balancer_sku(enable_validation=True)

    def test_get_api_server_authorized_ip_ranges(self):
        # TODO: need update, raw input should be str, output should be List[str]
        # default
        ctx_1 = AKSCreateContext(
            self.cmd,
            {
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges"
            },
        )
        self.assertEqual(
            ctx_1.get_api_server_authorized_ip_ranges(),
            "test_api_server_authorized_ip_ranges",
        )
        api_server_access_profile = (
            self.models.ManagedClusterAPIServerAccessProfile(
                authorized_ip_ranges="test_mc_api_server_authorized_ip_ranges"
            )
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_api_server_authorized_ip_ranges(),
            "test_mc_api_server_authorized_ip_ranges",
        )

        # valid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "load_balancer_sku": "standard",
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
            },
        )
        self.assertEqual(
            ctx_2.get_api_server_authorized_ip_ranges(enable_validation=True),
            "test_api_server_authorized_ip_ranges",
        )

    def test_get_fqdn_subdomain(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"fqdn_subdomain": None})
        self.assertEqual(ctx_1.get_fqdn_subdomain(), None)
        mc = self.models.ManagedCluster(
            location="test_location", fqdn_subdomain="test_mc_fqdn_subdomain"
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_fqdn_subdomain(), "test_mc_fqdn_subdomain")

        # valid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "dns_name_prefix": None,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        self.assertEqual(
            ctx_2.get_fqdn_subdomain(enable_validation=True),
            "test_fqdn_subdomain",
        )

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
        self.assertEqual(
            ctx_2.get_nodepool_name(enable_trim=True), "test_nodepoo"
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(
            ctx_2.get_nodepool_name(enable_trim=True), "test_nodepool_name"
        )

        # dynamic completion
        ctx_3 = AKSCreateContext(self.cmd, {"nodepool_name": None})
        self.assertEqual(ctx_3.get_nodepool_name(enable_trim=True), "nodepool1")

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

    def test_get_node_count(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"node_count": 3})
        self.assertEqual(ctx_1.get_node_count(), 3)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", count=20
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_node_count(), 20)

        # valid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": True,
                "min_count": 3,
                "max_count": 10,
            },
        )
        self.assertEqual(ctx_2.get_node_count(enable_validation=True), 5)

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

    def test_get_enable_cluster_autoscaler(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"enable_cluster_autoscaler": False})
        self.assertEqual(ctx_1.get_enable_cluster_autoscaler(), False)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", enable_auto_scaling=True
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_cluster_autoscaler(), True)

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
            ctx_2.get_enable_cluster_autoscaler(enable_validation=True)

    def test_get_min_count(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"min_count": None})
        self.assertEqual(ctx_1.get_min_count(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", min_count=5
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_min_count(), 5)

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": False,
                "min_count": 3,
                "max_count": None,
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_min_count(enable_validation=True)

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
            ctx_3.get_min_count(enable_validation=True)

    def test_get_max_count(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"max_count": None})
        self.assertEqual(ctx_1.get_max_count(), None)
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_nodepool_name", max_count=10
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_max_count(), 10)

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": 10,
            },
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_max_count(enable_validation=True)

        # invalid parameter with validation
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "node_count": 5,
                "enable_cluster_autoscaler": True,
                "min_count": 7,
                "max_count": 10,
            },
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_max_count(enable_validation=True)

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

        # custom value
        ctx_2 = AKSCreateContext(self.cmd, {"enable_ahub": True})
        self.assertEqual(ctx_2.get_enable_ahub(), True)

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
