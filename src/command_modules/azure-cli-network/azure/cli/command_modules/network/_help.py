# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long, too-many-lines

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

helps['network vnet subnet'] = """
    type: group
    short-summary: Manage network interfaces.
"""

# Network Interface (NIC)

helps['network nic'] = """
    type: group
    short-summary: Manage network interfaces (NIC)
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

# NIC ip-config

helps['network nic ip-config'] = """
    type: group
    short-summary: Manage NIC IP configurations.
"""

helps['network nic ip-config create'] = """
    type: command
    short-summary: Create a new IP configuration on a NIC.
    long-summary: You must have the Microsoft.Network/AllowMultipleIpConfigurationsPerNic feature
        enabled for your subscription. Only one configuration may be designated as the primary
        IP configuration per NIC, using the --make-primary flag.
"""

helps['network nic ip-config delete'] = """
    type: command
    short-summary: Delete an IP configuration from a NIC.
    long-summary: A NIC must have at least one IP configuration.
"""

helps['network nic ip-config list'] = """
    type: command
    short-summary: List IP configurations on a NIC.
"""

helps['network nic ip-config show'] = """
    type: command
    short-summary: Show details of an IP configurations on a NIC.
"""

helps['network nic ip-config update'] = """
    type: command
    short-summary: Update an IP configurations on a NIC.
"""

# NIC IP config address pool

helps['network nic ip-config address-pool'] = """
    type: group
    short-summary: Manage NIC IP configuration backend address pools.
"""

helps['network nic ip-config address-pool add'] = """
    type: command
    short-summary: Add a backend address pool reference to an IP configuration.
"""

helps['network nic ip-config address-pool remove'] = """
    type: command
    short-summary: Remove a backend address pool reference from an IP configuration.
"""

# NIC IP config inbound NAT rules

helps['network nic ip-config inbound-nat-rule'] = """
    type: group
    short-summary: Manage NIC IP configuration inbound NAT rules.
"""

helps['network nic ip-config inbound-nat-rule add'] = """
    type: command
    short-summary: Add an inbound NAT rule reference to an IP configuration.
"""

helps['network nic ip-config inbound-nat-rule remove'] = """
    type: command
    short-summary: Remove an inbound NAT rule reference from an IP configuration.
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
    long-summary: You may also create a subnet at the same time by specifying a subnet name and
        (optionally) an address prefix.
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

# Application Gateway

helps['network application-gateway'] = """
    type: group
    short-summary: Provides application-level routing and load balancing services
"""

helps['network application-gateway create'] = """
    type: command
    short-summary: Create a new application gateway.
"""

helps['network application-gateway delete'] = """
    type: command
    short-summary: Delete an application gateway.
"""

helps['network application-gateway list'] = """
    type: command
    short-summary: List application gateways in a resource group or subscription.
"""

helps['network application-gateway show'] = """
    type: command
    short-summary: Show details of an application gateway.
"""

helps['network application-gateway start'] = """
    type: command
    short-summary: Start an application gateway.
"""

helps['network application-gateway stop'] = """
    type: command
    short-summary: Stop an application gateway.
"""

helps['network application-gateway update'] = """
    type: command
    short-summary: Update an application gateway.
"""

# Application Gateway Address Pool

helps['network application-gateway address-pool'] = """
    type: group
    short-summary: Manage application gateway backend address pools.
"""

helps['network application-gateway address-pool create'] = """
    type: command
    short-summary: Create a new application gateway backend address pool.
"""

helps['network application-gateway address-pool delete'] = """
    type: command
    short-summary: Delete an application gateway backend address pool.
"""

helps['network application-gateway address-pool list'] = """
    type: command
    short-summary: List backend address pools in an application gateway.
"""

helps['network application-gateway address-pool show'] = """
    type: command
    short-summary: Show details of an application gateway backend address pool.
"""

# Application Gateway Frontend IP

helps['network application-gateway frontend-ip'] = """
    type: group
    short-summary: Manage application gateway front-end IP addresses
"""

