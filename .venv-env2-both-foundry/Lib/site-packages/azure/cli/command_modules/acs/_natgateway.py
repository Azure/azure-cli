# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from types import SimpleNamespace


def create_nat_gateway_profile(managed_outbound_ip_count, idle_timeout, models: SimpleNamespace):
    """parse and build NAT gateway profile"""
    if not is_nat_gateway_profile_provided(managed_outbound_ip_count, idle_timeout):
        return None

    profile = models.ManagedClusterNATGatewayProfile()
    return configure_nat_gateway_profile(managed_outbound_ip_count, idle_timeout, profile, models)


def update_nat_gateway_profile(managed_outbound_ip_count, idle_timeout, profile, models: SimpleNamespace):
    """parse and update an existing NAT gateway profile"""
    if not is_nat_gateway_profile_provided(managed_outbound_ip_count, idle_timeout):
        return profile
    if not profile:
        profile = models.ManagedClusterNATGatewayProfile()
    return configure_nat_gateway_profile(managed_outbound_ip_count, idle_timeout, profile, models)


def is_nat_gateway_profile_provided(managed_outbound_ip_count, idle_timeout):
    return any([managed_outbound_ip_count is not None, idle_timeout])


def configure_nat_gateway_profile(managed_outbound_ip_count, idle_timeout, profile, models: SimpleNamespace):
    """configure a NAT Gateway with customer supplied values"""
    if managed_outbound_ip_count is not None:
        ManagedClusterManagedOutboundIPProfile = models.ManagedClusterManagedOutboundIPProfile
        profile.managed_outbound_ip_profile = ManagedClusterManagedOutboundIPProfile(
            count=managed_outbound_ip_count
        )

    if idle_timeout:
        profile.idle_timeout_in_minutes = idle_timeout

    return profile
