# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long, too-many-lines

helps['network'] = """
    type: group
    short-summary: Manages Azure Network resources.
"""

helps['network dns'] = """
    type: group
    short-summary: Host your DNS domain in Azure.
"""

# region Application Gateway

helps['network application-gateway'] = """
    type: group
    short-summary: Provides application-level routing and load balancing services.
"""

helps['network application-gateway create'] = """
    type: command
    short-summary: Create an application gateway.
"""

helps['network application-gateway delete'] = """
    type: command
    short-summary: Delete an application gateway.
"""

helps['network application-gateway list'] = """
    type: command
    short-summary: List application gateways.
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

helps['network application-gateway show-backend-health'] = """
    type: command
    short-summary: Show details about the backend health of an application gateway.
"""

helps['network application-gateway wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the application gateway is met.
"""
#endregion

# region Application Gateway Address Pool

helps['network application-gateway address-pool'] = """
    type: group
    short-summary: Manage backend address pools for an application gateway.
"""

helps['network application-gateway address-pool create'] = """
    type: command
    short-summary: Create a backend address pool.
"""

helps['network application-gateway address-pool delete'] = """
    type: command
    short-summary: Delete a backend address pool.
"""

helps['network application-gateway address-pool list'] = """
    type: command
    short-summary: List backend address pools.
"""

helps['network application-gateway address-pool show'] = """
    type: command
    short-summary: Show details of a backend address pool.
"""

helps['network application-gateway address-pool update'] = """
    type: command
    short-summary: Update a backend address pool.
"""
# endregion

# region Application Gateway Authorization Cert
helps['network application-gateway auth-cert'] = """
    type: group
    short-summary: Manage authorization certificates for an application gateway.
"""

helps['network application-gateway auth-cert create'] = """
    type: command
    short-summary: Create an authorization certificate.
"""

helps['network application-gateway auth-cert delete'] = """
    type: command
    short-summary: Delete an authorization certificate.
"""

helps['network application-gateway auth-cert list'] = """
    type: command
    short-summary: List authorization certificates.
"""

helps['network application-gateway auth-cert show'] = """
    type: command
    short-summary: Show details of an authorization certificate.
"""

helps['network application-gateway auth-cert update'] = """
    type: command
    short-summary: Update an authorization certificate.
"""
# endregion

# region Application Gateway Frontend IP

helps['network application-gateway frontend-ip'] = """
    type: group
    short-summary: Manage frontend IP addresses for an application gateway.
"""

helps['network application-gateway frontend-ip create'] = """
    type: command
    short-summary: Create a frontend IP address.
"""

helps['network application-gateway frontend-ip delete'] = """
    type: command
    short-summary: Delete a frontend IP address.
"""

helps['network application-gateway frontend-ip list'] = """
    type: command
    short-summary: List frontend IP addresses.
"""

helps['network application-gateway frontend-ip show'] = """
    type: command
    short-summary: Show details of a frontend IP address.
"""

helps['network application-gateway frontend-ip update'] = """
    type: command
    short-summary: Update a frontend IP address.
"""
#endregion

# region Application Gateway frontend port

helps['network application-gateway frontend-port'] = """
    type: group
    short-summary: Manage frontend ports for an application gateway.
"""

helps['network application-gateway frontend-port create'] = """
    type: command
    short-summary: Create a frontend port.
"""

helps['network application-gateway frontend-port delete'] = """
    type: command
    short-summary: Delete a frontend port.
"""

helps['network application-gateway frontend-port list'] = """
    type: command
    short-summary: List frontend ports.
"""

helps['network application-gateway frontend-port show'] = """
    type: command
    short-summary: Show details of a frontend port.
"""

helps['network application-gateway frontend-port update'] = """
    type: command
    short-summary: Update a frontend port.
"""
#endregion

# region Application Gateway HTTP listener

helps['network application-gateway http-listener'] = """
    type: group
    short-summary: Manage HTTP listeners for an application gateway.
"""

