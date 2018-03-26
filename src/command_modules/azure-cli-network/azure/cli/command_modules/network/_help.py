# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['network'] = """
    type: group
    short-summary: Manage Azure Network resources.
"""

helps['network list-usages'] = """
    type: command
    short-summary: List the number of network resources in a region that are used against a subscription quota.
"""

helps['network dns'] = """
    type: group
    short-summary: Manage DNS domains in Azure.
"""

# region Application Gateway
helps['network application-gateway'] = """
    type: group
    short-summary: Manage application-level routing and load balancing services.
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
    short-summary: Get the details of an application gateway.
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
    short-summary: Get information on the backend health of an application gateway.
"""

helps['network application-gateway wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the application gateway is met.
"""
# endregion

# region Application Gateway Address Pool
helps['network application-gateway address-pool'] = """
    type: group
    short-summary: Manage backend address pools for an application gateway.
"""

helps['network application-gateway address-pool create'] = """
    type: command
    short-summary: Create a backend address pool.
    examples:
        - name: Create an address pool with two endpoints.
          text: |
            az network application-gateway address-pool create \\
                -g MyResourceGroup --gateway-name MyApplicationGateway \\
                -n MyAddressPool --servers 10.0.0.4 10.0.0.5
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
    short-summary: Get the details for a backend address pool.
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
    short-summary: Get the details of an authorization certificate.
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
    short-summary: Get the details of a frontend IP address.
"""

helps['network application-gateway frontend-ip update'] = """
    type: command
    short-summary: Update a frontend IP address.
"""
# endregion

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
    short-summary: Get the details for a frontend port.
"""

helps['network application-gateway frontend-port update'] = """
    type: command
    short-summary: Update a frontend port.
"""
# endregion

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
    short-summary: Get the details for an HTTP listener.
"""

helps['network application-gateway http-listener update'] = """
    type: command
    short-summary: Update an HTTP listener.
"""
# endregion

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
    short-summary: Get the details of a gateway's HTTP settings.
"""

helps['network application-gateway http-settings update'] = """
    type: command
    short-summary: Update HTTP settings.
"""
# endregion

# region Application Gateway probe
helps['network application-gateway probe'] = """
    type: group
    short-summary: Manage probes to gather and evaluate information on a gateway.
"""
helps['network application-gateway probe create'] = """
    type: command
    short-summary: Create a probe.
    examples:
        - name: Create an application gateway probe.
          text: >
            az network application-gateway probe create -g MyResourceGroup -n MyProbe \\
                    --protocol https --gateway-name MyApplicationGateway \\
                    --host 127.0.0.1 --path /path/to/probe
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
    short-summary: Get the details of a probe.
"""

helps['network application-gateway probe update'] = """
    type: command
    short-summary: Update a probe.
"""
# endregion

# region Application Gateway redirect configuration
helps['network application-gateway redirect-config'] = """
    type: group
    short-summary: Manage redirect configurations.
"""

helps['network application-gateway redirect-config create'] = """
    type: command
    short-summary: Create a redirect configuration.
"""

helps['network application-gateway redirect-config delete'] = """
    type: command
    short-summary: Delete a redirect configuration.
"""

helps['network application-gateway redirect-config list'] = """
    type: command
    short-summary: List redirect configurations.
"""

helps['network application-gateway redirect-config show'] = """
    type: command
    short-summary: Get the details of a redirect configuration.
"""

helps['network application-gateway redirect-config update'] = """
    type: command
    short-summary: Update a redirect configuration.
"""

# endregion

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
    short-summary: Get the details of a rule.
"""

helps['network application-gateway rule update'] = """
    type: command
    short-summary: Update a rule.
"""
# endregion

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
    short-summary: Get the details of an SSL certificate.
"""

helps['network application-gateway ssl-cert update'] = """
    type: command
    short-summary: Update an SSL certificate.
"""
# endregion

# region Application Gateway SSL Policy
helps['network application-gateway ssl-policy'] = """
    type: group
    short-summary: Manage the SSL policy for an application gateway.
"""

helps['network application-gateway ssl-policy set'] = """
    type: command
    short-summary: Update or clear SSL policy settings.
    parameters:
        - name: --cipher-suites
          populator-commands:
            - az network application-gateway ssl-policy list-options
        - name: --disabled-ssl-protocols
          populator-commands:
            - az network application-gateway ssl-policy list-options
        - name: --min-protocol-version
          populator-commands:
            - az network application-gateway ssl-policy list-options
"""

helps['network application-gateway ssl-policy show'] = """
    type: command
    short-summary: Get the details of a gateway's SSL policy settings.
"""

helps['network application-gateway ssl-policy predefined'] = """
    type: group
    short-summary: Get information on predefined SSL policies.
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
    long-summary: >
        The map must be created with at least one rule. This command requires the creation of the
        first rule at the time the map is created. To create additional rules using different
        address pools or HTTP settings, use the `url-path-map rule create` command. To update the
        rule created using this command, use the `url-path-map rule update` command.
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
    short-summary: Get the details of a URL path map.
"""

helps['network application-gateway url-path-map update'] = """
    type: command
    short-summary: Update a URL path map.
"""
# endregion

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
# endregion

# region Application Gateway WAF Config
helps['network application-gateway waf-config'] = """
    type: group
    short-summary: Configure the settings of a web application firewall.
    long-summary: This command is only applicable to application gateways with an SKU type of WAF.
"""

helps['network application-gateway waf-config set'] = """
    type: command
    short-summary: Update the firewall configuration of a web application.
    parameters:
        - name: --rule-set-type
          short-summary: Rule set type.
          populator-commands:
          - az network application-gateway waf-config list-rule-sets
        - name: --rule-set-version
          short-summary: Rule set version.
          populator-commands:
          - az network application-gateway waf-config list-rule-sets
        - name: --disabled-rule-groups
          short-summary: Space-separated list of rule groups to disable. To disable individual rules, use `--disabled-rules`.
          populator-commands:
          - az network application-gateway waf-config list-rule-sets
        - name: --disabled-rules
          short-summary: Space-separated list of rule IDs to disable.
          populator-commands:
          - az network application-gateway waf-config list-rule-sets
    examples:
        - name: Disable rules for validation of request body parsing and SQL injection.
          text: |
            az network application-gateway waf-config set -g MyResourceGroup -n MyGatewayName \\
                    --enabled true --rule-set-type OWASP --rule-set-version 3.0 \\
                    --disabled-rules 920130 920140 \\
                    --disabled-rule-groups REQUEST-942-APPLICATION-ATTACK-SQLI
"""

helps['network application-gateway waf-config show'] = """
    type: command
    short-summary: Get the firewall configuration of a web application.
