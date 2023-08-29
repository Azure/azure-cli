# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from distutils.version import StrictVersion  # pylint: disable=deprecated-module
from types import SimpleNamespace
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
)
from knack.log import get_logger

logger = get_logger(__name__)


def set_load_balancer_sku(sku, kubernetes_version):
    if sku:
        return sku
    if kubernetes_version and StrictVersion(kubernetes_version) < StrictVersion("1.13.0"):
        logger.warning('Setting load_balancer_sku to basic as it is not specified and kubernetes'
                       'version(%s) less than 1.13.0 only supports basic load balancer SKU\n',
                       kubernetes_version)
        return "basic"
    return "standard"


def update_load_balancer_profile(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                 outbound_ip_prefixes, outbound_ports, idle_timeout, profile, models):
    """parse and update an existing load balancer profile"""
    if not is_load_balancer_profile_provided(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                             outbound_ip_prefixes, outbound_ports, idle_timeout):
        return profile
    return configure_load_balancer_profile(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                           outbound_ip_prefixes, outbound_ports, idle_timeout, profile, models)


def create_load_balancer_profile(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                 outbound_ip_prefixes, outbound_ports, idle_timeout, models):
    """parse and build load balancer profile"""
    if not is_load_balancer_profile_provided(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                             outbound_ip_prefixes, outbound_ports, idle_timeout):
        return None
    return configure_load_balancer_profile(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                           outbound_ip_prefixes, outbound_ports, idle_timeout, None, models)


def configure_load_balancer_profile(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips,
                                    outbound_ip_prefixes, outbound_ports, idle_timeout, profile, models):
    """configure a load balancer with customer supplied values"""
    if not profile:
        if isinstance(models, SimpleNamespace):
            ManagedClusterLoadBalancerProfile = models.ManagedClusterLoadBalancerProfile
        else:
            ManagedClusterLoadBalancerProfile = models.get("ManagedClusterLoadBalancerProfile")
        profile = ManagedClusterLoadBalancerProfile()
    if any([managed_outbound_ip_count,
            managed_outbound_ipv6_count,
            outbound_ips,
            outbound_ip_prefixes]):
        ip_provider = 0

        outbound_ip_resources = _get_load_balancer_outbound_ips(outbound_ips, models)
        if outbound_ip_resources:
            if isinstance(models, SimpleNamespace):
                ManagedClusterLoadBalancerProfileOutboundIPs = models.ManagedClusterLoadBalancerProfileOutboundIPs
            else:
                ManagedClusterLoadBalancerProfileOutboundIPs = models.get(
                    "ManagedClusterLoadBalancerProfileOutboundIPs"
                )
            # ips -> i_ps due to track 2 naming issue
            profile.outbound_i_ps = ManagedClusterLoadBalancerProfileOutboundIPs(
                public_i_ps=outbound_ip_resources
            )
            profile.managed_outbound_i_ps = None
            profile.outbound_ip_prefixes = None
            ip_provider += 1
        outbound_ip_prefix_resources = _get_load_balancer_outbound_ip_prefixes(outbound_ip_prefixes, models)
        if outbound_ip_prefix_resources:
            if isinstance(models, SimpleNamespace):
                ManagedClusterLoadBalancerProfileOutboundIPPrefixes = (
                    models.ManagedClusterLoadBalancerProfileOutboundIPPrefixes
                )
            else:
                ManagedClusterLoadBalancerProfileOutboundIPPrefixes = models.get(
                    "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
                )
            profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
                public_ip_prefixes=outbound_ip_prefix_resources
            )
            profile.outbound_i_ps = None
            profile.managed_outbound_i_ps = None
            ip_provider += 1

        if managed_outbound_ip_count or managed_outbound_ipv6_count:
            if profile.managed_outbound_i_ps is None:
                if isinstance(models, SimpleNamespace):
                    ManagedClusterLoadBalancerProfileManagedOutboundIPs = (
                        models.ManagedClusterLoadBalancerProfileManagedOutboundIPs
                    )
                else:
                    ManagedClusterLoadBalancerProfileManagedOutboundIPs = models.get(
                        "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
                    )
                profile.managed_outbound_i_ps = ManagedClusterLoadBalancerProfileManagedOutboundIPs()
            if managed_outbound_ip_count:
                profile.managed_outbound_i_ps.count = managed_outbound_ip_count
            if managed_outbound_ipv6_count:
                profile.managed_outbound_i_ps.count_ipv6 = managed_outbound_ipv6_count
            profile.outbound_ip_prefixes = None
            profile.outbound_i_ps = None
            ip_provider += 1
        if ip_provider <= 0 or ip_provider > 1:
            raise InvalidArgumentValueError("outbound ip/ipprefix and managed ip should be mutual exclusive.")
    if outbound_ports:
        profile.allocated_outbound_ports = outbound_ports
    if idle_timeout:
        profile.idle_timeout_in_minutes = idle_timeout
    return profile


def is_load_balancer_profile_provided(managed_outbound_ip_count, managed_outbound_ipv6_count, outbound_ips, ip_prefixes,
                                      outbound_ports, idle_timeout):
    return any([managed_outbound_ip_count,
                managed_outbound_ipv6_count,
                outbound_ips,
                ip_prefixes,
                outbound_ports,
                idle_timeout])


def _get_load_balancer_outbound_ips(load_balancer_outbound_ips, models):
    """parse load balancer profile outbound IP ids and return an array of references to the outbound IP resources"""
    load_balancer_outbound_ip_resources = None
    if isinstance(models, SimpleNamespace):
        ResourceReference = models.ResourceReference
    else:
        ResourceReference = models.get("ResourceReference")
    if load_balancer_outbound_ips is not None:
        if isinstance(load_balancer_outbound_ips, str):
            load_balancer_outbound_ip_resources = \
                [ResourceReference(id=x.strip())
                    for x in load_balancer_outbound_ips.split(',')]
        else:
            load_balancer_outbound_ip_resources = load_balancer_outbound_ips
    return load_balancer_outbound_ip_resources


def _get_load_balancer_outbound_ip_prefixes(load_balancer_outbound_ip_prefixes, models):
    """parse load balancer profile outbound IP prefix ids and return an array \
    of references to the outbound IP prefix resources"""
    load_balancer_outbound_ip_prefix_resources = None
    if isinstance(models, SimpleNamespace):
        ResourceReference = models.ResourceReference
    else:
        ResourceReference = models.get("ResourceReference")
    if load_balancer_outbound_ip_prefixes:
        if isinstance(load_balancer_outbound_ip_prefixes, str):
            load_balancer_outbound_ip_prefix_resources = \
                [ResourceReference(id=x.strip())
                    for x in load_balancer_outbound_ip_prefixes.split(',')]
        else:
            load_balancer_outbound_ip_prefix_resources = load_balancer_outbound_ip_prefixes
    return load_balancer_outbound_ip_prefix_resources
