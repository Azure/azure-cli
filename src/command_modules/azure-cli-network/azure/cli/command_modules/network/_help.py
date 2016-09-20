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

helps['network'] = """
    type: group
    short-summary: Manages Network resources
"""
helps['network application-gateway'] = """
    type: group
    short-summary: Provides application-level routing and load balancing services
"""
helps['network application-gateway address-pool'] = """
    type: group
    short-summary: Manage application gateway address pools
"""
helps['network application-gateway frontend-ip'] = """
    type: group
    short-summary: Manage application gateway front-end IP addresses
"""
helps['network application-gateway frontend-port'] = """
    type: group
    short-summary: Manage application gateway front-end ports
"""
helps['network application-gateway http-listener'] = """
    type: group
    short-summary: Manage application gateway HTTP listeners
"""
helps['network application-gateway http-settings'] = """
    type: group
    short-summary: Manage application gateway HTTP settings
"""
helps['network application-gateway probe'] = """
    type: group
    short-summary: Gather information, such as utilization, to be evaluated by rules
"""
helps['network application-gateway rule'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules
"""
helps['network application-gateway ssl-cert'] = """
    type: group
    short-summary: Manage application gateway SSL certificates
"""
helps['network application-gateway url-path-map'] = """
    type: group
    short-summary: Manage application gateway URL path maps
"""
helps['network application-gateway url-path-map rule'] = """
    type: group
    short-summary: Manage application gateway URL path map rules
"""
helps['network dns'] = """
    type: group
    short-summary: Host your DNS domain in Azure
"""
helps['network dns record'] = """
    type: group
    short-summary: Manage DNS records contained in a record set
"""
helps['network dns record a'] = """
    type: group
    short-summary: Manage DNS A records
"""
helps['network dns record aaaa'] = """
    type: group
    short-summary: Manage DNS AAAA records
"""
helps['network dns record cname'] = """
    type: group
    short-summary: Manage DNS CNAME records
"""
helps['network dns record mx'] = """
    type: group
    short-summary: Manage DNS MX (mail) records
"""
helps['network dns record ns'] = """
    type: group
    short-summary: Manage DNS NS (nameserver) records
"""
helps['network dns record ptr'] = """
    type: group
    short-summary: Manage DNS PTR (pointer) records
"""
helps['network dns record srv'] = """
    type: group
    short-summary: Manage DNS SRV records
"""
helps['network dns record txt'] = """
    type: group
    short-summary: Manage DNS TXT records
"""
helps['network dns record-set'] = """
    type: group
    short-summary: Manage DNS record-set
"""
helps['network dns zone'] = """
    type: group
    short-summary: Manage DNS zones
"""
helps['network express-route'] = """
    type: group
    short-summary: Dedicated private network fiber connections to Azure
"""
helps['network express-route circuit'] = """
    type: group
    short-summary: Manage express route circuits
"""
helps['network express-route circuit-auth'] = """
    type: group
    short-summary: Manage express route circuit authentication
"""
helps['network express-route circuit-peering'] = """
    type: group
    short-summary: Manage express route peering
"""
helps['network express-route service-provider'] = """
    type: group
    short-summary: View express route service providers
"""
helps['network lb'] = """
    type: group
    short-summary: Deliver high availability and network performance to your applications
"""
helps['network lb address-pool'] = """
    type: group
    short-summary: Manage LB address pools
"""
helps['network lb frontend-ip'] = """
    type: group
    short-summary: Manage LB front-end IP addresses
"""
helps['network lb inbound-nat-pool'] = """
    type: group
    short-summary: Manage LB inbound NAT address pools
"""
helps['network lb inbound-nat-rule'] = """
    type: group
    short-summary: Manage LB inbound NAT rules
"""
helps['network lb probe'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules
"""
helps['network lb rule'] = """
    type: group
    short-summary: Gather information, such as utilization, to be evaluated by rules
"""
helps['network local-gateway'] = """
    type: group
    short-summary: Manage local gateways
"""
helps['network nic'] = """
    type: group
    short-summary: Manage network interfaces (NIC)
"""
helps['network nic ip-config'] = """
    type: group
    short-summary: Manage NIC ip configurations
"""
helps['network nic ip-config address-pool'] = """
    type: group
    short-summary: Manage NIC address pools
"""
helps['network nic ip-config inbound-nat-rule'] = """
    type: group
    short-summary: Manage NIC inbound NAT rules
"""
helps['network nsg'] = """
    type: group
    short-summary: Manage Network Security Groups (NSG)
"""
helps['network nsg rule'] = """
    type: group
    short-summary: Manage NSG rules
"""
helps['network public-ip'] = """
    type: group
    short-summary: Manage public IP addresses
"""
helps['network route-table'] = """
    type: group
    short-summary: Manage route tables
"""
helps['network route-table route'] = """
    type: group
    short-summary: Manage route table routes
"""
helps['network traffic-manager'] = """
    type: group
    short-summary: Route incoming traffic for high performance and availability
"""
helps['network traffic-manager endpoint'] = """
    type: group
    short-summary: Manage traffic manager end points
"""
helps['network traffic-manager profile'] = """
    type: group
    short-summary: Manage traffic manager profiles
"""
helps['network vnet'] = """
    type: group
    short-summary: Provision private networks
"""
helps['network vnet subnet'] = """
    type: group
    short-summary: Manage subnets
"""
helps['network vpn-connection'] = """
    type: group
    short-summary: Manage VPN connections
"""
helps['network vpn-connection shared-key'] = """
    type: group
    short-summary: Manage VPN shared keys
"""
helps['network vpn-gateway'] = """
    type: group
    short-summary: Establish secure, cross-premises connectivity
"""
helps['network vpn-gateway revoked-cert'] = """
    type: group
    short-summary: Manage VPN gateway revoked certificates
"""
helps['network vpn-gateway root-cert'] = """
    type: group
    short-summary: Manage VPN gateway root certificates
"""
