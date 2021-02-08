# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def validate_failover_policies(ns):
    """ Extracts multiple space-separated failoverPolicies in regionName=failoverPriority format """
    from azure.mgmt.cosmosdb.models import FailoverPolicy
    fp_dict = []
    for item in ns.failover_policies:
        comps = item.split('=', 1)
        fp_dict.append(FailoverPolicy(location_name=comps[0], failover_priority=int(comps[1])))
    ns.failover_policies = fp_dict


def validate_ip_range_filter(ns):
    """ Extracts multiple comma-separated ip rules """
    from azure.mgmt.cosmosdb.models import IpAddressOrRange
    if ns.ip_range_filter is not None:
        ip_rules_list = []
        for item in ns.ip_range_filter:
            for i in item.split(","):
                if i:
                    ip_rules_list.append(IpAddressOrRange(ip_address_or_range=i))
                    ns.ip_range_filter = ip_rules_list
        ns.ip_range_filter = ip_rules_list


def validate_private_endpoint_connection_id(ns):
    if ns.connection_id:
        from azure.cli.core.util import parse_proxy_resource_id
        result = parse_proxy_resource_id(ns.connection_id)
        ns.resource_group_name = result['resource_group']
        ns.account_name = result['name']
        ns.private_endpoint_connection_name = result['child_name_1']

    if not all([ns.account_name, ns.resource_group_name, ns.private_endpoint_connection_name]):
        raise CLIError(None, 'incorrect usage: [--id ID | --name NAME --account-name NAME --resource-group NAME]')

    del ns.connection_id


def validate_capabilities(ns):
    """ Extracts multiple space-separated capabilities """
    from azure.mgmt.cosmosdb.models import Capability
    if ns.capabilities is not None:
        capabilties_list = []
        for item in ns.capabilities:
            capabilties_list.append(Capability(name=item))
        ns.capabilities = capabilties_list


def validate_virtual_network_rules(ns):
    """ Extracts multiple space-separated virtual network rules """
    from azure.mgmt.cosmosdb.models import VirtualNetworkRule
    if ns.virtual_network_rules is not None:
        virtual_network_rules_list = []
        for item in ns.virtual_network_rules:
            virtual_network_rules_list.append(VirtualNetworkRule(id=item))
        ns.virtual_network_rules = virtual_network_rules_list
