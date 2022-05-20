# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['cdn'] = """
type: group
short-summary: Manage Azure Content Delivery Networks (CDNs).
"""

helps['cdn custom-domain'] = """
type: group
short-summary: Manage Azure CDN Custom Domains to provide custom host names for endpoints.
"""

helps['cdn custom-domain create'] = """
type: command
short-summary: Create a new custom domain to provide a hostname for a CDN endpoint.
long-summary: >
    Creates a new custom domain which must point to the hostname of the endpoint.
    For example, the custom domain hostname cdn.contoso.com would need to have a
    CNAME record pointing to the hostname of the endpoint related to this custom
    domain.
parameters:
  - name: --profile-name
    type: string
    short-summary: Name of the CDN profile which is unique within the resource group.
  - name: --endpoint-name
    type: string
    short-summary: Name of the endpoint under the profile which is unique globally.
  - name: --hostname
    type: string
    short-summary: The host name of the custom domain. Must be a domain name.
examples:
  - name: Create a custom domain with resource name customdomain1 within an endpoint and profile.
    text: >
        az cdn custom-domain create -g group --endpoint-name endpoint --profile-name profile
        -n customdomain1 --hostname www.example.com
"""

helps['cdn custom-domain delete'] = """
type: command
short-summary: Delete the custom domain of a CDN.
examples:
  - name: Delete a custom domain with resource name customdomain1.
    text: >
        az cdn custom-domain delete -g group --endpoint-name endpoint --profile-name profile
        -n customdomain1
"""

helps['cdn custom-domain show'] = """
type: command
short-summary: Show details for the custom domain of a CDN.
examples:
  - name: Get the details of a custom domain with resource name customdomain1.
    text: >
        az cdn custom-domain show -g group --endpoint-name endpoint --profile-name profile
        -n customdomain1
"""

helps['cdn custom-domain enable-https'] = """
type: command
short-summary: Enable HTTPS for a custom domain. The resource name of the custom domain could be obtained using "az cdn custom-domain list".
examples:
  - name: Enable HTTPS for custom domain with resource name customdomain1 using a CDN-managed certificate
    text: >
        az cdn custom-domain enable-https -g group --profile-name profile --endpoint-name endpoint
        -n customdomain1
  - name: Enable HTTPS for custom domain with resource name customdomain1 using a CDN-managed certificate and set the minimum TLS version to 1.2
    text: >
        az cdn custom-domain enable-https -g group --profile-name profile --endpoint-name endpoint
        -n customdomain1 --min-tls-version 1.2
"""

helps['cdn edge-node'] = """
type: group
short-summary: View all available CDN edge nodes.
"""

helps['cdn name-exists'] = """
type: command
short-summary: Check the availability of a resource name.
               This is needed for resources where name is globally unique, such as a CDN endpoint.
examples:
  - name: Check whether the resource name contoso is available or not.
    text: >
        az cdn name-exists --name contoso
"""

helps['cdn endpoint'] = """
type: group
short-summary: Manage CDN endpoints.
"""

helps['cdn endpoint create'] = """
type: command
short-summary: Create a named endpoint to connect to a CDN.
examples:
  - name: Create an endpoint to service content for hostname over HTTP or HTTPS.
    text: >
        az cdn endpoint create -g group -n endpoint --profile-name profile
        --origin www.example.com
  - name: Create an endpoint with a custom domain origin with HTTP and HTTPS ports.
    text: >
        az cdn endpoint create -g group -n endpoint --profile-name profile
        --origin www.example.com 88 4444
  - name: Create an endpoint with a custom domain origin with private link enabled.
    text: >
        az cdn endpoint create -g group -n endpoint --profile-name profile
        --origin www.example.com 80 443
        /subscriptions/subid/resourcegroups/rg1/providers/Microsoft.Network/privateLinkServices/pls1
        eastus "Please approve this request"
  - name: Create an https-only endpoint with a custom domain origin and support compression for Azure CDN's default compression MIME types.
    text: >
        az cdn endpoint create -g group -n endpoint --profile-name profile
        --origin www.example.com --no-http --enable-compression
  - name: Create an endpoint with a custom domain origin and support compression for specific MIME types.
    text: >
        az cdn endpoint create -g group -n endpoint --profile-name profile
        --origin www.example.com --enable-compression --content-types-to-compress text/plain text/html
"""

helps['cdn endpoint delete'] = """
type: command
short-summary: Delete a CDN endpoint.
examples:
  - name: Delete a CDN endpoint.
    text: az cdn endpoint delete -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint list'] = """
type: command
short-summary: List available endpoints for a CDN.
examples:
  - name: List all endpoints within a given CDN profile.
    text: >
        az cdn endpoint list -g group --profile-name profile-name
"""

helps['cdn endpoint load'] = """
type: command
short-summary: Pre-load content for a CDN endpoint.
parameters:
  - name: --content-paths
    type: string
    short-summary: The path to the content to be loaded. Path should be a relative
                   file URL of the origin.
examples:
  - name: Pre-load Javascript and CSS content for an endpoint.
    text: >
        az cdn endpoint load -g group -n endpoint --profile-name profile-name --content-paths
        '/scripts/app.js' '/styles/main.css'
"""

helps['cdn endpoint purge'] = """
type: command
short-summary: Purge pre-loaded content for a CDN endpoint.
parameters:
  - name: --content-paths
    type: string
    short-summary: The path to the content to be purged. Can describe a file path or a
                   wildcard directory.
examples:
  - name: Purge pre-loaded Javascript and CSS content.
    text: >
        az cdn endpoint purge -g group -n endpoint --profile-name profile-name --content-paths
        '/scripts/app.js' '/styles/*'
"""

helps['cdn endpoint validate-custom-domain'] = """
type: command
short-summary: Validates the custom domain mapping to ensure it maps to the correct CDN endpoint in DNS.
parameters:
  - name: --host-name
    type: string
    short-summary: The host name of the custom domain. Must be a domain name.
examples:
  - name: Validate domain www.contoso.com to see whether it maps to the correct CDN endpoint in DNS.
    text: >
        az cdn endpoint validate-custom-domain -g group -n endpoint --profile-name profile-name --host-name www.contoso.com
"""

helps['cdn endpoint start'] = """
type: command
short-summary: Start a CDN endpoint.
examples:
  - name: Start a CDN endpoint.
    text: >
        az cdn endpoint start -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint stop'] = """
type: command
short-summary: Stop a CDN endpoint.
examples:
  - name: Stop a CDN endpoint.
    text: >
        az cdn endpoint stop -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint update'] = """
type: command
short-summary: Update a CDN endpoint to manage how content is delivered.
parameters:
  - name: --default-origin-group
    type: string
    short-summary: >
        The origin group to use for origins not explicitly included in an origin group. Can be
        specified as a resource ID or the name of an origin group of this endpoint.
