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
  - name: Create a custom domain within an endpoint and profile.
    text: >
        az cdn custom-domain create -g group --endpoint-name endpoint --profile-name profile \\
            -n domain-name --hostname www.example.com
  - name: Enable custom https with a minimum
    text: >
        az cdn custom-domain create -g group --endpoint-name endpoint --profile-name profile \\
            -n domain-name --hostname www.example.com
"""

helps['cdn custom-domain delete'] = """
type: command
short-summary: Delete the custom domain of a CDN.
examples:
  - name: Delete a custom domain.
    text: >
        az cdn custom-domain delete -g group --endpoint-name endpoint --profile-name profile \\
            -n domain-name
"""

helps['cdn custom-domain show'] = """
type: command
short-summary: Show details for the custom domain of a CDN.
examples:
  - name: Get the details of a custom domain.
    text: >
        az cdn custom-domain show -g group --endpoint-name endpoint --profile-name profile \\
            -n domain-name
"""

helps['cdn edge-node'] = """
type: group
short-summary: View all available CDN edge nodes.
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
  - name: Create an endpoint with a custom domain with compression and only HTTPS.
    text: >
        az cdn endpoint create -g group -n endpoint --profile-name profile
        --origin www.example.com --no-http --enable-compression
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
examples:
  - name: Pre-load Javascript and CSS content for an endpoint.
    text: >
        az cdn endpoint load -g group -n endpoint --profile-name profile-name --content-paths
        '/scripts/app.js' '/styles/main.css'
"""

helps['cdn endpoint purge'] = """
type: command
short-summary: Purge pre-loaded content for a CDN endpoint.
examples:
  - name: Purge pre-loaded Javascript and CSS content.
    text: >
        az cdn endpoint purge -g group -n endpoint --profile-name profile-name --content-paths
        '/scripts/app.js' '/styles/*'
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
examples:
  - name: Create a global rule to disable caching.
    text: >
        az cdn endpoint rule add -g group -n endpoint --profile-name profile --order 0
        --rule-name global --action-name CacheExpiration --cache-behavior BypassCache
  - name: Create a rule for http to https redirect
    text: >
        az cdn endpoint rule add -g group -n endpoint --profile-name profile --order 1
        --rule-name "redirect" --match-variable RequestScheme --operator Equal --match-values HTTPS
        --action-name "UrlRedirect" --redirect-protocol Https --redirect-type Moved
"""

helps['cdn endpoint rule remove'] = """
type: command
short-summary: Remove a delivery rule from an endpoint.
examples:
  - name: Remove the global rule.
    text: >
        az cdn endpoint rule remove -g group -n endpoint --profile-name profile --rule-name Global
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
        az cdn endpoint rule condition add -g group -n endpoint --profile-name profile --rule-name name \\
            --match-variable RemoteAddress --operator GeoMatch --match-values "TH"
"""

helps['cdn endpoint rule condition remove'] = """
type: command
short-summary: Remove a condition from a delivery rule.
examples:
  - name: Remove the first condition.
    text: >
        az cdn endpoint rule condition remove -g group -n endpoint --profile-name profile --rule-name name \\
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
        az cdn endpoint rule action add -g group -n endpoint --profile-name profile --rule-name name \\
            --action-name "UrlRedirect" --redirect-protocol HTTPS --redirect-type Moved
  - name: Add a cache expiration action
    text: >
        az cdn endpoint rule action add -g group -n endpoint --profile-name profile --rule-name name \\
            --action-name "CacheExpiration" --cache-behavior BypassCache
"""

helps['cdn endpoint rule action remove'] = """
type: command
short-summary: Remove an action from a delivery rule.
examples:
  - name: Remove the first action.
    text: >
        az cdn endpoint rule action remove -g group -n endpoint --profile-name profile --rule-name name \\
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
        az cdn endpoint waf policy set -g group --endpoint-name endpoint \\
            --profile-name profile --waf-policy-subscription-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \\
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

helps['cdn profile update'] = """
type: command
short-summary: Update a CDN profile.
examples:
  - name: Update a CDN profile. (autogenerated)
    text: az cdn profile update --name MyCDNProfileWhichIsUniqueWithinResourceGroup --resource-group MyResourceGroup
    crafted: true
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
    text: |
        az cdn waf policy set -g group -n policy
  - name: Create a CDN WAF policy in with a custom block response status code.
    text: |
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
    text: |
        az cdn waf policy managed-rule-set add -g group --policy-name policy \\
          --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy managed-rule-set remove'] = """
