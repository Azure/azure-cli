# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.command_modules.acs import _loadbalancer as loadbalancer
from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterModels
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
)

class TestLoadBalancer(unittest.TestCase):

    def test_configure_load_balancer_profile(self):
        cmd = MockCmd(MockCLI())
        managed_outbound_ip_count = 5
        managed_outbound_ipv6_count = 4
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
            count=2,
            count_ipv6=3
        )
        profile.outbound_i_ps = ManagedClusterLoadBalancerProfileOutboundIPs(
            public_i_ps="public_i_ps"
        )
        profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
            public_ip_prefixes="public_ip_prefixes"
        )

        p = loadbalancer.configure_load_balancer_profile(
            managed_outbound_ip_count,
            managed_outbound_ipv6_count,
            outbound_ips,
            outbound_ip_prefixes,
            outbound_ports,
            idle_timeout,
            profile,
            load_balancer_models,
        )

        self.assertEqual(p.managed_outbound_i_ps.count, 5)
        self.assertEqual(p.managed_outbound_i_ps.count_ipv6, 4)
        self.assertEqual(p.outbound_i_ps, None)
        self.assertEqual(p.outbound_ip_prefixes, None)
        self.assertEqual(p.allocated_outbound_ports, 80)
        self.assertEqual(p.idle_timeout_in_minutes, 3600)

    def test_update_load_balancer_profile(self):
        cmd = MockCmd(MockCLI())
        managed_outbound_ip_count = None
        managed_outbound_ipv6_count = None
        outbound_ips = "ip1"
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
        profile = ManagedClusterLoadBalancerProfile()
        profile.managed_outbound_i_ps = ManagedClusterLoadBalancerProfileManagedOutboundIPs(
            count=2,
            count_ipv6=3
        )

        p = loadbalancer.configure_load_balancer_profile(
            managed_outbound_ip_count,
            managed_outbound_ipv6_count,
            outbound_ips,
            outbound_ip_prefixes,
            outbound_ports,
            idle_timeout,
            profile,
            load_balancer_models,
        )

        self.assertEqual(p.managed_outbound_i_ps, None)
        self.assertEqual(p.outbound_i_ps.public_i_ps,  [load_balancer_models.ResourceReference(id=x.strip()) for x in ['ip1']])
        self.assertEqual(p.allocated_outbound_ports, 80)
        self.assertEqual(p.idle_timeout_in_minutes, 3600)

    def test_configure_load_balancer_profile_error(self):
        cmd = MockCmd(MockCLI())
        managed_outbound_ip_count = 5
        managed_outbound_ipv6_count = 3
        outbound_ips = "testpip1,testpip2"
        outbound_ip_prefixes = None
        outbound_ports = 80
        idle_timeout = 3600
        backend_pool_type = "nodeIP"

        load_balancer_models = AKSManagedClusterModels(cmd, ResourceType.MGMT_CONTAINERSERVICE).load_balancer_models
        # store all the models used by load balancer
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
        # ips -> i_ps due to track 2 naming issue
        profile.managed_outbound_i_ps = ManagedClusterLoadBalancerProfileManagedOutboundIPs(
            count=2
        )
        # ips -> i_ps due to track 2 naming issue
        profile.outbound_i_ps = ManagedClusterLoadBalancerProfileOutboundIPs(
            public_i_ps="public_ips"
        )
        profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
            public_ip_prefixes="public_ip_prefixes"
        )
        err = "outbound ip/ipprefix and managed ip should be mutual exclusive."
        with self.assertRaises(InvalidArgumentValueError) as cm:
            loadbalancer.configure_load_balancer_profile(
                managed_outbound_ip_count,
                managed_outbound_ipv6_count,
                outbound_ips,
                outbound_ip_prefixes,
                outbound_ports,
                idle_timeout,
                profile,
                load_balancer_models,
            )
        self.assertEqual(str(cm.exception), err)


if __name__ == '__main__':
    unittest.main()