examples:
  - name: Turn off HTTP traffic for an endpoint.
    text: >
        az cdn endpoint update -g group -n endpoint --profile-name profile --no-http
  - name: Enable content compression for an endpoint.
    text: >
        az cdn endpoint update -g group -n endpoint --profile-name profile
        --enable-compression
"""

helps['cdn endpoint rule'] = """
type: group
short-summary: Manage delivery rules for an endpoint.
"""

helps['cdn endpoint rule add'] = """
type: command
short-summary: Add a delivery rule to a CDN endpoint.
parameters:
  - name: --rule-name
    type: string
    short-summary: >
        Name of the rule, only required for Microsoft SKU.
examples:
  - name: Create a global rule to disable caching.
    text: >
        az cdn endpoint rule add -g group -n endpoint --profile-name profile --order 0
        --rule-name global --action-name CacheExpiration --cache-behavior BypassCache
  - name: Create a rule for http to https redirect.
    text: >
        az cdn endpoint rule add -g group -n endpoint --profile-name profile --order 1
        --rule-name "redirect" --match-variable RequestScheme --operator Equal --match-values HTTP
        --action-name "UrlRedirect" --redirect-protocol Https --redirect-type Moved
  - name: Create a rule to distribute requests with "/test1" in its URL path to origin group with name "origingroup1".
    text: >
        az cdn endpoint rule add -g group -n endpoint --profile-name profile --order 1
        --rule-name "origin-groupo-verride" --match-variable UrlPath --operator Contains --match-values /test1
        --action-name "OriginGroupOverride" --origin-group origingroup1
"""

helps['cdn endpoint rule remove'] = """
type: command
short-summary: Remove a delivery rule from an endpoint.
examples:
  - name: Remove the global rule.
    text: >
        az cdn endpoint rule remove -g group -n endpoint --profile-name profile --rule-name Global
  - name: Remove the rule with the order 4.
    text: >
        az cdn endpoint rule remove -g group -n endpoint --profile-name profile --order 4
"""

helps['cdn endpoint rule show'] = """
type: command
short-summary: Show delivery rules asscociate with the endpoint.
examples:
  - name: show delivery rules asscociate with the endpoint.
    text: >
        az cdn endpoint rule show -g group -n endpoint --profile-name profile
"""

helps['cdn endpoint rule condition'] = """
type: group
short-summary: Manage delivery rule conditions for an endpoint.
"""

helps['cdn endpoint rule condition add'] = """
type: command
short-summary: Add a condition to a delivery rule.
examples:
  - name: Add a remote address condition.
    text: >
        az cdn endpoint rule condition add -g group -n endpoint --profile-name profile --rule-name name
        --match-variable RemoteAddress --operator GeoMatch --match-values "TH"
"""

helps['cdn endpoint rule condition remove'] = """
type: command
short-summary: Remove a condition from a delivery rule.
examples:
  - name: Remove the first condition.
    text: >
        az cdn endpoint rule condition remove -g group -n endpoint --profile-name profile --rule-name name
        --index 0
"""

helps['cdn endpoint rule condition show'] = """
type: command
short-summary: show delivery rules asscociate with the endpoint.
examples:
  - name: show delivery rules asscociate with the endpoint.
    text: >
        az cdn endpoint rule condition show -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint rule action'] = """
type: group
short-summary: Manage delivery rule actions for an endpoint.
"""

helps['cdn endpoint rule action add'] = """
type: command
short-summary: Add an action to a delivery rule.
examples:
  - name: Add a redirect action.
    text: >
        az cdn endpoint rule action add -g group -n endpoint --profile-name profile --rule-name name
        --action-name "UrlRedirect" --redirect-protocol HTTPS --redirect-type Moved
  - name: Add a cache expiration action
    text: >
        az cdn endpoint rule action add -g group -n endpoint --profile-name profile --rule-name name
        --action-name "CacheExpiration" --cache-behavior BypassCache
"""

helps['cdn endpoint rule action remove'] = """
type: command
short-summary: Remove an action from a delivery rule.
examples:
  - name: Remove the first action.
    text: >
        az cdn endpoint rule action remove -g group -n endpoint --profile-name profile --rule-name name
        --index 0
"""

helps['cdn endpoint rule action show'] = """
type: command
short-summary: show delivery rules asscociate with the endpoint.
examples:
  - name: show delivery rules asscociate with the endpoint.
    text: >
        az cdn endpoint rule action show -g group --profile-name profile-name -n endpoint
"""

helps['cdn endpoint waf'] = """
type: group
short-summary: Manage WAF properties of a CDN endpoint.
"""

helps['cdn endpoint waf policy'] = """
type: group
short-summary: Apply a CDN WAF policy to a CDN endpoint.
"""

helps['cdn endpoint waf policy set'] = """
type: command
short-summary: Set the CDN WAF policy applied to a CDN endpoint
parameters:
  - name: --waf-policy-id
    type: string
    short-summary: >
        The Resource ID of the CDN WAF policy to apply to this endpoint.
  - name: --waf-policy-subscription-id
    type: string
    short-summary: >
        The Resource ID of the CDN WAF policy to apply to this endpoint. ignored
        if --waf-policy-id is set.
  - name: --waf-policy-resource-group-name
    type: string
    short-summary: >
        The resource group of the CDN WAF policy to apply to this endpoint.
        Ignored if --waf-policy-id is set.
  - name: --waf-policy-name
    type: string
    short-summary: >
        The name of the CDN WAF policy to apply to this endpoint. Ignored if
        --waf-policy-id is set.
examples:
  - name: Set the CDN WAF policy applied to a CDN endpoint by WAF Policy name.
    text: >
        az cdn endpoint waf policy set -g group --endpoint-name endpoint
        --profile-name profile --waf-policy-subscription-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
"""

helps['cdn endpoint waf policy remove'] = """
type: command
short-summary: Remove a CDN WAF policy from a CDN endpoint.
examples:
  - name: Remove a CDN WAF policy from a CDN endpoint.
    text: >
        az cdn endpoint waf policy remove -g group --endpoint-name endpoint --profile-name profile
"""

helps['cdn endpoint waf policy show'] = """
type: command
short-summary: Show which CDN WAF policy is applied to a CDN endpoint.
examples:
  - name: Show which CDN WAF policy is applied to a CDN endpoint.
    text: >
        az cdn endpoint waf policy show -g group --endpoint-name endpoint --profile-name profile
"""

helps['cdn origin'] = """
type: group
short-summary: List or show existing origins related to CDN endpoints.
"""

helps['cdn origin create'] = """
type: command
short-summary: Create an origin.
parameters:
  - name: --host-name
    type: string
    short-summary: >
        The host name where requests to the origin will be sent.
  - name: --http-port
    type: int
    short-summary: >
        The port used for http requests to the origin.
  - name: --https-port
    type: int
    short-summary: >
        The port used for https requests to the origin.
  - name: --origin-host-header
    type: string
    short-summary: >
        The Host header to send for requests to this origin.
  - name: --weight
    type: int
    short-summary: >
        The weight of the origin in given origin group for load balancing. Must be between 1 and 1000.
  - name: --priority
    type: int
    short-summary: >
        The load balancing priority. Higher priorities will not be used for load
        balancing if any lower priority origin is healthy. Must be between 1 and 5.
  - name: --disabled
    type: bool
    short-summary: >
        Don't use the origin for load balancing.
  - name: --private-link-resource-id -p
    type: string
    short-summary: >
        The resource id of the private link that the origin will be connected to.
  - name: --private-link-location -l
    type: string
    short-summary: >
        The location of the private link that the origin will be connected to.
  - name: --private-link-approval-message -m
    type: string
    short-summary: >
        The message that is shown to the approver of the private link request.