helps['network application-gateway http-listener create'] = """
    type: command
    short-summary: Create an HTTP listener.
"""

helps['network application-gateway http-listener delete'] = """
    type: command
    short-summary: Delete an HTTP listener.
"""

helps['network application-gateway http-listener list'] = """
    type: command
    short-summary: List HTTP listeners.
"""

helps['network application-gateway http-listener show'] = """
    type: command
    short-summary: Show details of an HTTP listener.
"""

helps['network application-gateway http-listener update'] = """
    type: command
    short-summary: Update an HTTP listener.
"""
#endregion

# region Application Gateway HTTP settings

helps['network application-gateway http-settings'] = """
    type: group
    short-summary: Manage HTTP settings for an application gateway.
"""

helps['network application-gateway http-settings create'] = """
    type: command
    short-summary: Create HTTP settings.
"""

helps['network application-gateway http-settings delete'] = """
    type: command
    short-summary: Delete HTTP settings.
"""

helps['network application-gateway http-settings list'] = """
    type: command
    short-summary: List HTTP settings.
"""

helps['network application-gateway http-settings show'] = """
    type: command
    short-summary: Show details of HTTP settings.
"""

helps['network application-gateway http-settings update'] = """
    type: command
    short-summary: Update HTTP settings.
"""
#endregion

# region Application Gateway probe

helps['network application-gateway probe'] = """
    type: group
    short-summary: Use probes to gather information, such as utilization, and then evaluate it by using rules.
"""
helps['network application-gateway probe create'] = """
    type: command
    short-summary: Create a probe.
"""

helps['network application-gateway probe delete'] = """
    type: command
    short-summary: Delete a probe.
"""

helps['network application-gateway probe list'] = """
    type: command
    short-summary: List probes.
"""

helps['network application-gateway probe show'] = """
    type: command
    short-summary: Show details of a probe.
"""

helps['network application-gateway probe update'] = """
    type: command
    short-summary: Update a probe.
"""
#endregion

# region Application Gateway rules

