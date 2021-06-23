# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from distutils.version import StrictVersion  # pylint: disable=no-name-in-module,import-error

# pylint: disable=no-name-in-module,import-error
from azure.cli.core.profiles import ResourceType

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


def update_load_balancer_profile(cmd, managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes,
                                 outbound_ports, idle_timeout, profile):
    """parse and update an existing load balancer profile"""
    if not is_load_balancer_profile_provided(managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes,
                                             outbound_ports, idle_timeout):
        return profile
    return configure_load_balancer_profile(cmd, managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes,
                                           outbound_ports, idle_timeout, profile)


def create_load_balancer_profile(cmd, managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes,
                                 outbound_ports, idle_timeout):
    """parse and build load balancer profile"""
    if not is_load_balancer_profile_provided(managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes,
                                             outbound_ports, idle_timeout):
        return None

    ManagedClusterLoadBalancerProfile = cmd.get_models('ManagedClusterLoadBalancerProfile',
                                                       resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                       operation_group='managed_clusters')
    profile = ManagedClusterLoadBalancerProfile()
    return configure_load_balancer_profile(cmd, managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes,
                                           outbound_ports, idle_timeout, profile)


def configure_load_balancer_profile(cmd, managed_outbound_ip_count, outbound_ips, outbound_ip_prefixes, outbound_ports,
                                    idle_timeout, profile):
    """configure a load balancer with customer supplied values"""
    if not profile:
        return profile

    outbound_ip_resources = _get_load_balancer_outbound_ips(cmd, outbound_ips)
    outbound_ip_prefix_resources = _get_load_balancer_outbound_ip_prefixes(
        cmd, outbound_ip_prefixes)

    if managed_outbound_ip_count or outbound_ip_resources or outbound_ip_prefix_resources:
        # ips -> i_ps due to track 2 naming issue
        profile.managed_outbound_i_ps = None
        # ips -> i_ps due to track 2 naming issue
        profile.outbound_i_ps = None
        profile.outbound_ip_prefixes = None
        if managed_outbound_ip_count:
            # ips -> i_ps due to track 2 naming issue
            ManagedClusterLoadBalancerProfileManagedOutboundIPs = cmd.get_models(
                'ManagedClusterLoadBalancerProfileManagedOutboundIPs',
                resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                operation_group='managed_clusters')
            profile.managed_outbound_i_ps = ManagedClusterLoadBalancerProfileManagedOutboundIPs(
                count=managed_outbound_ip_count
            )
        if outbound_ip_resources:
            # ips -> i_ps due to track 2 naming issue
            ManagedClusterLoadBalancerProfileOutboundIPs = cmd.get_models(
                'ManagedClusterLoadBalancerProfileOutboundIPs',
                resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                operation_group='managed_clusters')
            profile.outbound_i_ps = ManagedClusterLoadBalancerProfileOutboundIPs(
                # ips -> i_ps due to track 2 naming issue
                public_i_ps=outbound_ip_resources
            )
        if outbound_ip_prefix_resources:
            ManagedClusterLoadBalancerProfileOutboundIPPrefixes = cmd.get_models(
                'ManagedClusterLoadBalancerProfileOutboundIPPrefixes',
                resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                operation_group='managed_clusters')
            profile.outbound_ip_prefixes = ManagedClusterLoadBalancerProfileOutboundIPPrefixes(
                public_ip_prefixes=outbound_ip_prefix_resources
            )
    if outbound_ports:
        profile.allocated_outbound_ports = outbound_ports
    if idle_timeout:
        profile.idle_timeout_in_minutes = idle_timeout
    return profile


def is_load_balancer_profile_provided(managed_outbound_ip_count, outbound_ips, ip_prefixes,
                                      outbound_ports, idle_timeout):
    return any([managed_outbound_ip_count,
                outbound_ips,
                ip_prefixes,
                outbound_ports,
                idle_timeout])


def _get_load_balancer_outbound_ips(cmd, load_balancer_outbound_ips):
    """parse load balancer profile outbound IP ids and return an array of references to the outbound IP resources"""
    load_balancer_outbound_ip_resources = None
    ResourceReference = cmd.get_models('ResourceReference', resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                       operation_group='managed_clusters')
    if load_balancer_outbound_ips:
        load_balancer_outbound_ip_resources = \
            [ResourceReference(id=x.strip())
             for x in load_balancer_outbound_ips.split(',')]
    return load_balancer_outbound_ip_resources


def _get_load_balancer_outbound_ip_prefixes(cmd, load_balancer_outbound_ip_prefixes):
    """parse load balancer profile outbound IP prefix ids and return an array \
    of references to the outbound IP prefix resources"""
    load_balancer_outbound_ip_prefix_resources = None
    ResourceReference = cmd.get_models('ResourceReference', resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                       operation_group='managed_clusters')
    if load_balancer_outbound_ip_prefixes:
        load_balancer_outbound_ip_prefix_resources = \
            [ResourceReference(id=x.strip())
             for x in load_balancer_outbound_ip_prefixes.split(',')]
    return load_balancer_outbound_ip_prefix_resources