examples:
  - name: Create an additional origin
    text: >
      az cdn origin create -g group --host-name example.contoso.com --profile-name profile --endpoint-name endpoint
      -n origin --host-name example.contoso.com --origin-host-header example.contoso.com
      --http-port 80 --https-port 443
  - name: Create a private origin
    text: >
      az cdn origin create -g group --host-name example.contoso.com --profile-name profile --endpoint-name endpoint
      -n origin --http-port 80 --https-port 443 --private-link-resource-id
      /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/group/providers/Microsoft.Network/privateLinkServices/pls
      --private-link-location EastUS --private-link-approval-message 'Please approve this request'
"""

helps['cdn origin update'] = """
type: command
short-summary: Update an origin.
parameters:
  - name: --host-name
    type: string
    short-summary: >
        The host name where requests to the origin will be sent.
  - name: --http-port
    type: int
    short-summary: >
        The port used for http requests to the origin.
  - name: --https-port
    type: int
    short-summary: >
        The port used for https requests to the origin.
  - name: --origin-host-header
    type: string
    short-summary: >
        The Host header to send for requests to this origin.
  - name: --weight
    type: int
    short-summary: >
        The weight of the origin in given origin group for load balancing. Must be between 1 and 1000.
  - name: --priority
    type: int
    short-summary: >
        The load balancing priority. Higher priorities will not be used for load
        balancing if any lower priority origin is healthy. Must be between 1 and 5.
  - name: --disabled
    type: bool
    short-summary: >
        Don't use the origin for load balancing.
  - name: --private-link-resource-id -p

    type: string
    short-summary: >
        The resource id of the private link that the origin will be connected to.
  - name: --private-link-location -l
    type: string
    short-summary: >
        The location of the private link that the origin will be connected to.
  - name: --private-link-approval-message -m
    type: string
    short-summary: >
        The message that is shown to the approver of the private link request.
examples:
  - name: Update an origin
    text: >
      az cdn origin update -g group --profile-name profile --endpoint-name endpoint -n origin --http-port 80
      --https-port 443 --priority 3 --weight 500 --host-name example.contoso.com
  - name: Disable an origin
    text: >
      az cdn origin update -g group --profile-name profile --endpoint-name endpoint -n origin --disabled
  - name: Connect an origin to a private link service
    text: >
      az cdn origin update -g group --profile-name profile --endpoint-name endpoint -n origin --http-port 80
      --https-port 443 --private-link-resource-id
      /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/group/providers/Microsoft.Network/privateLinkServices/pls
      --private-link-location EastUS --private-link-approval-message 'Please approve this request'
"""

helps['cdn origin-group'] = """
type: group
short-summary: Manage origin groups of an endpoint.
"""

helps['cdn origin-group create'] = """
type: command
short-summary: Create an origin group.
parameters:
  - name: --origins
    type: int
    short-summary: >
        The origins load balanced by this origin group, as a comma-separated list of origin names or
        origin resource IDs.
  - name: --probe-interval
    type: int
    short-summary: >
        The frequency to perform health probes in seconds.
  - name: --probe-path
    type: str
    short-summary: >
        The path relative to the origin that is used to determine the health of the origin.
  - name: --probe-protocol
    type: string
    short-summary: >
        The protocol to use for health probes.
  - name: --probe-method
    type: string
    short-summary: >
        The request method to use for health probes.
  # Uncomment this once response error detection support is added in RP:
  # - name: --response-error-detection-error-types
  #   type: string
  #   short-summary: >
  #       The type of response errors for real user requests for which the origin will be deemed unhealthy.
  # - name: --response-error-detection-failover-threshold
  #   type: int
  #   short-summary: >
  #       The threshold of failed requests required to trigger failover as a percent of 100.
  # - name: --response-error-detection-status-code-ranges
  #   type: string
  #   short-summary: >
  #       The HTTP response status codes to count toward the response error detection failover threshold, specified
  #       as a comma-separated list of ranges.
examples:
  - name: Create an origin group
    text: >
      az cdn origin-group create -g group --profile-name profile --endpoint-name endpoint -n origin-group
      --origins origin-0,origin-1
  - name: Create an origin group with a custom health probe
    text: >
      az cdn origin-group create -g group --profile-name profile --endpoint-name endpoint -n origin-group
      --origins origin-0,origin-1 --probe-path /healthz --probe-interval 90
      --probe-protocol HTTPS --probe-method GET
  # Uncomment this once response error detection support is added in RP:
  # - name: Create an origin group with response error detection
  #   text: >
  #     az cdn origin-group create -g group --profile-name profile --endpoint-name endpoint -n origin-group
  #     --origins origin-0,origin-1 --response-error-detection-error-types TcpErrorsOnly
  #     --response-error-detection-failover-threshold 5
  #     --response-error-detection-status-code-ranges 300-399,500-599
"""

helps['cdn origin-group update'] = """
type: command
short-summary: Update an origin group.
parameters:
  - name: --origins
    type: int
    short-summary: >
        The origins load balanced by this origin group, as a comma-separated list of origin names from the
        parent endpoint origin IDs.
  - name: --probe-interval
    type: int
    short-summary: >
        The frequency to perform health probes in seconds.
  - name: --probe-path
    type: str
    short-summary: >
        The path relative to the origin that is used to determine the health of the origin.
  - name: --probe-protocol
    type: string
    short-summary: >
        The protocol to use for health probes.
  - name: --probe-method
    type: string
    short-summary: >
        The request method to use for health probes.
  # Uncomment this once response error detection support is added in RP:
  # - name: --response-error-detection-error-types
  #   type: string
  #   short-summary: >
  #       The type of response errors for real user requests for which the origin will be deemed unhealthy.
  # - name: --response-error-detection-failover-threshold
  #   type: int
  #   short-summary: >
  #       The threshold of failed requests required to trigger failover as a percent of 100.
  # - name: --response-error-detection-status-code-ranges
  #   type: string
  #   short-summary: >
  #       The HTTP response status codes to count toward the response error detection failover threshold.