"""

helps['network application-gateway waf-config list-rule-sets'] = """
    type: command
    short-summary: (PREVIEW) Get information on available WAF rule sets, rule groups, and rule IDs.
    parameters:
        - name: --group
          short-summary: >
            List rules for the specified rule group. Use '*' to list rules for all groups.
            Omit to suppress listing individual rules.
        - name: --type
          short-summary: Rule set type to list. Omit to list all types.
        - name: --version
          short-summary: Rule set version to list. Omit to list all versions.
    examples:
        - name: List available rule groups in OWASP type rule sets.
          text: >
            az network application-gateway waf-config list-rule-sets --type OWASP
        - name: List available rules in the OWASP 3.0 rule set.
          text: >
            az network application-gateway waf-config list-rule-sets --group '*' --type OWASP --version 3.0
        - name: List available rules in the 'crs_35_bad_robots' rule group.
          text: >
            az network application-gateway waf-config list-rule-sets --group crs_35_bad_robots
"""

# endregion

# region DNS record-set
helps['network dns record-set'] = """
    type: group
    short-summary: Manage DNS records and record sets.
"""

# endregion

# region DNS records
dns_record_types = ['a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']

for record in dns_record_types:
    helps['network dns record-set {}'.format(record)] = """
        type: group
        short-summary: Manage DNS {} records.
    """.format(record.upper())

for record in dns_record_types:
    indef_article = 'an' if record.startswith('a') else 'a'

    helps['network dns record-set {0} remove-record'.format(record)] = """
        type: command
        short-summary: Remove {1} {0} record from its record set.
        long-summary: >
            By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
    """.format(record.upper(), indef_article)

    helps['network dns record-set {} create'.format(record)] = """
        type: command
        short-summary: Create an empty {} record set.
    """.format(record.upper())

    helps['network dns record-set {} delete'.format(record)] = """
        type: command
        short-summary: Delete {1} {0} record set and all associated records.
    """.format(record.upper(), indef_article)

    helps['network dns record-set {} list'.format(record)] = """
        type: command
        short-summary: List all {} record sets in a zone.
    """.format(record.upper())

    helps['network dns record-set {} show'.format(record)] = """
        type: command
        short-summary: Get the details for {1} {0} record set.
        examples:
        - name: Show information about {1} {0} record set.
          text: >
            az network dns record-set {2} show -g MyResourceGroup -n MyRecordSet -z www.mysite.com
    """.format(record.upper(), indef_article, record)

for record in [r for r in dns_record_types if r != 'cname']:
    indef_article = 'an' if record.startswith('a') else 'a'

    helps['network dns record-set {} update'.format(record)] = """
        type: command
        short-summary: Update {} {} record set.
    """.format(indef_article, record.upper())

    helps['network dns record-set {} add-record'.format(record)] = """
        type: command
        short-summary: Add {} {} record.
    """.format(indef_article, record.upper())

helps['network dns record-set cname set-record'] = """
    type: command
    short-summary: Set the value of the CNAME record.
"""

helps['network dns record-set soa'] = """
    type: group
    short-summary: Manage a DNS zone's SOA record.
"""

helps['network dns record-set soa show'] = """
    type: command
    short-summary: Get the details of a DNS zone's SOA record.
"""

helps['network dns record-set soa update'] = """
    type: command
    short-summary: Update properties of a zone's SOA record.
"""

helps['network dns record-set list'] = """
    type: command
    short-summary: List all record sets within a DNS zone.
    examples:
        - name: List all "@" record sets within this zone.
          text: >
            az network dns record-set list -g MyResourceGroup -z www.mysite.com --query "[?name=='@']"
"""

# endregion

# region Application Security Group
helps['network asg'] = """
    type: group
    short-summary: Manage application security groups (ASGs).
    long-summary: >
        You can configure network security as a natural extension of an application's structure, ASG allows
        you to group virtual machines and define network security policies based on those groups. You can specify an
        application security group as the source and destination in a NSG security rule. For more information
        visit https://docs.microsoft.com/en-us/azure/virtual-network/create-network-security-group-preview
"""

helps['network asg create'] = """
    type: command
    short-summary: Create an application security group.
    long-summary: >
        You can configure network security as a natural extension of an application's structure, ASG
        allows you to group virtual machines and define network security policies based on those groups. You can
        specify an application security group as the source and destination in a NSG security rule. For more
        information visit https://docs.microsoft.com/en-us/azure/virtual-network/create-network-security-group-preview
    parameters:
        - name: --name -n
          short-summary: Name of the new application security group resource.
    examples:
        - name: Create a typical ASG
          text: >
            az network asg create -g MyGroup -n MyAppSecGroup
"""

helps['network asg delete'] = """
    type: command
    short-summary: Delete an application security group.
"""

helps['network asg list'] = """
    type: command
    short-summary: List application security groups.
"""

helps['network asg show'] = """
    type: command
    short-summary: Get details of an application security group.
"""

helps['network asg update'] = """
    type: command
    short-summary: Update an application security group.
"""

# endregion

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
          short-summary: Only create a DNS zone if one doesn't exist that matches the given name.
    examples:
        - name: Create a DNS zone using a fully qualified domain name.
          text: >
            az network dns zone create -g MyResourceGroup -n www.mysite.com
"""

helps['network dns zone delete'] = """
    type: command
    short-summary: Delete a DNS zone and all associated records.
"""

helps['network dns zone export'] = """
    type: command
    short-summary: Export a DNS zone as a DNS zone file.
"""

helps['network dns zone import'] = """
    type: command
    short-summary: Create a DNS zone using a DNS zone file.
    examples:
        - name: Import a local zone file into a DNS zone resource.
          text: >
            az network dns zone import -g MyResourceGroup -n MyZone -f /path/to/zone/file
"""

helps['network dns zone list'] = """
    type: command
    short-summary: List DNS zones.
"""

helps['network dns zone show'] = """
    type: command
    short-summary: Get a DNS zone's parameters. Does not show DNS records within the zone.
"""

helps['network dns zone update'] = """
    type: command
    short-summary: Update a DNS zone's properties. Does not modify DNS records within the zone.
    parameters:
        - name: --if-match
          short-summary: Update only if the resource with the same ETAG exists.
"""
# endregion

# region Express Route
helps['network express-route'] = """
    type: group
    short-summary: Manage dedicated private network fiber connections to Azure.
"""

helps['network express-route create'] = """
    type: command
    short-summary: Create an ExpressRoute circuit.
    parameters:
        - name: --bandwidth
          populator-commands:
          - az network express-route list-service-providers
        - name: --peering-location
          populator-commands:
          - az network express-route list-service-providers
        - name: --provider
          populator-commands:
          - az network express-route list-service-providers
"""

helps['network express-route delete'] = """
    type: command
    short-summary: Delete an ExpressRoute circuit.
"""

helps['network express-route get-stats'] = """
    type: command
    short-summary: Get the statistics for an ExpressRoute circuit.
"""

helps['network express-route list'] = """
    type: command
    short-summary: List ExpressRoute circuits.
"""

helps['network express-route list-arp-tables'] = """
    type: command
    short-summary: List the currently advertised address resolution protocol (ARP) table of an ExpressRoute circuit.
"""

helps['network express-route list-route-tables'] = """
    type: command
    short-summary: List the currently advertised route tables of an ExpressRoute circuit.
"""

helps['network express-route show'] = """
    type: command
    short-summary: Get the details for an ExpressRoute circuit.
"""

helps['network express-route update'] = """
    type: command
    short-summary: Update settings of an ExpressRoute circuit.
"""

