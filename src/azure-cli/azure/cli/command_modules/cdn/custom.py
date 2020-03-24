# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.cdn.models import (Endpoint, SkuName, EndpointUpdateParameters, ProfileUpdateParameters,
                                   EndpointPropertiesUpdateParametersDeliveryPolicy, DeliveryRule,
                                   DeliveryRuleRemoteAddressCondition, RemoteAddressMatchConditionParameters,
                                   DeliveryRuleRequestMethodCondition, RequestMethodMatchConditionParameters,
                                   DeliveryRuleQueryStringCondition, QueryStringMatchConditionParameters,
                                   DeliveryRulePostArgsCondition, PostArgsMatchConditionParameters,
                                   DeliveryRuleRequestHeaderCondition, RequestHeaderMatchConditionParameters,
                                   DeliveryRuleRequestUriCondition, RequestUriMatchConditionParameters,
                                   DeliveryRuleRequestBodyCondition, RequestBodyMatchConditionParameters,
                                   DeliveryRuleRequestSchemeCondition, RequestSchemeMatchConditionParameters,
                                   DeliveryRuleUrlPathCondition, UrlPathMatchConditionParameters,
                                   DeliveryRuleUrlFileExtensionCondition, UrlFileExtensionMatchConditionParameters,
                                   DeliveryRuleUrlFileNameCondition, UrlFileNameMatchConditionParameters,
                                   DeliveryRuleHttpVersionCondition, HttpVersionMatchConditionParameters,
                                   DeliveryRuleIsDeviceCondition, IsDeviceMatchConditionParameters,
                                   DeliveryRuleCookiesCondition, CookiesMatchConditionParameters,
                                   DeliveryRuleCacheExpirationAction, CacheExpirationActionParameters,
                                   DeliveryRuleRequestHeaderAction, HeaderActionParameters,
                                   DeliveryRuleResponseHeaderAction, DeliveryRuleCacheKeyQueryStringAction,
                                   CacheKeyQueryStringActionParameters, UrlRedirectAction,
                                   DeliveryRuleAction, UrlRedirectActionParameters,
                                   UrlRewriteAction, UrlRewriteActionParameters,
                                   PolicyMode, PolicyEnabledState, CdnWebApplicationFirewallPolicy, ManagedRuleSet,
                                   ManagedRuleGroupOverride, CustomRule, RateLimitRule)

from azure.mgmt.cdn.operations import (EndpointsOperations)

from azure.cli.core.util import (sdk_no_wait, find_child_item)
from azure.cli.core.commands import upsert_to_collection

from knack.util import CLIError
from knack.log import get_logger
logger = get_logger(__name__)


def default_content_types():
    return ["text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/x-javascript",
            "application/javascript",
            "application/json",
            "application/xml"]


def _update_mapper(existing, new, keys):
    for key in keys:
        existing_value = getattr(existing, key)
        new_value = getattr(new, key)
        setattr(new, key, new_value if new_value is not None else existing_value)


# region Custom Commands
def list_profiles(client, resource_group_name=None):
    profiles = client.profiles
    profile_list = profiles.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else profiles.list()
    return list(profile_list)


def update_endpoint(instance,
                    origin_host_header=None,
                    origin_path=None,
                    content_types_to_compress=None,
                    is_compression_enabled=None,
                    is_http_allowed=None,
                    is_https_allowed=None,
                    query_string_caching_behavior=None,
                    tags=None):
    params = EndpointUpdateParameters(
        origin_host_header=origin_host_header,
        origin_path=origin_path,
        content_types_to_compress=content_types_to_compress,
        is_compression_enabled=is_compression_enabled,
        is_http_allowed=is_http_allowed,
        is_https_allowed=is_https_allowed,
        query_string_caching_behavior=query_string_caching_behavior,
        tags=tags
    )

    if is_compression_enabled and not instance.content_types_to_compress:
        params.content_types_to_compress = default_content_types()

    _update_mapper(instance, params, [
        'origin_host_header',
        'origin_path',
        'content_types_to_compress',
        'is_compression_enabled',
        'is_http_allowed',
        'is_https_allowed',
        'query_string_caching_behavior',
        'tags'
    ])
    return params


