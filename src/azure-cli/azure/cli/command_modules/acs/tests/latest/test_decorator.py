# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
from knack import CLI
from knack.util import CLIError
import tempfile
import unittest
from unittest.mock import patch

from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from azure.cli.core._config import ENV_VAR_PREFIX

from azure.cli.command_modules.acs.decorator import (
    AKSCreateModels,
    AKSCreateParameters,
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


class AKSCreateParametersTestCase(unittest.TestCase):
    def test_parameters(self):
        data = {"key1": "value1", "key2": 200}
        param = AKSCreateParameters(data)
        self.assertEqual(param.key1, "value1")
        self.assertEqual(getattr(param, "key2"), 200)


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

        # empty string
        ctx_2 = AKSCreateContext(self.cmd, {"resource_group_name": ""})
        self.assertEqual(ctx_2.get_resource_group_name(), "")

    def test_get_name(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"name": "test_name"})
        self.assertEqual(ctx_1.get_name(), "test_name")

        # empty string
        ctx_2 = AKSCreateContext(self.cmd, {"name": ""})
        self.assertEqual(ctx_2.get_name(), "")

    def test_get_ssh_key_value(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())

        # valid key
        ctx_1 = AKSCreateContext(
            self.cmd, {"ssh_key_value": public_key, "no_ssh_key": False}
        )
        self.assertEqual(
            ctx_1.get_ssh_key_value(enable_validation=True), public_key
        )

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

        # invalid key without validation
        ctx_4 = AKSCreateContext(self.cmd, {"ssh_key_value": "fake-key"})
        self.assertEqual(ctx_4.get_ssh_key_value(), "fake-key")

    def test_get_dns_name_prefix(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd, {"dns_name_prefix": "test_dns_name_prefix"}
        )
        self.assertEqual(ctx_1.get_dns_name_prefix(), "test_dns_name_prefix")

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "dns_name_prefix": None,
                "fqdn_subdomain": None,
                "name": "test_name",
                "resource_group_name": "test_rg_name",
            },
        )
        ctx_2.set_intermediate("subscription_id", "1234-5678")
        self.assertEqual(
            ctx_2.get_dns_name_prefix(), "testname-testrgname-1234-5"
        )
        self.assertEqual(
            ctx_2.get_intermediate("dns_name_prefix"),
            "testname-testrgname-1234-5",
        )
        mc = self.models.ManagedCluster(
            location="test_location", dns_prefix="test_dns_name_prefix"
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_dns_name_prefix(), "test_dns_name_prefix")
        self.assertEqual(ctx_2.get_intermediate("dns_name_prefix"), None)

        # invalid parameter with validation
        ctx_3 = AKSCreateContext(
            self.cmd,
            {
                "dns_name_prefix": "test_dns_name_prefix",
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_dns_name_prefix(enable_validation=True)

    def test_get_location(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"location": "test_location"})
        self.assertEqual(ctx_1.get_location(), "test_location")

        # dynamic completion
        with patch(
            "azure.cli.command_modules.acs.decorator._get_rg_location",
            return_value="test_location",
        ):
            ctx_2 = AKSCreateContext(
                self.cmd,
                {"location": None, "resource_group_name": "test_rg_name"},
            )
            self.assertEqual(ctx_2.get_location(), "test_location")

    def test_get_kubernetes_version(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd, {"kubernetes_version": "test_kubernetes_version"}
        )
        self.assertEqual(
            ctx_1.get_kubernetes_version(), "test_kubernetes_version"
        )

        # empty string
        ctx_2 = AKSCreateContext(self.cmd, {"kubernetes_version": ""})
        self.assertEqual(ctx_2.get_kubernetes_version(), "")

    def test_get_no_ssh_key(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"no_ssh_key": True})
        self.assertEqual(ctx_1.get_no_ssh_key(), True)

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(
            self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": False}
        )
        with self.assertRaises(CLIError):
            ctx_2.get_no_ssh_key(enable_validation=True)

    def test_get_vm_set_type(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"vm_set_type": "test_vm_set_type"})
        self.assertEqual(ctx_1.get_vm_set_type(), "test_vm_set_type")

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {"vm_set_type": None, "kubernetes_version": None},
        )
        self.assertEqual(ctx_2.get_vm_set_type(), "VirtualMachineScaleSets")
        self.assertEqual(
            ctx_2.get_intermediate("vm_set_type"),
            "VirtualMachineScaleSets",
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            name="test_ap_name", type="test_vm_set_type"
        )
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_vm_set_type(), "test_vm_set_type")
        self.assertEqual(ctx_2.get_intermediate("vm_set_type"), None)

    def test_get_load_balancer_sku(self):
        # default
        ctx_1 = AKSCreateContext(
            self.cmd, {"load_balancer_sku": "test_load_balancer_sku"}
        )
        self.assertEqual(
            ctx_1.get_load_balancer_sku(), "test_load_balancer_sku"
        )

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {"load_balancer_sku": None, "kubernetes_version": None},
        )
        self.assertEqual(ctx_2.get_load_balancer_sku(), "standard")
        self.assertEqual(
            ctx_2.get_intermediate("load_balancer_sku"),
            "standard",
        )
        network_profile = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="test_load_balancer_sku"
        )
        mc = self.models.ManagedCluster(
            location="test_location", network_profile=network_profile
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(
            ctx_2.get_load_balancer_sku(), "test_load_balancer_sku"
        )
        self.assertEqual(ctx_2.get_intermediate("load_balancer_sku"), None)

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
        ctx_1 = AKSCreateContext(
            self.cmd, {"fqdn_subdomain": "test_fqdn_subdomain"}
        )
        self.assertEqual(ctx_1.get_fqdn_subdomain(), "test_fqdn_subdomain")

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
        mc = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc, mc)

    def test_construct_default_mc(self):
        dec_1 = AKSCreateDecorator(
            self.cmd, self.client, self.models, {"location": "test_location"}
        )
        with patch(
            "azure.cli.command_modules.acs.decorator.get_subscription_id",
            return_value="test_sub_id",
        ):
            dec_mc = dec_1.construct_default_mc()
        mc = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc, mc)
