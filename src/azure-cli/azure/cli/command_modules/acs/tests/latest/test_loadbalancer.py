# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock

from knack import CLI

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.profiles import get_sdk, ResourceType, supported_api_version

from azure.mgmt.containerservice.v2021_03_01.models import ManagedClusterLoadBalancerProfile
from azure.mgmt.containerservice.v2021_03_01.models import ManagedClusterLoadBalancerProfileManagedOutboundIPs
from azure.mgmt.containerservice.v2021_03_01.models import ManagedClusterLoadBalancerProfileOutboundIPPrefixes
from azure.mgmt.containerservice.v2021_03_01.models import ManagedClusterLoadBalancerProfileOutboundIPs
from azure.cli.core.util import CLIError
from azure.cli.command_modules.acs import _loadbalancer as loadbalancer

class TestLoadBalancer(unittest.TestCase):

    def test_configure_load_balancer_profile(self):
        cmd = mock.MagicMock()
        managed_outbound_ip_count = 5
        outbound_ips = None
        outbound_ip_prefixes = None
        outbound_ports = 80
        idle_timeout = 3600

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

        p = loadbalancer.configure_load_balancer_profile(cmd,
            managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes, outbound_ports, idle_timeout, profile)

        self.assertIsNotNone(p.managed_outbound_i_ps)
        self.assertIsNone(p.outbound_i_ps)
        self.assertIsNone(p.outbound_ip_prefixes)


if __name__ == '__main__':
    unittest.main()