type: command
short-summary: Remove a managed rule set from a CDN WAF policy.
examples:
  - name: Remove DefaultRuleSet_1.0 from a CDN WAF policy.
    text: |
        az cdn waf policy managed-rule-set remove -g group --policy-name policy \\
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
        az cdn waf policy managed-rule-set show -g group --policy-name policy \\
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
    long-summary: |
        rule overrides are specified as key value pairs in the form "KEY=VALUE [KEY=VALUE ...]".
        Available keys are 'id', 'action', and 'enabled'. 'id' is required. Valid values for
        'action' are 'Block', 'Redirect', 'Allow', and 'Log', defaulting to 'Block'. Valid values
        for 'enabled' are 'Enabled' and 'Disabled', defaulting to 'Disabled'.
examples:
  - name: Add a rule group override for SQL injections to DefaultRuleSet_1.0 on a CDN WAF policy.
    text: |
        az cdn waf policy managed-rule-set rule-group-override set -g group --policy-name policy \\
          --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI -r \\
          id=942440 action=Redirect enabled=Enabled
  - name: Add multiple rule group overrides to DefaultRuleSet_1.0 on a CDN WAF policy.
    text: |
        az cdn waf policy managed-rule-set rule-group-override set -g group --policy-name policy \\
          --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI \\
          -r id=942440 action=Redirect enabled=Enabled \\
          -r id=942120 -r id=942100
"""

helps['cdn waf policy managed-rule-set rule-group-override delete'] = """
type: command
short-summary: Remove a rule group override from a managed rule set on a CDN WAF policy.
examples:
  - name: Remove the rule group override for SQLI from DefaultRuleSet_1.0 on a CDN WAF policy.
    text: |
        az cdn waf policy managed-rule-set rule-group-override delete -g group --policy-name policy \\
          --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI
"""

helps['cdn waf policy managed-rule-set rule-group-override list'] = """
type: command
short-summary: List rule group overrides of a managed rule on a CDN WAF policy.
examples:
  - name: List rule group overrides of a managed rule on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override list -g group --policy-name policy \\
          --rule-set-type DefaultRuleSet --rule-set-version 1.0
"""

helps['cdn waf policy managed-rule-set rule-group-override show'] = """
type: command
short-summary: Show a rule group override of a managed rule on a CDN WAF policy.
examples:
  - name: Get the rule group override for rule group SQLI of DefaultRuleSet_1.0 on a CDN WAF policy.
    text: >
        az cdn waf policy managed-rule-set rule-group-override show -g group --policy-name policy \\
          --rule-set-type DefaultRuleSet --rule-set-version 1.0 -n SQLI
"""

helps['cdn waf policy managed-rule-set rule-group-override list-available'] = """
type: command
short-summary: List available CDN WAF managed rule groups of a managed rule set.
examples:
  - name: List available rule groups for DefaultRuleSet_1.0.
    text: |
      az cdn waf policy managed-rule-set rule-group-override list-available \\
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
    long-summary: |
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
    text: |
        az cdn waf policy custom-rule set -g group --policy-name policy -n customrule \\
          --action Block --priority 100 --match-condition \\
          match-variable=RequestMethod operator=Equal negate=true match-value=GET match-value=HEAD
  - name: Create or update a custom rule with multiple match conditions and whitespace in a match value.
    text: |
        az cdn waf policy custom-rule set -g group --policy-name policy -n customrule \\
          --action Redirect --priority 100 \\
          -m match-variable=RequestUri operator=Contains match-value=.. \\
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
    text: |
        az cdn waf policy rate-limit-rule set -g group --policy-name policy \\
          -n ratelimitrule --action Block --priority 100 --duration 1 --request-threshold 100 \\
          -m match-variable=RequestMethod operator=Equal negate=true match-value=GET match-value=HEAD
  - name: Create or update a rate limit rule with multiple match conditions.
    text: |
        az cdn waf policy rate-limit-rule set -g group --policy-name policy \\
          -n ratelimitrule --action Redirect --priority 200 --duration 5 --request-threshold 100 \\
          -m match-variable=RequestMethod operator=Equal match-value=PUT \\
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
