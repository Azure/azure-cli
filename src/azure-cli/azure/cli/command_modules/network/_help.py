# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['network'] = """
type: group
short-summary: Manage Azure Network resources.
"""

helps['network application-gateway'] = """
type: group
short-summary: Manage application-level routing and load balancing services.
long-summary: To learn more about Application Gateway, visit https://docs.microsoft.com/azure/application-gateway/application-gateway-create-gateway-cli
"""

helps['network application-gateway address-pool'] = """
type: group
short-summary: Manage address pools of an application gateway.
"""

helps['network application-gateway address-pool create'] = """
type: command
short-summary: Create an address pool.
examples:
  - name: Create an address pool with two endpoints.
    text: |
        az network application-gateway address-pool create -g MyResourceGroup \\
            --gateway-name MyAppGateway -n MyAddressPool --servers 10.0.0.4 10.0.0.5
"""

helps['network application-gateway address-pool delete'] = """
type: command
short-summary: Delete an address pool.
examples:
  - name: Delete an address pool.
    text: az network application-gateway address-pool delete -g MyResourceGroup --gateway-name MyAppGateway -n MyAddressPool
"""

helps['network application-gateway address-pool list'] = """
type: command
short-summary: List address pools.
examples:
  - name: List address pools.
    text: az network application-gateway address-pool list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway address-pool show'] = """
type: command
short-summary: Get the details of an address pool.
examples:
  - name: Get the details of an address pool.
    text: az network application-gateway address-pool show -g MyResourceGroup --gateway-name MyAppGateway -n MyAddressPool
"""

helps['network application-gateway address-pool update'] = """
type: command
short-summary: Update an address pool.
examples:
  - name: Update backend address pool.
    text: az network application-gateway address-pool update -g MyResourceGroup --gateway-name MyAppGateway \\ -n MyAddressPool --servers 10.0.0.4 10.0.0.5 10.0.0.6
  - name: Add to the backend address pool by using backend server IP address.
    text: |
        az network application-gateway address-pool update -g MyResourceGroup --gateway-name MyAppGateway -n MyAddressPool \\
            --add backendAddresses ipAddress=10.0.0.4
  - name: Remove an existing ip of the backend address pool("0" is the index).
    text: |
        az network application-gateway address-pool update -g MyResourceGroup --gateway-name MyAppGateway -n MyAddressPool \\
            --remove backendAddresses 0
"""

helps['network application-gateway auth-cert'] = """
type: group
short-summary: Manage authorization certificates of an application gateway.
"""

helps['network application-gateway auth-cert create'] = """
type: command
short-summary: Create an authorization certificate.
examples:
  - name: Create an authorization certificate.
    text: |
        az network application-gateway auth-cert create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyAuthCert --cert-file /path/to/cert/file
"""

helps['network application-gateway auth-cert delete'] = """
type: command
short-summary: Delete an authorization certificate.
examples:
  - name: Delete an authorization certificate.
    text: az network application-gateway auth-cert delete -g MyResourceGroup --gateway-name MyAppGateway -n MyAuthCert
"""

helps['network application-gateway auth-cert list'] = """
type: command
short-summary: List authorization certificates.
examples:
  - name: List authorization certificates.
    text: az network application-gateway auth-cert list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway auth-cert show'] = """
type: command
short-summary: Show an authorization certificate.
examples:
  - name: Show an authorization certificate.
    text: az network application-gateway auth-cert show -g MyResourceGroup --gateway-name MyAppGateway -n MyAuthCert
  - name: View expiry date of an authorization certificate. It is in Base-64 encoded X.509(.CER) format.
    text: |
        az network application-gateway auth-cert show -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyAuthCert --query data -o tsv | base64 -d | openssl x509 -enddate -noout
"""

helps['network application-gateway auth-cert update'] = """
type: command
short-summary: Update an authorization certificate.
examples:
  - name: Update authorization certificates to use a new cert file.
    text: az network application-gateway auth-cert update -g MyResourceGroup --gateway-name MyAppGateway \\ -n MyAuthCert --cert-file /path/to/new/cert/file
"""

helps['network application-gateway create'] = """
type: command
short-summary: Create an application gateway.
parameters:
  - name: --trusted-client-cert
    short-summary: The application gateway trusted client certificate.
    long-summary: |
        Usage: --trusted-client-certificates name=client1 data=client.cer

        name: Required. Name of the trusted client certificate that is unique within an Application Gateway
        data: Required. Certificate public data.

        Multiple trusted client certificates can be specified by using more than one `--trusted-client-certificates` argument.
  - name: --ssl-profile
    short-summary: The application gateway ssl profiles.
    long-summary: |
        Usage: --ssl-profile name=MySslProfile client-auth-configuration=True cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 policy-type=Custom min-protocol-version=TLSv1_0

        name: Required. Name of the SSL profile that is unique within an Application Gateway.
        polic-name: Name of Ssl Policy.
        policy-type: Type of Ssl Policy.
        min-protocol-version: Minimum version of Ssl protocol to be supported on application gateway.
        cipher-suites: Ssl cipher suites to be enabled in the specified order to application gateway.
        disabled-ssl-protocols: Space-separated list of protocols to disable.
        trusted-client-certificates: Array of references to application gateway trusted client certificates.
        client-auth-configuration: Client authentication configuration of the application gateway resource.

        Multiple ssl profiles can be specified by using more than one `--ssl-profile` argument.

examples:
  - name: Create an application gateway with VMs as backend servers.
    text: |
        az network application-gateway create -g MyResourceGroup -n MyAppGateway --capacity 2 --sku Standard_Medium \\
            --vnet-name MyVNet --subnet MySubnet --http-settings-cookie-based-affinity Enabled \\
            --public-ip-address MyAppGatewayPublicIp --servers 10.0.0.4 10.0.0.5
  - name: Create an application gateway. (autogenerated)
    text: |
        az network application-gateway create --capacity 2 --frontend-port MyFrontendPort --http-settings-cookie-based-affinity Enabled --http-settings-port 80 --http-settings-protocol Http --location westus2 --name MyAppGateway --public-ip-address MyAppGatewayPublicIp --resource-group MyResourceGroup --sku Standard_Small --subnet MySubnet --vnet-name MyVNet
    crafted: true
"""

helps['network application-gateway delete'] = """
type: command
short-summary: Delete an application gateway.
examples:
  - name: Delete an application gateway.
    text: az network application-gateway delete -g MyResourceGroup -n MyAppGateway
"""

helps['network application-gateway private-link'] = """
type: group
short-summary: Manage Private Link of an Application Gateway
"""

helps['network application-gateway private-link add'] = """
type: command
short-summary: Add a new Private Link with a default IP Configuration and associate it with an existing Frontend IP
"""

helps['network application-gateway private-link remove'] = """
type: command
short-summary: Remove a Private Link and clear association with Frontend IP. The subnet associate with a Private Link might need to clear manually
"""

helps['network application-gateway private-link show'] = """
type: command
short-summary: Show a Private Link
"""

helps['network application-gateway private-link list'] = """
type: command
short-summary: List all the Private Link
"""

helps['network application-gateway private-link wait'] = """
type: command
short-summary: Place the CLI in a waiting state until the condition of corresponding application gateway is met
"""

helps['network application-gateway private-link ip-config'] = """
type: group
short-summary: Manage IP configuration of a Private Link to configure its capability
"""

helps['network application-gateway private-link ip-config add'] = """
type: command
short-summary: Add an IP configuration to a Private Link to scale up its capability
"""

helps['network application-gateway private-link ip-config remove'] = """
type: command
short-summary: Remove an IP configuration from a Private Link to scale down its capability
"""

helps['network application-gateway private-link ip-config show'] = """
type: command
short-summary: Show an IP configuration of a Private Link
"""

helps['network application-gateway private-link ip-config list'] = """
type: command
short-summary: List all the IP configuration of a Private Link
"""

helps['network application-gateway private-link ip-config wait'] = """
type: command
short-summary: Place the CLI in a waiting state until the condition of corresponding application gateway is met
"""

helps['network application-gateway frontend-ip'] = """
type: group
short-summary: Manage frontend IP addresses of an application gateway.
"""

helps['network application-gateway frontend-ip create'] = """
type: command
short-summary: Create a frontend IP address.
examples:
  - name: Create a frontend IP address.
    text: |
        az network application-gateway frontend-ip create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyFrontendIp --public-ip-address MyPublicIpAddress
  - name: Create a frontend IP address. (autogenerated)
    text: |
        az network application-gateway frontend-ip create --gateway-name MyAppGateway --name MyFrontendIp --private-ip-address 10.10.10.50 --resource-group MyResourceGroup --subnet MySubnet --vnet-name MyVnet
    crafted: true
"""

helps['network application-gateway frontend-ip delete'] = """
type: command
short-summary: Delete a frontend IP address.
examples:
  - name: Delete a frontend IP address.
    text: az network application-gateway frontend-ip delete -g MyResourceGroup --gateway-name MyAppGateway -n MyFrontendIp
"""

helps['network application-gateway frontend-ip list'] = """
type: command
short-summary: List frontend IP addresses.
examples:
  - name: List frontend IP addresses.
    text: az network application-gateway frontend-ip list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway frontend-ip show'] = """
type: command
short-summary: Get the details of a frontend IP address.
examples:
  - name: Get the details of a frontend IP address.
    text: az network application-gateway frontend-ip show -g MyResourceGroup --gateway-name MyAppGateway -n MyFrontendIp
"""

helps['network application-gateway frontend-ip update'] = """
type: command
short-summary: Update a frontend IP address.
examples:
  - name: Update a frontend IP address. (autogenerated)
    text: |
        az network application-gateway frontend-ip update --gateway-name MyAppGateway --name MyFrontendIp --private-ip-address 10.10.10.50 --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway frontend-port'] = """
type: group
short-summary: Manage frontend ports of an application gateway.
"""

helps['network application-gateway frontend-port create'] = """
type: command
short-summary: Create a frontend port.
examples:
  - name: Create a frontend port.
    text: |
        az network application-gateway frontend-port create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyFrontendPort --port 8080
"""

helps['network application-gateway frontend-port delete'] = """
type: command
short-summary: Delete a frontend port.
examples:
  - name: Delete a frontend port.
    text: az network application-gateway frontend-port delete -g MyResourceGroup --gateway-name MyAppGateway -n MyFrontendPort
"""

helps['network application-gateway frontend-port list'] = """
type: command
short-summary: List frontend ports.
examples:
  - name: List frontend ports.
    text: az network application-gateway frontend-port list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway frontend-port show'] = """
type: command
short-summary: Get the details of a frontend port.
examples:
  - name: Get the details of a frontend port.
    text: az network application-gateway frontend-port show -g MyResourceGroup --gateway-name MyAppGateway -n MyFrontendPort
"""

helps['network application-gateway frontend-port update'] = """
type: command
short-summary: Update a frontend port.
examples:
  - name: Update a frontend port to use a different port.
    text: |
        az network application-gateway frontend-port update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyFrontendPort --port 8081
"""

helps['network application-gateway http-listener'] = """
type: group
short-summary: Manage HTTP listeners of an application gateway.
"""

helps['network application-gateway http-listener create'] = """
type: command
short-summary: Create an HTTP listener.
examples:
  - name: Create an HTTP listener.
    text: |
        az network application-gateway http-listener create -g MyResourceGroup --gateway-name MyAppGateway \\
            --frontend-port MyFrontendPort -n MyHttpListener --frontend-ip MyAppGatewayPublicIp
"""

helps['network application-gateway http-listener delete'] = """
type: command
short-summary: Delete an HTTP listener.
examples:
  - name: Delete an HTTP listener.
    text: az network application-gateway http-listener delete -g MyResourceGroup --gateway-name MyAppGateway -n MyHttpListener
"""

helps['network application-gateway http-listener list'] = """
type: command
short-summary: List HTTP listeners.
examples:
  - name: List HTTP listeners.
    text: az network application-gateway http-listener list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway http-listener show'] = """
type: command
short-summary: Get the details of an HTTP listener.
examples:
  - name: Get the details of an HTTP listener.
    text: az network application-gateway http-listener show -g MyResourceGroup --gateway-name MyAppGateway -n MyHttpListener
"""

helps['network application-gateway http-listener update'] = """
type: command
short-summary: Update an HTTP listener.
examples:
  - name: Update an HTTP listener to use a different hostname.
    text: |
        az network application-gateway http-listener update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyHttpListener --host-name www.mynewhost.com
"""

helps['network application-gateway listener'] = """
type: group
short-summary: Manage listeners of an application gateway.
"""

helps['network application-gateway listener create'] = """
type: command
short-summary: Create a listener.
examples:
  - name: Create a listener.
    text: |
        az network application-gateway listener create -g MyResourceGroup --gateway-name MyAppGateway \\
            --frontend-port MyFrontendPort -n MyListener --frontend-ip MyAppGatewayPublicIp
"""

helps['network application-gateway listener delete'] = """
type: command
short-summary: Delete a listener.
examples:
  - name: Delete a listener.
    text: az network application-gateway listener delete -g MyResourceGroup --gateway-name MyAppGateway -n MyListener
"""

helps['network application-gateway listener list'] = """
type: command
short-summary: List listeners.
examples:
  - name: List listeners.
    text: az network application-gateway listener list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway listener show'] = """
type: command
short-summary: Get the details of a listener.
examples:
  - name: Get the details of a listener.
    text: az network application-gateway listener show -g MyResourceGroup --gateway-name MyAppGateway -n MyListener
"""

helps['network application-gateway listener update'] = """
type: command
short-summary: Update a listener.
examples:
  - name: Update a listener to use a different frontend port.
    text: |
        az network application-gateway listener update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyListener --frontend-port MyNewFrontendPort
"""

helps['network application-gateway http-settings'] = """
type: group
short-summary: Manage HTTP settings of an application gateway.
"""

helps['network application-gateway http-settings create'] = """
type: command
short-summary: Create HTTP settings.
examples:
  - name: Create HTTP settings.
    text: |
        az network application-gateway http-settings create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyHttpSettings --port 80 --protocol Http --cookie-based-affinity Disabled --timeout 30
  - name: Create HTTP settings. (autogenerated)
    text: |
        az network application-gateway http-settings create --gateway-name MyAppGateway --host-name MyHost --name MyHttpSettings --port 80 --probe MyNewProbe --protocol Http --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway http-settings delete'] = """
type: command
short-summary: Delete HTTP settings.
examples:
  - name: Delete HTTP settings.
    text: az network application-gateway http-settings delete -g MyResourceGroup --gateway-name MyAppGateway -n MyHttpSettings
"""

helps['network application-gateway http-settings list'] = """
type: command
short-summary: List HTTP settings.
examples:
  - name: List HTTP settings.
    text: az network application-gateway http-settings list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway http-settings show'] = """
type: command
short-summary: Get the details of a gateway's HTTP settings.
examples:
  - name: Get the details of a gateway's HTTP settings.
    text: az network application-gateway http-settings show -g MyResourceGroup --gateway-name MyAppGateway -n MyHttpSettings
"""

helps['network application-gateway http-settings update'] = """
type: command
short-summary: Update HTTP settings.
examples:
  - name: Update HTTP settings to use a new probe.
    text: |
        az network application-gateway http-settings update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyHttpSettings --probe MyNewProbe
  - name: Update HTTP settings. (autogenerated)
    text: |
        az network application-gateway http-settings update --enable-probe true --gateway-name MyAppGateway --name MyHttpSettings --probe MyNewProbe --resource-group MyResourceGroup
    crafted: true
  - name: Update HTTP settings. (autogenerated)
    text: |
        az network application-gateway http-settings update --gateway-name MyAppGateway --host-name-from-backend-pool true --name MyHttpSettings --port 80 --probe MyNewProbe --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway settings'] = """
type: group
short-summary: Manage settings of an application gateway.
"""

helps['network application-gateway settings create'] = """
type: command
short-summary: Create settings.
examples:
  - name: Create settings.
    text: |
        az network application-gateway settings create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MySettings --port 80 --protocol Http --timeout 30
  - name: Create settings. (autogenerated)
    text: |
        az network application-gateway settings create --gateway-name MyAppGateway --host-name MyHost --name MySettings \
        --port 80 --probe MyNewProbe --protocol Tcp --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway settings delete'] = """
type: command
short-summary: Delete settings.
examples:
  - name: Delete settings.
    text: az network application-gateway settings delete -g MyResourceGroup --gateway-name MyAppGateway -n MyHttpSettings
"""

helps['network application-gateway settings list'] = """
type: command
short-summary: List settings.
examples:
  - name: List settings.
    text: az network application-gateway settings list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway settings show'] = """
type: command
short-summary: Get the details of a gateway's settings.
examples:
  - name: Get the details of a gateway's settings.
    text: az network application-gateway settings show -g MyResourceGroup --gateway-name MyAppGateway -n MySettings
"""

helps['network application-gateway settings update'] = """
type: command
short-summary: Update settings.
examples:
  - name: Update settings to use a new probe.
    text: |
        az network application-gateway settings update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MySettings --probe MyNewProbe
  - name: Update settings.
    text: |
        az network application-gateway settings update --gateway-name MyAppGateway --name MySettings --probe MyNewProbe --resource-group MyResourceGroup
    crafted: true
  - name: Update settings to use a new port.
    text: |
        az network application-gateway settings update --gateway-name MyAppGateway --backend-pool-host-name true --name MySettings --port 80 --probe MyNewProbe --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway identity'] = """
