# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.command_modules.acs import _natgateway as natgateway
from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterModels
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.profiles import ResourceType


class TestCreateNatGatewayProfile(unittest.TestCase):
    def setUp(self):
        # manually register CUSTOM_MGMT_AKS_PREVIEW
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        # store all the models used by nat gateway
        self.nat_gateway_models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE).nat_gateway_models

    def test_empty_arguments(self):
        profile = natgateway.create_nat_gateway_profile(None, None, models=self.nat_gateway_models)
        self.assertIsNone(profile)

    def test_nonempty_arguments(self):
        managed_outbound_ip_count = 2
        idle_timeout = 30

        profile = natgateway.create_nat_gateway_profile(managed_outbound_ip_count, idle_timeout, models=self.nat_gateway_models)

        self.assertEqual(profile.managed_outbound_ip_profile.count, managed_outbound_ip_count)
        self.assertEqual(profile.idle_timeout_in_minutes, idle_timeout)


class TestUpdateNatGatewayProfile(unittest.TestCase):
    def setUp(self):
        # manually register CUSTOM_MGMT_AKS_PREVIEW
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        # store all the models used by nat gateway
        self.nat_gateway_models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE).nat_gateway_models

    def test_empty_arguments(self):
        origin_profile = self.nat_gateway_models.ManagedClusterNATGatewayProfile(
            managed_outbound_ip_profile=self.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(
                count=1
            ),
            idle_timeout_in_minutes=4
        )

        profile = natgateway.update_nat_gateway_profile(None, None, origin_profile, models=self.nat_gateway_models)

        self.assertEqual(profile.managed_outbound_ip_profile.count, origin_profile.managed_outbound_ip_profile.count)
        self.assertEqual(profile.idle_timeout_in_minutes, origin_profile.idle_timeout_in_minutes)

    def test_nonempty_arguments(self):
        origin_profile = self.nat_gateway_models.ManagedClusterNATGatewayProfile(
            managed_outbound_ip_profile=self.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(
                count=1
            ),
            idle_timeout_in_minutes=4
        )
        new_managed_outbound_ip_count = 2
        new_idle_timeout = 30

        profile = natgateway.update_nat_gateway_profile(new_managed_outbound_ip_count, new_idle_timeout, origin_profile, models=self.nat_gateway_models)

        self.assertEqual(profile.managed_outbound_ip_profile.count, new_managed_outbound_ip_count)
        self.assertEqual(profile.idle_timeout_in_minutes, new_idle_timeout)


class TestIsNatGatewayProfileProvided(unittest.TestCase):
    def test_empty_arguments(self):
        result = natgateway.is_nat_gateway_profile_provided(None, None)
        self.assertFalse(result)

    def test_nonempty_managed_outbound_ip_count(self):
        result = natgateway.is_nat_gateway_profile_provided(1, None)
        self.assertTrue(result)

    def test_nonempty_idle_timeout(self):
        result = natgateway.is_nat_gateway_profile_provided(None, 4)
        self.assertTrue(result)

    def test_nonempty_arguments(self):
        result = natgateway.is_nat_gateway_profile_provided(1, 4)
        self.assertTrue(result)

    def test_nonempty_arguments(self):
        result = natgateway.is_nat_gateway_profile_provided(0, None)
        self.assertTrue(result)


class TestNatGatewayV2(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.nat_gateway_models = AKSManagedClusterModels(
            self.cmd, ResourceType.MGMT_CONTAINERSERVICE
        ).nat_gateway_models

    def test_is_provided_by_sku_and_v2_params(self):
        self.assertTrue(natgateway.is_nat_gateway_profile_provided(None, None, nat_gateway_sku="StandardV2"))
        self.assertTrue(natgateway.is_nat_gateway_profile_provided(None, None, managed_outbound_ipv6_count=1))
        self.assertTrue(natgateway.is_nat_gateway_profile_provided(None, None, outbound_ip_ids="/sub/ip1"))
        self.assertTrue(natgateway.is_nat_gateway_profile_provided(None, None, outbound_ip_prefix_ids="/sub/pfx1"))
        self.assertFalse(natgateway.is_nat_gateway_profile_provided(None, None))

    def test_create_with_sku_and_v2_params(self):
        profile = natgateway.create_nat_gateway_profile(
            2, 10, models=self.nat_gateway_models,
            managed_outbound_ipv6_count=1,
            outbound_ip_ids="/sub/ip1, /sub/ip2",
            outbound_ip_prefix_ids="/sub/pfx1",
            nat_gateway_sku="StandardV2",
        )
        self.assertEqual(profile.sku, "StandardV2")
        self.assertEqual(profile.managed_outbound_ip_profile.count, 2)
        self.assertEqual(profile.managed_outbound_ip_profile.count_ipv6, 1)
        self.assertEqual(profile.outbound_i_ps.public_i_ps, ["/sub/ip1", "/sub/ip2"])
        self.assertEqual(profile.outbound_ip_prefixes.public_ip_prefixes, ["/sub/pfx1"])
        self.assertEqual(profile.idle_timeout_in_minutes, 10)

    def test_create_sku_only(self):
        profile = natgateway.create_nat_gateway_profile(
            None, None, models=self.nat_gateway_models, nat_gateway_sku="StandardV2"
        )
        self.assertIsNotNone(profile)
        self.assertEqual(profile.sku, "StandardV2")

    def test_update_sets_sku_on_existing_profile(self):
        origin = self.nat_gateway_models.ManagedClusterNATGatewayProfile(
            managed_outbound_ip_profile=self.nat_gateway_models.ManagedClusterManagedOutboundIPProfile(count=1),
            idle_timeout_in_minutes=4,
        )
        profile = natgateway.update_nat_gateway_profile(
            None, None, origin, models=self.nat_gateway_models, nat_gateway_sku="StandardV2"
        )
        self.assertEqual(profile.sku, "StandardV2")
        self.assertEqual(profile.managed_outbound_ip_profile.count, 1)


if __name__ == "__main__":
    unittest.main()