examples:
  - name: Update which origins are included in an origin group.
    text: >
      az cdn origin-group update -g group --profile-name profile --endpoint-name endpoint -n origin-group
      --origins origin-0,origin-2
  - name: Update an origin group with a custom health probe
    text: >
      az cdn origin-group update -g group --profile-name profile --endpoint-name endpoint -n origin-group
      --origins origin-0,origin-1 --probe-path /healthz --probe-interval 90
      --probe-protocol HTTPS --probe-method GET
  # Uncomment this once response error detection support is added in RP:
  # - name: Update an origin group with response error detection
  #   text: >
  #     az cdn origin-group update -g group --profile-name profile --endpoint-name endpoint -n origin-group
  #     --origins origin-0,origin-1 --response-error-detection-error-types TcpErrorsOnly
  #     --response-error-detection-failover-threshold 5
  #     --response-error-detection-status-code-ranges 300-399,500-599
"""

helps['cdn profile'] = """
type: group
short-summary: Manage CDN profiles to define an edge network.
"""

helps['cdn profile create'] = """
type: command
short-summary: Create a new CDN profile.
parameters:
  - name: --sku
    type: string
    short-summary: >
        The pricing tier (defines a CDN provider, feature list and rate) of the CDN profile.
        Defaults to Standard_Akamai.
examples:
  - name: Create a CDN profile using Verizon premium CDN.
    text: >
        az cdn profile create -g group -n profile --sku Premium_Verizon
  - name: Create a new CDN profile. (autogenerated)
    text: az cdn profile create --location westus2 --name profile --resource-group group --sku Standard_Verizon
    crafted: true
"""

helps['cdn profile delete'] = """
type: command
short-summary: Delete a CDN profile.
examples:
  - name: Delete a CDN profile.
    text: >
        az cdn profile delete -g group -n profile
"""

helps['cdn profile list'] = """
type: command
short-summary: List CDN profiles.
examples:
  - name: List CDN profiles in a resource group.
    text: >
        az cdn profile list -g group
"""

helps['cdn profile show'] = """
type: command
short-summary: Show CDN profile details.
examples:
  - name: Show CDN profile details.
    text: >
        az cdn profile show -g group -n profile
"""

helps['cdn profile update'] = """
type: command
short-summary: Update a CDN profile.
examples:
  - name: Update a CDN profile. (autogenerated)
    text: az cdn profile update --name MyCDNProfileWhichIsUniqueWithinResourceGroup --resource-group MyResourceGroup
    crafted: true
