# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def validate_failover_policies(ns):
    """ Extracts multiple space-separated failoverPolicies in regionName=failoverPriority format """
    from azure.mgmt.cosmosdb.models import FailoverPolicy
    fp_dict = []
    for item in ns.failover_policies:
        comps = item.split('=', 1)
        fp_dict.append(FailoverPolicy(location_name=comps[0], failover_priority=int(comps[1])))
    ns.failover_policies = fp_dict


def validate_locations(ns):
    """ Extracts multiple space-separated locations in regionName=failoverPriority format """
    from azure.mgmt.cosmosdb.models import Location
    if ns.locations is None:
        ns.locations = []
        return
    loc_dict = []
    for item in ns.locations:
        comps = item.split('=', 1)
        loc_dict.append(Location(location_name=comps[0], failover_priority=int(comps[1])))
    ns.locations = loc_dict


def validate_ip_range_filter(ns):
    if ns.ip_range_filter:
        ns.ip_range_filter = ",".join(ns.ip_range_filter)


def validate_capabilities(ns):
    """ Extracts multiple space-separated capabilities """
    from azure.mgmt.cosmosdb.models import Capability
    if ns.capabilities is not None:
        capabilties_list = []
        for item in ns.capabilities:
            capabilties_list.append(Capability(name=item))
        ns.capabilities = capabilties_list


def validate_virtual_network_rules(ns):
    """ Extracts multiple space-separated virtual network rules
    in vnetId[=ignoreMissingVNetServiceEndpoint] format"""
    from azure.mgmt.cosmosdb.models import VirtualNetworkRule
    if ns.virtual_network_rules is not None:
        virtual_network_rules_list = []
        for item in ns.virtual_network_rules:
            comps = item.split('=', 1)
            ignore_missing_endpoint = comps[1].lower() == "true" if len(comps) > 1 else True
            vnet_rule = VirtualNetworkRule(id=comps[0], ignore_missing_vnet_service_endpoint=ignore_missing_endpoint)
            virtual_network_rules_list.append(vnet_rule)
        ns.virtual_network_rules = virtual_network_rules_list
