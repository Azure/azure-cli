# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import os
import unittest
from unittest.mock import Mock, patch
import tempfile
from knack import CLI
from knack.util import CLIError
from azure.cli.core.azclierror import (
    CLIInternalError,
    ResourceNotFoundError,
    ClientRequestError,
    ArgumentUsageError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    ValidationError,
    UnauthorizedError,
)


from azure.cli.core._config import ENV_VAR_PREFIX
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand
from azure.cli.command_modules.acs.decorator import (
    AKSCreateModels,
    AKSCreateParameters,
    AKSCreateContext,
    AKSCreateDecorator,
)
from azure.cli.core.profiles import get_sdk, ResourceType, supported_api_version


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
            models.ManagedClusterAgentPoolProfile,
            getattr(module, "ManagedClusterAgentPoolProfile"),
        )
        self.assertEqual(
            models.ManagedClusterIdentity,
            getattr(module, "ManagedClusterIdentity"),
        )
        self.assertEqual(
            models.ComponentsQit0EtSchemasManagedclusterpropertiesPropertiesIdentityprofileAdditionalproperties,
            getattr(
                module,
                "ComponentsQit0EtSchemasManagedclusterpropertiesPropertiesIdentityprofileAdditionalproperties",
            ),
        )
        self.assertEqual(
            models.ManagedCluster, getattr(module, "ManagedCluster")
        )
        self.assertEqual(
            models.Components1Umhcm8SchemasManagedclusteridentityPropertiesUserassignedidentitiesAdditionalproperties,
            getattr(
                module,
                "Components1Umhcm8SchemasManagedclusteridentityPropertiesUserassignedidentitiesAdditionalproperties",
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
        pass

    def test_set_intermediate(self):
        pass

    def test_remove_intermediate(self):
        pass

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
        ctx_1 = AKSCreateContext(self.cmd, {"kubernetes_version": "test_kubernetes_version"})
        self.assertEqual(ctx_1.get_kubernetes_version(), "test_kubernetes_version")

        # empty string
        ctx_2 = AKSCreateContext(self.cmd, {"kubernetes_version": ""})
        self.assertEqual(ctx_2.get_kubernetes_version(), "")

    def test_get_no_ssh_key(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"no_ssh_key": True})
        self.assertEqual(ctx_1.get_no_ssh_key(), True)

        # invalid parameter with validation
        ctx_2 = AKSCreateContext(self.cmd, {"ssh_key_value": "fake-key", "no_ssh_key": False})
        with self.assertRaises(CLIError):
            ctx_2.get_no_ssh_key(enable_validation=True)

    def test_get_vm_set_type(self):
        # default
        ctx_1 = AKSCreateContext(self.cmd, {"vm_set_type": "test_vm_set_type"})
        self.assertEqual(ctx_1.get_vm_set_type(), "test_vm_set_type")

        # dynamic completion
        ctx_2 = AKSCreateContext(
            self.cmd,
            {
                "vm_set_type": None,
                "kubernetes_version": None
            },
        )
        self.assertEqual(
            ctx_2.get_vm_set_type(), "VirtualMachineScaleSets"
        )
        self.assertEqual(
            ctx_2.get_intermediate("vm_set_type"),
            "VirtualMachineScaleSets",
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(name="test_ap_name", type="test_vm_set_type")
        mc = self.models.ManagedCluster(
            location="test_location", agent_pool_profiles=[agent_pool_profile]
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_vm_set_type(), "test_vm_set_type")
        self.assertEqual(ctx_2.get_intermediate("vm_set_type"), None)