helps['network application-gateway rule'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules.
"""

helps['network application-gateway rule create'] = """
    type: command
    short-summary: Create a rule.
"""

helps['network application-gateway rule delete'] = """
    type: command
    short-summary: Delete a rule.
"""

helps['network application-gateway rule list'] = """
    type: command
    short-summary: List rules.
"""

helps['network application-gateway rule show'] = """
    type: command
    short-summary: Show details of a rule.
"""

helps['network application-gateway rule update'] = """
    type: command
    short-summary: Update a rule.
"""
#endregion

# region Application Gateway SSL Certs

helps['network application-gateway ssl-cert'] = """
    type: group
    short-summary: Manage SSL certificates for an application gateway.
"""
helps['network application-gateway ssl-cert create'] = """
    type: command
    short-summary: Upload an SSL certificate.
"""

helps['network application-gateway ssl-cert delete'] = """
    type: command
    short-summary: Delete an SSL certificate.
"""

helps['network application-gateway ssl-cert list'] = """
    type: command
    short-summary: List SSL certificates.
"""

helps['network application-gateway ssl-cert show'] = """
    type: command
    short-summary: Show details of an SSL certificate.
"""

helps['network application-gateway ssl-cert update'] = """
    type: command
    short-summary: Update an SSL certificate.
"""
#endregion

# region Application Gateway SSL Policy
helps['network application-gateway ssl-policy'] = """
    type: group
    short-summary: Manage the SSL policy for an application gateway.
"""

helps['network application-gateway ssl-policy set'] = """
    type: command
    short-summary: Update or clear SSL policy settings.
"""

helps['network application-gateway ssl-policy show'] = """
    type: command
    short-summary: Show the SSL policy settings.
"""
# endregion

# region Application Gateway URL path map

helps['network application-gateway url-path-map'] = """
    type: group
    short-summary: Manage URL path maps for an application gateway.
"""
helps['network application-gateway url-path-map create'] = """
    type: command
    short-summary: Create a URL path map.
"""

helps['network application-gateway url-path-map delete'] = """
    type: command
    short-summary: Delete a URL path map.
"""

helps['network application-gateway url-path-map list'] = """
    type: command
    short-summary: List URL path maps.
"""

helps['network application-gateway url-path-map show'] = """
    type: command
    short-summary: Show details of a URL path map.
"""

helps['network application-gateway url-path-map update'] = """
    type: command
    short-summary: Update a URL path map.
"""
#endregion

# region Application Gateway URL path map rules

helps['network application-gateway url-path-map rule'] = """
    type: group
    short-summary: Manage the rules for a URL path map.
"""

helps['network application-gateway url-path-map rule create'] = """
    type: command
    short-summary: Create a rule for a URL path map.
"""

helps['network application-gateway url-path-map rule delete'] = """
    type: command
    short-summary: Delete a rule for a URL path map.
"""
#endregion

# region Application Gateway WAF Config
helps['network application-gateway waf-config'] = """
    type: group
    short-summary: Configure the settings of a web application firewall.
    long-summary: This command is only applicable to application gateways with SKU type of WAF.
"""

helps['network application-gateway waf-config set'] = """
    type: command
    short-summary: Update the firewall configuration of a web application.
"""

helps['network application-gateway waf-config show'] = """
    type: command
    short-summary: Show the firewall configuration of a web application.
"""
# endregion

# region DNS record-set

helps['network dns record-set'] = """
    type: group
    short-summary: Manage DNS records and record sets.
"""

# endregion

# region DNS records

for record in ['a', 'aaaa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:
    helps['network dns record-set {}'.format(record)] = """
        type: group
        short-summary: Manage DNS {} records.
    """.format(record.upper())

for record in ['a', 'aaaa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:

    helps['network dns record-set {} remove-record'.format(record)] = """
        type: command
        short-summary: Remove {} record from its record set.
        long-summary: >
            By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
    """.format(record.upper())

    helps['network dns record-set {} create'.format(record)] = """
        type: command
        short-summary: Create an empty {} record set.
    """.format(record.upper())

    helps['network dns record-set {} delete'.format(record)] = """
        type: command
        short-summary: Delete a {} record set and all records within.
    """.format(record.upper())

    helps['network dns record-set {} list'.format(record)] = """
        type: command
        short-summary: List all {} record sets in a zone.
    """.format(record.upper())

    helps['network dns record-set {} show'.format(record)] = """
        type: command
        short-summary: Show details of {} record set.
    """.format(record.upper())

for item in ['a', 'aaaa', 'mx', 'ns', 'ptr', 'srv', 'txt']:

    helps['network dns record-set {} update'.format(record)] = """
        type: command
        short-summary: Update {} record set.
    """.format(record.upper())

    helps['network dns record-set {} add-record'.format(record)] = """
        type: command
        short-summary: Add {} record.
    """.format(record.upper())

helps['network dns record-set cname set-record'] = """
    type: command
    short-summary: Set the value of the CNAME record.
"""

helps['network dns record-set soa'] = """
    type: group
    short-summary: Manage DNS zone SOA record.
"""

helps['network dns record-set soa show'] = """
    type: command
    short-summary: Show details of the DNS zone's SOA record.
"""

helps['network dns record-set soa update'] = """
    type: command
    short-summary: Update properties of the zone's SOA record.
"""


helps['network dns record-set list'] = """
    type: command
    short-summary: List all record sets within a DNS zone.
"""

#endregion

# region DNS Zone
helps['network dns zone'] = """
    type: group
    short-summary: Manage DNS zones.
"""

helps['network dns zone create'] = """
    type: command
    short-summary: Create a DNS zone.
    parameters:
        - name: --if-none-match
          short-summary: Create a DNS zone only if one doesn't exist that matches the given one.
"""

helps['network dns zone delete'] = """
    type: command
    short-summary: Delete a DNS zone and all associated records.
    long-summary: |
        WARNING: This operation cannot be undone.
"""

helps['network dns zone export'] = """
    type: command
    short-summary: Export a DNS zone as a DNS zone file.
"""

helps['network dns zone import'] = """
    type: command
    short-summary: Create a DNS zone using a DNS zone file.
"""

helps['network dns zone list'] = """
    type: command
    short-summary: List DNS zones.
"""

helps['network dns zone show'] = """
    type: command
    short-summary: Get DNS zone parameters. Does not show DNS records within the zone.
"""

helps['network dns zone update'] = """
    type: command
    short-summary: Update DNS zone properties. Does not modify DNS records within the zone.
    parameters:
        - name: --if-match
          short-summary: Update only if the resource with the same ETAG exists.
"""
#endregion

# region Express Route

helps['network express-route'] = """
    type: group
    short-summary: Manage dedicated private network fiber connections to Azure.
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
    short-summary: Show statistics of an ExpressRoute circuit.
"""

helps['network express-route list'] = """
    type: command
    short-summary: List ExpressRoute circuits.
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

helps['network express-route list-service-providers'] = """
    type: command
    short-summary: List available ExpressRoute service providers.
"""
#endregion

# region Express Route auth

helps['network express-route auth'] = """
    type: group
    short-summary: Manage authentication of an ExpressRoute circuit.
"""

helps['network express-route auth create'] = """
    type: command
    short-summary: Create an authorization setting.
"""

helps['network express-route auth delete'] = """
    type: command
    short-summary: Delete an authorization setting.
"""

helps['network express-route auth list'] = """
    type: command
    short-summary: List authorization settings.
"""

helps['network express-route auth show'] = """
    type: command
    short-summary: Show details of an authorization setting.
"""
#endregion

# region Express Route peering

helps['network express-route peering'] = """
    type: group
    short-summary: Manage ExpressRoute peering.
"""

helps['network express-route peering create'] = """
    type: command
    short-summary: Create peering settings.
"""

helps['network express-route peering delete'] = """
    type: command
    short-summary: Delete peering settings.
"""

helps['network express-route peering list'] = """
    type: command
    short-summary: List peering settings.
"""

helps['network express-route peering show'] = """
    type: command
    short-summary: Show peering details.
"""

helps['network express-route peering update'] = """
    type: command
    short-summary: Update peering settings.
"""
#endregion

# region Load Balancer

helps['network lb'] = """
    type: group
    short-summary: Use a load balancer to deliver high availability and network performance to your applications.
"""

helps['network lb create'] = """
    type: command
    short-summary: Create a load balancer.
"""

helps['network lb delete'] = """
    type: command
    short-summary: Delete a load balancer.
"""

helps['network lb list'] = """
    type: command
    short-summary: List load balancers.
"""

helps['network lb show'] = """
    type: command
    short-summary: Show details of a load balancer.
"""

helps['network lb update'] = """
    type: command
    short-summary: Update a load balancer.
"""
#endregion

# region Load Balancer address pool

helps['network lb address-pool'] = """
    type: group
    short-summary: Manage backend address pools for a load balancer.
"""

helps['network lb address-pool create'] = """
    type: command
    short-summary: Create a backend address pool.
"""

helps['network lb address-pool delete'] = """
    type: command
    short-summary: Delete a backend address pool.
"""

helps['network lb address-pool list'] = """
    type: command
    short-summary: List backend address pools.
"""

helps['network lb address-pool show'] = """
    type: command
    short-summary: Show details of a backend address pool.
"""
#endregion

# region Load Balancer frontend IP

helps['network lb frontend-ip'] = """
    type: group
    short-summary: Manage frontend IP addresses for a load balancer. 
"""

helps['network lb frontend-ip create'] = """
    type: command
    short-summary: Create a frontend IP address.
"""

helps['network lb frontend-ip delete'] = """
    type: command
    short-summary: Delete a frontend IP address.
"""

helps['network lb frontend-ip list'] = """
    type: command
    short-summary: List frontend IP addresses.
"""

helps['network lb frontend-ip show'] = """
    type: command
    short-summary: Show details of a frontend IP address.
"""

helps['network lb frontend-ip update'] = """
    type: command
    short-summary: Update a frontend IP address.
"""
#endregion

# region Load Balancer inbound NAT pool

helps['network lb inbound-nat-pool'] = """
    type: group
    short-summary: Manage inbound NAT address pools for a load balancer. 
"""

helps['network lb inbound-nat-pool create'] = """
    type: command
    short-summary: Create an inbound NAT address pool.
"""

helps['network lb inbound-nat-pool delete'] = """
    type: command
    short-summary: Delete an inbound NAT address pool.
"""

helps['network lb inbound-nat-pool list'] = """
    type: command
    short-summary: List inbound NAT address pools.
"""

helps['network lb inbound-nat-pool show'] = """
    type: command
    short-summary: Show details of an inbound NAT address pool.
"""

helps['network lb inbound-nat-pool update'] = """
    type: command
    short-summary: Update an inbound NAT address pool.
"""
#endregion

# region Load Balancer inbound NAT rule

helps['network lb inbound-nat-rule'] = """
    type: group
    short-summary: Manage inbound NAT rules for a load balancer.
"""

helps['network lb inbound-nat-rule create'] = """
    type: command
    short-summary: Create an inbound NAT rule.
"""

helps['network lb inbound-nat-rule delete'] = """
    type: command
    short-summary: Delete an inbound NAT rule.
"""

helps['network lb inbound-nat-rule list'] = """
    type: command
    short-summary: List inbound NAT rules.
"""

helps['network lb inbound-nat-rule show'] = """
    type: command
    short-summary: Show details of an inbound NAT rule.
"""

helps['network lb inbound-nat-rule update'] = """
    type: command
    short-summary: Update an inbound NAT rule.
"""
#endregion

# region Load Balancer probe

helps['network lb probe'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules.
"""

helps['network lb probe create'] = """
    type: command
    short-summary: Create a probe.
"""

helps['network lb probe delete'] = """
    type: command
    short-summary: Delete a probe.
"""

helps['network lb probe list'] = """
    type: command
    short-summary: List probes.
"""

helps['network lb probe show'] = """
    type: command
    short-summary: Show details of a probe.
"""

helps['network lb probe update'] = """
    type: command
    short-summary: Update a probe.
"""
#endregion

# region Load Balancer rule

helps['network lb rule'] = """
    type: group
    short-summary: Manage load balancing rules.
"""

helps['network lb rule create'] = """
    type: command
    short-summary: Create a load balancing rule.
"""

helps['network lb rule delete'] = """
    type: command
    short-summary: Delete a load balancing rule.
"""

helps['network lb rule list'] = """
    type: command
    short-summary: List load balancing rules.
"""

helps['network lb rule show'] = """
    type: command
    short-summary: Show details of a load balancing rule.
"""

helps['network lb rule update'] = """
    type: command
    short-summary: Update a load balancing rule.
"""
#endregion

# region Local Gateway

helps['network local-gateway'] = """
    type: group
    short-summary: Manage local gateways.
"""

helps['network local-gateway create'] = """
    type: command
    short-summary: Create a local VPN gateway.
"""

helps['network local-gateway delete'] = """
    type: command
    short-summary: Delete a local VPN gateway.
"""
helps['network local-gateway list'] = """
    type: command
    short-summary: List local VPN gateways.
"""
helps['network local-gateway show'] = """
    type: command
    short-summary: Show details of a local VPN gateway.
"""

helps['network local-gateway update'] = """
    type: command
    short-summary: Update a local VPN gateway.
"""
#endregion

# region Network Interface (NIC)

helps['network nic'] = """
    type: group
    short-summary: Manage network interfaces.
"""

helps['network nic show-effective-route-table'] = """
    type: command
    short-summary: Show all route tables applied to a network interface.
"""

helps['network nic list-effective-nsg'] = """
    type: command
    short-summary: List all network security groups applied to a network interface.
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
    short-summary: List network interfaces.
    long-summary: |
        Does not list network interfaces attached to VMs in VM scale sets. Use 'az vmss nic list' or 'az vmss nic list-vm-nics' to display that information.
"""

helps['network nic show'] = """
    type: command
    short-summary: Show details of a network interface.
"""

helps['network nic update'] = """
    type: command
    short-summary: Update a network interface.
"""
#endregion

# region NIC ip-config

helps['network nic ip-config'] = """
    type: group
    short-summary: Manage IP configurations of a network interface.
"""

helps['network nic ip-config create'] = """
    type: command
    short-summary: Create an IP configuration.
    long-summary: You must have the Microsoft.Network/AllowMultipleIpConfigurationsPerNic feature enabled for your subscription. Only one configuration may be designated as the primary IP configuration per NIC, using the --make-primary flag.
"""

helps['network nic ip-config delete'] = """
    type: command
    short-summary: Delete an IP configuration.
    long-summary: A NIC must have at least one IP configuration.
"""

helps['network nic ip-config list'] = """
    type: command
    short-summary: List IP configurations.
"""

helps['network nic ip-config show'] = """
    type: command
    short-summary: Show details of an IP configuration.
"""

helps['network nic ip-config update'] = """
    type: command
    short-summary: Update an IP configuration.
"""
#endregion

# region NIC IP config address pool

helps['network nic ip-config address-pool'] = """
    type: group
    short-summary: Manage backend address pools in an IP configuration.
"""

helps['network nic ip-config address-pool add'] = """
    type: command
    short-summary: Add a backend address pool.
"""

helps['network nic ip-config address-pool remove'] = """
    type: command
    short-summary: Remove a backend address pool.
"""
#endregion

# region NIC IP config inbound NAT rules

helps['network nic ip-config inbound-nat-rule'] = """
    type: group
    short-summary: Manage inbound NAT rules for an IP configuration.
"""

helps['network nic ip-config inbound-nat-rule add'] = """
    type: command
    short-summary: Add an inbound NAT rule.
"""

helps['network nic ip-config inbound-nat-rule remove'] = """
    type: command
    short-summary: Remove an inbound NAT rule.
"""
#endregion

# region Network Security Group (NSG)

helps['network nsg'] = """
    type: group
    short-summary: Manage Azure Network Security Groups.
"""

helps['network nsg rule'] = """
    type: group
    short-summary: Manage NSG rules.
"""

helps['network nsg rule create'] = """
    type: command
    short-summary: Create an NSG rule.
"""

helps['network nsg rule delete'] = """
    type: command
    short-summary: Delete an NSG rule.
"""

helps['network nsg rule list'] = """
    type: command
    short-summary: List all rules in an NSG.
"""

helps['network nsg rule show'] = """
    type: command
    short-summary: Show details of an NSG rule.
"""

helps['network nsg rule update'] = """
    type: command
    short-summary: Update an NSG rule.
"""


#endregion

# region Public IP

helps['network public-ip'] = """
    type: group
    short-summary: Manage public IP addresses.
"""

helps['network public-ip create'] = """
    type: command
    short-summary: Create a public IP address.
"""

helps['network public-ip delete'] = """
    type: command
    short-summary: Delete a public IP address.
"""

helps['network public-ip list'] = """
    type: command
    short-summary: List public IP addresses.
"""

helps['network public-ip show'] = """
    type: command
    short-summary: Show details of a public IP address.
"""

helps['network public-ip update'] = """
    type: command
    short-summary: Update a public IP address.
"""
#endregion

# region Route Table

helps['network route-table'] = """
    type: group
    short-summary: Manage route tables.
"""

helps['network route-table create'] = """
    type: command
    short-summary: Create a route table.
"""

helps['network route-table delete'] = """
    type: command
    short-summary: Delete a route table.
"""

helps['network route-table list'] = """
    type: command
    short-summary: List route tables.
"""

helps['network route-table show'] = """
    type: command
    short-summary: Show details of a route table.
"""

helps['network route-table update'] = """
    type: command
    short-summary: Update a route table.
"""

helps['network route-table route'] = """
    type: group
    short-summary: Manage routes in a route table.
"""

helps['network route-table route create'] = """
    type: command
    short-summary: Create a route in a route table.
"""

helps['network route-table route delete'] = """
    type: command
    short-summary: Delete a route from a route table.
"""

helps['network route-table route list'] = """
    type: command
    short-summary: List routes in a route table.
"""

helps['network route-table route show'] = """
    type: command
    short-summary: Show details of a route in a route table.
"""

helps['network route-table route update'] = """
    type: command
    short-summary: Update a route in a route table.
"""

#endregion

# region Traffic Manager

helps['network traffic-manager'] = """
    type: group
    short-summary: Route incoming traffic for high performance and availability.
"""

helps['network traffic-manager endpoint'] = """
    type: group
    short-summary: Manage Traffic Manager end points.
"""

helps['network traffic-manager profile'] = """
    type: group
    short-summary: Manage Traffic Manager profiles.
"""

helps['network traffic-manager profile check-dns'] = """
    type: command
    short-summary: Check the availability of a relative DNS name.
"""

helps['network traffic-manager profile create'] = """
    type: command
    short-summary: Create a profile.
"""

helps['network traffic-manager profile delete'] = """
    type: command
    short-summary: Delete a profile.
"""

helps['network traffic-manager profile list'] = """
    type: command
    short-summary: List profiles.
"""

helps['network traffic-manager profile show'] = """
    type: command
    short-summary: Show details of a profile.
"""

helps['network traffic-manager profile update'] = """
    type: command
    short-summary: Update a profile.
"""

helps['network traffic-manager endpoint create'] = """
    type: command
    short-summary: Create an endpoint.
"""

helps['network traffic-manager endpoint delete'] = """
    type: command
    short-summary: Delete an endpoint.
"""

helps['network traffic-manager endpoint list'] = """
    type: command
    short-summary: List endpoints.
"""

helps['network traffic-manager endpoint show'] = """
    type: command
    short-summary: Show details of an endpoint.
"""

helps['network traffic-manager endpoint update'] = """
    type: command
    short-summary: Update an endpoint.
"""
#endregion

# region Virtual Network (VNET)

helps['network vnet'] = """
    type: group
    short-summary: Manage Azure Virtual Networks.
"""

helps['network vnet check-ip-address'] = """
    type: command
    short-summary: Check whether a private IP address is available for use.
"""

helps['network vnet create'] = """
    type: command
    short-summary: Create a virtual network.
    long-summary: You may also create a subnet at the same time by specifying a subnet name and (optionally) an address prefix.
"""

helps['network vnet delete'] = """
    type: command
    short-summary: Delete a virtual network.
"""

helps['network vnet list'] = """
    type: command
    short-summary: List virtual networks.
"""

helps['network vnet show'] = """
    type: command
    short-summary: Show details on a virtual network.
"""

helps['network vnet update'] = """
    type: command
    short-summary: Update a virtual network.
"""
#endregion

# region VNet Subnet

helps['network vnet subnet'] = """
    type: group
    short-summary: Manage subnets in an Azure Virtual Network.
"""

helps['network vnet subnet create'] = """
    type: command
    short-summary: Create a subnet.
"""

helps['network vnet subnet delete'] = """
    type: command
    short-summary: Delete a subnet.
"""

helps['network vnet subnet list'] = """
    type: command
    short-summary: List subnets.
"""

helps['network vnet subnet show'] = """
    type: command
    short-summary: Show details of a subnet.
"""

helps['network vnet subnet update'] = """
    type: command
    short-summary: Update a subnet.
"""
#endregion

# region Virtual Network (VNet) Peering

helps['network vnet peering'] = """
    type: group
    short-summary: Manage peering connections between Azure Virtual Networks.
"""

helps['network vnet peering create'] = """
    type: command
    short-summary: Create a peering.
"""

helps['network vnet peering delete'] = """
    type: command
    short-summary: Delete a peering.
"""

helps['network vnet peering list'] = """
    type: command
    short-summary: List peerings.
"""

helps['network vnet peering show'] = """
    type: command
    short-summary: Show details of a peering.
"""

helps['network vnet peering update'] = """
    type: command
    short-summary: Update a peering.
"""
#endregion

# region VPN Connection

helps['network vpn-connection'] = """
    type: group
    short-summary: Manage VPN connections.
"""

helps['network vpn-connection create'] = """
    type: command
    short-summary: Create a VPN connection.
"""

helps['network vpn-connection delete'] = """
    type: command
    short-summary: Delete a VPN connection.
"""

helps['network vpn-connection list'] = """
    type: command
    short-summary: List VPN connections.
"""

helps['network vpn-connection show'] = """
    type: command
    short-summary: Show details of a VPN connection.
"""

helps['network vpn-connection update'] = """
    type: command
    short-summary: Update a VPN connection.
"""

#endregion

# region VPN Connection shared key

helps['network vpn-connection shared-key'] = """
    type: group
    short-summary: Manage VPN shared keys.
"""

helps['network vpn-connection shared-key reset'] = """
    type: command
    short-summary: Reset a VPN connection shared key.
"""

helps['network vpn-connection shared-key show'] = """
    type: command
    short-summary: Show a VPN connection shared key.
"""

helps['network vpn-connection shared-key update'] = """
    type: command
    short-summary: Update a VPN connection shared key.
"""

#endregion

# region VNet Gateway

helps['network vnet-gateway'] = """
    type: group
    short-summary: Use an Azure Virtual Network Gateway to establish secure, cross-premises connectivity.
"""

helps['network vnet-gateway create'] = """
    type: command
    short-summary: Create a virtual network gateway.
"""

helps['network vnet-gateway create'] = """
    type: command
    short-summary: Create a virtual network gateway.
"""

helps['network vnet-gateway delete'] = """
    type: command
    short-summary: Delete a virtual network gateway.
"""

helps['network vnet-gateway list'] = """
    type: command
    short-summary: List virtual network gateways.
"""

helps['network vnet-gateway reset'] = """
    type: command
    short-summary: Reset a virtual network gateway.
"""

helps['network vnet-gateway show'] = """
    type: command
    short-summary: Show details of a virtual network gateway.
"""

helps['network vnet-gateway update'] = """
    type: command
    short-summary: Update a virtual network gateway.
"""
#endregion

# region VNet Gateway Revoke Cert

helps['network vnet-gateway revoked-cert'] = """
    type: group
    short-summary: Manage revoked certificates in a virtual network gateway.
"""

helps['network vnet-gateway revoked-cert create'] = """
    type: command
    short-summary: Revoke a certificate.
"""

helps['network vnet-gateway revoked-cert delete'] = """
    type: command
    short-summary: Delete a revoked certificate.
"""

#endregion

# region VNet Gateway Root Cert
helps['network vnet-gateway root-cert'] = """
    type: group
    short-summary: Manage root certificates for a virtuak network gateway.
"""

helps['network vnet-gateway root-cert create'] = """
    type: command
    short-summary: Upload a root certificate.
"""

helps['network vnet-gateway root-cert delete'] = """
    type: command
    short-summary: Delete a root certificate.
"""

#endregion