helps['network application-gateway frontend-ip create'] = """
    type: command
    short-summary: Create a new application gateway front-end IP address.
"""

helps['network application-gateway frontend-ip delete'] = """
    type: command
    short-summary: Delete an application gateway front-end IP address.
"""

helps['network application-gateway frontend-ip list'] = """
    type: command
    short-summary: List front-end IP addresses in an application gateway.
"""

helps['network application-gateway frontend-ip show'] = """
    type: command
    short-summary: Show details of an application gateway front-end IP address.
"""

# Application Gateway frontend port

helps['network application-gateway frontend-port'] = """
    type: group
    short-summary: Manage application gateway front-end ports
"""

helps['network application-gateway frontend-port create'] = """
    type: command
    short-summary: Create a new application gateway front-end port.
"""

helps['network application-gateway frontend-port delete'] = """
    type: command
    short-summary: Delete an application gateway front-end port.
"""

helps['network application-gateway frontend-port list'] = """
    type: command
    short-summary: List front-end ports in an application gateway.
"""

helps['network application-gateway frontend-port show'] = """
    type: command
    short-summary: Show details of an application gateway front-end port.
"""

# Application Gateway HTTP listener

helps['network application-gateway http-listener'] = """
    type: group
    short-summary: Manage application gateway HTTP listeners
"""

helps['network application-gateway http-listener create'] = """
    type: command
    short-summary: Create a new application gateway HTTP listener.
"""

helps['network application-gateway http-listener delete'] = """
    type: command
    short-summary: Delete an application gateway HTTP listener.
"""

helps['network application-gateway http-listener list'] = """
    type: command
    short-summary: List HTTP listeners in an application gateway.
"""

helps['network application-gateway http-listener show'] = """
    type: command
    short-summary: Show details of an application gateway HTTP listener.
"""

# Application Gateway HTTP settings

helps['network application-gateway http-settings'] = """
    type: group
    short-summary: Manage application gateway HTTP settings
"""

helps['network application-gateway http-settings create'] = """
    type: command
    short-summary: Create new application gateway HTTP settings.
"""

helps['network application-gateway http-settings delete'] = """
    type: command
    short-summary: Delete application gateway HTTP settings.
"""

helps['network application-gateway http-settings list'] = """
    type: command
    short-summary: List HTTP settings in an application gateway.
"""

helps['network application-gateway http-settings show'] = """
    type: command
    short-summary: Show details of an application gateway HTTP settings.
"""

# Application Gateway probe

helps['network application-gateway probe'] = """
    type: group
    short-summary: Gather information, such as utilization, to be evaluated by rules
"""
helps['network application-gateway probe create'] = """
    type: command
    short-summary: Create a new application gateway probe.
"""

helps['network application-gateway probe delete'] = """
    type: command
    short-summary: Delete an application gateway probe.
"""

helps['network application-gateway probe list'] = """
    type: command
    short-summary: List probes in an application gateway.
"""

helps['network application-gateway probe show'] = """
    type: command
    short-summary: Show details of an application gateway probe.
"""

# Application Gateway rules

