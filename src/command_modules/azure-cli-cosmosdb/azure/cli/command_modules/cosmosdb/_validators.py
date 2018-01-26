# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def validate_failover_policies(ns):
    """ Extracts multiple space-separated failoverPolicies in regionName=failoverPriority format """
    from azure.mgmt.cosmosdb.models.failover_policy import FailoverPolicy
    fp_dict = []
    for item in ns.failover_policies:
        comps = item.split('=', 1)
        fp_dict.append(FailoverPolicy(comps[0], int(comps[1])))
    ns.failover_policies = fp_dict


def validate_locations(ns):
    """ Extracts multiple space-separated locations in regionName=failoverPriority format """
    from azure.mgmt.cosmosdb.models.location import Location
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
