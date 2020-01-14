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
                                   UrlRewriteAction, UrlRewriteActionParameters)

from azure.cli.core.util import sdk_no_wait


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


# pylint: disable=too-many-return-statements
def create_condition(match_variable=None, operator=None, match_values=None,
                     selector=None, negate_condition=None, transform=None):
    if match_variable == 'RemoteAddress':
        return DeliveryRuleRemoteAddressCondition(
            parameters=RemoteAddressMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestMethod':
        return DeliveryRuleRequestMethodCondition(
            parameters=RequestMethodMatchConditionParameters(
                match_values=match_values.split(","),
                negate_condition=negate_condition
            ))
    if match_variable == 'QueryString':
        return DeliveryRuleQueryStringCondition(
            parameters=QueryStringMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'PostArgs':
        return DeliveryRulePostArgsCondition(
            parameters=PostArgsMatchConditionParameters(
                operator=operator,
                selector=selector,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestHeader':
        return DeliveryRuleRequestHeaderCondition(
            parameters=RequestHeaderMatchConditionParameters(
                operator=operator,
                selector=selector,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestUri':
        return DeliveryRuleRequestUriCondition(
            parameters=RequestUriMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestBody':
        return DeliveryRuleRequestBodyCondition(
            parameters=RequestBodyMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestScheme':
        return DeliveryRuleRequestSchemeCondition(
            parameters=RequestSchemeMatchConditionParameters(
                match_values=match_values.split(","),
                negate_condition=negate_condition
            ))
    if match_variable == 'UrlPath':
        return DeliveryRuleUrlPathCondition(
            parameters=UrlPathMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'UrlFileExtension':
        return DeliveryRuleUrlFileExtensionCondition(
            parameters=UrlFileExtensionMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'UrlFileName':
        return DeliveryRuleUrlFileNameCondition(
            parameters=UrlFileNameMatchConditionParameters(
                operator=operator,
                match_values=match_values.split(","),
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'HttpVersion':
        return DeliveryRuleHttpVersionCondition(
            parameters=HttpVersionMatchConditionParameters(
                match_values=match_values.split(","),
                negate_condition=negate_condition
            ))
    if match_variable == 'IsDevice':
        return DeliveryRuleIsDeviceCondition(
            parameters=IsDeviceMatchConditionParameters(
                match_values=match_values.split(","),
                negate_condition=negate_condition
            ))
    if match_variable == 'Cookies':
        return DeliveryRuleCookiesCondition(
            parameters=CookiesMatchConditionParameters(
                operator=operator,
                selector=selector,
                match_values=match_values.split(","),
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
                policy.rules[i].conditions.pop(int(index))

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
                policy.rules[i].actions.pop(int(index))

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
