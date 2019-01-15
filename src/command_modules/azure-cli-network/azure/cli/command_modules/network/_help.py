# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["network lb frontend-ip show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a frontend IP address.
"""

helps["network list-usages"] = """
"type": |-
    command
"short-summary": |-
    List the number of network resources in a region that are used against a subscription quota.
"""

helps["network dns record-set srv"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS SRV records.
"""

helps["network application-gateway rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a rule.
"""

helps["network lb show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a load balancer.
"examples":
-   "name": |-
        Get the details of a load balancer.
    "text": |-
        az network lb show --name MyLb --query [0] --resource-group MyResourceGroup
"""

helps["network dns record-set ptr add-record"] = """
"type": |-
    command
"short-summary": |-
    Add a PTR record.
"""

helps["network dns record-set mx create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty MX record set.
"""

helps["network lb rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a load balancing rule.
"""

helps["network application-gateway ssl-cert create"] = """
"type": |-
    command
"short-summary": |-
    Upload an SSL certificate.
"""

helps["network dns record-set ns remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove an NS record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network dns record-set a update"] = """
"type": |-
    command
"short-summary": |-
    Update an A record set.
"""

helps["network nsg show"] = """
"type": |-
    command
"short-summary": |-
    Get information about a network security group.
"examples":
-   "name": |-
        Get information about a network security group.
    "text": |-
        az network nsg show --resource-group MyResourceGroup --query [0] --name MyNsg
"""

helps["network lb probe list"] = """
"type": |-
    command
"short-summary": |-
    List probes.
"""

helps["network dns record-set ptr show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a PTR record set.
"""

helps["network application-gateway auth-cert create"] = """
"type": |-
    command
"short-summary": |-
    Create an authorization certificate.
"""

helps["network local-gateway create"] = """
"type": |-
    command
"short-summary": |-
    Create a local VPN gateway.
"""

helps["network express-route peering create"] = """
"type": |-
    command
"short-summary": |-
    Create peering settings for an ExpressRoute circuit.
"""

helps["network nsg delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a network security group.
"examples":
-   "name": |-
        Delete a network security group.
    "text": |-
        az network nsg delete --resource-group MyResourceGroup --name MyNsg
"""

helps["network application-gateway ssl-policy set"] = """
"type": |-
    command
"short-summary": |-
    Update or clear SSL policy settings.
"long-summary": |-
    To view the predefined policies, use `az network application-gateway ssl-policy predefined list`.
"parameters":
-   "name": |-
        --cipher-suites
    "populator-commands":
    - |-
        az network application-gateway ssl-policy list-options
-   "name": |-
        --disabled-ssl-protocols
    "populator-commands":
    - |-
        az network application-gateway ssl-policy list-options
-   "name": |-
        --min-protocol-version
    "populator-commands":
    - |-
        az network application-gateway ssl-policy list-options
"""

helps["network application-gateway stop"] = """
"type": |-
    command
"short-summary": |-
    Stop an application gateway.
"""

helps["network dns record-set txt list"] = """
"type": |-
    command
"short-summary": |-
    List all TXT record sets in a zone.
"""

helps["network application-gateway address-pool show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an address pool.
"""

helps["network express-route update"] = """
"type": |-
    command
"short-summary": |-
    Update settings of an ExpressRoute circuit.
"""

helps["network route-filter rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a rule in a route filter.
"parameters":
-   "name": |-
        --communities
    "short-summary": |-
        Space-separated list of border gateway protocol (BGP) community values to filter on.
    "populator-commands":
    - |-
        az network route-filter rule list-service-communities
"""

helps["network nic ip-config address-pool add"] = """
"type": |-
    command
"short-summary": |-
    Add an address pool to an IP configuration.
"""

helps["network application-gateway probe delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a probe.
"""

helps["network application-gateway http-listener show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an HTTP listener.
"""

helps["network application-gateway waf-config set"] = """
"type": |-
    command
"short-summary": |-
    Update the firewall configuration of a web application.
"long-summary": |
    This command is only applicable to application gateways with an SKU type of WAF. To learn more, visit https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-web-application-firewall-cli
"parameters":
-   "name": |-
        --rule-set-type
    "short-summary": |-
        Rule set type.
    "populator-commands":
    - |-
        az network application-gateway waf-config list-rule-sets
-   "name": |-
        --rule-set-version
    "short-summary": |-
        Rule set version.
    "populator-commands":
    - |-
        az network application-gateway waf-config list-rule-sets
-   "name": |-
        --disabled-rule-groups
    "short-summary": |-
        Space-separated list of rule groups to disable. To disable individual rules, use `--disabled-rules`.
    "populator-commands":
    - |-
        az network application-gateway waf-config list-rule-sets
-   "name": |-
        --disabled-rules
    "short-summary": |-
        Space-separated list of rule IDs to disable.
    "populator-commands":
    - |-
        az network application-gateway waf-config list-rule-sets
-   "name": |-
        --exclusion
    "short-summary": |-
        Add an exclusion expression to the WAF check.
    "long-summary": |
        Usage:   --exclusion VARIABLE OPERATOR VALUE

        Multiple exclusions can be specified by using more than one `--exclusion` argument.
"""

helps["network lb outbound-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage outbound rules of a load balancer.
"""

helps["network route-filter rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a rule in a route filter.
"""

helps["network application-gateway ssl-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage the SSL policy of an application gateway.
"""

helps["network express-route peering connection create"] = """
"type": |-
    command
"short-summary": |-
    Create connections between two ExpressRoute circuits.
"""

helps["network dns record-set ptr delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a PTR record set and all associated records.
"""

helps["network lb address-pool delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an address pool.
"""

helps["network vpn-connection create"] = """
"type": |-
    command
"short-summary": |-
    Create a VPN connection.
"long-summary": |-
    The VPN Gateway and Local Network Gateway must be provisioned before creating the connection between them.
"""

helps["network local-gateway update"] = """
"type": |-
    command
"short-summary": |-
    Update a local VPN gateway.
"""

helps["network route-table route update"] = """
"type": |-
    command
"short-summary": |-
    Update a route in a route table.
"""

helps["network route-table route delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a route from a route table.
"""

helps["network application-gateway show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an application gateway.
"""

helps["network application-gateway url-path-map rule"] = """
"type": |-
    group
"short-summary": |-
    Manage the rules of a URL path map.
"""

helps["network service-endpoint policy delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a service endpoint policy.
"""

helps["network dns record-set aaaa"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS AAAA records.
"""

helps["network nic create"] = """
"type": |-
    command
"short-summary": |-
    Create a network interface.
"examples":
-   "name": |-
        Create a network interface.
    "text": |-
        az network nic create --subnet MySubnet --public-ip-address <public-ip-address> --location westus2 --name MyNic --resource-group MyResourceGroup --vnet-name MyVnet
"""

helps["network route-filter rule list"] = """
"type": |-
    command
"short-summary": |-
    List rules in a route filter.
"""

helps["network application-gateway start"] = """
"type": |-
    command
"short-summary": |-
    Start an application gateway.
"""

helps["network express-route list-route-tables"] = """
"type": |-
    command
"short-summary": |-
    Show the current routing table of an ExpressRoute circuit peering.
"""

helps["network traffic-manager profile"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Traffic Manager profiles.
"""

helps["network express-route list-arp-tables"] = """
"type": |-
    command
"short-summary": |-
    Show the current Address Resolution Protocol (ARP) table of an ExpressRoute circuit.
"""

helps["network dns record-set srv update"] = """
"type": |-
    command
"short-summary": |-
    Update an SRV record set.
"""

helps["network vnet-gateway update"] = """
"type": |-
    command
"short-summary": |-
    Update a virtual network gateway.
"""

helps["network public-ip"] = """
"type": |-
    group
"short-summary": |-
    Manage public IP addresses.
"long-summary": |
    To learn more about public IP addresses visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-public-ip-address
"""

helps["network vnet-gateway show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a virtual network gateway.
"""

helps["network dns record-set txt remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove a TXT record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network traffic-manager profile list"] = """
"type": |-
    command
"short-summary": |-
    List traffic manager profiles.
"""

helps["network nic show-effective-route-table"] = """
"type": |-
    command
"short-summary": |-
    Show the effective route table applied to a network interface.
"long-summary": |
    To learn more about troubleshooting using the effective route tables visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-routes-troubleshoot-portal#using-effective-routes-to-troubleshoot-vm-traffic-flow
"""

helps["network application-gateway ssl-cert list"] = """
"type": |-
    command
"short-summary": |-
    List SSL certificates.
"""

helps["network dns record-set aaaa create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty AAAA record set.
"""

helps["network lb probe show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a probe.
"""

helps["network application-gateway http-listener list"] = """
"type": |-
    command
"short-summary": |-
    List HTTP listeners.
"""

helps["network vnet create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network.
"long-summary": |
    You may also create a subnet at the same time by specifying a subnet name and (optionally) an address prefix. To learn about how to create a virtual network visit https://docs.microsoft.com/en-us/azure/virtual-network/manage-virtual-network#create-a-virtual-network
"examples":
-   "name": |-
        Create a virtual network.
    "text": |-
        az network vnet create --address-prefixes <address-prefixes> --location westus2 --resource-group MyResourceGroup --subnet-name MySubnet --name MyVnet --subnet-prefixes <subnet-prefixes>
"""

helps["network dns record-set aaaa delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an AAAA record set and all associated records.
"""

helps["network dns record-set ns update"] = """
"type": |-
    command
"short-summary": |-
    Update an NS record set.
"""

helps["network application-gateway frontend-port list"] = """
"type": |-
    command
"short-summary": |-
    List frontend ports.
"""

helps["network application-gateway redirect-config update"] = """
"type": |-
    command
"short-summary": |-
    Update a redirect configuration.
"""

helps["network route-filter create"] = """
"type": |-
    command
"short-summary": |-
    Create a route filter.
"""

helps["network asg"] = """
"type": |-
    group
"short-summary": |-
    Manage application security groups (ASGs).
"long-summary": |
    You can configure network security as a natural extension of an application's structure, ASG allows you to group virtual machines and define network security policies based on those groups. You can specify an application security group as the source and destination in a NSG security rule. For more information visit https://docs.microsoft.com/en-us/azure/virtual-network/create-network-security-group-preview
"""

helps["network application-gateway redirect-config list"] = """
"type": |-
    command
"short-summary": |-
    List redirect configurations.
"""

helps["network dns record-set txt show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a TXT record set.
"""

helps["network vnet-gateway wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the virtual network gateway is met.
"""

helps["network watcher troubleshooting start"] = """
"type": |-
    command
"short-summary": |-
    Troubleshoot issues with VPN connections or gateway connectivity.
"parameters":
-   "name": |-
        --resource-type -t
    "short-summary": |-
        The type of target resource to troubleshoot, if resource ID is not specified.
-   "name": |-
        --storage-account
    "short-summary": |-
        Name or ID of the storage account in which to store the troubleshooting results.
-   "name": |-
        --storage-path
    "short-summary": |-
        Fully qualified URI to the storage blob container in which to store the troubleshooting results.
"""

helps["network nic"] = """
"type": |-
    group
"short-summary": |-
    Manage network interfaces.
"long-summary": |
    To learn more about network interfaces in Azure visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface
"""

helps["network application-gateway waf-config"] = """
"type": |-
    group
"short-summary": |-
    Configure the settings of a web application firewall.
"long-summary": |
    These commands are only applicable to application gateways with an SKU type of WAF. To learn more, visit https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-web-application-firewall-cli
"""

helps["network lb rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a load balancing rule.
"""

helps["network asg show"] = """
"type": |-
    command
"short-summary": |-
    Get details of an application security group.
"""

helps["network route-filter list"] = """
"type": |-
    command
"short-summary": |-
    List route filters.
"""

helps["network dns record-set ptr list"] = """
"type": |-
    command
"short-summary": |-
    List all PTR record sets in a zone.
"""

helps["network asg create"] = """
"type": |-
    command
"short-summary": |-
    Create an application security group.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name of the new application security group resource.
"""

helps["network traffic-manager endpoint show-geographic-hierarchy"] = """
"type": |-
    command
"short-summary": |-
    Get the default geographic hierarchy used by the geographic traffic routing method.
"""

helps["network application-gateway root-cert show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a trusted root certificate.
"""

helps["network vnet-gateway vpn-client generate"] = """
"type": |-
    command
"short-summary": |-
    Generate VPN client configuration.
"long-summary": |-
    The command outputs a URL to a zip file for the generated VPN client configuration.
"""

helps["network application-gateway"] = """
"type": |-
    group
"short-summary": |-
    Manage application-level routing and load balancing services.
"long-summary": |-
    To learn more about Application Gateway, visit https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-create-gateway-cli
"""

helps["network service-endpoint policy-definition update"] = """
"type": |-
    command
"short-summary": |-
    Update a service endpoint policy definition.
"""

helps["network vnet peering show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a peering.
"""

helps["network application-gateway frontend-ip list"] = """
"type": |-
    command
"short-summary": |-
    List frontend IP addresses.
"""

helps["network vpn-connection ipsec-policy add"] = """
"type": |-
    command
"short-summary": |-
    Add a VPN connection IPSec policy.
"long-summary": |-
    Set all IPsec policies of a VPN connection. If you want to set any IPsec policy, you must set them all.
"""

helps["network nic ip-config list"] = """
"type": |-
    command
"short-summary": |-
    List the IP configurations of a NIC.
"""

helps["network application-gateway url-path-map"] = """
"type": |-
    group
"short-summary": |-
    Manage URL path maps of an application gateway.
"""

helps["network dns record-set cname delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a CNAME record set and its associated record.
"""

helps["network watcher connection-monitor delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a connection monitor for the given region.
"""

helps["network vnet-gateway list-learned-routes"] = """
"type": |-
    command
"short-summary": |-
    This operation retrieves a list of routes the virtual network gateway has learned, including routes learned from BGP peers.
"""

helps["network dns record-set a"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS A records.
"""

helps["network lb address-pool list"] = """
"type": |-
    command
"short-summary": |-
    List address pools.
"""

helps["network lb frontend-ip"] = """
"type": |-
    group
"short-summary": |-
    Manage frontend IP addresses of a load balancer.
"""

helps["network express-route auth show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a link authorization of an ExpressRoute circuit.
"""

helps["network route-table show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a route table.
"""

helps["network traffic-manager profile create"] = """
"type": |-
    command
"short-summary": |-
    Create a traffic manager profile.
"""

helps["network express-route peering list"] = """
"type": |-
    command
"short-summary": |-
    List peering settings of an ExpressRoute circuit.
"""

helps["network application-gateway url-path-map delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a URL path map.
"""

helps["network application-gateway url-path-map create"] = """
"type": |-
    command
"short-summary": |-
    Create a URL path map.
"long-summary": |
    The map must be created with at least one rule. This command requires the creation of the first rule at the time the map is created. To learn more visit https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-create-url-route-cli
"""

helps["network lb address-pool show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an address pool.
"""

helps["network route-filter delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a route filter.
"""

helps["network dns record-set ptr"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS PTR records.
"""

helps["network express-route auth create"] = """
"type": |-
    command
"short-summary": |-
    Create a new link authorization for an ExpressRoute circuit.
"""

helps["network dns record-set cname"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS CNAME records.
"""

helps["network vnet-gateway list-bgp-peer-status"] = """
"type": |-
    command
"short-summary": |-
    Retrieve the status of BGP peers.
"""

helps["network lb create"] = """
"type": |-
    command
"short-summary": |-
    Create a load balancer.
"""

helps["network vnet-gateway root-cert"] = """
"type": |-
    group
"short-summary": |-
    Manage root certificates of a virtual network gateway.
"""

helps["network dns record-set a list"] = """
"type": |-
    command
"short-summary": |-
    List all A record sets in a zone.
"""

helps["network application-gateway url-path-map rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a rule for a URL path map.
"""

helps["network dns record-set caa update"] = """
"type": |-
    command
"short-summary": |-
    Update a CAA record set.
"""

helps["network service-endpoint policy-definition list"] = """
"type": |-
    command
"short-summary": |-
    List service endpoint policy definitions.
"""

helps["network dns record-set ns list"] = """
"type": |-
    command
"short-summary": |-
    List all NS record sets in a zone.
"""

helps["network dns zone show"] = """
"type": |-
    command
"short-summary": |-
    Get a DNS zone parameters. Does not show DNS records within the zone.
"""

helps["network application-gateway http-settings update"] = """
"type": |-
    command
"short-summary": |-
    Update HTTP settings.
"""

helps["network watcher flow-log"] = """
"type": |-
    group
"short-summary": |-
    Manage network security group flow logging.
"long-summary": |
    For more information about configuring flow logs visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-cli
"""

helps["network vnet peering"] = """
"type": |-
    group
"short-summary": |-
    Manage peering connections between Azure Virtual Networks.
"long-summary": |-
    To learn more about virtual network peering visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering
"""

helps["network public-ip prefix delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a public IP prefix resource.
"""

helps["network asg update"] = """
"type": |-
    command
"short-summary": |-
    Update an application security group.
"long-summary": |
    This command can only be used to update the tags for an application security group. Name and resource group are immutable and cannot be updated.
"""

helps["network local-gateway show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a local VPN gateway.
"""

helps["network vpn-connection shared-key update"] = """
"type": |-
    command
"short-summary": |-
    Update a VPN connection shared key.
"""

helps["network traffic-manager profile update"] = """
"type": |-
    command
"short-summary": |-
    Update a traffic manager profile.
"""

helps["network lb inbound-nat-rule list"] = """
"type": |-
    command
"short-summary": |-
    List inbound NAT rules.
"""

helps["network lb delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a load balancer.
"""

helps["network route-table route show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a route in a route table.
"""

helps["network vnet subnet show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a subnet.
"examples":
-   "name": |-
        Show details of a subnet.
    "text": |-
        az network vnet subnet show --output json --name MySubnet --query [0] --vnet-name MyVNet --resource-group MyResourceGroup
"""

helps["network lb rule"] = """
"type": |-
    group
"short-summary": |-
    Manage load balancing rules.
"""

helps["network dns record-set cname create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty CNAME record set.
"""

helps["network express-route wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the ExpressRoute is met.
"""

helps["network dns record-set ptr update"] = """
"type": |-
    command
"short-summary": |-
    Update a PTR record set.
"""

helps["network vnet list"] = """
"type": |-
    command
"short-summary": |-
    List virtual networks.
"examples":
-   "name": |-
        List virtual networks.
    "text": |-
        az network vnet list --resource-group MyResourceGroup
"""

helps["network dns record-set caa list"] = """
"type": |-
    command
"short-summary": |-
    List all CAA record sets in a zone.
"""

helps["network express-route list"] = """
"type": |-
    command
"short-summary": |-
    List all ExpressRoute circuits for the current subscription.
"""

helps["network application-gateway auth-cert update"] = """
"type": |-
    command
"short-summary": |-
    Update an authorization certificate.
"""

helps["network watcher packet-capture delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a packet capture session.
"""

helps["network vnet-gateway list"] = """
"type": |-
    command
"short-summary": |-
    List virtual network gateways.
"""

helps["network nsg rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a network security group rule.
"examples":
-   "name": |-
        Create a network security group rule.
    "text": |-
        az network nsg rule create --access Allow --priority 100 --nsg-name MyNsg --destination-address-prefixes <destination-address-prefixes> --description <description> --name MyNsgRule --protocol * --resource-group MyResourceGroup --direction Inbound --destination-port-ranges <destination-port-ranges> --source-address-prefixes <source-address-prefixes>
"""

helps["network application-gateway probe list"] = """
"type": |-
    command
"short-summary": |-
    List probes.
"""

helps["network express-route auth"] = """
"type": |-
    group
"short-summary": |-
    Manage authentication of an ExpressRoute circuit.
"long-summary": |
    To learn more about ExpressRoute circuit authentication visit https://docs.microsoft.com/en-us/azure/expressroute/howto-linkvnet-cli#connect-a-virtual-network-in-a-different-subscription-to-a-circuit
"""

helps["network route-table delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a route table.
"""

helps["network dns zone"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS zones.
"""

helps["network vnet-gateway revoked-cert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a revoked certificate.
"""

helps["network public-ip prefix update"] = """
"type": |-
    command
"short-summary": |-
    Update a public IP prefix resource.
"""

helps["network nic ip-config create"] = """
"type": |-
    command
"short-summary": |-
    Create an IP configuration.
"long-summary": |
    You must have the Microsoft.Network/AllowMultipleIpConfigurationsPerNic feature enabled for your subscription. Only one configuration may be designated as the primary IP configuration per NIC, using the `--make-primary` flag.
"""

helps["network express-route peering connection delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an ExpressRoute circuit connection.
"""

helps["network traffic-manager endpoint list"] = """
"type": |-
    command
"short-summary": |-
    List traffic manager endpoints.
"""

helps["network application-gateway show-backend-health"] = """
"type": |-
    command
"short-summary": |-
    Get information on the backend health of an application gateway.
"""

helps["network service-endpoint policy-definition show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a service endpoint policy definition.
"""

helps["network watcher troubleshooting show"] = """
"type": |-
    command
"short-summary": |-
    Get the results of the last troubleshooting operation.
"""

helps["network application-gateway ssl-policy list-options"] = """
"type": |-
    command
"short-summary": |-
    Lists available SSL options for configuring SSL policy.
"""

helps["network application-gateway rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a rule.
"""

helps["network local-gateway list"] = """
"type": |-
    command
"short-summary": |-
    List all local VPN gateways in a resource group.
"""

helps["network route-filter rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a rule in a route filter.
"""

helps["network nsg create"] = """
"type": |-
    command
"short-summary": |-
    Create a network security group.
"examples":
-   "name": |-
        Create a network security group.
    "text": |-
        az network nsg create --resource-group MyResourceGroup --location westus2 --name MyNsg
"""

helps["network express-route peering delete"] = """
"type": |-
    command
"short-summary": |-
    Delete peering settings.
"""

helps["network express-route get-stats"] = """
"type": |-
    command
"short-summary": |-
    Get the statistics of an ExpressRoute circuit.
"""

helps["network application-gateway ssl-policy predefined show"] = """
"type": |-
    command
"short-summary": |-
    Gets SSL predefined policy with the specified policy name.
"""

helps["network route-table update"] = """
"type": |-
    command
"short-summary": |-
    Update a route table.
"""

helps["network application-gateway http-listener create"] = """
"type": |-
    command
"short-summary": |-
    Create an HTTP listener.
"""

helps["network vpn-connection delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a VPN connection.
"""

helps["network vnet-gateway revoked-cert"] = """
"type": |-
    group
"short-summary": |-
    Manage revoked certificates in a virtual network gateway.
"long-summary": |-
    Prevent machines using this certificate from accessing Azure through this gateway.
"""

helps["network public-ip show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a public IP address.
"""

helps["network application-gateway ssl-policy predefined"] = """
"type": |-
    group
"short-summary": |-
    Get information on predefined SSL policies.
"""

helps["network dns record-set srv add-record"] = """
"type": |-
    command
"short-summary": |-
    Add an SRV record.
"""

helps["network dns record-set mx add-record"] = """
"type": |-
    command
"short-summary": |-
    Add an MX record.
"""

helps["network watcher connection-monitor query"] = """
"type": |-
    command
"short-summary": |-
    Query a snapshot of the most recent connection state of a connection monitor.
"""

helps["network route-filter rule list-service-communities"] = """
"type": |-
    command
"short-summary": |-
    Gets all the available BGP service communities.
"""

helps["network express-route peering update"] = """
"type": |-
    command
"short-summary": |-
    Update peering settings of an ExpressRoute circuit.
"""

helps["network lb inbound-nat-pool list"] = """
"type": |-
    command
"short-summary": |-
    List inbound NAT address pools.
"""

helps["network application-gateway rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a rule.
"""

helps["network dns record-set ptr remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove a PTR record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network watcher packet-capture"] = """
"type": |-
    group
"short-summary": |-
    Manage packet capture sessions on VMs.
"long-summary": |
    These commands require that both Azure Network Watcher is enabled for the VMs region and that AzureNetworkWatcherExtension is enabled on the VM. For more information visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-packet-capture-manage-cli
"""

helps["network route-table list"] = """
"type": |-
    command
"short-summary": |-
    List route tables.
"""

helps["network service-endpoint policy"] = """
"type": |-
    group
"short-summary": |-
    Manage service endpoint policies.
"""

helps["network watcher connection-monitor create"] = """
"type": |-
    command
"short-summary": |-
    Create a connection monitor.
"parameters":
-   "name": |-
        --source-resource
    "short-summary": |
        Currently only Virtual Machines are supported.
-   "name": |-
        --dest-resource
    "short-summary": |
        Currently only Virtual Machines are supported.
"""

helps["network watcher configure"] = """
"type": |-
    command
"short-summary": |-
    Configure the Network Watcher service for different regions.
"parameters":
-   "name": |-
        --enabled
    "short-summary": |-
        Enabled status of Network Watcher in the specified regions.
-   "name": |-
        --locations -l
    "short-summary": |-
        Space-separated list of locations to configure.
-   "name": |-
        --resource-group -g
    "short-summary": |-
        Name of resource group. Required when enabling new regions.
    "long-summary": |
        When a previously disabled region is enabled to use Network Watcher, a
            Network Watcher resource will be created in this resource group.
"""

helps["network application-gateway ssl-cert update"] = """
"type": |-
    command
"short-summary": |-
    Update an SSL certificate.
"""

helps["network route-table route create"] = """
"type": |-
    command
"short-summary": |-
    Create a route in a route table.
"""

helps["network vnet check-ip-address"] = """
"type": |-
    command
"short-summary": |-
    Check if a private IP address is available for use within a virtual network.
"""

helps["network lb inbound-nat-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update an inbound NAT rule.
"""

helps["network watcher test-ip-flow"] = """
"type": |-
    command
"short-summary": |-
    Test IP flow to/from a VM given the currently configured network security group rules.
"long-summary": |
    Requires that Network Watcher is enabled for the region in which the VM is located. For more information visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-check-ip-flow-verify-cli
"parameters":
-   "name": |-
        --local
    "short-summary": |
        The private IPv4 address for the VMs NIC and the port of the packet in X.X.X.X:PORT format. `*` can be used for port when direction is outbound.
-   "name": |-
        --remote
    "short-summary": |
        The IPv4 address and port for the remote side of the packet X.X.X.X:PORT format. `*` can be used for port when the direction is inbound.
-   "name": |-
        --direction
    "short-summary": |-
        Direction of the packet relative to the VM.
-   "name": |-
        --protocol
    "short-summary": |-
        Protocol to test.
"""

helps["network lb inbound-nat-pool update"] = """
"type": |-
    command
"short-summary": |-
    Update an inbound NAT address pool.
"""

helps["network watcher show-next-hop"] = """
"type": |-
    command
"short-summary": |-
    Get information on the 'next hop' of a VM.
"long-summary": |
    Requires that Network Watcher is enabled for the region in which the VM is located. For more information about show-next-hop visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-check-next-hop-cli
"""

helps["network dns record-set ptr create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty PTR record set.
"""

helps["network asg delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an application security group.
"""

helps["network lb frontend-ip list"] = """
"type": |-
    command
"short-summary": |-
    List frontend IP addresses.
"""

helps["network nic ip-config delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an IP configuration.
"long-summary": |-
    A NIC must have at least one IP configuration.
"""

helps["network application-gateway http-settings list"] = """
"type": |-
    command
"short-summary": |-
    List HTTP settings.
"""

helps["network ddos-protection"] = """
"type": |-
    group
"short-summary": |-
    Manage DDoS Protection Plans.
"""

helps["network express-route show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an ExpressRoute circuit.
"""

helps["network lb probe"] = """
"type": |-
    group
"short-summary": |-
    Evaluate probe information and define routing rules.
"""

helps["network application-gateway frontend-port delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a frontend port.
"""

helps["network watcher packet-capture stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a running packet capture session.
"""

helps["network dns record-set caa"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS CAA records.
"""

helps["network express-route peering"] = """
"type": |-
    group
"short-summary": |-
    Manage ExpressRoute peering of an ExpressRoute circuit.
"""

helps["network interface-endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage interface endpoints.
"""

helps["network dns record-set srv remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove an SRV record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network nic ip-config"] = """
"type": |-
    group
"short-summary": |-
    Manage IP configurations of a network interface.
"""

helps["network vnet-gateway vpn-client show-url"] = """
"type": |-
    command
"short-summary": |-
    Retrieve a pre-generated VPN client configuration.
"long-summary": |-
    The profile needs to be generated first using vpn-client generate command.
"""

helps["network application-gateway address-pool list"] = """
"type": |-
    command
"short-summary": |-
    List address pools.
"""

helps["network lb outbound-rule list"] = """
"type": |-
    command
"short-summary": |-
    List outbound rules.
"""

helps["network nic ip-config address-pool"] = """
"type": |-
    group
"short-summary": |-
    Manage address pools in an IP configuration.
"""

helps["network vpn-connection show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a VPN connection.
"""

helps["network application-gateway auth-cert list"] = """
"type": |-
    command
"short-summary": |-
    List authorization certificates.
"""

helps["network express-route"] = """
"type": |-
    group
"short-summary": |-
    Manage dedicated private network fiber connections to Azure.
"long-summary": |
    To learn more about ExpressRoute circuits visit https://docs.microsoft.com/en-us/azure/expressroute/howto-circuit-cli
"""

helps["network private-endpoint list"] = """
"type": |-
    command
"short-summary": |-
    List private endpoints.
"""

helps["network nic update"] = """
"type": |-
    command
"short-summary": |-
    Update a network interface.
"examples":
-   "name": |-
        Update a network interface.
    "text": |-
        az network nic update --network-security-group MyNewNsg --name MyNic --resource-group MyResourceGroup
"""

helps["network profile list"] = """
"type": |-
    command
"short-summary": |-
    List network profiles.
"""

helps["network application-gateway rule list"] = """
"type": |-
    command
"short-summary": |-
    List rules.
"""

helps["network dns record-set ns create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty NS record set.
"""

helps["network express-route auth list"] = """
"type": |-
    command
"short-summary": |-
    List link authorizations of an ExpressRoute circuit.
"""

helps["network service-endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage policies related to service endpoints.
"""

helps["network dns zone create"] = """
"type": |-
    command
"short-summary": |-
    Create a DNS zone.
"parameters":
-   "name": |-
        --if-none-match
    "short-summary": |-
        Only create a DNS zone if one doesn't exist that matches the given name.
"examples":
-   "name": |-
        Create a DNS zone.
    "text": |-
        az network dns zone create --name www.mysite.com --resource-group MyResourceGroup
"""

helps["network application-gateway probe show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a probe.
"""

helps["network application-gateway root-cert"] = """
"type": |-
    group
"short-summary": |-
    Manage trusted root certificates of an application gateway.
"""

helps["network lb outbound-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create an outbound-rule.
"""

helps["network dns record-set aaaa update"] = """
"type": |-
    command
"short-summary": |-
    Update an AAAA record set.
"""

helps["network ddos-protection delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a DDoS protection plan.
"""

helps["network dns record-set a remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove an A record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network dns record-set caa delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a CAA record set and all associated records.
"""

helps["network application-gateway address-pool update"] = """
"type": |-
    command
"short-summary": |-
    Update an address pool.
"""

helps["network vnet peering update"] = """
"type": |-
    command
"short-summary": |-
    Update a peering.
"""

helps["network application-gateway frontend-ip delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a frontend IP address.
"""

helps["network nsg list"] = """
"type": |-
    command
"short-summary": |-
    List network security groups.
"""

helps["network local-gateway wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the local gateway is met.
"""

helps["network vpn-connection list"] = """
"type": |-
    command
"short-summary": |-
    List all VPN connections in a resource group.
"""

helps["network traffic-manager endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Traffic Manager end points.
"""

helps["network vnet-gateway root-cert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a root certificate.
"""

helps["network dns record-set soa show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an SOA record.
"""

helps["network application-gateway http-listener"] = """
"type": |-
    group
"short-summary": |-
    Manage HTTP listeners of an application gateway.
"""

helps["network dns record-set aaaa list"] = """
"type": |-
    command
"short-summary": |-
    List all AAAA record sets in a zone.
"""

helps["network vnet peering create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network peering connection.
"long-summary": |
    To successfully peer two virtual networks this command must be called twice with the values for --vnet-name and --remote-vnet reversed.
"examples":
-   "name": |-
        Create a virtual network peering connection.
    "text": |-
        az network vnet peering create --allow-vnet-access <allow-vnet-access> --resource-group MyResourceGroup --remote-vnet <remote-vnet> --vnet-name MyVnet --name MyVNetPeering
"""

helps["network nic ip-config address-pool remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an address pool of an IP configuration.
"""

helps["network traffic-manager profile show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a traffic manager profile.
"""

helps["network dns record-set cname remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove a CNAME record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network dns record-set txt update"] = """
"type": |-
    command
"short-summary": |-
    Update a TXT record set.
"""

helps["network vpn-connection update"] = """
"type": |-
    command
"short-summary": |-
    Update a VPN connection.
"""

helps["network watcher packet-capture list"] = """
"type": |-
    command
"short-summary": |-
    List all packet capture sessions within a resource group.
"""

helps["network route-filter"] = """
"type": |-
    group
"short-summary": |-
    (PREVIEW) Manage route filters.
"long-summary": |
    To learn more about route filters with Microsoft peering with ExpressRoute, visit https://docs.microsoft.com/en-us/azure/expressroute/how-to-routefilter-cli
"""

helps["network watcher troubleshooting"] = """
"type": |-
    group
"short-summary": |-
    Manage Network Watcher troubleshooting sessions.
"long-summary": |
    For more information on configuring troubleshooting visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-troubleshoot-manage-cli
"""

helps["network nsg rule"] = """
"type": |-
    group
"short-summary": |-
    Manage network security group rules.
"""

helps["network application-gateway frontend-port show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a frontend port.
"""

helps["network dns record-set ns show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an NS record set.
"""

helps["network nic ip-config inbound-nat-rule add"] = """
"type": |-
    command
"short-summary": |-
    Add an inbound NAT rule to an IP configuration.
"""

helps["network nsg update"] = """
"type": |-
    command
"short-summary": |-
    Update a network security group.
"long-summary": |
    This command can only be used to update the tags of an NSG. Name and resource group are immutable and cannot be updated.
"""

helps["network application-gateway auth-cert show"] = """
"type": |-
    command
"short-summary": |-
    Show an authorization certificate.
"""

helps["network express-route create"] = """
"type": |-
    command
"short-summary": |-
    Create an ExpressRoute circuit.
"parameters":
-   "name": |-
        --bandwidth
    "populator-commands":
    - |-
        az network express-route list-service-providers
-   "name": |-
        --peering-location
    "populator-commands":
    - |-
        az network express-route list-service-providers
-   "name": |-
        --provider
    "populator-commands":
    - |-
        az network express-route list-service-providers
"""

helps["network dns record-set mx delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an MX record set and all associated records.
"""

helps["network nic list-effective-nsg"] = """
"type": |-
    command
"short-summary": |-
    List all effective network security groups applied to a network interface.
"long-summary": |
    To learn more about troubleshooting using effective security rules visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-nsg-troubleshoot-portal
"""

helps["network dns record-set a delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an A record set and all associated records.
"""

helps["network dns record-set caa add-record"] = """
"type": |-
    command
"short-summary": |-
    Add a CAA record.
"""

helps["network lb address-pool"] = """
"type": |-
    group
"short-summary": |-
    Manage address pools of a load balancer.
"""

helps["network application-gateway http-listener delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an HTTP listener.
"""

helps["network dns zone export"] = """
"type": |-
    command
"short-summary": |-
    Export a DNS zone as a DNS zone file.
"examples":
-   "name": |-
        Export a DNS zone as a DNS zone file.
    "text": |-
        az network dns zone export --file-name MyFile --name www.mysite.com --resource-group MyResourceGroup
"""

helps["network public-ip prefix create"] = """
"type": |-
    command
"short-summary": |-
    Create a public IP prefix resource.
"""

helps["network express-route list-service-providers"] = """
"type": |-
    command
"short-summary": |-
    List available ExpressRoute service providers.
"""

helps["network application-gateway http-settings show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a gateway's HTTP settings.
"""

helps["network application-gateway root-cert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a trusted root certificate.
"""

helps["network application-gateway frontend-port"] = """
"type": |-
    group
"short-summary": |-
    Manage frontend ports of an application gateway.
"""

helps["network express-route auth delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a link authorization of an ExpressRoute circuit.
"""

helps["network dns"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS domains in Azure.
"""

helps["network watcher flow-log configure"] = """
"type": |-
    command
"short-summary": |-
    Configure flow logging on a network security group.
"parameters":
-   "name": |-
        --nsg
    "short-summary": |-
        Name or ID of the Network Security Group to target.
-   "name": |-
        --enabled
    "short-summary": |-
        Enable logging.
-   "name": |-
        --retention
    "short-summary": |-
        Number of days to retain logs.
-   "name": |-
        --storage-account
    "short-summary": |-
        Name or ID of the storage account in which to save the flow logs.
"""

helps["network traffic-manager endpoint delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a traffic manager endpoint.
"""

helps["network dns zone list"] = """
"type": |-
    command
"short-summary": |-
    List DNS zones.
"""

helps["network watcher show-topology"] = """
"type": |-
    command
"short-summary": |-
    Get the network topology of a resource group, virtual network or subnet.
"long-summary": |-
    For more information about using network topology visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-topology-cli
"parameters":
-   "name": |-
        --resource-group -g
    "short-summary": |-
        The name of the target resource group to perform topology on.
-   "name": |-
        --location -l
    "short-summary": |-
        Location. Defaults to the location of the target resource group.
    "long-summary": |
        Topology information is only shown for resources within the target resource group that are within the specified region.
"""

helps["network application-gateway address-pool create"] = """
"type": |-
    command
"short-summary": |-
    Create an address pool.
"""

helps["network application-gateway url-path-map update"] = """
"type": |-
    command
"short-summary": |-
    Update a URL path map.
"""

helps["network application-gateway http-settings"] = """
"type": |-
    group
"short-summary": |-
    Manage HTTP settings of an application gateway.
"""

helps["network vnet-gateway reset"] = """
"type": |-
    command
"short-summary": |-
    Reset a virtual network gateway.
"""

helps["network vnet subnet delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a subnet.
"""

helps["network application-gateway frontend-ip create"] = """
"type": |-
    command
"short-summary": |-
    Create a frontend IP address.
"""

helps["network dns record-set caa remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove a CAA record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network nic wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the network interface is met.
"""

helps["network vpn-connection ipsec-policy list"] = """
"type": |-
    command
"short-summary": |-
    List IPSec policies associated with a VPN connection.
"""

helps["network lb inbound-nat-pool show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an inbound NAT address pool.
"""

helps["network application-gateway delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an application gateway.
"""

helps["network vnet update"] = """
"type": |-
    command
"short-summary": |-
    Update a virtual network.
"""

helps["network ddos-protection list"] = """
"type": |-
    command
"short-summary": |-
    List DDoS protection plans.
"""

helps["network application-gateway ssl-cert"] = """
"type": |-
    group
"short-summary": |-
    Manage SSL certificates of an application gateway.
"long-summary": |-
    For more information visit https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-ssl-cli
"""

helps["network nic show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a network interface.
"examples":
-   "name": |-
        Get the details of a network interface.
    "text": |-
        az network nic show --query [0]
"""

helps["network nic list"] = """
"type": |-
    command
"short-summary": |-
    List network interfaces.
"long-summary": |
    To list network interfaces attached to VMs in VM scale sets use 'az vmss nic list' or 'az vmss nic list-vm-nics'.
"""

helps["network vpn-connection ipsec-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage VPN connection IPSec policies.
"""

helps["network lb list"] = """
"type": |-
    command
"short-summary": |-
    List load balancers.
"examples":
-   "name": |-
        List load balancers.
    "text": |-
        az network lb list --resource-group MyResourceGroup
"""

helps["network ddos-protection update"] = """
"type": |-
    command
"short-summary": |-
    Update a DDoS protection plan.
"parameters":
-   "name": |-
        --vnets
    "long-summary": |
        This parameter can only be used if all the VNets are within the same subscription as the DDoS protection plan. If this is not the case, set the protection plan on the VNet directly using the `az network vnet update` command.
"""

helps["network dns record-set srv show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an SRV record set.
"""

helps["network application-gateway root-cert update"] = """
"type": |-
    command
"short-summary": |-
    Update a trusted root certificate.
"""

helps["network dns record-set mx"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS MX records.
"""

helps["network application-gateway http-settings create"] = """
"type": |-
    command
"short-summary": |-
    Create HTTP settings.
"""

helps["network dns record-set ns"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS NS records.
"""

helps["network vnet-gateway revoked-cert create"] = """
"type": |-
    command
"short-summary": |-
    Revoke a certificate.
"""

helps["network public-ip delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a public IP address.
"""

helps["network application-gateway rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a rule.
"long-summary": |-
    Rules are executed in the order in which they are created.
"""

helps["network dns record-set ns delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an NS record set and all associated records.
"""

helps["network dns record-set a create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty A record set.
"""

helps["network dns record-set list"] = """
"type": |-
    command
"short-summary": |-
    List all record sets within a DNS zone.
"""

helps["network dns record-set mx update"] = """
"type": |-
    command
"short-summary": |-
    Update an MX record set.
"""

helps["network express-route peering connection show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an ExpressRoute circuit connection.
"""

helps["network dns record-set caa create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty CAA record set.
"""

helps["network dns record-set cname show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a CNAME record set.
"""

helps["network watcher connection-monitor start"] = """
"type": |-
    command
"short-summary": |-
    Start the specified connection monitor.
"""

helps["network dns record-set mx remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove an MX record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network express-route peering connection"] = """
"type": |-
    group
"short-summary": |-
    Manage ExpressRoute circuit connections.
"""

helps["network nsg rule list"] = """
"type": |-
    command
"short-summary": |-
    List all rules in a network security group.
"examples":
-   "name": |-
        List all rules in a network security group.
    "text": |-
        az network nsg rule list --output json --nsg-name MyNsg --resource-group MyResourceGroup
"""

helps["network watcher connection-monitor"] = """
"type": |-
    group
"short-summary": |-
    Manage connection monitoring between an Azure Virtual Machine and any IP resource.
"long-summary": |
    Connection monitor can be used to monitor network connectivity between an Azure virtual machine and an IP address.
     The IP address can be assigned to another Azure resource or a resource on the Internet or on-premises. To learn
     more visit https://aka.ms/connectionmonitordoc
"""

helps["network route-table route"] = """
"type": |-
    group
"short-summary": |-
    Manage routes in a route table.
"""

helps["network ddos-protection show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a DDoS protection plan.
"""

helps["network application-gateway waf-config list-rule-sets"] = """
"type": |-
    command
"short-summary": |-
    Get information on available WAF rule sets, rule groups, and rule IDs.
"parameters":
-   "name": |-
        --group
    "short-summary": |
        List rules for the specified rule group. Use `*` to list rules for all groups. Omit to suppress listing individual rules.
-   "name": |-
        --type
    "short-summary": |-
        Rule set type to list. Omit to list all types.
-   "name": |-
        --version
    "short-summary": |-
        Rule set version to list. Omit to list all versions.
"""

helps["network application-gateway frontend-port update"] = """
"type": |-
    command
"short-summary": |-
    Update a frontend port.
"""

helps["network lb frontend-ip update"] = """
"type": |-
    command
"short-summary": |-
    Update a frontend IP address.
"""

helps["network vpn-connection ipsec-policy clear"] = """
"type": |-
    command
"short-summary": |-
    Delete all IPsec policies on a VPN connection.
"""

helps["network vnet list-endpoint-services"] = """
"type": |-
    command
"short-summary": |-
    List which services support VNET service tunneling in a given region.
"long-summary": |-
    To learn more about service endpoints visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoints-configure#azure-cli
"""

helps["network dns zone delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a DNS zone and all associated records.
"""

helps["network vnet-gateway create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network gateway.
"""

helps["network application-gateway create"] = """
"type": |-
    command
"short-summary": |-
    Create an application gateway.
"""

helps["network dns record-set a add-record"] = """
"type": |-
    command
"short-summary": |-
    Add an A record.
"""

helps["network vnet peering delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a peering.
"examples":
-   "name": |-
        Delete a peering.
    "text": |-
        az network vnet peering delete --resource-group MyResourceGroup --vnet-name MyVnet1 --name MyVnet1ToMyVnet2
"""

helps["network lb probe update"] = """
"type": |-
    command
"short-summary": |-
    Update a probe.
"""

helps["network asg list"] = """
"type": |-
    command
"short-summary": |-
    List all application security groups in a subscription.
"""

helps["network public-ip prefix show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a public IP prefix resource.
"""

helps["network traffic-manager"] = """
"type": |-
    group
"short-summary": |-
    Manage the routing of incoming traffic.
"""

helps["network lb inbound-nat-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an inbound NAT rule.
"""

helps["network application-gateway url-path-map rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a rule of a URL path map.
"""

helps["network vnet subnet create"] = """
"type": |-
    command
"short-summary": |-
    Create a subnet and associate an existing NSG and route table.
"parameters":
-   "name": |-
        --service-endpoints
    "short-summary": |-
        Space-separated list of services allowed private access to this subnet.
    "populator-commands":
    - |-
        az network vnet list-endpoint-services
"examples":
-   "name": |-
        Create a subnet and associate an existing NSG and route table.
    "text": |-
        az network vnet subnet create --resource-group MyResourceGroup --address-prefixes <address-prefixes> --vnet-name MyVnet --name MySubnet
"""

helps["network watcher test-connectivity"] = """
"type": |-
    command
"short-summary": |-
    (PREVIEW) Test if a connection can be established between a Virtual Machine and a given endpoint.
"long-summary": |
    To check connectivity between two VMs in different regions, use the VM ids instead of the VM names for the source and destination resource arguments. To register for this feature or see additional examples visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-connectivity-cli
"parameters":
-   "name": |-
        --source-resource
    "short-summary": |-
        Name or ID of the resource from which to originate traffic.
    "long-summary": |-
        Currently only Virtual Machines are supported.
-   "name": |-
        --source-port
    "short-summary": |-
        Port number from which to originate traffic.
-   "name": |-
        --dest-resource
    "short-summary": |-
        Name or ID of the resource to receive traffic.
    "long-summary": |-
        Currently only Virtual Machines are supported.
-   "name": |-
        --dest-port
    "short-summary": |-
        Port number on which to receive traffic.
-   "name": |-
        --dest-address
    "short-summary": |-
        The IP address or URI at which to receive traffic.
"""

helps["network vpn-connection shared-key"] = """
"type": |-
    group
"short-summary": |-
    Manage VPN shared keys.
"""

helps["network application-gateway probe update"] = """
"type": |-
    command
"short-summary": |-
    Update a probe.
"""

helps["network watcher packet-capture show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a packet capture session.
"""

helps["network dns record-set txt delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a TXT record set and all associated records.
"""

helps["network lb outbound-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update an outbound-rule.
"""

helps["network application-gateway address-pool delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an address pool.
"""

helps["network public-ip create"] = """
"type": |-
    command
"short-summary": |-
    Create a public IP address.
"""

helps["network private-endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage private endpoints.
"""

helps["network lb inbound-nat-pool delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an inbound NAT address pool.
"""

helps["network route-table"] = """
"type": |-
    group
"short-summary": |-
    Manage route tables.
"""

helps["network application-gateway ssl-cert show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an SSL certificate.
"""

helps["network application-gateway probe"] = """
"type": |-
    group
"short-summary": |-
    Manage probes to gather and evaluate information on a gateway.
"""

helps["network local-gateway"] = """
"type": |-
    group
"short-summary": |-
    Manage local gateways.
"long-summary": |
    For more information on local gateways, visit: https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-cli#localnet
"""

helps["network nic ip-config inbound-nat-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage inbound NAT rules of an IP configuration.
"""

helps["network vpn-connection shared-key reset"] = """
"type": |-
    command
"short-summary": |-
    Reset a VPN connection shared key.
"""

helps["network nic ip-config show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of an IP configuration.
"""

helps["network vnet-gateway list-advertised-routes"] = """
"type": |-
    command
"short-summary": |-
    List the routes of a virtual network gateway advertised to the specified peer.
"""

helps["network dns record-set aaaa show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an AAAA record set.
"""

helps["network lb inbound-nat-rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an inbound NAT rule.
"""

helps["network lb inbound-nat-pool create"] = """
"type": |-
    command
"short-summary": |-
    Create an inbound NAT address pool.
"""

helps["network local-gateway delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a local VPN gateway.
"long-summary": |
    In order to delete a Local Network Gateway, you must first delete ALL Connection objects in Azure that are connected to the Gateway. After deleting the Gateway, proceed to delete other resources now not in use. For more information, follow the order of instructions on this page: https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-delete-vnet-gateway-portal
"""

helps["network dns record-set txt add-record"] = """
"type": |-
    command
"short-summary": |-
    Add a TXT record.
"""

helps["network route-filter rule"] = """
"type": |-
    group
"short-summary": |-
    (PREVIEW) Manage rules in a route filter.
"long-summary": |
    To learn more about route filters with Microsoft peering with ExpressRoute, visit https://docs.microsoft.com/en-us/azure/expressroute/how-to-routefilter-cli
"""

helps["network service-endpoint policy show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a service endpoint policy.
"""

helps["network application-gateway root-cert create"] = """
"type": |-
    command
"short-summary": |-
    Upload a trusted root certificate.
"""

helps["network lb frontend-ip delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a frontend IP address.
"""

helps["network service-endpoint policy create"] = """
"type": |-
    command
"short-summary": |-
    Create a service endpoint policy.
"""

helps["network"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Network resources.
"""

helps["network application-gateway frontend-ip update"] = """
"type": |-
    command
"short-summary": |-
    Update a frontend IP address.
"""

helps["network dns record-set soa update"] = """
"type": |-
    command
"short-summary": |-
    Update properties of an SOA record.
"""

helps["network lb frontend-ip create"] = """
"type": |-
    command
"short-summary": |-
    Create a frontend IP address.
"""

helps["network dns record-set srv create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty SRV record set.
"""

helps["network vnet subnet list-available-delegations"] = """
"type": |-
    command
"short-summary": |-
    List the services available for subnet delegation.
"""

helps["network vnet subnet update"] = """
"type": |-
    command
"short-summary": |-
    Update a subnet.
"parameters":
-   "name": |-
        --service-endpoints
    "short-summary": |-
        Space-separated list of services allowed private access to this subnet.
    "populator-commands":
    - |-
        az network vnet list-endpoint-services
"examples":
-   "name": |-
        Update a subnet.
    "text": |-
        az network vnet subnet update --network-security-group MyNsg --resource-group MyResourceGroup --vnet-name MyVNet --name MySubnet
"""

helps["network express-route peering show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an express route peering.
"""

helps["network dns record-set a show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an A record set.
"""

helps["network lb address-pool create"] = """
"type": |-
    command
"short-summary": |-
    Create an address pool.
"""

helps["network dns zone import"] = """
"type": |-
    command
"short-summary": |-
    Create a DNS zone using a DNS zone file.
"examples":
-   "name": |-
        Create a DNS zone using a DNS zone file.
    "text": |-
        az network dns zone import --file-name /path/to/zone/file --name MyZone --resource-group MyResourceGroup
"""

helps["network traffic-manager profile delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a traffic manager profile.
"""

helps["network watcher"] = """
"type": |-
    group
"short-summary": |-
    Manage the Azure Network Watcher.
"long-summary": |
    Network Watcher assists with monitoring and diagnosing conditions at a network scenario level. To learn more visit https://docs.microsoft.com/en-us/azure/network-watcher/
"""

helps["network public-ip prefix list"] = """
"type": |-
    command
"short-summary": |-
    List public IP prefix resources.
"""

helps["network route-filter update"] = """
"type": |-
    command
"short-summary": |-
    Update a route filter.
"long-summary": |
    This command can only be used to update the tags for a route filter. Name and resource group are immutable and cannot be updated.
"""

helps["network application-gateway ssl-policy predefined list"] = """
"type": |-
    command
"short-summary": |-
    Lists all SSL predefined policies for configuring SSL policy.
"""

helps["network dns record-set aaaa remove-record"] = """
"type": |-
    command
"short-summary": |-
    Remove AAAA record from its record set.
"long-summary": |
    By default, if the last record in a set is removed, the record set is deleted. To retain the empty record set, include --keep-empty-record-set.
"""

helps["network application-gateway ssl-cert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an SSL certificate.
"""

helps["network lb update"] = """
"type": |-
    command
"short-summary": |-
    Update a load balancer.
"long-summary": |
    This command can only be used to update the tags for a load balancer. Name and resource group are immutable and cannot be updated.
"""

helps["network application-gateway root-cert list"] = """
"type": |-
    command
"short-summary": |-
    List trusted root certificates.
"""

helps["network nic delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a network interface.
"examples":
-   "name": |-
        Delete a network interface.
    "text": |-
        az network nic delete --resource-group MyResourceGroup --name MyNic
"""

helps["network interface-endpoint list"] = """
"type": |-
    command
"short-summary": |-
    List interface endpoints.
"""

helps["network service-endpoint policy-definition"] = """
"type": |-
    group
"short-summary": |-
    Manage service endpoint policy definitions.
"""

helps["network public-ip update"] = """
"type": |-
    command
"short-summary": |-
    Update a public IP address.
"""

helps["network nsg rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a network security group rule.
"examples":
-   "name": |-
        Delete a network security group rule.
    "text": |-
        az network nsg rule delete --nsg-name MyNsg --name MyNsgRule --resource-group MyResourceGroup
"""

helps["network application-gateway http-listener update"] = """
"type": |-
    command
"short-summary": |-
    Update an HTTP listener.
"""

helps["network application-gateway address-pool"] = """
"type": |-
    group
"short-summary": |-
    Manage address pools of an application gateway.
"""

helps["network vnet show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a virtual network.
"examples":
-   "name": |-
        Get the details of a virtual network.
    "text": |-
        az network vnet show --resource-group MyResourceGroup --output json --name MyVNet
"""

helps["network dns record-set txt"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS TXT records.
"""

helps["network public-ip list"] = """
"type": |-
    command
"short-summary": |-
    List public IP addresses.
"""

helps["network application-gateway redirect-config"] = """
"type": |-
    group
"short-summary": |-
    Manage redirect configurations.
"""

helps["network lb rule list"] = """
"type": |-
    command
"short-summary": |-
    List load balancing rules.
"examples":
-   "name": |-
        List load balancing rules.
    "text": |-
        az network lb rule list --lb-name MyLb --resource-group MyResourceGroup
"""

helps["network lb rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a load balancing rule.
"""

helps["network lb"] = """
"type": |-
    group
"short-summary": |-
    Manage and configure load balancers.
"long-summary": |-
    To learn more about Azure Load Balancer visit https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-get-started-internet-arm-cli
"""

helps["network route-filter show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a route filter.
"""

helps["network dns record-set mx show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an MX record set.
"""

helps["network lb inbound-nat-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create an inbound NAT rule.
"""

helps["network application-gateway probe create"] = """
"type": |-
    command
"short-summary": |-
    Create a probe.
"""

helps["network vpn-connection"] = """
"type": |-
    group
"short-summary": |-
    Manage VPN connections.
"long-summary": |
    For more information on site-to-site connections, visit https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-cli. For more information on Vnet-to-Vnet connections, visit https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-howto-vnet-vnet-cli
"""

helps["network application-gateway redirect-config create"] = """
"type": |-
    command
"short-summary": |-
    Create a redirect configuration.
"""

helps["network dns record-set cname set-record"] = """
"type": |-
    command
"short-summary": |-
    Set the value of a CNAME record.
"""

helps["network dns record-set ns add-record"] = """
"type": |-
    command
"short-summary": |-
    Add an NS record.
"""

helps["network interface-endpoint show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an interface endpoint.
"""

helps["network dns record-set cname list"] = """
"type": |-
    command
"short-summary": |-
    List the CNAME record set in a zone.
"""

helps["network vnet subnet list"] = """
"type": |-
    command
"short-summary": |-
    List the subnets in a virtual network.
"examples":
-   "name": |-
        List the subnets in a virtual network.
    "text": |-
        az network vnet subnet list --vnet-name MyVNet --resource-group MyResourceGroup
"""

helps["network dns zone update"] = """
"type": |-
    command
"short-summary": |-
    Update a DNS zone properties. Does not modify DNS records within the zone.
"parameters":
-   "name": |-
        --if-match
    "short-summary": |-
        Update only if the resource with the same ETAG exists.
"""

helps["network vnet-gateway root-cert create"] = """
"type": |-
    command
"short-summary": |-
    Upload a root certificate.
"""

helps["network dns record-set aaaa add-record"] = """
"type": |-
    command
"short-summary": |-
    Add an AAAA record.
"""

helps["network service-endpoint policy update"] = """
"type": |-
    command
"short-summary": |-
    Update a service endpoint policy.
"""

helps["network lb probe create"] = """
"type": |-
    command
"short-summary": |-
    Create a probe.
"examples":
-   "name": |-
        Create a probe.
    "text": |-
        az network lb probe create --protocol Http --port <port> --name MyProbe --lb-name MyLb --resource-group MyResourceGroup
"""

helps["network application-gateway rule"] = """
"type": |-
    group
"short-summary": |-
    Evaluate probe information and define routing rules.
"long-summary": |
    For more information, visit, https://docs.microsoft.com/en-us/azure/application-gateway/application-gateway-customize-waf-rules-cli
"""

helps["network lb rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a load balancing rule.
"examples":
-   "name": |-
        Create a load balancing rule.
    "text": |-
        az network lb rule create --probe-name MyProbe --backend-pool-name MyBackendPool --name MyLoadBalancingRule --resource-group MyResourceGroup --protocol All --backend-port <backend-port> --lb-name MyLb --frontend-port <frontend-port>
"""

helps["network vnet peering list"] = """
"type": |-
    command
"short-summary": |-
    List peerings.
"examples":
-   "name": |-
        List peerings.
    "text": |-
        az network vnet peering list --vnet-name MyVnet1 --resource-group MyResourceGroup
"""

helps["network lb inbound-nat-pool"] = """
"type": |-
    group
"short-summary": |-
    Manage inbound NAT address pools of a load balancer.
"""

helps["network application-gateway url-path-map list"] = """
"type": |-
    command
"short-summary": |-
    List URL path maps.
"""

helps["network watcher show-security-group-view"] = """
"type": |-
    command
"short-summary": |-
    Get detailed security information on a VM for the currently configured network security group.
"long-summary": |
    For more information on using security group view visit https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-security-group-view-cli
"""

helps["network watcher connection-monitor show"] = """
"type": |-
    command
"short-summary": |-
    Shows a connection monitor by name.
"""

helps["network application-gateway auth-cert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an authorization certificate.
"""

helps["network watcher connection-monitor list"] = """
"type": |-
    command
"short-summary": |-
    List connection monitors for the given region.
"""

helps["network vpn-connection shared-key show"] = """
"type": |-
    command
"short-summary": |-
    Retrieve a VPN connection shared key.
"""

helps["network vnet-gateway delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a virtual network gateway.
"long-summary": |
    In order to delete a Virtual Network Gateway, you must first delete ALL Connection objects in Azure that are
     connected to the Gateway. After deleting the Gateway, proceed to delete other resources now not in use.
     For more information, follow the order of instructions on this page:
     https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-delete-vnet-gateway-portal
"""

helps["network watcher list"] = """
"type": |-
    command
"short-summary": |-
    List Network Watchers.
"""

helps["network service-endpoint policy-definition create"] = """
"type": |-
    command
"short-summary": |-
    Create a service endpoint policy definition.
"parameters":
-   "name": |-
        --service
    "populator-commands":
    - |-
        az network service-endpoint list
"""

helps["network dns record-set mx list"] = """
"type": |-
    command
"short-summary": |-
    List all MX record sets in a zone.
"""

helps["network vnet-gateway"] = """
"type": |-
    group
"short-summary": |-
    Use an Azure Virtual Network Gateway to establish secure, cross-premises connectivity.
"long-summary": |
    To learn more about Azure Virtual Network Gateways, visit https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-cli
"""

helps["network nsg rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a network security group rule.
"examples":
-   "name": |-
        Get the details of a network security group rule.
    "text": |-
        az network nsg rule show --resource-group MyResourceGroup --nsg-name MyNsg --query [0] --name MyNsgRule
"""

helps["network application-gateway update"] = """
"type": |-
    command
"short-summary": |-
    Update an application gateway.
"""

helps["network private-endpoint show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an private endpoint.
"""

helps["network application-gateway auth-cert"] = """
"type": |-
    group
"short-summary": |-
    Manage authorization certificates of an application gateway.
"""

helps["network traffic-manager endpoint show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a traffic manager endpoint.
"""

helps["network route-filter rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a rule from a route filter.
"""

helps["network dns record-set txt create"] = """
"type": |-
    command
"short-summary": |-
    Create an empty TXT record set.
"""

helps["network lb outbound-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an outbound-rule.
"""

helps["network service-endpoint policy list"] = """
"type": |-
    command
"short-summary": |-
    List service endpoint policies.
"""

helps["network nsg"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Network Security Groups (NSGs).
"long-summary": |
    You can control network traffic to resources in a virtual network using a network security group. A network security group contains a list of security rules that allow or deny inbound or outbound network traffic based on source or destination IP addresses, Application Security Groups, ports, and protocols. For more information visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-networks-create-nsg-arm-cli
"""

helps["network nic ip-config inbound-nat-rule remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an inbound NAT rule of an IP configuration.
"""

helps["network profile show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a network profile.
"""

helps["network application-gateway ssl-policy show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of gateway's SSL policy settings.
"""

helps["network dns record-set soa"] = """
"type": |-
    group
"short-summary": |-
    Manage a DNS SOA record.
"""

helps["network application-gateway list"] = """
"type": |-
    command
"short-summary": |-
    List application gateways.
"""

helps["network profile delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a network profile.
"""

helps["network application-gateway wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the application gateway is met.
"""

helps["network lb inbound-nat-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage inbound NAT rules of a load balancer.
"""

helps["network traffic-manager endpoint create"] = """
"type": |-
    command
"short-summary": |-
    Create a traffic manager endpoint.
"parameters":
-   "name": |-
        --geo-mapping
    "populator-commands":
    - |-
        az network traffic-manager endpoint show-geographic-hierarchy
"""

helps["network traffic-manager profile check-dns"] = """
"type": |-
    command
"short-summary": |-
    Check the availability of a relative DNS name.
"long-summary": |-
    This checks for the avabilility of dns prefixes for trafficmanager.net.
"""

helps["network application-gateway waf-config show"] = """
"type": |-
    command
"short-summary": |-
    Get the firewall configuration of a web application.
"""

helps["network vnet-gateway vpn-client"] = """
"type": |-
    group
"short-summary": |-
    Download a VPN client configuration required to connect to Azure via point-to-site.
"""

helps["network service-endpoint policy-definition delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a service endpoint policy definition.
"""

helps["network lb outbound-rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an outbound rule.
"""

helps["network vnet delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a virtual network.
"examples":
-   "name": |-
        Delete a virtual network.
    "text": |-
        az network vnet delete --name myVNet --resource-group MyResourceGroup
"""

helps["network route-table route list"] = """
"type": |-
    command
"short-summary": |-
    List routes in a route table.
"""

helps["network watcher packet-capture create"] = """
"type": |-
    command
"short-summary": |-
    Create and start a packet capture session.
"parameters":
-   "name": |-
        --capture-limit
    "short-summary": |-
        The maximum size in bytes of the capture output.
-   "name": |-
        --capture-size
    "short-summary": |-
        Number of bytes captured per packet. Excess bytes are truncated.
-   "name": |-
        --time-limit
    "short-summary": |-
        Maximum duration of the capture session in seconds.
-   "name": |-
        --storage-account
    "short-summary": |-
        Name or ID of a storage account to save the packet capture to.
-   "name": |-
        --storage-path
    "short-summary": |-
        Fully qualified URI of an existing storage container in which to store the capture file.
    "long-summary": |
        If not specified, the container 'network-watcher-logs' will be created if it does not exist and the capture file will be stored there.
-   "name": |-
        --file-path
    "short-summary": |
        Local path on the targeted VM at which to save the packet capture. For Linux VMs, the path must start with /var/captures.
-   "name": |-
        --vm
    "short-summary": |-
        Name or ID of the VM to target.
-   "name": |-
        --filters
    "short-summary": |-
        JSON encoded list of packet filters. Use `@{path}` to load from file.
"""

helps["network nic ip-config update"] = """
"type": |-
    command
"short-summary": |-
    Update an IP configuration.
"""

helps["network application-gateway redirect-config delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a redirect configuration.
"""

helps["network express-route delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an ExpressRoute circuit.
"""

helps["network dns record-set caa show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a CAA record set.
"""

helps["network watcher run-configuration-diagnostic"] = """
"type": |-
    command
"short-summary": |-
    Run a configuration diagnostic on a target resource.
"long-summary": |
    Requires that Network Watcher is enabled for the region in which the target is located.
"""

helps["network application-gateway frontend-ip"] = """
"type": |-
    group
"short-summary": |-
    Manage frontend IP addresses of an application gateway.
"""

helps["network application-gateway frontend-port create"] = """
"type": |-
    command
"short-summary": |-
    Create a frontend port.
"""

helps["network profile"] = """
"type": |-
    group
"short-summary": |-
    Manage network profiles.
"long-summary": |
    To create a network profile, see the create command for the relevant resource. Currently, only Azure Container Instances are supported.
"""

helps["network application-gateway redirect-config show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a redirect configuration.
"""

helps["network vnet subnet"] = """
"type": |-
    group
"short-summary": |-
    Manage subnets in an Azure Virtual Network.
"long-summary": |-
    To learn more about subnets visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-subnet
"""

helps["network dns record-set"] = """
"type": |-
    group
"short-summary": |-
    Manage DNS records and record sets.
"""

helps["network dns record-set srv list"] = """
"type": |-
    command
"short-summary": |-
    List all SRV record sets in a zone.
"""

helps["network watcher packet-capture show-status"] = """
"type": |-
    command
"short-summary": |-
    Show the status of a packet capture session.
"""

helps["network watcher connection-monitor stop"] = """
"type": |-
    command
"short-summary": |-
    Stop the specified connection monitor.
"""

helps["network traffic-manager endpoint update"] = """
"type": |-
    command
"short-summary": |-
    Update a traffic manager endpoint.
"""

helps["network watcher flow-log show"] = """
"type": |-
    command
"short-summary": |-
    Get the flow log configuration of a network security group.
"""

helps["network lb probe delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a probe.
"examples":
-   "name": |-
        Delete a probe.
    "text": |-
        az network lb probe delete --name MyProbe --lb-name MyLb --resource-group MyResourceGroup
"""

helps["network application-gateway url-path-map show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a URL path map.
"""

helps["network application-gateway http-settings delete"] = """
"type": |-
    command
"short-summary": |-
    Delete HTTP settings.
"""

helps["network nsg rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a network security group rule.
"examples":
-   "name": |-
        Update a network security group rule.
    "text": |-
        az network nsg rule update --resource-group MyResourceGroup --access Allow --nsg-name MyNsg --source-address-prefixes <source-address-prefixes> --name MyNsgRule
"""

helps["network application-gateway frontend-ip show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a frontend IP address.
"""

helps["network route-table create"] = """
"type": |-
    command
"short-summary": |-
    Create a route table.
"""

helps["network vnet"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Virtual Networks.
"long-summary": |-
    To learn more about Virtual Networks visit https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-network
"examples":
-   "name": |-
        Get the details of a virtual network gateway.
    "text": |-
        az network vnet-gateway show --resource-group MyResourceGroup --name MyVnetGateway
-   "name": |-
        List virtual network gateways.
    "text": |-
        az network vnet-gateway list --resource-group MyResourceGroup
"""

helps["network public-ip prefix"] = """
"type": |-
    group
"short-summary": |-
    Manage public IP prefix resources.
"""

helps["network ddos-protection create"] = """
"type": |-
    command
"short-summary": |-
    Create a DDoS protection plan.
"parameters":
-   "name": |-
        --vnets
    "long-summary": |
        This parameter can only be used if all the VNets are within the same subscription as the DDoS protection plan. If this is not the case, set the protection plan on the VNet directly using the `az network vnet update` command.
"""

helps["network dns record-set srv delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an SRV record set and all associated records.
"""