def show_endpoint_waf_policy_link(client: EndpointsOperations,
                                  resource_group_name: str,
                                  profile_name: str,
                                  endpoint_name: str):

    from azure.mgmt.cdn.models import (EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink)

    link = client.get(resource_group_name, profile_name, endpoint_name).web_application_firewall_policy_link
    if link is not None:
        return link
    raise CLIError(f"endpoint {endpoint_name} does not have a CDN WAF policy link.", endpoint_name)


def set_endpoint_waf_policy_link(client: EndpointsOperations,
                                 resource_group_name: str,
                                 profile_name: str,
                                 endpoint_name: str,
                                 waf_policy_subscription_id: str = "",
                                 waf_policy_resource_group_name: str = "",
                                 waf_policy_name: str = "",
                                 waf_policy_id: str = ""):

    from azure.mgmt.cdn.models import (EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink)

    endpoint = client.get(resource_group_name, profile_name, endpoint_name)

    if waf_policy_id == "":
        if waf_policy_subscription_id is None or waf_policy_resource_group_name is None or waf_policy_name is None:
            raise CLIError('Either --waf-policy-id or all of --waf-policy-subscription-id, '
                           '--waf-policy-resource-group-name, and --waf-policy-name must be specified.')
        waf_policy_id = f'/subscriptions/{waf_policy_subscription_id}' \
                        f'/resourceGroups/{waf_policy_resource_group_name}' \
                        f'/providers/Microsoft.Cdn' \
                        f'/CdnWebApplicationFirewallPolicies/{waf_policy_name}'
    print(waf_policy_id)
    endpoint.web_application_firewall_policy_link = \
        EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink(id=waf_policy_id)

    result = client.create(resource_group_name, profile_name, endpoint_name, endpoint).result()
    if result is not None:
        return result.web_application_firewall_policy_link
    return EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink(id=None)


def remove_endpoint_waf_policy_link(client: EndpointsOperations,
                                    resource_group_name: str,
                                    profile_name: str,
                                    endpoint_name: str):

    endpoint = client.get(resource_group_name, profile_name, endpoint_name)
    endpoint.web_application_firewall_policy_link = None
    client.create(resource_group_name, profile_name, endpoint_name, endpoint).wait()


