# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import importlib
import unittest
from unittest import mock

from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.acs import _loadbalancer as loadbalancer


class TestLoadBalancer(unittest.TestCase):

    def test_configure_load_balancer_profile(self):
        managed_outbound_ip_count = 5
        outbound_ips = None
        outbound_ip_prefixes = None
        outbound_ports = 80
        idle_timeout = 3600

        # load models directly (instead of through the `get_sdk` method provided by the cli component)
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES
        sdk_profile = AZURE_API_PROFILES["2020-09-01-hybrid"][
            ResourceType.MGMT_CONTAINERSERVICE
        ]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(
            api_version.replace("-", "_")
        )
        module = importlib.import_module(module_name)

        ManagedClusterLoadBalancerProfile = getattr(
            module, "ManagedClusterLoadBalancerProfile"
        )
        ManagedClusterLoadBalancerProfileManagedOutboundIPs = getattr(
            module, "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
        )
        ManagedClusterLoadBalancerProfileOutboundIPs = getattr(
            module, "ManagedClusterLoadBalancerProfileOutboundIPs"
        )
        ManagedClusterLoadBalancerProfileOutboundIPPrefixes = getattr(
            module, "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
        )
        ResourceReference = getattr(module, "ResourceReference")
        lb_models = {
            "ManagedClusterLoadBalancerProfile": ManagedClusterLoadBalancerProfile,
            "ManagedClusterLoadBalancerProfileManagedOutboundIPs": ManagedClusterLoadBalancerProfileManagedOutboundIPs,
            "ManagedClusterLoadBalancerProfileOutboundIPs": ManagedClusterLoadBalancerProfileOutboundIPs,
            "ManagedClusterLoadBalancerProfileOutboundIPPrefixes": ManagedClusterLoadBalancerProfileOutboundIPPrefixes,
            "ResourceReference": ResourceReference,
        }

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
            lb_models,
        )

        self.assertEqual(p.managed_outbound_i_ps.count, 5)
        self.assertEqual(p.outbound_i_ps, None)
        self.assertEqual(p.outbound_ip_prefixes, None)
        self.assertEqual(p.allocated_outbound_ports, 80)
        self.assertEqual(p.idle_timeout_in_minutes, 3600)


if __name__ == '__main__':
    unittest.main()