"""

helps['cdn waf'] = """
type: group
short-summary: Manage CDN WAF.
long-summary: >
    WAF on Azure CDN from Microsoft is currently in public preview and is provided with a preview service level agreement.
    Certain features may not be supported or may have constrained capabilities.
    See the Supplemental Terms of Use for Microsoft Azure Previews (https://azure.microsoft.com/en-us/support/legal/preview-supplemental-terms/) for details.
"""

helps['cdn waf policy'] = """
type: group
short-summary: Manage CDN WAF policies.
"""

helps['cdn waf policy set'] = """
type: command
short-summary: Create a new CDN WAF policy.
parameters:
  - name: --sku
    type: string
    short-summary: >
        The pricing tier (defines a CDN provider, feature list and rate) of the CDN WAF policy.
  - name: --mode
    type: string
    short-summary: The operation mode of the policy. Valid options are 'Detection' and 'Prevention'.
  - name: --block-response-body
    type: string
    short-summary: The response body to send when a request is blocked, provided as a Base64 encoded string.
  - name: --block-response-status-code
    type: int
    short-summary: The response status code to send when a request is blocked.
  - name: --redirect-url
    type: string
    short-summary: The URL to use when redirecting a request.
  - name: --disabled
    type: bool
    short-summary: Disable the policy.
examples:
  - name: Create a CDN WAF policy in detection mode.
    text: >
        az cdn waf policy set -g group -n policy
  - name: Create a CDN WAF policy in with a custom block response status code.
    text: >
        az cdn waf policy set -g group -n policy --mode Prevention --block-response-status-code 200
"""

helps['cdn waf policy delete'] = """
type: command
short-summary: Delete a CDN WAF policy.
examples:
  - name: Delete a CDN policy.
    text: >
        az cdn waf policy delete -g group -n policy
"""

helps['cdn waf policy list'] = """
type: command
short-summary: List CDN WAF policies.
examples:
  - name: List CDN WAF policies in a resource group.
    text: >
        az cdn waf policy list -g group
"""

helps['cdn waf policy show'] = """
type: command
short-summary: Show details of a CDN WAF policy.
examples:
  - name: Get the details of a CDN WAF policy.
    text: az cdn waf policy show -g group -n policy
"""

helps['cdn waf policy managed-rule-set'] = """
type: group
short-summary: Manage managed rule sets of a CDN WAF policy.
"""

helps['cdn waf policy managed-rule-set add'] = """
type: command
short-summary: Add a managed rule set to a CDN WAF policy.
examples:
  - name: Add DefaultRuleSet_1.0 to a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set add -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy managed-rule-set remove'] = """
type: command
short-summary: Remove a managed rule set from a CDN WAF policy.
examples:
  - name: Remove DefaultRuleSet_1.0 from a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set remove -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy managed-rule-set list'] = """
type: command
short-summary: List managed rule sets added to a CDN WAF policy.
examples:
  - name: List managed rule sets added to a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set list -g group --policy-name policy
"""

helps['cdn waf policy managed-rule-set show'] = """
type: command
short-summary: Show a managed rule of a CDN WAF policy.
examples:
  - name: Get a managed rule set of a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set show -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy managed-rule-set list-available'] = """
type: command
short-summary: List available CDN WAF managed rule sets.
examples:
  - name: List all available CDN WAF managed rule sets.
    text: az cdn waf policy managed-rule-set list-available
"""

helps['cdn waf policy managed-rule-set rule-group-override'] = """
type: group
short-summary: Manage rule group overrides of a managed rule on a CDN WAF policy.
"""

helps['cdn waf policy managed-rule-set rule-group-override set'] = """
type: command
short-summary: Add or update a rule group override to a managed rule set on a CDN WAF policy.
parameters:
  - name: --rule-override -r
    short-summary: Override a rule in the rule group.
    long-summary: >
        rule overrides are specified as key value pairs in the form "KEY=VALUE [KEY=VALUE ...]".
        Available keys are 'id', 'action', and 'enabled'. 'id' is required. Valid values for
        'action' are 'Block', 'Redirect', 'Allow', and 'Log', defaulting to 'Block'. Valid values
        for 'enabled' are 'Enabled' and 'Disabled', defaulting to 'Disabled'.
examples:
  - name: Add a rule group override for SQL injections to DefaultRuleSet_1.0 on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override set -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI -r
        id=942440 action=Redirect enabled=Enabled
  - name: Add multiple rule group overrides to DefaultRuleSet_1.0 on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override set -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI
        -r id=942440 action=Redirect enabled=Enabled
        -r id=942120 -r id=942100
"""

helps['cdn waf policy managed-rule-set rule-group-override delete'] = """
type: command
short-summary: Remove a rule group override from a managed rule set on a CDN WAF policy.
examples:
  - name: Remove the rule group override for SQLI from DefaultRuleSet_1.0 on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override delete -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI
"""

helps['cdn waf policy managed-rule-set rule-group-override list'] = """
type: command
short-summary: List rule group overrides of a managed rule on a CDN WAF policy.
examples:
  - name: List rule group overrides of a managed rule on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override list -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy managed-rule-set rule-group-override show'] = """
type: command
short-summary: Show a rule group override of a managed rule on a CDN WAF policy.
examples:
  - name: Get the rule group override for rule group SQLI of DefaultRuleSet_1.0 on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override show -g group --policy-name policy
        --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI
"""

helps['cdn waf policy managed-rule-set rule-group-override list-available'] = """
type: command
short-summary: List available CDN WAF managed rule groups of a managed rule set.
examples:
  - name: List available rule groups for DefaultRuleSet_1.0.
    text: >
      az cdn waf policy managed-rule-set rule-group-override list-available
      --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy custom-rule'] = """
type: group
short-summary: Manage custom rules of a CDN WAF policy.
"""

helps['cdn waf policy custom-rule set'] = """
type: command
short-summary: Add a custom rule to a CDN WAF policy.
parameters:
  - name: --action
    type: string
    short-summary: >
        The action to take when the rule is matched.
  - name: --match-condition -m
    type: string
    short-summary: Conditions used to determine if the rule is matched for a request.
    long-summary: >
        Match conditions are specified as key value pairs in the form "KEY=VALUE [KEY=VALUE ...]".
        Available keys are 'match-variable', 'operator', 'match-value', 'selector', 'negate', and
        'transform'. 'match-variable', 'operator', and 'match-value' are required. 'match-value'
        and 'transform' may be specified multiple times per match condition.

        Valid values for 'match-variable' are 'RemoteAddr', 'SocketAddr', 'RequestMethod',
        'RequestHeader', 'RequestUri', 'QueryString', 'RequestBody', 'Cookies', and 'PostArgs'.
        Valid values for 'operator' are 'Any', 'IPMatch', 'GeoMatch', 'Equal', 'Contains',
        'LessThan', 'GreaterThan', 'LessThanOrEqual', 'GreaterThanOrEqual', 'BeginsWith',
        'EndsWith', and 'RegEx'. Valid values for 'transform' are 'Lowercase', 'Uppercase',
        'Trim', 'UrlDecode', 'UrlEncode', and 'RemoveNulls'. Valid values for 'negate' are 'True'
        and 'False', and 'negate' defaults to 'False'.
  - name: --priority
    type: int
    short-summary: The priority of the custom rule as a non-negative integer.
  - name: --disabled
    type: bool
    short-summary: Disable the custom rule
examples:
  - name: Create or update a rule that blocks requests unless method is GET or POST.
    text: >
        az cdn waf policy custom-rule set -g group --policy-name policy -n customrule
        --action Block --priority 100 --match-condition
        match-variable=RequestMethod operator=Equal negate=true match-value=GET match-value=HEAD
  - name: Create or update a custom rule with multiple match conditions and whitespace in a match value.
    text: >
        az cdn waf policy custom-rule set -g group --policy-name policy -n customrule
        --action Redirect --priority 100
        -m match-variable=RequestUri operator=Contains match-value=..
        -m match-variable=QueryString operator=Contains "match-value= "
"""

helps['cdn waf policy custom-rule delete'] = """
type: command
short-summary: Remove a custom rule from a CDN WAF policy.
examples:
  - name: Remove a custom rule from a CDN WAF policy.
    text: >
        az cdn waf policy custom-rule delete -g group --policy-name policy -n customrule
"""

helps['cdn waf policy custom-rule list'] = """
type: command
short-summary: List custom rules of a CDN WAF policy.
examples:
  - name: List custom rules of a CDN WAF policy.
    text: >
        az cdn waf policy custom-rule list -g group --policy-name policy
"""

helps['cdn waf policy custom-rule show'] = """
type: command
short-summary: Show a custom rule of a CDN WAF policy.
examples:
  - name: Get a custom rule of a CDN WAF policy.
    text: >
        az cdn waf policy custom-rule show -g group --policy-name policy -n customrule
"""


helps['cdn waf policy rate-limit-rule'] = """
type: group
short-summary: Manage rate limit rules of a CDN WAF policy.
"""

helps['cdn waf policy rate-limit-rule set'] = """
type: command
short-summary: Add a rate limit rule to a CDN WAF policy.
parameters:
  - name: --action
    type: string
    short-summary: >
        The action to take when the rule is matched.
  - name: --match-condition -m
    type: string
    short-summary: Conditions used to determine if the rule is matched for a request.
    long-summary: >
        Match conditions are specified as key value pairs in the form "KEY=VALUE [KEY=VALUE ...]".
        Available keys are 'match-variable', 'operator', 'match-value', 'selector', 'negate', and
        'transform'. 'match-variable', 'operator', and 'match-value' are required. 'match-value' and
        'transform' may be specified multiple times per match condition.
  - name: --priority
    type: int
    short-summary: The priority of the rate limit rule as a non-negative integer.
  - name: --disabled
    type: bool
    short-summary: Disable the rate limit rule
  - name: --duration
    type: int
    short-summary: The duration of the rate limit in minutes. Valid values are 1 and 5.
  - name: --request-threshold
    type: int
    short-summary: The request threshold to trigger rate limiting.
examples:
  - name: Create or update a rule that rate limits requests unless method is GET or POST.
    text: >
        az cdn waf policy rate-limit-rule set -g group --policy-name policy
        -n ratelimitrule --action Block --priority 100 --duration 1 --request-threshold 100
        -m match-variable=RequestMethod operator=Equal negate=true match-value=GET match-value=HEAD
  - name: Create or update a rate limit rule with multiple match conditions.
    text: >
        az cdn waf policy rate-limit-rule set -g group --policy-name policy
        -n ratelimitrule --action Redirect --priority 200 --duration 5 --request-threshold 100
        -m match-variable=RequestMethod operator=Equal match-value=PUT
        -m match-variable=RequestUri operator=Contains match-value=/expensive/resource/
"""

helps['cdn waf policy rate-limit-rule delete'] = """
type: command
short-summary: Remove a rate limit rule from a CDN WAF policy.
examples:
  - name: Remove a rate limit rule from a CDN WAF policy.
    text: >
        az cdn waf policy rate-limit-rule delete -g group --policy-name policy -n ratelimitrule
"""

helps['cdn waf policy rate-limit-rule list'] = """
type: command
short-summary: List rate limit rules of a CDN WAF policy.
examples:
  - name: List rate limit rules of a CDN WAF policy.
    text: >
        az cdn waf policy rate-limit-rule list -g group --policy-name policy
"""

helps['cdn waf policy rate-limit-rule show'] = """
type: command
short-summary: Show a rate limit rule of a CDN WAF policy.
examples:
  - name: Get a rate limit rule of a CDN WAF policy.
    text: >
        az cdn waf policy rate-limit-rule show -g group --policy-name policy -n ratelimitrule
"""

helps['afd'] = """
type: group
short-summary: Manage Azure Front Door Standard/Premium. For classical Azure Front Door, please refer https://docs.microsoft.com/en-us/cli/azure/network/front-door?view=azure-cli-latest
"""

helps['afd profile'] = """
type: group
short-summary: Manage AFD profiles.
"""

helps['afd profile create'] = """
type: command
short-summary: Create a new AFD profile.
examples:
  - name: Create an AFD profile using Standard SKU.
    text: >
        az afd profile create -g group --profile-name profile --sku Standard_AzureFrontDoor
"""

helps['afd profile delete'] = """
type: command
short-summary: Delete an AFD profile.
examples:
  - name: Delete an AFD profile.
    text: >
        az afd profile delete -g group --profile-name profile
"""

helps['afd profile usage'] = """
type: command
short-summary: List resource usage within the specific AFD profile.
examples:
  - name: List resource usage within the specific AFD profile.
    text: >
        az afd profile usage -g group --profile-name profile
"""

helps['afd profile show'] = """
type: command
short-summary: Show details of an AFD profile.
examples:
  - name: Show details of an AFD profile.
    text: >
        az afd profile show -g group --profile-name profile
"""

helps['afd profile list'] = """
type: command
short-summary: List AFD profiles.
examples:
  - name: List AFD profiles in a resource group.
    text: >
        az afd profile list -g group
"""

helps['afd profile update'] = """
type: command
short-summary: Update an AFD profile.
examples:
  - name: Update an AFD profile with tags.
    text: az afd profile update --profile-name profile --resource-group MyResourceGroup --tags tag1=value1
"""

helps['afd origin-group'] = """
type: group
short-summary: Manage origin groups under the specified profile.
long-summary: >
    An origin group is a set of origins to which Front Door load balances your client requests.
"""

helps['afd origin-group create'] = """
type: command
short-summary: Creates a new origin group within the specified profile.
examples:
  - name: Creates a new origin group within the specified profile.
    text: >
        az afd origin-group create -g group --origin-group-name og1 --profile-name profile
        --probe-request-type GET --probe-protocol Http --probe-interval-in-seconds 120 --probe-path /test1/azure.txt
        --sample-size 4 --successful-samples-required 3
        --additional-latency-in-milliseconds 50
"""

helps['afd origin-group update'] = """
type: command
short-summary: Creates a new origin group within the specified profile.
examples:
  - name: Update the probe setting of the specified origin group.
    text: >
        az afd origin-group update -g group --origin-group-name og1 --profile-name profile
        --probe-request-type HEAD --probe-protocol Https --probe-interval-in-seconds 120 --probe-path /test1/azure.txt
"""

helps['afd origin-group delete'] = """
type: command
short-summary: Deletes an existing origin group within the specified profile.
examples:
  - name: Deletes an existing origin group within a profile.
    text: >
        az afd origin-group delete -g group --origin-group-name og1 --profile-name profile
"""

helps['afd origin'] = """
type: group
short-summary: Manage origins within the specified origin group.
long-summary: >
    Origins are the application servers where Front Door will route your client requests.
    Utilize any publicly accessible application server, including App Service, Traffic Manager, Private Link, and many others.
"""

helps['afd origin create'] = """
type: command
short-summary: Create an AFD origin.
examples:
  - name: Create an regular origin
    text: >
      az afd origin create -g group --host-name example.contoso.com --profile-name profile --origin-group-name originGroup
      --origin-name origin1 --origin-host-header example.contoso.com --priority 1 --weight 500 --enabled-state Enabled
      --http-port 80 --https-port 443
  - name: Create a private link origin
    text: >
      az afd origin create -g group --host-name example.contoso.com --profile-name profile --origin-group-name originGroup
      --origin-name origin1 --origin-host-header example.contoso.com --priority 1 --weight 500 --enabled-state Enabled
      --http-port 80 --https-port 443 --private-link-resource
      /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/group/providers/Microsoft.Storage/storageAccounts/plstest
      --private-link-location EastUS --private-link-request-message 'Please approve this request' --private-link-sub-resource table
"""

helps['afd origin update'] = """
type: command
short-summary: Update the settings of the specified AFD origin.
examples:
  - name: Update the host header and priority of the specified origin.
    text: >
      az afd origin update -g group --host-name example.contoso.com --profile-name profile --origin-group-name originGroup
      --origin-name origin1 --origin-host-header example.contoso.com --priority 3
  - name: Disable private link of the origin.
    text: >
      az afd origin update -g group --host-name example.contoso.com --profile-name profile --origin-group-name originGroup
      --origin-name origin1 --enable-private-link False
"""

helps['afd custom-domain'] = """
type: group
short-summary: Manage custom domains within the specified profile.
"""

helps['afd custom-domain create'] = """
type: command
short-summary: Create a custom domain within the specified profile.
long-summary: >
    The operation will complete with a created custom domain with its validation state set to 'Pending.
    You have to create a DNS TXT record "_dnsauth.<your_custom_domain>" with the validation token as its value to make the domain's validation state become 'Approved' to server traffic.
    Use "az afd custom-domain show" to obtain the validation token.
    The validation token will expire after 7 days and your domain's validation state will become "Timeout" if no correct TXT record detected in that period.
    You could use 'az afd custom-domain regenerate-validation-token' to regenerate the validation token to restart the validation process.
examples:
  - name: Create a custom domain that uses AFD managed cerficate for SSL/TLS encryption.
    text: >
        az afd custom-domain create -g group --custom-domain-name customDomain --profile-name profile --host-name www.contoso.com
        --minimum-tls-version TLS12 --certificate-type ManagedCertificate
  - name: Create a custom domain that uses your own cerficate for SSL/TLS encryption, the certificate is stored in Azure Key Vault and referenced by an AFD secret.
    text: >
        az afd custom-domain create -g group --custom-domain-name customDomain --profile-name profile --host-name www.contoso.com
        --minimum-tls-version TLS12 --certificate-type CustomerCertificate --secret secretName
"""

helps['afd custom-domain update'] = """
type: command
short-summary: Update a custom domain within the specified profile.
examples:
  - name: Update the custom domain's supported minimum TLS version.
    text: >
        az afd custom-domain update -g group --custom-domain-name customDomain --profile-name profile --minimum-tls-version TLS12
  - name: Update the custom domain's certificate type to AFD managed certificate.
    text: >
        az afd custom-domain update -g group --custom-domain-name customDomain --profile-name profile --certificate-type ManagedCertificate
"""

helps['afd custom-domain delete'] = """
type: command
short-summary: Delete a custom domain.
examples:
  - name: Delete a custom domain.
    text: >
        az afd custom-domain delete -g group --profile-name profile  --custom-domain-name customDomainName
"""

helps['afd custom-domain show'] = """
type: command
short-summary: Show the custom domain details.
examples:
  - name: show details of the custom domain within the specified profile.
    text: >
        az afd custom-domain show -g group --profile-name profile  --custom-domain-name customDomainName
"""

helps['afd custom-domain list'] = """
type: command
short-summary: List all the custom domains within the specified profile.
examples:
  - name: List all the custom domains within the specified profile.
    text: >
        az afd custom-domain list -g group --profile-name profile
"""

helps['afd custom-domain wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the custom domain is met.
examples:
  - name: Wait until a custom domain is created.
    text: az afd custom-domain wait -g MyResourceGroup --profile-name MyProfle --custom-domain-name MyCustomDomain --created
"""

helps['afd custom-domain regenerate-validation-token'] = """
type: command
short-summary: Regenerate the domain validation token to restart the validation process.
examples:
  - name: Regenerate the domain validation token.
    text: az afd custom-domain regenerate-validation-token -g MyResourceGroup --profile-name MyProfle --custom-domain-name MyCustomDomain
"""

helps['afd endpoint'] = """
type: group
short-summary: Manage AFD endpoints within the specified profile.
long-summary: >
    An endpoint is a logical grouping of domains and their associated configurations.
"""

helps['afd endpoint create'] = """
type: command
short-summary: Creates an endpoint within the specified profile.
long-summary: >
    Azure Front Door will generate a deterministic DNS domain based on the customer input endpoint name in the form of <endpoint name>-<hash>.z01.azurefd.net,
    the deterministic DNS domain could be reused within the tenant, subscription, or resource group depends on the --name-reuse-scope option.
    Customer will get the same DNS domain in the reuse scope if the endpoint get deleted and recreated.
examples:
  - name: Creates an enabled endpoint
    text: >
        az afd endpoint create -g group --endpoint-name endpoint1 --profile-name profile --enabled-state Enabled
"""

helps['afd endpoint update'] = """
type: command
short-summary: Update an endpoint within the specified profile.
examples:
  - name: Update an endpoint's state to disabled.
    text: >
        az afd endpoint update -g group --endpoint-name endpoint1 --profile-name profile --enabled-state Disabled
"""

helps['afd endpoint delete'] = """
type: command
short-summary: Delete an endpoint within the specified profile.
examples:
  - name: Delete an endpoint named endpoint1.
    text: >
        az afd endpoint delete -g group --profile-name profile --endpoint-name endpoint1
"""

helps['afd endpoint show'] = """
type: command
short-summary: Show details of an endpoint within the specified profile.
examples:
  - name: show details of the endpoint named endpoint1.
    text: >
        az afd endpoint show -g group --profile-name profile  --endpoint-name endpoint1
"""

helps['afd endpoint list'] = """
type: command
short-summary: List all the endpoints within the specified profile.
examples:
  - name: List all the endpoints within the specified profile.
    text: >
        az afd endpoint list -g group --profile-name profile
"""

helps['afd endpoint purge'] = """
type: command
short-summary: Removes cached contents from Azure Front Door.
examples:
  - name: Remove all cached cotents under directory "/script" for domain www.contoso.com
    text: >
        az afd endpoint purge -g group --profile-name profile --domains www.contoso.com --content-paths '/scripts/*'
"""

helps['afd route'] = """
type: group
short-summary: Manage routes under an AFD endpoint.
long-summary: >
    A route maps your domains and matching URL path patterns to a specific origin group.
"""

helps['afd route create'] = """
type: command
short-summary: Creates a new route within the specified endpoint.
examples:
  - name: Creates a route to assoicate the endpoint's default domain with an origin group for all HTTPS requests.
    text: >
        az afd route create -g group --endpoint-name endpoint1 --profile-name profile --route-name route1 --https-redirect False
        --origin-group og001 --supported-protocols Https --link-to-default-domain Enabled --forwarding-protocol MatchRequest
  - name: Creates a route to assoicate the endpoint's default domain with an origin group for all requests and use the specified rule sets to customize the route behavior.
    text: >
        az afd route create -g group --endpoint-name endpoint1 --profile-name profile --route-name route1 --rule-sets ruleset1 rulseset2
        --origin-group og001 --supported-protocols Http Https --link-to-default-domain Enabled --forwarding-protocol MatchRequest --https-redirect False
  - name: Creates a route to assoicate the endpoint's default domain and a custom domain with an origin group for all requests with the specified path patterns and redirect all trafic to use Https.
    text: >
        az afd route create -g group --endpoint-name endpoint1 --profile-name profile --route-name route1 --patterns-to-match /test1/* /tes2/*
        --origin-group og001 --supported-protocols Http Https --custom-domains cd001 --forwarding-protocol MatchRequest --https-redirect True --link-to-default-domain Enabled
"""

helps['afd route update'] = """
type: command
short-summary: Update an existing route within the specified endpoint.
examples:
  - name: Update a route to accept both Http and Https requests and redirect all trafic to use Https.
    text: >
        az afd route update -g group --endpoint-name endpoint1 --profile-name profile --route-name route1
        --supported-protocols Http Https --https-redirect True
  - name: Update a route's rule sets settings to customize the route behavior.
    text: >
        az afd route update -g group --endpoint-name endpoint1 --profile-name profile --route-name route1 --rule-sets ruleset1 rulseset2
  - name: Update a route's compression settings to enable compression for the specified content types.
    text: >
        az afd route update -g group --endpoint-name endpoint1 --profile-name profile --route-name route1 --query-string-caching-behavior IgnoreQueryString
        --enable-compression true --content-types-to-compress text/javascript text/plain
"""

helps['afd security-policy'] = """
type: group
short-summary: Manage security policies within the specified profile.
long-summary: >
    Security policies could be used to apply a web application firewall policy to protect your web applications against OWASP top-10 vulnerabilities and
    block malicious bots.
"""

helps['afd security-policy create'] = """
type: command
short-summary: Creates a new security policy within the specified profile.
examples:
  - name: Creates a security policy to apply the specified WAF policy to an endpoint's default domain and a custom domain.
    text: >
        az afd security-policy create -g group --profile-name profile --security-policy-name sp1 --domains
        /subscriptions/sub1/resourcegroups/rg1/providers/Microsoft.Cdn/profiles/profile1/afdEndpoints/endpoint1
        /subscriptions/sub1/resourcegroups/rg1/providers/Microsoft.Cdn/profiles/profile1/customDomains/customDomain1
        --waf-policy
        /subscriptions/sub1/resourcegroups/rg1/providers/Microsoft.Network/frontdoorwebapplicationfirewallpolicies/waf1
"""

helps['afd security-policy update'] = """
type: command
short-summary: Update an existing security policy within the specified profile.
examples:
  - name: Update the specified security policy's domain list.
    text: >
        az afd security-policy update -g group --security-policy-name sp1 --profile-name profile --domains
        /subscriptions/sub1/resourcegroups/rg1/providers/Microsoft.Cdn/profiles/profile1/customDomains/customDomain1
"""

helps['afd route delete'] = """
type: command
short-summary: Delete an existing route within the specified endpoint.
examples:
  - name: Delete an route named route1.
    text: >
        az afd route delete -g group --profile-name profile --endpoint-name endpoint1 --route-name route1
"""

helps['afd secret'] = """
type: group
short-summary: Manage secrets within the specified profile.
long-summary: >
    Secrets are used to reference your own certificate stored in Azure Key Vault.
    You must specifiy the secret name when creating custom domain if you want to use your own certificate for TLS encryption.
"""

helps['afd secret create'] = """
type: command
short-summary: Creates a new secret within the specified profile.
examples:
  - name: Creates a secret using the specified certificate version.
    text: >
        az afd secret create -g group --profile-name profile --secret-name secret1 --secret-version version1
        --secret-source /subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.KeyVault/vaults/vault1/secrets/cert1
"""

helps['afd secret update'] = """
type: command
short-summary: Update an existing secret within the specified profile.
examples:
  - name: Update the specified secret to use the certificate's latest version.
    text: >
        az afd secret update -g group --profile-name profile --secret-name secret1 --use-latest-version
"""

helps['afd route delete'] = """
type: command
short-summary: Delete an existing route within the specified endpoint.
examples:
  - name: Delete a route named route1.
    text: >
        az afd route delete -g group --profile-name profile --endpoint-name endpoint1 --route-name route1
"""

helps['afd route show'] = """
type: command
short-summary: Show route details.
examples:
  - name: show details of the route named route1.
    text: >
        az afd route show -g group --profile-name profile  --endpoint-name endpoint1 --route-name route1
"""

helps['afd route list'] = """
type: command
short-summary: List all the routes within the specified endpoint.
examples:
  - name: List all the routes within the specified endpoint.
    text: >
        az afd route list -g group --profile-name profile --endpoint-name endpoint1
"""

helps['afd rule-set'] = """
type: group
short-summary: Manage rule set for the specified profile.
long-summary: >
    Rules Set allows you to customize how HTTP requests are handled at the edge and provides more controls of the behaviors of your web application.
"""

helps['afd rule-set create'] = """
type: command
short-summary: Creates a new rule set under the specified profile.
examples:
  - name: Create a new rule set under the specified profile.
    text: >
        az afd rule-set create -g group --rule-set-name ruleset1 --profile-name profile
"""

helps['afd rule-set delete'] = """
type: command
short-summary: Delete the rule set.
examples:
  - name: Delete a rule set with the name ruleset1.
    text: >
        az afd rule-set delete -g group --rule-set-name ruleset1 --profile-name profile
"""

helps['afd rule'] = """
type: group
short-summary: Manage delivery rules within the specified rule set.
"""

helps['afd rule create'] = """
type: command
short-summary: Creates a new delivery rule within the specified rule set.
examples:
  - name: Create a rule to append a response header for requests from Thailand.
    text: >
        az afd rule create -g group --rule-set-name ruleset1 --profile-name profile --order 2 --match-variable RemoteAddress --operator GeoMatch --match-values TH
        --rule-name disablecahing --action-name ModifyResponseHeader --header-action Append --header-name X-CDN --header-value AFDX
  - name: Create a rule for http to https redirect
    text: >
        az afd rule create -g group --rule-set-name ruleset1 --profile-name profile --order 1
        --rule-name "redirect" --match-variable RequestScheme --operator Equal --match-values HTTP
        --action-name "UrlRedirect" --redirect-protocol Https --redirect-type Moved
"""

helps['afd rule delete'] = """
type: command
short-summary: Remove a delivery rule from rule set.
examples:
  - name: Remove a rule with name rule1.
    text: >
        az afd rule delete -g group --rule-set-name ruleSetName --profile-name profile --rule-name rule1
"""

helps['afd rule show'] = """
type: command
short-summary: Show delivery rule details.
examples:
  - name: show details of the delivery rule with name rule1.
    text: >
        az afd rule show -g group --rule-set-name ruleSetName --profile-name profile --rule-name rule1
"""

helps['afd rule condition'] = """
type: group
short-summary: Manage delivery rule conditions for a rule.
"""

helps['afd rule condition add'] = """
type: command
short-summary: Add a condition to a delivery rule.
examples:
  - name: Add a remote address condition.
    text: >
        az afd rule condition add -g group --rule-set-name ruleSetName --profile-name profile --rule-name name
        --match-variable RemoteAddress --operator GeoMatch --match-values "TH"
"""

helps['afd rule condition remove'] = """
type: command
short-summary: Remove a condition from a delivery rule.
examples:
  - name: Remove the first condition.
    text: >
        az afd rule condition remove -g group --rule-set-name ruleSetName --profile-name profile --rule-name name
        --index 0
"""

helps['afd rule condition list'] = """
type: command
short-summary: show condtions asscociated with the rule.
examples:
  - name: show condtions asscociated with the rule.
    text: >
        az afd rule condition list -g group --rule-set-name ruleSetName --profile-name profile --rule-name name
"""

helps['afd rule action'] = """
type: group
short-summary: Manage delivery rule actions for a rule.
"""

helps['afd rule action add'] = """
type: command
short-summary: Add an action to a delivery rule.
examples:
  - name: Add a redirect action.
    text: >
        az afd rule action add --rule-set-name ruleSetName --profile-name profile --rule-name name
        --action-name "UrlRedirect" --redirect-protocol HTTPS --redirect-type Moved
  - name: Add a cache expiration action
    text: >
        az afd rule action add --rule-set-name ruleSetName --profile-name profile --rule-name name
        --action-name "CacheExpiration" --cache-behavior BypassCache
"""

helps['afd rule action remove'] = """
type: command
short-summary: Remove an action from a delivery rule.
examples:
  - name: Remove the first action.
    text: >
        az afd rule action remove -g group --rule-set-name ruleSetName --profile-name profile --rule-name name
        --index 0
"""

helps['afd rule action list'] = """
type: command
short-summary: show actions asscociated with the rule.
examples:
  - name: show actions asscociated with the rule.
    text: >
        az afd rule action list -g group --rule-set-name ruleSetName --profile-name profile --rule-name name
"""

helps['afd log-analytic'] = """
type: group
short-summary: Manage afd log analytic results.
"""

helps['afd log-analytic location'] = """
type: group
short-summary: Manage available location names for AFD log analysis.
"""

helps['afd log-analytic metric'] = """
type: group
short-summary: Manage metric statistics for AFD profile.
"""

helps['afd log-analytic ranking'] = """
type: group
short-summary: Manage ranking statistics for AFD profile.
"""

helps['afd waf-log-analytic'] = """
type: group
short-summary: Manage afd WAF related log analytic results.
"""

helps['afd log-analytic resource'] = """
type: group
short-summary: Manage endpoints and custom domains available for AFD log analysis.
"""

helps['afd waf-log-analytic metric'] = """
type: group
short-summary: Manage WAF related metric statistics for AFD profile.
"""

helps['afd waf-log-analytic ranking'] = """
type: group
short-summary: Manage WAF related ranking statistics for AFD profile.
"""