helps['network express-route list-service-providers'] = """
    type: command
    short-summary: List available ExpressRoute service providers.
"""

helps['network express-route wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the ExpressRoute is met.
"""

# endregion

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
    short-summary: Get the details of an authorization setting.
"""
# endregion

# region Express Route peering
helps['network express-route peering'] = """
    type: group
    short-summary: Manage ExpressRoute peering.
"""

helps['network express-route peering create'] = """
    type: command
    short-summary: Create peering settings.
    examples:
        - name: Create Microsoft Peering settings with IPv4 configuration.
          text: |
            az network express-route peering create -g MyResourceGroup \\
                --circuit-name MyCircuit --peering-type MicrosoftPeering --peer-asn 10002 \\
                --vlan-id 103 --primary-peer-subnet 101.0.0.0/30 \\
                --secondary-peer-subnet 102.0.0.0/30 --advertised-public-prefixes 101.0.0.0/30
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
    short-summary: Get the details for an express route peering.
"""

helps['network express-route peering update'] = """
    type: command
    short-summary: Update peering settings.
    examples:
        - name: Add IPv6 Microsoft Peering settings to existing IPv4 config.
          text: |
            az network express-route peering update -g MyResourceGroup \\
                --circuit-name MyCircuit --peering-type MicrosoftPeering --ip-version ipv6 \\
                --primary-peer-subnet 2002:db00::/126 --secondary-peer-subnet 2003:db00::/126 \\
                --advertised-public-prefixes 2002:db00::/126
          min_profile: latest
"""
# endregion

# region Load Balancer
helps['network lb'] = """
    type: group
    short-summary: Manage and configure load balancers.
"""

helps['network lb create'] = """
    type: command
    short-summary: Create a load balancer.
    examples:
        - name: Create a basic load balancer.
          text: >
            az network lb create -g MyResourceGroup -n MyLb
        - name: Create a load balancer on a specific virtual network and subnet.
          text: >
            az network lb create -g MyResourceGroup -n MyLb --vnet-name MyVnet --subnet MySubnet
        - name: Create a zone flavored public facing load balancer through provisioning a zonal public ip.
          text: >
            az network lb create -g MyResourceGroup -n MyLB --public-ip-zone 2
        - name: Create a zone flavored internal facing load balancer through provisioning a zonal frontend ip configuration.
          text: >
            az network lb create -g MyResourceGroup -n MyLB --frontend-ip-zone 1 -vnet-name MyVnet --subnet MySubnet
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
    short-summary: Get the details for a load balancer.
"""

helps['network lb update'] = """
    type: command
    short-summary: Update a load balancer.
"""
# endregion

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
    short-summary: Get the details for a backend address pool.
"""
# endregion

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
    short-summary: Get the details of a frontend IP address.
"""

helps['network lb frontend-ip update'] = """
    type: command
    short-summary: Update a frontend IP address.
"""
# endregion

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
    short-summary: Get the details for an inbound NAT address pool.
"""

helps['network lb inbound-nat-pool update'] = """
    type: command
    short-summary: Update an inbound NAT address pool.
"""
# endregion

# region Load Balancer inbound NAT rule
helps['network lb inbound-nat-rule'] = """
    type: group
    short-summary: Manage inbound NAT rules for a load balancer.
"""

helps['network lb inbound-nat-rule create'] = """
    type: command
    short-summary: Create an inbound NAT rule.
    examples:
        - name: Create a basic inbound NAT rule for port 80.
          text: |
            az network lb inbound-nat-rule create -g MyResourceGroup --lb-name MyLb -n MyNatRule \\
                --protocol Tcp --frontend-port 80 --backend-port 80
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
    short-summary: Get the details for an inbound NAT rule.
"""

helps['network lb inbound-nat-rule update'] = """
    type: command
    short-summary: Update an inbound NAT rule.
"""
# endregion

# region Load Balancer probe
helps['network lb probe'] = """
    type: group
    short-summary: Evaluate probe information and define routing rules.
"""

helps['network lb probe create'] = """
    type: command
    short-summary: Create a probe.
    examples:
        - name: Create a probe on a load balancer over HTTP and port 80.
          text: |
            az network lb probe create -g MyResourceGroup --lb-name MyLb -n MyProbe \\
                --protocol http --port 80 --path /
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
    short-summary: Get the details for a probe.
"""

helps['network lb probe update'] = """
    type: command
    short-summary: Update a probe.
"""
# endregion

# region Load Balancer rule
helps['network lb rule'] = """
    type: group
    short-summary: Manage load balancing rules.
"""

helps['network lb rule create'] = """
    type: command
    short-summary: Create a load balancing rule.
    examples:
        - name: >
            Create a basic load balancing rule that assigns a front-facing IP
            configuration and port to a backend address pool and port.
          text: |
            az network lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule \\
                --protocol Tcp --frontend-port 80 --backend-port 80
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
    short-summary: Get the details of a load balancing rule.
"""

helps['network lb rule update'] = """
    type: command
    short-summary: Update a load balancing rule.
"""
# endregion

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
    short-summary: Get the details for a local VPN gateway.
"""

helps['network local-gateway update'] = """
    type: command
    short-summary: Update a local VPN gateway.
"""
# endregion

# region Network Interface (NIC)
helps['network nic'] = """
    type: group
    short-summary: Manage network interfaces.
    long-summary: >
        To learn more about network interfaces in Azure visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface
"""

helps['network nic show-effective-route-table'] = """
    type: command
    short-summary: Show the effective route table applied to a network interface.
    long-summary: >
        To learn more about how to troubleshoot using effective route tables visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-routes-troubleshoot-portal#using-effective-routes-to-troubleshoot-vm-traffic-flow
    examples:
        - name: Show effective routes applied to a network interface.
          text: az network nic show-effective-route-table -n MyNic -g MyResourceGroup
"""

helps['network nic list-effective-nsg'] = """
    type: command
    short-summary: List all effective network security groups applied to a network interface.
    long-summary: >
        To learn more about how to troubleshoot using effective security rules visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-nsg-troubleshoot-portal
    examples:
        - name: List the effective security groups associated with a NIC.
          text: az network nic list-effective-nsg -n MyNic -g MyResourceGroup
"""

helps['network nic create'] = """
    type: command
    short-summary: Create a network interface.
    long-summary: To learn more about network interfaces in Azure visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface
    examples:
        - name: Create a network interface for a specified subnet on a specified virtual network.
          text: >
            az network nic create -g MyResourceGroup --vnet-name MyVnet --subnet MySubnet -n MyNic
        - name: >
            Create a network interface for a specified subnet on a virtual network which allows
                IP forwarding subject to a network security group.
          text: |
            az network nic create -g MyResourceGroup --vnet-name MyVnet --subnet MySubnet -n MyNic \\
                --ip-forwarding --network-security-group MyNsg
        - name: >
            Create a network interface for a specified subnet on a virtual network with network security group and application security groups.
          text: |
            az network nic create -g MyResourceGroup --vnet-name MyVnet \\
                --subnet MySubnet -n MyNic --network-security-group MyNsg \\
                --network-security-group MyNsg --application-security-groups Web App
"""

helps['network nic delete'] = """
    type: command
    short-summary: Delete a network interface.
"""

helps['network nic list'] = """
    type: command
    short-summary: List network interfaces.
    long-summary: >
        Does not list network interfaces attached to VMs in VM scale sets. Use 'az vmss nic list' or 'az vmss nic list-vm-nics' to display that information.
        To learn more about network interfaces in Azure visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface
    examples:
        - name: List all NICs by internal DNS suffix.
          text: >
            az network nic list --query "[?dnsSettings.internalDomainNameSuffix==`<dns_suffix>`]"
"""

helps['network nic show'] = """
    type: command
    short-summary: Get the details of a network interface.
    long-summary: >
        To learn more about network interfaces in Azure visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface
    examples:
        - name: Get the internal domain name suffix for a NIC.
          text: az network nic show -g MyResourceGroup -n MyNic --query "dnsSettings.internalDomainNameSuffix"
"""

helps['network nic update'] = """
    type: command
    short-summary: Update a network interface.
    long-summary: >
        To learn more about network interfaces in Azure visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface
    examples:
        - name: Update a network interface to use a different network security group.
          text: az network nic update -g MyResourceGroup -n MyNic --network-security-group MyNsg
"""
# endregion

# region NIC ip-config
helps['network nic ip-config'] = """
    type: group
    short-summary: Manage IP configurations of a network interface.
"""

helps['network nic ip-config create'] = """
    type: command
    short-summary: Create an IP configuration.
    long-summary: >
        You must have the Microsoft.Network/AllowMultipleIpConfigurationsPerNic feature enabled for your subscription.
        Only one configuration may be designated as the primary IP configuration per NIC, using the `--make-primary` flag.
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
    short-summary: Get the details of an IP configuration.
"""

helps['network nic ip-config update'] = """
    type: command
    short-summary: Update an IP configuration.
    examples:
        - name: Update a NIC to use a new private IP address.
          text: >
            az network nic ip-config update -g MyResourceGroup --nic-name MyNic -n MyIpConfig --private-ip-address 10.0.0.9
        - name: Make an IP configuration the default for the supplied NIC.
          text: >
            az network nic ip-config update -g MyResourceGroup --nic-name MyNic -n MyIpConfig --make-primary
"""
# endregion

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
# endregion

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
# endregion

# region Network Security Group (NSG)
helps['network nsg'] = """
    type: group
    short-summary: Manage Azure Network Security Groups (NSGs).
    long-summary: >
      Network traffic to resources in Azure are controlled by NSGs. An NSG contains a list of security rules that
      determine allowed inbound and outbound traffic based on IP, Application Security Groups, ports, and protocols.
      For more information visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-networks-nsg
"""

helps['network nsg rule'] = """
    type: group
    short-summary: Manage network security group rules.
"""

helps['network nsg create'] = """
    type: command
    short-summary: Create a network security group.
    examples:
        - name: Create an NSG with some tags.
          text: >
            az network nsg create -g MyResourceGroup -n MyNsg --tags super_secure no_80 no_22
"""

helps['network nsg list'] = """
    type: command
    short-summary: List network security groups.
    examples:
        - name: List all NSGs in the 'westus' region.
          text: >
            az network nsg list --query "[?location=='westus']"
"""

helps['network nsg show'] = """
    type: command
    short-summary: Get information about a network security group.
    examples:
        - name: Get basic information about an NSG.
          text: >
            az network nsg show -g MyResourceGroup -n MyNsg
        - name: Get basic information about all default NSG rules with "Allow" access.
          text: >
            az network nsg show -g MyResourceGroup -n MyNsg --query "defaultSecurityRules[?access=='Allow']"
"""

helps['network nsg rule create'] = """
    type: command
    short-summary: Create a network security group rule.
    examples:
        - name: Create a basic "Allow" NSG rule with the highest priority.
          text: >
            az network nsg rule create -g MyResourceGroup --nsg-name MyNsg -n MyNsgRule --priority 100
        - name: Create a "Deny" rule over TCP for a specific IP address range with the lowest priority.
          text: |
            az network nsg rule create -g MyResourceGroup --nsg-name MyNsg -n MyNsgRule --priority 4096 \\
                --source-address-prefixes 208.130.28/24 --source-port-ranges 80 \\
                --destination-address-prefixes '*' --destination-port-ranges 80 8080 --access Deny \\
                --protocol Tcp --description "Deny from specific IP address ranges on 80 and 8080."
        - name: Create a security rule using service tags.  For more details visit https://aka.ms/servicetags
          text: |
            az network nsg rule create -g MyResourceGroup --nsg-name MyNsg -n MyNsgRuleWithTags \\
                --priority 400 --source-address-prefixes VirtualNetwork --destination-address-prefixes Storage \\
                --destination-port-ranges * --direction Outbound --access Allow --protocol Tcp --description "Allow VirtualNetwork to Storage."
        - name: Create a security rule using application security groups. https://aka.ms/applicationsecuritygroups
          text: |
            az network nsg rule create -g MyResourceGroup --nsg-name MyNsg -n MyNsgRuleWithAsg \\
                --priority 500 --source-address-prefixes Internet --destination-port-ranges 80 8080 \\
                --destination-asgs Web --access Allow --protocol Tcp --description "Allow Internet to Web ASG on ports 80,8080."
"""

helps['network nsg rule delete'] = """
    type: command
    short-summary: Delete a network security group rule.
"""

helps['network nsg rule list'] = """
    type: command
    short-summary: List all rules in a network security group.
"""

helps['network nsg rule show'] = """
    type: command
    short-summary: Get the details for a network security group rule.
"""

helps['network nsg rule update'] = """
    type: command
    short-summary: Update a network security group rule.
    examples:
        - name: Update an NSG rule with a new wildcard destination address prefix.
          text: >
            az network nsg rule update -g MyResourceGroup --nsg-name MyNsg -n MyNsgRule --destination-address-prefix '*'
"""

# endregion

# region Public IP
helps['network public-ip'] = """
    type: group
    short-summary: Manage public IP addresses.
    long-summary: >
        To learn more about public IP addresses visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address
"""

helps['network public-ip create'] = """
    type: command
    short-summary: Create a public IP address.
    long-summary: To learn more about how to create a public IP address, visit  https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address#create-a-public-ip-address
    examples:
        - name: Create a basic public IP resource.
          text: >
            az network public-ip create -g MyResourceGroup -n MyIp
        - name: Create a static public IP resource for a DNS name label.
          text: >
            az network public-ip create -g MyResourceGroup -n MyIp --dns-name MyLabel --allocation-method Static
        - name: Create a public IP resource in an availability zone in the current resource group's region.
          text: >
            az network public-ip create -g MyResourceGroup -n MyIp --zone 2
"""

helps['network public-ip delete'] = """
    type: command
    short-summary: Delete a public IP address.
    long-summary: To learn more about how to delete a public IP address visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address#view-change-settings-for-or-delete-a-public-ip-address
    examples:
        - name: Delete a network interface
          text: az network public-ip delete -n MyNic -g MyResourceGroup
"""

helps['network public-ip list'] = """
    type: command
    short-summary: List public IP addresses.
    long-summary: To learn more about how to manage public IP addresses, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address
    examples:
        - name: List all public IPs in a resource group.
          text: >
            az network public-ip list -g MyResourceGroup
        - name: List all public IPs for a domain name label.
          text: >
            az network public-ip list -g MyResourceGroup --query "[?dnsSettings.domainNameLabel=='MyLabel']"
"""

helps['network public-ip show'] = """
    type: command
    short-summary: Get the details of a public IP address.
    long-summary: To learn more information about  public IP addressed in Azure, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address#view-change-settings-for-or-delete-a-public-ip-address
    examples:
        - name: Get information about a public IP resource.
          text: >
            az network public-ip show -g MyResourceGroup -n MyIp
        - name: Get the FQDN and IP address for a public IP resource.
          text: >
            az network public-ip show -g MyResourceGroup -n MyIp --query "{fqdn: dnsSettings.fqdn, address: ipAddress}"
"""

helps['network public-ip update'] = """
    type: command
    short-summary: Update a public IP address.
    long-summary: >
        To learn more information about public IP addresses in Azure, visit: https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address#view-change-settings-for-or-delete-a-public-ip-address
    examples:
        - name: Update a public IP resource with a DNS name label and static allocation.
          text: >
            az network public-ip update -g MyResourceGroup -n MyIp --dns-name MyLabel --allocation-method Static
"""
# endregion

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
    short-summary: Get the details for a route table.
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
    short-summary: Get the details of a route in a route table.
"""

helps['network route-table route update'] = """
    type: command
    short-summary: Update a route in a route table.
"""

# endregion

# region Route Filter
helps['network route-filter'] = """
    type: group
    short-summary: (PREVIEW) Manage route filters.
"""

helps['network route-filter create'] = """
    type: command
    short-summary: Create a route filter.
"""

helps['network route-filter delete'] = """
    type: command
    short-summary: Delete a route filter.
"""

helps['network route-filter list'] = """
    type: command
    short-summary: List route filters.
"""

helps['network route-filter show'] = """
    type: command
    short-summary: Get the details of a route filter.
"""

helps['network route-filter update'] = """
    type: command
    short-summary: Update a route filter.
"""

helps['network route-filter rule'] = """
    type: group
    short-summary: (PREVIEW) Manage rules in a route filter.
"""

helps['network route-filter rule create'] = """
    type: command
    short-summary: Create a rule in a route filter.
    parameters:
        - name: --communities
          short-summary: Space-separated list of border gateway protocol (BGP) community values to filter on.
          populator-commands:
            - az network route-filter rule list-service-communities
"""

helps['network route-filter rule delete'] = """
    type: command
    short-summary: Delete a rule from a route filter.
"""

helps['network route-filter rule list'] = """
    type: command
    short-summary: List rules in a route filter.
"""

helps['network route-filter rule show'] = """
    type: command
    short-summary: Get the details of a rule in a route filter.
"""

helps['network route-filter rule update'] = """
    type: command
    short-summary: Update a rule in a route filter.
"""

# endregion

# region Traffic Manager
helps['network traffic-manager'] = """
    type: group
    short-summary: Manage the routing of incoming traffic.
"""

helps['network traffic-manager endpoint'] = """
    type: group
    short-summary: Manage traffic manager end points.
"""

helps['network traffic-manager profile'] = """
    type: group
    short-summary: Manage traffic manager profiles.
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
    short-summary: Get the details for a profile.
"""

helps['network traffic-manager profile update'] = """
    type: command
    short-summary: Update a profile.
"""

helps['network traffic-manager endpoint create'] = """
    type: command
    short-summary: Create an endpoint.
    parameters:
        - name: --geo-mapping
          short-summary: Space-separated list of country/region codes mapped to this endpoint when using the 'Geographic' routing method.
          populator-commands:
          - az network traffic-manager endpoint show-geographic-hierarchy
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
    short-summary: Get the details for an endpoint.
"""

helps['network traffic-manager endpoint update'] = """
    type: command
    short-summary: Update an endpoint.
"""
# endregion

# region Virtual Network (VNET)
helps['network vnet'] = """
    type: group
    short-summary: Manage Azure Virtual Networks.
    long-summary: To learn more about Virtual Networks visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network
"""

helps['network vnet check-ip-address'] = """
    type: command
    short-summary: Check if a private IP address is available for use within a virtual network.
    examples:
        - name: Check whether 10.0.0.4 is available within MyVnet.
          text: >
            az network vnet check-ip-address -n MyVnet -g MyResourceGroup --ip-address 10.0.0.4
"""

helps['network vnet create'] = """
    type: command
    short-summary: Create a virtual network.
    long-summary: You may also create a subnet at the same time by specifying a subnet name and (optionally) an address prefix. To learn about how to create a virtual network visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network#create-vnet
    examples:
        - name: Create a virtual network.
          text: >
            az network vnet create -g MyResourceGroup -n MyVnet
        - name: Create a virtual network with a specific address prefix and one subnet.
          text: >
            az network vnet create -g MyResourceGroup -n MyVnet --address-prefix 10.0.0.0/16 --subnet-name MySubnet --subnet-prefix 10.0.0.0/24
"""

helps['network vnet delete'] = """
    type: command
    short-summary: Delete a virtual network.
    long-summary: >
        To learn more about deleting a virtual network, visit: https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network#delete-vnet
    examples:
     - name: Delete a virtual network
       text: az network vnet delete -n myVNet -g MyResourceGroup
"""

helps['network vnet list'] = """
    type: command
    short-summary: List virtual networks.
    long-summary: To learn more about virtual networks, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network#a-name--view-vnetaview-virtual-networks-and-settings
    examples:
        - name: List virtual networks which specify a certain address prefix.
          text: az network vnet list --query "[?contains(addressSpace.addressPrefixes, '10.0.0.0/16')]"
"""

helps['network vnet show'] = """
    type: command
    short-summary: Get the details of a virtual network.
    long-summary: To learn more about virtual networks and settings, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network#a-name--view-vnetaview-virtual-networks-and-settings
    examples:
        - name: Get details for MyVNet.
          text: az network vnet show -n MyVNet -g MyResourceGroup
"""

helps['network vnet update'] = """
    type: command
    short-summary: Update a virtual network.
    long-summary: To learn more about managing virtual networks, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network
    examples:
        - name: Update MyVNet's DNS server
          text: az network vnet update -n MyVNet -g MyResourceGroup --dns-servers 10.2.0.8
"""
# endregion

# region VNet Subnet
helps['network vnet subnet'] = """
    type: group
    short-summary: Manage subnets in an Azure Virtual Network.
    long-summary: To learn more about subnets visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet
"""

helps['network vnet subnet create'] = """
    type: command
    short-summary: Create a subnet and associate an existing NSG and route table.
    long-summary: To learn more about subnets, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet
    parameters:
        - name: --service-endpoints
          short-summary: Space-separated list of services allowed private access to this subnet.
          populator-commands:
            - az network vnet list-endpoint-services
    examples:
        - name: Create new subnet attached to an NSG with a custom route table.
          text: |
            az network vnet subnet create -g MyResourceGroup --vnet-name MyVnet -n MySubnet \\
                --address-prefix 10.0.0.0/24 --network-security-group MyNsg --route-table MyRouteTable
"""

helps['network vnet subnet delete'] = """
    type: command
    short-summary: Delete a subnet.
    long-summary: To learn more about deleting a virtual network visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet#delete-subnet
    examples:
        - name: Delete a subnet
          text: az network vnet subnet delete -n mySubnet -g MyResourceGroup
"""

helps['network vnet subnet list'] = """
    type: command
    short-summary: List subnets.
    long-summary: To learn more about subnets in Azure, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet
    examples:
        - name: Typical usage
          text: az network vnet subnet list -n myVNet -g myResourceGroup
"""

helps['network vnet subnet show'] = """
    type: command
    short-summary: Show details of a subnet.
    long-summary: To learn more about subnets, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet
    examples:
        - name: Show subnets associated to a specific virtual network
          text: az network vnet subnet show -n mySubnet --vnet-name myVNet -g myResourceGroup
"""

helps['network vnet subnet update'] = """
    type: command
    short-summary: Update a subnet.
    long-summary: To learn more about subnets, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet
    parameters:
        - name: --service-endpoints
          short-summary: Space-separated list of services allowed private access to this subnet.
          populator-commands:
            - az network vnet list-endpoint-services
    examples:
        - name: Associate a network security group to a subnet
          text: az network vnet subnet update -n MySubnet --vnet-name MyVNet -g MyResourceGroup --network-security-group MyNSG
"""

helps['network vnet list-endpoint-services'] = """
    type: command
    short-summary: List which services support VNET service tunneling for a given region.
    long-summary: To learn more about service endpoints visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoints-configure#azure-cli
    examples:
        - name: List the endpoint services available for use in the West US region.
          text: az network vnet list-endpoint-services -l westus -o table
"""
# endregion

# region Virtual Network (VNet) Peering
helps['network vnet peering'] = """
    type: group
    short-summary: Manage peering connections between Azure Virtual Networks.
    long-summary: To learn more about virtual network peering visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering
"""

helps['network vnet peering create'] = """
    type: command
    short-summary: Create a peering.
    long-summary: To learn more about virtual network peering about how to create a peering, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering#before-you-begin
    examples:
        - name: Create a virtual network peering between virtual networks in the same region
          text: |
            az network vnet create --name MyVnet1 --resource-group MyResourceGroup --location eastus --address-prefix 10.0.0.0/16 \\
                \\n\\n az network vnet create --name MyVnet2 --resource-group MyResourceGroup --location eastus --address-prefix 10.1.0.0/16 \\
                \\n\\n vnet1Id=$(az network vnet show --resource-group MyResourceGroup--name MyVnet1 --query id --out tsv) \\
                \\n\\n vnet2Id=$(az network vnet show --resource-group MyResourceGroup --name MyVnet2 --query id --out tsv) \\
                \\n\\n az network vnet peering create --name MyVnet1ToMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1 --remote-vnet-id $vnet2Id --allow-vnet-access \\
                \\n\\n az network vnet peering create --name MyVnet2ToMyVnet1 --resource-group MyResourceGroup --vnet-name MyVnet2 --remote-vnet-id $vnet1Id --allow-vnet-access
        - name: Create a virtual network peering between virtual networks in different regions
          text: |
            az network vnet create --name MyVnet1 --resource-group MyResourceGroup --location westcentralus --address-prefix 10.0.0.0/16 \\
                \\n\\n az network vnet create --name MyVnet2 --resource-group MyResourceGroup --location canadacentral --address-prefix 10.2.0.0/16 \\
                \\n\\n vnet1Id=$(az network vnet show --resource-group MyResourceGroup--name MyVnet1 --query id --out tsv) \\
                \\n\\n vnet2Id=$(az network vnet show --resource-group MyResourceGroup --name MyVnet2 --query id --out tsv) \\
                \\n\\n az network vnet peering create --name MyVnet1ToMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1 --remote-vnet-id $vnet2Id --allow-vnet-access \\
                \\n\\n az network vnet peering create --name MyVnet2ToMyVnet1 --resource-group MyResourceGroup --vnet-name MyVnet2 --remote-vnet-id $vnet1Id --allow-vnet-access
"""

helps['network vnet peering delete'] = """
    type: command
    short-summary: Delete a peering.
    long-summary: To learn more about how to delete a virtual network peering visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering#delete-a-peering
    examples:
        - name: Delete a virtual network peering
          text: >
            az network vnet peering delete --name MyVnet1toMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1
"""

helps['network vnet peering list'] = """
    type: command
    short-summary: List peerings.
    long-summary: To learn more about virtual network peerings, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering#view-or-change-peering-settings
    examples:
        - name: List all peerings of a specified virtual network
          text: >
            az network vnet peering list --resource-group MyResourceGroup --vnet-name MyVnet1
"""

helps['network vnet peering show'] = """
    type: command
    short-summary: Show details of a peering.
    long-summary: To learn more about virtual network peering details and settings, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering#view-or-change-peering-settings
    examples:
        - name: Show all details of the specified virtual network peering.
          text: >
             az network vnet peering show --name MyVnet1toMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1
"""

helps['network vnet peering update'] = """
    type: command
    short-summary: Update a peering.
    long-summary: To learn more about updating virtual network peerings, visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering
    examples:
        - name: Change forwarded traffic configuration of a virtual network peering
          text: >
            az network vnet peering update ---name MyVnet1toMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1 --set allowForwardedTraffic==true
        - name: Change virtual network access of a virtual network peering
          text: >
            az network vnet peering update ---name MyVnet1toMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1 --set allowVirtualNetworkAccess==true
        - name: Change gateway transit property configuration of a virtual network peering
          text: >
            az network vnet peering update ---name MyVnet1toMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1 --set allowGatewayTransit==true
        - name: Use remote gateways in virtual network peering
          text: >
            az network vnet peering update ---name MyVnet1toMyVnet2 --resource-group MyResourceGroup --vnet-name MyVnet1 --set useRemoteGateways==true
"""

# endregion

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
    short-summary: Get the details of a VPN connection.
"""

helps['network vpn-connection update'] = """
    type: command
    short-summary: Update a VPN connection.
"""

# endregion

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
    short-summary: Retrieve a VPN connection shared key.
"""

helps['network vpn-connection shared-key update'] = """
    type: command
    short-summary: Update a VPN connection shared key.
"""

# endregion

# region VPN Connection IPSec Policy
helps['network vpn-connection ipsec-policy'] = """
    type: group
    short-summary: Manage VPN connection IPSec policies.
"""

helps['network vpn-connection ipsec-policy add'] = """
    type: command
    short-summary: Add a VPN connection IPSec policy.
"""

helps['network vpn-connection ipsec-policy list'] = """
    type: command
    short-summary: List IPSec policies associated with a VPN connection.
"""

helps['network vpn-connection ipsec-policy clear'] = """
    type: command
    short-summary: Delete all IPSec policies on a VPN connection.
"""

# endregion

# region VNet Gateway
helps['network vnet-gateway'] = """
    type: group
    short-summary: Use an Azure Virtual Network Gateway to establish secure, cross-premises connectivity.
"""

helps['network vnet-gateway create'] = """
    type: command
    short-summary: Create a virtual network gateway.
    examples:
        - name: Create a basic virtual network gateway and associate with a public IP address.
          text: >
            az network vnet-gateway create -g MyResourceGroup --vnet MyVnet -n MyVnetGateway --public-ip-address MyIp
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
    short-summary: Get the details for a virtual network gateway.
"""

helps['network vnet-gateway update'] = """
    type: command
    short-summary: Update a virtual network gateway.
"""

helps['network vnet-gateway wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the virtual network gateway is met.
"""

helps['network vnet-gateway vpn-client'] = """
    type: group
    short-summary: Download a configured client with which to connect to a VPN.
"""

helps['network vnet-gateway vpn-client generate'] = """
    type: command
    short-summary: Generates a binary client file that can be used to connect to a VPN.
    long-summary: The legacy implementation returns an EXE, while the latest implementation returns a ZIP file.
"""


# endregion

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

# endregion

# region VNet Gateway Root Cert
helps['network vnet-gateway root-cert'] = """
    type: group
    short-summary: Manage root certificates for a virtual network gateway.
"""

helps['network vnet-gateway root-cert create'] = """
    type: command
    short-summary: Upload a root certificate.
"""

helps['network vnet-gateway root-cert delete'] = """
    type: command
    short-summary: Delete a root certificate.
"""

# endregion

# region Network Watcher
helps['network watcher'] = """
    type: group
    short-summary: Manage the Azure Network Watcher.
    long-summary: >
        Network Watcher assists with monitoring and diagnosing conditions at a network scenario level. To learn more visit https://docs.microsoft.com/en-us/azure/network-watcher/
"""

helps['network watcher list'] = """
    type: command
    short-summary: List Network Watchers.
    examples:
        - name: List all Network Watchers in a subscription.
          text: az network watcher list
"""

helps['network watcher configure'] = """
    type: command
    short-summary: Configure the Network Watcher service for different regions.
    parameters:
        - name: --enabled
          short-summary: Enabled status of Network Watch in the specified regions.
        - name: --locations -l
          short-summary: Space-separated list of locations to configure.
        - name: --resource-group -g
          short-summary: Name of resource group. Required when enabling new regions.
          long-summary: >
            When a previously disabled region is enabled to use Network Watcher, a
                Network Watcher resource will be created in this resource group.
    examples:
        - name: Configure Network Watcher in a region.
          text: az network watcher configure --resource-group NetworkWatcherRG  --locations westus --enabled true
"""

helps['network watcher troubleshooting'] = """
    type: group
    short-summary: Manage Network Watcher troubleshooting sessions.
    long-summary: >
        For more information on configuring troubleshooting visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-troubleshoot-manage-cli
"""

helps['network watcher troubleshooting start'] = """
    type: command
    short-summary: Troubleshoot issues with VPN connections or gateway connectivity.
    long-summary: For more information on configuring troubleshooting, visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-troubleshoot-manage-cli
    parameters:
        - name: --resource-type -t
          short-summary: The type of target resource to troubleshoot, if resource ID is not specified.
        - name: --storage-account
          short-summary: Name or ID of the storage account in which to store the troubleshooting results.
        - name: --storage-path
          short-summary: Fully qualified URI to the storage blob container in which to store the troubleshooting results.
    examples:
        - name: Start a troubleshooting operation
          text: |
            az network watcher troubleshooting start --resource-group MyResourceGroup \\
                --resource MyResourceName --resource-type {vnetGateway/vpnConnection} --storage-account MyStorageAccount \\
                --storage-path https://{storageAccountName}.blob.core.windows.net/{containerName}
"""

helps['network watcher troubleshooting show'] = """
    type: command
    short-summary: Get the results of the last troubleshooting operation.
    long-summary: For more information on configuring troubleshooting, visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-troubleshoot-manage-cli
    examples:
        - name: Show the results or status of a troubleshooting operation
          text: az network watcher troubleshooting show --resource MyResourceName --resource-group MyResourceGroup --resource-type vnetGateway
"""

helps['network watcher test-ip-flow'] = """
    type: command
    short-summary: Test IP flow to/from a VM given the currently configured network security group rules.
    long-summary: Requires that Network Watcher is enabled for the region in which the VM is located. For more information visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-check-ip-flow-verify-cli
    parameters:
        - name: --local
          short-summary: >
            The private IPv4 address for the VM's NIC and the port of the packet in
            X.X.X.X:PORT format. '*' can be used for port when direction is outbound.
        - name: --remote
          short-summary: >
            The IPv4 address and port for the remote side of the packet
            X.X.X.X:PORT format. '*' can be used for port when direction is inbound.
        - name: --direction
          short-summary: Direction of the packet relative to the VM.
        - name: --protocol
          short-summary: Protocol to test.
    examples:
        - name: Run test-ip-flow verify to test logical connectivity from a VM to the specified destination IPv4 address and port.
          text: |
            az network watcher test-ip-flow --resource-group MyResourceGroup --direction Outbound  \\
                --protocol TCP --local 10.0.0.4:* --remote 10.1.0.4:80 --vm MyVm
"""

helps['network watcher test-connectivity'] = """
    type: command
    short-summary: (PREVIEW) Test if a connection can be established between a Virtual Machine and a given endpoint.
    long-summary: >
        To register for this feature or see additional examples visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-connectivity-cli
    parameters:
        - name: --source-resource
          short-summary: Name or ID of the resource from which to originate traffic.
          long-summary: Currently only Virtual Machines are supported.
        - name: --source-port
          short-summary: Port number from which to originate traffic.
        - name: --dest-resource
          short-summary: Name or ID of the resource to receive traffic.
          long-summary: Currently only Virtual Machines are supported.
        - name: --dest-port
          short-summary: Port number on which to receive traffic.
        - name: --dest-address
          short-summary: The IP address or URI at which to receive traffic.
    examples:
        - name: Check connectivity between two virtual machines in the same resource group over port 80.
          text: az network watcher test-connectivity -g MyResourceGroup --source-resource MyVmName1 --dest-resource MyVmName2 --dest-port 80
        - name: Check connectivity between two virtual machines in the same subscription in two different resource groups over port 80.
          text: |
            Vm1Id=$(az vm show --resource-group MyResourceGroup--name MyVm1 --query id --out tsv) \\
                Vm2Id=$(az vm show --resource-group MyResourceGroup--name MyVm2 --query id --out tsv) \\
                az network watcher test-connectivity --source-resource $MyVmId1 --dest-resource $MyVmId2 --dest-port 80
"""

helps['network watcher show-next-hop'] = """
    type: command
    short-summary: Get information on the 'next hop' for a VM.
    long-summary: Requires that Network Watcher is enabled for the region in which the VM is located. For more information about show-next-hop visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-check-next-hop-cli
    examples:
        - name: Get the next hop from a VM's assigned IP address to a destination at 10.1.0.4.
          text: az network watcher show-next-hop -g MyResourceGroup --vm MyVm --source-ip 10.0.0.4 --dest-ip 10.1.0.4
"""

helps['network watcher show-security-group-view'] = """
    type: command
    short-summary: Get detailed security information on a VM for the currently configured network security group.
    long-summary: For more information on using security group view visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-security-group-view-cli
    examples:
        - name: Get the network security group information for the specified VM.
          text: az network watcher show-security-group-view -g MyResourceGroup --vm MyVm
"""

helps['network watcher show-topology'] = """
    type: command
    short-summary: Get the network topology of a resource group, virtual network or subnet.
    long-summary: For more information about using network topology visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-topology-cli
    parameters:
        - name: --resource-group -g
          short-summary: The name of the target resource group to perform topology on.
        - name: --location -l
          short-summary: Location. Defaults to the location of the target resource group.
          long-summary: >
            Topology information is only shown for resources within the target
            resource group that are within the specified region.
    examples:
        - name: Use show-topology to get the topology of resources within a resource group.
          text: az network watcher show-topology -g resourcegroupname
"""

helps['network watcher connection-monitor'] = """
    type: group
    short-summary: Manage connection monitoring.
"""

helps['network watcher connection-monitor create'] = """
    type: command
    short-summary: Create a connection monitor.
    parameters:
        - name: --source-resource
          long-summary: >
            Currently only Virtual Machines are supported.
        - name: --dest-resource
          long-summary: >
            Currently only Virtual Machines are supported.
"""

helps['network watcher connection-monitor list'] = """
    type: command
    short-summary: List connection monitors for the given region.
"""

helps['network watcher packet-capture'] = """
    type: group
    short-summary: Manage packet capture sessions on VMs.
    long-summary: >
        These commands require that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information on packet-capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
"""

helps['network watcher packet-capture create'] = """
    type: command
    short-summary: Create and start a packet capture session.
    long-summary: >
        This command requires that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information on packet-capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    parameters:
        - name: --capture-limit
          short-summary: The maximum size in bytes of the capture output.
        - name: --capture-size
          short-summary: Number of bytes captured per packet. Excess bytes are truncated.
        - name: --time-limit
          short-summary: Maximum duration of the capture session in seconds.
        - name: --storage-account
          short-summary: Name or ID of a storage account to save the packet capture to.
        - name: --storage-path
          short-summary: Fully qualified URI of an existing storage container in which to store the capture file.
          long-summary: >
            If not specified, the container 'network-watcher-logs' will be
            created if it does not exist and the capture file will be stored there.
        - name: --file-path
          short-summary: >
                Local path on the targeted VM at which to save the packet capture. For Linux VMs, the
                path must start with /var/captures.
        - name: --vm
          short-summary: Name or ID of the VM to target.
        - name: --filters
          short-summary: JSON encoded list of packet filters. Use `@<file path>` to load from file.
    examples:
        - name: Create a packet capture session on a VM
          text: az network watcher packet-capture create -g MyResourceGroup -n MyPacketCaptureName --vm MyVm --storage-account MyStorageAccount
        - name: Create a packet capture session on a VM with optional filters for protocols, local IP address and remote IP address ranges and ports
          text: |
                az network watcher packet-capture create -g MyResourceGroup -n MyPacketCaptureName --vm MyVm  \\
                    --storage-account MyStorageAccount --filters '[ \\
                        { \\
                            "protocol":"TCP", \\
                            "remoteIPAddress":"1.1.1.1-255.255.255", \\
                            "localIPAddress":"10.0.0.3", \\
                            "remotePort":"20" \\
                        }, \\
                        { \\
                            "protocol":"TCP", \\
                            "remoteIPAddress":"1.1.1.1-255.255.255", \\
                            "localIPAddress":"10.0.0.3", \\
                            "remotePort":"80" \\
                        }, \\
                        { \\
                            "protocol":"TCP", \\
                            "remoteIPAddress":"1.1.1.1-255.255.255", \\
                            "localIPAddress":"10.0.0.3", \\
                            "remotePort":"443" \\
                        }, \\
                        { \\
                            "protocol":"UDP" \\
                        }]'
"""

helps['network watcher packet-capture delete'] = """
    type: command
    long-summary: >
        This command requires that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Delete a packet capture session. Note that this only deletes the session and not the capture file.
          text: az network watcher packet-capture delete -n packetCaptureName --location westcentralus
"""

helps['network watcher packet-capture list'] = """
    type: command
    long-summary: >
        This command requires that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: List all packet capture sessions within a resource group.
          text: az network watcher packet-capture list --location westus
"""

helps['network watcher packet-capture show'] = """
    type: command
    long-summary: >
        This command requires that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Show a packet capture session.
          text: az network watcher packet-capture show --location westus -n MyPacketCapture
"""

helps['network watcher packet-capture show-status'] = """
    type: command
    long-summary: >
        This command requires that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Show the status of a packet capture session.
          text: az network watcher packet-capture show-status --location westus -n MyPacketCapture
"""

helps['network watcher packet-capture stop'] = """
    type: command
    long-summary: >
        This command requires that both Azure Network Watcher is enabled for the VM's region and that AzureNetworkWatcherExtension is enabled on the VM.
        For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Stop a running packet capture session.
          text: az network watcher packet-capture stop --location westus -n MyPacketCapture
"""

helps['network watcher packet-capture show'] = """
    type: command
    long-summary: For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Show a packet capture session.
          text: az network watcher packet-capture show --location myresourcegroup -n mypacketcapture
"""

helps['network watcher packet-capture show-status'] = """
    type: command
    long-summary: For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Show the status of a packet capture session.
          text: az network watcher packet-capture show-status --location myresourcegroup -n mypacketcapture
"""

helps['network watcher packet-capture stop'] = """
    type: command
    long-summary: For more information about configuring packet capture visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
    examples:
        - name: Stop a running packet capture session.
          text: az network watcher packet-capture stop --location myresourcegroup -n mypacketcapture
"""


helps['network watcher flow-log'] = """
    type: group
    short-summary: Manage network security group flow logging.
    long-summary: For more information about configuring flow logs visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-cli
"""

helps['network watcher flow-log configure'] = """
    type: command
    short-summary: Configure flow logging on a network security group.
    long-summary: For more information about configuring flow logs, visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-cli
    parameters:
        - name: --nsg
          short-summary: Name or ID of the Network Security Group to target.
        - name: --enabled
          short-summary: Enable logging.
        - name: --retention
          short-summary: Number of days to retain logs.
        - name: --storage-account
          short-summary: Name or ID of the storage account in which to save the flow logs.
    examples:
        - name: Enable NSG flow logs.
          text: az network watcher flow-log configure -g MyResourceGroup --enabled true --nsg MyNsg --storage-account MyStorageAccount
        - name: Disable NSG flow logs
          text: az network watcher flow-log configure -g MyResourceGroup --enabled false --nsg MyNsg
"""

helps['network watcher flow-log show'] = """
    type: command
    short-summary: Get the flow log configuration for a network security group.
    long-summary: For more information about configuring flow logs, visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-cli
    examples:
        - name: Show NSG flow logs.
          text: az network watcher flow-log show -g myGroup --nsg nsgName
"""

# endregion
