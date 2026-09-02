# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from types import SimpleNamespace


def create_nat_gateway_profile(
    managed_outbound_ip_count,
    idle_timeout,
    models: SimpleNamespace,
    managed_outbound_ipv6_count=None,
    outbound_ip_ids=None,
    outbound_ip_prefix_ids=None,
    nat_gateway_sku=None,
):
    """parse and build NAT gateway profile"""
    if not is_nat_gateway_profile_provided(
        managed_outbound_ip_count, idle_timeout,
        managed_outbound_ipv6_count, outbound_ip_ids, outbound_ip_prefix_ids,
        nat_gateway_sku,
    ):
        return None

    profile = models.ManagedClusterNATGatewayProfile()
    return configure_nat_gateway_profile(
        managed_outbound_ip_count, idle_timeout, profile, models,
        managed_outbound_ipv6_count, outbound_ip_ids, outbound_ip_prefix_ids,
        nat_gateway_sku,
    )


def update_nat_gateway_profile(
    managed_outbound_ip_count,
    idle_timeout,
    profile,
    models: SimpleNamespace,
    managed_outbound_ipv6_count=None,
    outbound_ip_ids=None,
    outbound_ip_prefix_ids=None,
    nat_gateway_sku=None,
):
    """parse and update an existing NAT gateway profile"""
    if not is_nat_gateway_profile_provided(
        managed_outbound_ip_count, idle_timeout,
        managed_outbound_ipv6_count, outbound_ip_ids, outbound_ip_prefix_ids,
        nat_gateway_sku,
    ):
        return profile
    if not profile:
        profile = models.ManagedClusterNATGatewayProfile()
    return configure_nat_gateway_profile(
        managed_outbound_ip_count, idle_timeout, profile, models,
        managed_outbound_ipv6_count, outbound_ip_ids, outbound_ip_prefix_ids,
        nat_gateway_sku,
    )


def is_nat_gateway_profile_provided(
    managed_outbound_ip_count,
    idle_timeout,
    managed_outbound_ipv6_count=None,
    outbound_ip_ids=None,
    outbound_ip_prefix_ids=None,
    nat_gateway_sku=None,
):
    return any([
        managed_outbound_ip_count is not None,
        idle_timeout,
        managed_outbound_ipv6_count is not None,
        outbound_ip_ids is not None,
        outbound_ip_prefix_ids is not None,
        nat_gateway_sku is not None,
    ])


def configure_nat_gateway_profile(
    managed_outbound_ip_count,
    idle_timeout,
    profile,
    models: SimpleNamespace,
    managed_outbound_ipv6_count=None,
    outbound_ip_ids=None,
    outbound_ip_prefix_ids=None,
    nat_gateway_sku=None,
):
    """configure a NAT Gateway with customer supplied values"""
    if managed_outbound_ip_count is not None or managed_outbound_ipv6_count is not None:
        ManagedClusterManagedOutboundIPProfile = models.ManagedClusterManagedOutboundIPProfile
        if not profile.managed_outbound_ip_profile:
            profile.managed_outbound_ip_profile = ManagedClusterManagedOutboundIPProfile()
        if managed_outbound_ip_count is not None:
            profile.managed_outbound_ip_profile.count = managed_outbound_ip_count
        if managed_outbound_ipv6_count is not None:
            profile.managed_outbound_ip_profile.count_ipv6 = managed_outbound_ipv6_count

    if idle_timeout:
        profile.idle_timeout_in_minutes = idle_timeout

    if outbound_ip_ids is not None:
        ManagedClusterNATGatewayProfileOutboundIPs = models.ManagedClusterNATGatewayProfileOutboundIPs
        ip_id_list = [x.strip() for x in outbound_ip_ids.split(',') if x.strip()]
        profile.outbound_i_ps = ManagedClusterNATGatewayProfileOutboundIPs(
            public_i_ps=ip_id_list
        )

    if outbound_ip_prefix_ids is not None:
        ManagedClusterNATGatewayProfileOutboundIpPrefixes = models.ManagedClusterNATGatewayProfileOutboundIpPrefixes
        prefix_id_list = [x.strip() for x in outbound_ip_prefix_ids.split(',') if x.strip()]
        profile.outbound_ip_prefixes = ManagedClusterNATGatewayProfileOutboundIpPrefixes(
            public_ip_prefixes=prefix_id_list
        )

    if nat_gateway_sku is not None:
        # GA shape: V2 is expressed as outboundType=managedNATGateway + natGatewayProfile.sku.
        profile.sku = nat_gateway_sku

    return profile