helps['network application-gateway rule'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules
"""
helps['network application-gateway rule create'] = """
    type: command
    short-summary: Create a new application gateway rule.
"""

helps['network application-gateway rule delete'] = """
    type: command
    short-summary: Delete an application gateway rule.
"""

helps['network application-gateway rule list'] = """
    type: command
    short-summary: List rules in an application gateway.
"""

helps['network application-gateway rule show'] = """
    type: command
    short-summary: Show details of an application gateway rule.
"""
# Application Gateway SSL Certs

helps['network application-gateway ssl-cert'] = """
    type: group
    short-summary: Manage application gateway SSL certificates
"""
helps['network application-gateway ssl-cert create'] = """
    type: command
    short-summary: Upload an SSL certificate for an application gateway.
"""

helps['network application-gateway ssl-cert delete'] = """
    type: command
    short-summary: Delete an application gateway SSL certificate.
"""

helps['network application-gateway ssl-cert list'] = """
    type: command
    short-summary: List SSL certificates in an application gateway.
"""

helps['network application-gateway ssl-cert show'] = """
    type: command
    short-summary: Show details of an application gateway SSL certificate.
"""
# Application Gateway URL path map

helps['network application-gateway url-path-map'] = """
    type: group
    short-summary: Manage application gateway URL path maps
"""
helps['network application-gateway url-path-map create'] = """
    type: command
    short-summary: Create a new application gateway URL path map.
"""

helps['network application-gateway url-path-map delete'] = """
    type: command
    short-summary: Delete an application gateway URL path map.
"""

helps['network application-gateway url-path-map list'] = """
    type: command
    short-summary: List URL path maps in an application gateway.
"""

helps['network application-gateway url-path-map show'] = """
    type: command
    short-summary: Show details of an application gateway URL path map.
"""
# Application Gateway URL path map rules

helps['network application-gateway url-path-map rule'] = """
    type: group
    short-summary: Manage application gateway URL path map rules
"""
helps['network application-gateway url-path-map rule create'] = """
    type: command
    short-summary: Create a new application gateway URL path map rule.
"""

helps['network application-gateway url-path-map rule delete'] = """
    type: command
    short-summary: Delete an application gateway URL path map rule.
"""

# DNS

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
helps['network dns zone create'] = """
    type: command
    short-summary: Creates or updates DNS zone properties. Does not modify DNS records within the zone.
    parameters:
        - name: --if-none-match
          short-summary: Create only if there isn't an existing DNS zone matches the given one.
"""
helps['network dns zone delete'] = """
    type: command
    short-summary: Deletes a DNS zone. WARNING All DNS records in the zone will also be deleted. This operation cannot be undone.
"""
helps['network dns zone export'] = """
    type: command
    short-summary: Export a DNS zone as a DNS zone file.
"""
helps['network dns zone import'] = """
    type: command
    short-summary: Export a DNS zone as a DNS zone file.
"""
helps['network dns zone list'] = """
    type: command
    short-summary: List DNS zones in a resource group or subscription.
"""
helps['network dns zone show'] = """
    type: command
    short-summary: Gets DNS zone parameters. Does not show DNS records within the zone.
"""
helps['network dns zone update'] = """
    type: command
    short-summary: Updates DNS zone properties. Does not modify DNS records within the zone.
    parameters:
        - name: --if-match
          short-summary: Update only if the resource with the same ETAG exists.
"""
helps['network express-route'] = """
    type: group
    short-summary: Dedicated private network fiber connections to Azure
"""
helps['network express-route create'] = """
    type: command
    short-summary: Create an ExpressRoute circuit.
"""
helps['network express-route delete'] = """
    type: command
    short-summary: Delete an ExpressRoute circuit.
"""
helps['network express-route get-stats'] = """
    type: command
    short-summary: Show stats of an ExpressRoute circuit.
"""
helps['network express-route list'] = """
    type: command
    short-summary: List ExpressRoute circuits in a subscription or resource group.
"""
helps['network express-route list-arp-tables'] = """
    type: command
    short-summary: List the currently advertised ARP table of an ExpressRoute circuit.
"""
helps['network express-route list-route-tables'] = """
    type: command
    short-summary: List the currently advertised route tables of an ExpressRoute circuit.
"""
helps['network express-route show'] = """
    type: command
    short-summary: Show details of an ExpressRoute circuit.
"""
helps['network express-route update'] = """
    type: command
    short-summary: Update settings of an ExpressRoute circuit.
"""
helps['network express-route auth'] = """
    type: group
    short-summary: Manage ExpressRoute circuit authentication
"""
helps['network express-route auth create'] = """
    type: command
    short-summary: Create an authorization setting in an ExpressRoute circuit.
"""
helps['network express-route auth delete'] = """
    type: command
    short-summary: Delete an authorization setting in an ExpressRoute circuit.
"""
helps['network express-route auth list'] = """
    type: command
    short-summary: List authorization settings of an ExpressRoute circuit.
"""
helps['network express-route auth show'] = """
    type: command
    short-summary: Show details of an authorization setting in an ExpressRoute circuit.
"""
helps['network express-route peering'] = """
    type: group
    short-summary: Manage ExpressRoute peering
"""
helps['network express-route peering create'] = """
    type: command
    short-summary: Create peering settings in an ExpressRoute circuit.
"""
helps['network express-route peering delete'] = """
    type: command
    short-summary: Delete peering settings in an ExpressRoute circuit.
"""
helps['network express-route peering list'] = """
    type: command
    short-summary: List peering settings of an ExpressRoute circuit.
"""
helps['network express-route peering show'] = """
    type: command
    short-summary: Show peering details of an ExpressRoute circuit.
"""
helps['network express-route peering update'] = """
    type: command
    short-summary: Update peering settings in an ExpressRoute circuit.
"""
helps['network express-route list-service-providers'] = """
    type: command
    short-summary: List available ExpressRoute service providers.
"""

# Load Balancer

helps['network lb'] = """
    type: group
    short-summary: Deliver high availability and network performance to your applications
"""

helps['network lb create'] = """
    type: command
    short-summary: Create a new load balancer.
"""

helps['network lb delete'] = """
    type: command
    short-summary: Delete a load balancer.
"""

helps['network lb list'] = """
    type: command
    short-summary: List load balancers in a resource group or subscription.
"""

helps['network lb show'] = """
    type: command
    short-summary: Show details of a load balancer.
"""

helps['network lb update'] = """
    type: command
    short-summary: Update a load balancer.
"""

# Load Balancer address pool

helps['network lb address-pool'] = """
    type: group
    short-summary: Manage load balancer backend address pools
"""

helps['network lb address-pool create'] = """
    type: command
    short-summary: Create a new load balancer backend address pool.
"""

helps['network lb address-pool delete'] = """
    type: command
    short-summary: Delete a load balancer backend address pool.
"""

helps['network lb address-pool list'] = """
    type: command
    short-summary: List backend address pools in a load balancer.
"""

helps['network lb address-pool show'] = """
    type: command
    short-summary: Show details of a load balancer backend address pool.
"""

# Load Balancer frontend IP

helps['network lb frontend-ip'] = """
    type: group
    short-summary: Manage load balancer front-end IP addresses
"""

helps['network lb frontend-ip create'] = """
    type: command
    short-summary: Create a new load balancer front-end IP address.
"""

helps['network lb frontend-ip delete'] = """
    type: command
    short-summary: Delete a load balancer front-end IP address.
"""

helps['network lb frontend-ip list'] = """
    type: command
    short-summary: List front-end IP addresses in a load balancer.
"""

helps['network lb frontend-ip show'] = """
    type: command
    short-summary: Show details of a load balancer front-end IP address.
"""

helps['network lb frontend-ip update'] = """
    type: command
    short-summary: Update a load balancer front-end IP address.
"""

# Load Balancer inbound NAT pool

helps['network lb inbound-nat-pool'] = """
    type: group
    short-summary: Manage load balancer inbound NAT address pools
"""

helps['network lb inbound-nat-pool create'] = """
    type: command
    short-summary: Create a new load balancer inbound NAT address pool.
"""

helps['network lb inbound-nat-pool delete'] = """
    type: command
    short-summary: Delete a load balancer inbound NAT address pool.
"""

helps['network lb inbound-nat-pool list'] = """
    type: command
    short-summary: List inbound NAT address pools in a load balancer.
"""

helps['network lb inbound-nat-pool show'] = """
    type: command
    short-summary: Show details of a load balancer inbound NAT address pool.
"""

helps['network lb inbound-nat-pool update'] = """
    type: command
    short-summary: Update a load balancer inbound NAT address pool.
"""

# Load Balancer inbound NAT rule

helps['network lb inbound-nat-rule'] = """
    type: group
    short-summary: Manage load balancer inbound NAT rules
"""

helps['network lb inbound-nat-rule create'] = """
    type: command
    short-summary: Create a new load balancer inbound NAT rule.
"""

helps['network lb inbound-nat-rule delete'] = """
    type: command
    short-summary: Delete a load balancer inbound NAT rule.
"""

helps['network lb inbound-nat-rule list'] = """
    type: command
    short-summary: List inbound NAT rules in a load balancer.
"""

helps['network lb inbound-nat-rule show'] = """
    type: command
    short-summary: Show details of a load balancer inbound NAT rule.
"""

helps['network lb inbound-nat-rule update'] = """
    type: command
    short-summary: Update a load balancer inbound NAT rule.
"""

# Load Balancer probe

helps['network lb probe'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules
"""

helps['network lb probe create'] = """
    type: command
    short-summary: Create a new load balancer probe.
"""

helps['network lb probe delete'] = """
    type: command
    short-summary: Delete a load balancer probe.
"""

helps['network lb probe list'] = """
    type: command
    short-summary: List probes in a load balancer.
"""

helps['network lb probe show'] = """
    type: command
    short-summary: Show details of a load balancer probe.
"""

helps['network lb probe update'] = """
    type: command
    short-summary: Update a load balancer probe.
"""

# Load Balancer rule

helps['network lb rule'] = """
    type: group
    short-summary: Gather information, such as utilization, to be evaluated by rules
"""

helps['network lb rule create'] = """
    type: command
    short-summary: Create a new load balancing rule.
"""

helps['network lb rule delete'] = """
    type: command
    short-summary: Delete a load balancing rule.
"""

helps['network lb rule list'] = """
    type: command
    short-summary: List load balancing rules in a load balancer.
"""

helps['network lb rule show'] = """
    type: command
    short-summary: Show details of a load balancing rule.
"""

helps['network lb rule update'] = """
    type: command
    short-summary: Update a load balancing rule.
"""

# Local Gateway

helps['network local-gateway'] = """
    type: group
    short-summary: Manage local gateways
"""

helps['network local-gateway create'] = """
    type: command
    short-summary: Create a new local VPN gateway.
"""

helps['network local-gateway delete'] = """
    type: command
    short-summary: Delete a local VPN gateway.
"""
helps['network local-gateway list'] = """
    type: command
    short-summary: List local VPN gateways in a resource group.
"""
helps['network local-gateway show'] = """
    type: command
    short-summary: Show details of a local VPN gateway.
"""

helps['network local-gateway update'] = """
    type: command
    short-summary: Update an existing local VPN gateway.
"""

# Network Security Group (NSG)

helps['network nsg'] = """
    type: group
    short-summary: Manage Network Security Groups (NSG)
"""
helps['network nsg rule'] = """
    type: group
    short-summary: Manage NSG rules
"""

# Public IP

helps['network public-ip'] = """
    type: group
    short-summary: Manage public IP addresses
"""

helps['network public-ip create'] = """
    type: command
    short-summary: Create a new public IP address.
"""

helps['network public-ip delete'] = """
    type: command
    short-summary: Delete a public IP address.
"""

helps['network public-ip list'] = """
    type: command
    short-summary: List public IP addresses within a resource group or subscription.
"""

helps['network public-ip show'] = """
    type: command
    short-summary: Show details of a public IP address.
"""

helps['network public-ip update'] = """
    type: command
    short-summary: Update an existing public IP address.
"""

# Route Table

helps['network route-table'] = """
    type: group
    short-summary: Manage route tables
"""
helps['network route-table route'] = """
    type: group
    short-summary: Manage route table routes
"""

# Traffic Manager

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

helps['network traffic-manager profile check-dns'] = """
    type: command
    short-summary: Check the availability of a Traffic Manager relative DNS name.
"""

helps['network traffic-manager profile create'] = """
    type: command
    short-summary: Create a new Traffic Manager profile.
"""

helps['network traffic-manager profile delete'] = """
    type: command
    short-summary: Delete a Traffic Manager profile.
"""

helps['network traffic-manager profile list'] = """
    type: command
    short-summary: List Traffic Manager profiles in a resource group or subscription.
"""

helps['network traffic-manager profile show'] = """
    type: command
    short-summary: Show details of a Traffic Manager profile.
"""

helps['network traffic-manager profile update'] = """
    type: command
    short-summary: Update an existing Traffic Manager profile.
"""

helps['network traffic-manager endpoint create'] = """
    type: command
    short-summary: Create a new Traffic Manager endpoint.
"""

helps['network traffic-manager endpoint delete'] = """
    type: command
    short-summary: Delete a Traffic Manager endpoint.
"""

helps['network traffic-manager endpoint list'] = """
    type: command
    short-summary: List Traffic Manager endpoints in a resource group.
"""

helps['network traffic-manager endpoint show'] = """
    type: command
    short-summary: Show details of a Traffic Manager endpoint.
"""

helps['network traffic-manager endpoint update'] = """
    type: command
    short-summary: Update an existing Traffic Manager endpoint.
"""

# Virtual Network (VNET)

helps['network vnet'] = """
    type: group
    short-summary: Provision private networks
"""
helps['network vnet subnet'] = """
    type: group
    short-summary: Manage subnets
"""

# VPN Connection

helps['network vpn-connection'] = """
    type: group
    short-summary: Manage VPN connections
"""

helps['network vpn-connection create'] = """
    type: command
    short-summary: Create a new VPN connection.
"""

helps['network vpn-connection delete'] = """
    type: command
    short-summary: Delete a VPN connection.
"""

helps['network vpn-connection list'] = """
    type: command
    short-summary: List VPN connections in a resource group or subscription.
"""

helps['network vpn-connection show'] = """
    type: command
    short-summary: Show details of a VPN connection.
"""

helps['network vpn-connection update'] = """
    type: command
    short-summary: Update a VPN connection.
"""

# VPN Connection shared key

helps['network vpn-connection shared-key'] = """
    type: group
    short-summary: Manage VPN shared keys
"""

helps['network vpn-connection shared-key reset'] = """
    type: command
    short-summary: Reset the VPN connection shared key.
"""

helps['network vpn-connection shared-key show'] = """
    type: command
    short-summary: Show the VPN connection shared key.
"""

helps['network vpn-connection shared-key update'] = """
    type: command
    short-summary: Update a VPN connection shared key.
"""

# VPN Gateway

helps['network vpn-gateway'] = """
    type: group
    short-summary: Establish secure, cross-premises connectivity
"""

helps['network vpn-gateway create'] = """
    type: command
    short-summary: Create a VPN gateway.
"""

helps['network vpn-gateway create'] = """
    type: command
    short-summary: Create a VPN gateway.
"""

helps['network vpn-gateway delete'] = """
    type: command
    short-summary: Delete a VPN gateway.
"""

helps['network vpn-gateway list'] = """
    type: command
    short-summary: List VPN gateways in a resource group or subscription.
"""

helps['network vpn-gateway reset'] = """
    type: command
    short-summary: Reset a VPN gateway.
"""

helps['network vpn-gateway show'] = """
    type: command
    short-summary: Show details of a VPN gateway.
"""

helps['network vpn-gateway update'] = """
    type: command
    short-summary: Update a VPN gateway.
"""

# VPN Gateway Revoke Cert

helps['network vpn-gateway revoked-cert'] = """
    type: group
    short-summary: Manage VPN gateway revoked certificates
"""

helps['network vpn-gateway revoked-cert create'] = """
    type: command
    short-summary: Revoke a VPN gateway certficate.
"""

helps['network vpn-gateway revoked-cert delete'] = """
    type: command
    short-summary: Delete a revoked VPN gateway certificate.
"""

# VPN Gateway Root Cert

helps['network vpn-gateway root-cert'] = """
    type: group
    short-summary: Manage VPN gateway root certificates
"""

helps['network vpn-gateway root-cert create'] = """
    type: command
    short-summary: Upload a VPN gateway root certificate.
"""

helps['network vpn-gateway root-cert delete'] = """
    type: command
    short-summary: Delete a VPN gateway root certificate.
"""
