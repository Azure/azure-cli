# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.command_modules.acs import _loadbalancer as loadbalancer


class TestLoadBalancer(unittest.TestCase):

    def test_configure_load_balancer_profile(self):
        cmd = mock.MagicMock()
        managed_outbound_ip_count = 5
        outbound_ips = None
        outbound_ip_prefixes = None
        outbound_ports = 80
        idle_timeout = 3600

        from azure.cli.command_modules.acs.decorator import AKSCreateModels
        # store all the models used by load balancer
        lb_models = AKSCreateModels(cmd).lb_models
        ManagedClusterLoadBalancerProfile = lb_models.get(
            "ManagedClusterLoadBalancerProfile"
        )
        ManagedClusterLoadBalancerProfileManagedOutboundIPs = lb_models.get(
            "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
        )
        ManagedClusterLoadBalancerProfileOutboundIPs = lb_models.get(
            "ManagedClusterLoadBalancerProfileOutboundIPs"
        )
        ManagedClusterLoadBalancerProfileOutboundIPPrefixes = lb_models.get(
            "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
        )

        profile = ManagedClusterLoadBalancerProfile()
        profile.managed_outbound_ips = ManagedClusterLoadBalancerProfileManagedOutboundIPs(
            count=2
        )
        profile.outbound_ips = ManagedClusterLoadBalancerProfileOutboundIPs(
            public_ips="public_ips"
        )
        profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
            public_ip_prefixes="public_ip_prefixes"
        )

        p = loadbalancer.configure_load_balancer_profile(
            cmd,
            managed_outbound_ip_count,
            outbound_ips,
            outbound_ip_prefixes,
            outbound_ports,
            idle_timeout,
            profile,
            lb_models,
        )

        self.assertIsNotNone(p.managed_outbound_i_ps)
        self.assertIsNone(p.outbound_i_ps)
        self.assertIsNone(p.outbound_ip_prefixes)


if __name__ == '__main__':
    unittest.main()
