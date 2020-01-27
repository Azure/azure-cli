# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from distutils.version import StrictVersion  # pylint: disable=no-name-in-module,import-error

# pylint: disable=no-name-in-module,import-error
from azure.mgmt.containerservice.v2019_11_01.models import ManagedClusterLoadBalancerProfile
from azure.mgmt.containerservice.v2019_11_01.models import ManagedClusterLoadBalancerProfileManagedOutboundIPs
from azure.mgmt.containerservice.v2019_11_01.models import ManagedClusterLoadBalancerProfileOutboundIPPrefixes
from azure.mgmt.containerservice.v2019_11_01.models import ManagedClusterLoadBalancerProfileOutboundIPs
from azure.mgmt.containerservice.v2019_11_01.models import ResourceReference


def set_load_balancer_sku(sku, kubernetes_version):
    if sku:
        return sku
    if kubernetes_version and StrictVersion(kubernetes_version) < StrictVersion("1.13.0"):
        print('Setting load_balancer_sku to basic as it is not specified and kubernetes \
        version(%s) less than 1.13.0 only supports basic load balancer SKU\n' % (kubernetes_version))
        return "basic"
    return "standard"


def _get_load_balancer_outbound_ips(load_balancer_outbound_ips):
    """parse load balancer profile outbound IP ids and return an array of references to the outbound IP resources"""
    load_balancer_outbound_ip_resources = None
    if load_balancer_outbound_ips:
        load_balancer_outbound_ip_resources = \
            [ResourceReference(id=x.strip()) for x in load_balancer_outbound_ips.split(',')]
    return load_balancer_outbound_ip_resources


def _get_load_balancer_outbound_ip_prefixes(load_balancer_outbound_ip_prefixes):
    """parse load balancer profile outbound IP prefix ids and return an array \
    of references to the outbound IP prefix resources"""
    load_balancer_outbound_ip_prefix_resources = None
    if load_balancer_outbound_ip_prefixes:
        load_balancer_outbound_ip_prefix_resources = \
            [ResourceReference(id=x.strip()) for x in load_balancer_outbound_ip_prefixes.split(',')]
    return load_balancer_outbound_ip_prefix_resources


def get_load_balancer_profile(managed_outbound_ip_count,
                               outbound_ips,
                               outbound_ip_prefixes,
                               outbound_ports,
                               load_balancer_idle_timeout):
    """parse and build load balancer profile"""
    load_balancer_outbound_ip_resources = _get_load_balancer_outbound_ips(outbound_ips)
    load_balancer_outbound_ip_prefix_resources = _get_load_balancer_outbound_ip_prefixes(
        outbound_ip_prefixes)

    load_balancer_profile = None
    if is_load_balancer_provided(managed_outbound_ip_count,
                                  load_balancer_outbound_ip_resources,
                                  load_balancer_outbound_ip_prefix_resources,
                                  outbound_ports,
                                  load_balancer_idle_timeout):
        load_balancer_profile = ManagedClusterLoadBalancerProfile()
        if managed_outbound_ip_count:
            load_balancer_profile.managed_outbound_ips = ManagedClusterLoadBalancerProfileManagedOutboundIPs(
                count=managed_outbound_ip_count
            )
        if load_balancer_outbound_ip_resources:
            load_balancer_profile.outbound_ips = ManagedClusterLoadBalancerProfileOutboundIPs(
                public_ips=load_balancer_outbound_ip_resources
            )
        if load_balancer_outbound_ip_prefix_resources:
            load_balancer_profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
                public_ip_prefixes=load_balancer_outbound_ip_prefix_resources
            )
        if outbound_ports:
            load_balancer_profile.allocated_outbound_ports = outbound_ports
        if load_balancer_idle_timeout:
            load_balancer_profile.idle_timeout_in_minutes = load_balancer_idle_timeout
    return load_balancer_profile


def is_load_balancer_provided(managed_outbound_ip_count, outbound_ips, ip_prefixes, outbound_ports, idle_timeout):
    return any([managed_outbound_ip_count,
                outbound_ips,
                ip_prefixes,
                outbound_ports,
                idle_timeout])