type: group
short-summary: Manage the managed service identity of an application gateway.
"""

helps['network application-gateway identity assign'] = """
type: command
short-summary: Assign a managed service identity to an application-gateway
examples:
  - name: Assign an identity to the application gateway
    text: az network application-gateway identity assign -g MyResourceGroup --gateway-name ag1 \\ --identity /subscriptions/*-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id1
"""

helps['network application-gateway identity remove'] = """
type: command
short-summary: Remove the managed service identity of an application-gateway
examples:
  - name: Remove an identity to the application gateway
    text: az network application-gateway identity remove -g MyResourceGroup --gateway-name ag1
"""

helps['network application-gateway identity show'] = """
type: command
short-summary: Show the managed service identity of an application-gateway
examples:
  - name: Show an identity to the application gateway
    text: az network application-gateway identity show -g MyResourceGroup --gateway-name ag1
"""

helps['network application-gateway list'] = """
type: command
short-summary: List application gateways.
examples:
  - name: List application gateways.
    text: az network application-gateway list -g MyResourceGroup
"""

helps['network application-gateway probe'] = """
type: group
short-summary: Manage probes to gather and evaluate information on a gateway.
"""

helps['network application-gateway probe create'] = """
type: command
short-summary: Create a probe.
examples:
  - name: Create an application gateway probe.
    text: |
        az network application-gateway probe create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyProbe --protocol https --host 127.0.0.1 --path /path/to/probe
"""

helps['network application-gateway probe delete'] = """
type: command
short-summary: Delete a probe.
examples:
  - name: Delete a probe.
    text: az network application-gateway probe delete -g MyResourceGroup --gateway-name MyAppGateway -n MyProbe
  - name: Delete a probe. (autogenerated)
    text: |
        az network application-gateway probe delete --gateway-name MyAppGateway --name MyProbe --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network application-gateway probe list'] = """
type: command
short-summary: List probes.
examples:
  - name: List probes.
    text: az network application-gateway probe list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway probe show'] = """
type: command
short-summary: Get the details of a probe.
examples:
  - name: Get the details of a probe.
    text: az network application-gateway probe show -g MyResourceGroup --gateway-name MyAppGateway -n MyProbe
"""

helps['network application-gateway probe update'] = """
type: command
short-summary: Update a probe.
examples:
  - name: Update an application gateway probe with a timeout of 60 seconds.
    text: |
        az network application-gateway probe update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyProbe --timeout 60
  - name: Update a probe. (autogenerated)
    text: |
        az network application-gateway probe update --gateway-name MyAppGateway --host 127.0.0.1 --name MyProbe --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network application-gateway redirect-config'] = """
type: group
short-summary: Manage redirect configurations.
"""

helps['network application-gateway redirect-config create'] = """
type: command
short-summary: Create a redirect configuration.
examples:
  - name: Create a redirect configuration to a http-listener called MyBackendListener.
    text: |
        az network application-gateway redirect-config create -g MyResourceGroup \\
            --gateway-name MyAppGateway -n MyRedirectConfig --type Permanent \\
            --include-path true --include-query-string true --target-listener MyBackendListener
"""

helps['network application-gateway redirect-config delete'] = """
type: command
short-summary: Delete a redirect configuration.
examples:
  - name: Delete a redirect configuration.
    text: az network application-gateway redirect-config delete -g MyResourceGroup \\ --gateway-name MyAppGateway -n MyRedirectConfig
"""

helps['network application-gateway redirect-config list'] = """
type: command
short-summary: List redirect configurations.
examples:
  - name: List redirect configurations.
    text: az network application-gateway redirect-config list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway redirect-config show'] = """
type: command
short-summary: Get the details of a redirect configuration.
examples:
  - name: Get the details of a redirect configuration.
    text: az network application-gateway redirect-config show -g MyResourceGroup --gateway-name MyAppGateway -n MyRedirectConfig
"""

helps['network application-gateway redirect-config update'] = """
type: command
short-summary: Update a redirect configuration.
examples:
  - name: Update a redirect configuration to a different http-listener.
    text: |
        az network application-gateway redirect-config update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyRedirectConfig --type Permanent --target-listener MyNewBackendListener
  - name: Update a redirect configuration. (autogenerated)
    text: |
        az network application-gateway redirect-config update --gateway-name MyAppGateway --include-path true --include-query-string true --name MyRedirectConfig --resource-group MyResourceGroup --target-listener MyNewBackendListener --type Permanent
    crafted: true
"""

helps['network application-gateway rewrite-rule'] = """
short-summary: Manage rewrite rules of an application gateway.
type: group
"""

helps['network application-gateway rewrite-rule condition'] = """
short-summary: Manage rewrite rule conditions of an application gateway.
type: group
"""

helps['network application-gateway rewrite-rule condition create'] = """
short-summary: Create a rewrite rule condition.
type: command
parameters:
  - name: --variable
    populator-commands:
      - az network application-gateway rewrite-rule condition list-server-variables
"""

helps['network application-gateway rewrite-rule condition delete'] = """
short-summary: Delete a rewrite rule condition.
type: command
"""

helps['network application-gateway rewrite-rule condition list'] = """
short-summary: List rewrite rule conditions.
type: command
examples:
  - name: List rewrite rule conditions. (autogenerated)
    text: |
        az network application-gateway rewrite-rule condition list --gateway-name MyGateway --resource-group MyResourceGroup --rule-name MyRule --rule-set-name MyRuleSet
    crafted: true
"""

helps['network application-gateway rewrite-rule condition show'] = """
short-summary: Get the details of a rewrite rule condition.
type: command
"""

helps['network application-gateway rewrite-rule condition update'] = """
short-summary: Update a rewrite rule condition.
type: command
parameters:
  - name: --variable
    populator-commands:
      - az network application-gateway rewrite-rule condition list-server-variables
"""

helps['network application-gateway rewrite-rule create'] = """
short-summary: Create a rewrite rule.
type: command
parameters:
  - name: --request-headers
    populator-commands:
      - az network application-gateway rewrite-rule list-request-headers
  - name: --response-headers
    populator-commands:
      - az network application-gateway rewrite-rule list-response-headers
"""

helps['network application-gateway rewrite-rule delete'] = """
short-summary: Delete a rewrite rule.
type: command
examples:
  - name: Delete a rewrite rule. (autogenerated)
    text: |
        az network application-gateway rewrite-rule delete --gateway-name MyGateway --name MyRewriteRule --resource-group MyResourceGroup --rule-set-name MyRuleSet
    crafted: true
"""

helps['network application-gateway rewrite-rule list'] = """
short-summary: List rewrite rules.
type: command
examples:
  - name: List rewrite rules. (autogenerated)
    text: |
        az network application-gateway rewrite-rule list --gateway-name MyGateway --resource-group MyResourceGroup --rule-set-name MyRuleSet
    crafted: true
"""

helps['network application-gateway rewrite-rule set'] = """
short-summary: Manage rewrite rule sets of an application gateway.
type: group
"""

helps['network application-gateway rewrite-rule set create'] = """
short-summary: Create a rewrite rule set.
type: command
examples:
  - name: Create a rewrite rule set. (autogenerated)
    text: |
        az network application-gateway rewrite-rule set create --gateway-name MyGateway --name MyRewriteRuleSet --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway rewrite-rule set delete'] = """
short-summary: Delete a rewrite rule set.
type: command
"""

helps['network application-gateway rewrite-rule set list'] = """
short-summary: List rewrite rule sets.
type: command
examples:
  - name: List rewrite rule sets. (autogenerated)
    text: |
        az network application-gateway rewrite-rule set list --gateway-name MyGateway --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway rewrite-rule set show'] = """
short-summary: Get the details of a rewrite rule set.
type: command
examples:
  - name: Get the details of a rewrite rule set. (autogenerated)
    text: |
        az network application-gateway rewrite-rule set show --gateway-name MyGateway --name MyRewriteRuleSet --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway rewrite-rule set update'] = """
short-summary: Update a rewrite rule set.
type: command
examples:
  - name: Update a rewrite rule set. (autogenerated)
    text: |
        az network application-gateway rewrite-rule set update --gateway-name MyGateway --name MyRewriteRuleSet --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway rewrite-rule show'] = """
short-summary: Get the details of a rewrite rule.
type: command
examples:
  - name: Get the details of a rewrite rule. (autogenerated)
    text: |
        az network application-gateway rewrite-rule show --gateway-name MyGateway --name MyRewriteRule --resource-group MyResourceGroup --rule-set-name MyRuleSet
    crafted: true
"""

helps['network application-gateway rewrite-rule update'] = """
short-summary: Update a rewrite rule.
type: command
parameters:
  - name: --request-headers
    populator-commands:
      - az network application-gateway rewrite-rule list-request-headers
  - name: --response-headers
    populator-commands:
      - az network application-gateway rewrite-rule list-response-headers
examples:
  - name: Update a rewrite rule. (autogenerated)
    text: |
        az network application-gateway rewrite-rule update --gateway-name MyGateway --name MyRewriteRule --remove tags.no_80 --resource-group MyResourceGroup --rule-set-name MyRuleSet
    crafted: true
"""

helps['network application-gateway root-cert'] = """
type: group
short-summary: Manage trusted root certificates of an application gateway.
"""

helps['network application-gateway root-cert create'] = """
type: command
short-summary: Upload a trusted root certificate.
examples:
  - name: Upload a trusted root certificate. (autogenerated)
    text: |
        az network application-gateway root-cert create --cert-file /path/to/cert/file --gateway-name MyGateway --name MyTrustedRootCertificate --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway root-cert delete'] = """
type: command
short-summary: Delete a trusted root certificate.
examples:
  - name: Delete a trusted root certificate.
    text: az network application-gateway root-cert delete -g MyResourceGroup --gateway-name MyAppGateway -n MyRootCert
"""

helps['network application-gateway root-cert list'] = """
type: command
short-summary: List trusted root certificates.
examples:
  - name: List trusted root certificates.
    text: az network application-gateway root-cert list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway root-cert show'] = """
type: command
short-summary: Get the details of a trusted root certificate.
examples:
  - name: Get the details of a trusted root certificate.
    text: az network application-gateway root-cert show -g MyResourceGroup --gateway-name MyAppGateway -n MyRootCert
"""

helps['network application-gateway root-cert update'] = """
type: command
short-summary: Update a trusted root certificate.
examples:
  - name: Update a trusted root certificate. (autogenerated)
    text: |
        az network application-gateway root-cert update --cert-file /path/to/cert/file --gateway-name MyGateway --name MyTrustedRootCertificate --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway rule'] = """
type: group
short-summary: Evaluate probe information and define http/https routing rules.
long-summary: >
    For more information, visit, https://docs.microsoft.com/azure/application-gateway/application-gateway-customize-waf-rules-cli
"""

helps['network application-gateway rule create'] = """
type: command
short-summary: Create a rule.
long-summary: Rules are executed in the order in which they are created.
examples:
  - name: Create a basic rule.
    text: |
        az network application-gateway rule create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyRule --http-listener MyBackendListener --rule-type Basic --address-pool MyAddressPool --http-settings MyHttpSettings
"""

helps['network application-gateway rule delete'] = """
type: command
short-summary: Delete a rule.
examples:
  - name: Delete a rule.
    text: az network application-gateway rule delete -g MyResourceGroup --gateway-name MyAppGateway -n MyRule
"""

helps['network application-gateway rule list'] = """
type: command
short-summary: List rules.
examples:
  - name: List rules.
    text: az network application-gateway rule list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway rule show'] = """
type: command
short-summary: Get the details of a rule.
examples:
  - name: Get the details of a rule.
    text: az network application-gateway rule show -g MyResourceGroup --gateway-name MyAppGateway -n MyRule
"""

helps['network application-gateway rule update'] = """
type: command
short-summary: Update a rule.
examples:
  - name: Update a rule use a new HTTP listener.
    text: |
        az network application-gateway rule update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyRule --http-listener MyNewBackendListener
  - name: Update a rule. (autogenerated)
    text: |
        az network application-gateway rule update --address-pool MyAddressPool --gateway-name MyAppGateway --name MyRule --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway routing-rule'] = """
type: group
short-summary: Evaluate probe information and define tcp/tls routing rules.
"""

helps['network application-gateway routing-rule create'] = """
type: command
short-summary: Create a rule.
long-summary: Rules are executed in the order in which they are created.
examples:
  - name: Create a basic rule.
    text: |
        az network application-gateway routing-rule create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyRule --listener MyBackendListener --rule-type Basic --address-pool MyAddressPool --settings MySettings
"""

helps['network application-gateway routing-rule delete'] = """
type: command
short-summary: Delete a rule.
examples:
  - name: Delete a rule.
    text: az network application-gateway routing-rule delete -g MyResourceGroup --gateway-name MyAppGateway -n MyRule
"""

helps['network application-gateway routing-rule list'] = """
type: command
short-summary: List rules.
examples:
  - name: List rules.
    text: az network application-gateway routing-rule list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway routing-rule show'] = """
type: command
short-summary: Get the details of a rule.
examples:
  - name: Get the details of a rule.
    text: az network application-gateway routing-rule show -g MyResourceGroup --gateway-name MyAppGateway -n MyRule
"""

helps['network application-gateway routing-rule update'] = """
type: command
short-summary: Update a rule.
examples:
  - name: Update a rule use a new listener.
    text: |
        az network application-gateway routing-rule update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyRule --listener MyNewBackendListener
  - name: Update a rule.
    text: |
        az network application-gateway routing-rule update --address-pool MyAddressPool --gateway-name MyAppGateway --name MyRule --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway show'] = """
type: command
short-summary: Get the details of an application gateway.
examples:
  - name: Get the details of an application gateway.
    text: az network application-gateway show -g MyResourceGroup -n MyAppGateway
"""

helps['network application-gateway show-backend-health'] = """
type: command
short-summary: Get information on the backend health of an application gateway.
examples:
  - name: Show backend health of an application gateway.
    text: az network application-gateway show-backend-health -g MyResourceGroup -n MyAppGateway
  - name: Show backend health of an application gateway for given combination of backend pool and http setting.
    text: |-
        az network application-gateway show-backend-health -g MyResourceGroup -n MyAppGateway --host-name-from-http-settings --path /test --timeout 100 --http-settings appGatewayBackendHttpSettings --address-pool appGatewayBackendPool
"""

helps['network application-gateway ssl-cert'] = """
type: group
short-summary: Manage SSL certificates of an application gateway.
long-summary: For more information visit https://docs.microsoft.com/azure/application-gateway/application-gateway-ssl-cli
"""

helps['network application-gateway ssl-cert create'] = """
type: command
short-summary: Upload an SSL certificate.
examples:
  - name: Upload an SSL certificate via --cert-file and --cert-password.
    text: |
        az network application-gateway ssl-cert create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MySSLCert --cert-file \\path\\to\\cert\\file --cert-password Abc123
  - name: |-
        Upload an SSL certificate via --key-vault-secret-id of a KeyVault Secret
        with Base64 encoded value of an unencrypted pfx
    text: |-
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
          -out azure-cli-app-tls.crt \\
          -keyout azure-cli-app-tls.key \\
          -subj "/CN=azure-cli-app"

        openssl pkcs12 -export \\
          -in azure-cli-tls.crt \\
          -inkey sample-app-tls.key \\
          -passout pass: -out azure-cli-cert.pfx

        SecretValue=$(cat azure-cli-cert.pfx | base64)

        az keyvault secret set --vault-name MyKeyVault --name MySecret --value ${SecretValue}

        az network application-gateway ssl-cert create \\
          --resource-group MyResourceGroup \\
          --gateway-name MyAppGateway \\
          -n MySSLCert \\
          --key-vault-secret-id MySecretSecretID
  - name: |-
        Upload an SSL certificate via --key-vault-secret-id of a KeyVault Certificate
    text: |-
        az keyvault certificate create \\
          --vault-name MyKeyVault \\
          --name MyCertificate \\
          --policy "$(az keyvault certificate get-default-policy)" \\

        az network application-gateway ssl-cert create \\
          --resource-group MyResourceGroup \\
          --gateway-name MyAppGateway \\
          -n MySSLCert \\
          --key-vault-secret-id MyCertificateSecretID
"""

helps['network application-gateway ssl-cert delete'] = """
type: command
short-summary: Delete an SSL certificate.
examples:
  - name: Delete an SSL certificate.
    text: az network application-gateway ssl-cert delete -g MyResourceGroup --gateway-name MyAppGateway -n MySslCert
"""

helps['network application-gateway ssl-cert list'] = """
type: command
short-summary: List SSL certificates.
examples:
  - name: List SSL certificates.
    text: az network application-gateway ssl-cert list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway ssl-cert show'] = """
type: command
short-summary: Get the details of an SSL certificate.
examples:
  - name: Get the details of an SSL certificate.
    text: az network application-gateway ssl-cert show -g MyResourceGroup --gateway-name MyAppGateway -n MySslCert
  - name: Display the expiry date of SSL certificate. The certificate is returned in PKCS7 format from which the expiration date needs to be retrieved.
    text: |
        publiccert=`az network application-gateway ssl-cert show -g MyResourceGroup --gateway-name MyAppGateway --name mywebsite.com --query publicCertData -o tsv`
        echo "-----BEGIN PKCS7-----" >> public.cert; echo "${publiccert}" >> public.cert; echo "-----END PKCS7-----" >> public.cert
        cat public.cert | fold -w 64 | openssl pkcs7 -print_certs | openssl x509 -noout -enddate
"""

helps['network application-gateway ssl-cert update'] = """
type: command
short-summary: Update an SSL certificate.
examples:
  - name: Change a gateway SSL certificate and password.
    text: |
        az network application-gateway ssl-cert update -g MyResourceGroup --gateway-name MyAppGateway -n MySslCert \\
            --cert-file \\path\\to\\new\\cert\\file --cert-password Abc123Abc123
"""

helps['network application-gateway ssl-policy'] = """
type: group
short-summary: Manage the SSL policy of an application gateway.
"""

helps['network application-gateway ssl-policy list-options'] = """
type: command
short-summary: Lists available SSL options for configuring SSL policy.
examples:
  - name: List available SSL options for configuring SSL policy.
    text: az network application-gateway ssl-policy list-options
"""

helps['network application-gateway ssl-policy predefined'] = """
type: group
short-summary: Get information on predefined SSL policies.
"""

helps['network application-gateway ssl-policy predefined list'] = """
type: command
short-summary: Lists all SSL predefined policies for configuring SSL policy.
examples:
  - name: Lists all SSL predefined policies for configuring SSL policy.
    text: az network application-gateway ssl-policy predefined list
"""

helps['network application-gateway ssl-policy predefined show'] = """
type: command
short-summary: Gets SSL predefined policy with the specified policy name.
examples:
  - name: Gets SSL predefined policy with the specified policy name.
    text: az network application-gateway ssl-policy predefined show -n AppGwSslPolicy20170401
"""

helps['network application-gateway ssl-policy set'] = """
type: command
short-summary: Update or clear SSL policy settings.
long-summary: To view the predefined policies, use `az network application-gateway ssl-policy predefined list`.
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
examples:
  - name: Set a predefined SSL policy.
    text: |
        az network application-gateway ssl-policy set -g MyResourceGroup --gateway-name MyAppGateway \\
            -n AppGwSslPolicy20170401S --policy-type Predefined
  - name: Set a custom SSL policy with TLSv1_2 and the cipher suites below.
    text: |
        az network application-gateway ssl-policy set -g MyResourceGroup --gateway-name MyAppGateway \\
            --policy-type Custom --min-protocol-version TLSv1_2 \\
            --cipher-suites TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 TLS_RSA_WITH_AES_128_GCM_SHA256
"""

helps['network application-gateway ssl-policy show'] = """
type: command
short-summary: Get the details of gateway's SSL policy settings.
examples:
  - name: Get the details of a gateway's SSL policy settings.
    text: az network application-gateway ssl-policy show -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway start'] = """
type: command
short-summary: Start an application gateway.
examples:
  - name: Start an application gateway.
    text: az network application-gateway start -g MyResourceGroup -n MyAppGateway
"""

helps['network application-gateway stop'] = """
type: command
short-summary: Stop an application gateway.
examples:
  - name: Stop an application gateway.
    text: az network application-gateway stop -g MyResourceGroup -n MyAppGateway
"""

helps['network application-gateway update'] = """
type: command
short-summary: Update an application gateway.
examples:
  - name: Update an application gateway. (autogenerated)
    text: |
        az network application-gateway update --name MyApplicationGateway --resource-group MyResourceGroup --set sku.tier=WAF_v2
    crafted: true
"""

helps['network application-gateway url-path-map'] = """
type: group
short-summary: Manage URL path maps of an application gateway.
"""

helps['network application-gateway url-path-map create'] = """
type: command
short-summary: Create a URL path map.
long-summary: >
    The map must be created with at least one rule. This command requires the creation of the
    first rule at the time the map is created. To learn more
    visit https://docs.microsoft.com/azure/application-gateway/application-gateway-create-url-route-cli
examples:
  - name: Create a URL path map with a rule.
    text: |
        az network application-gateway url-path-map create -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyUrlPathMap --rule-name MyUrlPathMapRule1 --paths /mypath1/* --address-pool MyAddressPool \\
            --default-address-pool MyAddressPool --http-settings MyHttpSettings --default-http-settings MyHttpSettings
"""

helps['network application-gateway url-path-map delete'] = """
type: command
short-summary: Delete a URL path map.
examples:
  - name: Delete a URL path map.
    text: az network application-gateway url-path-map delete -g MyResourceGroup --gateway-name MyAppGateway -n MyUrlPathMap
"""

helps['network application-gateway url-path-map list'] = """
type: command
short-summary: List URL path maps.
examples:
  - name: List URL path maps.
    text: az network application-gateway url-path-map list -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway url-path-map rule'] = """
type: group
short-summary: Manage the rules of a URL path map.
"""

helps['network application-gateway url-path-map rule create'] = """
type: command
short-summary: Create a rule for a URL path map.
examples:
  - name: Create a rule for a URL path map.
    text: |
        az network application-gateway url-path-map rule create -g MyResourceGroup \\
            --gateway-name MyAppGateway -n MyUrlPathMapRule2 --path-map-name MyUrlPathMap \\
            --paths /mypath2/* --address-pool MyAddressPool --http-settings MyHttpSettings
"""

helps['network application-gateway url-path-map rule delete'] = """
type: command
short-summary: Delete a rule of a URL path map.
examples:
  - name: Delete a rule of a URL path map.
    text: |
        az network application-gateway url-path-map rule delete -g MyResourceGroup --gateway-name MyAppGateway \\
            --path-map-name MyUrlPathMap -n MyUrlPathMapRule2
"""

helps['network application-gateway url-path-map show'] = """
type: command
short-summary: Get the details of a URL path map.
examples:
  - name: Get the details of a URL path map.
    text: az network application-gateway url-path-map show -g MyResourceGroup --gateway-name MyAppGateway -n MyUrlPathMap
"""

helps['network application-gateway url-path-map update'] = """
type: command
short-summary: Update a URL path map.
examples:
  - name: Update a URL path map to use new default HTTP settings.
    text: |
        az network application-gateway url-path-map update -g MyResourceGroup --gateway-name MyAppGateway \\
            -n MyUrlPathMap --default-http-settings MyNewHttpSettings
  - name: Update a URL path map. (autogenerated)
    text: |
        az network application-gateway url-path-map update --default-address-pool MyAddressPool --default-http-settings MyNewHttpSettings --gateway-name MyAppGateway --name MyUrlPathMap --remove tags.no_80 --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-config'] = """
type: group
short-summary: Configure the settings of a web application firewall.
long-summary: >
    These commands are only applicable to application gateways with an SKU type of WAF. To learn
    more, visit https://docs.microsoft.com/azure/application-gateway/application-gateway-web-application-firewall-cli
"""

helps['network application-gateway waf-config list-rule-sets'] = """
type: command
short-summary: Get information on available WAF rule sets, rule groups, and rule IDs.
parameters:
  - name: --group
    short-summary: >
        List rules for the specified rule group. Use `*` to list rules for all groups.
        Omit to suppress listing individual rules.
  - name: --type
    short-summary: Rule set type to list. Omit to list all types.
  - name: --version
    short-summary: Rule set version to list. Omit to list all versions.
examples:
  - name: List available rule groups in OWASP type rule sets.
    text: az network application-gateway waf-config list-rule-sets --type OWASP
  - name: List available rules in the OWASP 3.0 rule set.
    text: az network application-gateway waf-config list-rule-sets --group '*' --type OWASP --version 3.0
  - name: List available rules in the `crs_35_bad_robots` rule group.
    text: az network application-gateway waf-config list-rule-sets --group crs_35_bad_robots
  - name: List available rules in table format.
    text: az network application-gateway waf-config list-rule-sets -o table
"""

helps['network application-gateway waf-config set'] = """
type: command
short-summary: Update the firewall configuration of a web application.
long-summary: >
    This command is only applicable to application gateways with an SKU type of WAF. To learn
    more, visit https://docs.microsoft.com/azure/application-gateway/application-gateway-web-application-firewall-cli
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
  - name: --exclusion
    short-summary: Add an exclusion expression to the WAF check.
    long-summary: |
        Usage:   --exclusion VARIABLE OPERATOR VALUE

        Multiple exclusions can be specified by using more than one `--exclusion` argument.
examples:
  - name: Configure WAF on an application gateway in detection mode with default values
    text: |
        az network application-gateway waf-config set -g MyResourceGroup --gateway-name MyAppGateway \\
            --enabled true --firewall-mode Detection --rule-set-version 3.0
  - name: Disable rules for validation of request body parsing and SQL injection.
    text: |
        az network application-gateway waf-config set -g MyResourceGroup --gateway-name MyAppGateway \\
            --enabled true --rule-set-type OWASP --rule-set-version 3.0 \\
            --disabled-rule-groups REQUEST-942-APPLICATION-ATTACK-SQLI \\
            --disabled-rules 920130 920140
  - name: Configure WAF on an application gateway with exclusions.
    text: |
        az network application-gateway waf-config set -g MyResourceGroup --gateway-name MyAppGateway \\
            --enabled true --firewall-mode Detection --rule-set-version 3.0 \\
            --exclusion "RequestHeaderNames StartsWith x-header" \\
            --exclusion "RequestArgNames Equals IgnoreThis"
"""

helps['network application-gateway waf-config show'] = """
type: command
short-summary: Get the firewall configuration of a web application.
examples:
  - name: Get the firewall configuration of a web application.
    text: az network application-gateway waf-config show -g MyResourceGroup --gateway-name MyAppGateway
"""

helps['network application-gateway waf-policy'] = """
type: group
short-summary: Manage application gateway web application firewall (WAF) policies.
"""

helps['network application-gateway waf-policy create'] = """
type: command
short-summary: Create an application gateway WAF policy.
examples:
  - name: Create an application gateway WAF policy. (autogenerated)
    text: |
        az network application-gateway waf-policy create --name MyApplicationGatewayWAFPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy delete'] = """
type: command
short-summary: Delete an application gateway WAF policy.
examples:
  - name: Delete an application gateway WAF policy. (autogenerated)
    text: |
        az network application-gateway waf-policy delete --name MyApplicationGatewayWAFPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy list'] = """
type: command
short-summary: List application gateway WAF policies.
examples:
  - name: List application gateway WAF policies. (autogenerated)
    text: |
        az network application-gateway waf-policy list --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy policy-setting'] = """
type: group
short-summary: Defines contents of a web application firewall global configuration.
"""

helps['network application-gateway waf-policy policy-setting update'] = """
type: command
short-summary: Update properties of a web application firewall global configuration.
examples:
  - name: Update properties of a web application firewall global configuration. (autogenerated)
    text: |
        az network application-gateway waf-policy policy-setting update --mode Prevention --policy-name MyPolicy --resource-group MyResourceGroup --state Disabled
    crafted: true
"""

helps['network application-gateway waf-policy policy-setting list'] = """
type: command
short-summary: List properties of a web application firewall global configuration.
examples:
  - name: List properties of a web application firewall global configuration. (autogenerated)
    text: |
        az network application-gateway waf-policy policy-setting list --policy-name MyPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy custom-rule'] = """
type: group
short-summary: Manage application gateway web application firewall (WAF) policy custom rules.
"""

helps['network application-gateway waf-policy custom-rule create'] = """
type: command
short-summary: Create an application gateway WAF policy custom rule.
examples:
  - name: Create an application gateway WAF policy custom rule. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule create --action Allow --name MyWafPolicyRule --policy-name MyPolicy --priority 500 --resource-group MyResourceGroup --rule-type MatchRule
    crafted: true
"""

helps['network application-gateway waf-policy custom-rule delete'] = """
type: command
short-summary: Delete an application gateway WAF policy custom rule.
examples:
  - name: Delete an application gateway WAF policy custom rule. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule delete --name MyWafPolicyRule --policy-name MyPolicy --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network application-gateway waf-policy custom-rule list'] = """
type: command
short-summary: List application gateway WAF policy custom rules.
examples:
  - name: List application gateway WAF policy custom rules. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule list --policy-name MyPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy custom-rule match-condition'] = """
type: group
short-summary: Manage application gateway web application firewall (WAF) policies.
"""

helps['network application-gateway waf-policy custom-rule match-condition add'] = """
type: command
short-summary: A match condition to an application gateway WAF policy custom rule.
examples:
  - name: Add application gateway WAF policy custom rule match condition with contains.
    text: |
        az network application-gateway waf-policy custom-rule match-condition add --resource-group MyResourceGroup --policy-name MyPolicy --name MyWAFPolicyRule --match-variables RequestHeaders.value --operator contains --values foo boo --transform lowercase
  - name: Add application gateway WAF policy custom rule match condition with equal.
    text: |
        az network application-gateway waf-policy custom-rule match-condition add --resource-group MyResourceGroup --policy-name MyPolicy --name MyWAFPolicyRule --match-variables RequestHeaders.Content-Type --operator Equal --values application/csp-report
"""

helps['network application-gateway waf-policy custom-rule match-condition list'] = """
type: command
short-summary: List application gateway WAF policy custom rule match conditions.
examples:
  - name: List application gateway WAF policy custom rule match conditions. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule match-condition list --name MyWAFPolicyRule --policy-name MyPolicy --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network application-gateway waf-policy custom-rule match-condition remove'] = """
type: command
short-summary: Remove a match condition from an application gateway WAF policy custom rule.
"""

helps['network application-gateway waf-policy custom-rule show'] = """
type: command
short-summary: Get the details of an application gateway WAF policy custom rule.
examples:
  - name: Get the details of an application gateway WAF policy custom rule. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule show --name MyWAFPolicyRule --policy-name MyPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy custom-rule update'] = """
type: command
short-summary: Update an application gateway WAF policy custom rule.
examples:
  - name: Update an application gateway WAF policy custom rule. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule update --name MyWAFPolicyRule --policy-name MyPolicy --resource-group MyResourceGroup --set useRemoteGateways=true
    crafted: true
  - name: Update an application gateway WAF policy custom rule. (autogenerated)
    text: |
        az network application-gateway waf-policy custom-rule update --action Allow --name MyWAFPolicyRule --policy-name MyPolicy --priority 500 --resource-group MyResourceGroup --rule-type MatchRule
    crafted: true
"""

helps['network application-gateway waf-policy managed-rule'] = """
type: group
short-summary: >
    Manage managed rules of a waf-policy.
    Visit: https://docs.microsoft.com/azure/web-application-firewall/afds/afds-overview
"""

helps['network application-gateway waf-policy managed-rule rule-set'] = """
type: group
short-summary: Manage managed rule set of managed rules of a WAF policy.
"""

helps['network application-gateway waf-policy managed-rule rule-set add'] = """
type: command
short-summary: >
  Add managed rule set to the WAF policy managed rules. For rule set and rules, please visit:
  https://docs.microsoft.com/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
examples:
  - name: Disable an attack protection rule
    text: |
      az network application-gateway waf-policy managed-rule rule-set add --policy-name MyPolicy -g MyResourceGroup --type OWASP --version 3.1 --group-name REQUEST-921-PROTOCOL-ATTACK --rules 921110
  - name: Add managed rule set to the WAF policy managed rules (autogenerated)
    text: |
        az network application-gateway waf-policy managed-rule rule-set add --policy-name MyPolicy --resource-group MyResourceGroup --type Microsoft_BotManagerRuleSet --version 0.1
    crafted: true
"""

helps['network application-gateway waf-policy managed-rule rule-set update'] = """
type: command
short-summary: >
  Manage rules of a WAF policy.
  If --group-name and --rules are provided, override existing rules. If --group-name is provided, clear all rules under a certain rule group. If neither of them are provided, update rule set and clear all rules under itself.
  For rule set and rules, please visit: https://docs.microsoft.com/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
examples:
  - name: Override rules under rule group EQUEST-921-PROTOCOL-ATTACK
    text: |
      az network application-gateway waf-policy managed-rule rule-set update --policy-name MyPolicy -g MyResourceGroup --type OWASP --version 3.1 --group-name REQUEST-921-PROTOCOL-ATTACK --rules 921130 921160
  - name: Update the OWASP protocol version from 3.1 to 3.0 which will clear the old rules
    text: |
      az network application-gateway waf-policy managed-rule rule-set update --policy-name MyPolicy -g MyResourceGroup --type OWASP --version 3.0
"""

helps['network application-gateway waf-policy managed-rule rule-set remove'] = """
type: command
short-summary: >
  Remove a managed rule set by rule set group name if rule_group_name is specified. Otherwise, remove all rule set.
examples:
  - name: Remove a managed rule set by rule set group name if rule_group_name is specified. Otherwise, remove all rule set.
    text: |
        az network application-gateway waf-policy managed-rule rule-set remove --policy-name MyPolicy --resource-group MyResourceGroup --type OWASP --version 3.1
"""

helps['network application-gateway waf-policy managed-rule rule-set list'] = """
type: command
short-summary: List all managed rule set.
examples:
  - name: List all managed rule set. (autogenerated)
    text: |
        az network application-gateway waf-policy managed-rule rule-set list --policy-name MyPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy managed-rule exclusion'] = """
type: group
short-summary: Manage OWASP CRS exclusions that are applied on a WAF policy managed rules.
"""

helps['network application-gateway waf-policy managed-rule exclusion add'] = """
type: command
short-summary: Add an OWASP CRS exclusion rule to the WAF policy managed rules.
"""

helps['network application-gateway waf-policy managed-rule exclusion remove'] = """
type: command
short-summary: Remove all OWASP CRS exclusion rules that are applied on a Waf policy managed rules.
"""

helps['network application-gateway waf-policy managed-rule exclusion list'] = """
type: command
short-summary: List all OWASP CRS exclusion rules that are applied on a Waf policy managed rules.
"""

helps['network application-gateway waf-policy managed-rule exclusion rule-set'] = """
type: group
short-summary: Define a managed rule set for exclusions.
"""

helps['network application-gateway waf-policy managed-rule exclusion rule-set add'] = """
type: command
short-summary: Add a managed rule set to an exclusion.
examples:
  - name: Add a managed rule set to an exclusion.
    text: |
        az network application-gateway waf-policy managed-rule exclusion rule-set add -g MyResourceGroup --policy-name MyPolicy --match-variable RequestHeaderNames --match-operator StartsWith --selector Bing --type OWASP --version 3.2 --group-name MyRuleGroup --rule-ids 921140 921150
"""

helps['network application-gateway waf-policy managed-rule exclusion rule-set remove'] = """
type: command
short-summary: Remove managed rule set within an exclusion.
examples:
  - name: Remove managed rule set within an exclusion.
    text: |
        az network application-gateway waf-policy managed-rule exclusion rule-set remove -g MyResourceGroup --policy-name MyPolicy --match-variable RequestHeaderNames --match-operator StartsWith --selector Bing --type OWASP --version 3.2 --group-name MyRuleGroup
"""

helps['network application-gateway waf-policy managed-rule exclusion rule-set list'] = """
type: command
short-summary: List all managed rule sets of an exclusion.
examples:
  - name: List all managed rule sets of an exclusion.
    text: |
        az network application-gateway waf-policy managed-rule exclusion rule-set list -g MyResourceGroup --policy-name MyPolicy
"""

helps['network application-gateway waf-policy show'] = """
type: command
short-summary: Get the details of an application gateway WAF policy.
examples:
  - name: Get the details of an application gateway WAF policy. (autogenerated)
    text: |
        az network application-gateway waf-policy show --name MyApplicationGatewayWAFPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy update'] = """
type: command
short-summary: Update an application gateway WAF policy.
examples:
  - name: Update an application gateway WAF policy. (autogenerated)
    text: |
        az network application-gateway waf-policy update --add communities='12076:5010' --name MyApplicationGatewayWAFPolicy --resource-group MyResourceGroup
    crafted: true
  - name: Update an application gateway WAF policy. (autogenerated)
    text: |
        az network application-gateway waf-policy update --name MyApplicationGatewayWAFPolicy --remove tags.no_80 --resource-group MyResourceGroup
    crafted: true
"""

helps['network application-gateway waf-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the application gateway WAF policy is met.
"""

helps['network application-gateway wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the application gateway is met.
examples:
  - name: Place the CLI in a waiting state until the application gateway is created.
    text: az network application-gateway wait -g MyResourceGroup -n MyAppGateway --created
"""

helps['network application-gateway client-cert'] = """
type: group
short-summary: Manage trusted client certificate of application gateway.
"""

helps['network application-gateway client-cert add'] = """
type: command
short-summary: Add trusted client certificate of the application gateway.
examples:
  - name: Add trusted client certificate for an existing application gateway.
    text: az network application-gateway client-cert add --gateway-name MyAppGateway -g MyResourceGroup --name MyCert --data Cert.cer
"""

helps['network application-gateway client-cert update'] = """
type: command
short-summary: Update trusted client certificate of the application gateway.
examples:
  - name: Update trusted client certificate for an existing application gateway.
    text: az network application-gateway client-cert update --gateway-name MyAppGateway -g MyResourceGroup --name MyCert --data Cert.cer
"""

helps['network application-gateway client-cert remove'] = """
type: command
short-summary: Remove an existing trusted client certificate of the application gateway.
examples:
  - name: Remove a trusted client certificate for an existing application gateway.
    text: az network application-gateway client-cert remove --gateway-name MyAppGateway -g MyResourceGroup --name MyCert
"""

helps['network application-gateway client-cert show'] = """
type: command
short-summary: Show an existing trusted client certificate of the application gateway.
examples:
  - name: Show a trusted client certificate for an existing application gateway.
    text: az network application-gateway client-cert show --gateway-name MyAppGateway -g MyResourceGroup --name MyCert
"""

helps['network application-gateway client-cert list'] = """
type: command
short-summary: List the existing trusted client certificate of the application gateway.
examples:
  - name: list all the trusted client certificate for an existing application gateway.
    text: az network application-gateway client-cert list --gateway-name MyAppGateway -g MyResourceGroup
"""

helps['network application-gateway ssl-profile'] = """
type: group
short-summary: Manage ssl profiles of application gateway.
"""

helps['network application-gateway ssl-profile add'] = """
type: command
short-summary: Add ssl profiles of the application gateway.
examples:
  - name: Add ssl profile for an existing application gateway.
    text: az network application-gateway ssl-profile add --gateway-name MyAppGateway -g MyResourceGroup --name MySslProfile
"""

helps['network application-gateway ssl-profile update'] = """
type: command
short-summary: Update ssl profiles of the application gateway.
examples:
  - name: Update ssl profile for an existing application gateway.
    text: az network application-gateway ssl-profile update --gateway-name MyAppGateway -g MyResourceGroup --name MySslProfile --client-auth-configuration False
"""

helps['network application-gateway ssl-profile remove'] = """
type: command
short-summary: Remove an existing ssl profiles of the application gateway.
examples:
  - name: Remove ssl profile for an existing application gateway.
    text: az network application-gateway ssl-profile remove --gateway-name MyAppGateway -g MyResourceGroup --name MySslProfile
"""

helps['network application-gateway ssl-profile show'] = """
type: command
short-summary: Show an existing ssl profiles of the application gateway.
examples:
  - name: Show ssl profile for an existing application gateway.
    text: az network application-gateway ssl-profile show --gateway-name MyAppGateway -g MyResourceGroup --name MySslProfile
"""

helps['network application-gateway ssl-profile list'] = """
type: command
short-summary: List the existing ssl profiles of the application gateway.
examples:
  - name: List all the ssl profile for an existing application gateway.
    text: az network application-gateway ssl-profile list --gateway-name MyAppGateway -g MyResourceGroup
"""

helps['network asg'] = """
type: group
short-summary: Manage application security groups (ASGs).
long-summary: >
    You can configure network security as a natural extension of an application's structure, ASG allows
    you to group virtual machines and define network security policies based on those groups. You can specify an
    application security group as the source and destination in a NSG security rule. For more information
    visit https://docs.microsoft.com/azure/virtual-network/create-network-security-group-preview
"""

helps['network asg create'] = """
type: command
short-summary: Create an application security group.
parameters:
  - name: --name -n
    short-summary: Name of the new application security group resource.
examples:
  - name: Create an application security group.
    text: az network asg create -g MyResourceGroup -n MyAsg --tags MyWebApp, CostCenter=Marketing
"""

helps['network asg delete'] = """
type: command
short-summary: Delete an application security group.
examples:
  - name: Delete an application security group.
    text: az network asg delete -g MyResourceGroup -n MyAsg
"""

helps['network asg list'] = """
type: command
short-summary: List all application security groups in a subscription.
examples:
  - name: List all application security groups in a subscription.
    text: az network asg list
"""

helps['network asg show'] = """
type: command
short-summary: Get details of an application security group.
examples:
  - name: Get details of an application security group.
    text: az network asg show -g MyResourceGroup -n MyAsg
"""

helps['network asg update'] = """
type: command
short-summary: Update an application security group.
long-summary: >
    This command can only be used to update the tags for an application security group.
    Name and resource group are immutable and cannot be updated.
examples:
  - name: Update an application security group with a modified tag value.
    text: az network asg update -g MyResourceGroup -n MyAsg --set tags.CostCenter=MyBusinessGroup
"""

helps['network ddos-protection'] = """
type: group
short-summary: Manage DDoS Protection Plans.
"""

helps['network ddos-protection create'] = """
type: command
short-summary: Create a DDoS protection plan.
parameters:
  - name: --vnets
    long-summary: >
        This parameter can only be used if all the VNets are within the same subscription as
        the DDoS protection plan. If this is not the case, set the protection plan on the VNet
        directly using the `az network vnet update` command.
examples:
  - name: Create a DDoS protection plan.
    text: az network ddos-protection create -g MyResourceGroup -n MyDdosPlan
  - name: Create a DDoS protection plan. (autogenerated)
    text: |
        az network ddos-protection create --location westus2 --name MyDdosPlan --resource-group MyResourceGroup
    crafted: true
"""

helps['network ddos-protection delete'] = """
type: command
short-summary: Delete a DDoS protection plan.
examples:
  - name: Delete a DDoS protection plan.
    text: az network ddos-protection delete -g MyResourceGroup -n MyDdosPlan
"""

helps['network ddos-protection list'] = """
type: command
short-summary: List DDoS protection plans.
examples:
  - name: List DDoS protection plans
    text: az network ddos-protection list
"""

helps['network ddos-protection show'] = """
type: command
short-summary: Show details of a DDoS protection plan.
examples:
  - name: Show details of a DDoS protection plan.
    text: az network ddos-protection show -g MyResourceGroup -n MyDdosPlan
"""

helps['network ddos-protection update'] = """
type: command
short-summary: Update a DDoS protection plan.
parameters:
  - name: --vnets
    long-summary: >
        This parameter can only be used if all the VNets are within the same subscription as
        the DDoS protection plan. If this is not the case, set the protection plan on the VNet
        directly using the `az network vnet update` command.
examples:
  - name: Add a Vnet to a DDoS protection plan in the same subscription.
    text: az network ddos-protection update -g MyResourceGroup -n MyDdosPlan --vnets MyVnet
  - name: Update a DDoS protection plan. (autogenerated)
    text: |
        az network ddos-protection update --name MyDdosPlan --remove tags.no_80 --resource-group MyResourceGroup
    crafted: true
"""

helps['network dns'] = """
type: group
short-summary: Manage DNS domains in Azure.
"""

helps['network dns record-set'] = """
type: group
short-summary: Manage DNS records and record sets.
"""

helps['network dns record-set a'] = """
type: group
short-summary: Manage DNS A records.
"""

helps['network dns record-set a add-record'] = """
type: command
short-summary: Add an A record.
examples:
  - name: Add an A record.
    text: |
        az network dns record-set a add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -a MyIpv4Address
"""

helps['network dns record-set a create'] = """
type: command
short-summary: Create an empty A record set.
examples:
  - name: Create an empty A record set.
    text: az network dns record-set a create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty A record set. (autogenerated)
    text: |
        az network dns record-set a create --name MyRecordSet --resource-group MyResourceGroup --ttl 30 --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set a delete'] = """
type: command
short-summary: Delete an A record set and all associated records.
examples:
  - name: Delete an A record set and all associated records.
    text: az network dns record-set a delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set a list'] = """
type: command
short-summary: List all A record sets in a zone.
examples:
  - name: List all A record sets in a zone.
    text: az network dns record-set a list -g MyResourceGroup -z www.mysite.com
"""

helps['network dns record-set a remove-record'] = """
type: command
short-summary: Remove an A record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove an A record from its record set.
    text: |
        az network dns record-set a remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -a MyIpv4Address
"""

helps['network dns record-set a show'] = """
type: command
short-summary: Get the details of an A record set.
examples:
  - name: Get the details of an A record set.
    text: az network dns record-set a show -g MyResourceGroup -n MyRecordSet -z www.mysite.com
"""

helps['network dns record-set a update'] = """
type: command
short-summary: Update an A record set.
examples:
  - name: Update an A record set.
    text: |
        az network dns record-set a update -g MyResourceGroup -n MyRecordSet \\
            -z www.mysite.com --metadata owner=WebTeam
  - name: Update an A record set. (autogenerated)
    text: |
        az network dns record-set a update --name MyRecordSet --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set aaaa'] = """
type: group
short-summary: Manage DNS AAAA records.
"""

helps['network dns record-set aaaa add-record'] = """
type: command
short-summary: Add an AAAA record.
examples:
  - name: Add an AAAA record.
    text: |
        az network dns record-set aaaa add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -a MyIpv6Address
"""

helps['network dns record-set aaaa create'] = """
type: command
short-summary: Create an empty AAAA record set.
examples:
  - name: Create an empty AAAA record set.
    text: az network dns record-set aaaa create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set aaaa delete'] = """
type: command
short-summary: Delete an AAAA record set and all associated records.
examples:
  - name: Delete an AAAA record set and all associated records.
    text: az network dns record-set aaaa delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set aaaa list'] = """
type: command
short-summary: List all AAAA record sets in a zone.
examples:
  - name: List all AAAA record sets in a zone.
    text: az network dns record-set aaaa list -g MyResourceGroup -z www.mysite.com
  - name: List all AAAA record sets in a zone. (autogenerated)
    text: |
        az network dns record-set aaaa list --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set aaaa remove-record'] = """
type: command
short-summary: Remove AAAA record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove an AAAA record from its record set.
    text: |
        az network dns record-set aaaa remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -a MyIpv6Address
"""

helps['network dns record-set aaaa show'] = """
type: command
short-summary: Get the details of an AAAA record set.
examples:
  - name: Get the details of an AAAA record set.
    text: az network dns record-set aaaa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set aaaa update'] = """
type: command
short-summary: Update an AAAA record set.
examples:
  - name: Update an AAAA record set.
    text: |
        az network dns record-set aaaa update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
"""

helps['network dns record-set caa'] = """
type: group
short-summary: Manage DNS CAA records.
"""

helps['network dns record-set caa add-record'] = """
type: command
short-summary: Add a CAA record.
examples:
  - name: Add a CAA record.
    text: |
        az network dns record-set caa add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --flags 0 --tag "issue" --value "ca.contoso.com"
"""

helps['network dns record-set caa create'] = """
type: command
short-summary: Create an empty CAA record set.
examples:
  - name: Create an empty CAA record set.
    text: az network dns record-set caa create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty CAA record set. (autogenerated)
    text: |
        az network dns record-set caa create --name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set caa delete'] = """
type: command
short-summary: Delete a CAA record set and all associated records.
examples:
  - name: Delete a CAA record set and all associated records.
    text: az network dns record-set caa delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Delete a CAA record set and all associated records. (autogenerated)
    text: |
        az network dns record-set caa delete --name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set caa list'] = """
type: command
short-summary: List all CAA record sets in a zone.
examples:
  - name: List all CAA record sets in a zone.
    text: az network dns record-set caa list -g MyResourceGroup -z www.mysite.com
"""

helps['network dns record-set caa remove-record'] = """
type: command
short-summary: Remove a CAA record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove a CAA record from its record set.
    text: |
        az network dns record-set caa remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --flags 0 --tag "issue" --value "ca.contoso.com"
"""

helps['network dns record-set caa show'] = """
type: command
short-summary: Get the details of a CAA record set.
examples:
  - name: Get the details of a CAA record set.
    text: az network dns record-set caa show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set caa update'] = """
type: command
short-summary: Update a CAA record set.
examples:
  - name: Update a CAA record set.
    text: |
        az network dns record-set caa update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
"""

helps['network dns record-set cname'] = """
type: group
short-summary: Manage DNS CNAME records.
"""

helps['network dns record-set cname create'] = """
type: command
short-summary: Create an empty CNAME record set.
examples:
  - name: Create an empty CNAME record set.
    text: az network dns record-set cname create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty CNAME record set. (autogenerated)
    text: |
        az network dns record-set cname create --name MyRecordSet --resource-group MyResourceGroup --ttl 30 --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set cname delete'] = """
type: command
short-summary: Delete a CNAME record set and its associated record.
examples:
  - name: Delete a CNAME record set and its associated record.
    text: az network dns record-set cname delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set cname list'] = """
type: command
short-summary: List the CNAME record set in a zone.
examples:
  - name: List the CNAME record set in a zone.
    text: az network dns record-set cname list -g MyResourceGroup -z www.mysite.com
"""

helps['network dns record-set cname remove-record'] = """
type: command
short-summary: Remove a CNAME record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove a CNAME record from its record set.
    text: |
        az network dns record-set cname remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -c www.contoso.com
"""

helps['network dns record-set cname set-record'] = """
type: command
short-summary: Set the value of a CNAME record.
examples:
  - name: Set the value of a CNAME record.
    text: |
        az network dns record-set cname set-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -c www.contoso.com
"""

helps['network dns record-set cname show'] = """
type: command
short-summary: Get the details of a CNAME record set.
examples:
  - name: Get the details of a CNAME record set.
    text: az network dns record-set cname show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set list'] = """
type: command
short-summary: List all record sets within a DNS zone.
examples:
  - name: List all "@" record sets within this zone.
    text: az network dns record-set list -g MyResourceGroup -z www.mysite.com --query "[?name=='@']"
"""

helps['network dns record-set mx'] = """
type: group
short-summary: Manage DNS MX records.
"""

helps['network dns record-set mx add-record'] = """
type: command
short-summary: Add an MX record.
examples:
  - name: Add an MX record.
    text: |
        az network dns record-set mx add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -e mail.mysite.com -p 10
"""

helps['network dns record-set mx create'] = """
type: command
short-summary: Create an empty MX record set.
examples:
  - name: Create an empty MX record set.
    text: az network dns record-set mx create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty MX record set. (autogenerated)
    text: |
        az network dns record-set mx create --name MyRecordSet --resource-group MyResourceGroup --ttl 30 --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set mx delete'] = """
type: command
short-summary: Delete an MX record set and all associated records.
examples:
  - name: Delete an MX record set and all associated records.
    text: az network dns record-set mx delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set mx list'] = """
type: command
short-summary: List all MX record sets in a zone.
examples:
  - name: List all MX record sets in a zone.
    text: az network dns record-set mx list -g MyResourceGroup -z www.mysite.com
  - name: List all MX record sets in a zone (autogenerated)
    text: |
        az network dns record-set mx list --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set mx remove-record'] = """
type: command
short-summary: Remove an MX record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove an MX record from its record set.
    text: |
        az network dns record-set mx remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -e mail.mysite.com -p 10
"""

helps['network dns record-set mx show'] = """
type: command
short-summary: Get the details of an MX record set.
examples:
  - name: Get the details of an MX record set.
    text: az network dns record-set mx show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set mx update'] = """
type: command
short-summary: Update an MX record set.
examples:
  - name: Update an MX record set.
    text: |
        az network dns record-set mx update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
  - name: Update an MX record set. (autogenerated)
    text: |
        az network dns record-set mx update --name MyRecordSet --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ns'] = """
type: group
short-summary: Manage DNS NS records.
"""

helps['network dns record-set ns add-record'] = """
type: command
short-summary: Add an NS record.
examples:
  - name: Add an NS record.
    text: |
        az network dns record-set ns add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -d ns.mysite.com
"""

helps['network dns record-set ns create'] = """
type: command
short-summary: Create an empty NS record set.
examples:
  - name: Create an empty NS record set.
    text: az network dns record-set ns create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty NS record set. (autogenerated)
    text: |
        az network dns record-set ns create --name MyRecordSet --resource-group MyResourceGroup --ttl 30 --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ns delete'] = """
type: command
short-summary: Delete an NS record set and all associated records.
examples:
  - name: Delete an NS record set and all associated records.
    text: az network dns record-set ns delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Delete an NS record set and all associated records. (autogenerated)
    text: |
        az network dns record-set ns delete --name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --yes --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ns list'] = """
type: command
short-summary: List all NS record sets in a zone.
examples:
  - name: List all NS record sets in a zone.
    text: az network dns record-set ns list -g MyResourceGroup -z www.mysite.com
"""

helps['network dns record-set ns remove-record'] = """
type: command
short-summary: Remove an NS record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove an NS record from its record set.
    text: |
        az network dns record-set ns remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -d ns.mysite.com
  - name: Remove an NS record from its record set. (autogenerated)
    text: |
        az network dns record-set ns remove-record --keep-empty-record-set --nsdname ns.mysite.com --record-set-name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ns show'] = """
type: command
short-summary: Get the details of an NS record set.
examples:
  - name: Get the details of an NS record set.
    text: az network dns record-set ns show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set ns update'] = """
type: command
short-summary: Update an NS record set.
examples:
  - name: Update an NS record set.
    text: |
        az network dns record-set ns update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
  - name: Update an NS record set. (autogenerated)
    text: |
        az network dns record-set ns update --name MyRecordSet --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ptr'] = """
type: group
short-summary: Manage DNS PTR records.
"""

helps['network dns record-set ptr add-record'] = """
type: command
short-summary: Add a PTR record.
examples:
  - name: Add a PTR record.
    text: |
        az network dns record-set ptr add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -d another.site.com
"""

helps['network dns record-set ptr create'] = """
type: command
short-summary: Create an empty PTR record set.
examples:
  - name: Create an empty PTR record set.
    text: az network dns record-set ptr create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty PTR record set. (autogenerated)
    text: |
        az network dns record-set ptr create --name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ptr delete'] = """
type: command
short-summary: Delete a PTR record set and all associated records.
examples:
  - name: Delete a PTR record set and all associated records.
    text: az network dns record-set ptr delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Delete a PTR record set and all associated records. (autogenerated)
    text: |
        az network dns record-set ptr delete --name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --yes --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ptr list'] = """
type: command
short-summary: List all PTR record sets in a zone.
examples:
  - name: List all PTR record sets in a zone.
    text: az network dns record-set ptr list -g MyResourceGroup -z www.mysite.com
  - name: List all PTR record sets in a zone. (autogenerated)
    text: |
        az network dns record-set ptr list --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set ptr remove-record'] = """
type: command
short-summary: Remove a PTR record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove a PTR record from its record set.
    text: |
        az network dns record-set ptr remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -d another.site.com
"""

helps['network dns record-set ptr show'] = """
type: command
short-summary: Get the details of a PTR record set.
examples:
  - name: Get the details of a PTR record set.
    text: az network dns record-set ptr show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set ptr update'] = """
type: command
short-summary: Update a PTR record set.
examples:
  - name: Update a PTR record set.
    text: |
        az network dns record-set ptr update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
"""

helps['network dns record-set soa'] = """
type: group
short-summary: Manage a DNS SOA record.
"""

helps['network dns record-set soa show'] = """
type: command
short-summary: Get the details of an SOA record.
examples:
  - name: Get the details of an SOA record.
    text: az network dns record-set soa show -g MyResourceGroup -z www.mysite.com
  - name: Get the details of an SOA record (autogenerated)
    text: |
        az network dns record-set soa show --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set soa update'] = """
type: command
short-summary: Update properties of an SOA record.
examples:
  - name: Update properties of an SOA record.
    text: |
        az network dns record-set soa update -g MyResourceGroup -z www.mysite.com \\
            -e myhostmaster.mysite.com
  - name: Update properties of an SOA record. (autogenerated)
    text: |
        az network dns record-set soa update --email myhostmaster.mysite.com --only-show-errors --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set srv'] = """
type: group
short-summary: Manage DNS SRV records.
"""

helps['network dns record-set srv add-record'] = """
type: command
short-summary: Add an SRV record.
examples:
  - name: Add an SRV record.
    text: |
        az network dns record-set srv add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -t webserver.mysite.com -r 8081 -p 10 -w 10
"""

helps['network dns record-set srv create'] = """
type: command
short-summary: Create an empty SRV record set.
examples:
  - name: Create an empty SRV record set.
    text: |
        az network dns record-set srv create -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet
  - name: Create an empty SRV record set. (autogenerated)
    text: |
        az network dns record-set srv create --metadata owner=WebTeam --name MyRecordSet --resource-group MyResourceGroup --ttl 30 --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set srv delete'] = """
type: command
short-summary: Delete an SRV record set and all associated records.
examples:
  - name: Delete an SRV record set and all associated records.
    text: az network dns record-set srv delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set srv list'] = """
type: command
short-summary: List all SRV record sets in a zone.
examples:
  - name: List all SRV record sets in a zone.
    text: az network dns record-set srv list -g MyResourceGroup -z www.mysite.com
"""

helps['network dns record-set srv remove-record'] = """
type: command
short-summary: Remove an SRV record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove an SRV record from its record set.
    text: |
        az network dns record-set srv remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -t webserver.mysite.com -r 8081 -p 10 -w 10
"""

helps['network dns record-set srv show'] = """
type: command
short-summary: Get the details of an SRV record set.
examples:
  - name: Get the details of an SRV record set.
    text: az network dns record-set srv show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set srv update'] = """
type: command
short-summary: Update an SRV record set.
examples:
  - name: Update an SRV record set.
    text: |
        az network dns record-set srv update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
"""

helps['network dns record-set txt'] = """
type: group
short-summary: Manage DNS TXT records.
"""

helps['network dns record-set txt add-record'] = """
type: command
short-summary: Add a TXT record.
examples:
  - name: Add a TXT record.
    text: |
        az network dns record-set txt add-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -v Owner=WebTeam
"""

helps['network dns record-set txt create'] = """
type: command
short-summary: Create an empty TXT record set.
examples:
  - name: Create an empty TXT record set.
    text: az network dns record-set txt create -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Create an empty TXT record set. (autogenerated)
    text: |
        az network dns record-set txt create --name MyRecordSet --resource-group MyResourceGroup --ttl 30 --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set txt delete'] = """
type: command
short-summary: Delete a TXT record set and all associated records.
examples:
  - name: Delete a TXT record set and all associated records.
    text: az network dns record-set txt delete -g MyResourceGroup -z www.mysite.com -n MyRecordSet
"""

helps['network dns record-set txt list'] = """
type: command
short-summary: List all TXT record sets in a zone.
examples:
  - name: List all TXT record sets in a zone.
    text: az network dns record-set txt list -g MyResourceGroup -z www.mysite.com
"""

helps['network dns record-set txt remove-record'] = """
type: command
short-summary: Remove a TXT record from its record set.
long-summary: >
    By default, if the last record in a set is removed, the record set is deleted.
    To retain the empty record set, include --keep-empty-record-set.
examples:
  - name: Remove a TXT record from its record set.
    text: |
        az network dns record-set txt remove-record -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet -v Owner=WebTeam
"""

helps['network dns record-set txt show'] = """
type: command
short-summary: Get the details of a TXT record set.
examples:
  - name: Get the details of a TXT record set.
    text: az network dns record-set txt show -g MyResourceGroup -z www.mysite.com -n MyRecordSet
  - name: Get the details of a TXT record set. (autogenerated)
    text: |
        az network dns record-set txt show --name MyRecordSet --resource-group MyResourceGroup --subscription MySubscription --zone-name www.mysite.com
    crafted: true
"""

helps['network dns record-set txt update'] = """
type: command
short-summary: Update a TXT record set.
examples:
  - name: Update a TXT record set.
    text: |
        az network dns record-set txt update -g MyResourceGroup -z www.mysite.com \\
            -n MyRecordSet --metadata owner=WebTeam
  - name: Update a TXT record set. (autogenerated)
    text: |
        az network dns record-set txt update --name MyRecordSet --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup --zone-name www.mysite.com
    crafted: true
"""

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
  - name: Create a DNS zone with delegation in the parent within the same subscription and resource group
    text: >
        az network dns zone create -g MyResourceGroup -n books.mysite.com -p mysite.com
  - name: Create a DNS zone with delegation in the parent in different subscription
    text: >
        az network dns zone create -g MyResourceGroup -n books.mysite.com -p "/subscriptions/**67e2/resourceGroups/OtherRg/providers/Microsoft.Network/dnszones/mysite.com"
"""

helps['network dns zone delete'] = """
type: command
short-summary: Delete a DNS zone and all associated records.
examples:
  - name: Delete a DNS zone using a fully qualified domain name.
    text: >
        az network dns zone delete -g MyResourceGroup -n www.mysite.com
"""

helps['network dns zone export'] = """
type: command
short-summary: Export a DNS zone as a DNS zone file.
examples:
  - name: Export a DNS zone as a DNS zone file.
    text: >
        az network dns zone export -g MyResourceGroup -n www.mysite.com -f mysite_com_zone.txt
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
examples:
  - name: List DNS zones in a resource group.
    text: >
        az network dns zone list -g MyResourceGroup
"""

helps['network dns zone show'] = """
type: command
short-summary: Get a DNS zone parameters. Does not show DNS records within the zone.
examples:
  - name: List DNS zones in a resource group.
    text: >
        az network dns zone show -g MyResourceGroup -n www.mysite.com
"""

helps['network dns zone update'] = """
type: command
short-summary: Update a DNS zone properties. Does not modify DNS records within the zone.
parameters:
  - name: --if-match
    short-summary: Update only if the resource with the same ETAG exists.
examples:
  - name: Update a DNS zone properties to change the user-defined value of a previously set tag.
    text: >
        az network dns zone update -g MyResourceGroup -n www.mysite.com --tags CostCenter=Marketing
  - name: Update a DNS zone properties (autogenerated)
    text: |
        az network dns zone update --name www.mysite.com --remove tags.no_80 --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route'] = """
type: group
short-summary: Manage dedicated private network fiber connections to Azure.
long-summary: >
    To learn more about ExpressRoute circuits visit
    https://docs.microsoft.com/azure/expressroute/howto-circuit-cli
"""

helps['network express-route auth'] = """
type: group
short-summary: Manage authentication of an ExpressRoute circuit.
long-summary: >
    To learn more about ExpressRoute circuit authentication visit
    https://docs.microsoft.com/azure/expressroute/howto-linkvnet-cli#connect-a-virtual-network-in-a-different-subscription-to-a-circuit
"""

helps['network express-route auth create'] = """
type: command
short-summary: Create a new link authorization for an ExpressRoute circuit.
examples:
  - name: Create a new link authorization for an ExpressRoute circuit.
    text: >
        az network express-route auth create --circuit-name MyCircuit -g MyResourceGroup -n MyAuthorization
"""

helps['network express-route auth delete'] = """
type: command
short-summary: Delete a link authorization of an ExpressRoute circuit.
examples:
  - name: Delete a link authorization of an ExpressRoute circuit.
    text: >
        az network express-route auth delete --circuit-name MyCircuit -g MyResourceGroup -n MyAuthorization
"""

helps['network express-route auth list'] = """
type: command
short-summary: List link authorizations of an ExpressRoute circuit.
examples:
  - name: List link authorizations of an ExpressRoute circuit.
    text: >
        az network express-route auth list -g MyResourceGroup --circuit-name MyCircuit
  - name: List link authorizations of an ExpressRoute circuit. (autogenerated)
    text: |
        az network express-route auth list --circuit-name MyCircuit --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network express-route auth show'] = """
type: command
short-summary: Get the details of a link authorization of an ExpressRoute circuit.
examples:
  - name: Get the details of a link authorization of an ExpressRoute circuit.
    text: >
        az network express-route auth show -g MyResourceGroup --circuit-name MyCircuit -n MyAuthorization
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
examples:
  - name: Create an ExpressRoute circuit.
    text: >
        az network express-route create --bandwidth 200 -n MyCircuit --peering-location "Silicon Valley" -g MyResourceGroup --provider "Equinix" -l "West US" --sku-family MeteredData --sku-tier Standard
"""

helps['network express-route delete'] = """
type: command
short-summary: Delete an ExpressRoute circuit.
examples:
  - name: Delete an ExpressRoute circuit.
    text: >
        az network express-route delete -n MyCircuit -g MyResourceGroup
  - name: Delete an ExpressRoute circuit. (autogenerated)
    text: |
        az network express-route delete --name MyCircuit --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network express-route gateway'] = """
type: group
short-summary: Manage ExpressRoute gateways.
"""

helps['network express-route gateway connection'] = """
type: group
short-summary: Manage ExpressRoute gateway connections.
"""

helps['network express-route gateway connection create'] = """
type: command
short-summary: Create an ExpressRoute gateway connection.
examples:
  - name: Create an ExpressRoute gateway connection.
    text: |
        az network express-route gateway connection create --gateway-name MyGateway -n MyExpressRouteConnection -g MyResourceGroup --peering /subscriptions/MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/expressRouteCircuits/MyCircuit/peerings/AzurePrivatePeering --associated-route-table /MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualHubs/MyHub/hubRouteTables/MyRouteTable1 --propagated-route-tables /MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualHubs/MyHub/hubRouteTables/MyRouteTable1 /MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualHubs/MyHub/hubRouteTables/MyRouteTable2 --labels label1 label2
  - name: Create an ExpressRoute gateway connection. (autogenerated)
    text: |
        az network express-route gateway connection create --gateway-name MyGateway --name MyExpressRouteConnection --peering /subscriptions/MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/expressRouteCircuits/MyCircuit/peerings/AzurePrivatePeering --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway connection delete'] = """
type: command
short-summary: Delete an ExpressRoute gateway connection.
examples:
  - name: Delete an ExpressRoute gateway connection. (autogenerated)
    text: |
        az network express-route gateway connection delete --gateway-name MyGateway --name MyExpressRouteConnection --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway connection list'] = """
type: command
short-summary: List ExpressRoute gateway connections.
examples:
  - name: List ExpressRoute gateway connections. (autogenerated)
    text: |
        az network express-route gateway connection list --gateway-name MyGateway --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway connection show'] = """
type: command
short-summary: Get the details of an ExpressRoute gateway connection.
examples:
  - name: Get the details of an ExpressRoute gateway connection. (autogenerated)
    text: |
        az network express-route gateway connection show --gateway-name MyGateway --name MyExpressRouteConnection --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway connection update'] = """
type: command
short-summary: Update an ExpressRoute gateway connection.
examples:
  - name: Update an ExpressRoute gateway connection.
    text: |
        az network express-route gateway connection update --gateway-name MyGateway -n MyExpressRouteConnection -g MyResourceGroup --peering /subscriptions/MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/expressRouteCircuits/MyCircuit/peerings/AzurePrivatePeering --associated-route-table /MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualHubs/MyHub/hubRouteTables/MyRouteTable1 --propagated-route-tables /MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualHubs/MyHub/hubRouteTables/MyRouteTable1 /MySub/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualHubs/MyHub/hubRouteTables/MyRouteTable2 --labels label1 label2
"""

helps['network express-route gateway create'] = """
type: command
short-summary: Create an ExpressRoute gateway.
"""

helps['network express-route gateway delete'] = """
type: command
short-summary: Delete an ExpressRoute gateway.
examples:
  - name: Delete an ExpressRoute gateway. (autogenerated)
    text: |
        az network express-route gateway delete --name MyExpressRouteGateway --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway list'] = """
type: command
short-summary: List ExpressRoute gateways.
examples:
  - name: List ExpressRoute gateways. (autogenerated)
    text: |
        az network express-route gateway list --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway show'] = """
type: command
short-summary: Get the details of an ExpressRoute gateway.
examples:
  - name: Get the details of an ExpressRoute gateway. (autogenerated)
    text: |
        az network express-route gateway show --name MyExpressRouteGateway --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route gateway update'] = """
type: command
short-summary: Update settings of an ExpressRoute gateway.
"""

helps['network express-route get-stats'] = """
type: command
short-summary: Get the statistics of an ExpressRoute circuit.
examples:
  - name: Get the statistics of an ExpressRoute circuit.
    text: >
        az network express-route get-stats -g MyResourceGroup -n MyCircuit
"""

helps['network express-route list'] = """
type: command
short-summary: List all ExpressRoute circuits for the current subscription.
examples:
  - name: List all ExpressRoute circuits for the current subscription.
    text: >
        az network express-route list -g MyResourceGroup
"""

helps['network express-route list-arp-tables'] = """
type: command
short-summary: Show the current Address Resolution Protocol (ARP) table of an ExpressRoute circuit.
examples:
  - name: Show the current Address Resolution Protocol (ARP) table of an ExpressRoute circuit.
    text: |
        az network express-route list-arp-tables -g MyResourceGroup -n MyCircuit \\
            --path primary --peering-name AzurePrivatePeering
"""

helps['network express-route list-route-tables'] = """
type: command
short-summary: Show the current routing table of an ExpressRoute circuit peering.
examples:
  - name: Show the current routing table of an ExpressRoute circuit peering.
    text: |
        az network express-route list-route-tables -g MyResourceGroup -n MyCircuit \\
            --path primary --peering-name AzurePrivatePeering
"""

helps['network express-route list-route-tables-summary'] = """
type: command
short-summary: Show the current routing table summary of an ExpressRoute circuit peering.
examples:
  - name: List Route Table Summary
    text: |
        az network express-route list-route-tables-summary -g MyResourceGroup -n MyCircuit --path primary --peering-name AzurePrivatePeering
"""

helps['network express-route list-service-providers'] = """
type: command
short-summary: List available ExpressRoute service providers.
examples:
  - name: List available ExpressRoute service providers.
    text: az network express-route list-service-providers
"""

helps['network express-route peering'] = """
type: group
short-summary: Manage ExpressRoute peering of an ExpressRoute circuit.
"""

helps['network express-route peering connection'] = """
type: group
short-summary: Manage ExpressRoute circuit connections.
"""

helps['network express-route peering connection create'] = """
type: command
short-summary: Create connections between two ExpressRoute circuits.
examples:
  - name: Create connection between two ExpressRoute circuits with AzurePrivatePeering settings.
    text: |
        az network express-route peering connection create -g MyResourceGroup --circuit-name \\
            MyCircuit --peering-name AzurePrivatePeering -n myConnection --peer-circuit \\
            MyOtherCircuit --address-prefix 104.0.0.0/29
"""

helps['network express-route peering connection delete'] = """
type: command
short-summary: Delete an ExpressRoute circuit connection.
examples:
  - name: Delete an ExpressRoute circuit connection. (autogenerated)
    text: |
        az network express-route peering connection delete --circuit-name MyCircuit --name MyPeeringConnection --peering-name MyPeering --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route peering connection show'] = """
type: command
short-summary: Get the details of an ExpressRoute circuit connection.
"""

helps['network express-route peering connection list'] = """
type: command
short-summary: List all global reach connections associated with a private peering in an express route circuit.
examples:
  - name: List ExpressRouteCircuit Connection
    text: |
        az network express-route peering connection list --circuit-name MyCircuit --peering-name MyPeering --resource-group MyResourceGroup
"""

helps['network express-route peering connection ipv6-config'] = """
type: group
short-summary: Manage ExpressRoute circuit connection configs.
"""

helps['network express-route peering connection ipv6-config set'] = """
type: command
short-summary: Set connection config to ExpressRoute circuit connection.
examples:
  - name: Set connection config to ExpressRoute circuit connection.
    text: |
        az network express-route peering connection ipv6-config set -g MyResourceGroup --circuit-name \\
            MyCircuit --peering-name AzurePrivatePeering -n myConnection --address-prefix .../125
"""

helps['network express-route peering connection ipv6-config remove'] = """
type: command
short-summary: Remove connection config to ExpressRoute circuit connection.
examples:
  - name: Remove connection config to ExpressRoute circuit connection.
    text: |
        az network express-route peering connection ipv6-config remove -g MyResourceGroup --circuit-name \\
            MyCircuit --peering-name AzurePrivatePeering -n myConnection
"""

helps['network express-route peering create'] = """
type: command
short-summary: Create peering settings for an ExpressRoute circuit.
examples:
  - name: Create Microsoft Peering settings with IPv4 configuration.
    text: |
        az network express-route peering create -g MyResourceGroup --circuit-name MyCircuit \\
            --peering-type MicrosoftPeering --peer-asn 10002 --vlan-id 103 \\
            --primary-peer-subnet 101.0.0.0/30 --secondary-peer-subnet 102.0.0.0/30 \\
            --advertised-public-prefixes 101.0.0.0/30
  - name: Create Microsoft Peering settings with IPv6 configuration.
    text: |
        az network express-route peering create -g MyResourceGroup --circuit-name MyCircuit \\
            --peering-type AzurePrivatePeering --peer-asn 10002 --vlan-id 103 --ip-version ipv6\\
            --primary-peer-subnet 2002:db00::/126 --secondary-peer-subnet 2003:db00::/126
  - name: Create peering settings for an ExpressRoute circuit. (autogenerated)
    text: |
        az network express-route peering create --circuit-name MyCircuit --peer-asn 10002 --peering-type AzurePublicPeering --primary-peer-subnet 101.0.0.0/30 --resource-group MyResourceGroup --secondary-peer-subnet 102.0.0.0/30 --shared-key Abc123 --vlan-id 103
    crafted: true
"""

helps['network express-route peering delete'] = """
type: command
short-summary: Delete peering settings.
examples:
  - name: Delete private peering.
    text: >
        az network express-route peering delete -g MyResourceGroup --circuit-name MyCircuit -n AzurePrivatePeering
"""

helps['network express-route peering list'] = """
type: command
short-summary: List peering settings of an ExpressRoute circuit.
examples:
  - name: List peering settings of an ExpressRoute circuit.
    text: >
        az network express-route peering list -g MyResourceGroup --circuit-name MyCircuit
"""

helps['network express-route peering peer-connection'] = """
type: group
short-summary: Manage ExpressRoute circuit peer connections.
"""

helps['network express-route peering show'] = """
type: command
short-summary: Get the details of an express route peering.
examples:
  - name: Get private peering details of an ExpressRoute circuit.
    text: >
        az network express-route peering show -g MyResourceGroup --circuit-name MyCircuit -n AzurePrivatePeering
"""

helps['network express-route peering update'] = """
type: command
short-summary: Update peering settings of an ExpressRoute circuit.
examples:
  - name: Add IPv6 Microsoft Peering settings to existing IPv4 config.
    text: |
        az network express-route peering update -g MyResourceGroup --circuit-name MyCircuit \\
            --ip-version ipv6 --primary-peer-subnet 2002:db00::/126 \\
            --secondary-peer-subnet 2003:db00::/126 --advertised-public-prefixes 2002:db00::/126
    supported-profiles: latest
  - name: Update peering settings of an ExpressRoute circuit. (autogenerated)
    text: |
        az network express-route peering update --circuit-name MyCircuit --name MyPeering --peer-asn 10002 --primary-peer-subnet 2002:db00::/126 --resource-group MyResourceGroup --secondary-peer-subnet 2003:db00::/126 --shared-key Abc123 --vlan-id 103
    crafted: true
"""

helps['network express-route peering get-stats'] = """
type: command
short-summary: Get all traffic stats of an ExpressRoute peering.
examples:
  - name: Get ExpressRoute Circuit Peering Traffic Stats
    text: |
        az network express-route peering get-stats --circuit-name MyCircuit --name MyPeering --resource-group MyResourceGroup
"""

helps['network express-route port'] = """
type: group
short-summary: Manage ExpressRoute ports.
"""

helps['network express-route port create'] = """
type: command
short-summary: Create an ExpressRoute port.
examples:
  - name: Create an ExpressRoute port. (autogenerated)
    text: |
        az network express-route port create --bandwidth 200 --encapsulation Dot1Q --location westus2 --name MyExpressRoutePort --peering-location westus --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route port delete'] = """
type: command
short-summary: Delete an ExpressRoute port.
examples:
  - name: Delete an ExpressRoute port. (autogenerated)
    text: |
        az network express-route port delete --name MyExpressRoutePort --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route port generate-loa'] = """
type: command
short-summary: Generate and download a letter of authorization for the requested ExpressRoutePort
"""

helps['network express-route port link'] = """
type: group
short-summary: View ExpressRoute links.
"""

helps['network express-route port link list'] = """
type: command
short-summary: List ExpressRoute links.
examples:
  - name: List ExpressRoute links. (autogenerated)
    text: |
        az network express-route port link list --port-name MyPort --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route port link show'] = """
type: command
short-summary: Get the details of an ExpressRoute link.
examples:
  - name: Get the details of an ExpressRoute link. (autogenerated)
    text: |
        az network express-route port link show --name MyLinkExpressRoutePort --port-name MyPort --resource-group MyResourceGroup
    crafted: true
"""


helps['network express-route port link update'] = """
type: command
short-summary: Manage MACsec configuration of an ExpressRoute Link.
examples:
  - name: Enable MACsec on ExpressRoute Direct Ports once at a time.
    text: |-
        az network express-route port link update \\
        --resource-group MyResourceGroup \\
        --port-name MyExpressRoutePort \\
        --name link1 \\
        --macsec-ckn-secret-identifier MacSecCKNSecretID \\
        --macsec-cak-secret-identifier MacSecCAKSecretID \\
        --macsec-cipher GcmAes128
  - name: Enable administrative state of an ExpressRoute Link.
    text: |-
        az network express-route port link update \\
        --resource-group MyResourceGroup \\
        --port-name MyExpressRoutePort \\
        --name link2 \\
        --admin-state Enabled
"""

helps['network express-route port list'] = """
type: command
short-summary: List ExpressRoute ports.
examples:
  - name: List ExpressRoute ports. (autogenerated)
    text: |
        az network express-route port list --resource-group myresourcegroup
    crafted: true
"""

helps['network express-route port location'] = """
type: group
short-summary: View ExpressRoute port location information.
"""

helps['network express-route port location list'] = """
type: command
short-summary: List ExpressRoute port locations.
"""

helps['network express-route port location show'] = """
type: command
short-summary: Get the details of an ExpressRoute port location.
examples:
  - name: Get the details of an ExpressRoute port location. (autogenerated)
    text: |
        az network express-route port location show --location westus2
    crafted: true
"""

helps['network express-route port show'] = """
type: command
short-summary: Get the details of an ExpressRoute port.
examples:
  - name: Get the details of an ExpressRoute port. (autogenerated)
    text: |
        az network express-route port show --name MyExpressRoutePort --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route port update'] = """
type: command
short-summary: Update settings of an ExpressRoute port.
examples:
  - name: Update settings of an ExpressRoute port (autogenerated)
    text: |
        az network express-route port update --name MyExpressRoutePort --resource-group MyResourceGroup
    crafted: true
"""

helps['network express-route port identity'] = """
type: group
short-summary: Manage the managed service identity of an ExpressRoute Port
"""

helps['network express-route port identity assign'] = """
type: command
short-summary: Assign a managed service identity to an ExpressRoute Port
examples:
  - name: Assign an identity to the ExpressRoute Port
    text: |-
        az network express-route port identity assign \\
        --resource-group MyResourceGroupg \\
        --name MyExpressRoutePort \\
        --identity MyUserAssignedManagedServiceIdentity
"""

helps['network express-route port identity remove'] = """
type: command
short-summary: Remove the managed service identity of an ExpressRoute Port
examples:
  - name: Remove an identity of the ExpressRoute Port
    text: az network express-route port identity remove -g MyResourceGroup --name MyExpressRoutePort
"""

helps['network express-route port identity show'] = """
type: command
short-summary: Show the managed service identity of an ExpressRoute Port
examples:
  - name: Show an identity of the ExpressRoute Port
    text: az network express-route port identity show -g MyResourceGroup --name MyExpressRoutePort
"""

helps['network express-route show'] = """
type: command
short-summary: Get the details of an ExpressRoute circuit.
examples:
  - name: Get the details of an ExpressRoute circuit.
    text: >
        az network express-route show -n MyCircuit -g MyResourceGroup
"""

helps['network express-route update'] = """
type: command
short-summary: Update settings of an ExpressRoute circuit.
examples:
  - name: Change the SKU of an ExpressRoute circuit from Standard to Premium.
    text: >
        az network express-route update -n MyCircuit -g MyResourceGroup --sku-tier Premium
"""

helps['network express-route wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the ExpressRoute is met.
examples:
  - name: Pause executing next line of CLI script until the ExpressRoute circuit is successfully provisioned.
    text: az network express-route wait -n MyCircuit -g MyResourceGroup --created
"""

helps['network cross-region-lb'] = """
type: group
short-summary: Manage and configure cross-region load balancers.
long-summary: To learn more about Azure Load Balancer visit https://docs.microsoft.com/azure/load-balancer/load-balancer-get-started-internet-arm-cli
"""

helps['network cross-region-lb create'] = """
type: command
short-summary: Create a cross-region load balancer.
examples:
  - name: Create a basic load balancer.
    text: >
        az network cross-region-lb create -g MyResourceGroup -n MyLb
"""

helps['network cross-region-lb update'] = """
type: command
short-summary: Update a cross-region load balancer.
long-summary: >
    This command can only be used to update the tags for a load balancer. Name and resource group are immutable and cannot be updated.
examples:
  - name: Update the tags of a load balancer.
    text: az network cross-region-lb update -g MyResourceGroup -n MyLb --set tags.CostCenter=MyBusinessGroup
"""

helps['network cross-region-lb list'] = """
type: command
short-summary: List load balancers.
examples:
  - name: List load balancers.
    text: az network cross-region-lb list -g MyResourceGroup
"""

helps['network cross-region-lb wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the cross-region load balancer is met.
examples:
  - name: Wait for load balancer to return as created.
    text: |
        az network cross-region-lb wait -g MyResourceGroup -n MyLB --created
"""

helps['network cross-region-lb address-pool'] = """
type: group
short-summary: Manage address pools of a cross-region load balancer.
"""

helps['network cross-region-lb address-pool create'] = """
type: command
short-summary: Create an address pool.
parameters:
  - name: --backend-address
    short-summary: Backend addresses information for backend address pool.
    long-summary: |
        Usage: --backend-address name=addr1 frontend-ip-address=regional_lb_resource_id

        name: Required. The name of the backend address.
        frontend-ip-address: Required. Resource id of a regional load balancer.

        Multiple backend addresses can be specified by using more than one `--backend-address` argument.
  - name: --backend-addresses-config-file --config-file
    short-summary: A config file used to set backend addresses. This argument is for experienced users. You may encounter parse errors if the json file is invalid.
    long-summary: |
        Usage: --backend-addresses-config-file @"{config_file.json}"

        A example config file is
        [
          {
            "name": "address1",
            "frontendIpAddress": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb1"
          },
          {
            "name": "address2",
            "frontendIpAddress": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2"
          }
        ]
examples:
  - name: Create an address pool.
    text: az network cross-region-lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool
  - name: Create an address pool with several backend addresses using key-value arguments.
    text: az network cross-region-lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-address name=addr1 frontend-ip-address=/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb1 --backend-address name=addr2 frontend-ip-address=/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2
  - name: Create an address pool with several backend addresses using config file
    text: az network cross-region-lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses-config-file @config_file.json
"""

helps['network cross-region-lb address-pool delete'] = """
type: command
short-summary: Delete an address pool.
examples:
  - name: Delete an address pool.
    text: az network cross-region-lb address-pool delete -g MyResourceGroup --lb-name MyLb -n MyAddressPool
"""

helps['network cross-region-lb address-pool address'] = """
type: group
short-summary: Manage backend addresses of the cross-region load balance backend address pool.
"""

helps['network cross-region-lb address-pool address add'] = """
type: command
short-summary: Add one backend address into the load balance backend address pool.
examples:
  - name: Add one backend address into the load balance backend address pool.
    text: az network cross-region-lb address-pool address add -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress --frontend-ip-address /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2
"""

helps['network cross-region-lb address-pool address remove'] = """
type: command
short-summary: Remove one backend address from the load balance backend address pool.
examples:
  - name: Remove one backend address from the load balance backend address pool.
    text: az network cross-region-lb address-pool address remove -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress
"""

helps['network cross-region-lb address-pool address list'] = """
type: command
short-summary: List all backend addresses of the load balance backend address pool.
examples:
  - name: List all backend addresses of the load balance backend address pool.
    text: az network cross-region-lb address-pool address list -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool
"""

helps['network lb address-pool tunnel-interface'] = """
type: group
short-summary: Manage tunnel interfaces of a load balancer.
"""

helps['network lb address-pool tunnel-interface add'] = """
type: command
short-summary: Add one tunnel interface into the load balance tunnel interface pool.
examples:
  - name: Add one tunnel interface into the load balance tunnel interface pool.
    text: az network lb address-pool tunnel-interface add -g MyResourceGroup --lb-name MyLb --address-pool MyAddressPool \
    --type external --protocol vxlan --identifier 901 --port 10000
"""

helps['network lb address-pool tunnel-interface update'] = """
type: command
short-summary: update one tunnel interface of load balance tunnel interface pool.
examples:
  - name: update one tunnel interface of load balance tunnel interface pool.
    text: az network lb address-pool tunnel-interface update -g MyResourceGroup --lb-name MyLb --address-pool MyAddressPool \
    --type external --protocol vxlan --identifier 901 --port 10000 --index 0
"""

helps['network lb address-pool tunnel-interface remove'] = """
type: command
short-summary: Remove one tunnel interface from the load balance tunnel interface pool.
examples:
  - name: Remove one tunnel interface from the load balance tunnel interface pool.
    text: az network lb address-pool tunnel-interface remove -g MyResourceGroup --lb-name MyLb  --address-pool MyAddressPool \
    --index 0
"""

helps['network lb address-pool tunnel-interface list'] = """
type: command
short-summary: List all tunnel interfacees of the load balance tunnel interface pool.
examples:
  - name: List all tunnel interfacees of the load balance tunnel interface pool.
    text: az network lb address-pool tunnel-interface list -g MyResourceGroup --lb-name MyLb --address-pool MyAddressPool
"""

helps['network cross-region-lb frontend-ip'] = """
type: group
short-summary: Manage frontend IP addresses of a cross-region load balancer.
"""

helps['network cross-region-lb frontend-ip create'] = """
type: command
short-summary: Create a frontend IP address.
examples:
  - name: Create a frontend ip address for a public load balancer.
    text: az network cross-region-lb frontend-ip create -g MyResourceGroup -n MyFrontendIp --lb-name MyLb --public-ip-address MyFrontendIp
"""

helps['network cross-region-lb frontend-ip delete'] = """
type: command
short-summary: Delete a frontend IP address.
examples:
  - name: Delete a frontend IP address.
    text: az network cross-region-lb frontend-ip delete -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
"""

helps['network cross-region-lb frontend-ip list'] = """
type: command
short-summary: List frontend IP addresses.
examples:
  - name: List frontend IP addresses.
    text: az network cross-region-lb frontend-ip list -g MyResourceGroup --lb-name MyLb
"""

helps['network cross-region-lb frontend-ip show'] = """
type: command
short-summary: Get the details of a frontend IP address.
examples:
  - name: Get the details of a frontend IP address.
    text: az network cross-region-lb frontend-ip show -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
"""

helps['network cross-region-lb frontend-ip update'] = """
type: command
short-summary: Update a frontend IP address.
examples:
  - name: Update the frontend IP address of a public load balancer.
    text: az network cross-region-lb frontend-ip update -g MyResourceGroup --lb-name MyLb -n MyFrontendIp --public-ip-address MyNewPublicIp
"""

helps['network cross-region-lb probe'] = """
type: group
short-summary: Evaluate probe information and define routing rules.
"""

helps['network cross-region-lb probe create'] = """
type: command
short-summary: Create a probe.
examples:
  - name: Create a probe on a load balancer over HTTP and port 80.
    text: |
        az network cross-region-lb probe create -g MyResourceGroup --lb-name MyLb -n MyProbe \\
            --protocol http --port 80 --path /
  - name: Create a probe on a load balancer over TCP on port 443.
    text: |
        az network cross-region-lb probe create -g MyResourceGroup --lb-name MyLb -n MyProbe \\
            --protocol tcp --port 443
"""

helps['network cross-region-lb probe delete'] = """
type: command
short-summary: Delete a probe.
examples:
  - name: Delete a probe.
    text: az network cross-region-lb probe delete -g MyResourceGroup --lb-name MyLb -n MyProbe
"""

helps['network cross-region-lb probe list'] = """
type: command
short-summary: List probes.
examples:
  - name: List probes.
    text: az network cross-region-lb probe list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network cross-region-lb probe show'] = """
type: command
short-summary: Get the details of a probe.
examples:
  - name: Get the details of a probe.
    text: az network cross-region-lb probe show -g MyResourceGroup --lb-name MyLb -n MyProbe
"""

helps['network cross-region-lb probe update'] = """
type: command
short-summary: Update a probe.
examples:
  - name: Update a probe with a different port and interval.
    text: az network cross-region-lb probe update -g MyResourceGroup --lb-name MyLb -n MyProbe --port 81 --interval 10
"""

helps['network cross-region-lb rule'] = """
type: group
short-summary: Manage cross-region load balancing rules.
"""

helps['network cross-region-lb rule create'] = """
type: command
short-summary: Create a load balancing rule.
examples:
  - name: >
        Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port.
    text: |
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp \\
            --frontend-ip-name MyFrontEndIp --frontend-port 80 \\
            --backend-pool-name MyAddressPool --backend-port 80
  - name: >
        Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port with the floating ip feature.
    text: |
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp \\
            --frontend-ip-name MyFrontEndIp --backend-pool-name MyAddressPool  \\
            --floating-ip true --frontend-port 80 --backend-port 80
  - name: >
        Create an HA ports load balancing rule that assigns a frontend IP and port to use all available backend IPs in a pool on the same port.
    text: |
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyHAPortsRule \\
            --protocol All --frontend-port 0 --backend-port 0 --frontend-ip-name MyFrontendIp \\
            --backend-pool-name MyAddressPool
"""

helps['network cross-region-lb rule delete'] = """
type: command
short-summary: Delete a load balancing rule.
examples:
  - name: Delete a load balancing rule.
    text: az network cross-region-lb rule delete -g MyResourceGroup --lb-name MyLb -n MyLbRule
"""

helps['network cross-region-lb rule list'] = """
type: command
short-summary: List load balancing rules.
examples:
  - name: List load balancing rules.
    text: az network cross-region-lb rule list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network cross-region-lb rule show'] = """
type: command
short-summary: Get the details of a load balancing rule.
examples:
  - name: Get the details of a load balancing rule.
    text: az network cross-region-lb rule show -g MyResourceGroup --lb-name MyLb -n MyLbRule
"""

helps['network cross-region-lb rule update'] = """
type: command
short-summary: Update a load balancing rule.
examples:
  - name: Update a load balancing rule to change the protocol to UDP.
    text: az network cross-region-lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Udp
    examples:
  - name: Update a load balancing rule to support HA ports.
    text: az network cross-region-lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule \\ --protocol All --frontend-port 0 --backend-port 0
"""

helps['network lb'] = """
type: group
short-summary: Manage and configure load balancers.
long-summary: |
  To learn more about Azure Load Balancer visit https://docs.microsoft.com/azure/load-balancer/load-balancer-get-started-internet-arm-cli
"""

helps['network lb wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the load balancer is met.
examples:
  - name: Wait for load balancer to return as created.
    text: |
        az network lb wait -g MyResourceGroup -n MyLB --created
"""

helps['network lb address-pool'] = """
type: group
short-summary: Manage address pools of a load balancer.
"""

helps['network lb address-pool create'] = """
type: command
short-summary: Create an address pool.
parameters:
  - name: --backend-address
    short-summary: Backend addresses information for backend address pool. If it's used, --vnet is required or subnet is required.
    long-summary: |
        Usage1: --backend-address name=addr1 ip-address=10.0.0.1 --vnet MyVnet
        Usage2: --backend-address name=addr1 ip-address=10.0.0.1 subnet=/subscriptions/000/resourceGroups/MyRg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet1
        Usage3: --backend-address name=addr1 ip-address=10.0.0.1 subnet=subnet1 --vnet MyVnet

        name: Required. The name of the backend address.
        ip-address: Required. Ip Address within the Virtual Network.
        subnet: Name or Id of the subnet.

        Multiple backend addresses can be specified by using more than one `--backend-address` argument.
  - name: --backend-addresses-config-file
    short-summary: A config file used to set backend addresses. This argument is for experienced users. You may encounter parse errors if the json file is invalid.
    long-summary: |
        Usage: --backend-addresses-config-file @"{config_file.json}"

        A example config file is
        [
          {
            "name": "address1",
            "virtualNetwork": "clitestvnet",
            "ipAddress": "10.0.0.4"
          },
          {
            "name": "address2",
            "virtualNetwork": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/virtualNetworks/clitestvnet",
            "ipAddress": "10.0.0.5"
          },
          {
            "name": "address3",
            "subnet": "subnet3",
            "ipAddress": "10.0.0.6"
          },
          {
            "name": "address4",
            "subnet": "/subscriptions/000/resourceGroups/MyRg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet4",
            "ipAddress": "10.0.0.7"
          }
        ]
examples:
  - name: Create an address pool.
    text: az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool
  - name: Create an address pool with several backend addresses using key-value arguments.
    text: az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --vnet {VnetResourceId} --backend-address name=addr1 ip-address=10.0.0.1 --backend-address name=addr2 ip-address=10.0.0.3
  - name: Create an address pool with several backend addresses using config file
    text: az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses-config-file @config_file.json
"""

helps['network lb address-pool update'] = """
type: command
short-summary: Update an address pool.
parameters:
  - name: --backend-address
    short-summary: Backend addresses information for backend address pool. If it's used, --vnet is required or subnet is required.
    long-summary: |
        Usage1: --backend-address name=addr1 ip-address=10.0.0.1 --vnet MyVnet
        Usage2: --backend-address name=addr1 ip-address=10.0.0.1 subnet=/subscriptions/000/resourceGroups/MyRg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet1
        Usage3: --backend-address name=addr1 ip-address=10.0.0.1 subnet=subnet1 --vnet MyVnet

        name: Required. The name of the backend address.
        ip-address: Required. Ip Address within the Virtual Network.
        subnet: Name or Id of the subnet.

        Multiple backend addresses can be specified by using more than one `--backend-address` argument.
  - name: --backend-addresses-config-file
    short-summary: A config file used to set backend addresses. This argument is for experienced users. You may encounter parse errors if the json file is invalid.
    long-summary: |
        Usage: --backend-addresses-config-file @"{config_file.json}"

        A example config file is
        [
          {
            "name": "address1",
            "virtualNetwork": "clitestvnet",
            "ipAddress": "10.0.0.4"
          },
          {
            "name": "address2",
            "virtualNetwork": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/virtualNetworks/clitestvnet",
            "ipAddress": "10.0.0.5"
          },
          {
            "name": "address3",
            "subnet": "subnet3",
            "ipAddress": "10.0.0.6"
          },
          {
            "name": "address4",
            "subnet": "/subscriptions/000/resourceGroups/MyRg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet4",
            "ipAddress": "10.0.0.7"
          }
        ]
examples:
  - name: Update an address pool with several backend addresses using key-value arguments.
    text: az network lb address-pool update -g MyResourceGroup --lb-name MyLb -n MyAddressPool --vnet {VnetResourceId} --backend-address name=addr1 ip-address=10.0.0.1 --backend-address name=addr2 ip-address=10.0.0.3
"""

helps['network lb address-pool delete'] = """
type: command
short-summary: Delete an address pool.
examples:
  - name: Delete an address pool.
    text: az network lb address-pool delete -g MyResourceGroup --lb-name MyLb -n MyAddressPool
"""

helps['network lb address-pool list'] = """
type: command
short-summary: List address pools.
examples:
  - name: List address pools.
    text: az network lb address-pool list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network lb address-pool show'] = """
type: command
short-summary: Get the details of an address pool.
examples:
  - name: Get the details of an address pool.
    text: az network lb address-pool show -g MyResourceGroup --lb-name MyLb -n MyAddressPool
"""

helps['network lb address-pool address'] = """
type: group
short-summary: Manage backend addresses of the load balance backend address pool.
"""

helps['network lb address-pool address add'] = """
type: command
short-summary: Add one backend address into the load balance backend address pool.
examples:
  - name: Add one backend address into the load balance backend address pool.
    text: az network lb address-pool address add -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress --vnet MyVnet --ip-address 10.0.0.1
  - name: Add one backend address into the load balance backend address pool with subnet.
    text: az network lb address-pool address add -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress --subnet /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet2 --ip-address 10.0.0.1
"""

helps['network lb address-pool address remove'] = """
type: command
short-summary: Remove one backend address from the load balance backend address pool.
examples:
  - name: Remove one backend address from the load balance backend address pool.
    text: az network lb address-pool address remove -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress
"""

helps['network lb address-pool address list'] = """
type: command
short-summary: List all backend addresses of the load balance backend address pool.
examples:
  - name: List all backend addresses of the load balance backend address pool.
    text: az network lb address-pool address list -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool
"""

helps['network lb create'] = """
type: command
short-summary: Create a load balancer.
examples:
  - name: Create a basic load balancer.
    text: >
        az network lb create -g MyResourceGroup -n MyLb --sku Basic
  - name: Create a basic load balancer on a specific virtual network and subnet. If a virtual network with the same name is found in the same resource group, the load balancer will utilize this virtual network.  If one is not found a new one will be created.
    text: >
        az network lb create -g MyResourceGroup -n MyLb --sku Basic --vnet-name MyVnet --subnet MySubnet
  - name: Create a basic load balancer on a subnet of a pre-existing virtual network. The subnet can be in arbitary resource group or subscription by providing the ID of the subnet.
    text: >
        az network lb create -g MyResourceGroup -n MyLb --sku Basic --subnet {subnetID}
  - name: Create a basic zone flavored internal load balancer, through provisioning a zonal public ip.
    text: >
        az network lb create -g MyResourceGroup -n MyLb --sku Basic --public-ip-zone 2
  - name: >
        Create a standard zone flavored public-facing load balancer, through provisioning a zonal frontend ip configuration and Vnet.
    text: >
        az network lb create -g MyResourceGroup -n MyLb --sku Standard --frontend-ip-zone 1 --vnet-name MyVnet --subnet MySubnet
"""

helps['network lb delete'] = """
type: command
short-summary: Delete a load balancer.
examples:
  - name: Delete a load balancer.
    text: az network lb delete -g MyResourceGroup -n MyLb
"""

helps['network lb frontend-ip'] = """
type: group
short-summary: Manage frontend IP addresses of a load balancer.
"""

helps['network lb frontend-ip create'] = """
type: command
short-summary: Create a frontend IP address.
examples:
  - name: Create a frontend ip address for a public load balancer.
    text: az network lb frontend-ip create -g MyResourceGroup -n MyFrontendIp --lb-name MyLb --public-ip-address MyFrontendIp
  - name: Create a frontend ip address for an internal load balancer.
    text: |
        az network lb frontend-ip create -g MyResourceGroup -n MyFrontendIp --lb-name MyLb \\
            --private-ip-address 10.10.10.100 --subnet MySubnet --vnet-name MyVnet
"""

helps['network lb frontend-ip delete'] = """
type: command
short-summary: Delete a frontend IP address.
examples:
  - name: Delete a frontend IP address.
    text: az network lb frontend-ip delete -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
"""

helps['network lb frontend-ip list'] = """
type: command
short-summary: List frontend IP addresses.
examples:
  - name: List frontend IP addresses.
    text: az network lb frontend-ip list -g MyResourceGroup --lb-name MyLb
"""

helps['network lb frontend-ip show'] = """
type: command
short-summary: Get the details of a frontend IP address.
examples:
  - name: Get the details of a frontend IP address.
    text: az network lb frontend-ip show -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
  - name: Get the details of a frontend IP address (autogenerated)
    text: |
        az network lb frontend-ip show --lb-name MyLb --name MyFrontendIp --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network lb frontend-ip update'] = """
type: command
short-summary: Update a frontend IP address.
examples:
  - name: Update the frontend IP address of a public load balancer.
    text: az network lb frontend-ip update -g MyResourceGroup --lb-name MyLb -n MyFrontendIp --public-ip-address MyNewPublicIp
  - name: Update the frontend IP address of an internal load balancer.
    text: az network lb frontend-ip update -g MyResourceGroup --lb-name MyLb -n MyFrontendIp --private-ip-address 10.10.10.50
  - name: Update a frontend IP address. (autogenerated)
    text: |
        az network lb frontend-ip update --lb-name MyLb --name MyFrontendIp --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup
    crafted: true
"""

helps['network lb inbound-nat-pool'] = """
type: group
short-summary: Manage inbound NAT address pools of a load balancer.
"""

helps['network lb inbound-nat-pool create'] = """
type: command
short-summary: Create an inbound NAT address pool.
examples:
  - name: Create an inbound NAT address pool.
    text: |
        az network lb inbound-nat-pool create -g MyResourceGroup --lb-name MyLb \\
        -n MyNatPool --protocol Tcp --frontend-port-range-start 80 --frontend-port-range-end 89 \\
        --backend-port 80 --frontend-ip-name MyFrontendIp
"""

helps['network lb inbound-nat-pool delete'] = """
type: command
short-summary: Delete an inbound NAT address pool.
examples:
  - name: Delete an inbound NAT address pool.
    text: az network lb inbound-nat-pool delete -g MyResourceGroup --lb-name MyLb -n MyNatPool
"""

helps['network lb inbound-nat-pool list'] = """
type: command
short-summary: List inbound NAT address pools.
examples:
  - name: List inbound NAT address pools.
    text: az network lb inbound-nat-pool list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network lb inbound-nat-pool show'] = """
type: command
short-summary: Get the details of an inbound NAT address pool.
examples:
  - name: Get the details of an inbound NAT address pool.
    text: az network lb inbound-nat-pool show -g MyResourceGroup --lb-name MyLb -n MyNatPool
"""

helps['network lb inbound-nat-pool update'] = """
type: command
short-summary: Update an inbound NAT address pool.
examples:
  - name: Update an inbound NAT address pool to a different backend port.
    text: |
        az network lb inbound-nat-pool update -g MyResourceGroup --lb-name MyLb -n MyNatPool \\
            --protocol Tcp --backend-port 8080
  - name: Update an inbound NAT address pool. (autogenerated)
    text: |
        az network lb inbound-nat-pool update --backend-port 8080 --enable-tcp-reset true --frontend-port-range-end 89 --frontend-port-range-start 80 --lb-name MyLb --name MyNatPool --resource-group MyResourceGroup
    crafted: true
  - name: Update an inbound NAT address pool. (autogenerated)
    text: |
        az network lb inbound-nat-pool update --enable-tcp-reset true --lb-name MyLb --name MyNatPool --protocol Udp --resource-group MyResourceGroup
    crafted: true
  - name: Update an inbound NAT address pool. (autogenerated)
    text: |
        az network lb inbound-nat-pool update --backend-port 8080 --floating-ip true --frontend-port-range-end 89 --frontend-port-range-start 80 --lb-name MyLb --name MyNatPool --protocol Udp --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb inbound-nat-rule'] = """
type: group
short-summary: Manage inbound NAT rules of a load balancer.
"""

helps['network lb inbound-nat-rule create'] = """
type: command
short-summary: Create an inbound NAT rule.
examples:
  - name: Create a basic inbound NAT rule for port 80.
    text: |
        az network lb inbound-nat-rule create -g MyResourceGroup --lb-name MyLb -n MyNatRule \\
            --protocol Tcp --frontend-port 80 --backend-port 80
  - name: Create a basic inbound NAT rule for a specific frontend IP and enable floating IP for NAT Rule.
    text: |
        az network lb inbound-nat-rule create -g MyResourceGroup --lb-name MyLb -n MyNatRule --protocol Tcp \\
            --frontend-port 5432 --backend-port 3389 --frontend-ip-name MyFrontendIp --floating-ip true
"""

helps['network lb inbound-nat-rule delete'] = """
type: command
short-summary: Delete an inbound NAT rule.
examples:
  - name: Delete an inbound NAT rule.
    text: az network lb inbound-nat-rule delete -g MyResourceGroup --lb-name MyLb -n MyNatRule
"""

helps['network lb inbound-nat-rule list'] = """
type: command
short-summary: List inbound NAT rules.
examples:
  - name: List inbound NAT rules.
    text: az network lb inbound-nat-rule list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network lb inbound-nat-rule show'] = """
type: command
short-summary: Get the details of an inbound NAT rule.
examples:
  - name: Get the details of an inbound NAT rule.
    text: az network lb inbound-nat-rule show -g MyResourceGroup --lb-name MyLb -n MyNatRule
"""

helps['network lb inbound-nat-rule update'] = """
type: command
short-summary: Update an inbound NAT rule.
examples:
  - name: Update an inbound NAT rule to disable floating IP and modify idle timeout duration.
    text: |
        az network lb inbound-nat-rule update -g MyResourceGroup --lb-name MyLb -n MyNatRule \\
            --floating-ip false --idle-timeout 5
  - name: Update an inbound NAT rule. (autogenerated)
    text: |
        az network lb inbound-nat-rule update --backend-port 3389 --frontend-port 5432 --lb-name MyLb --name MyNatRule --protocol Udp --resource-group MyResourceGroup
    crafted: true
  - name: Update an inbound NAT rule. (autogenerated)
    text: |
        az network lb inbound-nat-rule update --lb-name MyLb --name MyNatRule --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup
    crafted: true
"""

helps['network lb list'] = """
type: command
short-summary: List load balancers.
examples:
  - name: List load balancers.
    text: az network lb list -g MyResourceGroup
"""

helps['network lb list-nic'] = """
type: command
short-summary: List associated load balancer network interfaces.
examples:
  - name: List associated load balancer network interfaces.
    text: az network lb list-nic -g MyResourceGroup --name MyLb
"""

helps['network lb list-mapping'] = """
type: command
short-summary: List inbound NAT rule port mappings.
examples:
  - name: List inbound NAT rule port mappings based on IP.
    text: az network lb list-mapping -n MyLb -g MyResourceGroup --backend-pool-name MyAddressPool --request ip=XX
  - name: List inbound NAT rule port mappings based on NIC.
    text: az network lb list-mapping -n MyLb -g MyResourceGroup --backend-pool-name MyAddressPool --request nic=XX
"""

helps['network lb outbound-rule'] = """
type: group
short-summary: Manage outbound rules of a load balancer.
"""

helps['network lb outbound-rule create'] = """
type: command
short-summary: Create an outbound-rule.
examples:
  - name: Create an outbound-rule. (autogenerated)
    text: |
        az network lb outbound-rule create --address-pool MyAddressPool --frontend-ip-configs myfrontendoutbound --idle-timeout 5 --lb-name MyLb --name MyOutboundRule --outbound-ports 10000 --protocol Udp --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb outbound-rule delete'] = """
type: command
short-summary: Delete an outbound-rule.
examples:
  - name: Delete an outbound-rule. (autogenerated)
    text: |
        az network lb outbound-rule delete --lb-name MyLb --name MyOutboundRule --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb outbound-rule list'] = """
type: command
short-summary: List outbound rules.
examples:
  - name: List outbound rules. (autogenerated)
    text: |
        az network lb outbound-rule list --lb-name MyLb --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb outbound-rule show'] = """
type: command
short-summary: Get the details of an outbound rule.
examples:
  - name: Get the details of an outbound rule. (autogenerated)
    text: |
        az network lb outbound-rule show --lb-name MyLb --name MyOutboundRule --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb outbound-rule update'] = """
type: command
short-summary: Update an outbound-rule.
examples:
  - name: Update an outbound-rule. (autogenerated)
    text: |
        az network lb outbound-rule update --lb-name MyLb --name MyOutboundRule --outbound-ports 10000 --resource-group MyResourceGroup
    crafted: true
"""

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
  - name: Create a probe on a load balancer over TCP on port 443.
    text: |
        az network lb probe create -g MyResourceGroup --lb-name MyLb -n MyProbe \\
            --protocol tcp --port 443
"""

helps['network lb probe delete'] = """
type: command
short-summary: Delete a probe.
examples:
  - name: Delete a probe.
    text: az network lb probe delete -g MyResourceGroup --lb-name MyLb -n MyProbe
"""

helps['network lb probe list'] = """
type: command
short-summary: List probes.
examples:
  - name: List probes.
    text: az network lb probe list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network lb probe show'] = """
type: command
short-summary: Get the details of a probe.
examples:
  - name: Get the details of a probe.
    text: az network lb probe show -g MyResourceGroup --lb-name MyLb -n MyProbe
"""

helps['network lb probe update'] = """
type: command
short-summary: Update a probe.
examples:
  - name: Update a probe with a different port and interval.
    text: az network lb probe update -g MyResourceGroup --lb-name MyLb -n MyProbe --port 81 --interval 10
  - name: Update a probe. (autogenerated)
    text: |
        az network lb probe update --lb-name MyLb --name MyProbe --port 81 --protocol Http --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb rule'] = """
type: group
short-summary: Manage load balancing rules.
"""

helps['network lb rule create'] = """
type: command
short-summary: Create a load balancing rule.
examples:
  - name: >
        Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port.
    text: |
        az network lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp \\
            --frontend-ip-name MyFrontEndIp --frontend-port 80 \\
            --backend-pool-name MyAddressPool --backend-port 80
  - name: >
        Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port with the floating ip feature.
    text: |
        az network lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp \\
            --frontend-ip-name MyFrontEndIp --backend-pool-name MyAddressPool  \\
            --floating-ip true --frontend-port 80 --backend-port 80
  - name: >
        Create an HA ports load balancing rule that assigns a frontend IP and port to use all available backend IPs in a pool on the same port.
    text: |
        az network lb rule create -g MyResourceGroup --lb-name MyLb -n MyHAPortsRule \\
            --protocol All --frontend-port 0 --backend-port 0 --frontend-ip-name MyFrontendIp \\
            --backend-pool-name MyAddressPool
"""

helps['network lb rule delete'] = """
type: command
short-summary: Delete a load balancing rule.
examples:
  - name: Delete a load balancing rule.
    text: az network lb rule delete -g MyResourceGroup --lb-name MyLb -n MyLbRule
"""

helps['network lb rule list'] = """
type: command
short-summary: List load balancing rules.
examples:
  - name: List load balancing rules.
    text: az network lb rule list -g MyResourceGroup --lb-name MyLb -o table
"""

helps['network lb rule show'] = """
type: command
short-summary: Get the details of a load balancing rule.
examples:
  - name: Get the details of a load balancing rule.
    text: az network lb rule show -g MyResourceGroup --lb-name MyLb -n MyLbRule
"""

helps['network lb rule update'] = """
type: command
short-summary: Update a load balancing rule.
examples:
  - name: Update a load balancing rule to change the protocol to UDP.
    text: az network lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Udp
    examples:
  - name: Update a load balancing rule to support HA ports.
    text: az network lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule \\ --protocol All --frontend-port 0 --backend-port 0
  - name: Update a load balancing rule. (autogenerated)
    text: |
        az network lb rule update --disable-outbound-snat true --lb-name MyLb --name MyLbRule --resource-group MyResourceGroup
    crafted: true
  - name: Update a load balancing rule. (autogenerated)
    text: |
        az network lb rule update --idle-timeout 5 --lb-name MyLb --name MyLbRule --resource-group MyResourceGroup
    crafted: true
"""

helps['network lb show'] = """
type: command
short-summary: Get the details of a load balancer.
examples:
  - name: Get the details of a load balancer.
    text: az network lb show -g MyResourceGroup -n MyLb
"""

helps['network lb update'] = """
type: command
short-summary: Update a load balancer.
long-summary: >
    This command can only be used to update the tags for a load balancer. Name and resource group are immutable and cannot be updated.
examples:
  - name: Update the tags of a load balancer.
    text: az network lb update -g MyResourceGroup -n MyLb --set tags.CostCenter=MyBusinessGroup
"""

helps['network list-service-tags'] = """
type: command
short-summary: List all service tags which are below to different resources
long-summary: >
    A service tag represents a group of IP address prefixes to help minimize complexity for security rule creation.
    To learn more about list-service-tags, visit https://docs.microsoft.com/azure/virtual-network/security-overview#service-tags. \\
    Note that the location parameter is used as a reference for version (not as a filter based on location).
    For example, even if you specify --location eastus2 you will get the list of service tags with prefix details across all regions but limited to the cloud that your subscription belongs to (i.e. Public, US government, China or Germany).
examples:
  - name: Gets a list of service tag information resources. (autogenerated)
    text: |
        az network list-service-tags --location westus2
    crafted: true
"""

helps['network list-usages'] = """
type: command
short-summary: List the number of network resources in a region that are used against a subscription quota.
examples:
  - name: List the provisioned network resources in East US region within a subscription.
    text: az network list-usages --location eastus -o table
"""

helps['network local-gateway'] = """
type: group
short-summary: Manage local gateways.
long-summary: >
    For more information on local gateways, visit: https://docs.microsoft.com/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-cli#localnet
"""

helps['network local-gateway create'] = """
type: command
short-summary: Create a local VPN gateway.
examples:
  - name: Create a Local Network Gateway to represent your on-premises site.
    text: |
        az network local-gateway create -g MyResourceGroup -n MyLocalGateway \\
            --gateway-ip-address 23.99.221.164 --local-address-prefixes 10.0.0.0/24 20.0.0.0/24
"""

helps['network local-gateway delete'] = """
type: command
short-summary: Delete a local VPN gateway.
long-summary: >
    In order to delete a Local Network Gateway, you must first delete ALL Connection objects in Azure
    that are connected to the Gateway. After deleting the Gateway, proceed to delete other resources now not in use.
    For more information, follow the order of instructions on this page: https://docs.microsoft.com/azure/vpn-gateway/vpn-gateway-delete-vnet-gateway-portal
examples:
  - name: Create a Local Network Gateway to represent your on-premises site.
    text: az network local-gateway delete -g MyResourceGroup -n MyLocalGateway
  - name: Delete a local VPN gateway. (autogenerated)
    text: |
        az network local-gateway delete --name MyLocalGateway --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network local-gateway list'] = """
type: command
short-summary: List all local VPN gateways in a resource group.
examples:
  - name: List all local VPN gateways in a resource group.
    text: az network local-gateway list -g MyResourceGroup
"""

helps['network local-gateway show'] = """
type: command
short-summary: Get the details of a local VPN gateway.
examples:
  - name: Get the details of a local VPN gateway.
    text: az network local-gateway show -g MyResourceGroup -n MyLocalGateway
"""

helps['network local-gateway update'] = """
type: command
short-summary: Update a local VPN gateway.
examples:
  - name: Update a Local Network Gateway provisioned with a 10.0.0.0/24 address prefix with additional prefixes.
    text: |
        az network local-gateway update -g MyResourceGroup -n MyLocalGateway \\
            --local-address-prefixes 10.0.0.0/24 20.0.0.0/24 30.0.0.0/24
  - name: Update a local VPN gateway. (autogenerated)
    text: |
        az network local-gateway update --gateway-ip-address 23.99.221.164 --name MyLocalGateway --resource-group MyResourceGroup
    crafted: true
"""

helps['network local-gateway wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the local gateway is met.
examples:
  - name: Wait for Local Network Gateway to return as created.
    text: |
        az network local-gateway wait -g MyResourceGroup -n MyLocalGateway --created
"""

helps['network nic'] = """
type: group
short-summary: Manage network interfaces.
long-summary: >
    To learn more about network interfaces in Azure visit https://docs.microsoft.com/azure/virtual-network/virtual-network-network-interface
"""

helps['network nic create'] = """
type: command
short-summary: Create a network interface.
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
        az network nic create -g MyResourceGroup --vnet-name MyVnet --subnet MySubnet -n MyNic \\
            --network-security-group MyNsg --application-security-groups Web App
"""

helps['network nic delete'] = """
type: command
short-summary: Delete a network interface.
examples:
  - name: Delete a network interface.
    text: >
        az network nic delete -g MyResourceGroup -n MyNic
"""

helps['network nic ip-config'] = """
type: group
short-summary: Manage IP configurations of a network interface.
"""

helps['network nic ip-config address-pool'] = """
type: group
short-summary: Manage address pools in an IP configuration.
"""

helps['network nic ip-config address-pool add'] = """
type: command
short-summary: Add an address pool to an IP configuration.
examples:
  - name: Add an address pool to an IP configuration.
    text: |
        az network nic ip-config address-pool add -g MyResourceGroup --nic-name MyNic \\
            -n MyIpConfig --address-pool MyAddressPool
  - name: Add an address pool to an IP configuration. (autogenerated)
    text: |
        az network nic ip-config address-pool add --address-pool MyAddressPool --ip-config-name MyIpConfig --lb-name MyLb --nic-name MyNic --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic ip-config address-pool remove'] = """
type: command
short-summary: Remove an address pool of an IP configuration.
examples:
  - name: Remove an address pool of an IP configuration.
    text: |
        az network nic ip-config address-pool remove -g MyResourceGroup --nic-name MyNic \\
            -n MyIpConfig --address-pool MyAddressPool
  - name: Remove an address pool of an IP configuration. (autogenerated)
    text: |
        az network nic ip-config address-pool remove --address-pool MyAddressPool --ip-config-name MyIpConfig --lb-name MyLb --nic-name MyNic --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic ip-config create'] = """
type: command
short-summary: Create an IP configuration.
long-summary: >
    You must have the Microsoft.Network/AllowMultipleIpConfigurationsPerNic feature enabled for your subscription.
    Only one configuration may be designated as the primary IP configuration per NIC, using the `--make-primary` flag.
examples:
  - name: Create a primary IP configuration for a NIC.
    text: az network nic ip-config create -g MyResourceGroup -n MyIpConfig --nic-name MyNic --make-primary
  - name: Create an IP configuration. (autogenerated)
    text: |
        az network nic ip-config create --name MyIpConfig --nic-name MyNic --private-ip-address 10.0.0.9 --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic ip-config delete'] = """
type: command
short-summary: Delete an IP configuration.
long-summary: A NIC must have at least one IP configuration.
examples:
  - name: Delete an IP configuration.
    text: az network nic ip-config delete -g MyResourceGroup -n MyIpConfig --nic-name MyNic
"""

helps['network nic ip-config inbound-nat-rule'] = """
type: group
short-summary: Manage inbound NAT rules of an IP configuration.
"""

helps['network nic ip-config inbound-nat-rule add'] = """
type: command
short-summary: Add an inbound NAT rule to an IP configuration.
examples:
  - name: Add an inbound NAT rule to an IP configuration.
    text: |
        az network nic ip-config inbound-nat-rule add -g MyResourceGroup --nic-name MyNic \\
            -n MyIpConfig --inbound-nat-rule MyNatRule
  - name: Add an inbound NAT rule to an IP configuration. (autogenerated)
    text: |
        az network nic ip-config inbound-nat-rule add --inbound-nat-rule MyNatRule --ip-config-name MyIpConfig --lb-name MyLb --nic-name MyNic --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic ip-config inbound-nat-rule remove'] = """
type: command
short-summary: Remove an inbound NAT rule of an IP configuration.
examples:
  - name: Remove an inbound NAT rule of an IP configuration.
    text: |
        az network nic ip-config inbound-nat-rule remove -g MyResourceGroup --nic-name MyNic \\
            -n MyIpConfig --inbound-nat-rule MyNatRule
  - name: Remove an inbound NAT rule of an IP configuration. (autogenerated)
    text: |
        az network nic ip-config inbound-nat-rule remove --inbound-nat-rule MyNatRule --ip-config-name MyIpConfig --lb-name MyLb --nic-name MyNic --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic ip-config list'] = """
type: command
short-summary: List the IP configurations of a NIC.
examples:
  - name: List the IP configurations of a NIC.
    text: az network nic ip-config list -g MyResourceGroup --nic-name MyNic
"""

helps['network nic ip-config show'] = """
type: command
short-summary: Show the details of an IP configuration.
examples:
  - name: Show the details of an IP configuration of a NIC.
    text: az network nic ip-config show -g MyResourceGroup -n MyIpConfig --nic-name MyNic
"""

helps['network nic ip-config update'] = """
type: command
short-summary: Update an IP configuration.
examples:
  - name: Update a NIC to use a new private IP address.
    text: |
        az network nic ip-config update -g MyResourceGroup --nic-name MyNic \\
            -n MyIpConfig --private-ip-address 10.0.0.9
  - name: Make an IP configuration the default for the supplied NIC.
    text: |
        az network nic ip-config update -g MyResourceGroup --nic-name MyNic \\
            -n MyIpConfig --make-primary
  - name: Update an IP configuration. (autogenerated)
    text: |
        az network nic ip-config update --name MyIpConfig --nic-name MyNic --public-ip-address MyAppGatewayPublicIp --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic list'] = """
type: command
short-summary: List network interfaces.
long-summary: >
    To list network interfaces attached to VMs in VM scale sets use 'az vmss nic list' or 'az vmss nic list-vm-nics'.
examples:
  - name: List all NICs by internal DNS suffix.
    text: >
        az network nic list --query "[?dnsSettings.internalDomainNameSuffix=`{dnsSuffix}`]"
"""

helps['network nic list-effective-nsg'] = """
type: command
short-summary: List all effective network security groups applied to a network interface.
long-summary: >
    To learn more about troubleshooting using effective security rules visit https://docs.microsoft.com/azure/virtual-network/virtual-network-nsg-troubleshoot-portal
examples:
  - name: List the effective security groups associated with a NIC.
    text: az network nic list-effective-nsg -g MyResourceGroup -n MyNic
"""

helps['network nic show'] = """
type: command
short-summary: Get the details of a network interface.
examples:
  - name: Get the internal domain name suffix of a NIC.
    text: az network nic show -g MyResourceGroup -n MyNic --query "dnsSettings.internalDomainNameSuffix"
"""

helps['network nic show-effective-route-table'] = """
type: command
short-summary: Show the effective route table applied to a network interface.
long-summary: >
    To learn more about troubleshooting using the effective route tables visit
    https://docs.microsoft.com/azure/virtual-network/virtual-network-routes-troubleshoot-portal#using-effective-routes-to-troubleshoot-vm-traffic-flow
examples:
  - name: Show the effective routes applied to a network interface.
    text: az network nic show-effective-route-table -g MyResourceGroup -n MyNic
"""

helps['network nic update'] = """
type: command
short-summary: Update a network interface.
examples:
  - name: Update a network interface to use a different network security group.
    text: az network nic update -g MyResourceGroup -n MyNic --network-security-group MyNewNsg
  - name: Update a network interface. (autogenerated)
    text: |
        az network nic update --accelerated-networking true --name MyNic --resource-group MyResourceGroup
    crafted: true
"""

helps['network nic wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the network interface is met.
examples:
  - name: Pause CLI until the network interface is created.
    text: az network nic wait -g MyResourceGroup -n MyNic --created
  - name: Place the CLI in a waiting state until a condition of the network interface is met. (autogenerated)
    text: |
        az network nic wait --deleted --name MyNic --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network nsg'] = """
type: group
short-summary: Manage Azure Network Security Groups (NSGs).
long-summary: >
    You can control network traffic to resources in a virtual network using a network security group.
    A network security group contains a list of security rules that allow or deny inbound or
    outbound network traffic based on source or destination IP addresses, Application Security
    Groups, ports, and protocols. For more information visit https://docs.microsoft.com/azure/virtual-network/virtual-networks-create-nsg-arm-cli
"""

helps['network nsg create'] = """
type: command
short-summary: Create a network security group.
examples:
  - name: Create an NSG in a resource group within a region with tags.
    text: az network nsg create -g MyResourceGroup -n MyNsg --tags super_secure no_80 no_22
"""

helps['network nsg delete'] = """
type: command
short-summary: Delete a network security group.
examples:
  - name: Delete an NSG in a resource group.
    text: az network nsg delete -g MyResourceGroup -n MyNsg
"""

helps['network nsg list'] = """
type: command
short-summary: List network security groups.
examples:
  - name: List all NSGs in the 'westus' region.
    text: az network nsg list --query "[?location=='westus']"
"""

helps['network nsg rule'] = """
type: group
short-summary: Manage network security group rules.
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
            --source-address-prefixes 208.130.28.0/24 --source-port-ranges 80 \\
            --destination-address-prefixes '*' --destination-port-ranges 80 8080 --access Deny \\
            --protocol Tcp --description "Deny from specific IP address ranges on 80 and 8080."
  - name: Create a security rule using service tags. For more details visit https://aka.ms/servicetags
    text: |
        az network nsg rule create -g MyResourceGroup --nsg-name MyNsg -n MyNsgRuleWithTags \\
            --priority 400 --source-address-prefixes VirtualNetwork --destination-address-prefixes Storage \\
            --destination-port-ranges '*' --direction Outbound --access Allow --protocol Tcp --description "Allow VirtualNetwork to Storage."
  - name: Create a security rule using application security groups. https://aka.ms/applicationsecuritygroups
    text: |
        az network nsg rule create -g MyResourceGroup --nsg-name MyNsg -n MyNsgRuleWithAsg \\
            --priority 500 --source-address-prefixes Internet --destination-port-ranges 80 8080 \\
            --destination-asgs Web --access Allow --protocol Tcp --description "Allow Internet to Web ASG on ports 80,8080."
"""

helps['network nsg rule delete'] = """
type: command
short-summary: Delete a network security group rule.
examples:
  - name: Delete a network security group rule.
    text: az network nsg rule delete -g MyResourceGroup --nsg-name MyNsg -n MyNsgRule
"""

helps['network nsg rule list'] = """
type: command
short-summary: List all rules in a network security group.
examples:
  - name: List all rules in a network security group.
    text: az network nsg rule list -g MyResourceGroup --nsg-name MyNsg
"""

helps['network nsg rule show'] = """
type: command
short-summary: Get the details of a network security group rule.
examples:
  - name: Get the details of a network security group rule.
    text: az network nsg rule show -g MyResourceGroup --nsg-name MyNsg -n MyNsgRule
"""

helps['network nsg rule update'] = """
type: command
short-summary: Update a network security group rule.
examples:
  - name: Update an NSG rule with a new wildcard destination address prefix.
    text: az network nsg rule update -g MyResourceGroup --nsg-name MyNsg -n MyNsgRule --destination-address-prefix '*'
  - name: Update a network security group rule. (autogenerated)
    text: |
        az network nsg rule update --name MyNsgRule --nsg-name MyNsg --resource-group MyResourceGroup --source-address-prefixes 208.130.28/24
    crafted: true
"""

helps['network nsg show'] = """
type: command
short-summary: Get information about a network security group.
examples:
  - name: Get basic information about an NSG.
    text: az network nsg show -g MyResourceGroup -n MyNsg
  - name: Get the default security rules of an NSG and format the output as a table.
    text: az network nsg show -g MyResourceGroup -n MyNsg --query "defaultSecurityRules[]" -o table
  - name: Get all default NSG rules with "Allow" access and format the output as a table.
    text: az network nsg show -g MyResourceGroup -n MyNsg --query "defaultSecurityRules[?access=='Allow']" -o table
"""

helps['network nsg update'] = """
type: command
short-summary: Update a network security group.
long-summary: >
    This command can only be used to update the tags of an NSG. Name and resource group are immutable and cannot be updated.
examples:
  - name: Remove a tag of an NSG.
    text: az network nsg update -g MyResourceGroup -n MyNsg --remove tags.no_80
  - name: Update a network security group. (autogenerated)
    text: |
        az network nsg update --name MyNsg --resource-group MyResourceGroup --set tags.CostCenter=MyBusinessGroup
    crafted: true
"""

helps['network private-endpoint'] = """
type: group
short-summary: Manage private endpoints.
"""

helps['network private-endpoint create'] = """
type: command
short-summary: Create a private endpoint.

parameters:
  - name: --ip-config
    short-summary: The private endpoint ip configurations.
    long-summary: |
        Usage: --ip-config name=MyIPConfig group-id=MyGroup member-name=MyMember private-ip-address=MyPrivateIPAddress
        Multiple ip configurations can be specified by using more than one `--ip-config` argument.
  - name: --asg
    short-summary: The private endpoint application security groups.
    long-summary: |
        Usage: --asg id=MyApplicationSecurityGroupId
        Multiple application security groups can be specified by using more than one `--asg` argument.

examples:
  - name: Create a private endpoint.
    text: az network private-endpoint create -g MyResourceGroup -n MyPE --vnet-name MyVnetName --subnet MySubnet --private-connection-resource-id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/privateLinkServices/MyPLS" --connection-name tttt -l centralus
  - name: Create a private endpoint with ASGs.
    text: |
        az network private-endpoint create -n MyPE -g MyResourceGroup --vnet-name MyVnetName --subnet MySubnet --connection-name MyConnectionName --group-id MyGroupId --private-connection-resource-id MyResourceId --asg id=MyAsgId --asg id=MyAsgId
"""

helps['network private-endpoint delete'] = """
type: command
short-summary: Delete a private endpoint.
examples:
  - name: Delete a private endpoint. (autogenerated)
    text: |
        az network private-endpoint delete --name MyPrivateEndpoint --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-endpoint list'] = """
type: command
short-summary: List private endpoints.
"""

helps['network private-endpoint show'] = """
type: command
short-summary: Get the details of a private endpoint.
examples:
  - name: Get the details of a private endpoint (autogenerated)
    text: |
        az network private-endpoint show --name MyPrivateEndpoint --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-endpoint update'] = """
type: command
short-summary: Update a private endpoint.
examples:
  - name: Update a private endpoint.
    text: az network private-endpoint update -g MyResourceGroup -n MyPE --request-message "test" --tags mytag=hello
  - name: Update a private endpoint. (autogenerated)
    text: |
        az network private-endpoint update --name MyPE --resource-group MyResourceGroup --set useRemoteGateways=true
    crafted: true
"""

helps['network private-endpoint dns-zone-group'] = """
type: group
short-summary: Manage private endpoint dns zone group.
"""

helps['network private-endpoint dns-zone-group create'] = """
type: command
short-summary: Create a private endpoint dns zone group.
examples:
  - name: Create a private endpoint dns zone group.
    text: az network private-endpoint dns-zone-group create --endpoint-name MyPE -g MyRG -n MyZoneGroup --zone-name Zone1 --private-dns-zone PrivateDNSZone1

"""

helps['network private-endpoint dns-zone-group add'] = """
type: command
short-summary: Add a private endpoint dns zone into a dns zone group.
examples:
  - name: Add a private endpoint dns zone group.
    text: az network private-endpoint dns-zone-group add --endpoint-name MyPE -g MyRG -n MyZoneGroup --zone-name Zone1 --private-dns-zone PrivateDNSZone1
"""

helps['network private-endpoint dns-zone-group remove'] = """
type: command
short-summary: Remove a private endpoint dns zone into a dns zone group.
examples:
  - name: Remove a private endpoint dns zone group.
    text: az network private-endpoint dns-zone-group remove --endpoint-name MyPE -g MyRG -n MyZoneGroup --zone-name Zone1
"""

helps['network private-endpoint dns-zone-group delete'] = """
type: command
short-summary: Delete a private endpoint dns zone group.
examples:
  - name: Delete a private endpoint dns zone group. (autogenerated)
    text: |
        az network private-endpoint dns-zone-group delete --endpoint-name MyEndpoint --name MyPrivateDnsZoneGroup --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-endpoint dns-zone-group list'] = """
type: command
short-summary: List all private endpoint dns zone groups.
examples:
  - name: List all private endpoint dns zone groups. (autogenerated)
    text: |
        az network private-endpoint dns-zone-group list --endpoint-name MyEndpoint --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-endpoint dns-zone-group show'] = """
type: command
short-summary: Show a private endpoint dns zone group.
examples:
  - name: Show a private endpoint dns zone group. (autogenerated)
    text: |
        az network private-endpoint dns-zone-group show --endpoint-name MyEndpoint --name MyPrivateDnsZoneGroup --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-endpoint ip-config'] = """
type: group
short-summary: Manage private endpoint ip configurations.
"""

helps['network private-endpoint ip-config add'] = """
type: command
short-summary: Add a private endpoint ip configuration.
examples:
  - name: Add a private endpoint ip configuration.
    text: az network private-endpoint ip-config add --endpoint-name MyPE -g MyRG -n MyIpConfig --group-id MyGroup --member-name MyMember --private-ip-address MyPrivateIPAddress
"""

helps['network private-endpoint ip-config remove'] = """
type: command
short-summary: Remove a private endpoint ip configuration.
examples:
  - name: Remove a private endpoint ip configuration.
    text: az network private-endpoint ip-config remove --endpoint-name MyPE -g MyRG -n MyIpConfig
"""

helps['network private-endpoint ip-config list'] = """
type: command
short-summary: List ip configuration within a private endpoint.
examples:
  - name: List ip configuration within a private endpoint.
    text: az network private-endpoint ip-config list --endpoint-name MyPE -g MyRG
"""

helps['network private-endpoint asg'] = """
type: group
short-summary: Manage private endpoint application security groups.
"""

helps['network private-endpoint asg add'] = """
type: command
short-summary: Add a private endpoint application security group.
examples:
  - name: Add a private endpoint application security group.
    text: az network private-endpoint asg add --endpoint-name MyPE -g MyRG --asg-id MyApplicationSecurityGroupId
"""

helps['network private-endpoint asg remove'] = """
type: command
short-summary: Remove a private endpoint application security group.
examples:
  - name: Remove a private endpoint application security group.
    text: az network private-endpoint asg remove --endpoint-name MyPE -g MyRG --asg-id MyApplicationSecurityGroupId
"""

helps['network private-endpoint asg list'] = """
type: command
short-summary: List application security group within a private endpoint.
examples:
  - name: List application security group within a private endpoint.
    text: az network private-endpoint asg list --endpoint-name MyPE -g MyRG
"""

helps['network private-link-service'] = """
type: group
short-summary: Manage private link services.
"""

helps['network private-link-service connection'] = """
type: group
short-summary: Manage private link service endpoint connections.
"""

helps['network private-link-service connection delete'] = """
type: command
short-summary: Delete a private link service endpoint connection.
examples:
  - name: Delete a private link service endpoint connection. (autogenerated)
    text: |
        az network private-link-service connection delete --name MyPrivateEndpointConnection --resource-group MyResourceGroup --service-name MyService
    crafted: true
"""

helps['network private-link-service connection update'] = """
type: command
short-summary: Update a private link service endpoint connection.
long-summary: >
    To update the connection status, the name of the connection should be provided.
    Please obtain this name by running 'az network private-link-service show -g MyResourceGroup -n MyPLSName'.
    The connection name is under the 'privateEndpointConnections' filed.
examples:
  - name: Update the endpoint connections status of private link service
    text: az network private-link-service connection update -g MyResourceGroup -n MyEndpointName.f072a430-2d82-4470-ab30-d23fcfee58d1 --service-name MyPLSName --connection-status Rejected
"""

helps['network private-link-service create'] = """
type: command
short-summary: Create a private link service.
examples:
  - name: Create a private link service
    text: az network private-link-service create -g MyResourceGroup -n MyPLSName --vnet-name MyVnetName --subnet MySubnet --lb-name MyLBName --lb-frontend-ip-configs LoadBalancerFrontEnd -l centralus
"""

helps['network private-link-service delete'] = """
type: command
short-summary: Delete a private link service.
examples:
  - name: Delete a private link service. (autogenerated)
    text: |
        az network private-link-service delete --name MyPrivateLinkService --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-link-service list'] = """
type: command
short-summary: List private link services.
"""

helps['network private-link-service show'] = """
type: command
short-summary: Get the details of a private link service.
examples:
  - name: Get the details of a private link service. (autogenerated)
    text: |
        az network private-link-service show --name MyPrivateLinkService --resource-group MyResourceGroup
    crafted: true
"""

helps['network private-link-service update'] = """
type: command
short-summary: Update a private link service.
examples:
  - name: Update a private link service
    text: az network private-link-service update -g MyResourceGroup -n MyPLSName --visibility SubId1 SubId2 --auto-approval SubId1 SubId2
"""

helps['network private-endpoint-connection'] = """
type: group
short-summary: Manage private endpoint connections.
"""

helps['network private-endpoint-connection approve'] = """
type: command
short-summary: Approve a private endpoint connection.
examples:
  - name: Approve a private endpoint connection for a storage account.
    text: az network private-endpoint-connection approve -g MyResourceGroup -n MyPrivateEndpoint --resource-name MySA --type Microsoft.Storage/storageAccounts --description "Approved"
  - name: Approve a private endpoint connection for a keyvault.
    text: az network private-endpoint-connection approve -g MyResourceGroup -n MyPrivateEndpoint --resource-name MyKV --type Microsoft.Keyvault/vaults --description "Approved"
  - name: Approve a private endpoint connection for an ACR.
    text: az network private-endpoint-connection approve --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001/providers/Microsoft.ContainerRegistry/registries/testreg000002/privateEndpointConnections/testreg000002.6e6bf72bc59d41cc89c698d4cc5ee79d --description "Approved"
"""

helps['network private-endpoint-connection reject'] = """
type: command
short-summary: Reject a private endpoint connection.
examples:
  - name: Reject a private endpoint connection for a storage account.
    text: az network private-endpoint-connection reject -g MyResourceGroup -n MyPrivateEndpoint --resource-name MySA --type Microsoft.Storage/storageAccounts --description "Rejected"
  - name: Reject a private endpoint connection for a keyvault.
    text: az network private-endpoint-connection reject -g MyResourceGroup -n MyPrivateEndpoint --resource-name MyKV --type Microsoft.Keyvault/vaults --description "Rejected"
  - name: Reject a private endpoint connection for an ACR.
    text: az network private-endpoint-connection reject --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001/providers/Microsoft.ContainerRegistry/registries/testreg000002/privateEndpointConnections/testreg000002.6e6bf72bc59d41cc89c698d4cc5ee79d --description "Rejected"
"""

helps['network private-endpoint-connection delete'] = """
type: command
short-summary: Delete a private endpoint connection.
examples:
  - name: Delete a private endpoint connection for a storage account.
    text: az network private-endpoint-connection delete -g MyResourceGroup -n MyPrivateEndpoint --resource-name MySA --type Microsoft.Storage/storageAccounts
  - name: Delete a private endpoint connection for a keyvault.
    text: az network private-endpoint-connection delete -g MyResourceGroup -n MyPrivateEndpoint --resource-name MyKV --type Microsoft.Keyvault/vaults
  - name: Delete a private endpoint connection for an ACR.
    text: az network private-endpoint-connection delete --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001/providers/Microsoft.ContainerRegistry/registries/testreg000002/privateEndpointConnections/testreg000002.6e6bf72bc59d41cc89c698d4cc5ee79d
"""

helps['network private-endpoint-connection show'] = """
type: command
short-summary: Show a private endpoint connection.
examples:
  - name: Show a private endpoint connection for a storage account.
    text: az network private-endpoint-connection show -g MyResourceGroup -n MyPrivateEndpoint --resource-name MySA --type Microsoft.Storage/storageAccounts
  - name: Show a private endpoint connection for a keyvault.
    text: az network private-endpoint-connection show -g MyResourceGroup -n MyPrivateEndpoint --resource-name MyKV --type Microsoft.Keyvault/vaults
  - name: Show a private endpoint connection for an ACR.
    text: az network private-endpoint-connection show --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001/providers/Microsoft.ContainerRegistry/registries/testreg000002/privateEndpointConnections/testreg000002.6e6bf72bc59d41cc89c698d4cc5ee79d
"""

helps['network private-endpoint-connection list'] = """
type: command
short-summary: List all private endpoint connections.
examples:
  - name: List all private endpoint connections for a storage account.
    text: az network private-endpoint-connection list -g MyResourceGroup -n MySA --type Microsoft.Storage/storageAccounts
  - name: List all private endpoint connections for a keyvault.
    text: az network private-endpoint-connection list -g MyResourceGroup -n MyKV --type Microsoft.Keyvault/vaults
  - name: List all private endpoint connections for an ACR.
    text: az network private-endpoint-connection list --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001/providers/Microsoft.ContainerRegistry/registries/testreg000002
"""

helps['network private-link-resource'] = """
type: group
short-summary: Manage private link resources.
"""

helps['network private-link-resource list'] = """
type: command
short-summary: List all private link resources.
examples:
  - name: List all private link resources for a storage account.
    text: az network private-link-resource list -g MyResourceGroup -n MySA --type Microsoft.Storage/storageAccounts
  - name: List all private link resources for a keyvault.
    text: az network private-link-resource list -g MyResourceGroup -n MyKV --type Microsoft.Keyvault/vaults
  - name: List all private link resources for an ACR.
    text: az network private-link-resource list --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001/providers/Microsoft.ContainerRegistry/registries/testreg000002
"""

helps['network profile'] = """
type: group
short-summary: Manage network profiles.
long-summary: >
    To create a network profile, see the create command for the relevant resource. Currently,
    only Azure Container Instances are supported.
"""

helps['network profile delete'] = """
type: command
short-summary: Delete a network profile.
examples:
  - name: Delete a network profile. (autogenerated)
    text: |
        az network profile delete --name MyNetworkProfile --resource-group MyResourceGroup
    crafted: true
"""

helps['network profile list'] = """
type: command
short-summary: List network profiles.
examples:
  - name: List network profiles (autogenerated)
    text: |
        az network profile list --resource-group MyResourceGroup
    crafted: true
"""

helps['network profile show'] = """
type: command
short-summary: Get the details of a network profile.
examples:
  - name: Get the details of a network profile. (autogenerated)
    text: |
        az network profile show --name MyNetworkProfile --resource-group MyResourceGroup
    crafted: true
"""

helps['network custom-ip'] = """
type: group
short-summary: Manage custom IP
"""

helps['network custom-ip prefix'] = """
type: group
short-summary: Manage custom IP prefix resources.
"""

helps['network custom-ip prefix create'] = """
type: command
short-summary: Create a custom IP prefix resource.
examples:
  - name: Create a custom IP prefix resource.
    text: |
        az network custom-ip prefix create --location westus2 --name MyCustomIpPrefix --resource-group MyResourceGroup
"""

helps['network custom-ip prefix wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the custom ip prefix is met.
examples:
  - name: Wait for custom ip prefix to return as created.
    text: |
        az network custom-ip prefix wait --name MyCustomIpPrefix --resource-group MyResourceGroup --created
"""

helps['network custom-ip prefix delete'] = """
type: command
short-summary: Delete a custom IP prefix resource.
examples:
  - name: Delete a custom IP prefix resource.
    text: |
        az network custom-ip prefix delete --name MyCustomIpPrefix --resource-group MyResourceGroup
"""

helps['network custom-ip prefix list'] = """
type: command
short-summary: List custom IP prefix resources.
"""

helps['network custom-ip prefix show'] = """
type: command
short-summary: Get the details of a custom IP prefix resource.
examples:
  - name: Get the details of a custom IP prefix resource.
    text: |
        az network custom-ip prefix show --name MyCustomIpPrefix --resource-group MyResourceGroup --subscription MySubscription
"""

helps['network custom-ip prefix update'] = """
type: command
short-summary: Update a custom IP prefix resource.
examples:
  - name: Update a custom IP prefix resource.
    text: |
        az network custom-ip prefix update --name MyCustomIpPrefix --resource-group MyResourceGroup --tags foo=doo
"""

helps['network public-ip'] = """
type: group
short-summary: Manage public IP addresses.
long-summary: >
    To learn more about public IP addresses visit https://docs.microsoft.com/azure/virtual-network/virtual-network-public-ip-address
"""

helps['network public-ip create'] = """
type: command
short-summary: Create a public IP address.
examples:
  - name: Create a basic public IP resource.
    text: az network public-ip create -g MyResourceGroup -n MyIp
  - name: Create a static public IP resource for a DNS name label.
    text: az network public-ip create -g MyResourceGroup -n MyIp --dns-name MyLabel --allocation-method Static
  - name: Create a public IP resource in an availability zone in the current resource group region.
    text: az network public-ip create -g MyResourceGroup -n MyIp --zone 2
"""

helps['network public-ip delete'] = """
type: command
short-summary: Delete a public IP address.
examples:
  - name: Delete a public IP address.
    text: az network public-ip delete -g MyResourceGroup -n MyIp
"""

helps['network public-ip list'] = """
type: command
short-summary: List public IP addresses.
examples:
  - name: List all public IPs in a subscription.
    text: az network public-ip list
  - name: List all public IPs in a resource group.
    text: az network public-ip list -g MyResourceGroup
  - name: List all public IPs of a domain name label.
    text: az network public-ip list -g MyResourceGroup --query "[?dnsSettings.domainNameLabel=='MyLabel']"
"""

helps['network public-ip prefix'] = """
type: group
short-summary: Manage public IP prefix resources.
"""

helps['network public-ip prefix create'] = """
type: command
short-summary: Create a public IP prefix resource.
examples:
  - name: Create a public IP prefix resource. (autogenerated)
    text: |
        az network public-ip prefix create --length 28 --location westus2 --name MyPublicIPPrefix --resource-group MyResourceGroup
    crafted: true
"""

helps['network public-ip prefix delete'] = """
type: command
short-summary: Delete a public IP prefix resource.
examples:
  - name: Delete a public IP prefix resource. (autogenerated)
    text: |
        az network public-ip prefix delete --name MyPublicIPPrefix --resource-group MyResourceGroup
    crafted: true
"""

helps['network public-ip prefix list'] = """
type: command
short-summary: List public IP prefix resources.
"""

helps['network public-ip prefix show'] = """
type: command
short-summary: Get the details of a public IP prefix resource.
examples:
  - name: Get the details of a public IP prefix resource. (autogenerated)
    text: |
        az network public-ip prefix show --name MyPublicIPPrefix --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network public-ip prefix update'] = """
type: command
short-summary: Update a public IP prefix resource.
examples:
  - name: Update a public IP prefix resource. (autogenerated)
    text: |
        az network public-ip prefix update --name MyPublicIPPrefix --resource-group MyResourceGroup --set useRemoteGateways=true
    crafted: true
"""

helps['network public-ip show'] = """
type: command
short-summary: Get the details of a public IP address.
examples:
  - name: Get information about a public IP resource.
    text: az network public-ip show -g MyResourceGroup -n MyIp
  - name: Get the FQDN and IP address of a public IP resource.
    text: >
        az network public-ip show -g MyResourceGroup -n MyIp --query "{fqdn: dnsSettings.fqdn, address: ipAddress}"
"""

helps['network public-ip update'] = """
type: command
short-summary: Update a public IP address.
examples:
  - name: Update a public IP resource with a DNS name label and static allocation.
    text: az network public-ip update -g MyResourceGroup -n MyIp --dns-name MyLabel --allocation-method Static
"""

helps['network route-filter'] = """
type: group
short-summary: Manage route filters.
long-summary: >
    To learn more about route filters with Microsoft peering with ExpressRoute, visit https://docs.microsoft.com/azure/expressroute/how-to-routefilter-cli
"""

helps['network route-filter create'] = """
type: command
short-summary: Create a route filter.
examples:
  - name: Create a route filter.
    text: az network route-filter create -g MyResourceGroup -n MyRouteFilter
  - name: Create a route filter. (autogenerated)
    text: |
        az network route-filter create --location westus2 --name MyRouteFilter --resource-group MyResourceGroup
    crafted: true
"""

helps['network route-filter delete'] = """
type: command
short-summary: Delete a route filter.
examples:
  - name: Delete a route filter.
    text: az network route-filter delete -g MyResourceGroup -n MyRouteFilter
"""

helps['network route-filter list'] = """
type: command
short-summary: List route filters.
examples:
  - name: List route filters in a resource group.
    text: az network route-filter list -g MyResourceGroup
"""

helps['network route-filter rule'] = """
type: group
short-summary: Manage rules in a route filter.
long-summary: >
    To learn more about route filters with Microsoft peering with ExpressRoute, visit https://docs.microsoft.com/azure/expressroute/how-to-routefilter-cli
"""

helps['network route-filter rule create'] = """
type: command
short-summary: Create a rule in a route filter.
parameters:
  - name: --communities
    short-summary: Space-separated list of border gateway protocol (BGP) community values to filter on.
    populator-commands:
      - az network route-filter rule list-service-communities
examples:
  - name: Create a rule in a route filter to allow Dynamics 365.
    text: |
        az network route-filter rule create -g MyResourceGroup --filter-name MyRouteFilter \\
            -n MyRouteFilterRule --communities 12076:5040 --access Allow
"""

helps['network route-filter rule delete'] = """
type: command
short-summary: Delete a rule from a route filter.
examples:
  - name: Delete a rule from a route filter.
    text: az network route-filter rule delete -g MyResourceGroup --filter-name MyRouteFilter -n MyRouteFilterRule
"""

helps['network route-filter rule list'] = """
type: command
short-summary: List rules in a route filter.
examples:
  - name: List rules in a route filter.
    text: az network route-filter rule list -g MyResourceGroup --filter-name MyRouteFilter
"""

helps['network route-filter rule list-service-communities'] = """
type: command
short-summary: Gets all the available BGP service communities.
examples:
  - name: Gets all the available BGP service communities.
    text: az network route-filter rule list-service-communities -o table
  - name: Get the community value for Exchange.
    text: |
        az network route-filter rule list-service-communities \\
            --query '[].bgpCommunities[?communityName==`Exchange`].[communityValue][][]' -o tsv
"""

helps['network route-filter rule show'] = """
type: command
short-summary: Get the details of a rule in a route filter.
examples:
  - name: Get the details of a rule in a route filter.
    text: az network route-filter rule show -g MyResourceGroup --filter-name MyRouteFilter -n MyRouteFilterRule
"""

helps['network route-filter rule update'] = """
type: command
short-summary: Update a rule in a route filter.
examples:
  - name: Update a rule in a route filter to add Exchange to rule list.
    text: |
        az network route-filter rule update -g MyResourceGroup --filter-name MyRouteFilter \\
            -n MyRouteFilterRule --add communities='12076:5010'
"""

helps['network route-filter show'] = """
type: command
short-summary: Get the details of a route filter.
examples:
  - name: Get the details of a route filter.
    text: az network route-filter show -g MyResourceGroup -n MyRouteFilter
  - name: Get the details of a route filter. (autogenerated)
    text: |
        az network route-filter show --expand peerings --name MyRouteFilter --resource-group MyResourceGroup
    crafted: true
"""

helps['network route-filter update'] = """
type: command
short-summary: Update a route filter.
long-summary: >
    This command can only be used to update the tags for a route filter. Name and resource group are immutable and cannot be updated.
examples:
  - name: Update the tags on a route filter.
    text: az network route-filter update -g MyResourceGroup -n MyRouteFilter --set tags.CostCenter=MyBusinessGroup
"""

helps['network route-table'] = """
type: group
short-summary: Manage route tables.
"""

helps['network route-table create'] = """
type: command
short-summary: Create a route table.
examples:
  - name: Create a route table.
    text: az network route-table create -g MyResourceGroup -n MyRouteTable
"""

helps['network route-table delete'] = """
type: command
short-summary: Delete a route table.
examples:
  - name: Delete a route table.
    text: az network route-table delete -g MyResourceGroup -n MyRouteTable
"""

helps['network route-table list'] = """
type: command
short-summary: List route tables.
examples:
  - name: List all route tables in a subscription.
    text: az network route-table list -g MyResourceGroup
"""

helps['network route-table route'] = """
type: group
short-summary: Manage routes in a route table.
"""

helps['network route-table route create'] = """
type: command
short-summary: Create a route in a route table.
examples:
  - name: Create a route that forces all inbound traffic to a Network Virtual Appliance.
    text: |
        az network route-table route create -g MyResourceGroup --route-table-name MyRouteTable -n MyRoute \\
            --next-hop-type VirtualAppliance --address-prefix 10.0.0.0/16 --next-hop-ip-address 10.0.100.4
"""

helps['network route-table route delete'] = """
type: command
short-summary: Delete a route from a route table.
examples:
  - name: Delete a route from a route table.
    text: az network route-table route delete -g MyResourceGroup --route-table-name MyRouteTable -n MyRoute
"""

helps['network route-table route list'] = """
type: command
short-summary: List routes in a route table.
examples:
  - name: List routes in a route table.
    text: az network route-table route list -g MyResourceGroup --route-table-name MyRouteTable
"""

helps['network route-table route show'] = """
type: command
short-summary: Get the details of a route in a route table.
examples:
  - name: Get the details of a route in a route table.
    text: az network route-table route show -g MyResourceGroup --route-table-name MyRouteTable -n MyRoute -o table
"""

helps['network route-table route update'] = """
type: command
short-summary: Update a route in a route table.
examples:
  - name: Update a route in a route table to change the next hop ip address.
    text: az network route-table route update -g MyResourceGroup --route-table-name MyRouteTable \\ -n MyRoute --next-hop-ip-address 10.0.100.5
  - name: Update a route in a route table. (autogenerated)
    text: |
        az network route-table route update --address-prefix 10.0.0.0/16 --name MyRoute --next-hop-ip-address 10.0.100.5 --next-hop-type VirtualNetworkGateway --resource-group MyResourceGroup --route-table-name MyRouteTable
    crafted: true
"""

helps['network route-table show'] = """
type: command
short-summary: Get the details of a route table.
examples:
  - name: Get the details of a route table.
    text: az network route-table show -g MyResourceGroup -n MyRouteTable
"""

helps['network route-table update'] = """
type: command
short-summary: Update a route table.
examples:
  - name: Update a route table to disable BGP route propogation.
    text: az network route-table update -g MyResourceGroup -n MyRouteTable --disable-bgp-route-propagation true
"""

helps['network service-endpoint'] = """
type: group
short-summary: Manage policies related to service endpoints.
"""

helps['network service-endpoint policy'] = """
type: group
short-summary: Manage service endpoint policies.
"""

helps['network service-endpoint policy create'] = """
type: command
short-summary: Create a service endpoint policy.
examples:
  - name: Create a service endpoint policy. (autogenerated)
    text: |
        az network service-endpoint policy create --name MyServiceEndpointPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network service-endpoint policy delete'] = """
type: command
short-summary: Delete a service endpoint policy.
"""

helps['network service-endpoint policy list'] = """
type: command
short-summary: List service endpoint policies.
examples:
  - name: List service endpoint policies. (autogenerated)
    text: |
        az network service-endpoint policy list --resource-group MyResourceGroup
    crafted: true
"""

helps['network service-endpoint policy show'] = """
type: command
short-summary: Get the details of a service endpoint policy.
examples:
  - name: Get the details of a service endpoint policy. (autogenerated)
    text: |
        az network service-endpoint policy show --name MyServiceEndpointPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network service-endpoint policy update'] = """
type: command
short-summary: Update a service endpoint policy.
"""

helps['network service-endpoint policy-definition'] = """
type: group
short-summary: Manage service endpoint policy definitions.
"""

helps['network service-endpoint policy-definition create'] = """
type: command
short-summary: Create a service endpoint policy definition.
parameters:
  - name: --service
    populator-commands:
      - az network service-endpoint list
"""

helps['network service-endpoint policy-definition delete'] = """
type: command
short-summary: Delete a service endpoint policy definition.
examples:
  - name: Delete a service endpoint policy definition (autogenerated)
    text: |
        az network service-endpoint policy-definition delete --name myserviceendpointpolicydefinition --policy-name mypolicy --resource-group myresourcegroup
    crafted: true
"""

helps['network service-endpoint policy-definition list'] = """
type: command
short-summary: List service endpoint policy definitions.
examples:
  - name: List service endpoint policy definitions. (autogenerated)
    text: |
        az network service-endpoint policy-definition list --policy-name MyPolicy --resource-group MyResourceGroup
    crafted: true
"""

helps['network service-endpoint policy-definition show'] = """
type: command
short-summary: Get the details of a service endpoint policy definition.
examples:
  - name: Get the details of a service endpoint policy definition. (autogenerated)
    text: |
        az network service-endpoint policy-definition show --name myserviceendpointpolicydefinition --policy-name mypolicy --resource-group myresourcegroup
    crafted: true
"""

helps['network service-endpoint policy-definition update'] = """
type: command
short-summary: Update a service endpoint policy definition.
examples:
  - name: Update a service endpoint policy definition. (autogenerated)
    text: |
        az network service-endpoint policy-definition update --add communities='12076:5010' --name MyServiceEndpointPolicyDefinition --policy-name MyPolicy --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network traffic-manager'] = """
type: group
short-summary: Manage the routing of incoming traffic.
"""

helps['network traffic-manager endpoint'] = """
type: group
short-summary: Manage Azure Traffic Manager end points.
"""

helps['network traffic-manager endpoint create'] = """
type: command
short-summary: Create a traffic manager endpoint.
parameters:
  - name: --geo-mapping
    populator-commands:
      - az network traffic-manager endpoint show-geographic-hierarchy
examples:
  - name: Create an endpoint for a performance profile to point to an Azure Web App endpoint.
    text: |
        az network traffic-manager endpoint create -g MyResourceGroup --profile-name MyTmProfile \\
            -n MyEndpoint --type azureEndpoints --target-resource-id $MyWebApp1Id --endpoint-status enabled
"""

helps['network traffic-manager endpoint delete'] = """
type: command
short-summary: Delete a traffic manager endpoint.
examples:
  - name: Delete a traffic manager endpoint.
    text: az network traffic-manager endpoint delete -g MyResourceGroup \\ --profile-name MyTmProfile -n MyEndpoint --type azureEndpoints
  - name: Delete a traffic manager endpoint. (autogenerated)
    text: |
        az network traffic-manager endpoint delete --name MyEndpoint --profile-name MyTmProfile --resource-group MyResourceGroup --subscription MySubscription --type azureEndpoints
    crafted: true
"""

helps['network traffic-manager endpoint list'] = """
type: command
short-summary: List traffic manager endpoints.
examples:
  - name: List traffic manager endpoints.
    text: az network traffic-manager endpoint list -g MyResourceGroup --profile-name MyTmProfile
"""

helps['network traffic-manager endpoint show'] = """
type: command
short-summary: Get the details of a traffic manager endpoint.
examples:
  - name: Get the details of a traffic manager endpoint.
    text: |
        az network traffic-manager endpoint show -g MyResourceGroup \\
            --profile-name MyTmProfile -n MyEndpoint --type azureEndpoints
"""

helps['network traffic-manager endpoint show-geographic-hierarchy'] = """
type: command
short-summary: Get the default geographic hierarchy used by the geographic traffic routing method.
examples:
  - name: Get the default geographic hierarchy used by the geographic traffic routing method.
    text: az network traffic-manager endpoint show-geographic-hierarchy
"""

helps['network traffic-manager endpoint update'] = """
type: command
short-summary: Update a traffic manager endpoint.
examples:
  - name: Update a traffic manager endpoint to change its weight.
    text: az network traffic-manager endpoint update -g MyResourceGroup --profile-name MyTmProfile \\ -n MyEndpoint --weight 20 --type azureEndpoints
  - name: Update a traffic manager endpoint. (autogenerated)
    text: |
        az network traffic-manager endpoint update --name MyEndpoint --profile-name MyTmProfile --resource-group MyResourceGroup --target webserver.mysite.com --type azureEndpoints
    crafted: true
  - name: Update a traffic manager endpoint. (autogenerated)
    text: |
        az network traffic-manager endpoint update --endpoint-status Enabled --name MyEndpoint --profile-name MyTmProfile --resource-group MyResourceGroup --type azureEndpoints
    crafted: true
"""

helps['network traffic-manager profile'] = """
type: group
short-summary: Manage Azure Traffic Manager profiles.
"""

helps['network traffic-manager profile check-dns'] = """
type: command
short-summary: Check the availability of a relative DNS name.
long-summary: This checks for the avabilility of dns prefixes for trafficmanager.net.
examples:
  - name: Check the availability of 'mywebapp.trafficmanager.net' in Azure.
    text: az network traffic-manager profile check-dns -n mywebapp
"""

helps['network traffic-manager profile create'] = """
type: command
short-summary: Create a traffic manager profile.
examples:
  - name: Create a traffic manager profile with performance routing.
    text: |
        az network traffic-manager profile create -g MyResourceGroup -n MyTmProfile --routing-method Performance \\
            --unique-dns-name mywebapp --ttl 30 --protocol HTTP --port 80 --path "/"
"""

helps['network traffic-manager profile delete'] = """
type: command
short-summary: Delete a traffic manager profile.
examples:
  - name: Delete a traffic manager profile.
    text: az network traffic-manager profile delete -g MyResourceGroup -n MyTmProfile
  - name: Delete a traffic manager profile. (autogenerated)
    text: |
        az network traffic-manager profile delete --name MyTmProfile --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network traffic-manager profile list'] = """
type: command
short-summary: List traffic manager profiles.
examples:
  - name: List traffic manager profiles.
    text: az network traffic-manager profile list -g MyResourceGroup
"""

helps['network traffic-manager profile show'] = """
type: command
short-summary: Get the details of a traffic manager profile.
examples:
  - name: Get the details of a traffic manager profile.
    text: az network traffic-manager profile show -g MyResourceGroup -n MyTmProfile
"""

helps['network traffic-manager profile update'] = """
type: command
short-summary: Update a traffic manager profile.
examples:
  - name: Update a traffic manager profile to change the TTL to 300.
    text: az network traffic-manager profile update -g MyResourceGroup -n MyTmProfile --ttl 300
  - name: Update a traffic manager profile. (autogenerated)
    text: |
        az network traffic-manager profile update --name MyTmProfile --resource-group MyResourceGroup --status Enabled
    crafted: true
"""

helps['network vnet'] = """
type: group
short-summary: Manage Azure Virtual Networks.
long-summary: To learn more about Virtual Networks visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-network
"""

helps['network vnet check-ip-address'] = """
type: command
short-summary: Check if a private IP address is available for use within a virtual network.
examples:
  - name: Check whether 10.0.0.4 is available within MyVnet.
    text: az network vnet check-ip-address -g MyResourceGroup -n MyVnet --ip-address 10.0.0.4
"""

helps['network vnet create'] = """
type: command
short-summary: Create a virtual network.
long-summary: >
    You may also create a subnet at the same time by specifying a subnet name and (optionally) an address prefix.
    To learn about how to create a virtual network visit https://docs.microsoft.com/azure/virtual-network/manage-virtual-network#create-a-virtual-network
examples:
  - name: Create a virtual network.
    text: az network vnet create -g MyResourceGroup -n MyVnet
  - name: Create a virtual network with a specific address prefix and one subnet.
    text: |
        az network vnet create -g MyResourceGroup -n MyVnet --address-prefix 10.0.0.0/16 \\
            --subnet-name MySubnet --subnet-prefix 10.0.0.0/24
  - name: Create a virtual network. (autogenerated)
    text: |
        az network vnet create --address-prefixes 10.0.0.0/16 --name MyVirtualNetwork --resource-group MyResourceGroup --subnet-name MyAseSubnet --subnet-prefixes 10.0.0.0/24
    crafted: true
"""

helps['network vnet delete'] = """
type: command
short-summary: Delete a virtual network.
examples:
  - name: Delete a virtual network.
    text: az network vnet delete -g MyResourceGroup -n myVNet
"""

helps['network vnet list'] = """
type: command
short-summary: List virtual networks.
examples:
  - name: List all virtual networks in a subscription.
    text: az network vnet list
  - name: List all virtual networks in a resource group.
    text: az network vnet list -g MyResourceGroup
  - name: List virtual networks in a subscription which specify a certain address prefix.
    text: az network vnet list --query "[?contains(addressSpace.addressPrefixes, '10.0.0.0/16')]"
"""

helps['network vnet list-endpoint-services'] = """
type: command
short-summary: List which services support VNET service tunneling in a given region.
long-summary: To learn more about service endpoints visit https://docs.microsoft.com/azure/virtual-network/virtual-network-service-endpoints-configure#azure-cli
examples:
  - name: List the endpoint services available for use in the West US region.
    text: az network vnet list-endpoint-services -l westus -o table
"""

helps['network vnet peering'] = """
type: group
short-summary: Manage peering connections between Azure Virtual Networks.
long-summary: To learn more about virtual network peering visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-peering
"""

helps['network vnet peering create'] = """
type: command
short-summary: Create a virtual network peering connection.
long-summary: >
    To successfully peer two virtual networks this command must be called twice with
    the values for --vnet-name and --remote-vnet reversed.
examples:
  - name: Create a peering connection between two virtual networks.
    text: |
        az network vnet peering create -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1 \\
            --remote-vnet MyVnet2Id --allow-vnet-access
"""

helps['network vnet peering sync'] = """
type: command
short-summary: Sync a virtual network peering connection.
examples:
  - name: Sync a peering connection.
    text: |
        az network vnet peering sync -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
"""

helps['network vnet peering delete'] = """
type: command
short-summary: Delete a peering.
examples:
  - name: Delete a virtual network peering connection.
    text: az network vnet peering delete -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
"""

helps['network vnet peering list'] = """
type: command
short-summary: List peerings.
examples:
  - name: List all peerings of a specified virtual network.
    text: az network vnet peering list -g MyResourceGroup --vnet-name MyVnet1
"""

helps['network vnet peering show'] = """
type: command
short-summary: Show details of a peering.
examples:
  - name: Show all details of the specified virtual network peering.
    text: az network vnet peering show -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
"""

helps['network vnet peering update'] = """
type: command
short-summary: Update a peering.
examples:
  - name: Change forwarded traffic configuration of a virtual network peering.
    text: >
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1 --set allowForwardedTraffic=true
  - name: Change virtual network access of a virtual network peering.
    text: >
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1 --set allowVirtualNetworkAccess=true
  - name: Change gateway transit property configuration of a virtual network peering.
    text: >
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1 --set allowGatewayTransit=true
  - name: Use remote gateways in virtual network peering.
    text: >
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1 --set useRemoteGateways=true
"""

helps['network vnet show'] = """
type: command
short-summary: Get the details of a virtual network.
examples:
  - name: Get details for MyVNet.
    text: az network vnet show -g MyResourceGroup -n MyVNet
"""

helps['network vnet list-available-ips'] = """
type: command
short-summary: List some available ips in the vnet.
examples:
  - name: List some available ips in the vnet.
    text: az network vnet list-available-ips -g MyResourceGroup -n MyVNet
"""

helps['network vnet subnet'] = """
type: group
short-summary: Manage subnets in an Azure Virtual Network.
long-summary: To learn more about subnets visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-subnet
"""

helps['network vnet subnet create'] = """
type: command
short-summary: Create a subnet and associate an existing NSG and route table.
parameters:
  - name: --service-endpoints
    short-summary: Space-separated list of services allowed private access to this subnet.
    populator-commands:
      - az network vnet list-endpoint-services
  - name: --nat-gateway
    short-summary: Attach Nat Gateway to subnet
examples:
  - name: Create new subnet attached to an NSG with a custom route table.
    text: |
        az network vnet subnet create -g MyResourceGroup --vnet-name MyVnet -n MySubnet \\
            --address-prefixes 10.0.0.0/24 --network-security-group MyNsg --route-table MyRouteTable
  - name: Create new subnet attached to a NAT gateway.
    text: az network vnet subnet create -n MySubnet --vnet-name MyVnet -g MyResourceGroup --nat-gateway MyNatGateway --address-prefixes "10.0.0.0/21"
"""

helps['network vnet subnet delete'] = """
type: command
short-summary: Delete a subnet.
examples:
  - name: Delete a subnet.
    text: az network vnet subnet delete -g MyResourceGroup -n MySubnet
  - name: Delete a subnet. (autogenerated)
    text: |
        az network vnet subnet delete --name MySubnet --resource-group MyResourceGroup --vnet-name MyVnet
    crafted: true
"""

helps['network vnet subnet list'] = """
type: command
short-summary: List the subnets in a virtual network.
examples:
  - name: List the subnets in a virtual network.
    text: az network vnet subnet list -g MyResourceGroup --vnet-name MyVNet
"""

helps['network vnet subnet list-available-delegations'] = """
type: command
short-summary: List the services available for subnet delegation.
examples:
  - name: Retrieve the service names for available delegations in the West US region.
    text: az network vnet subnet list-available-delegations -l westus --query [].serviceName
  - name: List the services available for subnet delegation. (autogenerated)
    text: |
        az network vnet subnet list-available-delegations --resource-group MyResourceGroup
    crafted: true
"""

helps['network vnet subnet show'] = """
type: command
short-summary: Show details of a subnet.
examples:
  - name: Show the details of a subnet associated with a virtual network.
    text: az network vnet subnet show -g MyResourceGroup -n MySubnet --vnet-name MyVNet
"""

helps['network vnet subnet update'] = """
type: command
short-summary: Update a subnet.
parameters:
  - name: --service-endpoints
    short-summary: Space-separated list of services allowed private access to this subnet.
    populator-commands:
      - az network vnet list-endpoint-services
  - name: --nat-gateway
    short-summary: Attach Nat Gateway to subnet
examples:
  - name: Associate a network security group to a subnet.
    text: az network vnet subnet update -g MyResourceGroup -n MySubnet --vnet-name MyVNet --network-security-group MyNsg
  - name: Update subnet with NAT gateway.
    text: az network vnet subnet update -n MySubnet --vnet-name MyVnet -g MyResourceGroup --nat-gateway MyNatGateway --address-prefixes "10.0.0.0/21"
  - name: Disable the private endpoint network policies
    text: az network vnet subnet update -n MySubnet --vnet-name MyVnet -g MyResourceGroup --disable-private-endpoint-network-policies
"""

helps['network vnet update'] = """
type: command
short-summary: Update a virtual network.
examples:
  - name: Update a virtual network with the IP address of a DNS server.
    text: az network vnet update -g MyResourceGroup -n MyVNet --dns-servers 10.2.0.8
  - name: Update a virtual network to delete DNS server.
    text: az network vnet update -g MyResourceGroup -n MyVNet --dns-servers ''
  - name: Update a virtual network. (autogenerated)
    text: |
        az network vnet update --address-prefixes 40.1.0.0/24 --name MyVNet --resource-group MyResourceGroup
    crafted: true
"""

helps['network vnet-gateway'] = """
type: group
short-summary: Use an Azure Virtual Network Gateway to establish secure, cross-premises connectivity.
long-summary: >
    To learn more about Azure Virtual Network Gateways, visit https://docs.microsoft.com/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-cli
"""

helps['network vnet-gateway create'] = """
type: command
short-summary: Create a virtual network gateway.
parameters:
  - name: --nat-rule
    short-summary: VirtualNetworkGatewayNatRule Resource.
    long-summary: |
        Usage: --nat-rule name=rule type=Static mode=EgressSnat internal-mappings=10.4.0.0/24 external-mappings=192.168.21.0/24 ip-config-id=/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/virtualNetworkGateways/gateway1/ipConfigurations/default

        name: Required.The name of the resource that is unique within a resource group. This name can be used to access the resource.
        internal-mappings: Required.The private IP address internal mapping for NAT.
        external-mappings: Required.The private IP address external mapping for NAT.
        type: The type of NAT rule for VPN NAT.
        mode: The Source NAT direction of a VPN NAT.
        ip-config-id: The IP Configuration ID this NAT rule applies to.

        Multiple nat rules can be specified by using more than one `--nat-rule` argument.
examples:
  - name: Create a basic virtual network gateway for site-to-site connectivity.
    text: |
        az network vnet-gateway create -g MyResourceGroup -n MyVnetGateway --public-ip-address MyGatewayIp \\
            --vnet MyVnet --gateway-type Vpn --sku VpnGw1 --vpn-type RouteBased --no-wait
  - name: >
        Create a basic virtual network gateway that provides point-to-site connectivity with a RADIUS secret that matches what is configured on a RADIUS server.
    text: |
        az network vnet-gateway create -g MyResourceGroup -n MyVnetGateway --public-ip-address MyGatewayIp \\
            --vnet MyVnet --gateway-type Vpn --sku VpnGw1 --vpn-type RouteBased --address-prefixes 40.1.0.0/24 \\
            --client-protocol IkeV2 SSTP --radius-secret 111_aaa --radius-server 30.1.1.15 --vpn-gateway-generation Generation1

  - name: >
        Create a basic virtual network gateway with multi authentication
    text: |
        az network vnet-gateway create -g MyResourceGroup -n MyVnetGateway --public-ip-address MyGatewayIp --vnet MyVnet --gateway-type Vpn --sku VpnGw1 --vpn-type RouteBased --address-prefixes 40.1.0.0/24 --client-protocol OpenVPN --radius-secret 111_aaa --radius-server 30.1.1.15 --aad-issuer https://sts.windows.net/00000-000000-00000-0000-000/ --aad-tenant https://login.microsoftonline.com/000 --aad-audience 0000-000 --root-cert-name root-cert --root-cert-data "root-cert.cer" --vpn-auth-type AAD Certificate Radius
  - name: Create a virtual network gateway. (autogenerated)
    text: |
        az network vnet-gateway create --gateway-type Vpn --location westus2 --name MyVnetGateway --no-wait --public-ip-addresses myVGPublicIPAddress --resource-group MyResourceGroup --sku Basic --vnet MyVnet --vpn-type PolicyBased
    crafted: true
"""

helps['network vnet-gateway delete'] = """
type: command
short-summary: Delete a virtual network gateway.
long-summary: >
    In order to delete a Virtual Network Gateway, you must first delete ALL Connection objects in Azure that are
     connected to the Gateway. After deleting the Gateway, proceed to delete other resources now not in use.
     For more information, follow the order of instructions on this page:
     https://docs.microsoft.com/azure/vpn-gateway/vpn-gateway-delete-vnet-gateway-portal
examples:
  - name: Delete a virtual network gateway.
    text: az network vnet-gateway delete -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway disconnect-vpn-connections'] = """
type: command
short-summary: Disconnect vpn connections of virtual network gateway.
examples:
  - name: Disconnect vpn connections of virtual network gateway.
    text: az network vnet-gateway disconnect-vpn-connections -g MyResourceGroup -n MyVnetGateway --vpn-connections MyConnetion1ByName MyConnection2ByID
"""

helps['network vnet-gateway ipsec-policy'] = """
type: group
short-summary: Manage virtual network gateway IPSec policies.
"""

helps['network vnet-gateway ipsec-policy add'] = """
type: command
short-summary: Add a virtual network gateway IPSec policy.
long-summary: Set all IPsec policies of a virtual network gateway. If you want to set any IPsec policy, you must set them all.
examples:
  - name: Add specified IPsec policies to a gateway instead of relying on defaults.
    text: |
        az network vnet-gateway ipsec-policy add -g MyResourceGroup --gateway-name MyGateway \\
            --dh-group DHGroup14 --ike-encryption AES256 --ike-integrity SHA384 --ipsec-encryption DES3 \\
            --ipsec-integrity GCMAES256 --pfs-group PFS2048 --sa-lifetime 27000 --sa-max-size 102400000
"""

helps['network vnet-gateway ipsec-policy clear'] = """
type: command
short-summary: Delete all IPsec policies on a virtual network gateway.
examples:
  - name: Remove all previously specified IPsec policies from a gateway.
    text: az network vnet-gateway ipsec-policy clear -g MyResourceGroup --gateway-name MyConnection
"""

helps['network vnet-gateway ipsec-policy list'] = """
type: command
short-summary: List IPSec policies associated with a virtual network gateway.
examples:
  - name: List the IPsec policies set on a gateway.
    text: az network vnet-gateway ipsec-policy list -g MyResourceGroup --gateway-name MyConnection
"""

helps['network vnet-gateway list'] = """
type: command
short-summary: List virtual network gateways.
examples:
  - name: List virtual network gateways in a resource group.
    text: az network vnet-gateway list -g MyResourceGroup
"""

helps['network vnet-gateway list-advertised-routes'] = """
type: command
short-summary: List the routes of a virtual network gateway advertised to the specified peer.
examples:
  - name: List the routes of a virtual network gateway advertised to the specified peer.
    text: az network vnet-gateway list-advertised-routes -g MyResourceGroup -n MyVnetGateway --peer 23.10.10.9
"""

helps['network vnet-gateway list-bgp-peer-status'] = """
type: command
short-summary: Retrieve the status of BGP peers.
examples:
  - name: Retrieve the status of a BGP peer.
    text: az network vnet-gateway list-bgp-peer-status -g MyResourceGroup -n MyVnetGateway --peer 23.10.10.9
"""

helps['network vnet-gateway list-learned-routes'] = """
type: command
short-summary: This operation retrieves a list of routes the virtual network gateway has learned, including routes learned from BGP peers.
examples:
  - name: Retrieve a list of learned routes.
    text: az network vnet-gateway list-learned-routes -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway show-supported-devices'] = """
type: command
short-summary: Get a xml format representation for supported vpn devices.
examples:
  - name: Get a xml format representation for supported vpn devices.
    text: az network vnet-gateway show-supported-devices -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway reset'] = """
type: command
short-summary: Reset a virtual network gateway.
examples:
  - name: Reset a virtual network gateway.
    text: az network vnet-gateway reset -g MyResourceGroup -n MyVnetGateway
  - name: Reset a virtual network gateway with Active-Active feature enabled.
    text: az network vnet-gateway reset -g MyResourceGroup -n MyVnetGateway --gateway-vip MyGatewayIP
"""

helps['network vnet-gateway revoked-cert'] = """
type: group
short-summary: Manage revoked certificates in a virtual network gateway.
long-summary: Prevent machines using this certificate from accessing Azure through this gateway.
"""

helps['network vnet-gateway revoked-cert create'] = """
type: command
short-summary: Revoke a certificate.
examples:
  - name: Revoke a certificate.
    text: |
        az network vnet-gateway revoked-cert create -g MyResourceGroup -n MyRootCertificate \\
            --gateway-name MyVnetGateway --thumbprint abc123
"""

helps['network vnet-gateway revoked-cert delete'] = """
type: command
short-summary: Delete a revoked certificate.
examples:
  - name: Delete a revoked certificate.
    text: az network vnet-gateway revoked-cert delete -g MyResourceGroup -n MyRootCertificate --gateway-name MyVnetGateway
  - name: Delete a revoked certificate. (autogenerated)
    text: |
        az network vnet-gateway revoked-cert delete --gateway-name MyVnetGateway --name MyRootCertificate --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network vnet-gateway root-cert'] = """
type: group
short-summary: Manage root certificates of a virtual network gateway.
"""

helps['network vnet-gateway root-cert create'] = """
type: command
short-summary: Upload a root certificate.
examples:
  - name: Add a Root Certificate to the list of certs allowed to connect to this Gateway.
    text: |
        az network vnet-gateway root-cert create -g MyResourceGroup -n MyRootCertificate \\
            --gateway-name MyVnetGateway --public-cert-data MyCertificateData
"""

helps['network vnet-gateway root-cert delete'] = """
type: command
short-summary: Delete a root certificate.
examples:
  - name: Remove a certificate from the list of Root Certificates whose children are allowed to access this Gateway.
    text: az network vnet-gateway root-cert delete -g MyResourceGroup -n MyRootCertificate --gateway-name MyVnetGateway
  - name: Delete a root certificate. (autogenerated)
    text: |
        az network vnet-gateway root-cert delete --gateway-name MyVnetGateway --name MyRootCertificate --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network vnet-gateway show'] = """
type: command
short-summary: Get the details of a virtual network gateway.
examples:
  - name: Get the details of a virtual network gateway.
    text: az network vnet-gateway show -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway update'] = """
type: command
short-summary: Update a virtual network gateway.
examples:
  - name: Change the SKU of a virtual network gateway.
    text: az network vnet-gateway update -g MyResourceGroup -n MyVnetGateway --sku VpnGw2
  - name: Update a virtual network gateway. (autogenerated)
    text: |
        az network vnet-gateway update --address-prefixes 40.1.0.0/24 --client-protocol IkeV2 --name MyVnetGateway --resource-group MyResourceGroup
    crafted: true
"""

helps['network vnet-gateway packet-capture'] = """
type: group
short-summary: Manage packet capture on a virtual network gateway.
"""

helps['network vnet-gateway packet-capture wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vnet gateway packet capture is met.
"""

helps['network vnet-gateway packet-capture start'] = """
type: command
short-summary: Start packet capture on a virtual network gateway.
examples:
  - name: Start packet capture on a virtual network gateway.
    text: az network vnet-gateway packet-capture start -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway packet-capture stop'] = """
type: command
short-summary: Stop packet capture on a virtual network gateway.
examples:
  - name: Stop packet capture on a virtual network gateway.
    text: az network vnet-gateway packet-capture stop -g MyResourceGroup -n MyVnetGateway --sas-url https://myStorageAct.blob.azure.com/artifacts?st=2019-04-10T22%3A12Z&se=2019-04-11T09%3A12Z&sp=rl&sv=2018-03-28&sr=c&sig=0000000000
"""

helps['network vnet-gateway vpn-client'] = """
type: group
short-summary: Download a VPN client configuration required to connect to Azure via point-to-site.
"""

helps['network vnet-gateway vpn-client generate'] = """
type: command
short-summary: Generate VPN client configuration.
long-summary: The command outputs a URL to a zip file for the generated VPN client configuration.
examples:
  - name: Create the VPN client configuration for RADIUS with EAP-MSCHAV2 authentication.
    text: az network vnet-gateway vpn-client generate -g MyResourceGroup -n MyVnetGateway --authentication-method EAPMSCHAPv2
  - name: Create the VPN client configuration for AMD64 architecture.
    text: az network vnet-gateway vpn-client generate -g MyResourceGroup -n MyVnetGateway --processor-architecture Amd64
  - name: Generate VPN client configuration. (autogenerated)
    text: |
        az network vnet-gateway vpn-client generate --name MyVnetGateway --processor-architecture Amd64 --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network vnet-gateway vpn-client show-url'] = """
type: command
short-summary: Retrieve a pre-generated VPN client configuration.
long-summary: The profile needs to be generated first using vpn-client generate command.
examples:
  - name: Get the pre-generated point-to-site VPN client of the virtual network gateway.
    text: az network vnet-gateway vpn-client show-url -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway vpn-client show-health'] = """
type: command
short-summary: Get the VPN client connection health detail per P2S client connection of the virtual network gateway.
examples:
  - name: Get the VPN client connection health detail per P2S client connection of the virtual network gateway.
    text: az network vnet-gateway vpn-client show-health -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway vpn-client ipsec-policy'] = """
type: group
short-summary: Manage the VPN client connection ipsec-policy for P2S client connection of the virtual network gateway.
"""

helps['network vnet-gateway vpn-client ipsec-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vnet gateway vpn client ipsec policy is met.
"""

helps['network vnet-gateway vpn-client ipsec-policy show'] = """
type: command
short-summary: Get the VPN client connection ipsec policy per P2S client connection of the virtual network gateway.
examples:
  - name: Get the VPN client connection ipsec policy per P2S client connection of the virtual network gateway.
    text: az network vnet-gateway vpn-client ipsec-policy show -g MyResourceGroup -n MyVnetGateway
"""

helps['network vnet-gateway vpn-client ipsec-policy set'] = """
type: command
short-summary: Set the VPN client connection ipsec policy per P2S client connection of the virtual network gateway.
examples:
  - name: Set the VPN client connection ipsec policy per P2S client connection of the virtual network gateway.
    text: |-
        az network vnet-gateway vpn-client ipsec-policy set -g MyResourceGroup -n MyVnetGateway \
        --dh-group DHGroup14 --ike-encryption AES256 --ike-integrity SHA384 --ipsec-encryption DES3 \
        --ipsec-integrity GCMAES256 --pfs-group PFS2048 --sa-lifetime 27000 --sa-max-size 102400000
"""

helps['network vnet-gateway wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the virtual network gateway is met.
examples:
  - name: Pause CLI until the virtual network gateway is created.
    text: az network vnet-gateway wait -g MyResourceGroup -n MyVnetGateway --created
  - name: Place the CLI in a waiting state until a condition of the virtual network gateway is met. (autogenerated)
    text: |
        az network vnet-gateway wait --name MyVnetGateway --resource-group MyResourceGroup --updated
    crafted: true
"""

helps['network vnet-gateway aad'] = """
type: group
short-summary: Manage AAD(Azure Active Directory) authentication of a virtual network gateway
"""

helps['network vnet-gateway aad assign'] = """
type: command
short-summary: Assign/Update AAD(Azure Active Directory) authentication to a virtual network gateway.
examples:
  - name: Assign AAD authentication to a virtual network gateway
    text: |-
        az network vnet-gateway aad assign \\
        --resource-group MyResourceGroup \\
        --gateway-name MyVnetGateway \\
        --tenant MyAADTenantURI \\
        --audience MyAADAudienceId \\
        --issuer MyAADIssuerURI
"""

helps['network vnet-gateway aad show'] = """
type: command
short-summary: Show AAD(Azure Active Directory) authentication of a virtual network gateway
examples:
  - name: Show AAD information
    text: az network vnet-gateway aad show --resource-group MyResourceGroup --gateway-name MyVnetGateway
"""

helps['network vnet-gateway aad remove'] = """
type: command
short-summary: Remove AAD(Azure Active Directory) authentication from a virtual network gateway
examples:
  - name: Remove AAD information
    text: az network vnet-gateway aad remove --resource-group MyResourceGroup --gateway-name MyVnetGateway
"""

helps['network vnet-gateway nat-rule'] = """
type: group
short-summary: Manage nat rule in a virtual network gateway
"""

helps['network vnet-gateway nat-rule wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vnet gateway nat rule is met.
"""

helps['network vnet-gateway nat-rule add'] = """
type: command
short-summary: Add nat rule in a virtual network gateway
examples:
  - name: Add nat rule
    text: az network vnet-gateway nat-rule add --resource-group MyResourceGroup --gateway-name MyVnetGateway --name Nat \
    --internal-mappings 10.4.0.0/24 --external-mappings 192.168.21.0/24
"""

helps['network vnet-gateway nat-rule list'] = """
type: command
short-summary: List nat rule for a virtual network gateway
examples:
  - name: List nat rule
    text: az network vnet-gateway nat-rule list --resource-group MyResourceGroup --gateway-name MyVnetGateway
"""

helps['network vnet-gateway nat-rule remove'] = """
type: command
short-summary: Remove nat rule from a virtual network gateway
examples:
  - name: Remove nat rule
    text: az network vnet-gateway nat-rule remove --resource-group MyResourceGroup --gateway-name MyVnetGateway \
    --name Nat
"""

helps['network vpn-connection'] = """
type: group
short-summary: Manage VPN connections.
long-summary: >
    For more information on site-to-site connections,
    visit https://docs.microsoft.com/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-cli.
    For more information on Vnet-to-Vnet connections, visit https://docs.microsoft.com/azure/vpn-gateway/vpn-gateway-howto-vnet-vnet-cli
"""

helps['network vpn-connection create'] = """
type: command
short-summary: Create a VPN connection.
long-summary: The VPN Gateway and Local Network Gateway must be provisioned before creating the connection between them.
parameters:
  - name: --vnet-gateway1
    short-summary: Name or ID of the source virtual network gateway.
  - name: --vnet-gateway2
    short-summary: Name or ID of the destination virtual network gateway to connect to using a 'Vnet2Vnet' connection.
  - name: --local-gateway2
    short-summary: Name or ID of the destination local network gateway to connect to using an 'IPSec' connection.
  - name: --express-route-circuit2
    short-summary: Name or ID of the destination ExpressRoute to connect to using an 'ExpressRoute' connection.
  - name: --authorization-key
    short-summary: The authorization key for the VPN connection.
  - name: --enable-bgp
    short-summary: Enable BGP for this VPN connection.
  - name: --validate
    short-summary: Display and validate the ARM template but do not create any resources.
examples:
  - name: >
        Create a site-to-site connection between an Azure virtual network and an on-premises local network gateway.
    text: >
        az network vpn-connection create -g MyResourceGroup -n MyConnection --vnet-gateway1 MyVnetGateway --local-gateway2 MyLocalGateway --shared-key Abc123
  - name: Create a VPN connection with --ingress-nat-rule.
    text: |
        az network vpn-connection create -g MyResourceGroup -n MyConnection --vnet-gateway1 MyVnetGateway --local-gateway2 MyLocalGateway --shared-key Abc123 --ingress-nat-rule /subscriptions/000/resourceGroups/TestBGPRG1/providers/Microsoft.Network/virtualNetworkGateways/gwx/natRules/nat
    crafted: true
  - name: Create a VPN connection. (autogenerated)
    text: |
        az network vpn-connection create --location westus2 --name MyConnection --resource-group MyResourceGroup --shared-key Abc123 --vnet-gateway1 MyVnetGateway --vnet-gateway2 /subscriptions/{subscriptionID}/resourceGroups/TestBGPRG1/providers/Microsoft.Network/virtualNetworkGateways/VNet1GW
    crafted: true
  - name: Create a VPN connection. (autogenerated)
    text: |
        az network vpn-connection create --local-gateway2 MyLocalGateway --location westus2 --name MyConnection --resource-group MyResourceGroup --shared-key Abc123 --vnet-gateway1 MyVnetGateway
    crafted: true
"""

helps['network vpn-connection delete'] = """
type: command
short-summary: Delete a VPN connection.
examples:
  - name: Delete a VPN connection.
    text: az network vpn-connection delete -g MyResourceGroup -n MyConnection
"""

helps['network vpn-connection ipsec-policy'] = """
type: group
short-summary: Manage VPN connection IPSec policies.
"""

helps['network vpn-connection ipsec-policy add'] = """
type: command
short-summary: Add a VPN connection IPSec policy.
long-summary: Set all IPsec policies of a VPN connection. If you want to set any IPsec policy, you must set them all.
examples:
  - name: Add specified IPsec policies to a connection instead of relying on defaults.
    text: |
        az network vpn-connection ipsec-policy add -g MyResourceGroup --connection-name MyConnection \\
            --dh-group DHGroup14 --ike-encryption AES256 --ike-integrity SHA384 --ipsec-encryption DES3 \\
            --ipsec-integrity GCMAES256 --pfs-group PFS2048 --sa-lifetime 27000 --sa-max-size 102400000
"""

helps['network vpn-connection ipsec-policy clear'] = """
type: command
short-summary: Delete all IPsec policies on a VPN connection.
examples:
  - name: Remove all previously specified IPsec policies from a connection.
    text: az network vpn-connection ipsec-policy clear -g MyResourceGroup --connection-name MyConnection
"""

helps['network vpn-connection ipsec-policy list'] = """
type: command
short-summary: List IPSec policies associated with a VPN connection.
examples:
  - name: List the IPsec policies set on a connection.
    text: az network vpn-connection ipsec-policy list -g MyResourceGroup --connection-name MyConnection
"""

helps['network vpn-connection list'] = """
type: command
short-summary: List all VPN connections.
examples:
  - name: List all VPN connections in a resource group.
    text: az network vpn-connection list -g MyResourceGroup
  - name: List all VPN connections in a virtual network gateway.
    text: az network vpn-connection list -g MyResourceGroup --vnet-gateway MyVnetGateway
"""

helps['network vpn-connection list-ike-sas'] = """
type: command
short-summary: List IKE Security Associations for a VPN connection.
examples:
  - name: List IKE Security Associations for a VPN connection.
    text: az network vpn-connection list-ike-sas -g MyResourceGroup -n MyConnection
"""

helps['network vpn-connection shared-key'] = """
type: group
short-summary: Manage VPN shared keys.
"""

helps['network vpn-connection shared-key reset'] = """
type: command
short-summary: Reset a VPN connection shared key.
examples:
  - name: Reset the shared key on a connection.
    text: az network vpn-connection shared-key reset -g MyResourceGroup --connection-name MyConnection --key-length 128
  - name: Reset a VPN connection shared key. (autogenerated)
    text: |
        az network vpn-connection shared-key reset --connection-name MyConnection --key-length 128 --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network vpn-connection shared-key show'] = """
type: command
short-summary: Retrieve a VPN connection shared key.
examples:
  - name: View the shared key of a connection.
    text: az network vpn-connection shared-key show -g MyResourceGroup --connection-name MyConnection
  - name: Retrieve a VPN connection shared key. (autogenerated)
    text: |
        az network vpn-connection shared-key show --connection-name MyConnection --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['network vpn-connection shared-key update'] = """
type: command
short-summary: Update a VPN connection shared key.
examples:
  - name: Change the shared key for the connection to "Abc123".
    text: az network vpn-connection shared-key update -g MyResourceGroup --connection-name MyConnection --value Abc123
  - name: Update a VPN connection shared key. (autogenerated)
    text: |
        az network vpn-connection shared-key update --connection-name MyConnection --resource-group MyResourceGroup --subscription MySubscription --value Abc123
    crafted: true
"""

helps['network vpn-connection show'] = """
type: command
short-summary: Get the details of a VPN connection.
examples:
  - name: View the details of a VPN connection.
    text: az network vpn-connection show -g MyResourceGroup -n MyConnection
"""

helps['network vpn-connection update'] = """
type: command
short-summary: Update a VPN connection.
examples:
  - name: Add BGP to an existing connection.
    text: az network vpn-connection update -g MyResourceGroup -n MyConnection --enable-bgp True
  - name: Update a VPN connection. (autogenerated)
    text: |
        az network vpn-connection update --name MyConnection --resource-group MyResourceGroup --use-policy-based-traffic-selectors true
    crafted: true
"""

helps['network vpn-connection show-device-config-script'] = """
type: command
short-summary: Get a XML format representation for VPN connection device configuration script.
examples:
  - name: Get a XML format representation for VPN connection device configuration script.
    text: az network vpn-connection show-device-config-script -g MyResourceGroup -n MyConnection --vendor "Cisco" --device-family "Cisco-ISR(IOS)" --firmware-version "Cisco-ISR-15.x--IKEv2+BGP"
"""

helps['network vpn-connection packet-capture'] = """
type: group
short-summary: Manage packet capture on a VPN connection.
"""

helps['network vpn-connection packet-capture wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vpn connection packet capture is met.
"""

helps['network vpn-connection packet-capture start'] = """
type: command
short-summary: Start packet capture on a VPN connection.
examples:
  - name: Start packet capture on a VPN connection.
    text: az network vpn-connection packet-capture start -g MyResourceGroup -n MyConnection
"""

helps['network vpn-connection packet-capture stop'] = """
type: command
short-summary: Stop packet capture on a VPN connection.
examples:
  - name: Stop packet capture on a VPN connection.
    text: az network vpn-connection packet-capture stop -g MyResourceGroup -n MyConnection --sas-url https://myStorageAct.blob.azure.com/artifacts?st=2019-04-10T22%3A12Z&se=2019-04-11T09%3A12Z&sp=rl&sv=2018-03-28&sr=c&sig=0000000000
"""

helps['network vrouter'] = """
type: group
short-summary: Manage the virtual router. This feature supports both VirtualHub and VirtualRouter. Considering VirtualRouter is deprecated, we recommend to create VirtualRouter with --hosted-subnet instead
"""

helps['network vrouter create'] = """
type: command
short-summary: Create a virtual router.
"""

helps['network vrouter update'] = """
type: command
short-summary: Update a virtual router.
examples:
  - name: Update a virtual router. (autogenerated)
    text: |
        az network vrouter update --name myvirtualrouter --resource-group myresourcegroup --tags super_secure no_80 no_22
    crafted: true
"""

helps['network vrouter show'] = """
type: command
short-summary: Show a virtual router.
"""

helps['network vrouter list'] = """
type: command
short-summary: List all virtual routers under a subscription or a resource group.
"""

helps['network vrouter delete'] = """
type: command
short-summary: Delete a virtual router under a resource group.
"""

helps['network vrouter peering'] = """
type: group
short-summary: Manage the virtual router peering.
"""

helps['network vrouter peering create'] = """
type: command
short-summary: Create a virtual router peering.
"""

helps['network vrouter peering update'] = """
type: command
short-summary: Update a virtual router peering.
"""

helps['network vrouter peering list'] = """
type: command
short-summary: List all virtual router peerings under a resource group.
"""

helps['network vrouter peering show'] = """
type: command
short-summary: Show a virtual router peering
"""

helps['network vrouter peering delete'] = """
type: command
short-summary: Delete a virtual router peering.
"""

helps['network routeserver'] = """
type: group
short-summary: Manage the route server.
"""

helps['network routeserver create'] = """
type: command
short-summary: Create a route server.
examples:
  - name: Create a route server.
    text: |
      az network routeserver create --resource-group myresourcegroup --name myrouteserver --hosted-subnet my_subnet_id --public-ip-address my_public_ip
"""

helps['network routeserver update'] = """
type: command
short-summary: Update a route server.
examples:
  - name: Update a route server.
    text: |
        az network routeserver update --name myrouteserver --resource-group myresourcegroup --tags super_secure no_80 no_22
    crafted: true
"""

helps['network routeserver show'] = """
type: command
short-summary: Show a route server.
"""

helps['network routeserver list'] = """
type: command
short-summary: List all route servers under a subscription or a resource group.
"""

helps['network routeserver delete'] = """
type: command
short-summary: Delete a route server under a resource group.
"""

helps['network routeserver wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the route server is met.
"""

helps['network routeserver peering'] = """
type: group
short-summary: Manage the route server peering.
"""

helps['network routeserver peering create'] = """
type: command
short-summary: Create a route server peering.
"""

helps['network routeserver peering update'] = """
type: command
short-summary: Update a route server peering.
"""

helps['network routeserver peering list'] = """
type: command
short-summary: List all route server peerings under a resource group.
"""

helps['network routeserver peering show'] = """
type: command
short-summary: Show a route server peering
"""

helps['network routeserver peering delete'] = """
type: command
short-summary: Delete a route server peering.
"""

helps['network routeserver peering list-learned-routes'] = """
type: command
short-summary: List all routes the route server bgp connection has learned.
"""

helps['network routeserver peering list-advertised-routes'] = """
type: command
short-summary: List all routes the route server bgp connection is advertising to the specified peer.
"""

helps['network routeserver peering wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the route server peering is met.
"""

helps['network watcher'] = """
type: group
short-summary: Manage the Azure Network Watcher.
long-summary: >
    Network Watcher assists with monitoring and diagnosing conditions at a network scenario level. To learn more visit https://docs.microsoft.com/azure/network-watcher/
"""

helps['network watcher configure'] = """
type: command
short-summary: Configure the Network Watcher service for different regions.
parameters:
  - name: --enabled
    short-summary: Enabled status of Network Watcher in the specified regions.
  - name: --locations -l
    short-summary: Space-separated list of locations to configure.
  - name: --resource-group -g
    short-summary: Name of resource group. Required when enabling new regions.
    long-summary: >
        When a previously disabled region is enabled to use Network Watcher, a
            Network Watcher resource will be created in this resource group.
examples:
  - name: Configure Network Watcher for the West US region.
    text: az network watcher configure -g NetworkWatcherRG  -l westus --enabled true
"""

helps['network watcher connection-monitor'] = """
type: group
short-summary: Manage connection monitoring between an Azure Virtual Machine and any IP resource.
long-summary: >
    Connection monitor can be used to monitor network connectivity between an Azure virtual machine and an IP address.
     The IP address can be assigned to another Azure resource or a resource on the Internet or on-premises. To learn
     more visit https://aka.ms/connectionmonitordoc
"""

helps['network watcher connection-monitor create'] = """
type: command
short-summary: Create a connection monitor.
long-summary: |
  This extension allow to create V1 and V2 version of connection monitor.
  V1 connection monitor supports single source and destination endpoint which comes with V1 argument groups as usual.
  V2 connection monitor supports multiple endpoints and several test protocol which comes with V2 argument groups.
parameters:
  - name: --source-resource
    short-summary: >
        Currently only Virtual Machines are supported.
  - name: --dest-resource
    short-summary: >
        Currently only Virtual Machines are supported.
examples:
  - name: Create a connection monitor for a virtual machine.
    text: |
        az network watcher connection-monitor create -g MyResourceGroup -n MyConnectionMonitorName \\
            --source-resource MyVM
  - name: Create a V2 connection monitor
    text: >
      az network watcher connection-monitor create
      --name MyV2ConnectionMonitor
      --endpoint-source-name "vm01"
      --endpoint-source-resource-id MyVM01ResourceID
      --endpoint-dest-name bing
      --endpoint-dest-address bing.com
      --test-config-name TCPTestConfig
      --protocol Tcp
      --tcp-port 2048
  - name: Create a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor create --endpoint-dest-address bing.com --endpoint-dest-name bing --endpoint-source-name "vm01" --endpoint-source-resource-id MyVM01ResourceID --location westus2 --name MyConnectionMonitorName --protocol Tcp --tcp-port 2048 --test-config-name TCPTestConfig
    crafted: true
"""

helps['network watcher connection-monitor delete'] = """
type: command
short-summary: Delete a connection monitor for the given region.
examples:
  - name: Delete a connection monitor for the given region.
    text: az network watcher connection-monitor delete -l westus -n MyConnectionMonitorName
"""

helps['network watcher connection-monitor list'] = """
type: command
short-summary: List connection monitors for the given region.
examples:
  - name: List a connection monitor for the given region.
    text: az network watcher connection-monitor list -l westus
  - name: List connection monitors for the given region. (autogenerated)
    text: |
        az network watcher connection-monitor list --location westus --subscription MySubscription
    crafted: true
"""

helps['network watcher connection-monitor query'] = """
type: command
short-summary: Query a snapshot of the most recent connection state of a connection monitor.
examples:
  - name: List a connection monitor for the given region.
    text: az network watcher connection-monitor query -l westus -n MyConnectionMonitorName
"""

helps['network watcher connection-monitor show'] = """
type: command
short-summary: Shows a connection monitor by name.
examples:
  - name: Show a connection monitor for the given name.
    text: az network watcher connection-monitor show -l westus -n MyConnectionMonitorName
"""

helps['network watcher connection-monitor start'] = """
type: command
short-summary: Start the specified connection monitor.
examples:
  - name: Start the specified connection monitor.
    text: az network watcher connection-monitor start -l westus -n MyConnectionMonitorName
"""

helps['network watcher connection-monitor stop'] = """
type: command
short-summary: Stop the specified connection monitor.
examples:
  - name: Stop the specified connection monitor.
    text: az network watcher connection-monitor stop -l westus -n MyConnectionMonitorName
"""


helps['network watcher connection-monitor endpoint'] = """
type: group
short-summary: Manage endpoint of a connection monitor
"""

helps['network watcher connection-monitor endpoint add'] = """
type: command
short-summary: Add an endpoint to a connection monitor
examples:
  - name: Add an external address as a destination endpoint
    text: >
      az network watcher connection-monitor endpoint add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyExternalEndpoint
      --address "bing.com"
      --dest-test-groups DefaultTestGroup
      --type ExternalAddress
  - name: Add an Azure VM as a source endpoint
    text: >
      az network watcher connection-monitor endpoint add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyVMEndpoint
      --resource-id MyVMResourceID
      --source-test-groups DefaultTestGroup
      --type AzureVM
  - name: Add a Subnet as a source endpoint with addresses excluded
    text: >
      az network watcher connection-monitor endpoint add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MySubnetEndpoint
      --resource-id MySubnetID
      --source-test-groups DefaultTestGroup
      --type AzureSubnet
      --address-exclude 10.0.0.25 10.0.0.30
      --coverage-level BelowAverage
"""

helps['network watcher connection-monitor endpoint remove'] = """
type: command
short-summary: Remove an endpoint from a connection monitor
examples:
  - name: Remove endpoint from all test groups of a connection monitor
    text: >
      az network watcher connection-monitor endpoint remove
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyEndpoint
  - name: Remove endpoint from two test groups of a connection monitor
    text: >
      az network watcher connection-monitor endpoint remove
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyEndpoint
      --test-groups DefaultTestGroup HealthCheckTestGroup
"""

helps['network watcher connection-monitor endpoint show'] = """
type: command
short-summary: Show an endpoint from a connection monitor
examples:
  - name: Show an endpoint from a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor endpoint show --connection-monitor MyConnectionMonitor --location westus2 --name myconnectionmonitorendpoint --subscription MySubscription
    crafted: true
"""

helps['network watcher connection-monitor endpoint list'] = """
type: command
short-summary: List all endpoints form a connection monitor
examples:
  - name: List all endpoints form a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor endpoint list --connection-monitor MyConnectionMonitor --location westus2
    crafted: true
"""


helps['network watcher connection-monitor test-configuration'] = """
type: group
short-summary: Manage test configuration of a connection monitor
"""

helps['network watcher connection-monitor test-configuration add'] = """
type: command
short-summary: Add a test configuration to a connection monitor
examples:
  - name: Add a test configuration with HTTP supported
    text: >
      az network watcher connection-monitor test-configuration add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyHTTPTestConfiguration
      --test-groups DefaultTestGroup
      --protocol Http
      --http-request-header name=Host value=bing.com
      --http-request-header name=UserAgent value=Edge
  - name: Add a test configuration with TCP supported
    text: >
      az network watcher connection-monitor test-configuration add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyHTTPTestConfiguration
      --test-groups TCPTestGroup DefaultTestGroup
      --protocol Tcp
      --tcp-port 4096
"""

helps['network watcher connection-monitor test-configuration remove'] = """
type: command
short-summary: Remove a test configuration from a connection monitor
examples:
  - name: Remove a test configuration from all test groups of a connection monitor
    text: >
      az network watcher connection-monitor test-configuration remove
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyTCPTestConfiguration
  - name: Remove a test configuration from two test groups of a connection monitor
    text: >
      az network watcher connection-monitor test-configuration remove
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyHTTPTestConfiguration
      --test-groups HTTPTestGroup DefaultTestGroup
"""

helps['network watcher connection-monitor test-configuration show'] = """
type: command
short-summary: Show a test configuration from a connection monitor
examples:
  - name: Show a test configuration from a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor test-configuration show --connection-monitor MyConnectionMonitor --location westus2 --name MyConnectionMonitorTestConfiguration
    crafted: true
"""

helps['network watcher connection-monitor test-configuration list'] = """
type: command
short-summary: List all test configurations of a connection monitor
examples:
  - name: List all test configurations of a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor test-configuration list --connection-monitor MyConnectionMonitor --location westus2
    crafted: true
"""

helps['network watcher connection-monitor test-group'] = """
type: group
short-summary: Manage a test group of a connection monitor
"""

helps['network watcher connection-monitor test-group add'] = """
type: command
short-summary: Add a test group along with new-added/existing endpoint and test configuration to a connection monitor
examples:
  - name: Add a test group along with existing endpoint and test configuration via their names
    text: >
      az network watcher connection-monitor test-group add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyHTTPTestGroup
      --endpoint-source-name MySourceEndpoint
      --endpoint-dest-name MyDestinationEndpoint
      --test-config-name MyTestConfiguration
  - name: Add a test group long with new-added source endpoint and existing test configuration via its name
    text: >
      az network watcher connection-monitor test-group add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyAccessibilityTestGroup
      --endpoint-source-name MySourceEndpoint
      --endpoint-source-resource-id MyLogAnalysisWorkspaceID
      --endpoint-dest-name MyExistingDestinationEndpoint
      --test-config-name MyExistingTestConfiguration
  - name: Add a test group along with new-added endpoints and test configuration
    text: >
      az network watcher connection-monitor test-group add
      --connection-monitor MyConnectionMonitor
      --location westus
      --name MyAccessibilityTestGroup
      --endpoint-source-name MySourceEndpoint
      --endpoint-source-resource-id MyVMResourceID
      --endpoint-dest-name bing
      --endpoint-dest-address bing.com
      --test-config-name MyNewTestConfiguration
      --protocol Tcp
      --tcp-port 4096
"""

helps['network watcher connection-monitor test-group remove'] = """
type: command
short-summary: Remove test group from a connection monitor
examples:
  - name: Remove test group from a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor test-group remove --connection-monitor MyConnectionMonitor --location westus2 --name MyConnectionMonitorTestGroup
    crafted: true
"""

helps['network watcher connection-monitor test-group show'] = """
type: command
short-summary: Show a test group of a connection monitor
examples:
  - name: Show a test group of a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor test-group show --connection-monitor MyConnectionMonitor --location westus2 --name MyConnectionMonitorTestGroup --subscription MySubscription
    crafted: true
"""

helps['network watcher connection-monitor test-group list'] = """
type: command
short-summary: List all test groups of a connection monitor
examples:
  - name: List all test groups of a connection monitor. (autogenerated)
    text: |
        az network watcher connection-monitor test-group list --connection-monitor MyConnectionMonitor --location westus2
    crafted: true
"""

helps['network watcher connection-monitor output'] = """
type: group
short-summary: Manage output of connection monitor
"""

helps['network watcher connection-monitor output add'] = """
type: command
short-summary: Add an output to a connection monitor
"""

helps['network watcher connection-monitor output remove'] = """
type: command
short-summary: Remove all outputs from a connection monitor
"""

helps['network watcher connection-monitor output list'] = """
type: command
short-summary: List all output from a connection monitor
"""

helps['network watcher flow-log'] = """
type: group
short-summary: Manage network security group flow logging.
long-summary: >
    For more information about configuring flow logs visit https://docs.microsoft.com/azure/network-watcher/network-watcher-nsg-flow-logging-cli
"""

helps['network watcher flow-log configure'] = """
type: command
short-summary: Configure flow logging on a network security group.
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
  - name: Disable NSG flow logs.
    text: az network watcher flow-log configure -g MyResourceGroup --enabled false --nsg MyNsg
"""

helps['network watcher flow-log create'] = """
type: command
short-summary: Create a flow log on a network security group.
examples:
  - name: Create a flow log with Network Security Group name
    text: >
      az network watcher flow-log create
      --location westus
      --resource-group MyResourceGroup
      --name MyFlowLog
      --nsg MyNetworkSecurityGroupName
      --storage-account account
  - name: Create a flow log with Network Security Group ID (could be in other resource group)
    text: >
      az network watcher flow-log create
      --location westus
      --name MyFlowLog
      --nsg MyNetworkSecurityGroupID
      --storage-account account
"""

helps['network watcher flow-log list'] = """
type: command
short-summary: List all flow log resources for the specified Network Watcher
examples:
  - name: List all flow log resources for the specified Network Watcher. (autogenerated)
    text: |
        az network watcher flow-log list --location westus2
    crafted: true
"""

helps['network watcher flow-log delete'] = """
type: command
short-summary: Delete the specified flow log resource.
examples:
  - name: Delete the specified flow log resource. (autogenerated)
    text: |
        az network watcher flow-log delete --location westus2 --name MyFlowLogger
    crafted: true
"""

helps['network watcher flow-log show'] = """
type: command
short-summary: Get the flow log configuration of a network security group.
examples:
  - name: Show NSG flow logs. (Deprecated)
    text: az network watcher flow-log show -g MyResourceGroup --nsg MyNsg
  - name: Show NSG flow logs with Azure Resource Management formatted.
    text: az network watcher flow-log show --location MyNetworkWatcher --name MyFlowLog
"""

helps['network watcher flow-log update'] = """
type: command
short-summary: Update the flow log configuration of a network security group
examples:
  - name: Update storage account with name to let resource group identify the storage account and network watcher
    text: >
      az network watcher flow-log update
      --location westus
      --resource-group MyResourceGroup
      --name MyFlowLog
      --storage-account accountname
  - name: Update storage account with ID to let location identify the network watcher
    text: >
      az network watcher flow-log update
      --location westus
      --resource-group MyResourceGroup
      --name MyFlowLog
      --storage-account accountid
  - name: Update Network Security Group on another resource group
    text: >
      az network watcher flow-log update
      --location westus
      --resource-group MyAnotherResourceGroup
      --name MyFlowLog
      --nsg MyNSG
  - name: Update Workspace on another resource group
    text: >
      az network watcher flow-log update
      --location westus
      --resource-group MyAnotherResourceGroup
      --name MyFlowLog
      --workspace MyAnotherLogAnalyticWorkspace
"""

helps['network watcher list'] = """
type: command
short-summary: List Network Watchers.
examples:
  - name: List all Network Watchers in a subscription.
    text: az network watcher list
"""

helps['network watcher packet-capture'] = """
type: group
short-summary: Manage packet capture sessions on VMs.
long-summary: >
    These commands require that both Azure Network Watcher is enabled for the VMs region and that AzureNetworkWatcherExtension is enabled on the VM.
    For more information visit https://docs.microsoft.com/azure/network-watcher/network-watcher-packet-capture-manage-cli
"""

helps['network watcher packet-capture create'] = """
type: command
short-summary: Create and start a packet capture session.
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
    short-summary: JSON encoded list of packet filters. Use `@{path}` to load from file.
examples:
  - name: Create a packet capture session on a VM.
    text: az network watcher packet-capture create -g MyResourceGroup -n MyPacketCaptureName --vm MyVm --storage-account MyStorageAccount
  - name: Create a packet capture session on a VM with optional filters for protocols, local IP address and remote IP address ranges and ports.
    text: |
        az network watcher packet-capture create -g MyResourceGroup -n MyPacketCaptureName --vm MyVm \\
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
short-summary: Delete a packet capture session.
examples:
  - name: Delete a packet capture session. This only deletes the session and not the capture file.
    text: az network watcher packet-capture delete -n packetCaptureName -l westcentralus
  - name: Delete a packet capture session. (autogenerated)
    text: |
        az network watcher packet-capture delete --location westcentralus --name packetCaptureName --subscription MySubscription
    crafted: true
"""

helps['network watcher packet-capture list'] = """
type: command
short-summary: List all packet capture sessions within a resource group.
examples:
  - name: List all packet capture sessions within a region.
    text: az network watcher packet-capture list -l westus
  - name: List all packet capture sessions within a resource group (autogenerated)
    text: |
        az network watcher packet-capture list --location westus --subscription MySubscription
    crafted: true
"""

helps['network watcher packet-capture show'] = """
type: command
short-summary: Show details of a packet capture session.
examples:
  - name: Show a packet capture session.
    text: az network watcher packet-capture show -l westus -n MyPacketCapture
"""

helps['network watcher packet-capture show-status'] = """
type: command
short-summary: Show the status of a packet capture session.
examples:
  - name: Show the status of a packet capture session.
    text: az network watcher packet-capture show-status -l westus -n MyPacketCapture
"""

helps['network watcher packet-capture stop'] = """
type: command
short-summary: Stop a running packet capture session.
examples:
  - name: Stop a running packet capture session.
    text: az network watcher packet-capture stop -l westus -n MyPacketCapture
"""

helps['network watcher run-configuration-diagnostic'] = """
type: command
short-summary: Run a configuration diagnostic on a target resource.
long-summary: >
    Requires that Network Watcher is enabled for the region in which the target is located.
examples:
  - name: Run configuration diagnostic on a VM with a single query.
    text: |
        az network watcher run-configuration-diagnostic --resource {VM_ID}
           --direction Inbound --protocol TCP --source 12.11.12.14 --destination 10.1.1.4 --port 12100
  - name: Run configuration diagnostic on a VM with multiple queries.
    text: |
        az network watcher run-configuration-diagnostic --resource {VM_ID}
            --queries '[
            {
                "direction": "Inbound", "protocol": "TCP", "source": "12.11.12.14",
                "destination": "10.1.1.4", "destinationPort": "12100"
            },
            {
                "direction": "Inbound", "protocol": "TCP", "source": "12.11.12.0/32",
                "destination": "10.1.1.4", "destinationPort": "12100"
            },
            {
                "direction": "Outbound", "protocol": "TCP", "source": "12.11.12.14",
                "destination": "10.1.1.4", "destinationPort": "12100"
            }]'
"""

helps['network watcher show-next-hop'] = """
type: command
short-summary: Get information on the 'next hop' of a VM.
long-summary: >
    Requires that Network Watcher is enabled for the region in which the VM is located.
    For more information about show-next-hop visit https://docs.microsoft.com/azure/network-watcher/network-watcher-check-next-hop-cli
examples:
  - name: Get the next hop from a VMs assigned IP address to a destination at 10.1.0.4.
    text: az network watcher show-next-hop -g MyResourceGroup --vm MyVm --source-ip 10.0.0.4 --dest-ip 10.1.0.4
"""

helps['network watcher show-security-group-view'] = """
type: command
short-summary: Get detailed security information on a VM for the currently configured network security group.
long-summary: >
    For more information on using security group view visit https://docs.microsoft.com/azure/network-watcher/network-watcher-security-group-view-cli
examples:
  - name: Get the network security group information for the specified VM.
    text: az network watcher show-security-group-view -g MyResourceGroup --vm MyVm
"""

helps['network watcher show-topology'] = """
type: command
short-summary: Get the network topology of a resource group, virtual network or subnet.
long-summary: For more information about using network topology visit https://docs.microsoft.com/azure/network-watcher/network-watcher-topology-cli
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
    text: az network watcher show-topology -g MyResourceGroup
"""

helps['network watcher test-connectivity'] = """
type: command
short-summary: Test if a connection can be established between a Virtual Machine and a given endpoint.
long-summary: >
    To check connectivity between two VMs in different regions, use the VM ids instead of the VM names for the source and destination resource arguments.
    To register for this feature or see additional examples visit https://docs.microsoft.com/azure/network-watcher/network-watcher-connectivity-cli
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
    text: az network watcher test-connectivity --source-resource MyVmId1 --dest-resource MyVmId2 --dest-port 80
"""

helps['network watcher test-ip-flow'] = """
type: command
short-summary: Test IP flow to/from a VM given the currently configured network security group rules.
long-summary: >
    Requires that Network Watcher is enabled for the region in which the VM is located.
    For more information visit https://docs.microsoft.com/azure/network-watcher/network-watcher-check-ip-flow-verify-cli
parameters:
  - name: --local
    short-summary: >
        The private IPv4 address for the VMs NIC and the port of the packet in
        X.X.X.X:PORT format. `*` can be used for port when direction is outbound.
  - name: --remote
    short-summary: >
        The IPv4 address and port for the remote side of the packet
        X.X.X.X:PORT format. `*` can be used for port when the direction is inbound.
  - name: --direction
    short-summary: Direction of the packet relative to the VM.
  - name: --protocol
    short-summary: Protocol to test.
examples:
  - name: Run test-ip-flow verify to test logical connectivity from a VM to the specified destination IPv4 address and port.
    text: |
        az network watcher test-ip-flow -g MyResourceGroup --direction Outbound \\
            --protocol TCP --local 10.0.0.4:* --remote 10.1.0.4:80 --vm MyVm
"""

helps['network watcher troubleshooting'] = """
type: group
short-summary: Manage Network Watcher troubleshooting sessions.
long-summary: >
    For more information on configuring troubleshooting visit https://docs.microsoft.com/azure/network-watcher/network-watcher-troubleshoot-manage-cli
"""

helps['network watcher troubleshooting show'] = """
type: command
short-summary: Get the results of the last troubleshooting operation.
examples:
  - name: Show the results or status of a troubleshooting operation for a Vnet Gateway.
    text: az network watcher troubleshooting show -g MyResourceGroup --resource MyVnetGateway --resource-type vnetGateway
"""

helps['network watcher troubleshooting start'] = """
type: command
short-summary: Troubleshoot issues with VPN connections or gateway connectivity.
parameters:
  - name: --resource-type -t
    short-summary: The type of target resource to troubleshoot, if resource ID is not specified.
  - name: --storage-account
    short-summary: Name or ID of the storage account in which to store the troubleshooting results.
  - name: --storage-path
    short-summary: Fully qualified URI to the storage blob container in which to store the troubleshooting results.
examples:
  - name: Start a troubleshooting operation on a VPN Connection.
    text: |
        az network watcher troubleshooting start -g MyResourceGroup --resource MyVPNConnection \\
            --resource-type vpnConnection --storage-account MyStorageAccount \\
            --storage-path https://{storageAccountName}.blob.core.windows.net/{containerName}
"""

helps['network list-service-aliases'] = """
type: command
short-summary: List available service aliases in the region which can be used for Service Endpoint Policies.
examples:
  - name: List available service aliases in the region which can be used for Service Endpoint Policies. (autogenerated)
    text: |
        az network list-service-aliases --location westus2
    crafted: true
"""

helps['network bastion'] = """
type: group
short-summary: Manage Azure Bastion host.
"""

helps['network bastion create'] = """
type: command
short-summary: Create a Azure Bastion host machine.
examples:
  - name: Create a Azure Bastion host machine. (autogenerated)
    text: |
        az network bastion create --location westus2 --name MyBastionHost --public-ip-address MyPublicIpAddress --resource-group MyResourceGroup --vnet-name MyVnet
    crafted: true
"""

helps['network bastion delete'] = """
type: command
short-summary: Delete a Azure Bastion host machine.
examples:
  - name: Delete a Azure Bastion host machine. (autogenerated)
    text: |
        az network bastion delete --name MyBastionHost --resource-group MyResourceGroup
    crafted: true
"""

helps['network bastion list'] = """
type: command
short-summary: List all Azure Bastion host machines.
"""

helps['network bastion show'] = """
type: command
short-summary: Show a Azure Bastion host machine.
examples:
  - name: Show a Azure Bastion host machine.
    text: |
        az network bastion show --name MyBastionHost --resource-group MyResourceGroup
    crafted: true
"""

helps['network bastion ssh'] = """
type: command
short-summary: SSH to a virtual machine using Tunneling from Azure Bastion.
examples:
  - name: SSH to virtual machine using Azure Bastion using password.
    text: |
        az network bastion ssh --name MyBastionHost --resource-group MyResourceGroup --target-resource-id vmResourceId --auth-type password --username xyz
  - name: SSH to virtual machine using Azure Bastion using ssh key file.
    text: |
        az network bastion ssh --name MyBastionHost --resource-group MyResourceGroup --target-resource-id vmResourceId --auth-type ssh-key --username xyz --ssh-key C:/filepath/sshkey.pem
  - name: SSH to virtual machine using Azure Bastion using AAD.
    text: |
        az network bastion ssh --name MyBastionHost --resource-group MyResourceGroup --target-resource-id vmResourceId --auth-type AAD
"""

helps['network bastion rdp'] = """
type: command
short-summary: RDP to target Virtual Machine using Tunneling from Azure Bastion.
examples:
  - name: RDP to virtual machine using Azure Bastion.
    text: |
        az network bastion rdp --name MyBastionHost --resource-group MyResourceGroup --target-resource-id vmResourceId
"""

helps['network bastion tunnel'] = """
type: command
short-summary: Open a tunnel through Azure Bastion to a target virtual machine.
examples:
  - name: Open a tunnel through Azure Bastion to a target virtual machine.
    text: |
        az network bastion tunnel --name MyBastionHost --resource-group MyResourceGroup --target-resource-id vmResourceId --resource-port 22 --port 50022
"""

helps['network security-partner-provider'] = """
type: group
short-summary: Manage Azure security partner provider.
"""

helps['network security-partner-provider create'] = """
type: command
short-summary: Create a Azure security partner provider.
"""

helps['network security-partner-provider update'] = """
type: command
short-summary: Update a Azure security partner provider.
"""

helps['network security-partner-provider delete'] = """
type: command
short-summary: Delete a Azure security partner provider.
"""

helps['network security-partner-provider list'] = """
type: command
short-summary: List all Azure security partner provider.
"""

helps['network security-partner-provider show'] = """
type: command
short-summary: Show a Azure security partner provider.
"""

helps['network virtual-appliance'] = """
type: group
short-summary: Manage Azure Network Virtual Appliance.
"""

helps['network virtual-appliance create'] = """
type: command
short-summary: Create an Azure network virtual appliance.
examples:
  - name: Create an Azure network virtual appliance.
    text: |
        az network virtual-appliance create -n MyName -g MyRG --vhub {vhubID} --vendor "barracudasdwanrelease" --scale-unit 2 -v latest --asn 10000 --init-config "echo $hello" --boot-blobs {blobUrl1} {blobUrl2} --cloud-blobs {blobUrl3} {blobUrl4}
"""

helps['network virtual-appliance update'] = """
type: command
short-summary: Update an Azure network virtual appliance.
examples:
  - name: Update an Azure network virtual appliance.
    text: |
        az network virtual-appliance update -n MyName -g MyRG --asn 20000 --init-config "echo $hello"
"""

helps['network virtual-appliance show'] = """
type: command
short-summary: Show the detail of an Azure network virtual appliance.
"""

helps['network virtual-appliance list'] = """
type: command
short-summary: List all Azure network virtual appliance.
"""

helps['network virtual-appliance delete'] = """
type: command
short-summary: Delete an Azure network virtual appliance.
"""

helps['network virtual-appliance site'] = """
type: group
short-summary: Manage Azure Network Virtual Appliance Site.
"""

helps['network virtual-appliance site create'] = """
type: command
short-summary: Create an Azure network virtual appliance site.
examples:
  - name: Create an Azure network virtual appliance site.
    text: |
        az network virtual-appliance site create -n MyName -g MyRG --appliance-name MyAppliance --address-prefix 10.0.0.0/24 --allow --default --optimize
"""

helps['network virtual-appliance site update'] = """
type: command
short-summary: Update an Azure network virtual appliance site.
examples:
  - name: Update an Azure network virtual appliance site.
    text: |
        az network virtual-appliance site update -n MyName -g MyRG --appliance-name MyAppliance --address-prefix 10.0.0.0/24 --allow false --default false --optimize false
"""

helps['network virtual-appliance site show'] = """
type: command
short-summary: Show the detail of an Azure network virtual appliance site.
"""

helps['network virtual-appliance site list'] = """
type: command
short-summary: List all Azure network virtual appliance site.
"""

helps['network virtual-appliance site delete'] = """
type: command
short-summary: Delete an Azure network virtual appliance site.
"""

helps['network virtual-appliance sku'] = """
type: group
short-summary: Manage Azure Network Virtual Appliance Sku.
"""

helps['network virtual-appliance sku show'] = """
type: command
short-summary: Show the detail of an Azure network virtual appliance sku.
"""

helps['network virtual-appliance sku list'] = """
type: command
short-summary: List all Azure network virtual appliance sku.
"""
