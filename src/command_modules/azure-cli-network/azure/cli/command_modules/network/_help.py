#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['network dns record-set create'] = """
            type: command
            parameters:
                - name: --type
                  short-summary: The type of DNS records in the record set.
                - name: --ttl
                  short-summary: Record set TTL (time-to-live).
"""

for t in ['add', 'remove']:
    helps['network dns record aaaa {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --ipv6-address
                      short-summary: IPV6 address in string notation.
    """

    helps['network dns record a {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --ipv4-address
                      short-summary: IPV4 address in string notation.
    """

    helps['network dns record cname {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --cname
                      short-summary: Canonical name.
    """

    helps['network dns record mx {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --exchange
                      short-summary: Exchange metric
                    - name: --preference
                      short-summary: preference metric
    """

    helps['network dns record ns {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --dname
                      short-summary: Name server domain name.
    """

    helps['network dns record ptr {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --dname
                      short-summary: PTR target domain name.
    """

    helps['network dns record srv {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --priority
                      short-summary: Priority metric.
                    - name: --weight
                      short-summary: Weight metric.
                    - name: --port
                      short-summary: Service port.
                    - name: --target
                      short-summary: Target domain name.
    """

    helps['network dns record txt {0}'.format(t)] = """
                type: command
                parameters:
                    - name: --value
                      short-summary: List of text values.
    """

helps['network dns record update-soa'] = """
            type: command
            parameters:
                - name: --email
                  short-summary: Email address.
                - name: --serial-number
                  short-summary: Serial number.
                - name: --refresh-time
                  short-summary: Refresh value (seconds).
                - name: --retry-time
                  short-summary: Retry time (seconds).
                - name: --expire-time
                  short-summary: Expire time (seconds).
                - name: --minimum-ttl
                  short-summary: Minimum TTL (time-to-live, seconds).
"""

# Network Interface (NIC)

helps['network vnet subnet'] = """
    type: group
    short-summary: Manage network interfaces.
"""

helps['network nic show-effective-route-table'] = """
    type: command
    short-summary: Show all route tables applied on a network interface.
"""

helps['network nic list-effective-nsg'] = """
    type: command
    short-summary: List all network security groups applied on a network interface.
"""

helps['network nic create'] = """
    type: command
    short-summary: Create a network interface.
"""

helps['network nic delete'] = """
    type: command
    short-summary: Delete a network interface.
"""

helps['network nic list'] = """
    type: command
    short-summary: List network interfaces within a subscription or resource group.
    long-summary: |
        Does not list network interfaces attached to scale set virtual machines. Use 'az vmss nic list' or 'az vmss nic list-vm-nics' to display that information.
"""

helps['network nic show'] = """
    type: command
    short-summary: Show details on a network interface.
"""

helps['network nic update'] = """
    type: command
    short-summary: Update a network interface.
"""

# Virtual Network (VNET)

helps['network vnet subnet'] = """
    type: group
    short-summary: Manage virtual networks.
"""

helps['network vnet check-ip-address'] = """
    type: command
    short-summary: Check whether a private IP address is available for use.
"""

helps['network vnet create'] = """
    type: command
    short-summary: Create a virtual network.
"""

helps['network vnet delete'] = """
    type: command
    short-summary: Delete a virtual network.
"""

helps['network vnet list'] = """
    type: command
    short-summary: List virtual networks within a resource group or subscription.
"""

helps['network vnet show'] = """
    type: command
    short-summary: Show details on a virtual network.
"""

helps['network vnet update'] = """
    type: command
    short-summary: Update a virtual network.
"""

# VNET Subnet

helps['network vnet subnet'] = """
    type: group
    short-summary: Manage virtual network subnets.
"""

helps['network vnet subnet create'] = """
    type: command
    short-summary: Create a virtual network subnet.
"""

helps['network vnet subnet delete'] = """
    type: command
    short-summary: Delete a virtual network subnet.
"""

helps['network vnet subnet list'] = """
    type: command
    short-summary: List subnets within a virtual network.
"""

helps['network vnet subnet show'] = """
    type: command
    short-summary: Show details on a virtual network subnet.
"""

helps['network vnet subnet update'] = """
    type: command
    short-summary: Update a virtual network subnet.
"""

# Virtual Network (VNET) Peering

helps['network vnet peering'] = """
    type: group
    short-summary: Manage peering connections between virtual networks.
"""

helps['network vnet peering create'] = """
    type: command
    short-summary: Create a virtual network peering.
"""

helps['network vnet peering delete'] = """
    type: command
    short-summary: Delete a virtual network peering.
"""

helps['network vnet peering list'] = """
    type: command
    short-summary: List peerings within a virtual network.
"""

helps['network vnet peering show'] = """
    type: command
    short-summary: Show details on a virtual network peering.
"""

helps['network vnet peering update'] = """
    type: command
    short-summary: Update a virtual network peering.
"""