# pylint: disable=too-many-return-statements
def create_condition(match_variable=None, operator=None, match_values=None,
                     selector=None, negate_condition=None, transform=None):
    if match_variable == 'RemoteAddress':
        return DeliveryRuleRemoteAddressCondition(
            parameters=RemoteAddressMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestMethod':
        return DeliveryRuleRequestMethodCondition(
            parameters=RequestMethodMatchConditionParameters(
                match_values=match_values,
                negate_condition=negate_condition
            ))
    if match_variable == 'QueryString':
        return DeliveryRuleQueryStringCondition(
            parameters=QueryStringMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'PostArgs':
        return DeliveryRulePostArgsCondition(
            parameters=PostArgsMatchConditionParameters(
                operator=operator,
                selector=selector,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestHeader':
        return DeliveryRuleRequestHeaderCondition(
            parameters=RequestHeaderMatchConditionParameters(
                operator=operator,
                selector=selector,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestUri':
        return DeliveryRuleRequestUriCondition(
            parameters=RequestUriMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestBody':
        return DeliveryRuleRequestBodyCondition(
            parameters=RequestBodyMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestScheme':
        return DeliveryRuleRequestSchemeCondition(
            parameters=RequestSchemeMatchConditionParameters(
                match_values=match_values,
                negate_condition=negate_condition
            ))
    if match_variable == 'UrlPath':
        return DeliveryRuleUrlPathCondition(
            parameters=UrlPathMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'UrlFileExtension':
        return DeliveryRuleUrlFileExtensionCondition(
            parameters=UrlFileExtensionMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'UrlFileName':
        return DeliveryRuleUrlFileNameCondition(
            parameters=UrlFileNameMatchConditionParameters(
                operator=operator,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'HttpVersion':
        return DeliveryRuleHttpVersionCondition(
            parameters=HttpVersionMatchConditionParameters(
                match_values=match_values,
                negate_condition=negate_condition
            ))
    if match_variable == 'IsDevice':
        return DeliveryRuleIsDeviceCondition(
            parameters=IsDeviceMatchConditionParameters(
                match_values=match_values,
                negate_condition=negate_condition
            ))
    if match_variable == 'Cookies':
        return DeliveryRuleCookiesCondition(
            parameters=CookiesMatchConditionParameters(
                operator=operator,
                selector=selector,
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    return None


# pylint: disable=too-many-return-statements
def create_action(action_name, cache_behavior=None, cache_duration=None, header_action=None,
                  header_name=None, header_value=None, query_string_behavior=None, query_parameters=None,
                  redirect_type=None, redirect_protocol=None, custom_hostname=None, custom_path=None,
                  custom_query_string=None, custom_fragment=None, source_pattern=None, destination=None,
                  preserve_unmatched_path=None):
    if action_name == "CacheExpiration":
        return DeliveryRuleCacheExpirationAction(
            parameters=CacheExpirationActionParameters(
                cache_behavior=cache_behavior,
                cache_duration=cache_duration
            ))
    if action_name == 'RequestHeader':
        return DeliveryRuleRequestHeaderAction(
            parameters=HeaderActionParameters(
                header_action=header_action,
                header_name=header_name,
                value=header_value
            ))
    if action_name == 'ResponseHeader':
        return DeliveryRuleResponseHeaderAction(
            parameters=HeaderActionParameters(
                header_action=header_action,
                header_name=header_name,
                value=header_value
            ))
    if action_name == "CacheKeyQueryString":
        return DeliveryRuleCacheKeyQueryStringAction(
            parameters=CacheKeyQueryStringActionParameters(
                query_string_behavior=query_string_behavior,
                query_parameters=query_parameters
            ))
    if action_name == 'UrlRedirect':
        return UrlRedirectAction(
            parameters=UrlRedirectActionParameters(
                redirect_type=redirect_type,
                destination_protocol=redirect_protocol,
                custom_path=custom_path,
                custom_hostname=custom_hostname,
                custom_query_string=custom_query_string,
                custom_fragment=custom_fragment
            ))
    if action_name == 'UrlRewrite':
        return UrlRewriteAction(
            parameters=UrlRewriteActionParameters(
                source_pattern=source_pattern,
                destination=destination,
                preserve_unmatched_path=preserve_unmatched_path
            ))
    return DeliveryRuleAction()


# pylint: disable=too-many-locals
def add_rule(client, resource_group_name, profile_name, endpoint_name,
             order, rule_name, action_name, match_variable=None, operator=None,
             match_values=None, selector=None, negate_condition=None, transform=None,
             cache_behavior=None, cache_duration=None, header_action=None,
             header_name=None, header_value=None, query_string_behavior=None, query_parameters=None,
             redirect_type=None, redirect_protocol=None, custom_hostname=None, custom_path=None,
             custom_querystring=None, custom_fragment=None, source_pattern=None,
             destination=None, preserve_unmatched_path=None):
    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    if policy is None:
        policy = EndpointPropertiesUpdateParametersDeliveryPolicy(
            description='delivery_policy',
            rules=[])

    conditions = []
    condition = create_condition(match_variable, operator, match_values, selector, negate_condition, transform)
    if condition is not None:
        conditions.append(condition)
    actions = []
    action = create_action(action_name, cache_behavior, cache_duration, header_action, header_name,
                           header_value, query_string_behavior, query_parameters, redirect_type,
                           redirect_protocol, custom_hostname, custom_path, custom_querystring,
                           custom_fragment, source_pattern, destination, preserve_unmatched_path)
    if action is not None:
        actions.append(action)

    rule = DeliveryRule(
        name=rule_name,
        order=order,
        conditions=conditions,
        actions=actions
    )

    policy.rules.append(rule)
    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.update(resource_group_name, profile_name, endpoint_name, params)


def add_condition(client, resource_group_name, profile_name, endpoint_name,
                  rule_name, match_variable, operator, match_values=None, selector=None,
                  negate_condition=None, transform=None):

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    condition = create_condition(match_variable, operator, match_values, selector, negate_condition, transform)
    for i in range(0, len(policy.rules)):
        if policy.rules[i].name == rule_name:
            policy.rules[i].conditions.append(condition)

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.update(resource_group_name, profile_name, endpoint_name, params)


def add_action(client, resource_group_name, profile_name, endpoint_name,
               rule_name, action_name, cache_behavior=None, cache_duration=None,
               header_action=None, header_name=None, header_value=None, query_string_behavior=None,
               query_parameters=None, redirect_type=None, redirect_protocol=None, custom_hostname=None,
               custom_path=None, custom_querystring=None, custom_fragment=None, source_pattern=None,
               destination=None, preserve_unmatched_path=None):

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    action = create_action(action_name, cache_behavior, cache_duration, header_action, header_name,
                           header_value, query_string_behavior, query_parameters, redirect_type,
                           redirect_protocol, custom_hostname, custom_path, custom_querystring,
                           custom_fragment, source_pattern, destination, preserve_unmatched_path)
    for i in range(0, len(policy.rules)):
        if policy.rules[i].name == rule_name:
            policy.rules[i].actions.append(action)

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.update(resource_group_name, profile_name, endpoint_name, params)


def remove_rule(client, resource_group_name, profile_name, endpoint_name, rule_name):

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    if policy is not None:
        for rule in policy.rules:
            if rule.name == rule_name:
                policy.rules.remove(rule)
    else:
        logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.update(resource_group_name, profile_name, endpoint_name, params)


def remove_condition(client, resource_group_name, profile_name, endpoint_name, rule_name, index):

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    if policy is not None:
        for i in range(0, len(policy.rules)):
            if policy.rules[i].name == rule_name:
                policy.rules[i].conditions.pop(index)
    else:
        logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.update(resource_group_name, profile_name, endpoint_name, params)


def remove_action(client, resource_group_name, profile_name, endpoint_name, rule_name, index):

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    if policy is not None:
        for i in range(0, len(policy.rules)):
            if policy.rules[i].name == rule_name:
                policy.rules[i].actions.pop(index)
    else:
        logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.update(resource_group_name, profile_name, endpoint_name, params)


def create_endpoint(client, resource_group_name, profile_name, name, origins, location=None,
                    origin_host_header=None, origin_path=None, content_types_to_compress=None,
                    is_compression_enabled=None, is_http_allowed=None, is_https_allowed=None,
                    query_string_caching_behavior=None, tags=None, no_wait=None):

    is_compression_enabled = False if is_compression_enabled is None else is_compression_enabled
    is_http_allowed = True if is_http_allowed is None else is_http_allowed
    is_https_allowed = True if is_https_allowed is None else is_https_allowed
    endpoint = Endpoint(location=location,
                        origins=origins,
                        origin_host_header=origin_host_header,
                        origin_path=origin_path,
                        content_types_to_compress=content_types_to_compress,
                        is_compression_enabled=is_compression_enabled,
                        is_http_allowed=is_http_allowed,
                        is_https_allowed=is_https_allowed,
                        query_string_caching_behavior=query_string_caching_behavior,
                        tags=tags)
    if is_compression_enabled and not endpoint.content_types_to_compress:
        endpoint.content_types_to_compress = default_content_types()

    return sdk_no_wait(no_wait, client.endpoints.create, resource_group_name, profile_name, name, endpoint)


# pylint: disable=unused-argument
def create_custom_domain(client, resource_group_name, profile_name, endpoint_name, custom_domain_name,
                         hostname, location=None, tags=None):
    return client.custom_domains.create(resource_group_name,
                                        profile_name,
                                        endpoint_name,
                                        custom_domain_name,
                                        hostname)


def update_profile(instance, tags=None):
    params = ProfileUpdateParameters(tags=tags)
    _update_mapper(instance, params, ['tags'])
    return params


def create_profile(client, resource_group_name, name,
                   sku=SkuName.standard_akamai.value,
                   location=None, tags=None):
    from azure.mgmt.cdn.models import (Profile, Sku)
    profile = Profile(location=location, sku=Sku(name=sku), tags=tags)
    return client.profiles.create(resource_group_name, name, profile)
# endregion


# region WAF Custom Commands
def list_waf_managed_rule_set(client):
    return client.list()


def _show_waf_managed_rule_set(client, rule_set_type, rule_set_version):
    rulesets = client.list()
    for r in rulesets:
        if r.rule_set_type == rule_set_type and r.rule_set_version == rule_set_version:
            return r
    raise CLIError("managed rule set type '{}' version '{}' not found".format(rule_set_type, rule_set_version))


def list_waf_managed_rule_groups(client, rule_set_type, rule_set_version):
    return _show_waf_managed_rule_set(client, rule_set_type, rule_set_version).rule_groups


def set_waf_policy(client,
                   resource_group_name, name,
                   sku=SkuName.standard_microsoft.value,
                   disabled=None,
                   mode=PolicyMode.detection.value,
                   redirect_url=None,
                   block_response_body=None,
                   block_response_status_code=None,
                   tags=None):
    from azure.mgmt.cdn.models import (PolicySettings, ErrorResponseException, Sku)
    policy = CdnWebApplicationFirewallPolicy(
        tags=tags,
        sku=Sku(name=sku),
        location='Global',
        policy_settings=PolicySettings(
            enabled_state=PolicyEnabledState.disabled.value if disabled else PolicyEnabledState.enabled.value,
            mode=mode,
            default_redirect_url=redirect_url,
            default_custom_block_response_status_code=block_response_status_code,
            default_custom_block_response_body=block_response_body))

    # Copy config set by sub-commands for updating an existing policy.
    try:
        existing = client.get(resource_group_name, name)
        # Update, let's copy over config set by sub-commands
        policy.custom_rules = existing.custom_rules
        policy.rate_limit_rules = existing.rate_limit_rules
        policy.managed_rules = existing.managed_rules
    except ErrorResponseException as e:
        # If the error isn't a 404, rethrow it.
        props = getattr(e.inner_exception, 'additional_properties')
        if not isinstance(props, dict) or not isinstance(props.get('error'), dict):
            raise e
        props = props['error']
        if props.get('code') != 'ResourceNotFound':
            raise e
        # 404 error means it's a new policy, nothing to copy.

    return client.create_or_update(resource_group_name, name, policy)


def _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version):
    for r in policy.managed_rules.managed_rule_sets:
        if r.rule_set_type == rule_set_type and r.rule_set_version == rule_set_version:
            return r
    return None


def add_waf_policy_managed_rule_set(client,
                                    resource_group_name,
                                    policy_name,
                                    rule_set_type,
                                    rule_set_version):

    # Get the existing WAF policy.
    policy = client.get(resource_group_name, policy_name)

    # Verify the managed rule set is not already added to the policy.
    existing = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if existing is not None:
        raise CLIError("managed rule set type '{}' version '{}' is already added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    # Add the managed rule set to the policy.
    policy.managed_rules.managed_rule_sets.append(ManagedRuleSet(rule_set_type=rule_set_type,
                                                                 rule_set_version=rule_set_version))
    result = client.create_or_update(resource_group_name, policy_name, policy).result()

    # Return the new managed rule set from the updated policy.
    updated = _find_policy_managed_rule_set(result, rule_set_type, rule_set_version)
    if updated is None:
        raise CLIError("failed to get added managed rule set in WAF policy '{}'".format(policy_name))

    return updated


def remove_waf_policy_managed_rule_set(client,
                                       resource_group_name,
                                       policy_name,
                                       rule_set_type,
                                       rule_set_version):
    # Get the existing WAF policy.
    policy = client.get(resource_group_name, policy_name)

    # Verify the managed rule set is added to the policy.
    existing = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if existing is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    # Remove the managed rule set from the policy.
    policy.managed_rules.managed_rule_sets.remove(existing)
    client.create_or_update(resource_group_name, policy_name, policy).wait()


def list_waf_policy_managed_rule_sets(client,
                                      resource_group_name,
                                      policy_name):
    policy = client.get(resource_group_name, policy_name)
    return policy.managed_rules.managed_rule_sets


def show_waf_policy_managed_rule_set(client,
                                     resource_group_name,
                                     policy_name,
                                     rule_set_type,
                                     rule_set_version):
    policy = client.get(resource_group_name, policy_name)
    existing = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if existing is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))
    return existing


def set_waf_managed_rule_group_override(client,
                                        resource_group_name,
                                        policy_name,
                                        rule_set_type,
                                        rule_set_version,
                                        name,
                                        rule_overrides):
    policy = client.get(resource_group_name, policy_name)
    ruleset = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if ruleset is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    rulegroup = ManagedRuleGroupOverride(rule_group_name=name, rules=rule_overrides)
    upsert_to_collection(ruleset, 'rule_group_overrides', rulegroup, 'rule_group_name')
    policy = client.create_or_update(resource_group_name, policy_name, policy).result()
    ruleset = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    return find_child_item(ruleset, name, path='rule_group_overrides', key_path='rule_group_name')


def delete_waf_managed_rule_group_override(client,
                                           resource_group_name,
                                           policy_name,
                                           rule_set_type,
                                           rule_set_version,
                                           name):
    policy = client.get(resource_group_name, policy_name)
    ruleset = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if ruleset is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    override = find_child_item(ruleset, name, path='rule_group_overrides', key_path='rule_group_name')
    ruleset.rule_group_overrides.remove(override)
    client.create_or_update(resource_group_name, policy_name, policy).wait()


def list_waf_policy_managed_rule_group_overrides(client,
                                                 resource_group_name,
                                                 policy_name,
                                                 rule_set_type,
                                                 rule_set_version):
    ruleset = show_waf_policy_managed_rule_set(client,
                                               resource_group_name,
                                               policy_name,
                                               rule_set_type,
                                               rule_set_version)
    return ruleset.rule_group_overrides


def show_waf_managed_rule_group_override(client,
                                         resource_group_name,
                                         policy_name,
                                         rule_set_type,
                                         rule_set_version,
                                         name):
    ruleset = show_waf_policy_managed_rule_set(client,
                                               resource_group_name,
                                               policy_name,
                                               rule_set_type,
                                               rule_set_version)
    return find_child_item(ruleset, name, path='rule_group_overrides', key_path='rule_group_name')


def set_waf_custom_rule(client,
                        resource_group_name,
                        policy_name,
                        name,
                        priority,
                        action,
                        match_conditions,
                        disabled=None):
    from azure.mgmt.cdn.models import (CustomRuleEnabledState)

    rule = CustomRule(name=name,
                      enabled_state=CustomRuleEnabledState.disabled if disabled else CustomRuleEnabledState.enabled,
                      action=action,
                      match_conditions=match_conditions,
                      priority=priority)

    policy = client.get(resource_group_name, policy_name)
    upsert_to_collection(policy.custom_rules, 'rules', rule, 'name')
    policy = client.create_or_update(resource_group_name, policy_name, policy).result()
    return find_child_item(policy.custom_rules, name, path='rules', key_path='name')


def delete_waf_custom_rule(client,
                           resource_group_name,
                           policy_name,
                           name,
                           no_wait=None):
    policy = client.get(resource_group_name, policy_name)
    rule = find_child_item(policy.custom_rules, name, path='rules', key_path='name')
    policy.custom_rules.rules.remove(rule)
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, policy_name, policy)


def show_waf_custom_rule(client, resource_group_name, policy_name, name):
    policy = client.get(resource_group_name, policy_name)
    return find_child_item(policy.custom_rules, name, path='rules', key_path='name')


def list_waf_custom_rules(client,
                          resource_group_name,
                          policy_name):
    return client.get(resource_group_name, policy_name).custom_rules.rules


def set_waf_rate_limit_rule(client,
                            resource_group_name,
                            policy_name,
                            name,
                            priority,
                            action,
                            request_threshold,
                            duration,
                            match_conditions,
                            disabled=None):
    from azure.mgmt.cdn.models import (CustomRuleEnabledState)

    rule = RateLimitRule(name=name,
                         enabled_state=CustomRuleEnabledState.disabled if disabled else CustomRuleEnabledState.enabled,
                         rate_limit_threshold=request_threshold,
                         rate_limit_duration_in_minutes=duration,
                         action=action,
                         match_conditions=match_conditions,
                         priority=priority)

    policy = client.get(resource_group_name, policy_name)
    upsert_to_collection(policy.rate_limit_rules, 'rules', rule, 'name')
    updated = client.create_or_update(resource_group_name, policy_name, policy).result()
    return find_child_item(updated.rate_limit_rules, name, path='rules', key_path='name')


def delete_waf_rate_limit_rule(client,
                               resource_group_name,
                               policy_name,
                               name,
                               no_wait=None):
    policy = client.get(resource_group_name, policy_name)
    rule = find_child_item(policy.rate_limit_rules, name, path='rules', key_path='name')
    policy.rate_limit_rules.rules.remove(rule)
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, policy_name, policy)


def show_waf_rate_limit_rule(client, resource_group_name, policy_name, name):
    policy = client.get(resource_group_name, policy_name)
    return find_child_item(policy.rate_limit_rules, name, path='rules', key_path='name')


def list_waf_rate_limit_rules(client,
                              resource_group_name,
                              policy_name):
    return client.get(resource_group_name, policy_name).rate_limit_rules.rules

# endregion
