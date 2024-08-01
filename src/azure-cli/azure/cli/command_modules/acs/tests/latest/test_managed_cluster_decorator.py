# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import unittest
from unittest import mock
from unittest.mock import Mock, call, patch, ANY

from azure.cli.command_modules.acs._consts import (
    ADDONS,
    CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
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
    CONST_OPEN_SERVICE_MESH_ADDON_NAME,
    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
    CONST_PRIVATE_DNS_ZONE_NONE,
    CONST_PRIVATE_DNS_ZONE_SYSTEM,
    CONST_ROTATION_POLL_INTERVAL,
    CONST_SECRET_ROTATION_ENABLED,
    CONST_VIRTUAL_NODE_ADDON_NAME,
    CONST_VIRTUAL_NODE_SUBNET_NAME,
    CONST_MONITORING_USING_AAD_MSI_AUTH,
    CONST_LOAD_BALANCER_SKU_STANDARD,
    CONST_LOAD_BALANCER_SKU_BASIC,
    CONST_DEFAULT_NODE_OS_TYPE,
    CONST_VIRTUAL_MACHINE_SCALE_SETS,
    CONST_NODEPOOL_MODE_SYSTEM,
    CONST_DEFAULT_NODE_VM_SIZE,
    CONST_LOAD_BALANCER_BACKEND_POOL_TYPE_NODE_IP,
    DecoratorEarlyExitException,
    DecoratorMode,
    AgentPoolDecoratorMode,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK,
    CONST_AZURE_SERVICE_MESH_MODE_DISABLED,
)
from azure.cli.command_modules.acs.agentpool_decorator import AKSAgentPoolContext, AKSAgentPoolParamDict
from azure.cli.command_modules.acs.managed_cluster_decorator import (
    AKSManagedClusterContext,
    AKSManagedClusterCreateDecorator,
    AKSManagedClusterModels,
    AKSManagedClusterParamDict,
    AKSManagedClusterUpdateDecorator,
)
from azure.cli.command_modules.acs.tests.latest.mocks import (
    MockCLI,
    MockClient,
    MockCmd,
)
from azure.cli.command_modules.acs.tests.latest.utils import get_test_data_file_path
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    AzureInternalError,
    AzCLIError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    NoTTYError,
    RequiredArgumentMissingError,
    UnknownError,
)
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import HttpResponseError
from knack.prompting import NoTTYException
import datetime
from dateutil.parser import parse


class AKSManagedClusterModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)

    def test_models(self):
        models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

        # load models directly (instead of through the `get_sdk` method provided by the cli component)
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES

        sdk_profile = AZURE_API_PROFILES["latest"][ResourceType.MGMT_CONTAINERSERVICE]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(api_version.replace("-", "_"))
        module = importlib.import_module(module_name)

        # load balancer models
        self.assertEqual(
            models.load_balancer_models.ManagedClusterLoadBalancerProfile,
            getattr(module, "ManagedClusterLoadBalancerProfile"),
        )
        self.assertEqual(
            models.load_balancer_models.ManagedClusterLoadBalancerProfileManagedOutboundIPs,
            getattr(module, "ManagedClusterLoadBalancerProfileManagedOutboundIPs"),
        )
        self.assertEqual(
            models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPs,
            getattr(module, "ManagedClusterLoadBalancerProfileOutboundIPs"),
        )
        self.assertEqual(
            models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPPrefixes,
            getattr(module, "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"),
        )
        self.assertEqual(
            models.load_balancer_models.ResourceReference,
            getattr(module, "ResourceReference"),
        )
        # nat gateway models
        self.assertEqual(
            models.nat_gateway_models.ManagedClusterNATGatewayProfile,
            getattr(module, "ManagedClusterNATGatewayProfile"),
        )
        self.assertEqual(
            models.nat_gateway_models.ManagedClusterManagedOutboundIPProfile,
            getattr(module, "ManagedClusterManagedOutboundIPProfile"),
        )


class AKSManagedClusterContextTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

    def test__init__(self):
        # fail on not passing dictionary-like parameters
        with self.assertRaises(CLIInternalError):
            AKSManagedClusterContext(self.cmd, [], self.models, DecoratorMode.CREATE)
        # fail on not passing decorator_mode with Enum type DecoratorMode
        with self.assertRaises(CLIInternalError):
            AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, 1)

    def test_attach_mc(self):
        ctx_1 = AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, DecoratorMode.CREATE)
        mc = self.models.ManagedCluster(location="test_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.mc, mc)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.existing_mc, None)

    def test_attach_existing_mc(self):
        ctx_1 = AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, DecoratorMode.UPDATE)
        mc = self.models.ManagedCluster(location="test_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.existing_mc, mc)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_existing_mc(mc)

    def test_attach_agentpool_context(self):
        ctx_1 = AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, DecoratorMode.CREATE)
        agentpool_ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_1.attach_agentpool_context(agentpool_ctx_1)
        self.assertEqual(ctx_1.agentpool_context, agentpool_ctx_1)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_agentpool_context(agentpool_ctx_1)

    def test_validate_cluster_autoscaler_profile(self):
        ctx = AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, DecoratorMode.CREATE)
        # default
        s1 = None
        t1 = ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s1)
        g1 = None
        self.assertEqual(t1, g1)

        # invalid type
        s2 = set()
        # fail on invalid type
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s2)

        # empty list
        s3 = []
        t3 = ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s3)
        g3 = {}
        self.assertEqual(t3, g3)

        # empty dict
        s4 = {}
        t4 = ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s4)
        g4 = {}
        self.assertEqual(t4, g4)

        # empty key & empty value
        s5 = ["="]
        # fail on empty key
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s5)

        # non-empty key & empty value
        s6 = ["scan-interval="]
        t6 = ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s6)
        g6 = {"scan-interval": ""}
        self.assertEqual(t6, g6)

        # invalid key
        s7 = ["bad-key=val"]
        # fail on invalid key
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s7)

        # valid key
        s8 = ["scan-interval=20s", "scale-down-delay-after-add=15m"]
        t8 = ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s8)
        g8 = {"scan-interval": "20s", "scale-down-delay-after-add": "15m"}
        self.assertEqual(t8, g8)

        # two pairs of empty key & empty value
        s9 = ["=", "="]
        # fail on empty key
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s9)

        # additional empty key & empty value
        s10 = ["scan-interval=20s", "="]
        # fail on empty key
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_cluster_autoscaler_profile(s10)

    def test_validate_gmsa_options(self):
        # default
        ctx = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.CREATE,
        )
        ctx._AKSManagedClusterContext__validate_gmsa_options(False, False, None, None, False)
        ctx._AKSManagedClusterContext__validate_gmsa_options(True, False, None, None, True)
        ctx._AKSManagedClusterContext__validate_gmsa_options(False, True, None, None, False)

        # fail on yes & prompt_y_n not specified
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=False,
        ), self.assertRaises(DecoratorEarlyExitException):
            ctx._AKSManagedClusterContext__validate_gmsa_options(True, False, None, None, False)

        # fail on gmsa_root_domain_name not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSManagedClusterContext__validate_gmsa_options(True, False, "test_gmsa_dns_server", None, False)

        # fail on enable_windows_gmsa not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSManagedClusterContext__validate_gmsa_options(False, False, None, "test_gmsa_root_domain_name", False)

        # fail on enable_windows_gmsa not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSManagedClusterContext__validate_gmsa_options(
                False, False, "test_gmsa_dns_server", "test_gmsa_root_domain_name", False
            )

        # fail on disable_windows_gmsa specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_gmsa_options(True, True, None, None, False)

        # fail on disable_windows_gmsa specified but gmsa_dns_server specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_gmsa_options(False, True, "test_gmsa_dns_server", None, False)

        # fail on disable_windows_gmsa specified but gmsa_root_domain_name specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSManagedClusterContext__validate_gmsa_options(False, True, None, "test_gmsa_root_domain_name", False)

    def test_get_subscription_id(self):
        ctx_1 = AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, DecoratorMode.CREATE)
        ctx_1.set_intermediate("subscription_id", "test_subscription_id")
        self.assertEqual(
            ctx_1.get_subscription_id(),
            "test_subscription_id",
        )
        ctx_1.remove_intermediate("subscription_id")
        self.assertEqual(ctx_1.get_intermediate("subscription_id"), None)
        mock_profile = Mock(get_subscription_id=Mock(return_value="test_subscription_id"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=mock_profile,
        ):
            self.assertEqual(
                ctx_1.get_subscription_id(),
                "test_subscription_id",
            )
            mock_profile.get_subscription_id.assert_called_once()

    def test_get_resource_group_name(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"resource_group_name": "test_rg_name"}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_resource_group_name(), "test_rg_name")

    def test_get_name(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"name": "test_name"}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_name(), "test_name")

    def test_get_location(self):
        # default & dynamic completion
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"location": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.get_rg_location",
            return_value="test_location",
        ) as mock_get_rg_location:
            self.assertEqual(ctx_1._get_location(read_only=True), None)
            self.assertEqual(ctx_1.get_intermediate("location"), None)
            self.assertEqual(ctx_1.get_location(), "test_location")
            self.assertEqual(ctx_1.get_intermediate("location"), "test_location")
            self.assertEqual(ctx_1.get_location(), "test_location")
        mock_get_rg_location.assert_called_once()
        mc = self.models.ManagedCluster(location="test_mc_location")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_location(), "test_mc_location")

    def test_get_tags(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "tags": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_tags(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            tags={},
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_tags(), {})

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "tags": {"xyz": "100"},
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            tags={},
        )
        ctx_2.attach_mc(mc_2)
        self.assertEqual(ctx_2.get_tags(), {"xyz": "100"})

    def test_get_kubernetes_version(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"kubernetes_version": ""}),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"kubernetes_version": ""}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_1.attach_agentpool_context(agentpool_ctx_1)
        self.assertEqual(ctx_1.get_kubernetes_version(), "")

    def test_get_dns_name_prefix(self):
        # default & dynamic completion
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "dns_name_prefix": None,
                    "fqdn_subdomain": None,
                    "name": "1234_test_name",
                    "resource_group_name": "test_rg_name",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        ctx_1.set_intermediate("subscription_id", "1234-5678")
        self.assertEqual(ctx_1._get_dns_name_prefix(read_only=True), None)
        self.assertEqual(ctx_1.get_dns_name_prefix(), "a1234testn-testrgname-1234-5")
        mc = self.models.ManagedCluster(location="test_location", dns_prefix="test_mc_dns_name_prefix")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_dns_name_prefix(), "test_mc_dns_name_prefix")

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "dns_name_prefix": "test_dns_name_prefix",
                    "fqdn_subdomain": "test_fqdn_subdomain",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive dns_name_prefix and fqdn_subdomain
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_dns_name_prefix()

    def test_get_node_osdisk_diskencryptionset_id(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "node_osdisk_diskencryptionset_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
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

    def test_get_ssh_key_value_and_no_ssh_key(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"ssh_key_value": public_key, "no_ssh_key": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_ssh_key_value_and_no_ssh_key(), (public_key, False))
        ssh_config = self.models.ContainerServiceSshConfiguration(
            public_keys=[self.models.ContainerServiceSshPublicKey(key_data="test_mc_ssh_key_value")]
        )
        linux_profile = self.models.ContainerServiceLinuxProfile(admin_username="test_user", ssh=ssh_config)
        mc = self.models.ManagedCluster(location="test_location", linux_profile=linux_profile)
        ctx_1.attach_mc(mc)
        # fail on invalid key
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_1.get_ssh_key_value_and_no_ssh_key(),
                "test_mc_ssh_key_value",
            )

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"ssh_key_value": "fake-key", "no_ssh_key": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid key
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_ssh_key_value_and_no_ssh_key()

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"ssh_key_value": "fake-key", "no_ssh_key": True}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_ssh_key_value_and_no_ssh_key(), ("fake-key", True))
        ssh_config_3 = self.models.ContainerServiceSshConfiguration(
            public_keys=[self.models.ContainerServiceSshPublicKey(key_data="test_mc_ssh_key_value")]
        )
        linux_profile_3 = self.models.ContainerServiceLinuxProfile(admin_username="test_user", ssh=ssh_config_3)
        mc_3 = self.models.ManagedCluster(location="test_location", linux_profile=linux_profile_3)
        ctx_3.attach_mc(mc_3)
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            self.assertEqual(
                ctx_3.get_ssh_key_value_and_no_ssh_key(),
                "test_mc_ssh_key_value",
            )

    def test_get_admin_username(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"admin_username": "azureuser"}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_admin_username(), "azureuser")
        ssh_config = self.models.ContainerServiceSshConfiguration(public_keys=[])
        linux_profile = self.models.ContainerServiceLinuxProfile(admin_username="test_mc_user", ssh=ssh_config)
        mc = self.models.ManagedCluster(location="test_location", linux_profile=linux_profile)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_admin_username(), "test_mc_user")

    def test_get_windows_admin_username_and_password(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"windows_admin_username": None, "windows_admin_password": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_windows_admin_username_and_password(), (None, None))
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin",
        )
        mc = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile)
        ctx_1.attach_mc(mc)
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            self.assertEqual(
                ctx_1.get_windows_admin_username_and_password(),
                ("test_mc_win_admin", "test_mc_win_admin_password"),
            )

        # dynamic completion
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "windows_admin_username": None,
                    "windows_admin_password": "test_win_admin_pd",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on no tty
        with patch(
            "knack.prompting.verify_is_a_tty",
            side_effect=NoTTYException,
        ), self.assertRaises(NoTTYError):
            ctx_2.get_windows_admin_username_and_password()
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt",
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
        mc = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile)
        ctx_2.attach_mc(mc)
        self.assertEqual(
            ctx_2.get_windows_admin_username_and_password(),
            ("test_mc_win_admin_name", "test_mc_win_admin_pd"),
        )

        # dynamic completion
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "windows_admin_username": "test_win_admin_name",
                    "windows_admin_password": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on no tty
        with patch(
            "knack.prompting.verify_is_a_tty",
            side_effect=NoTTYException,
        ), self.assertRaises(NoTTYError):
            ctx_3.get_windows_admin_username_and_password()
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_pass",
            return_value="test_win_admin_pd",
        ):
            self.assertEqual(
                ctx_3.get_windows_admin_username_and_password(),
                ("test_win_admin_name", "test_win_admin_pd"),
            )

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "windows_admin_username": None,
                    "windows_admin_password": None,
                    "enable_windows_gmsa": False,
                    "gmsa_dns_server": None,
                    "gmsa_root_domain_name": "test_gmsa_root_domain_name",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on windows admin username/password not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_windows_admin_username_and_password()

    def test_get_windows_admin_password(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"windows_admin_password": None}),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_windows_admin_password(), None)

    def test_get_enable_ahub(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_ahub": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_ahub(), False)
        windows_profile = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin",
            admin_password="test_mc_win_admin_password",
            license_type="Windows_Server",
        )
        mc = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_ahub(), True)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_ahub": True, "disable_ahub": True}),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on mutually exclusive disable_ahub and enable_ahub
        with self.assertRaises(MutuallyExclusiveArgumentError):
            self.assertEqual(ctx_2.get_enable_ahub(), True)

    def test_get_disable_ahub(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_ahub": False}),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_disable_ahub(), False)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_ahub": True, "disable_ahub": True}),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on mutually exclusive disable_ahub and enable_ahub
        with self.assertRaises(MutuallyExclusiveArgumentError):
            self.assertEqual(ctx_2.get_disable_ahub(), True)

    def test_get_enable_windows_gmsa(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_windows_gmsa": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_windows_gmsa(), False)
        windows_gmsa_profile_1 = self.models.WindowsGmsaProfile(enabled=True)
        windows_profile_1 = self.models.ManagedClusterWindowsProfile(
            admin_username="test_admin_username",
            gmsa_profile=windows_gmsa_profile_1,
        )
        mc = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile_1)
        ctx_1.attach_mc(mc)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=True,
        ):
            self.assertEqual(ctx_1.get_enable_windows_gmsa(), True)

    def test_get_gmsa_dns_server_and_root_domain_name(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_windows_gmsa": False,
                    "gmsa_dns_server": None,
                    "gmsa_root_domain_name": None,
                    "disable_windows_gmsa": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_gmsa_dns_server_and_root_domain_name(), (None, None))
        windows_gmsa_profile_1 = self.models.WindowsGmsaProfile(
            enabled=True,
            dns_server="test_dns_server",
            root_domain_name="test_root_domain_name",
        )
        windows_profile_1 = self.models.ManagedClusterWindowsProfile(
            admin_username="test_admin_username",
            gmsa_profile=windows_gmsa_profile_1,
        )
        mc = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_gmsa_dns_server_and_root_domain_name(),
            ("test_dns_server", "test_root_domain_name"),
        )

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_windows_gmsa": True,
                    "gmsa_dns_server": "test_gmsa_dns_server",
                    "gmsa_root_domain_name": "test_gmsa_root_domain_name",
                    "disable_windows_gmsa": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        windows_gmsa_profile_2 = self.models.WindowsGmsaProfile(
            enabled=True,
            dns_server="test_dns_server",
            root_domain_name=None,
        )
        windows_profile_2 = self.models.ManagedClusterWindowsProfile(
            admin_username="test_admin_username",
            gmsa_profile=windows_gmsa_profile_2,
        )
        mc = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile_2)
        ctx_2.attach_mc(mc)
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            ctx_2.get_gmsa_dns_server_and_root_domain_name()

    def test_get_disable_windows_gmsa(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_windows_gmsa": False,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_disable_windows_gmsa(), False)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_windows_gmsa(), False)

    def test_get_service_principal_and_client_secret(
        self,
    ):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": None,
                    "client_secret": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_1.get_service_principal_and_client_secret(),
            (None, None),
        )

        # custom
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": "test_service_principal",
                    "client_secret": "test_client_secret",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_service_principal_and_client_secret(),
            ("test_service_principal", "test_client_secret"),
        )

        # custom
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": None,
                    "client_secret": "test_client_secret",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on service_principal not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_service_principal_and_client_secret()

        # custom
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": "test_service_principal",
                    "client_secret": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on client_secret not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_service_principal_and_client_secret()

        # custom
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": "test_service_principal",
                    "client_secret": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        sp_profile_5 = self.models.ManagedClusterServicePrincipalProfile(
            client_id=None, secret="test_client_secret"
        )
        mc_5 = self.models.ManagedCluster(location="test_location", service_principal_profile=sp_profile_5)
        ctx_5.attach_mc(mc_5)
        # fail on inconsistent state
        with self.assertRaises(CLIInternalError):
            ctx_5.get_service_principal_and_client_secret()

    def test_get_enable_managed_identity(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": None,
                    "client_secret": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_managed_identity(), True)
        identity = self.models.ManagedClusterIdentity()
        mc = self.models.ManagedCluster(location="test_location", identity=identity)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1._get_enable_managed_identity(read_only=True), False)
        self.assertEqual(ctx_1.get_enable_managed_identity(), True)

        # dynamic completion
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": True,
                    "service_principal": "test_service_principal",
                    "client_secret": "test_client_secret",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2._get_enable_managed_identity(read_only=True), True)
        # fail on mutually exclusive enable_managed_identity and service_principal/client_secret
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_managed_identity()

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": False,
                    "service_principal": "test_service_principal",
                    "client_secret": "test_client_secret",
                    "assign_identity": "test_assign_identity",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_managed_identity()

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_4.get_enable_managed_identity(), True)

        # custom value
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": False,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_5.get_enable_managed_identity(), False)
        mc_5 = self.models.ManagedCluster(location="test_location", identity=self.models.ManagedClusterIdentity(
            type="SystemAssigned"
        ))
        ctx_5.attach_mc(mc_5)
        self.assertEqual(ctx_5.get_enable_managed_identity(), False)

    def test_get_skip_subnet_role_assignment(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"skip_subnet_role_assignment": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_skip_subnet_role_assignment(), False)

    def test_get_assign_identity(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"assign_identity": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_assign_identity(), None)
        user_assigned_identity = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity = self.models.ManagedClusterIdentity(
            type="UserAssigned", user_assigned_identities=user_assigned_identity
        )
        mc = self.models.ManagedCluster(location="test_location", identity=identity)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_assign_identity(), "test_assign_identity")

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_managed_identity": False,
                    "service_principal": "test_service_principal",
                    "client_secret": "test_client_secret",
                    "assign_identity": "test_assign_identity",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_assign_identity()

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": None,
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on assign_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_assign_identity()

    def test_get_identity_by_msi_client(self):
        # custom value
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": "/subscriptions/1234/resourcegroups/test_rg/providers/microsoft.managedidentity/userassignedidentities/5678",
                    "enable_managed_identity": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        identity_obj = Mock(client_id="1234-5678", principal_id="8765-4321")
        msi_client = Mock(user_assigned_identities=Mock(get=Mock(return_value=identity_obj)))
        with patch(
            "azure.cli.command_modules.acs._helpers.get_msi_client",
            return_value=msi_client,
        ) as get_msi_client:
            identity = ctx_1.get_identity_by_msi_client(ctx_1.get_assign_identity())
            self.assertEqual(identity.client_id, "1234-5678")
            self.assertEqual(identity.principal_id, "8765-4321")
            get_msi_client.assert_called_once_with(self.cmd.cli_ctx, "1234")
            msi_client.user_assigned_identities.get.assert_called_once_with(
                resource_group_name="test_rg", resource_name="5678"
            )

    def test_get_user_assigned_identity_client_id(self):
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"assign_identity": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on assign_identity not provided
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_user_assigned_identity_client_id()

        # custom value
        identity_obj = Mock(
            client_id="test_client_id",
        )
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext.get_identity_by_msi_client",
            return_value=identity_obj,
        ) as get_identity_helper:
            ctx_2 = AKSManagedClusterContext(
                self.cmd,
                AKSManagedClusterParamDict(
                    {
                        "assign_identity": "test_assign_identity",
                        "enable_managed_identity": True,
                    }
                ),
                self.models,
                DecoratorMode.CREATE,
            )
            self.assertEqual(ctx_2.get_user_assigned_identity_client_id(), "test_client_id")
            get_identity_helper.assert_called_with("test_assign_identity")
            self.assertEqual(ctx_2.get_user_assigned_identity_client_id("custom_assign_identity"), "test_client_id")
            get_identity_helper.assert_called_with("custom_assign_identity")

    def test_get_user_assigned_identity_object_id(self):
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"assign_identity": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on assign_identity not provided
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_user_assigned_identity_object_id()

        # custom value
        identity_obj = Mock(
            principal_id="test_principal_id",
        )
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext.get_identity_by_msi_client",
            return_value=identity_obj,
        ) as get_identity_helper:
            ctx_2 = AKSManagedClusterContext(
                self.cmd,
                AKSManagedClusterParamDict(
                    {
                        "assign_identity": "test_assign_identity",
                        "enable_managed_identity": True,
                    }
                ),
                self.models,
                DecoratorMode.CREATE,
            )
            self.assertEqual(ctx_2.get_user_assigned_identity_object_id(), "test_principal_id")
            get_identity_helper.assert_called_with("test_assign_identity")
            self.assertEqual(ctx_2.get_user_assigned_identity_object_id("custom_assign_identity"), "test_principal_id")
            get_identity_helper.assert_called_with("custom_assign_identity")

    def test_get_attach_acr(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"attach_acr": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_attach_acr(), None)

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "attach_acr": "test_attach_acr",
                    "enable_managed_identity": True,
                    "no_wait": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_managed_identity and no_wait
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_attach_acr()

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "attach_acr": "test_attach_acr",
                    "enable_managed_identity": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on service_principal/client_secret not specified
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext._get_enable_managed_identity",
            return_value=False,
        ), self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_attach_acr()

        # custom value (update mode)
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "attach_acr": "test_attach_acr",
                    "enable_managed_identity": True,
                    "no_wait": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_4.get_attach_acr(), "test_attach_acr")

        # custom value
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "attach_acr": "test_attach_acr",
                    "enable_managed_identity": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_5.get_attach_acr(), "test_attach_acr")

    def test_get_detach_acr(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"detach_acr": None}),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_detach_acr(), None)

    def test_get_assignee_from_identity_or_sp_profile(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on no mc attached and no client id found
        with self.assertRaises(UnknownError):
            ctx_1.get_assignee_from_identity_or_sp_profile()

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.UPDATE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
        )
        ctx_2.attach_mc(mc_2)
        # fail on kubelet identity not found
        with self.assertRaises(UnknownError):
            ctx_2.get_assignee_from_identity_or_sp_profile()

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.UPDATE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="UserAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id", object_id="test_object_id"
                )
            },
        )
        ctx_3.attach_mc(mc_3)
        self.assertEqual(
            ctx_3.get_assignee_from_identity_or_sp_profile(),
            ("test_object_id", False),
        )

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.UPDATE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=self.models.ManagedClusterServicePrincipalProfile(client_id="test_client_id"),
        )
        ctx_4.attach_mc(mc_4)
        self.assertEqual(
            ctx_4.get_assignee_from_identity_or_sp_profile(),
            ("test_client_id", True),
        )

    def test_get_load_balancer_sku(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"load_balancer_sku": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_sku(), CONST_LOAD_BALANCER_SKU_STANDARD)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"load_balancer_sku": CONST_LOAD_BALANCER_SKU_BASIC}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_load_balancer_sku(), CONST_LOAD_BALANCER_SKU_BASIC)

        # invalid parameter with validation
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_sku": CONST_LOAD_BALANCER_SKU_BASIC,
                    "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when api_server_authorized_ip_ranges is assigned
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_load_balancer_sku()

        # invalid parameter with validation
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_sku": CONST_LOAD_BALANCER_SKU_BASIC,
                    "enable_private_cluster": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when enable_private_cluster is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_load_balancer_sku()

        # custom value (lower case)
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"load_balancer_sku": "STANDARD"}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_5.get_load_balancer_sku(), "standard")

    def test_get_load_balancer_managed_outbound_ip_count(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_managed_outbound_ip_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_managed_outbound_ip_count(), None)
        ctx_1_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_managed_outbound_ip_count": 10,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1_notnull.get_load_balancer_managed_outbound_ip_count(), 10)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_managed_outbound_ip_count": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            managed_outbound_i_ps=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileManagedOutboundIPs(
                count=10
            )
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_load_balancer_managed_outbound_ip_count(), None)

    def test_get_load_balancer_managed_outbound_ipv6_count(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_managed_outbound_ipv6_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_managed_outbound_ipv6_count(), None)
        ctx_1_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_managed_outbound_ipv6_count": 10,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1_notnull.get_load_balancer_managed_outbound_ipv6_count(), 10)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_managed_outbound_ipv6_count": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            managed_outbound_i_ps=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileManagedOutboundIPs(
                count=10
            )
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_load_balancer_managed_outbound_ipv6_count(), None)

    def test_get_load_balancer_backend_pool_type(self):
        ctx = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_backend_pool_type": "nodeIP",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx.get_load_balancer_backend_pool_type(), "nodeIP")

    def test_get_load_balancer_outbound_ips(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ips": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ips(), None)
        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ips": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            outbound_i_ps=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPs(
                public_i_ps=[self.models.load_balancer_models.ResourceReference(id="test_public_ip")]
            )
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_load_balancer_outbound_ips(), None)

    def test_get_load_balancer_outbound_ip_prefixes(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ip_prefixes": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ip_prefixes(), None)
        ctx_1_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ip_prefixes": "fakeids",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1_notnull.get_load_balancer_outbound_ip_prefixes(), "fakeids")
        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ip_prefixes": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_load_balancer_outbound_ip_prefixes(), None)
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            outbound_ip_prefixes=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
                public_ip_prefixes=[self.models.load_balancer_models.ResourceReference(id="test_public_ip_prefix")]
            )
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_load_balancer_outbound_ip_prefixes(), None)

    def test_get_load_balancer_outbound_ports(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ports": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ports(), None)
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ports": 10,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_outbound_ports(), 10)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_outbound_ports": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_load_balancer_outbound_ports(), None)
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            allocated_outbound_ports=10
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_load_balancer_outbound_ports(), None)

    def test_get_load_balancer_idle_timeout(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_idle_timeout": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_load_balancer_idle_timeout(), None)

        ctx_1_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_idle_timeout": 10,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1_notnull.get_load_balancer_idle_timeout(), 10)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_idle_timeout": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_load_balancer_idle_timeout(), None)
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            idle_timeout_in_minutes=10
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_load_balancer_idle_timeout(), None)
        # custom value
        ctx_2_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_idle_timeout": 20,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2_notnull.get_load_balancer_idle_timeout(), 20)
        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            idle_timeout_in_minutes=10
        )
        network_profile_2 = self.models.ContainerServiceNetworkProfile(load_balancer_profile=load_balancer_profile_2)
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        ctx_2_notnull.attach_mc(mc)
        self.assertEqual(ctx_2_notnull.get_load_balancer_idle_timeout(), 20)

    def test_get_nat_gateway_managed_outbound_ip_count(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"nat_gateway_managed_outbound_ip_count": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_nat_gateway_managed_outbound_ip_count(), None)

                # default
        ctx_1_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"nat_gateway_managed_outbound_ip_count": 2}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1_notnull.get_nat_gateway_managed_outbound_ip_count(), 2)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"nat_gateway_managed_outbound_ip_count": None}),
            self.models,
            DecoratorMode.UPDATE,
        )
        nat_gateway_profile = self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(
            managed_outbound_ip_profile=self.models.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(count=10)
        )
        network_profile = self.models.ContainerServiceNetworkProfile(nat_gateway_profile=nat_gateway_profile)
        mc = self.models.ManagedCluster(
            location="test_location",
            network_profile=network_profile,
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_nat_gateway_managed_outbound_ip_count(), 10)

        ctx_2_notnull = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"nat_gateway_managed_outbound_ip_count": 15}),
            self.models,
            DecoratorMode.UPDATE,
        )
        nat_gateway_profile = self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(
            managed_outbound_ip_profile=self.models.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(count=10)
        )
        network_profile = self.models.ContainerServiceNetworkProfile(nat_gateway_profile=nat_gateway_profile)
        mc = self.models.ManagedCluster(
            location="test_location",
            network_profile=network_profile,
        )
        ctx_2_notnull.attach_mc(mc)
        self.assertEqual(ctx_2_notnull.get_nat_gateway_managed_outbound_ip_count(), 15)

    def test_get_nat_gateway_idle_timeout(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"nat_gateway_idle_timeout": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_nat_gateway_idle_timeout(), None)
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"nat_gateway_idle_timeout": None}),
            self.models,
            DecoratorMode.UPDATE,
        )
        nat_gateway_profile = self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(
            idle_timeout_in_minutes=20,
        )
        network_profile = self.models.ContainerServiceNetworkProfile(nat_gateway_profile=nat_gateway_profile)
        mc = self.models.ManagedCluster(
            location="test_location",
            network_profile=network_profile,
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_nat_gateway_idle_timeout(), 20)

    def test_get_outbound_type(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "outbound_type": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1._get_outbound_type(read_only=True), None)
        self.assertEqual(ctx_1.get_outbound_type(), "loadBalancer")
        network_profile_1 = self.models.ContainerServiceNetworkProfile(outbound_type="test_outbound_type")
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_outbound_type(), "test_outbound_type")

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                    "load_balancer_sku": "basic",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when outbound_type is CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_outbound_type()

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_3.attach_agentpool_context(agentpool_ctx_3)
        # fail on vnet_subnet_id not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_outbound_type()

        # invalid parameter
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                    "vnet_subnet_id": "test_vnet_subnet_id",
                    "load_balancer_managed_outbound_ip_count": 10,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_4 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"vnet_subnet_id": "test_vnet_subnet_id"}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_4.attach_agentpool_context(agentpool_ctx_4)
        # fail on mutually exclusive outbound_type and managed_outbound_ip_count/outbound_ips/outbound_ip_prefixes of
        # load balancer
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_4.get_outbound_type()

        # invalid parameter
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                    "vnet_subnet_id": "test_vnet_subnet_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_5 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"vnet_subnet_id": "test_vnet_subnet_id"}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_5.attach_agentpool_context(agentpool_ctx_5)
        load_balancer_profile = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            outbound_ip_prefixes=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
                public_ip_prefixes=[self.models.load_balancer_models.ResourceReference(id="test_public_ip_prefix")]
            )
        )
        # fail on mutually exclusive outbound_type and managed_outbound_ip_count/outbound_ips/outbound_ip_prefixes of
        # load balancer
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_5.get_outbound_type(
                load_balancer_profile=load_balancer_profile,
            )

        # invalid parameter
        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "outbound_type": CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                    "vnet_subnet_id": "test_vnet_subnet_id",
                    "load_balancer_managed_outbound_ipv6_count": 10,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_6 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"vnet_subnet_id": "test_vnet_subnet_id"}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_6.attach_agentpool_context(agentpool_ctx_6)
        # fail on mutually exclusive outbound_type and managed_outbound_ipv6_count on
        # load balancer
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_6.get_outbound_type()

    def test_get_network_plugin_mode(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_plugin_mode": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_network_plugin_mode(), None)
        network_profile_1 = self.models.ContainerServiceNetworkProfile(network_plugin_mode="test_network_plugin_mode")
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_network_plugin_mode(), "test_network_plugin_mode")

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "pod_cidr": "test_pod_cidr",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # empty on network_plugin not specified
        self.assertEqual(ctx_2.get_network_plugin_mode(), None)

        # custom
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "pod_cidr": "test_pod_cidr",
                    "network_plugin": "azure",
                    "network_plugin_mode": "overlay",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_network_plugin_mode(), "overlay")

    def test_get_network_plugin(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_plugin": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_network_plugin(), None)
        network_profile_1 = self.models.ContainerServiceNetworkProfile(network_plugin="test_network_plugin")
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_network_plugin(), "test_network_plugin")

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "pod_cidr": "test_pod_cidr",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertIsNone(ctx_2.get_network_plugin())

        # custom
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "pod_cidr": "test_pod_cidr",
                    "network_plugin": "azure"
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )

        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_3.get_network_plugin(), "azure")

        # test update returns azure
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_plugin": "azure",
                    "network_plugin_mode": "overlay"
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )

        self.assertEqual(ctx_4.get_network_plugin(), "azure")

        # test update returns the value already on the mc
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_plugin": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        network_profile_5 = self.models.ContainerServiceNetworkProfile(network_plugin="azure")
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_5)
        ctx_5.attach_mc(mc)
        self.assertEqual(ctx_5.get_network_plugin(), "azure")

        # test update from kubenet -> overlay
        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_plugin": "azure",
                    "network_plugin_mode": "overlay",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        network_profile_6 = self.models.ContainerServiceNetworkProfile(network_plugin="kubenet", pod_cidr="100.112.0.0/12")
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_6)
        ctx_6.attach_mc(mc)
        self.assertEqual(ctx_6.get_network_plugin(), "azure")

        # do not use default from SDK when CREATE and nothing provided by user
        ctx_7 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        network_profile_7 = self.models.ContainerServiceNetworkProfile()
        self.assertEqual(network_profile_7.network_plugin, "kubenet") # kubenet is the default that comes from the SDK
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_7)
        ctx_7.attach_mc(mc)
        self.assertIsNone(ctx_7.get_network_plugin())

    def test_mc_get_network_dataplane(self):
        # Default, not set.
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_network_dataplane(), None)

        # Set to cilium.
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_dataplane": "cilium",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_network_dataplane(), "cilium")

        # Set to azure.
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_dataplane": "azure",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_network_dataplane(), "azure")

    def test_get_pod_cidrs(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"pod_cidrs": None}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_pod_cidrs(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(pod_cidrs="test_pod_cidrs"),
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_pod_cidrs(),
            "test_pod_cidrs",
        )

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"pod_cidrs": ""}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_pod_cidrs(), [])

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"pod_cidrs": "10.244.0.0/16,2001:abcd::/64"}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_pod_cidrs(), ["10.244.0.0/16", "2001:abcd::/64"])

    def test_get_service_cidrs(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"service_cidrs": None}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_service_cidrs(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(service_cidrs="test_service_cidrs"),
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_service_cidrs(),
            "test_service_cidrs",
        )

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"service_cidrs": ""}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_service_cidrs(), [])

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"service_cidrs": "10.244.0.0/16,2001:abcd::/64"}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_service_cidrs(), ["10.244.0.0/16", "2001:abcd::/64"])

    def test_get_ip_families(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"ip_families": None}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_ip_families(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(ip_families="test_ip_families"),
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_ip_families(),
            "test_ip_families",
        )

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"ip_families": ""}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_ip_families(), [])

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"ip_families": "IPv4,IPv6"}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_ip_families(), ["IPv4", "IPv6"])

    def test_get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
        self,
    ):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "pod_cidr": None,
                    "service_cidr": None,
                    "dns_service_ip": None,
                    "network_policy": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_1.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(),
            (None, None, None, None, None),
        )
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            pod_cidr="test_pod_cidr",
            service_cidr="test_service_cidr",
            dns_service_ip="test_dns_service_ip",
        )
        mc = self.models.ManagedCluster(location="test_location", network_profile=network_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(),
            (
                "test_pod_cidr",
                "test_service_cidr",
                "test_dns_service_ip",
                None,
                None,
            ),
        )

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "pod_cidr": "test_pod_cidr",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on network_plugin not specified
        self.assertEqual(
            ctx_2.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(),
            (
                "test_pod_cidr",
                None,
                None,
                None,
                None,
            )
        )

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "service_cidr": "test_service_cidr",
                    "dns_service_ip": "test_dns_service_ip",
                    "network_policy": "test_network_policy",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on network_plugin not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

        # require network_plugin when netpol is provided
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "network_policy": "test_network_policy",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on network_plugin not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

    def test_get_addon_consts(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.CREATE,
        )
        addon_consts = ctx_1.get_addon_consts()
        ground_truth_addon_consts = {
            "ADDONS": ADDONS,
            "CONST_ACC_SGX_QUOTE_HELPER_ENABLED": CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
            "CONST_AZURE_POLICY_ADDON_NAME": CONST_AZURE_POLICY_ADDON_NAME,
            "CONST_CONFCOM_ADDON_NAME": CONST_CONFCOM_ADDON_NAME,
            "CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME": CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
            "CONST_INGRESS_APPGW_ADDON_NAME": CONST_INGRESS_APPGW_ADDON_NAME,
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID": CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME": CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME,
            "CONST_INGRESS_APPGW_SUBNET_CIDR": CONST_INGRESS_APPGW_SUBNET_CIDR,
            "CONST_INGRESS_APPGW_SUBNET_ID": CONST_INGRESS_APPGW_SUBNET_ID,
            "CONST_INGRESS_APPGW_WATCH_NAMESPACE": CONST_INGRESS_APPGW_WATCH_NAMESPACE,
            "CONST_KUBE_DASHBOARD_ADDON_NAME": CONST_KUBE_DASHBOARD_ADDON_NAME,
            "CONST_MONITORING_ADDON_NAME": CONST_MONITORING_ADDON_NAME,
            "CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID": CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
            "CONST_OPEN_SERVICE_MESH_ADDON_NAME": CONST_OPEN_SERVICE_MESH_ADDON_NAME,
            "CONST_VIRTUAL_NODE_ADDON_NAME": CONST_VIRTUAL_NODE_ADDON_NAME,
            "CONST_VIRTUAL_NODE_SUBNET_NAME": CONST_VIRTUAL_NODE_SUBNET_NAME,
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME": CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
            "CONST_SECRET_ROTATION_ENABLED": CONST_SECRET_ROTATION_ENABLED,
            "CONST_ROTATION_POLL_INTERVAL": CONST_ROTATION_POLL_INTERVAL,
            "CONST_MONITORING_USING_AAD_MSI_AUTH": CONST_MONITORING_USING_AAD_MSI_AUTH,
        }
        self.assertEqual(addon_consts, ground_truth_addon_consts)

    def test_get_enable_addons(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_1.attach_agentpool_context(agentpool_ctx_1)
        self.assertEqual(ctx_1.get_enable_addons(), [])

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": "http_application_routing,monitoring",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_2.attach_agentpool_context(agentpool_ctx_2)
        self.assertEqual(
            ctx_2.get_enable_addons(),
            ["http_application_routing", "monitoring"],
        )

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": "test_addon_1,test_addon_2",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_3.attach_agentpool_context(agentpool_ctx_3)
        # fail on invalid enable_addons
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_enable_addons()

        # invalid parameter
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": "test_addon_1,test_addon_2,test_addon_1,test_addon_2",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_4 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_4.attach_agentpool_context(agentpool_ctx_4)
        # fail on invalid/duplicate enable_addons
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_addons()

        # invalid parameter
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "workspace_resource_id": "/test_workspace_resource_id",
                    "enable_addons": "",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_5 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_5.attach_agentpool_context(agentpool_ctx_5)
        # fail on enable_addons (monitoring) not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_5.get_enable_addons()

        # invalid parameter
        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": "virtual-node",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        agentpool_ctx_6 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            AgentPoolDecoratorMode.MANAGED_CLUSTER,
        )
        ctx_6.attach_agentpool_context(agentpool_ctx_6)
        # fail on aci_subnet_name/vnet_subnet_id not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_6.get_enable_addons()

    def test_get_http_proxy_config(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"http_proxy_config": None}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_http_proxy_config(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            http_proxy_config=self.models.ManagedClusterHTTPProxyConfig(http_proxy="test_http_proxy"),
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_http_proxy_config(),
            self.models.ManagedClusterHTTPProxyConfig(http_proxy="test_http_proxy"),
        )

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"http_proxy_config": "fake-path"}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid file path
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_http_proxy_config()

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"http_proxy_config": get_test_data_file_path("invalidconfig.json")}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        # fail on invalid file path
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_http_proxy_config()

    def test_get_workspace_resource_id(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "workspace_resource_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1._get_workspace_resource_id(read_only=True), None)
        addon_profiles_1 = {
            CONST_MONITORING_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: "test_workspace_resource_id"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        # fail on enable_addons (monitoring) not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_workspace_resource_id()

        # custom value & dynamic completion
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": "monitoring",
                    "workspace_resource_id": "test_workspace_resource_id/",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_workspace_resource_id(), "/test_workspace_resource_id")

        # dynamic completion
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_addons": "monitoring",
                    "resource_group_name": "test_rg_name",
                    "workspace_resource_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        ctx_3.set_intermediate("subscription_id", "test_subscription_id")
        get_resource_groups_client = Mock(check_existence=Mock(return_value=False))
        result = Mock(id="test_workspace_resource_id")
        async_poller = Mock(result=Mock(return_value=result), done=Mock(return_value=True))
        get_resources_client = Mock(begin_create_or_update_by_id=Mock(return_value=async_poller))
        with patch(
            "azure.cli.command_modules.acs.addonconfiguration.get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client",
            return_value=get_resource_groups_client,
        ), patch(
            "azure.cli.command_modules.acs.addonconfiguration.get_resources_client",
            return_value=get_resources_client,
        ):
            self.assertEqual(ctx_3.get_workspace_resource_id(), "/test_workspace_resource_id")
        get_resource_groups_client.check_existence.assert_called_once_with("DefaultResourceGroup-EUS")
        get_resource_groups_client.create_or_update.assert_called_once_with("DefaultResourceGroup-EUS", {"location": "eastus"})
        default_workspace_resource_id = (
            "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.OperationalInsights/workspaces/{2}".format(
                "test_subscription_id",
                "DefaultResourceGroup-EUS",
                "DefaultWorkspace-test_subscription_id-EUS",
            )
        )
        # the return values are func_name, args and kwargs
        _, args, _ = get_resources_client.begin_create_or_update_by_id.mock_calls[0]
        # not interested in mocking generic_resource, so we only check the first two args
        self.assertEqual(args[:2], (default_workspace_resource_id, "2015-11-01-preview"))

    def test_get_enable_msi_auth_for_monitoring(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_msi_auth_for_monitoring": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_msi_auth_for_monitoring(), False)
        addon_profiles_1 = {
            CONST_MONITORING_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_MONITORING_USING_AAD_MSI_AUTH: "true"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_msi_auth_for_monitoring(), True)

    def test_get_virtual_node_addon_os_type(self):
        # default
        ctx_1 = AKSManagedClusterContext(self.cmd, AKSManagedClusterParamDict({}), self.models, DecoratorMode.CREATE)
        self.assertEqual(ctx_1.get_virtual_node_addon_os_type(), "Linux")

    def test_get_aci_subnet_name(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aci_subnet_name": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_aci_subnet_name(), None)
        addon_profiles_1 = {
            CONST_VIRTUAL_NODE_ADDON_NAME
            + ctx_1.get_virtual_node_addon_os_type(): self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_VIRTUAL_NODE_SUBNET_NAME: "test_aci_subnet_name"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_aci_subnet_name(), "test_aci_subnet_name")

    def test_get_appgw_name(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "appgw_name": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_appgw_name(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME: "test_appgw_name"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_name(), "test_appgw_name")

    def test_get_appgw_subnet_cidr(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "appgw_subnet_cidr": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_appgw_subnet_cidr(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_INGRESS_APPGW_SUBNET_CIDR: "test_appgw_subnet_cidr"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_subnet_cidr(), "test_appgw_subnet_cidr")

    def test_get_appgw_id(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "appgw_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_appgw_id(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID: "test_appgw_id"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_id(), "test_appgw_id")

    def test_get_appgw_subnet_id(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "appgw_subnet_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_appgw_subnet_id(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_INGRESS_APPGW_SUBNET_ID: "test_appgw_subnet_id"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_subnet_id(), "test_appgw_subnet_id")

    def test_get_appgw_watch_namespace(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "appgw_watch_namespace": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_appgw_watch_namespace(), None)
        addon_profiles_1 = {
            CONST_INGRESS_APPGW_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_INGRESS_APPGW_WATCH_NAMESPACE: "test_appgw_watch_namespace"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_appgw_watch_namespace(), "test_appgw_watch_namespace")

    def test_get_enable_sgxquotehelper(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_sgxquotehelper": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_sgxquotehelper(), False)
        addon_profiles_1 = {
            CONST_CONFCOM_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "true"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_sgxquotehelper(), True)

    def test_get_enable_secret_rotation(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_secret_rotation": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_secret_rotation(), False)
        addon_profiles_1 = {
            CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_SECRET_ROTATION_ENABLED: "true"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_secret_rotation(), True)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_secret_rotation": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on azure keyvault secrets provider not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_enable_secret_rotation()

    def test_get_disable_secret_rotation(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_secret_rotation": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_secret_rotation(), False)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_secret_rotation": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on azure keyvault secrets provider not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_disable_secret_rotation()

    def test_get_rotation_poll_interval(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "rotation_poll_interval": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_rotation_poll_interval(), None)
        addon_profiles_1 = {
            CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_ROTATION_POLL_INTERVAL: "2m"},
            )
        }
        mc = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_rotation_poll_interval(), "2m")

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "rotation_poll_interval": "2m",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on azure keyvault secrets provider not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_rotation_poll_interval()

    def test_get_enable_aad(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_aad": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_aad(), False)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            managed=True,
        )
        mc = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_aad(), True)

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_aad": True,
                    "aad_client_app_id": "test_aad_client_app_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_aad and aad_client_app_id/aad_server_app_id/aad_server_app_secret
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_aad()

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_aad": False,
                    "enable_azure_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on enable_aad not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_aad()

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_aad": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        aad_profile_4 = self.models.ManagedClusterAADProfile(
            managed=True,
        )
        mc_4 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_4)
        ctx_4.attach_mc(mc_4)
        # fail on managed aad already enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_aad()

    def test_get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(
        self,
    ):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aad_client_app_id": None,
                    "aad_server_app_id": None,
                    "aad_server_app_secret": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
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
        mc = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_1)
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
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_aad": True,
                    "aad_client_app_id": "test_aad_client_app_id",
                    "aad_server_app_id": "test_aad_server_app_id",
                    "aad_server_app_secret": "test_aad_server_app_secret",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_aad and aad_client_app_id/aad_server_app_id/aad_server_app_secret
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret()

    def test_get_aad_tenant_id(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aad_tenant_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1._get_aad_tenant_id(read_only=True), None)
        self.assertEqual(ctx_1.get_aad_tenant_id(), None)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            tenant_id="test_aad_tenant_id",
        )
        mc = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_aad_tenant_id(), "test_aad_tenant_id")

        # dynamic completion
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_aad": False,
                    "aad_client_app_id": "test_aad_client_app_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        profile = Mock(get_login_credentials=Mock(return_value=(None, None, "test_aad_tenant_id")))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=profile,
        ):
            self.assertEqual(ctx_2.get_aad_tenant_id(), "test_aad_tenant_id")

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aad_tenant_id": "test_aad_tenant_id",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        aad_profile_3 = self.models.ManagedClusterAADProfile(
            managed=False,
        )
        mc_3 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_3)
        ctx_3.attach_mc(mc_3)
        # fail on managed aad not enabled
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_3.get_aad_tenant_id(),
                "test_aad_tenant_id",
            )

    def test_get_aad_admin_group_object_ids(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aad_admin_group_object_ids": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_aad_admin_group_object_ids(), None)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            admin_group_object_i_ds="test_aad_admin_group_object_ids",
        )
        mc = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(
            ctx_1.get_aad_admin_group_object_ids(),
            "test_aad_admin_group_object_ids",
        )

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aad_admin_group_object_ids": "test_value_1,test_value_2",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_aad_admin_group_object_ids(),
            ["test_value_1", "test_value_2"],
        )

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aad_admin_group_object_ids": "test_value_1,test_value_2",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        aad_profile_3 = self.models.ManagedClusterAADProfile(
            managed=False,
        )
        mc_3 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_3)
        ctx_3.attach_mc(mc_3)
        # fail on managed aad not enabled
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(
                ctx_3.get_aad_admin_group_object_ids(),
                ["test_value_1", "test_value_2"],
            )

    def test_get_disable_rbac(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_rbac": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_rbac(), None)
        mc = self.models.ManagedCluster(location="test_location", enable_rbac=False)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_disable_rbac(), True)

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_rbac": True,
                    "enable_azure_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive disable_rbac and enable_azure_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_disable_rbac()

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_rbac": True,
                    "enable_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive disable_rbac and enable_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_disable_rbac()

    def test_get_enable_rbac(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_rbac": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_rbac(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            enable_rbac=True,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_rbac(), True)

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_rbac": True,
                    "disable_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive disable_rbac and enable_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_rbac()

    def test_get_enable_azure_rbac(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_rbac": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_azure_rbac(), False)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=True,
        )
        mc = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_azure_rbac(), True)

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            DecoratorMode.CREATE,
        )
        aad_profile_2 = self.models.ManagedClusterAADProfile(
            managed=True,
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
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_rbac": True,
                    "enable_aad": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on enable_aad not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_3.get_enable_azure_rbac()

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        ctx_4.attach_mc(mc_4)
        # fail on managed aad not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_azure_rbac()

        # custom value
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_rbac": True,
                    "disable_azure_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        aad_profile_5 = self.models.ManagedClusterAADProfile(
            managed=True,
        )
        mc_5 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_5)
        ctx_5.attach_mc(mc_5)
        # fail on mutually exclusive enable_azure_rbac and disable_azure_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_5.get_enable_azure_rbac()

    def test_get_disable_azure_rbac(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_azure_rbac": False,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_disable_azure_rbac(), False)
        aad_profile_1 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=False,
        )
        mc = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_1)
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_disable_azure_rbac(), False)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_azure_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        aad_profile_2 = self.models.ManagedClusterAADProfile(
            managed=False,
        )
        mc_2 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_2)
        ctx_2.attach_mc(mc_2)
        # fail on managed aad not enabled
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_2.get_disable_azure_rbac(), True)

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_rbac": True,
                    "disable_azure_rbac": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        aad_profile_3 = self.models.ManagedClusterAADProfile(
            managed=True,
        )
        mc_3 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_3)
        ctx_3.attach_mc(mc_3)
        # fail on mutually exclusive enable_azure_rbac and disable_azure_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_disable_azure_rbac()

    def test_get_api_server_authorized_ip_ranges(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"api_server_authorized_ip_ranges": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_1.get_api_server_authorized_ip_ranges(),
            [],
        )
        api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
            authorized_ip_ranges=["test_mc_api_server_authorized_ip_ranges"]
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
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_sku": "standard",
                    "api_server_authorized_ip_ranges": "test_ip_range_1 , test_ip_range_2",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(
            ctx_2.get_api_server_authorized_ip_ranges(),
            ["test_ip_range_1", "test_ip_range_2"],
        )

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "load_balancer_sku": "basic",
                    "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when api_server_authorized_ip_ranges is assigned
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_api_server_authorized_ip_ranges()

        # invalid parameter
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_private_cluster and api_server_authorized_ip_ranges
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_4.get_api_server_authorized_ip_ranges()

        # default (update mode)
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "api_server_authorized_ip_ranges": None,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_5.get_api_server_authorized_ip_ranges(), None)

        # custom value (update mode)
        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "api_server_authorized_ip_ranges": "",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_6.get_api_server_authorized_ip_ranges(), [])

        # custom value (update mode)
        ctx_7 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_7 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
        )
        mc_7 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_7,
        )
        ctx_7.attach_mc(mc_7)
        # fail on mutually exclusive api_server_authorized_ip_ranges and private cluster
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_7.get_api_server_authorized_ip_ranges()

    def test_get_fqdn_subdomain(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"fqdn_subdomain": None}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_fqdn_subdomain(), None)
        mc = self.models.ManagedCluster(location="test_location", fqdn_subdomain="test_mc_fqdn_subdomain")
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_fqdn_subdomain(), "test_mc_fqdn_subdomain")

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "dns_name_prefix": "test_dns_name_prefix",
                    "fqdn_subdomain": "test_fqdn_subdomain",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive dns_name_prefix and fqdn_subdomain
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_fqdn_subdomain()

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "fqdn_subdomain": "test_fqdn_subdomain",
                    "private_dns_zone": "system",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on fqdn_subdomain specified and private_dns_zone equals to CONST_PRIVATE_DNS_ZONE_SYSTEM
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_fqdn_subdomain()

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "fqdn_subdomain": "test_fqdn_subdomain",
                    "private_dns_zone": "test_private_dns_zone",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid private_dns_zone when fqdn_subdomain is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_fqdn_subdomain()

    def test_get_enable_private_cluster(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_private_cluster(), False)
        api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_enable_private_cluster(), True)

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "load_balancer_sku": "basic",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid load_balancer_sku (basic) when enable_private_cluster is specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_enable_private_cluster()

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on mutually exclusive enable_private_cluster and api_server_authorized_ip_ranges
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_enable_private_cluster()

        # invalid parameter
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": False,
                    "disable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on disable_public_fqdn specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_4.get_enable_private_cluster()

        # invalid parameter
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": False,
                    "private_dns_zone": "system",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on private_dns_zone specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_5.get_enable_private_cluster()

        # custom value
        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_6 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=False,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_6,
        )
        ctx_6.attach_mc(mc_6)
        # fail on disable_public_fqdn specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            ctx_6.get_enable_private_cluster()

        # custom value
        ctx_7 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_7 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=False,
        )
        mc_7 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_7,
        )
        ctx_7.attach_mc(mc_7)
        # fail on enable_public_fqdn specified when private cluster is not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_7.get_enable_private_cluster()

        # custom value (update mode)
        ctx_8 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_8 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
        )
        mc_8 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_8,
        )
        ctx_8.attach_mc(mc_8)
        # fail on mutually exclusive api_server_authorized_ip_ranges and private cluster
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_8.get_enable_private_cluster()

    def test_get_disable_public_fqdn(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_public_fqdn(), False)
        api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster_public_fqdn=False,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        # fail on disable_public_fqdn specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_1.get_disable_public_fqdn(), True)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": True,
                    "enable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on mutually exclusive disable_public_fqdn and enable_public_fqdn
        with self.assertRaises(MutuallyExclusiveArgumentError):
            self.assertEqual(ctx_2.get_disable_public_fqdn(), True)

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on private cluster not enabled in update mode
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_3.get_disable_public_fqdn(), True)

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": True,
                    "private_dns_zone": "none",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_4 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_4,
        )
        ctx_4.attach_mc(mc_4)
        # fail on invalid private_dns_zone (none) when disable_public_fqdn is specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_4.get_disable_public_fqdn(), True)

    def test_get_enable_public_fqdn(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_public_fqdn": False,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_enable_public_fqdn(), False)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": True,
                    "enable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on mutually exclusive disable_public_fqdn and enable_public_fqdn
        with self.assertRaises(MutuallyExclusiveArgumentError):
            self.assertEqual(ctx_2.get_enable_public_fqdn(), True)

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_3 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=False,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_3,
        )
        ctx_3.attach_mc(mc_3)
        # fail on private cluster not enabled in update mode
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_3.get_enable_public_fqdn(), True)

    def test_get_private_dns_zone(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "private_dns_zone": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_private_dns_zone(), None)
        api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
            private_dns_zone="test_private_dns_zone",
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile,
        )
        ctx_1.attach_mc(mc)
        # fail on private_dns_zone specified when enable_private_cluster is not specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_1.get_private_dns_zone(), "test_private_dns_zone")

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "private_dns_zone": "test_private_dns_zone",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid private_dns_zone
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_2.get_private_dns_zone(), "test_private_dns_zone")

        # invalid parameter
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_private_cluster": True,
                    "private_dns_zone": CONST_PRIVATE_DNS_ZONE_SYSTEM,
                    "fqdn_subdomain": "test_fqdn_subdomain",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid private_dns_zone when fqdn_subdomain is specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_3.get_private_dns_zone(), CONST_PRIVATE_DNS_ZONE_SYSTEM)

        # custom value
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_public_fqdn": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        api_server_access_profile_4 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
            private_dns_zone=CONST_PRIVATE_DNS_ZONE_NONE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_4,
        )
        ctx_4.attach_mc(mc_4)
        # fail on invalid private_dns_zone (none) when disable_public_fqdn is specified
        with self.assertRaises(InvalidArgumentValueError):
            self.assertEqual(ctx_4.get_private_dns_zone(), CONST_PRIVATE_DNS_ZONE_NONE)

    def test_get_user_assignd_identity_from_mc(self):
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        user_assigned_identity_1 = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity_1 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=user_assigned_identity_1,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_1,
        )
        ctx_1.attach_mc(mc_1)
        self.assertEqual(ctx_1.get_user_assignd_identity_from_mc(), "test_assign_identity")

    def test_get_assign_kubelet_identity(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": "test_assign_identity",
                    "assign_kubelet_identity": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
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
        self.assertEqual(ctx_1.get_assign_kubelet_identity(), "test_assign_kubelet_identity")

        # invalid parameter
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": None,
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on assign_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            self.assertEqual(
                ctx_2.get_assign_kubelet_identity(),
                "test_assign_kubelet_identity",
            )

        # update
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": None,
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        user_assigned_identity_3 = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity_3 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=user_assigned_identity_3,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_3,
        )
        ctx_3.attach_mc(mc_3)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=True,
        ):
            self.assertEqual(
                ctx_3.get_assign_kubelet_identity(),
                "test_assign_kubelet_identity",
            )

        # update
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": None,
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on assign_identity not specified and not existed in mc
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=True,
        ), self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_assign_kubelet_identity()

        # update
        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "assign_identity": None,
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on no confirm
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=False,
        ), self.assertRaises(DecoratorEarlyExitException):
            ctx_5.get_assign_kubelet_identity()

    def test_get_auto_upgrade_channel(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "auto_upgrade_channel": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_auto_upgrade_channel(), None)
        auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile(upgrade_channel="test_auto_upgrade_channel")
        mc = self.models.ManagedCluster(
            location="test_location",
            auto_upgrade_profile=auto_upgrade_profile,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_auto_upgrade_channel(), "test_auto_upgrade_channel")

    def test_get_cluster_autoscaler_profile(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "cluster_autoscaler_profile": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
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
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "cluster_autoscaler_profile": {
                        "scan-interval": "30s",
                        "expander": "least-waste",
                    },
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        auto_scaler_profile_2 = self.models.ManagedClusterPropertiesAutoScalerProfile(
            scan_interval="10s",
            expander="random",
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile=auto_scaler_profile_2,
        )
        ctx_2.attach_mc(mc_2)
        self.assertEqual(
            ctx_2._get_cluster_autoscaler_profile(read_only=True),
            {
                "scan-interval": "30s",
                "expander": "least-waste",
            },
        )
        print(ctx_2.get_cluster_autoscaler_profile())
        self.assertEqual(
            ctx_2.get_cluster_autoscaler_profile(),
            {
                "additional_properties": {},
                "balance_similar_node_groups": None,
                "daemonset_eviction_for_empty_nodes": None,
                "daemonset_eviction_for_occupied_nodes": None,
                "ignore_daemonsets_utilization": None,
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
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "uptime_sla": False,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_uptime_sla(), False)
        sku = self.models.ManagedClusterSKU(
            name="Base",
            tier="Standard",
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            sku=sku,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_uptime_sla(), True)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "uptime_sla": False,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        sku_2 = self.models.ManagedClusterSKU(
            name="Base",
            tier="Standard",
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=sku_2,
        )
        ctx_2.attach_mc(mc_2)
        self.assertEqual(ctx_2.get_uptime_sla(), False)

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "uptime_sla": True,
                    "no_uptime_sla": True,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        sku_3 = self.models.ManagedClusterSKU(
            name="Base",
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
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "no_uptime_sla": False,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_no_uptime_sla(), False)
        sku = self.models.ManagedClusterSKU(
            name="Base",
            tier="Standard",
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            sku=sku,
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_no_uptime_sla(), False)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "uptime_sla": True,
                    "no_uptime_sla": True,
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        sku_2 = self.models.ManagedClusterSKU(
            name="Base",
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

    def test_get_disable_local_accounts(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_local_accounts": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_disable_local_accounts(), False)
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=True,
        )
        ctx_1.attach_mc(mc_1)
        self.assertEqual(ctx_1.get_disable_local_accounts(), True)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_local_accounts": True, "enable_local_accounts": True}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_disable_local_accounts(), True)

        # custom value
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_local_accounts": True, "enable_local_accounts": True}),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on mutually exclusive disable_local_accounts and enable_local_accounts
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_disable_local_accounts()

    def test_get_enable_local_accounts(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_local_accounts": False}),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_enable_local_accounts(), False)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_local_accounts": True, "disable_local_accounts": True}),
            self.models,
            DecoratorMode.UPDATE,
        )
        # fail on mutually exclusive disable_local_accounts and enable_local_accounts
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_2.get_enable_local_accounts()

    def test_get_edge_zone(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "edge_zone": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
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

    def test_get_node_resource_group(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"node_resource_group": None}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_node_resource_group(), None)
        mc = self.models.ManagedCluster(
            location="test_location",
            node_resource_group="test_node_resource_group",
        )
        ctx_1.attach_mc(mc)
        self.assertEqual(ctx_1.get_node_resource_group(), "test_node_resource_group")

    def test_get_defender_config(self):
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_defender": True,
                    "defender_config": get_test_data_file_path(
                        "defenderconfig.json"
                    ),
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        defender_config_1 = ctx_1.get_defender_config()
        ground_truth_defender_config_1 = self.models.ManagedClusterSecurityProfileDefender(
            log_analytics_workspace_resource_id="test_workspace_resource_id",
            security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                enabled=True
            ),
        )
        self.assertEqual(defender_config_1, ground_truth_defender_config_1)

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {"enable_defender": True, "defender_config": "fake-path"}
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        # fail on invalid file path
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_defender_config()

        # custom
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_defender": True}),
            self.models,
            DecoratorMode.UPDATE,
        )
        defender_config_3 = ctx_3.get_defender_config()
        ground_truth_defender_config_3 = self.models.ManagedClusterSecurityProfileDefender(
            security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                enabled=False,
            ),
        )
        self.assertEqual(defender_config_3, ground_truth_defender_config_3)

        # custom
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_defender": True}),
            self.models,
            DecoratorMode.UPDATE,
        )
        ctx_4.set_intermediate("subscription_id", "test_subscription_id")
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_default_log_analytics_workspace_for_monitoring",
            return_value="test_workspace_resource_id",
        ):
            defender_config_4 = ctx_4.get_defender_config()
        ground_truth_defender_config_4 = self.models.ManagedClusterSecurityProfileDefender(
            log_analytics_workspace_resource_id="test_workspace_resource_id",
            security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                enabled=True,
            ),
        )
        self.assertEqual(defender_config_4, ground_truth_defender_config_4)

    def test_get_workload_identity_profile__create_no_set(self):
        ctx = AKSManagedClusterContext(
            self.cmd, AKSManagedClusterParamDict({}), self.models, decorator_mode=DecoratorMode.CREATE
        )
        self.assertIsNone(ctx.get_workload_identity_profile())

    def test_get_workload_identity_profile__create_enable_without_oidc_issuer(self):
        ctx = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_workload_identity": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx.get_workload_identity_profile()

    def test_get_workload_identity_profile__create_enable_with_oidc_issuer(self):
        ctx = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_oidc_issuer": True,
                    "enable_workload_identity": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        profile = ctx.get_workload_identity_profile()
        self.assertTrue(profile.enabled)

    def test_get_workload_identity_profile__update_not_set(self):
        ctx = AKSManagedClusterContext(
            self.cmd, AKSManagedClusterParamDict({}), self.models, decorator_mode=DecoratorMode.UPDATE
        )
        ctx.attach_mc(self.models.ManagedCluster(location="test_location"))
        self.assertIsNone(ctx.get_workload_identity_profile())

    def test_get_workload_identity_profile__update_with_enable_and_disable(self):
        ctx = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_workload_identity": True,
                    "disable_workload_identity": True,
                }
            ),
            self.models, decorator_mode=DecoratorMode.UPDATE
        )
        ctx.attach_mc(self.models.ManagedCluster(location="test_location"))
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx.get_workload_identity_profile()

    def test_get_workload_identity_profile__update_with_enable_without_oidc_issuer(self):
        ctx = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_workload_identity": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        ctx.attach_mc(self.models.ManagedCluster(location="test_location"))
        with self.assertRaises(RequiredArgumentMissingError):
            ctx.get_workload_identity_profile()

    def test_get_workload_identity_profile__update_with_enable(self):
        for previous_enablement_status in [
            None,  # preivous not set
            True,  # previous set to enabled=true
            False,  # previous set to enabled=false
        ]:
            ctx = AKSManagedClusterContext(
                self.cmd,
                AKSManagedClusterParamDict(
                    {
                        "enable_workload_identity": True,
                    }
                ),
                self.models,
                decorator_mode=DecoratorMode.UPDATE,
            )
            mc = self.models.ManagedCluster(location="test_location")
            mc.oidc_issuer_profile = self.models.ManagedClusterOIDCIssuerProfile(enabled=True)
            if previous_enablement_status is None:
                mc.security_profile = None
            else:
                mc.security_profile = self.models.ManagedClusterSecurityProfile(
                    workload_identity=self.models.ManagedClusterSecurityProfileWorkloadIdentity(
                        enabled=previous_enablement_status
                    )
                )
            ctx.attach_mc(mc)
            profile = ctx.get_workload_identity_profile()
            self.assertTrue(profile.enabled)

    def test_get_workload_identity_profile__update_with_disable(self):
        for previous_enablement_status in [
            None,  # preivous not set
            True,  # previous set to enabled=true
            False,  # previous set to enabled=false
        ]:
            ctx = AKSManagedClusterContext(
                self.cmd,
                AKSManagedClusterParamDict(
                    {
                        "disable_workload_identity": True,
                    }
                ),
                self.models,
                decorator_mode=DecoratorMode.UPDATE,
            )
            mc = self.models.ManagedCluster(location="test_location")
            mc.oidc_issuer_profile = self.models.ManagedClusterOIDCIssuerProfile(enabled=True)
            if previous_enablement_status is None:
                mc.security_profile = None
            else:
                mc.security_profile = self.models.ManagedClusterSecurityProfile(
                    workload_identity=self.models.ManagedClusterSecurityProfileWorkloadIdentity(
                        enabled=previous_enablement_status
                    )
                )
            ctx.attach_mc(mc)
            profile = ctx.get_workload_identity_profile()
            self.assertFalse(profile.enabled)

    def test_get_enable_azure_keyvault_kms(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertIsNone(ctx_0.get_enable_azure_keyvault_kms())

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_azure_keyvault_kms(), False)

        key_id_1 = "https://fakekeyvault.vault.azure.net/secrets/fakekeyname/fakekeyversion"
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_id=key_id_1,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_enable_azure_keyvault_kms(), True)

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_id=key_id_1,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_3.attach_mc(mc)
        self.assertEqual(ctx_3.get_enable_azure_keyvault_kms(), False)

        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_enable_azure_keyvault_kms()

        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "azure_keyvault_kms_key_id": "test_azure_keyvault_kms_key_id",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_5.get_enable_azure_keyvault_kms()

    def test_get_disable_azure_keyvault_kms(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertIsNone(ctx_0.get_enable_azure_keyvault_kms())

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_azure_keyvault_kms": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_disable_azure_keyvault_kms(), True)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_azure_keyvault_kms": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_disable_azure_keyvault_kms(), False)

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": True,
                    "disable_azure_keyvault_kms": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_disable_azure_keyvault_kms()

    def test_get_azure_keyvault_kms_key_id(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertIsNone(ctx_0.get_azure_keyvault_kms_key_id())

        key_id_1 = "https://fakekeyvault.vault.azure.net/secrets/fakekeyname/fakekeyversion"
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": True,
                    "azure_keyvault_kms_key_id": key_id_1,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_azure_keyvault_kms_key_id(), key_id_1)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": True,
                    "azure_keyvault_kms_key_id": key_id_1,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        key_id_2 = "https://fakekeyvault2.vault.azure.net/secrets/fakekeyname2/fakekeyversion2"
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_id=key_id_2,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_azure_keyvault_kms_key_id(), key_id_2)

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": True,
                    "azure_keyvault_kms_key_id": key_id_1,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_id=key_id_2,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_3.attach_mc(mc)
        self.assertEqual(ctx_3.get_azure_keyvault_kms_key_id(), key_id_1)

        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "azure_keyvault_kms_key_id": key_id_1,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_azure_keyvault_kms_key_id()

        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_keyvault_kms": False,
                    "azure_keyvault_kms_key_id": key_id_1,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_5.get_azure_keyvault_kms_key_id()

    def test_get_azure_keyvault_kms_key_vault_network_access(self):
        key_vault_network_access_1 = "Public"
        key_vault_network_access_2 = "Private"

        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_0.get_azure_keyvault_kms_key_vault_network_access()

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "azure_keyvault_kms_key_vault_network_access": key_vault_network_access_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_1.get_azure_keyvault_kms_key_vault_network_access()

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": False,
                "azure_keyvault_kms_key_vault_network_access": key_vault_network_access_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_azure_keyvault_kms_key_vault_network_access()

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": key_vault_network_access_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_azure_keyvault_kms_key_vault_network_access(), key_vault_network_access_1)

        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": key_vault_network_access_2,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_azure_keyvault_kms_key_vault_network_access()

        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": key_vault_network_access_2,
                "azure_keyvault_kms_key_vault_resource_id": "fake-resource-id",
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_5.get_azure_keyvault_kms_key_vault_network_access(), key_vault_network_access_2)

        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": key_vault_network_access_2,
                "azure_keyvault_kms_key_vault_resource_id": "fake-resource-id",
            }),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_vault_network_access=key_vault_network_access_1,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_6.attach_mc(mc)
        self.assertEqual(ctx_6.get_azure_keyvault_kms_key_vault_network_access(), key_vault_network_access_2)

    def test_get_azure_keyvault_kms_key_vault_resource_id(self):
        key_vault_resource_id_1 = "/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo"
        key_vault_resource_id_2 = "/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/bar/providers/Microsoft.KeyVault/vaults/bar"

        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertIsNone(ctx_0.get_azure_keyvault_kms_key_vault_resource_id())

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Public",
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_azure_keyvault_kms_key_vault_resource_id(), None)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Public",
                "azure_keyvault_kms_key_vault_resource_id": "",
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_azure_keyvault_kms_key_vault_resource_id(), "")

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Private",
                "azure_keyvault_kms_key_vault_resource_id": key_vault_resource_id_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_3.get_azure_keyvault_kms_key_vault_resource_id(), key_vault_resource_id_1)

        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Private",
                "azure_keyvault_kms_key_vault_resource_id": key_vault_resource_id_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_vault_network_access="Private",
            key_vault_resource_id=key_vault_resource_id_2,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_4.attach_mc(mc)
        self.assertEqual(ctx_4.get_azure_keyvault_kms_key_vault_resource_id(), key_vault_resource_id_2)

        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Private",
                "azure_keyvault_kms_key_vault_resource_id": key_vault_resource_id_2,
            }),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
            enabled=True,
            key_vault_network_access="Private",
            key_vault_resource_id=key_vault_resource_id_1,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_5.attach_mc(mc)
        self.assertEqual(ctx_5.get_azure_keyvault_kms_key_vault_resource_id(), key_vault_resource_id_2)

        ctx_6 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "azure_keyvault_kms_key_vault_resource_id": key_vault_resource_id_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_6.get_azure_keyvault_kms_key_vault_resource_id()

        ctx_7 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": False,
                "azure_keyvault_kms_key_vault_resource_id": key_vault_resource_id_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_7.get_azure_keyvault_kms_key_vault_resource_id()

        ctx_8 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Public",
                "azure_keyvault_kms_key_vault_resource_id": key_vault_resource_id_1,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(ArgumentUsageError):
            ctx_8.get_azure_keyvault_kms_key_vault_resource_id()

        ctx_9 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_azure_keyvault_kms": True,
                "azure_keyvault_kms_key_vault_network_access": "Private",
                "azure_keyvault_kms_key_vault_resource_id": "",
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(ArgumentUsageError):
            ctx_9.get_azure_keyvault_kms_key_vault_resource_id()

    def test_get_enable_image_cleaner(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_0.get_enable_image_cleaner(), None)

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_image_cleaner": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_enable_image_cleaner(), False)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_image_cleaner": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_2.get_enable_image_cleaner(), True)

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_image_cleaner": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_3.get_enable_image_cleaner(), False)

        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_image_cleaner": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_4.get_enable_image_cleaner(), True)

    def test_get_disable_image_cleaner(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_0.get_disable_image_cleaner(), None)

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_image_cleaner": True,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_disable_image_cleaner(), True)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "disable_image_cleaner": False,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_disable_image_cleaner(), False)

    def test_get_image_cleaner_interval_hours(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertIsNone(ctx_0.get_image_cleaner_interval_hours())


        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_image_cleaner": True,
                    "image_cleaner_interval_hours": 24,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_image_cleaner_interval_hours(), 24)

        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "image_cleaner_interval_hours": 24,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_2.get_image_cleaner_interval_hours()

        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "image_cleaner_interval_hours": 24,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=25,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_3.attach_mc(mc)
        self.assertEqual(ctx_3.get_image_cleaner_interval_hours(), 24)

        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "image_cleaner_interval_hours": 24,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=False,
            interval_hours=25,
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        ctx_4.attach_mc(mc)
        with self.assertRaises(RequiredArgumentMissingError):
            ctx_4.get_image_cleaner_interval_hours()

        ctx_5 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_image_cleaner": True,
                    "disable_image_cleaner": True,
                    "image_cleaner_interval_hours": 24,
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_5.get_image_cleaner_interval_hours()

    def test_get_blob_driver(self):
        # create with blob driver enabled
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_blob_driver": True,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        ctx_1.attach_mc(mc_1)
        storage_profile_1 = self.models.ManagedClusterStorageProfile(
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(
                enabled=True,
            ),
        )
        self.assertEqual(ctx_1.get_storage_profile(), storage_profile_1)

        # create without blob driver enabled
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        ctx_2.attach_mc(mc_1)
        storage_profile_2 = self.models.ManagedClusterStorageProfile(
            blob_csi_driver=None,
        )
        self.assertEqual(ctx_2.get_storage_profile(), storage_profile_2)

        # update blob driver enabled
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_blob_driver": True,
                "yes": True,
            }),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        ctx_3.attach_mc(mc_1)
        storage_profile_3 = self.models.ManagedClusterStorageProfile(
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(
                enabled=True,
            ),
        )
        self.assertEqual(ctx_3.get_storage_profile(), storage_profile_3)

        # update blob driver disabled
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "disable_blob_driver": True,
                "yes": True,
            }),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        ctx_4.attach_mc(mc_1)
        storage_profile_4 = self.models.ManagedClusterStorageProfile(
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(
                enabled=False,
            ),
        )
        self.assertEqual(ctx_4.get_storage_profile(), storage_profile_4)

    def test_get_storage_profile(self):
        # create
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "disable_disk_driver": True,
            }),
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        ctx_1.attach_mc(mc_1)
        ground_truth_storage_profile_1 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(
                enabled=False,
            ),
            file_csi_driver=None,
            snapshot_controller=None,
            blob_csi_driver=None,
        )
        self.assertEqual(ctx_1.get_storage_profile(), ground_truth_storage_profile_1)

        # update
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({
                "enable_file_driver": True,
                "disable_snapshot_controller": True,
                "enable_blob_driver": True,
                "yes": True,
            }),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        storage_profile_2 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(
                enabled=True,
            ),
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(
                enabled=False,
            ),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(
                enabled=True,
            ),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(
                enabled=False,
            ),
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            storage_profile=storage_profile_2,
        )
        ctx_2.attach_mc(mc_2)
        ground_truth_storage_profile_2 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=None,
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(
                enabled=True,
            ),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(
                enabled=False,
            ),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(
                enabled=True,
            ),
        )
        self.assertEqual(ctx_2.get_storage_profile(), ground_truth_storage_profile_2)

    def test_get_yes(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"yes": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_yes(), False)

    def test_get_no_wait(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"no_wait": False}),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_no_wait(), False)

    def test_get_aks_custom_headers(self):
        # default
        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aks_custom_headers": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_aks_custom_headers(), {})

        # custom value
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "aks_custom_headers": "abc=def,xyz=123",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_aks_custom_headers(), {"abc": "def", "xyz": "123"})
        service_principal_profile_2 = self.models.ManagedClusterServicePrincipalProfile(
            client_id="test_service_principal", secret="test_client_secret"
        )
        mc = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile_2,
        )
        ctx_2.attach_mc(mc)
        self.assertEqual(ctx_2.get_aks_custom_headers(), {"abc": "def", "xyz": "123"})

    def test_get_force_upgrade(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_0.get_force_upgrade(), None)

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_force_upgrade": True}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_force_upgrade(), True)
        ctx_2 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"enable_force_upgrade": False}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_force_upgrade(), False)
        ctx_3 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_force_upgrade": True}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_3.get_force_upgrade(), False)
        ctx_4 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({"disable_force_upgrade": False}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_4.get_force_upgrade(), True)

    def test_get_upgrade_override_until(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict({}),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_0.get_upgrade_override_until(), None)

        ctx_1 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "upgrade_override_until": "2022-11-01T13:00:00Z",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_1.get_upgrade_override_until(), "2022-11-01T13:00:00Z")

    def test_handle_enable_disable_asm(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_service_mesh": True,
                    "revision": "asm-1-18"
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        old_profile = self.models.ServiceMeshProfile(
            mode=CONST_AZURE_SERVICE_MESH_MODE_DISABLED,
            istio=self.models.IstioServiceMesh(),
        )
        new_profile, updated = ctx_0._handle_enable_disable_asm(old_profile)
        self.assertEqual(updated, True)
        self.assertEqual(new_profile, self.models.ServiceMeshProfile(
            mode="Istio", istio=self.models.IstioServiceMesh(revisions=["asm-1-18"])
        ))

    def test_handle_ingress_gateways_asm(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_service_mesh": True,
                    "enable_ingress_gateway": True,
                    "ingress_gateway_type": "Internal",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        old_profile = self.models.ServiceMeshProfile(
            mode=CONST_AZURE_SERVICE_MESH_MODE_DISABLED,
            istio=self.models.IstioServiceMesh(),
        )
        new_profile, updated = ctx_0._handle_ingress_gateways_asm(old_profile)
        self.assertEqual(updated, True)
        self.assertEqual(new_profile, self.models.ServiceMeshProfile(
            mode="Istio",
            istio=self.models.IstioServiceMesh(
                components=self.models.IstioComponents(
                    ingress_gateways=[
                        self.models.IstioIngressGateway(
                            mode="Internal",
                            enabled=True,
                        )
                    ]
                )
            ),
        ))
        # ASM was never enabled on the cluster
        old_profile = self.models.ServiceMeshProfile(
            mode=CONST_AZURE_SERVICE_MESH_MODE_DISABLED,
        )
        new_profile, updated = ctx_0._handle_ingress_gateways_asm(old_profile)
        self.assertEqual(updated, True)
        self.assertEqual(new_profile, self.models.ServiceMeshProfile(
            mode="Istio",
            istio=self.models.IstioServiceMesh(
                components=self.models.IstioComponents(
                    ingress_gateways=[
                        self.models.IstioIngressGateway(
                            mode="Internal",
                            enabled=True,
                        )
                    ]
                )
            ),
        ))

    def test_handle_pluginca_asm(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "enable_azure_service_mesh": True,
                    "key_vault_id": "/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo",
                    "ca_cert_object_name": "my-ca-cert",
                    "ca_key_object_name": "my-ca-key",
                    "root_cert_object_name": "my-root-cert",
                    "cert_chain_object_name": "my-cert-chain",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        old_profile = self.models.ServiceMeshProfile(
            mode=CONST_AZURE_SERVICE_MESH_MODE_DISABLED,
            istio=self.models.IstioServiceMesh(),
        )
        new_profile, updated = ctx_0._handle_pluginca_asm(old_profile)
        self.assertEqual(updated, True)
        self.assertEqual(new_profile, self.models.ServiceMeshProfile(
            mode="Istio",
            istio=self.models.IstioServiceMesh(
                certificate_authority=self.models.IstioCertificateAuthority(
                    plugin=self.models.IstioPluginCertificateAuthority(
                        key_vault_id="/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo",
                        cert_object_name="my-ca-cert",
                        key_object_name="my-ca-key",
                        root_cert_object_name="my-root-cert",
                        cert_chain_object_name="my-cert-chain",
                    )
                )
            ),
        ))

    def test_handle_upgrade_asm(self):
        ctx_0 = AKSManagedClusterContext(
            self.cmd,
            AKSManagedClusterParamDict(
                {
                    "mesh_upgrade_command": CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START,
                    "revision": "asm-1-18",
                }
            ),
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        old_profile = self.models.ServiceMeshProfile(
            mode="Istio", istio=self.models.IstioServiceMesh(revisions=["asm-1-17"])
        )
        new_profile, updated = ctx_0._handle_upgrade_asm(old_profile)
        self.assertEqual(updated, True)
        self.assertEqual(new_profile, self.models.ServiceMeshProfile(
            mode="Istio",
            istio=self.models.IstioServiceMesh(revisions=["asm-1-17", "asm-1-18"]),
        ))


class AKSManagedClusterCreateDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)
        self.client = MockClient()

    def test_init(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        self.assertIsNotNone(dec_1.models)
        self.assertIsNotNone(dec_1.context)
        self.assertIsNotNone(dec_1.agentpool_decorator)
        self.assertIsNotNone(dec_1.agentpool_context)

    def test_ensure_mc(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_mc(None)
        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on inconsistent mc with internal context
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_mc(mc_1)

    def test_remove_restore_defaults_in_mc(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1._remove_defaults_in_mc(None)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1._restore_defaults_in_mc(None)
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1._remove_defaults_in_mc(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        ground_truth_mc_1.additional_properties = None
        self.assertEqual(dec_mc_1, ground_truth_mc_1)
        self.assertEqual(dec_1.context.get_intermediate("defaults_in_mc"), {"additional_properties": {}})

        dec_mc_2 = dec_1._restore_defaults_in_mc(dec_mc_1)
        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_init_mc(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "location": "test_location",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        dec_mc = dec_1.init_mc()
        ground_truth_mc = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc, ground_truth_mc)
        self.assertEqual(dec_mc, dec_1.context.mc)

    def test_set_up_agentpool_profile(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "nodepool_name": "test_np_name",
                "node_vm_size": "Standard_DSx_vy",
                "os_sku": None,
                "snapshot_id": "test_snapshot_id",
                "vnet_subnet_id": "test_vnet_subnet_id",
                "pod_subnet_id": "test_pod_subnet_id",
                "enable_node_public_ip": True,
                "node_public_ip_prefix_id": "test_node_public_ip_prefix_id",
                "enable_cluster_autoscaler": True,
                "min_count": 5,
                "max_count": 20,
                "node_count": 10,
                "nodepool_tags": {"k1": "v1"},
                "nodepool_labels": {"k1": "v1", "k2": "v2"},
                "node_osdisk_size": 100,
                "node_osdisk_type": "test_os_disk_type",
                "vm_set_type": None,
                "zones": ["tz1", "tz2"],
                "ppg": "test_ppg_id",
                "max_pods": 50,
                "enable_encryption_at_host": True,
                "enable_ultra_ssd": True,
                "enable_fips_image": True,
                "kubelet_config": None,
                "linux_os_config": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        mock_snapshot = Mock(
            kubernetes_version="",
            os_sku="snapshot_os_sku",
            os_type=None,
            vm_size="snapshot_vm_size",
        )
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            dec_mc_1 = dec_1.set_up_agentpool_profile(mc_1)
        ground_truth_agentpool_profile_1 = self.models.ManagedClusterAgentPoolProfile(
            name="test_np_name",
            orchestrator_version="",
            vm_size="Standard_DSx_vy",
            os_type=CONST_DEFAULT_NODE_OS_TYPE,
            os_sku="snapshot_os_sku",
            creation_data=self.models.CreationData(source_resource_id="test_snapshot_id"),
            vnet_subnet_id="test_vnet_subnet_id",
            pod_subnet_id="test_pod_subnet_id",
            enable_node_public_ip=True,
            node_public_ip_prefix_id="test_node_public_ip_prefix_id",
            enable_auto_scaling=True,
            min_count=5,
            max_count=20,
            count=10,
            node_labels={"k1": "v1", "k2": "v2"},
            tags={"k1": "v1"},
            node_taints=[],
            os_disk_size_gb=100,
            os_disk_type="test_os_disk_type",
            upgrade_settings=self.models.AgentPoolUpgradeSettings(),
            type=CONST_VIRTUAL_MACHINE_SCALE_SETS,
            availability_zones=["tz1", "tz2"],
            proximity_placement_group_id="test_ppg_id",
            max_pods=50,
            enable_encryption_at_host=True,
            enable_ultra_ssd=True,
            enable_fips=True,
            mode=CONST_NODEPOOL_MODE_SYSTEM,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        ground_truth_mc_1.agent_pool_profiles = [ground_truth_agentpool_profile_1]
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_set_up_mc_properties(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "name": "test_cluster",
                "resource_group_name": "test_rg_name",
                "tags": {"t1": "v1"},
                "kubernetes_version": "test_kubernetes_version",
                "dns_name_prefix": None,
                "node_osdisk_diskencryptionset_id": "test_node_osdisk_diskencryptionset_id",
                "disable_local_accounts": True,
                "disable_rbac": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_mc_properties(None)
        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=mock_profile,
        ):
            dec_mc_1 = dec_1.set_up_mc_properties(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            tags={"t1": "v1"},
            kubernetes_version="test_kubernetes_version",
            dns_prefix="testcluste-testrgname-1234-5",
            disk_encryption_set_id="test_node_osdisk_diskencryptionset_id",
            disable_local_accounts=True,
            enable_rbac=False,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_set_up_linux_profile(self):
        import paramiko

        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "admin_username": "azureuser",
                "no_ssh_key": False,
                "ssh_key_value": public_key,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_linux_profile(None)
        dec_mc_1 = dec_1.set_up_linux_profile(mc_1)

        ssh_config_1 = self.models.ContainerServiceSshConfiguration(
            public_keys=[self.models.ContainerServiceSshPublicKey(key_data=public_key)]
        )
        linux_profile_1 = self.models.ContainerServiceLinuxProfile(admin_username="azureuser", ssh=ssh_config_1)
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location", linux_profile=linux_profile_1)
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "admin_username": "test_user",
                "no_ssh_key": True,
                "ssh_key_value": "test_key",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_linux_profile(mc_2)

        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_windows_profile(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "windows_admin_username": None,
                "windows_admin_password": None,
                "enable_ahub": False,
                "enable_windows_gmsa": False,
                "gmsa_dns_server": None,
                "gmsa_root_domain_name": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_windows_profile(None)
        dec_mc_1 = dec_1.set_up_windows_profile(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "windows_admin_username": "test_win_admin_name",
                "windows_admin_password": None,
                "enable_ahub": True,
                "enable_windows_gmsa": True,
                "gmsa_dns_server": "test_gmsa_dns_server",
                "gmsa_root_domain_name": "test_gmsa_root_domain_name",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_pass",
            return_value="test_win_admin_pd",
        ):
            dec_mc_2 = dec_2.set_up_windows_profile(mc_2)

        gmsa_profile_2 = self.models.WindowsGmsaProfile(
            enabled=True,
            dns_server="test_gmsa_dns_server",
            root_domain_name="test_gmsa_root_domain_name",
        )
        windows_profile_2 = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_win_admin_name",
            admin_password="test_win_admin_pd",
            license_type="Windows_Server",
            gmsa_profile=gmsa_profile_2,
        )

        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location", windows_profile=windows_profile_2)
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "windows_admin_username": None,
                "windows_admin_password": None,
                "enable_ahub": True,
                "enable_windows_gmsa": True,
                "gmsa_dns_server": None,
                "gmsa_root_domain_name": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        with self.assertRaises(RequiredArgumentMissingError):
            dec_3.set_up_windows_profile(mc_3)

    def test_set_up_storage_profile(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"disable_disk_driver": True, "disable_file_driver": True, "disable_snapshot_controller": True, "enable_blob_driver": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.set_up_storage_profile(mc_1)
        storage_profile_1 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(enabled=False),
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(enabled=False),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(enabled=False),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(enabled=True),
        )
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location", storage_profile=storage_profile_1)
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_set_up_service_principal_profile(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "service_principal": None,
                "client_secret": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_service_principal_profile(None)
        dec_mc_1 = dec_1.set_up_service_principal_profile(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        # fail on mutually exclusive enable_managed_identity and service_principal/client_secret
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_2.set_up_service_principal_profile(mc_2)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": False,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.set_up_service_principal_profile(mc_3)
        service_principal_profile_3 = self.models.ManagedClusterServicePrincipalProfile(
            client_id="test_service_principal", secret="test_client_secret"
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile_3,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_process_add_role_assignment_for_vnet_subnet(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "vnet_subnet_id": None,
                "skip_subnet_role_assignment": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.process_add_role_assignment_for_vnet_subnet(None)
        dec_1.process_add_role_assignment_for_vnet_subnet(mc_1)
        self.assertEqual(
            dec_1.context.get_intermediate("need_post_creation_vnet_permission_granting"),
            False,
        )

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "skip_subnet_role_assignment": False,
                "assign_identity": None,
                "yes": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.subnet_role_assignment_exists",
            return_value=False,
        ):
            dec_2.process_add_role_assignment_for_vnet_subnet(mc_2)
        self.assertEqual(
            dec_2.context.get_intermediate("need_post_creation_vnet_permission_granting"),
            True,
        )

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "skip_subnet_role_assignment": False,
                "assign_identity": None,
                "yes": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.subnet_role_assignment_exists",
            return_value=False,
        ):
            dec_3.process_add_role_assignment_for_vnet_subnet(mc_3)
        self.assertEqual(
            dec_3.context.get_intermediate("need_post_creation_vnet_permission_granting"),
            True,
        )

        # custom value
        dec_4 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "skip_subnet_role_assignment": False,
                "assign_identity": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        service_principal_profile_4 = self.models.ManagedClusterServicePrincipalProfile(
            client_id="test_service_principal", secret="test_client_secret"
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            service_principal_profile=service_principal_profile_4,
        )
        dec_4.context.attach_mc(mc_4)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.subnet_role_assignment_exists",
            return_value=False,
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_role_assignment",
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
            dec_4.context.get_intermediate("need_post_creation_vnet_permission_granting"),
            False,
        )

        # custom value
        identity_obj = Mock(
            principal_id="test_object_id",
        )
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext.get_identity_by_msi_client",
            return_value=identity_obj,
        ):
            dec_5 = AKSManagedClusterCreateDecorator(
                self.cmd,
                self.client,
                {
                    "enable_managed_identity": True,
                    "vnet_subnet_id": "test_vnet_subnet_id",
                    "skip_subnet_role_assignment": False,
                    "assign_identity": "test_assign_identity",
                },
                ResourceType.MGMT_CONTAINERSERVICE,
            )
            mc_5 = self.models.ManagedCluster(
                location="test_location",
            )
            dec_5.context.attach_mc(mc_5)
            with patch(
                "azure.cli.command_modules.acs.managed_cluster_decorator.subnet_role_assignment_exists",
                return_value=False,
            ), patch(
                "azure.cli.command_modules.acs.managed_cluster_decorator.add_role_assignment",
                return_value=False,
            ) as add_role_assignment:
                dec_5.process_add_role_assignment_for_vnet_subnet(mc_5)
            add_role_assignment.assert_called_once_with(
                self.cmd,
                "Network Contributor",
                "test_object_id",
                is_service_principal=False,
                scope="test_vnet_subnet_id",
            )
            self.assertEqual(
                dec_5.context.get_intermediate("need_post_creation_vnet_permission_granting"),
                False,
            )

    def test_process_attach_acr(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "attach_acr": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.process_attach_acr(None)
        dec_1.process_attach_acr(mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": True,
                "no_wait": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        # fail on mutually exclusive attach_acr, enable_managed_identity and no_wait
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_2.process_attach_acr(mc_2)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "attach_acr": "test_attach_acr",
                "enable_managed_identity": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        # fail on service_principal/client_secret not specified
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext._get_enable_managed_identity",
            return_value=False,
        ), self.assertRaises(RequiredArgumentMissingError):
            dec_3.process_attach_acr(mc_3)
        service_principal_profile_3 = self.models.ManagedClusterServicePrincipalProfile(
            client_id="test_service_principal", secret="test_client_secret"
        )
        mc_3.service_principal_profile = service_principal_profile_3
        dec_3.context.set_intermediate("subscription_id", "test_subscription_id")
        registry = Mock(id="test_registry_id")
        with patch(
            "azure.cli.command_modules.acs._roleassignments.get_resource_by_name",
            return_value=registry,
        ), patch("azure.cli.command_modules.acs._roleassignments.ensure_aks_acr_role_assignment") as ensure_assignment:
            dec_3.process_attach_acr(mc_3)
        ensure_assignment.assert_called_once_with(self.cmd, "test_service_principal", "test_registry_id", False, True)

    def test_set_up_network_profile(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": None,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": None,
                "load_balancer_idle_timeout": None,
                "load_balancer_backend_pool_type": CONST_LOAD_BALANCER_BACKEND_POOL_TYPE_NODE_IP,
                "outbound_type": None,
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "network_policy": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_network_profile(None)
        dec_mc_1 = dec_1.set_up_network_profile(mc_1)

        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            network_plugin=None,
            pod_cidr="10.244.0.0/16",  # default value in SDK
            service_cidr="10.0.0.0/16",  # default value in SDK
            dns_service_ip="10.0.0.10",  # default value in SDK
            load_balancer_sku="standard",
            outbound_type="loadBalancer",
        )
        load_balancer_profile_1 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            backend_pool_type=CONST_LOAD_BALANCER_BACKEND_POOL_TYPE_NODE_IP,
        )
        network_profile_1.load_balancer_profile = load_balancer_profile_1
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location", network_profile=network_profile_1)
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": 3,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": 5,
                "load_balancer_idle_timeout": None,
                "outbound_type": None,
                "network_plugin": "kubenet",
                "pod_cidr": "10.246.0.0/16",
                "service_cidr": None,
                "dns_service_ip": None,
                "network_policy": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_network_profile(mc_2)

        load_balancer_profile_2 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            managed_outbound_i_ps=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileManagedOutboundIPs(
                count=3
            ),
            allocated_outbound_ports=5,
        )

        network_profile_2 = self.models.ContainerServiceNetworkProfile(
            network_plugin="kubenet",
            pod_cidr="10.246.0.0/16",
            service_cidr=None,  # overwritten to None
            dns_service_ip=None,  # overwritten to None
            load_balancer_sku="standard",
            outbound_type="loadBalancer",
            load_balancer_profile=load_balancer_profile_2,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location", network_profile=network_profile_2)
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "load_balancer_sku": "basic",
                "load_balancer_managed_outbound_ip_count": None,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": "test_ip_prefix_1,test_ip_prefix_2",
                "load_balancer_outbound_ports": None,
                "load_balancer_idle_timeout": 20,
                "outbound_type": None,
                "network_plugin": None,
                "pod_cidr": None,
                "service_cidr": None,
                "dns_service_ip": None,
                "network_policy": None,
                "nat_gateway_managed_outbound_ip_count": None,
                "nat_gateway_idle_timeout": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.set_up_network_profile(mc_3)

        network_profile_3 = self.models.ContainerServiceNetworkProfile(
            network_plugin=None,  # None is overriden in the CLI because we don't want the default from the SDK
            pod_cidr="10.244.0.0/16",  # default value in SDK
            service_cidr="10.0.0.0/16",  # default value in SDK
            dns_service_ip="10.0.0.10",  # default value in SDK
            load_balancer_sku="basic",
            outbound_type="loadBalancer",
            load_balancer_profile=None,  # profile dropped when lb sku is basic
        )
        ground_truth_mc_3 = self.models.ManagedCluster(location="test_location", network_profile=network_profile_3)
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_set_up_network_profile_ipv6(self):
        # custom value
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": 3,
                "load_balancer_managed_outbound_ipv6_count": 3,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": 5,
                "load_balancer_idle_timeout": None,
                "outbound_type": None,
                "network_plugin": "kubenet",
                "pod_cidr": None,
                "service_cidr": None,
                "pod_cidrs": "10.246.0.0/16,2002:ab12::/64",
                "service_cidrs": "192.168.0.0/16,2001:abcd::/84",
                "ip_families": "ipv4,ipv6",
                "dns_service_ip": None,
                "network_policy": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.set_up_network_profile(mc_1)

        load_balancer_profile_1 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            managed_outbound_i_ps=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileManagedOutboundIPs(
                count=3,
                count_ipv6=3,
            ),
            allocated_outbound_ports=5,
        )

        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            network_plugin="kubenet",
            pod_cidrs=["10.246.0.0/16", "2002:ab12::/64"],
            service_cidrs=["192.168.0.0/16", "2001:abcd::/84"],
            ip_families=["ipv4","ipv6"],
            pod_cidr=None, # overwritten to None
            service_cidr=None,  # overwritten to None
            dns_service_ip=None,  # overwritten to None
            load_balancer_sku="standard",
            outbound_type="loadBalancer",
            load_balancer_profile=load_balancer_profile_1,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location", network_profile=network_profile_1)
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_build_http_application_routing_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        http_application_routing_addon_profile = dec_1.build_http_application_routing_addon_profile()
        ground_truth_http_application_routing_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
        )
        self.assertEqual(
            http_application_routing_addon_profile,
            ground_truth_http_application_routing_addon_profile,
        )

    def test_build_kube_dashboard_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        kube_dashboard_addon_profile = dec_1.build_kube_dashboard_addon_profile()
        ground_truth_kube_dashboard_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
        )
        self.assertEqual(
            kube_dashboard_addon_profile,
            ground_truth_kube_dashboard_addon_profile,
        )

    def test_build_monitoring_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "location": "test_location",
                "enable_addons": "monitoring",
                "workspace_resource_id": "test_workspace_resource_id",
                "enable_msi_auth_for_monitoring": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=mock_profile,
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_container_insights_for_monitoring",
            return_value=None,
        ):
            self.assertEqual(dec_1.context.get_intermediate("monitoring_addon_enabled"), None)
            monitoring_addon_profile = dec_1.build_monitoring_addon_profile()
            ground_truth_monitoring_addon_profile = self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: "/test_workspace_resource_id",
                    CONST_MONITORING_USING_AAD_MSI_AUTH: "false",
                },
            )
            self.assertEqual(monitoring_addon_profile, ground_truth_monitoring_addon_profile)
            self.assertEqual(dec_1.context.get_intermediate("monitoring_addon_enabled"), True)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_addons": "",
                "workspace_resource_id": "test_workspace_resource_id",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on enable_addons (monitoring) not specified
        with self.assertRaises(RequiredArgumentMissingError):
            dec_2.build_monitoring_addon_profile()

    def test_build_azure_policy_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_policy_addon_profile = dec_1.build_azure_policy_addon_profile()
        ground_truth_azure_policy_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
        )
        self.assertEqual(azure_policy_addon_profile, ground_truth_azure_policy_addon_profile)

    def test_build_virtual_node_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"aci_subnet_name": "test_aci_subnet_name"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        self.assertEqual(dec_1.context.get_intermediate("virtual_node_addon_enabled"), None)
        virtual_node_addon_profile = dec_1.build_virtual_node_addon_profile()
        ground_truth_virtual_node_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={CONST_VIRTUAL_NODE_SUBNET_NAME: "test_aci_subnet_name"},
        )
        self.assertEqual(virtual_node_addon_profile, ground_truth_virtual_node_addon_profile)
        self.assertEqual(dec_1.context.get_intermediate("virtual_node_addon_enabled"), True)

    def test_build_ingress_appgw_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        self.assertEqual(dec_1.context.get_intermediate("ingress_appgw_addon_enabled"), None)
        ingress_appgw_addon_profile = dec_1.build_ingress_appgw_addon_profile()
        ground_truth_ingress_appgw_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        self.assertEqual(
            ingress_appgw_addon_profile,
            ground_truth_ingress_appgw_addon_profile,
        )
        self.assertEqual(dec_1.context.get_intermediate("ingress_appgw_addon_enabled"), True)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "appgw_name": "test_appgw_name",
                "appgw_subnet_cidr": "test_appgw_subnet_cidr",
                "appgw_id": "test_appgw_id",
                "appgw_subnet_id": "test_appgw_subnet_id",
                "appgw_watch_namespace": "test_appgw_watch_namespace",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        self.assertEqual(dec_2.context.get_intermediate("ingress_appgw_addon_enabled"), None)
        ingress_appgw_addon_profile = dec_2.build_ingress_appgw_addon_profile()
        ground_truth_ingress_appgw_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME: "test_appgw_name",
                CONST_INGRESS_APPGW_SUBNET_CIDR: "test_appgw_subnet_cidr",
                CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID: "test_appgw_id",
                CONST_INGRESS_APPGW_SUBNET_ID: "test_appgw_subnet_id",
                CONST_INGRESS_APPGW_WATCH_NAMESPACE: "test_appgw_watch_namespace",
            },
        )
        self.assertEqual(
            ingress_appgw_addon_profile,
            ground_truth_ingress_appgw_addon_profile,
        )
        self.assertEqual(dec_2.context.get_intermediate("ingress_appgw_addon_enabled"), True)

    def test_build_confcom_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        confcom_addon_profile = dec_1.build_confcom_addon_profile()
        ground_truth_confcom_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "false"},
        )
        self.assertEqual(confcom_addon_profile, ground_truth_confcom_addon_profile)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_sgxquotehelper": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        confcom_addon_profile = dec_2.build_confcom_addon_profile()
        ground_truth_confcom_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "true"},
        )
        self.assertEqual(confcom_addon_profile, ground_truth_confcom_addon_profile)

    def test_build_open_service_mesh_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        open_service_mesh_addon_profile = dec_1.build_open_service_mesh_addon_profile()
        ground_truth_open_service_mesh_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        self.assertEqual(
            open_service_mesh_addon_profile,
            ground_truth_open_service_mesh_addon_profile,
        )

    def test_build_azure_keyvault_secrets_provider_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_keyvault_secrets_provider_addon_profile = dec_1.build_azure_keyvault_secrets_provider_addon_profile()
        ground_truth_azure_keyvault_secrets_provider_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_SECRET_ROTATION_ENABLED: "false",
                CONST_ROTATION_POLL_INTERVAL: "2m",
            },
        )
        self.assertEqual(
            azure_keyvault_secrets_provider_addon_profile,
            ground_truth_azure_keyvault_secrets_provider_addon_profile,
        )

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_secret_rotation": True, "rotation_poll_interval": "30m"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_keyvault_secrets_provider_addon_profile = dec_2.build_azure_keyvault_secrets_provider_addon_profile()
        ground_truth_azure_keyvault_secrets_provider_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_SECRET_ROTATION_ENABLED: "true",
                CONST_ROTATION_POLL_INTERVAL: "30m",
            },
        )
        self.assertEqual(
            azure_keyvault_secrets_provider_addon_profile,
            ground_truth_azure_keyvault_secrets_provider_addon_profile,
        )

    def test_set_up_addon_profiles(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_addons": None,
                "workspace_resource_id": None,
                "enable_msi_auth_for_monitoring": None,
                "aci_subnet_name": None,
                "appgw_name": None,
                "appgw_subnet_cidr": None,
                "appgw_id": None,
                "appgw_subnet_id": None,
                "appgw_watch_namespace": None,
                "enable_sgxquotehelper": False,
                "enable_secret_rotation": False,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_addon_profiles(None)
        dec_mc_1 = dec_1.set_up_addon_profiles(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location", addon_profiles={})
        self.assertEqual(dec_mc_1, ground_truth_mc_1)
        self.assertEqual(dec_1.context.get_intermediate("monitoring_addon_enabled"), None)
        self.assertEqual(dec_1.context.get_intermediate("virtual_node_addon_enabled"), None)
        self.assertEqual(dec_1.context.get_intermediate("ingress_appgw_addon_enabled"), None)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "location": "test_location",
                "vnet_subnet_id": "test_vnet_subnet_id",
                "enable_addons": "http_application_routing,monitoring,virtual-node,kube-dashboard,azure-policy,ingress-appgw,confcom,open-service-mesh,azure-keyvault-secrets-provider",
                "workspace_resource_id": "test_workspace_resource_id",
                "enable_msi_auth_for_monitoring": False,
                "aci_subnet_name": "test_aci_subnet_name",
                "appgw_name": "test_appgw_name",
                "appgw_subnet_cidr": "test_appgw_subnet_cidr",
                "appgw_id": "test_appgw_id",
                "appgw_subnet_id": "test_appgw_subnet_id",
                "appgw_watch_namespace": "test_appgw_watch_namespace",
                "enable_sgxquotehelper": True,
                "enable_secret_rotation": True,
                "rotation_poll_interval": "30m",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=mock_profile,
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_container_insights_for_monitoring",
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
                    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: "/test_workspace_resource_id",
                    CONST_MONITORING_USING_AAD_MSI_AUTH: "false",
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
            CONST_OPEN_SERVICE_MESH_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={},
            ),
            CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_SECRET_ROTATION_ENABLED: "true",
                    CONST_ROTATION_POLL_INTERVAL: "30m",
                },
            ),
        }
        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location", addon_profiles=addon_profiles_2)
        self.assertEqual(dec_mc_2, ground_truth_mc_2)
        self.assertEqual(dec_2.context.get_intermediate("monitoring_addon_enabled"), True)
        self.assertEqual(dec_2.context.get_intermediate("virtual_node_addon_enabled"), True)
        self.assertEqual(dec_2.context.get_intermediate("ingress_appgw_addon_enabled"), True)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
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
                "useAADAuth": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        # fail on invalid enable_addons
        with self.assertRaises(InvalidArgumentValueError):
            dec_3.set_up_addon_profiles(mc_3)

        # custom value
        dec_4 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_addons": "virtual-node",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        dec_4.context.attach_mc(mc_4)
        # fail on aci_subnet_name/vnet_subnet_id not specified
        with self.assertRaises(RequiredArgumentMissingError):
            dec_4.set_up_addon_profiles(mc_4)

    def test_set_up_aad_profile(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
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
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_aad_profile(None)
        dec_mc_1 = dec_1.set_up_aad_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
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
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_aad_profile(mc_2)

        aad_profile_2 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=True,
            admin_group_object_i_ds=["test_value_1test_value_2"],
        )
        ground_truth_mc_2 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_2)
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
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
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        profile = Mock(get_login_credentials=Mock(return_value=(None, None, "test_aad_tenant_id")))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=profile,
        ):
            dec_mc_3 = dec_3.set_up_aad_profile(mc_3)

        aad_profile_3 = self.models.ManagedClusterAADProfile(
            client_app_id="test_aad_client_app_id",
            tenant_id="test_aad_tenant_id",
        )
        ground_truth_mc_3 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_3)
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # custom value
        dec_4 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
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
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        dec_4.context.attach_mc(mc_4)
        # fail on mutually exclusive enable_azure_rbac and disable_rbac
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_4.set_up_aad_profile(mc_4)

    def test_set_up_api_server_access_profile(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": False,
                "disable_public_fqdn": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_api_server_access_profile(None)
        dec_mc_1 = dec_1.set_up_api_server_access_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": "test_ip_1, test_ip_2",
                "enable_private_cluster": False,
                "disable_public_fqdn": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_api_server_access_profile(mc_2)

        api_server_access_profile_2 = self.models.ManagedClusterAPIServerAccessProfile(
            authorized_ip_ranges=["test_ip_1", "test_ip_2"],
            enable_private_cluster=None,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": True,
                "disable_public_fqdn": True,
                "private_dns_zone": None,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.set_up_api_server_access_profile(mc_3)

        api_server_access_profile_3 = self.models.ManagedClusterAPIServerAccessProfile(
            authorized_ip_ranges=[],
            enable_private_cluster=True,
            enable_private_cluster_public_fqdn=False,
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_3,
            fqdn_subdomain="test_fqdn_subdomain",
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # invalid value
        dec_4 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": "test_api_server_authorized_ip_ranges",
                "enable_private_cluster": True,
                "disable_public_fqdn": False,
                "private_dns_zone": None,
                "fqdn_subdomain": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        dec_4.context.attach_mc(mc_4)
        # fail on mutually exclusive enable_private_cluster and api_server_authorized_ip_ranges
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_4.set_up_api_server_access_profile(mc_4)

        # invalid value
        dec_5 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": None,
                "enable_private_cluster": True,
                "disable_public_fqdn": False,
                "private_dns_zone": CONST_PRIVATE_DNS_ZONE_SYSTEM,
                "fqdn_subdomain": "test_fqdn_subdomain",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(location="test_location")
        dec_5.context.attach_mc(mc_5)
        # fail on invalid private_dns_zone when fqdn_subdomain is specified
        with self.assertRaises(InvalidArgumentValueError):
            dec_5.set_up_api_server_access_profile(mc_5)

    def test_set_up_identity(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": False,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
                "assign_identity": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_identity(None)
        dec_mc_1 = dec_1.set_up_identity(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "assign_identity": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
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
        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "assign_identity": "test_assign_identity",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
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
        dec_4 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": False,
                "service_principal": "test_service_principal",
                "client_secret": "test_client_secret",
                "assign_identity": "test_assign_identity",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(location="test_location")
        dec_4.context.attach_mc(mc_4)
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            dec_4.set_up_identity(mc_4)

        # custom, identity backfilled to msi as no sp specified
        dec_5 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(location="test_location")
        dec_5.context.attach_mc(mc_5)
        dec_mc_5 = dec_5.set_up_identity(mc_5)
        identity_5 = self.models.ManagedClusterIdentity(
            type="SystemAssigned",
        )
        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_5,
        )
        self.assertEqual(dec_mc_5, ground_truth_mc_5)

    def test_set_up_identity_profile(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "assign_identity": None,
                "assign_kubelet_identity": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
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
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext.get_identity_by_msi_client",
            side_effect=[identity_obj_1, identity_obj_2],
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_cluster_identity_permission_on_kubelet_identity"
        ) as mock_ensure_method:
            dec_2 = AKSManagedClusterCreateDecorator(
                self.cmd,
                self.client,
                {
                    "enable_managed_identity": True,
                    "assign_identity": "test_assign_identity",
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                },
                ResourceType.MGMT_CONTAINERSERVICE,
            )
            mc_2 = self.models.ManagedCluster(location="test_location")
            dec_2.context.attach_mc(mc_2)
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
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "auto_upgrade_channel": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_auto_upgrade_profile(None)
        dec_mc_1 = dec_1.set_up_auto_upgrade_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "auto_upgrade_channel": "test_auto_upgrade_channel",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
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
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "cluster_autoscaler_profile": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_auto_scaler_profile(None)
        dec_mc_1 = dec_1.set_up_auto_scaler_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "cluster_autoscaler_profile": {"expander": "random"},
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_auto_scaler_profile(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile={"expander": "random"},
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_sku(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "uptime_sla": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_sku(None)
        dec_mc_1 = dec_1.set_up_sku(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "uptime_sla": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_sku(mc_2)
        sku = self.models.ManagedClusterSKU(
            name="Base",
            tier="Standard",
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=sku,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_set_up_extended_location(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "edge_zone": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_extended_location(None)
        dec_mc_1 = dec_1.set_up_extended_location(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "edge_zone": "test_edge_zone",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
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

    def test_set_up_node_resource_group(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"node_resource_group": "test_node_resource_group"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_node_resource_group(None)
        dec_mc_1 = dec_1.set_up_node_resource_group(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            node_resource_group="test_node_resource_group",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_set_up_defender(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_defender": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate("subscription_id", "test_subscription_id")

        with patch(
                "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_default_log_analytics_workspace_for_monitoring",
                return_value="test_workspace_resource_id",
        ):
            dec_mc_1 = dec_1.set_up_defender(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            security_profile=self.models.ManagedClusterSecurityProfile(
                defender=self.models.ManagedClusterSecurityProfileDefender(
                    log_analytics_workspace_resource_id="test_workspace_resource_id",
                    security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                        enabled=True
                    ),
                )
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_set_up_workload_identity_profile__default_value(self):
        dec = AKSManagedClusterCreateDecorator(self.cmd, self.client, {}, ResourceType.MGMT_CONTAINERSERVICE)
        mc = self.models.ManagedCluster(location="test_location")
        dec.context.attach_mc(mc)
        updated_mc = dec.set_up_workload_identity_profile(mc)
        self.assertIsNone(updated_mc.security_profile)

    def test_set_up_workload_identity_profile__default_value_with_security_profile(self):
        dec = AKSManagedClusterCreateDecorator(self.cmd, self.client, {}, ResourceType.MGMT_CONTAINERSERVICE)
        mc = self.models.ManagedCluster(location="test_location")
        mc.security_profile = self.models.ManagedClusterSecurityProfile()
        dec.context.attach_mc(mc)
        updated_mc = dec.set_up_workload_identity_profile(mc)
        self.assertIsNone(updated_mc.security_profile.workload_identity)

    def test_set_up_workload_identity_profile__enabled(self):
        dec = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_oidc_issuer": True,
                "enable_workload_identity": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc = self.models.ManagedCluster(location="test_location")
        dec.context.attach_mc(mc)
        updated_mc = dec.set_up_workload_identity_profile(mc)
        self.assertTrue(updated_mc.security_profile.workload_identity.enabled)

    def test_set_up_azure_service_mesh(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.set_up_azure_service_mesh_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_azure_service_mesh": True,
                "revision": "asm-1-88"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_azure_service_mesh_profile(mc_2)

        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-88"]
                )
            ),
        )

        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_azure_service_mesh": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.set_up_azure_service_mesh_profile(mc_3)

        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh()
            ),
        )

        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_construct_mc_profile_default(self):
        import inspect

        import paramiko
        from azure.cli.command_modules.acs.custom import aks_create

        optional_params = {}
        positional_params = []
        for _, v in inspect.signature(aks_create).parameters.items():
            if v.default != v.empty:
                optional_params[v.name] = v.default
            else:
                positional_params.append(v.name)
        ground_truth_positional_params = [
            "cmd",
            "client",
            "resource_group_name",
            "name",
            "ssh_key_value",
        ]
        self.assertEqual(positional_params, ground_truth_positional_params)

        # prepare ssh key
        key = paramiko.RSAKey.generate(2048)
        public_key = "{} {}".format(key.get_name(), key.get_base64())

        # prepare a dictionary of default parameters
        raw_param_dict = {
            "resource_group_name": "test_rg_name",
            "name": "test_name",
            "ssh_key_value": public_key,
        }
        raw_param_dict.update(optional_params)

        # default value in `aks_create`
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            raw_param_dict,
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.get_rg_location",
            return_value="test_location",
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile",
            return_value=mock_profile,
        ):
            dec_mc_1 = dec_1.construct_mc_profile_default()

        upgrade_settings_1 = self.models.AgentPoolUpgradeSettings()
        ground_truth_agentpool_1 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            orchestrator_version="",
            vm_size=CONST_DEFAULT_NODE_VM_SIZE,
            os_type=CONST_DEFAULT_NODE_OS_TYPE,
            enable_node_public_ip=False,
            enable_auto_scaling=False,
            count=3,
            node_taints=[],
            upgrade_settings=upgrade_settings_1,
            type=CONST_VIRTUAL_MACHINE_SCALE_SETS,
            enable_encryption_at_host=False,
            enable_ultra_ssd=False,
            enable_fips=False,
            mode=CONST_NODEPOOL_MODE_SYSTEM,
        )
        ssh_config_1 = self.models.ContainerServiceSshConfiguration(
            public_keys=[self.models.ContainerServiceSshPublicKey(key_data=public_key)]
        )
        linux_profile_1 = self.models.ContainerServiceLinuxProfile(admin_username="azureuser", ssh=ssh_config_1)
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="standard",
            network_plugin=None,
        )
        identity_1 = self.models.ManagedClusterIdentity(type="SystemAssigned")
        storage_profile_1 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=None,
            file_csi_driver=None,
            blob_csi_driver=None,
            snapshot_controller=None,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            dns_prefix="testname-testrgname-1234-5",
            kubernetes_version="",
            addon_profiles={},
            enable_rbac=True,
            agent_pool_profiles=[ground_truth_agentpool_1],
            linux_profile=linux_profile_1,
            network_profile=network_profile_1,
            identity=identity_1,
            storage_profile=storage_profile_1,
            disable_local_accounts=False,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_1.context.raw_param.print_usage_statistics()

    def test_check_is_postprocessing_required(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), False)
        dec_1.context.set_intermediate("monitoring_addon_enabled", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_1.context.remove_intermediate("monitoring_addon_enabled")
        dec_1.context.set_intermediate("ingress_appgw_addon_enabled", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_1.context.remove_intermediate("ingress_appgw_addon_enabled")
        dec_1.context.set_intermediate("virtual_node_addon_enabled", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_1.context.remove_intermediate("virtual_node_addon_enabled")
        dec_1.context.set_intermediate("need_post_creation_vnet_permission_granting", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_managed_identity": True, "attach_acr": "test_attach_acr"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        self.assertEqual(dec_2.check_is_postprocessing_required(mc_2), True)

    def test_immediate_processing_after_request(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"vnet_subnet_id": "test_vnet_subnet_id"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate("need_post_creation_vnet_permission_granting", True)
        self.client.get = Mock(return_value=Mock(identity=Mock(principal_id="test_principal_id")))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_role_assignment", return_value=False
        ) as mock_add:
            dec_1.immediate_processing_after_request(mc_1)
        mock_add.assert_called_once_with(
            self.cmd,
            "Network Contributor",
            "test_principal_id",
            scope="test_vnet_subnet_id",
            is_service_principal=False,
        )

    def test_postprocessing_after_mc_created(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_msi_auth_for_monitoring": False},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate("monitoring_addon_enabled", True)
        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch("azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_monitoring_role_assignment"
        ) as mock_add:
            dec_1.postprocessing_after_mc_created(mc_1)
        mock_add.assert_called_once_with(mc_1, ANY, self.cmd)

        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "resource_group_name": "test_rg_name",
                "name": "test_name",
                "enable_msi_auth_for_monitoring": True,
                "enable_addons": "monitoring"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        monitoring_addon_profile_2 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_MONITORING_ADDON_NAME: monitoring_addon_profile_2,
            },
        )
        dec_2.context.attach_mc(mc_2)
        dec_2.context.set_intermediate("monitoring_addon_enabled", True)
        mock_profile_2 = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile_2
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_container_insights_for_monitoring"
        ) as mock_ensure:
            dec_2.postprocessing_after_mc_created(mc_2)
        mock_ensure.assert_called_once_with(
            self.cmd,
            monitoring_addon_profile_2,
            "1234-5678-9012",
            "test_rg_name",
            "test_name",
            "test_location",
            remove_monitoring=False,
            aad_route=True,
            create_dcr=False,
            create_dcra=True,
            enable_syslog=None,
            data_collection_settings=None,
            is_private_cluster=None,
            ampls_resource_id=None,
            enable_high_log_scale_mode=None,
        )

        dec_3 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"vnet_subnet_id": "test_vnet_subnet_id", "enable_managed_identity": True, "attach_acr": "test_attach_acr"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        dec_3.context.set_intermediate("ingress_appgw_addon_enabled", True)
        dec_3.context.set_intermediate("virtual_node_addon_enabled", True)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_ingress_appgw_addon_role_assignment"
        ) as mock_add_ingress_3, patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_virtual_node_role_assignment"
        ) as mock_add_virtual_3:
            dec_3.postprocessing_after_mc_created(mc_3)
        mock_add_ingress_3.assert_called_once_with(mc_3, self.cmd)
        mock_add_virtual_3.assert_called_once_with(self.cmd, mc_3, "test_vnet_subnet_id")

        dec_4 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_managed_identity": True, "attach_acr": "test_attach_acr"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id", object_id="test_object_id"
                )
            },
        )
        dec_4.context.attach_mc(mc_4)
        mock_profile_4 = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile_4
        ), patch("azure.cli.command_modules.acs.managed_cluster_decorator.ensure_aks_acr") as mock_ensure_4:
            dec_4.postprocessing_after_mc_created(mc_4)
        mock_ensure_4.assert_called_once_with(
            self.cmd,
            assignee="test_object_id",
            acr_name_or_id="test_attach_acr",
            subscription_id="1234-5678-9012",
            is_service_principal=False,
        )

    def test_put_mc(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_msi_auth_for_monitoring": False},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.sdk_no_wait",
            return_value=mc_1,
        ):
            self.assertEqual(dec_1.put_mc(mc_1), mc_1)

        dec_1.context.set_intermediate("monitoring_addon_enabled", True)
        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch("azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_monitoring_role_assignment"
        ) as mock_add, patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.LongRunningOperation",
            return_value=Mock(return_value=mc_1),
        ):
            self.assertEqual(dec_1.put_mc(mc_1), mc_1)
        mock_add.assert_called_once_with(mc_1, ANY, self.cmd)

    def test_create_mc(self):
        # raise exception
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.create_mc(None)

        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        err_1 = HttpResponseError(message="not found in Active Directory tenant")
        # fail on mock HttpResponseError, max retry exceeded
        with self.assertRaises(AzCLIError), patch("time.sleep"), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterCreateDecorator.put_mc",
            side_effect=err_1,
        ):
            dec_1.create_mc(mc_1)

        # raise exception
        resp = Mock(
            reason="error reason",
            status_code=500,
            text=Mock(return_value="error text"),
        )
        err_2 = HttpResponseError(response=resp)
        # fail on mock HttpResponseError
        with self.assertRaises(AzureInternalError), patch("time.sleep"), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterCreateDecorator.put_mc",
            side_effect=[err_1, err_2],
        ):
            dec_1.create_mc(mc_1)

        # return mc
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterCreateDecorator.put_mc",
            return_value=mc_1,
        ):
            self.assertEqual(dec_1.create_mc(mc_1), mc_1)

    def test_set_up_http_proxy_config(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"http_proxy_config": get_test_data_file_path("httpproxyconfig.json")},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_http_proxy_config(None)
        dec_mc_1 = dec_1.set_up_http_proxy_config(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            http_proxy_config={
                "httpProxy": "http://cli-proxy-vm:3128/",
                "httpsProxy": "https://cli-proxy-vm:3129/",
                "noProxy": ["localhost", "127.0.0.1"],
                "trustedCa": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZHekNDQXdPZ0F3SUJBZ0lVT1FvajhDTFpkc2Vscjk3cnZJd3g1T0xEc3V3d0RRWUpLb1pJaHZjTkFRRUwKQlFBd0Z6RVZNQk1HQTFVRUF3d01ZMnhwTFhCeWIzaDVMWFp0TUI0WERUSXlNRE13T0RFMk5EUTBOMW9YRFRNeQpNRE13TlRFMk5EUTBOMW93RnpFVk1CTUdBMVVFQXd3TVkyeHBMWEJ5YjNoNUxYWnRNSUlDSWpBTkJna3Foa2lHCjl3MEJBUUVGQUFPQ0FnOEFNSUlDQ2dLQ0FnRUEvTVB0VjVCVFB0NmNxaTRSZE1sbXIzeUlzYTJ1anpjaHh2NGgKanNDMUR0blJnb3M1UzQxUEgwcmkrM3RUU1ZYMzJ5cndzWStyRDFZUnVwbTZsbUU3R2hVNUkwR2k5b3prU0YwWgpLS2FKaTJveXBVL0ZCK1FQcXpvQ1JzTUV3R0NibUtGVmw4VnVoeW5kWEs0YjRrYmxyOWJsL2V1d2Q3TThTYnZ6CldVam5lRHJRc2lJc3J6UFQ0S0FaTHFjdHpEZTRsbFBUN1lLYTMzaGlFUE9mdldpWitkcWthUUE5UDY0eFhTeW4KZkhYOHVWQUozdUJWSmVHeEQwcGtOSjdqT3J5YVV1SEh1Y1U4UzltSWpuS2pBQjVhUGpMSDV4QXM2bG1iMzEyMgp5KzF0bkVBbVhNNTBEK1VvRWpmUzZIT2I1cmRpcVhHdmMxS2JvS2p6a1BDUnh4MmE3MmN2ZWdVajZtZ0FKTHpnClRoRTFsbGNtVTRpemd4b0lNa1ZwR1RWT0xMbjFWRkt1TmhNWkN2RnZLZ25Lb0F2M0cwRlVuZldFYVJSalNObUQKTFlhTURUNUg5WnQycERJVWpVR1N0Q2w3Z1J6TUVuWXdKTzN5aURwZzQzbzVkUnlzVXlMOUpmRS9OaDdUZzYxOApuOGNKL1c3K1FZYllsanVyYXA4cjdRRlNyb2wzVkNoRkIrT29yNW5pK3ZvaFNBd0pmMFVsTXBHM3hXbXkxVUk0ClRGS2ZGR1JSVHpyUCs3Yk53WDVoSXZJeTVWdGd5YU9xSndUeGhpL0pkeHRPcjJ0QTVyQ1c3K0N0Z1N2emtxTkUKWHlyN3ZrWWdwNlk1TFpneTR0VWpLMEswT1VnVmRqQk9oRHBFenkvRkY4dzFGRVZnSjBxWS9yV2NMa0JIRFQ4Ugp2SmtoaW84Q0F3RUFBYU5mTUYwd0Z3WURWUjBSQkJBd0RvSU1ZMnhwTFhCeWIzaDVMWFp0TUJJR0ExVWRFd0VCCi93UUlNQVlCQWY4Q0FRQXdEd1lEVlIwUEFRSC9CQVVEQXdmbmdEQWRCZ05WSFNVRUZqQVVCZ2dyQmdFRkJRY0QKQWdZSUt3WUJCUVVIQXdFd0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dJQkFBb21qQ3lYdmFRT3hnWUs1MHNYTEIyKwp3QWZkc3g1bm5HZGd5Zmc0dXJXMlZtMTVEaEd2STdDL250cTBkWXkyNE4vVWJHN1VEWHZseUxJSkZxMVhQN25mCnBaRzBWQ2paNjlibXhLbTNaOG0wL0F3TXZpOGU5ZWR5OHY5a05CQ3dMR2tIYkE4WW85Q0lpUWdlbGZwcDF2VWgKYm5OQmhhRCtpdTZDZmlDTHdnSmIvaXc3ZW8vQ3lvWnF4K3RqWGFPMnpYdm00cC8rUUlmQU9ndEdRTEZVOGNmWgovZ1VyVHE1Z0ZxMCtQOUd5V3NBVEpGNnE3TDZXWlpqME91VHNlN2Y0Q1NpajZNbk9NTXhBK0pvYWhKejdsc1NpClRKSEl3RXA1ci9SeWhweWVwUXhGWWNVSDVKSmY5cmFoWExXWmkrOVRqeFNNMll5aHhmUlBzaVVFdUdEb2s3OFEKbS9RUGlDaTlKSmIxb2NtVGpBVjh4RFNob2NpdlhPRnlobjZMbjc3dkxqWStBYXZ0V0RoUXRocHVQeHNMdFZ6bQplMFNIMTFkRUxSdGI3NG1xWE9yTzdmdS8rSUJzM0pxTEUvVSt4dXhRdHZHOHZHMXlES0hIU1pxUzJoL1dzNGw0Ck5pQXNoSGdlaFFEUEJjWTl3WVl6ZkJnWnBPVU16ZERmNTB4K0ZTbFk0M1dPSkp6U3VRaDR5WjArM2t5Z3VDRjgKcm5NTFNjZXlTNGNpNExtSi9LQ1N1R2RmNlhWWXo4QkU5Z2pqanBDUDZxeTBVbFJlZldzL2lnL3djSysyYkYxVApuL1l2KzZnWGVDVEhKNzVxRElQbHA3RFJVVWswZmJNajRiSWthb2dXV2s0emYydThteFpMYTBsZVBLTktaTi9tCkdDdkZ3cjNlaSt1LzhjenA1RjdUCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K",
            },
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_set_up_image_cleaner(self):
        dec_0 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_0 = self.models.ManagedCluster(location="test_location")
        dec_0.context.attach_mc(mc_0)
        dec_mc_0 = dec_0.set_up_image_cleaner(mc_0)
        ground_truth_mc_0 = self.models.ManagedCluster(location="test_location")
        self.assertEqual(dec_mc_0, ground_truth_mc_0)

        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_image_cleaner": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.set_up_image_cleaner(mc_1)

        ground_truth_image_cleaner_profile_1 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=7*24,
        )
        ground_truth_security_profile_1 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_1,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_1,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "enable_image_cleaner": True,
                "image_cleaner_interval_hours": 24
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.set_up_image_cleaner(mc_2)

        ground_truth_image_cleaner_profile_2 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=24,
        )
        ground_truth_security_profile_2 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_2,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

class AKSManagedClusterUpdateDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)
        self.client = MockClient()

    def test_init(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        self.assertIsNotNone(dec_1.models)
        self.assertIsNotNone(dec_1.context)
        self.assertIsNotNone(dec_1.agentpool_decorator)
        self.assertIsNotNone(dec_1.agentpool_context)

    def test_check_raw_parameters(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on no updated parameter provided
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=False,
        ), self.assertRaises(RequiredArgumentMissingError):
            dec_1.check_raw_parameters()

        # unless user says they want to reconcile
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=True,
        ):
            dec_1.check_raw_parameters()

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "cluster_autoscaler_profile": {},
                "api_server_authorized_ip_ranges": "",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        dec_2.check_raw_parameters()

    def test_ensure_mc(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_mc(None)
        mc_1 = self.models.ManagedCluster(location="test_location")
        # fail on inconsistent mc with internal context
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_mc(mc_1)

    def test_fetch_mc(self):
        mock_mc = self.models.ManagedCluster(
            location="test_location",
        )
        self.client.get = Mock(return_value=mock_mc)
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "name": "test_cluster",
                "resource_group_name": "test_rg_name",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        dec_mc = dec_1.fetch_mc()
        ground_truth_mc = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc, ground_truth_mc)
        self.assertEqual(dec_mc, dec_1.context.mc)
        self.client.get.assert_called_once_with("test_rg_name", "test_cluster")

    def test_update_storage_profile(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"disable_disk_driver": True, "disable_file_driver": True, "enable_blob_driver": True, "disable_snapshot_controller": True, "yes": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        storage_profile_1 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(enabled=True),
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(enabled=True),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(enabled=False),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(enabled=False),
        )
        mc_1 = self.models.ManagedCluster(location="test_location", storage_profile=storage_profile_1)
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_storage_profile(mc_1)
        ground_truth_storage_profile_1 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(enabled=False),
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(enabled=False),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(enabled=False),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(enabled=True),
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location", storage_profile=ground_truth_storage_profile_1
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_disk_driver": True, "enable_file_driver": True, "enable_snapshot_controller": True, "disable_blob_driver": True, "yes": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        storage_profile_2 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(enabled=False),
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(enabled=False),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(enabled=True),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(enabled=False),
        )
        mc_2 = self.models.ManagedCluster(location="test_location", storage_profile=storage_profile_2)
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_storage_profile(mc_2)
        ground_truth_storage_profile_2 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=self.models.ManagedClusterStorageProfileDiskCSIDriver(enabled=True),
            file_csi_driver=self.models.ManagedClusterStorageProfileFileCSIDriver(enabled=True),
            blob_csi_driver=self.models.ManagedClusterStorageProfileBlobCSIDriver(enabled=False),
            snapshot_controller=self.models.ManagedClusterStorageProfileSnapshotController(enabled=True),
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location", storage_profile=ground_truth_storage_profile_2
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_update_upgrade_settings(self):
        # Should not update mc if unset
        dec_0 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,

        )
        mc_0 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings()
        )
        dec_0.context.attach_mc(mc_0)
        dec_mc_0 = dec_0.update_upgrade_settings(mc_0)
        ground_truth_mc_0 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings()
        )
        self.assertEqual(dec_mc_0, ground_truth_mc_0)

        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    force_upgrade=True,
                    until=parse("2023-04-01T13:00:00Z")
                )
            )
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_upgrade_settings(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    force_upgrade=True,
                    until=parse("2023-04-01T13:00:00Z")
                )
            )
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # force_upgrade false
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"disable_force_upgrade": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    force_upgrade=True,
                    until=parse("2099-04-01T13:00:00Z")
                )
            )
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_upgrade_settings(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    force_upgrade=False,
                    until=parse("2099-04-01T13:00:00Z")
                )
            )
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # force_upgrade true
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_force_upgrade": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_upgrade_settings(mc_3)
        self.assertEqual(dec_mc_3.upgrade_settings.override_settings.force_upgrade, True)
        self.assertGreater(dec_mc_3.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=2)).timestamp())
        self.assertLess(dec_mc_3.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=4)).timestamp())

        # Set Until
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"upgrade_override_until": "2023-04-01T13:00:00Z"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    until=parse("2023-01-01T13:00:00Z")
                )
            )
        )
        dec_4.context.attach_mc(mc_4)
        dec_mc_4 = dec_4.update_upgrade_settings(mc_4)
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    until=parse("2023-04-01T13:00:00Z")
                )
            )
        )
        self.assertEqual(dec_mc_4, ground_truth_mc_4)

        # Set both fields
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_force_upgrade": True,
             "upgrade_override_until": "2023-04-01T13:00:00Z"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    force_upgrade=True,
                    until=parse("2023-05-01T13:00:00Z")
                )
            )
        )
        dec_5.context.attach_mc(mc_5)
        dec_mc_5 = dec_5.update_upgrade_settings(mc_5)
        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    force_upgrade=True,
                    until=parse("2023-04-01T13:00:00Z")
                )
            )
        )
        self.assertEqual(dec_mc_5, ground_truth_mc_5)

        dec_6 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"upgrade_override_until": "abc"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
            upgrade_settings=self.models.ClusterUpgradeSettings(
                override_settings = self.models.UpgradeOverrideSettings(
                    until=parse("2023-05-01T13:00:00Z")
                )
            )
        )
        dec_6.context.attach_mc(mc_6)
        with self.assertRaises(InvalidArgumentValueError):
            dec_6.update_upgrade_settings(mc_6)

    def test_update_agentpool_profile(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "update_cluster_autoscaler": True,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": 3,
                "max_count": 10,
                "nodepool_labels": {"key1": "value1", "key2": "value2"},
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        agentpool_profile_1 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            count=3,
            enable_auto_scaling=True,
            min_count=1,
            max_count=5,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[agentpool_profile_1],
        )
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_agentpool_profile(None)
        dec_mc_1 = dec_1.update_agentpool_profile(mc_1)

        ground_truth_agentpool_profile_1 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            count=3,
            enable_auto_scaling=True,
            min_count=3,
            max_count=10,
            node_labels={"key1": "value1", "key2": "value2"},
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[ground_truth_agentpool_profile_1],
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "update_cluster_autoscaler": False,
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
                "nodepool_labels": {},
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        agentpool_profile_21 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            node_labels={"key1": "value1", "key2": "value2"},
        )
        agentpool_profile_22 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool2",
            node_labels={"key1": "value1", "key2": "value2"},
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[agentpool_profile_21, agentpool_profile_22],
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_agentpool_profile(mc_2)

        ground_truth_agentpool_profile_21 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
            node_labels={},
        )
        ground_truth_agentpool_profile_22 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool2",
            node_labels={},
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[ground_truth_agentpool_profile_21, ground_truth_agentpool_profile_22],
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(location="test_location")
        dec_3.context.attach_mc(mc_3)
        # fail on incomplete mc object (no agent pool profiles)
        with self.assertRaises(UnknownError):
            dec_3.update_agentpool_profile(mc_3)

    def test_update_auto_scaler_profile(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "cluster_autoscaler_profile": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile=self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
            ),
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_auto_scaler_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile=self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "cluster_autoscaler_profile": {},
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile=self.models.ManagedClusterPropertiesAutoScalerProfile(
                scan_interval="10s",
            ),
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_auto_scaler_profile(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_scaler_profile={},
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_update_tags(self):
        # default value in `aks_create`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "tags": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
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
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "tags": {},
            },
            ResourceType.MGMT_CONTAINERSERVICE,
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

    def test_process_attach_detach_acr(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "attach_acr": None,
                "detach_acr": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id", object_id="test_object_id"
                )
            },
        )
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate("subscription_id", "test_subscription_id")
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.process_attach_detach_acr(None)
        dec_1.process_attach_detach_acr(mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "attach_acr": "test_attach_acr",
                "detach_acr": "test_detach_acr",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id", object_id="test_object_id"
                )
            },
        )
        dec_2.context.attach_mc(mc_2)
        dec_2.context.set_intermediate("subscription_id", "test_subscription_id")
        with patch("azure.cli.command_modules.acs.managed_cluster_decorator.ensure_aks_acr") as ensure_acr:
            dec_2.process_attach_detach_acr(mc_2)
            ensure_acr.assert_has_calls(
                [
                    call(
                        self.cmd,
                        assignee="test_object_id",
                        acr_name_or_id="test_attach_acr",
                        subscription_id="test_subscription_id",
                        is_service_principal=False,
                    ),
                    call(
                        self.cmd,
                        assignee="test_object_id",
                        acr_name_or_id="test_detach_acr",
                        subscription_id="test_subscription_id",
                        detach=True,
                        is_service_principal=False,
                    ),
                ]
            )

    def test_update_sku(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "uptime_sla": False,
                "no_uptime_sla": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Free",
            ),
        )
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_sku(None)
        dec_mc_1 = dec_1.update_sku(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Free",
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "uptime_sla": True,
                "no_uptime_sla": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Free",
            ),
        )
        dec_2.context.attach_mc(mc_2)
        # fail on mutually exclusive uptime_sla and no_uptime_sla
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_2.update_sku(mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "uptime_sla": False,
                "no_uptime_sla": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Standard",
            ),
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_sku(mc_3)
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Free",
            ),
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # custom value
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "uptime_sla": True,
                "no_uptime_sla": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Free",
            ),
        )
        dec_4.context.attach_mc(mc_4)
        dec_mc_4 = dec_4.update_sku(mc_4)
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Standard",
            ),
        )
        self.assertEqual(dec_mc_4, ground_truth_mc_4)

    def test_update_load_balancer_profile(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": None,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": None,
                "load_balancer_outbound_ports": None,
                "load_balancer_idle_timeout": None,
            },
            resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_load_balancer_profile(None)

        load_balancer_profile_1 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile()
        network_profile_1 = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile_1,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=network_profile_1,
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_load_balancer_profile(mc_1)

        ground_truth_load_balancer_profile_1 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile()
        ground_truth_network_profile_1 = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=ground_truth_load_balancer_profile_1,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=ground_truth_network_profile_1,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        # fail on incomplete mc object (no network profile)
        with self.assertRaises(UnknownError):
            dec_2.update_load_balancer_profile(mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "load_balancer_sku": None,
                "load_balancer_managed_outbound_ip_count": None,
                "load_balancer_outbound_ips": None,
                "load_balancer_outbound_ip_prefixes": "test_ip_prefix_1,test_ip_prefix_2",
                "load_balancer_outbound_ports": 20,
                "load_balancer_idle_timeout": 30,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        load_balancer_profile_3 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            outbound_i_ps=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPs(
                public_i_ps=[
                    self.models.load_balancer_models.ResourceReference(id="test_ip_1"),
                    self.models.load_balancer_models.ResourceReference(id="test_ip_2"),
                ]
            ),
            allocated_outbound_ports=5,
        )
        network_profile_3 = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=load_balancer_profile_3,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            network_profile=network_profile_3,
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_load_balancer_profile(mc_3)

        ground_truth_load_balancer_profile_3 = self.models.load_balancer_models.ManagedClusterLoadBalancerProfile(
            outbound_ip_prefixes=self.models.load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
                public_ip_prefixes=[
                    self.models.load_balancer_models.ResourceReference(id="test_ip_prefix_1"),
                    self.models.load_balancer_models.ResourceReference(id="test_ip_prefix_2"),
                ]
            ),
            allocated_outbound_ports=20,
            idle_timeout_in_minutes=30,
        )
        ground_truth_network_profile_3 = self.models.ContainerServiceNetworkProfile(
            load_balancer_profile=ground_truth_load_balancer_profile_3,
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            network_profile=ground_truth_network_profile_3,
        )
        print(dec_mc_3.network_profile.load_balancer_profile)
        print(ground_truth_mc_3.network_profile.load_balancer_profile)
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_update_nat_gateway_profile(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "nat_gateway_managed_outbound_ip_count": None,
                "nat_gateway_idle_timeout": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_nat_gateway_profile(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                nat_gateway_profile=self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(),
                load_balancer_sku="standard",
                outbound_type="managedNATGateway",
            ),
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_nat_gateway_profile(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                nat_gateway_profile=self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(),
                load_balancer_sku="standard",
                outbound_type="managedNATGateway",
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "nat_gateway_managed_outbound_ip_count": 5,
                "nat_gateway_idle_timeout": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(location="test_location")
        dec_2.context.attach_mc(mc_2)
        # fail on incomplete mc object (no network profile)
        with self.assertRaises(UnknownError):
            dec_2.update_nat_gateway_profile(mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "nat_gateway_managed_outbound_ip_count": 5,
                "nat_gateway_idle_timeout": 30,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                nat_gateway_profile=self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(
                    managed_outbound_ip_profile=self.models.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(
                        count=10
                    ),
                    idle_timeout_in_minutes=20,
                ),
                load_balancer_sku="standard",
                outbound_type="managedNATGateway"
            ),
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_nat_gateway_profile(mc_3)

        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                nat_gateway_profile=self.models.nat_gateway_models.ManagedClusterNATGatewayProfile(
                    managed_outbound_ip_profile=self.models.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(
                        count=5
                    ),
                    idle_timeout_in_minutes=30,
                ),
                load_balancer_sku="standard",
                outbound_type="managedNATGateway"
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_update_outbound_type(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "outbound_type": "managedNATGateway",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_outbound_type_in_network_profile(None)
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                load_balancer_sku="standard",
                outbound_type="loadBalancer",
            ),
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_outbound_type_in_network_profile(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                load_balancer_sku="standard",
                outbound_type="managedNATGateway",
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "outbound_type": "managedNATGateway"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        with self.assertRaises(CLIInternalError):
            dec_1.update_outbound_type_in_network_profile(dec_2)

    def test_update_disable_local_accounts(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_local_accounts": False,
                "enable_local_accounts": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_disable_local_accounts(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=True,
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_disable_local_accounts(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=True,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_local_accounts": True,
                "enable_local_accounts": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_2 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=False,
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_disable_local_accounts(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=True,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_local_accounts": False,
                "enable_local_accounts": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_3 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=True,
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_disable_local_accounts(mc_3)
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            disable_local_accounts=False,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_update_api_server_access_profile(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": None,
                "disable_public_fqdn": False,
                "enable_public_fqdn": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_api_server_access_profile(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_api_server_access_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": "",
                "disable_public_fqdn": True,
                "enable_public_fqdn": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        api_server_access_profile_2 = self.models.ManagedClusterAPIServerAccessProfile(
            authorized_ip_ranges=["test_ip_1", "test_ip_2"],
            enable_private_cluster=True,
            enable_private_cluster_public_fqdn=True,
            private_dns_zone=CONST_PRIVATE_DNS_ZONE_SYSTEM,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_2,
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_api_server_access_profile(mc_2)
        ground_truth_api_server_access_profile_2 = self.models.ManagedClusterAPIServerAccessProfile(
            authorized_ip_ranges=[],
            enable_private_cluster=True,
            enable_private_cluster_public_fqdn=False,
            private_dns_zone=CONST_PRIVATE_DNS_ZONE_SYSTEM,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=ground_truth_api_server_access_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "api_server_authorized_ip_ranges": None,
                "disable_public_fqdn": False,
                "enable_public_fqdn": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        api_server_access_profile_3 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
            enable_private_cluster_public_fqdn=False,
            private_dns_zone=CONST_PRIVATE_DNS_ZONE_NONE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=api_server_access_profile_3,
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_api_server_access_profile(mc_3)
        ground_truth_api_server_access_profile_3 = self.models.ManagedClusterAPIServerAccessProfile(
            enable_private_cluster=True,
            enable_private_cluster_public_fqdn=True,
            private_dns_zone=CONST_PRIVATE_DNS_ZONE_NONE,
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            api_server_access_profile=ground_truth_api_server_access_profile_3,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

    def test_update_windows_profile(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_ahub": False,
                "disable_ahub": False,
                "windows_admin_password": None,
                "enable_windows_gmsa": False,
                "gmsa_dns_server": None,
                "gmsa_root_domain_name": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_windows_profile(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_windows_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_ahub": True,
                "disable_ahub": False,
                "windows_admin_password": "test_admin_password",
                "enable_windows_gmsa": True,
                "gmsa_dns_server": "test_gmsa_dns_server",
                "gmsa_root_domain_name": "test_gmsa_root_domain_name",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        gmsa_profile_2 = self.models.WindowsGmsaProfile(
            enabled=True,
            dns_server="test_mc_gmsa_dns_server",
            root_domain_name="test_mc_gmsa_root_domain_name",
        )
        windows_profile_2 = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin_name",
            admin_password="test_mc_win_admin_pd",
            gmsa_profile=gmsa_profile_2,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            windows_profile=windows_profile_2,
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_windows_profile(mc_2)

        ground_truth_gmsa_profile_2 = self.models.WindowsGmsaProfile(
            enabled=True,
            dns_server="test_gmsa_dns_server",
            root_domain_name="test_gmsa_root_domain_name",
        )
        ground_truth_windows_profile_2 = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin_name",
            admin_password="test_admin_password",
            license_type="Windows_Server",
            gmsa_profile=ground_truth_gmsa_profile_2,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            windows_profile=ground_truth_windows_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_ahub": False,
                "disable_ahub": True,
                "windows_admin_password": None,
                "enable_windows_gmsa": False,
                "gmsa_dns_server": None,
                "gmsa_root_domain_name": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        windows_profile_3 = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin_name",
            admin_password="test_mc_win_admin_pd",
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            windows_profile=windows_profile_3,
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_windows_profile(mc_3)

        ground_truth_windows_profile_3 = self.models.ManagedClusterWindowsProfile(
            # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="fake secrets in unit test")]
            admin_username="test_mc_win_admin_name",
            admin_password="test_mc_win_admin_pd",
            license_type="None",
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            windows_profile=ground_truth_windows_profile_3,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # custom value
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_ahub": True,
                "disable_ahub": False,
                "windows_admin_password": None,
                "enable_windows_gmsa": False,
                "gmsa_dns_server": None,
                "gmsa_root_domain_name": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_4.context.attach_mc(mc_4)
        # fail on incomplete mc object (no windows profile)
        with self.assertRaises(UnknownError):
            dec_4.update_windows_profile(mc_4)

        # custom value
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_ahub": False,
                "disable_ahub": False,
                "windows_admin_password": None,
                "enable_windows_gmsa": True,
                "gmsa_dns_server": None,
                "gmsa_root_domain_name": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_5.context.attach_mc(mc_5)
        # fail on incomplete mc object (no windows profile)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=True,
        ), self.assertRaises(UnknownError):
            dec_5.update_windows_profile(mc_5)

    def test_update_aad_profile(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_aad": False,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": None,
                "enable_azure_rbac": False,
                "disable_azure_rbac": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_aad_profile(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_aad_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_aad": True,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": None,
                "enable_azure_rbac": False,
                "disable_azure_rbac": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        aad_profile_2 = self.models.ManagedClusterAADProfile(
            managed=False,
        )
        mc_2 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_2)
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_aad_profile(mc_2)
        ground_truth_aad_profile_2 = self.models.ManagedClusterAADProfile(
            managed=True,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            aad_profile=ground_truth_aad_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_aad": False,
                "aad_tenant_id": "test_aad_tenant_id",
                "aad_admin_group_object_ids": "test_admin_1,test_admin_2",
                "enable_azure_rbac": True,
                "disable_azure_rbac": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        aad_profile_3 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=False,
        )
        mc_3 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_3)
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_aad_profile(mc_3)
        ground_truth_aad_profile_3 = self.models.ManagedClusterAADProfile(
            managed=True,
            enable_azure_rbac=True,
            tenant_id="test_aad_tenant_id",
            admin_group_object_i_ds=["test_admin_1", "test_admin_2"],
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            aad_profile=ground_truth_aad_profile_3,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # custom value
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_aad": False,
                "aad_tenant_id": None,
                "aad_admin_group_object_ids": None,
                "enable_azure_rbac": False,
                "disable_azure_rbac": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        aad_profile_4 = self.models.ManagedClusterAADProfile(
            managed=True,
            tenant_id="test_aad_tenant_id",
            admin_group_object_i_ds=["test_admin_1", "test_admin_2"],
            enable_azure_rbac=True,
        )
        mc_4 = self.models.ManagedCluster(location="test_location", aad_profile=aad_profile_4)
        dec_4.context.attach_mc(mc_4)
        dec_mc_4 = dec_4.update_aad_profile(mc_4)
        ground_truth_aad_profile_4 = self.models.ManagedClusterAADProfile(
            managed=True,
            tenant_id="test_aad_tenant_id",
            admin_group_object_i_ds=["test_admin_1", "test_admin_2"],
            enable_azure_rbac=False,
        )
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            aad_profile=ground_truth_aad_profile_4,
        )
        self.assertEqual(dec_mc_4, ground_truth_mc_4)

    def test_update_auto_upgrade_profile(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "auto_upgrade_channel": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_auto_upgrade_profile(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_auto_upgrade_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "auto_upgrade_channel": "stable",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mc_2 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_auto_upgrade_profile(mc_2)

        auto_upgrade_profile_2 = self.models.ManagedClusterAutoUpgradeProfile(upgrade_channel="stable")
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            auto_upgrade_profile=auto_upgrade_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_update_identity(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": False,
                "assign_identity": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_identity(None)

        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_identity(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": False,
                "assign_identity": "test_assign_identity",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_2.context.attach_mc(mc_2)
        # fail on enable_managed_identity not specified
        with self.assertRaises(RequiredArgumentMissingError):
            dec_2.update_identity(mc_2)

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "assign_identity": "test_assign_identity",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_3.context.attach_mc(mc_3)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=False,
        ):
            # fail on user does not confirm
            with self.assertRaises(DecoratorEarlyExitException):
                dec_3.update_identity(mc_3)

        # custom value
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "assign_identity": "test_assign_identity",
                "yes": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        identity_4 = self.models.ManagedClusterIdentity(type="SystemAssigned")
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_4,
        )
        dec_4.context.attach_mc(mc_4)
        dec_4.update_identity(mc_4)
        ground_truth_user_assigned_identity_4 = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        ground_truth_identity_4 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=ground_truth_user_assigned_identity_4,
        )
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            identity=ground_truth_identity_4,
        )
        self.assertEqual(mc_4, ground_truth_mc_4)

        # custom value
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "assign_identity": None,
                "yes": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        user_assigned_identity_5 = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity_5 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=user_assigned_identity_5,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_5,
        )
        dec_5.context.attach_mc(mc_5)
        dec_5.update_identity(mc_5)
        ground_truth_identity_5 = self.models.ManagedClusterIdentity(
            type="SystemAssigned",
        )
        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            identity=ground_truth_identity_5,
        )
        self.assertEqual(mc_5, ground_truth_mc_5)
        # custom value
        dec_6 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_managed_identity": True,
                "assign_identity": "test_assign_identity",
                "yes": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        user_assigned_identity_6 = {
            "original_test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        identity_6 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=user_assigned_identity_6,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
            identity=identity_6,
        )
        dec_6.context.attach_mc(mc_6)
        dec_6.update_identity(mc_6)
        ground_truth_user_assigned_identity_6 = {
            "test_assign_identity": self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
        }
        ground_truth_identity_6 = self.models.ManagedClusterIdentity(
            type="UserAssigned",
            user_assigned_identities=ground_truth_user_assigned_identity_6,
        )
        ground_truth_mc_6 = self.models.ManagedCluster(
            location="test_location",
            identity=ground_truth_identity_6,
        )
        self.assertEqual(mc_6, ground_truth_mc_6)

    def test_ensure_azure_keyvault_secrets_provider_addon_profile(self):
        # custom
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on addon azure-keyvault-secrets-provider not provided
        with self.assertRaises(InvalidArgumentValueError):
            dec_1.ensure_azure_keyvault_secrets_provider_addon_profile(None)

        # custom
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        azure_keyvault_secrets_provider_addon_profile_2 = (
            self.models.ManagedClusterAddonProfile(enabled=True)
        )
        dec_azure_keyvault_secrets_provider_addon_profile_2 = (
            dec_2.ensure_azure_keyvault_secrets_provider_addon_profile(
                azure_keyvault_secrets_provider_addon_profile_2
            )
        )
        ground_truth_azure_keyvault_secrets_provider_addon_profile_2 = (
            self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_SECRET_ROTATION_ENABLED: "false",
                    CONST_ROTATION_POLL_INTERVAL: "2m",
                },
            )
        )
        self.assertEqual(
            dec_azure_keyvault_secrets_provider_addon_profile_2,
            ground_truth_azure_keyvault_secrets_provider_addon_profile_2,
        )

    def test_update_azure_keyvault_secrets_provider_addon_profile(self):
        # default
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": False,
                "disable_secret_rotation": False,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        dec_1.update_azure_keyvault_secrets_provider_addon_profile(None)

        # custom value
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": True,
                "disable_secret_rotation": False,
                "rotation_poll_interval": "5m",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_keyvault_secrets_provider_addon_profile_2 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_SECRET_ROTATION_ENABLED: "false",
                CONST_ROTATION_POLL_INTERVAL: "2m",
            },
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: azure_keyvault_secrets_provider_addon_profile_2
            },
        )
        dec_2.context.attach_mc(mc_2)
        dec_2.update_azure_keyvault_secrets_provider_addon_profile(azure_keyvault_secrets_provider_addon_profile_2)
        ground_truth_azure_keyvault_secrets_provider_addon_profile_2 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_SECRET_ROTATION_ENABLED: "true",
                CONST_ROTATION_POLL_INTERVAL: "5m",
            },
        )
        self.assertEqual(
            azure_keyvault_secrets_provider_addon_profile_2,
            ground_truth_azure_keyvault_secrets_provider_addon_profile_2,
        )

        # custom value
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": False,
                "disable_secret_rotation": True,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_keyvault_secrets_provider_addon_profile_3 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_SECRET_ROTATION_ENABLED: "true",
                CONST_ROTATION_POLL_INTERVAL: "2m",
            },
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: azure_keyvault_secrets_provider_addon_profile_3
            },
        )
        dec_3.context.attach_mc(mc_3)
        dec_3.update_azure_keyvault_secrets_provider_addon_profile(azure_keyvault_secrets_provider_addon_profile_3)
        ground_truth_azure_keyvault_secrets_provider_addon_profile_3 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_SECRET_ROTATION_ENABLED: "false",
                CONST_ROTATION_POLL_INTERVAL: "2m",
            },
        )
        self.assertEqual(
            azure_keyvault_secrets_provider_addon_profile_3,
            ground_truth_azure_keyvault_secrets_provider_addon_profile_3,
        )

        # custom value
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": True,
                "disable_secret_rotation": False,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_keyvault_secrets_provider_addon_profile_4 = self.models.ManagedClusterAddonProfile(enabled=False)
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: azure_keyvault_secrets_provider_addon_profile_4
            },
        )
        dec_4.context.attach_mc(mc_4)
        # fail on addon azure-keyvault-secrets-provider not enabled
        with self.assertRaises(InvalidArgumentValueError):
            dec_4.update_azure_keyvault_secrets_provider_addon_profile(azure_keyvault_secrets_provider_addon_profile_4)

        # backfill nil config to default then update
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": True,
                "disable_secret_rotation": False,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        azure_keyvault_secrets_provider_addon_profile_5 = (
            self.models.ManagedClusterAddonProfile(enabled=True)
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: azure_keyvault_secrets_provider_addon_profile_5
            },
        )
        dec_5.context.attach_mc(mc_5)
        dec_azure_keyvault_secrets_provider_addon_profile_5 = (
            dec_5.update_azure_keyvault_secrets_provider_addon_profile(
                azure_keyvault_secrets_provider_addon_profile_5
            )
        )
        ground_truth_azure_keyvault_secrets_provider_addon_profile_5 = (
            self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_SECRET_ROTATION_ENABLED: "true",
                    CONST_ROTATION_POLL_INTERVAL: "2m",
                },
            )
        )
        self.assertEqual(
            dec_azure_keyvault_secrets_provider_addon_profile_5,
            ground_truth_azure_keyvault_secrets_provider_addon_profile_5,
        )

    def test_update_image_cleaner(self):
        dec_0 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_0 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_0.context.attach_mc(mc_0)
        dec_mc_0 = dec_0.update_image_cleaner(mc_0)
        ground_truth_mc_0 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_0, ground_truth_mc_0)

        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_image_cleaner": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_image_cleaner(mc_1)

        ground_truth_image_cleaner_profile_1 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=7*24,
        )
        ground_truth_security_profile_1 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_1,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_1,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "image_cleaner_interval_hours": 24
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=25,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_image_cleaner(mc_2)

        ground_truth_image_cleaner_profile_2 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=24,
        )
        ground_truth_security_profile_2 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_2,
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_2,
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_image_cleaner": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=False,
            interval_hours=25,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_image_cleaner(mc_3)

        ground_truth_image_cleaner_profile_3 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=25,
        )
        ground_truth_security_profile_3 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_3,
        )
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_3,
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_image_cleaner": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=25,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        dec_4.context.attach_mc(mc_4)
        dec_mc_4 = dec_4.update_image_cleaner(mc_4)

        ground_truth_image_cleaner_profile_4 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=False,
            interval_hours=25,
        )
        ground_truth_security_profile_4 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_4,
        )
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_4,
        )
        self.assertEqual(dec_mc_4, ground_truth_mc_4)

        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_image_cleaner": True,
                "image_cleaner_interval_hours": 24,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        security_profile = self.models.ManagedClusterSecurityProfile()
        security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=False,
            interval_hours=25,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            security_profile=security_profile,
        )
        dec_5.context.attach_mc(mc_5)
        dec_mc_5 = dec_5.update_image_cleaner(mc_5)

        ground_truth_image_cleaner_profile_5 = self.models.ManagedClusterSecurityProfileImageCleaner(
            enabled=True,
            interval_hours=24,
        )
        ground_truth_security_profile_5 = self.models.ManagedClusterSecurityProfile(
            image_cleaner=ground_truth_image_cleaner_profile_5,
        )
        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            security_profile=ground_truth_security_profile_5,
        )
        self.assertEqual(dec_mc_5, ground_truth_mc_5)

    def test_update_addon_profiles(self):
        # default value in `aks_update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": False,
                "disable_secret_rotation": False,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_addon_profiles(None)

        monitoring_addon_profile_1 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        ingress_appgw_addon_profile_1 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        virtual_node_addon_profile_1 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_MONITORING_ADDON_NAME: monitoring_addon_profile_1,
                CONST_INGRESS_APPGW_ADDON_NAME: ingress_appgw_addon_profile_1,
                CONST_VIRTUAL_NODE_ADDON_NAME
                + dec_1.context.get_virtual_node_addon_os_type(): virtual_node_addon_profile_1,
            },
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_addon_profiles(mc_1)

        ground_truth_monitoring_addon_profile_1 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        ground_truth_ingress_appgw_addon_profile_1 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        ground_truth_virtual_node_addon_profile_1 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_MONITORING_ADDON_NAME: ground_truth_monitoring_addon_profile_1,
                CONST_INGRESS_APPGW_ADDON_NAME: ground_truth_ingress_appgw_addon_profile_1,
                CONST_VIRTUAL_NODE_ADDON_NAME
                + dec_1.context.get_virtual_node_addon_os_type(): ground_truth_virtual_node_addon_profile_1,
            },
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)
        self.assertEqual(dec_1.context.get_intermediate("monitoring_addon_enabled"), True)
        self.assertEqual(dec_1.context.get_intermediate("ingress_appgw_addon_enabled"), True)
        self.assertEqual(dec_1.context.get_intermediate("virtual_node_addon_enabled"), True)

        # update addon azure_keyvault_secrets_provider with partial profile
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": True,
                "disable_secret_rotation": False,
                "rotation_poll_interval": "5m",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        azure_keyvault_secrets_provider_addon_profile_2 = (
            self.models.ManagedClusterAddonProfile(enabled=True)
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: azure_keyvault_secrets_provider_addon_profile_2
            },
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_addon_profiles(mc_2)

        ground_truth_azure_keyvault_secrets_provider_addon_profile_2 = (
            self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_SECRET_ROTATION_ENABLED: "true",
                    CONST_ROTATION_POLL_INTERVAL: "5m",
                },
            )
        )
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: ground_truth_azure_keyvault_secrets_provider_addon_profile_2,
            },
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # update addon azure_keyvault_secrets_provider with no profile
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_secret_rotation": True,
                "disable_secret_rotation": False,
                "rotation_poll_interval": None,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_3.context.attach_mc(mc_3)
        # fail on addon azure-keyvault-secrets-provider not enabled
        with self.assertRaises(InvalidArgumentValueError):
            dec_3.update_addon_profiles(mc_3)

    def test_update_defender(self):
        # enable
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_defender": True,
                "defender_config": get_test_data_file_path(
                    "defenderconfig.json"
                ),
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate(
            "subscription_id", "test_subscription_id"
        )

        dec_mc_1 = dec_1.update_defender(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            security_profile=self.models.ManagedClusterSecurityProfile(
                defender=self.models.ManagedClusterSecurityProfileDefender(
                    log_analytics_workspace_resource_id="test_workspace_resource_id",
                    security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                        enabled=True
                    ),
                )
            ),
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # disable
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"disable_defender": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            security_profile=self.models.ManagedClusterSecurityProfile(
                defender=self.models.ManagedClusterSecurityProfileDefender(
                    log_analytics_workspace_resource_id="test_workspace_resource_id",
                    security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                        enabled=True
                    ),
                )
            ),
        )
        dec_2.context.attach_mc(mc_2)
        dec_2.context.set_intermediate(
            "subscription_id", "test_subscription_id"
        )

        dec_mc_2 = dec_2.update_defender(mc_2)

        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            security_profile=self.models.ManagedClusterSecurityProfile(
                defender=self.models.ManagedClusterSecurityProfileDefender(
                    security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                        enabled=False
                    ),
                )
            ),
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

    def test_update_workload_identity_profile__default_value(self):
        dec = AKSManagedClusterUpdateDecorator(self.cmd, self.client, {}, ResourceType.MGMT_CONTAINERSERVICE)
        mc = self.models.ManagedCluster(location="test_location")
        dec.context.attach_mc(mc)
        updated_mc = dec.update_workload_identity_profile(mc)
        self.assertIsNone(updated_mc.security_profile)

    def test_update_workload_identity_profile__enabled(self):
        dec = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_workload_identity": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc = self.models.ManagedCluster(location="test_location")
        mc.oidc_issuer_profile = self.models.ManagedClusterOIDCIssuerProfile(enabled=True)
        dec.context.attach_mc(mc)
        updated_mc = dec.update_workload_identity_profile(mc)
        self.assertTrue(updated_mc.security_profile.workload_identity.enabled)

    def test_update_workload_identity_profile__disabled(self):
        dec = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_workload_identity": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc = self.models.ManagedCluster(location="test_location")
        mc.oidc_issuer_profile = self.models.ManagedClusterOIDCIssuerProfile(enabled=True)
        dec.context.attach_mc(mc)
        updated_mc = dec.update_workload_identity_profile(mc)
        self.assertFalse(updated_mc.security_profile.workload_identity.enabled)

    def test_update_identity_profile(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_identity_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        cluster_identity_obj = Mock(
            client_id="test_cluster_identity_client_id",
            principal_id="test_cluster_identity_object_id",
        )
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext.get_identity_by_msi_client",
            side_effect=[cluster_identity_obj],
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_cluster_identity_permission_on_kubelet_identity",
            return_value=None,
        ):
            dec_2 = AKSManagedClusterUpdateDecorator(
                self.cmd,
                self.client,
                {
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                    "yes": True,
                },
                ResourceType.MGMT_CONTAINERSERVICE,
            )
            cluster_identity = self.models.ManagedClusterIdentity(
                type="UserAssigned",
                user_assigned_identities={"test_assign_identity": {}},
            )
            mc_2 = self.models.ManagedCluster(location="test_location", identity=cluster_identity)
            dec_2.context.attach_mc(mc_2)
            dec_mc_2 = dec_2.update_identity_profile(mc_2)

            identity_profile_2 = {
                "kubeletidentity": self.models.UserAssignedIdentity(
                    resource_id="test_assign_kubelet_identity",
                )
            }
            ground_truth_mc_2 = self.models.ManagedCluster(
                location="test_location",
                identity=cluster_identity,
                identity_profile=identity_profile_2,
            )
            self.assertEqual(dec_mc_2, ground_truth_mc_2)

        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
            return_value=False,
        ), self.assertRaises(DecoratorEarlyExitException):
            dec_3 = AKSManagedClusterUpdateDecorator(
                self.cmd,
                self.client,
                {
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                },
                ResourceType.MGMT_CONTAINERSERVICE,
            )
            cluster_identity = self.models.ManagedClusterIdentity(
                type="UserAssigned",
                user_assigned_identities={"test_assign_identity": {}},
            )
            mc_3 = self.models.ManagedCluster(location="test_location", identity=cluster_identity)
            dec_3.context.attach_mc(mc_3)
            dec_3.update_identity_profile(mc_3)

        with self.assertRaises(RequiredArgumentMissingError):
            dec_4 = AKSManagedClusterUpdateDecorator(
                self.cmd,
                self.client,
                {
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                    "yes": True,
                },
                ResourceType.MGMT_CONTAINERSERVICE,
            )
            mc_4 = self.models.ManagedCluster(location="test_location")
            dec_4.context.attach_mc(mc_4)
            dec_4.update_identity_profile(mc_4)

        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterContext.get_identity_by_msi_client",
            side_effect=[cluster_identity_obj],
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_cluster_identity_permission_on_kubelet_identity",
            return_value=None,
        ):
            dec_5 = AKSManagedClusterUpdateDecorator(
                self.cmd,
                self.client,
                {
                    "enable_managed_identity": True,
                    "assign_identity": "test_assign_identity",
                    "assign_kubelet_identity": "test_assign_kubelet_identity",
                    "yes": True,
                },
                ResourceType.MGMT_CONTAINERSERVICE,
            )
            cluster_identity = self.models.ManagedClusterIdentity(
                type="UserAssigned",
                user_assigned_identities={"test_assign_identity": {}},
            )
            mc_5 = self.models.ManagedCluster(location="test_location", identity=cluster_identity)
            dec_5.context.attach_mc(mc_5)
            dec_mc_5 = dec_5.update_identity_profile(mc_5)

            identity_profile_5 = {
                "kubeletidentity": self.models.UserAssignedIdentity(
                    resource_id="test_assign_kubelet_identity",
                )
            }
            ground_truth_mc_5 = self.models.ManagedCluster(
                location="test_location",
                identity=cluster_identity,
                identity_profile=identity_profile_5,
            )
            self.assertEqual(dec_mc_5, ground_truth_mc_5)

    def test_update_network_plugin_settings(self):
        # default value in `aks_update`
        dec_1 =AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "pod_cidr": "100.64.0.0/10",
                "network_plugin_mode": "overlay",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                pod_cidr=None,
                service_cidr="192.168.0.0/16"
            ),
        )

        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_network_plugin_settings(None)
        dec_mc_1 = dec_1.update_network_plugin_settings(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/10",
                service_cidr="192.168.0.0/16",
            ),
        )

        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # test expanding pod cidr
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "pod_cidr": "100.64.0.0/10",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16"
            ),
        )

        dec_2.context.attach_mc(mc_2)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_2.update_network_plugin_settings(None)
        dec_mc_2 = dec_2.update_network_plugin_settings(mc_2)

        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/10",
                service_cidr="192.168.0.0/16",
            ),
        )

        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # test no updates made with same network plugin mode
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "network_plugin_mode": "overlay",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16"
            ),
        )

        dec_3.context.attach_mc(mc_3)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_3.update_network_plugin_settings(None)
        dec_mc_3 = dec_3.update_network_plugin_settings(mc_3)

        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16",
            ),
        )

        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # test update network dataplane
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "network_dataplane": "cilium",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                network_dataplane="cilium",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16"
            ),
        )

        dec_4.context.attach_mc(mc_4)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_4.update_network_plugin_settings(None)
        dec_mc_4 = dec_4.update_network_plugin_settings(mc_4)

        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                network_dataplane="cilium",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16",
            ),
        )

        self.assertEqual(dec_mc_4, ground_truth_mc_4)

        # test no updates made with empty network plugin settings
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16"
            ),
        )

        dec_5.context.attach_mc(mc_5)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_5.update_network_plugin_settings(None)
        dec_mc_5 = dec_5.update_network_plugin_settings(mc_5)

        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
                pod_cidr="100.64.0.0/16",
                service_cidr="192.168.0.0/16",
            ),
        )

        self.assertEqual(dec_mc_5, ground_truth_mc_5)

        # test update network policy
        dec_6 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "network_policy": "azure",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_policy="",
            ),
        )

        dec_6.context.attach_mc(mc_6)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_6.update_network_plugin_settings(None)
        dec_mc_6 = dec_6.update_network_plugin_settings(mc_6)

        ground_truth_mc_6 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_policy="azure",
            ),
        )

        self.assertEqual(dec_mc_6, ground_truth_mc_6)

        # test update network policy
        dec_7 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "network_plugin": "azure",
                "network_plugin_mode": "overlay"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_7 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="kubenet",
            ),
        )

        dec_7.context.attach_mc(mc_7)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_7.update_network_plugin_settings(None)
        dec_mc_7 = dec_7.update_network_plugin_settings(mc_7)

        ground_truth_mc_7 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_plugin_mode="overlay",
            ),
        )

        self.assertEqual(dec_mc_7, ground_truth_mc_7)

        # (Uninstall NPM) test update network policy ("azure" => "none")
        dec_8 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "network_policy": "none",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_8 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_policy="azure",
            ),
        )

        dec_8.context.attach_mc(mc_8)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_8.update_network_plugin_settings(None)
        dec_mc_8 = dec_8.update_network_plugin_settings(mc_8)

        ground_truth_mc_8 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_policy="none",
            ),
        )

        self.assertEqual(dec_mc_8, ground_truth_mc_8)

        # (Uninstall NPM) test update network policy ("calico" => "none")
        dec_9 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "network_policy": "none",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_9 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_policy="calico",
            ),
        )

        dec_9.context.attach_mc(mc_9)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_9.update_network_plugin_settings(None)
        dec_mc_9 = dec_9.update_network_plugin_settings(mc_9)

        ground_truth_mc_9 = self.models.ManagedCluster(
            location="test_location",
            network_profile=self.models.ContainerServiceNetworkProfile(
                network_plugin="azure",
                network_policy="none",
            ),
        )

        self.assertEqual(dec_mc_9, ground_truth_mc_9)


    def _mock_get_keyvault_client(cli_ctx, subscription_id=None):
        free_mock_client = mock.MagicMock()
        return free_mock_client

    @mock.patch('azure.cli.command_modules.acs._client_factory.get_keyvault_client', _mock_get_keyvault_client)
    def test_update_app_routing_profile(self):
        # enable app routing
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_app_routing": True, "enable_kv": False},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_app_routing_profile(mc_1)
        ground_truth_ingress_profile_1 = self.models.ManagedClusterIngressProfile(
            web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                enabled=True,
            )
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location", ingress_profile=ground_truth_ingress_profile_1
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        # enable app routing with key vault
        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_app_routing": True, "enable_kv": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_app_routing_profile(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                )
            ),
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                    enabled=True,
                    config={
                        CONST_SECRET_ROTATION_ENABLED: "false",
                        CONST_ROTATION_POLL_INTERVAL: "2m",
                    },
                )
            },
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        # disable app routing
        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_app_routing": False,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_app_routing_profile(mc_3)
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=False,
                )
            ),
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)
        # add dns zone resource ids
        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "dns_zone_resource_ids": "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com, /subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com",
                "add_dns_zone": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                )
            ),
        )
        dec_4.context.attach_mc(mc_4)
        dec_mc_4 = dec_4.update_app_routing_profile(mc_4)
        ground_truth_mc_4 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                    dns_zone_resource_ids=[
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com",
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com",
                    ],
                )
            ),
        )

        self.assertEqual(dec_mc_4, ground_truth_mc_4)

        # delete dns zone resource ids
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "dns_zone_resource_ids": "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com",
                "delete_dns_zone": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                    dns_zone_resource_ids=[
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com",
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com",
                    ],
                )
            ),
        )
        dec_5.context.attach_mc(mc_5)
        dec_mc_5 = dec_5.update_app_routing_profile(mc_5)
        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True, dns_zone_resource_ids=["/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com"]
                )
            ),
        )
        self.assertEqual(dec_mc_5, ground_truth_mc_5)

        # update dns zone resource ids
        dec_6 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "dns_zone_resource_ids": "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/privateDnsZones/testdnszone_3.com,/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/privateDnsZones/testdnszone_4.com",
                "update_dns_zone": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                    dns_zone_resource_ids=[
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com",
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com",
                    ],
                )
            ),
        )
        dec_6.context.attach_mc(mc_6)
        dec_mc_6 = dec_6.update_app_routing_profile(mc_6)

        ground_truth_mc_6 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                    dns_zone_resource_ids=[
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/privateDnsZones/testdnszone_3.com",
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/privateDnsZones/testdnszone_4.com",
                    ],
                )
            ),
        )
        self.assertEqual(dec_mc_6, ground_truth_mc_6)

        # list dns zone resource ids
        dec_7 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"list_dns_zones": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_7 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                    dns_zone_resource_ids=[
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com",
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com",
                    ],
                )
            ),
        )
        dec_7.context.attach_mc(mc_7)
        dec_mc_7 = dec_7.update_app_routing_profile(mc_7)
        ground_truth_mc_7 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                    dns_zone_resource_ids=[
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_1.com",
                        "/subscriptions/testsub/resourceGroups/testrg/providers/Microsoft.Network/dnsZones/testdnszone_2.com",
                    ],
                )
            ),
        )
        self.assertEqual(dec_mc_7, ground_truth_mc_7)

        # update app routing with key vault
        from azure.cli.core.mock import DummyCli
        from azure.cli.core.commands import AzCliCommand
        from azure.cli.core import AzCommandsLoader

        command_kwargs = {"operation_group": "vaults"}
        cli_ctx = DummyCli()
        self.cmd = AzCliCommand(AzCommandsLoader(cli_ctx), "mock-cmd", None, kwargs=command_kwargs)
        dec_8 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_kv": True, "keyvault_id": "/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_8 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                )
            ),
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                    enabled=False,
                )
            }
        )
        mc_8.ingress_profile.web_app_routing.identity = self.models.UserAssignedIdentity(
            resource_id="test_resource_id",
            client_id="test_client_id",
            object_id="test_object_id",
        )
        dec_8.context.attach_mc(mc_8)
        dec_mc_8 = dec_8.update_app_routing_profile(mc_8)
        ground_truth_mc_8 = self.models.ManagedCluster(
            location="test_location",
            ingress_profile=self.models.ManagedClusterIngressProfile(
                web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                    enabled=True,
                ),
            ),
            addon_profiles={
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME: self.models.ManagedClusterAddonProfile(
                    enabled=True,
                    config={
                        CONST_SECRET_ROTATION_ENABLED: "false",
                        CONST_ROTATION_POLL_INTERVAL: "2m",
                    },
                )
            },
        )
        ground_truth_mc_8.ingress_profile.web_app_routing.identity = self.models.UserAssignedIdentity(
            resource_id="test_resource_id",
            client_id="test_client_id",
            object_id="test_object_id",
        )

        self.assertEqual(dec_mc_8, ground_truth_mc_8)

    def test_enable_disable_cost_analysis(self):
        # Should not update mc if unset
        dec_0 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_0 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_0.context.attach_mc(mc_0)
        dec_mc_0 = dec_0.update_metrics_profile(mc_0)
        ground_truth_mc_0 = self.models.ManagedCluster(
            location="test_location",
        )
        self.assertEqual(dec_mc_0, ground_truth_mc_0)

        # Should error if both set
        dec_6 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"disable_cost_analysis": True, "enable_cost_analysis": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_6.context.attach_mc(mc_6)
        with self.assertRaises(MutuallyExclusiveArgumentError):
            dec_6.update_metrics_profile(mc_6)


    def test_update_mc_profile_default(self):
        import inspect

        from azure.cli.command_modules.acs.custom import aks_update

        optional_params = {}
        positional_params = []
        for _, v in inspect.signature(aks_update).parameters.items():
            if v.default != v.empty:
                optional_params[v.name] = v.default
            else:
                positional_params.append(v.name)
        ground_truth_positional_params = [
            "cmd",
            "client",
            "resource_group_name",
            "name",
        ]
        self.assertEqual(positional_params, ground_truth_positional_params)

        # prepare a dictionary of default parameters
        raw_param_dict = {
            "resource_group_name": "test_rg_name",
            "name": "test_name",
        }
        raw_param_dict.update(optional_params)

        # default value in `update`
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            raw_param_dict,
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        mock_existing_mc = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[
                self.models.ManagedClusterAgentPoolProfile(
                    name="nodepool1",
                )
            ],
            network_profile=self.models.ContainerServiceNetworkProfile(
                load_balancer_sku="standard",
            ),
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    resource_id="test_resource_id",
                    client_id="test_client_id",
                    object_id="test_object_id",
                )
            },
        )
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.get_rg_location",
            return_value="test_location",
        ), patch("azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile,), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterUpdateDecorator.check_raw_parameters",
            return_value=True,
        ), patch.object(
            self.client, "get", return_value=mock_existing_mc
        ):
            dec_mc_1 = dec_1.update_mc_profile_default()

        ground_truth_agent_pool_profile_1 = self.models.ManagedClusterAgentPoolProfile(
            name="nodepool1",
        )
        ground_truth_network_profile_1 = self.models.ContainerServiceNetworkProfile(
            load_balancer_sku="standard",
        )
        ground_truth_identity_1 = self.models.ManagedClusterIdentity(type="SystemAssigned")
        ground_truth_identity_profile_1 = {
            "kubeletidentity": self.models.UserAssignedIdentity(
                resource_id="test_resource_id",
                client_id="test_client_id",
                object_id="test_object_id",
            )
        }
        ground_truth_storage_profile_1 = self.models.ManagedClusterStorageProfile(
            disk_csi_driver=None,
            file_csi_driver=None,
            blob_csi_driver=None,
            snapshot_controller=None,
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            agent_pool_profiles=[ground_truth_agent_pool_profile_1],
            network_profile=ground_truth_network_profile_1,
            identity=ground_truth_identity_1,
            identity_profile=ground_truth_identity_profile_1,
            storage_profile=ground_truth_storage_profile_1,
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_1.context.raw_param.print_usage_statistics()

    def test_check_is_postprocessing_required(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), False)
        dec_1.context.set_intermediate("monitoring_addon_enabled", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_1.context.remove_intermediate("monitoring_addon_enabled")
        dec_1.context.set_intermediate("ingress_appgw_addon_enabled", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_1.context.remove_intermediate("ingress_appgw_addon_enabled")
        dec_1.context.set_intermediate("virtual_node_addon_enabled", True)
        self.assertEqual(dec_1.check_is_postprocessing_required(mc_1), True)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"attach_acr": "test_attach_acr"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location", identity=self.models.ManagedClusterIdentity(type="SystemAssigned")
        )
        dec_2.context.attach_mc(mc_2)
        self.assertEqual(dec_2.check_is_postprocessing_required(mc_2), True)

    def test_immediate_processing_after_request(self):
        pass

    def test_postprocessing_after_mc_created(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_msi_auth_for_monitoring": False},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_1.context.set_intermediate("monitoring_addon_enabled", True)
        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch("azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_monitoring_role_assignment"
        ) as mock_add:
            dec_1.postprocessing_after_mc_created(mc_1)
        mock_add.assert_called_once_with(mc_1, ANY, self.cmd)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "resource_group_name": "test_rg_name",
                "name": "test_name",
                "enable_msi_auth_for_monitoring": True,
                "enable_addons": "monitoring"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        monitoring_addon_profile_2 = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
            addon_profiles={
                CONST_MONITORING_ADDON_NAME: monitoring_addon_profile_2,
            },
        )
        dec_2.context.attach_mc(mc_2)
        dec_2.context.set_intermediate("monitoring_addon_enabled", True)
        mock_profile_2 = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile_2
        ), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.ensure_container_insights_for_monitoring"
        ) as mock_ensure:
            dec_2.postprocessing_after_mc_created(mc_2)
        mock_ensure.assert_called_once_with(
            self.cmd,
            monitoring_addon_profile_2,
            "1234-5678-9012",
            "test_rg_name",
            "test_name",
            "test_location",
            remove_monitoring=False,
            aad_route=True,
            create_dcr=False,
            create_dcra=True,
            enable_syslog=None,
            data_collection_settings=None,
            is_private_cluster=None,
            ampls_resource_id=None,
            enable_high_log_scale_mode=None,
        )

        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"vnet_subnet_id": "test_vnet_subnet_id", "attach_acr": "test_attach_acr"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location", identity=self.models.ManagedClusterIdentity(type="SystemAssigned")
        )
        dec_3.context.attach_mc(mc_3)
        dec_3.context.set_intermediate("ingress_appgw_addon_enabled", True)
        dec_3.context.set_intermediate("virtual_node_addon_enabled", True)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_ingress_appgw_addon_role_assignment"
        ) as mock_add_ingress_3, patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_virtual_node_role_assignment"
        ) as mock_add_virtual_3:
            dec_3.postprocessing_after_mc_created(mc_3)
        mock_add_ingress_3.assert_called_once_with(mc_3, self.cmd)
        mock_add_virtual_3.assert_called_once_with(self.cmd, mc_3, "test_vnet_subnet_id")

        dec_4 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"attach_acr": "test_attach_acr"},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_4 = self.models.ManagedCluster(
            location="test_location",
            identity=self.models.ManagedClusterIdentity(type="SystemAssigned"),
            identity_profile={
                "kubeletidentity": self.models.UserAssignedIdentity(
                    client_id="test_client_id", object_id="test_object_id"
                )
            },
        )
        dec_4.context.attach_mc(mc_4)
        mock_profile_4 = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile_4
        ), patch("azure.cli.command_modules.acs.managed_cluster_decorator.ensure_aks_acr") as mock_ensure_4:
            dec_4.postprocessing_after_mc_created(mc_4)
        mock_ensure_4.assert_called_once_with(
            self.cmd,
            assignee="test_object_id",
            acr_name_or_id="test_attach_acr",
            subscription_id="1234-5678-9012",
            is_service_principal=False,
        )

    def test_put_mc(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"enable_msi_auth_for_monitoring": False},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        with patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.sdk_no_wait",
            return_value=mc_1,
        ):
            self.assertEqual(dec_1.put_mc(mc_1), mc_1)

        dec_1.context.set_intermediate("monitoring_addon_enabled", True)
        mock_profile = Mock(get_subscription_id=Mock(return_value="1234-5678-9012"))
        with patch("azure.cli.command_modules.acs.managed_cluster_decorator.Profile", return_value=mock_profile), patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.add_monitoring_role_assignment"
        ) as mock_add, patch(
            "azure.cli.command_modules.acs.managed_cluster_decorator.LongRunningOperation",
            return_value=Mock(return_value=mc_1),
        ):
            self.assertEqual(dec_1.put_mc(mc_1), mc_1)
        mock_add.assert_called_once_with(mc_1, ANY, self.cmd)

    def test_update_mc(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        with patch("azure.cli.command_modules.acs.managed_cluster_decorator.AKSManagedClusterCreateDecorator.put_mc"):
            dec_1.update_mc(mc_1)

    def test_update_http_proxy_config(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {"http_proxy_config": get_test_data_file_path("httpproxyconfig.json")},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1.update_http_proxy_config(None)
        dec_mc_1 = dec_1.update_http_proxy_config(mc_1)

        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            http_proxy_config={
                "httpProxy": "http://cli-proxy-vm:3128/",
                "httpsProxy": "https://cli-proxy-vm:3129/",
                "noProxy": ["localhost", "127.0.0.1"],
                "trustedCa": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZHekNDQXdPZ0F3SUJBZ0lVT1FvajhDTFpkc2Vscjk3cnZJd3g1T0xEc3V3d0RRWUpLb1pJaHZjTkFRRUwKQlFBd0Z6RVZNQk1HQTFVRUF3d01ZMnhwTFhCeWIzaDVMWFp0TUI0WERUSXlNRE13T0RFMk5EUTBOMW9YRFRNeQpNRE13TlRFMk5EUTBOMW93RnpFVk1CTUdBMVVFQXd3TVkyeHBMWEJ5YjNoNUxYWnRNSUlDSWpBTkJna3Foa2lHCjl3MEJBUUVGQUFPQ0FnOEFNSUlDQ2dLQ0FnRUEvTVB0VjVCVFB0NmNxaTRSZE1sbXIzeUlzYTJ1anpjaHh2NGgKanNDMUR0blJnb3M1UzQxUEgwcmkrM3RUU1ZYMzJ5cndzWStyRDFZUnVwbTZsbUU3R2hVNUkwR2k5b3prU0YwWgpLS2FKaTJveXBVL0ZCK1FQcXpvQ1JzTUV3R0NibUtGVmw4VnVoeW5kWEs0YjRrYmxyOWJsL2V1d2Q3TThTYnZ6CldVam5lRHJRc2lJc3J6UFQ0S0FaTHFjdHpEZTRsbFBUN1lLYTMzaGlFUE9mdldpWitkcWthUUE5UDY0eFhTeW4KZkhYOHVWQUozdUJWSmVHeEQwcGtOSjdqT3J5YVV1SEh1Y1U4UzltSWpuS2pBQjVhUGpMSDV4QXM2bG1iMzEyMgp5KzF0bkVBbVhNNTBEK1VvRWpmUzZIT2I1cmRpcVhHdmMxS2JvS2p6a1BDUnh4MmE3MmN2ZWdVajZtZ0FKTHpnClRoRTFsbGNtVTRpemd4b0lNa1ZwR1RWT0xMbjFWRkt1TmhNWkN2RnZLZ25Lb0F2M0cwRlVuZldFYVJSalNObUQKTFlhTURUNUg5WnQycERJVWpVR1N0Q2w3Z1J6TUVuWXdKTzN5aURwZzQzbzVkUnlzVXlMOUpmRS9OaDdUZzYxOApuOGNKL1c3K1FZYllsanVyYXA4cjdRRlNyb2wzVkNoRkIrT29yNW5pK3ZvaFNBd0pmMFVsTXBHM3hXbXkxVUk0ClRGS2ZGR1JSVHpyUCs3Yk53WDVoSXZJeTVWdGd5YU9xSndUeGhpL0pkeHRPcjJ0QTVyQ1c3K0N0Z1N2emtxTkUKWHlyN3ZrWWdwNlk1TFpneTR0VWpLMEswT1VnVmRqQk9oRHBFenkvRkY4dzFGRVZnSjBxWS9yV2NMa0JIRFQ4Ugp2SmtoaW84Q0F3RUFBYU5mTUYwd0Z3WURWUjBSQkJBd0RvSU1ZMnhwTFhCeWIzaDVMWFp0TUJJR0ExVWRFd0VCCi93UUlNQVlCQWY4Q0FRQXdEd1lEVlIwUEFRSC9CQVVEQXdmbmdEQWRCZ05WSFNVRUZqQVVCZ2dyQmdFRkJRY0QKQWdZSUt3WUJCUVVIQXdFd0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dJQkFBb21qQ3lYdmFRT3hnWUs1MHNYTEIyKwp3QWZkc3g1bm5HZGd5Zmc0dXJXMlZtMTVEaEd2STdDL250cTBkWXkyNE4vVWJHN1VEWHZseUxJSkZxMVhQN25mCnBaRzBWQ2paNjlibXhLbTNaOG0wL0F3TXZpOGU5ZWR5OHY5a05CQ3dMR2tIYkE4WW85Q0lpUWdlbGZwcDF2VWgKYm5OQmhhRCtpdTZDZmlDTHdnSmIvaXc3ZW8vQ3lvWnF4K3RqWGFPMnpYdm00cC8rUUlmQU9ndEdRTEZVOGNmWgovZ1VyVHE1Z0ZxMCtQOUd5V3NBVEpGNnE3TDZXWlpqME91VHNlN2Y0Q1NpajZNbk9NTXhBK0pvYWhKejdsc1NpClRKSEl3RXA1ci9SeWhweWVwUXhGWWNVSDVKSmY5cmFoWExXWmkrOVRqeFNNMll5aHhmUlBzaVVFdUdEb2s3OFEKbS9RUGlDaTlKSmIxb2NtVGpBVjh4RFNob2NpdlhPRnlobjZMbjc3dkxqWStBYXZ0V0RoUXRocHVQeHNMdFZ6bQplMFNIMTFkRUxSdGI3NG1xWE9yTzdmdS8rSUJzM0pxTEUvVSt4dXhRdHZHOHZHMXlES0hIU1pxUzJoL1dzNGw0Ck5pQXNoSGdlaFFEUEJjWTl3WVl6ZkJnWnBPVU16ZERmNTB4K0ZTbFk0M1dPSkp6U3VRaDR5WjArM2t5Z3VDRjgKcm5NTFNjZXlTNGNpNExtSi9LQ1N1R2RmNlhWWXo4QkU5Z2pqanBDUDZxeTBVbFJlZldzL2lnL3djSysyYkYxVApuL1l2KzZnWGVDVEhKNzVxRElQbHA3RFJVVWswZmJNajRiSWthb2dXV2s0emYydThteFpMYTBsZVBLTktaTi9tCkdDdkZ3cjNlaSt1LzhjenA1RjdUCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K",
            },
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_update_service_mesh_profile(self):
        dec_1 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_azure_service_mesh": True,
                "revision": "asm-1-18"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.update_azure_service_mesh_profile(mc_1)
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-18"]
                )
            )
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

        dec_2 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_azure_service_mesh": True,
                "enable_ingress_gateway": True,
                "ingress_gateway_type": "Internal",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_2 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_2.context.attach_mc(mc_2)
        dec_mc_2 = dec_2.update_azure_service_mesh_profile(mc_2)
        ground_truth_mc_2 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    components=self.models.IstioComponents(
                        ingress_gateways=[
                            self.models.IstioIngressGateway(
                                mode="Internal",
                                enabled=True,
                            )
                        ]
                    )
                )
            )
        )
        self.assertEqual(dec_mc_2, ground_truth_mc_2)

        dec_3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_azure_service_mesh": True,
                "key_vault_id": "/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo",
                "ca_cert_object_name": "my-ca-cert",
                "ca_key_object_name": "my-ca-key",
                "root_cert_object_name": "my-root-cert",
                "cert_chain_object_name": "my-cert-chain",
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_3 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_3.context.attach_mc(mc_3)
        dec_mc_3 = dec_3.update_azure_service_mesh_profile(mc_3)
        ground_truth_mc_3 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    certificate_authority=self.models.IstioCertificateAuthority(
                        plugin=self.models.IstioPluginCertificateAuthority(
                            key_vault_id='/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo',
                            cert_object_name='my-ca-cert',
                            key_object_name='my-ca-key',
                            root_cert_object_name='my-root-cert',
                            cert_chain_object_name='my-cert-chain',
                        )
                    )
                )
            )
        )
        self.assertEqual(dec_mc_3, ground_truth_mc_3)

        # aks mesh upgrade start
        dec_5 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "mesh_upgrade_command": CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START,
                "revision": "asm-1-18"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_5 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17"]
                )
            )
        )
        dec_5.context.attach_mc(mc_5)
        dec_mc_5 = dec_5.update_azure_service_mesh_profile(mc_5)
        ground_truth_mc_5 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17", "asm-1-18"]
                )
            )
        )
        self.assertEqual(dec_mc_5, ground_truth_mc_5)

        # aks mesh upgrade complete
        dec_6 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "mesh_upgrade_command": CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_6 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17", "asm-1-18"]
                )
            )
        )
        dec_6.context.attach_mc(mc_6)
        with patch(
                "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
                return_value=True,
        ):
            dec_mc_6 = dec_6.update_azure_service_mesh_profile(mc_6)
        ground_truth_mc_6 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-18"]
                )
            )
        )
        self.assertEqual(dec_mc_6, ground_truth_mc_6)

        # aks mesh upgrade rollback
        dec_7 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "mesh_upgrade_command": CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_7 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17", "asm-1-18"]
                )
            )
        )
        dec_7.context.attach_mc(mc_7)
        with patch(
                "azure.cli.command_modules.acs.managed_cluster_decorator.prompt_y_n",
                return_value=True,
        ):
            dec_mc_7 = dec_7.update_azure_service_mesh_profile(mc_7)
        ground_truth_mc_7 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17"]
                )
            )
        )
        self.assertEqual(dec_mc_7, ground_truth_mc_7)

        # az aks mesh upgrade rollback - when upgrade is not in progress
        dec_8 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "mesh_upgrade_command": CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_8 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17"]
                )
            )
        )
        dec_8.context.attach_mc(mc_8)
        with self.assertRaises(ArgumentUsageError):
            dec_8.update_azure_service_mesh_profile(mc_8)

        # az aks mesh upgrade complete - when upgrade is not in progress
        dec_9 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "mesh_upgrade_command": CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_9 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17"]
                )
            )
        )
        dec_9.context.attach_mc(mc_9)
        with self.assertRaises(ArgumentUsageError):
            dec_9.update_azure_service_mesh_profile(mc_9)

        # az aks mesh enable - when azure service mesh has already been enabled
        dec_10 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_azure_service_mesh": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_10 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Istio",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17"]
                )
            )
        )
        dec_10.context.attach_mc(mc_10)
        with self.assertRaises(ArgumentUsageError):
            dec_10.update_azure_service_mesh_profile(mc_10)

        # az aks mesh disable - when azure service mesh has already been disabled
        dec_10 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_azure_service_mesh": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_10 = self.models.ManagedCluster(
            location="test_location",
            service_mesh_profile=self.models.ServiceMeshProfile(
                mode="Disabled",
                istio=self.models.IstioServiceMesh(
                    revisions=["asm-1-17"]
                )
            )
        )
        dec_10.context.attach_mc(mc_10)
        with self.assertRaises(ArgumentUsageError):
            dec_10.update_azure_service_mesh_profile(mc_10)

        # az aks mesh disable - when azure service mesh was never enabled
        dec_11 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "disable_azure_service_mesh": True,
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_11 = self.models.ManagedCluster(
            location="test_location",
        )
        dec_11.context.attach_mc(mc_11)
        with self.assertRaises(ArgumentUsageError):
            dec_11.update_azure_service_mesh_profile(mc_11)

    def test_set_up_app_routing_profile(self):
        dec_1 = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {"enable_app_routing": True},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        mc_1 = self.models.ManagedCluster(location="test_location")
        dec_1.context.attach_mc(mc_1)
        dec_mc_1 = dec_1.set_up_ingress_web_app_routing(mc_1)
        ground_truth_ingress_profile_1 = self.models.ManagedClusterIngressProfile(
            web_app_routing=self.models.ManagedClusterIngressProfileWebAppRouting(
                enabled=True,
            )
        )
        ground_truth_mc_1 = self.models.ManagedCluster(
            location="test_location", ingress_profile=ground_truth_ingress_profile_1
        )
        self.assertEqual(dec_mc_1, ground_truth_mc_1)

    def test_setup_supportPlan(self):
        # default value in `aks_create`
        ltsDecorator = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "k8s_support_plan": "AKSLongTermSupport"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        premiumSKU = self.models.ManagedClusterSKU(
                name="Base",
                tier="Premium")
        premiumCluster = self.models.ManagedCluster(
            location="test_location",
            support_plan=None,
            sku=premiumSKU,
        )
        ltsDecorator.context.attach_mc(premiumCluster)

        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            ltsDecorator.set_up_k8s_support_plan(None)

        ltsClusterCalculated = ltsDecorator.set_up_k8s_support_plan(premiumCluster)
        expectedLTSCluster = self.models.ManagedCluster(
            location="test_location",
            support_plan="AKSLongTermSupport",
            sku=premiumSKU,
        )
        self.assertEqual(ltsClusterCalculated, expectedLTSCluster)

        nonLTSDecorator = AKSManagedClusterCreateDecorator(
            self.cmd,
            self.client,
            {
                "k8s_support_plan": "KubernetesOfficial"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        nonLTSDecorator.context.attach_mc(premiumCluster)
        nonLTSClusterCalculated = nonLTSDecorator.set_up_k8s_support_plan(premiumCluster)
        expectedNonLTSCluster = self.models.ManagedCluster(
            location="test_location",
            support_plan="KubernetesOfficial",
            sku=premiumSKU,
        )
        self.assertEqual(nonLTSClusterCalculated, expectedNonLTSCluster)

    def test_update_supportPlan(self):
        # default value in `aks_create`
        noopDecorator = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )

        premiumSKU = self.models.ManagedClusterSKU(
                name="Base",
                tier="Premium")
        ltsCluster = self.models.ManagedCluster(
            location="test_location",
            sku=premiumSKU,
            support_plan="AKSLongTermSupport",
        )
        noopDecorator.context.attach_mc(ltsCluster)

        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            noopDecorator.update_k8s_support_plan(None)

        ltsClusterCalculated = noopDecorator.update_k8s_support_plan(ltsCluster)
        self.assertEqual(ltsClusterCalculated, ltsCluster)

        disableLTSDecorator = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {
                "k8s_support_plan": "KubernetesOfficial"
            },
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        disableLTSDecorator.context.attach_mc(ltsCluster)
        nonLTSClusterCalculated = disableLTSDecorator.update_k8s_support_plan(ltsCluster)
        expectedNonLTSCluster = self.models.ManagedCluster(
            location="test_location",
            support_plan="KubernetesOfficial",
            sku=premiumSKU,
        )
        self.assertEqual(nonLTSClusterCalculated, expectedNonLTSCluster)

        normalCluster = self.models.ManagedCluster(
            location="test_location",
            sku=self.models.ManagedClusterSKU(
                name="Base",
                tier="Standard"),
            support_plan="KubernetesOfficial",
        )
        noopDecorator3 = AKSManagedClusterUpdateDecorator(
            self.cmd,
            self.client,
            {},
            ResourceType.MGMT_CONTAINERSERVICE,
        )
        noopDecorator3.context.attach_mc(normalCluster)
        normalClusterCalculated = noopDecorator3.update_k8s_support_plan(normalCluster)
        self.assertEqual(normalClusterCalculated, normalCluster)


if __name__ == "__main__":
    unittest.main()
