# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.command_modules.acs import _loadbalancer as loadbalancer
from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterModels
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.profiles import ResourceType


class TestLoadBalancer(unittest.TestCase):

    def test_configure_load_balancer_profile(self):
        cmd = MockCmd(MockCLI())
        managed_outbound_ip_count = 5
        outbound_ips = None
        outbound_ip_prefixes = None
        outbound_ports = 80
        idle_timeout = 3600

        # store all the models used by load balancer
        load_balancer_models = AKSManagedClusterModels(cmd, ResourceType.MGMT_CONTAINERSERVICE).load_balancer_models
        ManagedClusterLoadBalancerProfile = (
            load_balancer_models.ManagedClusterLoadBalancerProfile
        )
        ManagedClusterLoadBalancerProfileManagedOutboundIPs = (
            load_balancer_models.ManagedClusterLoadBalancerProfileManagedOutboundIPs
        )
        ManagedClusterLoadBalancerProfileOutboundIPs = (
            load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPs
        )
        ManagedClusterLoadBalancerProfileOutboundIPPrefixes = (
            load_balancer_models.ManagedClusterLoadBalancerProfileOutboundIPPrefixes
        )

        profile = ManagedClusterLoadBalancerProfile()
        profile.managed_outbound_i_ps = ManagedClusterLoadBalancerProfileManagedOutboundIPs(
            count=2
        )
        profile.outbound_i_ps = ManagedClusterLoadBalancerProfileOutboundIPs(
            public_i_ps="public_i_ps"
        )
        profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
            public_ip_prefixes="public_ip_prefixes"
        )

        p = loadbalancer.configure_load_balancer_profile(
            managed_outbound_ip_count,
            outbound_ips,
            outbound_ip_prefixes,
            outbound_ports,
            idle_timeout,
            profile,
            load_balancer_models,
        )

        self.assertEqual(p.managed_outbound_i_ps.count, 5)
        self.assertEqual(p.outbound_i_ps, None)
        self.assertEqual(p.outbound_ip_prefixes, None)
        self.assertEqual(p.allocated_outbound_ports, 80)
        self.assertEqual(p.idle_timeout_in_minutes, 3600)


if __name__ == '__main__':
    unittest.main()
