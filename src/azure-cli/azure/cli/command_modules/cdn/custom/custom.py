# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from azure.mgmt.cdn.models import (Endpoint, SkuName, EndpointUpdateParameters, ProfileUpdateParameters,
                                   MinimumTlsVersion, EndpointPropertiesUpdateParametersDeliveryPolicy, DeliveryRule,
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
                                   CacheKeyQueryStringActionParameters, UrlRedirectAction, ValidateCustomDomainInput,
                                   DeliveryRuleAction, UrlRedirectActionParameters, LoadParameters,
                                   UrlRewriteAction, UrlRewriteActionParameters, PurgeParameters,
                                   CheckNameAvailabilityInput, CustomDomainParameters, ProbeProtocol,
                                   HealthProbeRequestType, RequestMethodOperator, OriginGroupOverrideAction,
                                   OriginGroupOverrideActionParameters, ResourceReference)

from azure.mgmt.cdn.models._cdn_management_client_enums import CacheType
from azure.mgmt.cdn.operations import (OriginsOperations, OriginGroupsOperations)

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import (sdk_no_wait)
from azure.core.exceptions import (ResourceNotFoundError)

from knack.util import CLIError
from knack.log import get_logger

from msrest.polling import LROPoller, NoPolling
from msrestazure.tools import is_valid_resource_id

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


def _convert_to_unified_delivery_rules(policy):
    for existing_rule in policy.rules:
        if existing_rule.conditions:
            for con in existing_rule.conditions:
                if con.parameters.operator is None and con.parameters.match_values is None:
                    if con.parameters.odata_type == UrlPathMatchConditionParameters.odata_type:
                        con.parameters.operator = con.parameters.additional_properties["matchType"]
                        con.parameters.match_values = con.parameters.additional_properties["path"].split(',')
                    if con.parameters.odata_type == UrlFileExtensionMatchConditionParameters.odata_type:
                        con.parameters.operator = "Any"
                        con.parameters.match_values = con.parameters.additional_properties["extensions"]


# region Custom Commands
def list_profiles(client, resource_group_name=None):
    profiles = client.profiles
    profile_list = profiles.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else profiles.list()

    return [profile for profile in profile_list if profile.sku.name not in
            (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door)]


def check_name_availability(client, name):
    """Check the availability of a resource name. This is needed for resources
    where name is globally unique, such as a CDN endpoint.
    :param name: The resource name to validate.
    :type name: str
    """

    validate_input = CheckNameAvailabilityInput(name=name)

    return client.check_name_availability(validate_input)


def validate_custom_domain(client, resource_group_name, profile_name, endpoint_name, host_name):
    validate_input = ValidateCustomDomainInput(host_name=host_name)

    return client.endpoints.validate_custom_domain(resource_group_name, profile_name, endpoint_name, validate_input)


def get_profile(client, resource_group_name, profile_name):
    profile = client.profiles.get(resource_group_name, profile_name)
    if profile.sku.name in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
        # Workaround to make the behavior consist with true "Not Found"
        logger.warning('Standard_AzureFrontDoor and Premium_AzureFrontDoor are only supported for AFD profiles')
        raise ResourceNotFoundError("Operation returned an invalid status code 'Not Found'")

    return profile


def delete_profile(client, resource_group_name, profile_name):
    profile = None
    try:
        profile = client.profiles.get(resource_group_name, profile_name)
    except ResourceNotFoundError:
        pass

    if profile is None or profile.sku.name in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
        def get_long_running_output(_):
            return None

        logger.warning('Standard_AzureFrontDoor and Premium_AzureFrontDoor are only supported for AFD profiles')
        return LROPoller(client, None, get_long_running_output, NoPolling())

    return client.profiles.begin_delete(resource_group_name, profile_name)


def update_endpoint(instance,
                    origin_host_header=None,
                    origin_path=None,
                    content_types_to_compress=None,
                    is_compression_enabled=None,
                    is_http_allowed=None,
                    is_https_allowed=None,
                    query_string_caching_behavior=None,
                    default_origin_group=None,
                    tags=None):

    # default origin group is specified as a name, format it as an ID.
    if default_origin_group is not None:
        if '/' not in default_origin_group:
            default_origin_group = f'{instance.id}/originGroups/{default_origin_group}'
        default_origin_group = ResourceReference(id=default_origin_group)

    params = EndpointUpdateParameters(
        origin_host_header=origin_host_header,
        origin_path=origin_path,
        content_types_to_compress=content_types_to_compress,
        is_compression_enabled=is_compression_enabled,
        is_http_allowed=is_http_allowed,
        is_https_allowed=is_https_allowed,
        query_string_caching_behavior=query_string_caching_behavior,
        default_origin_group=default_origin_group,
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
        'default_origin_group',
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
                match_values=match_values,
                negate_condition=negate_condition,
                transforms=transform
            ))
    if match_variable == 'RequestMethod':
        return DeliveryRuleRequestMethodCondition(
            parameters=RequestMethodMatchConditionParameters(
                match_values=match_values,
                negate_condition=negate_condition,
                operator=RequestMethodOperator.EQUAL
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
                negate_condition=negate_condition,
                operator=RequestMethodOperator.EQUAL
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
                negate_condition=negate_condition,
                operator=RequestMethodOperator.EQUAL
            ))
    if match_variable == 'IsDevice':
        return DeliveryRuleIsDeviceCondition(
            parameters=IsDeviceMatchConditionParameters(
                match_values=match_values,
                negate_condition=negate_condition,
                operator=RequestMethodOperator.EQUAL
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
                  preserve_unmatched_path=None, cmd=None, resource_group_name=None, profile_name=None,
                  endpoint_name=None, origin_group=None):
    if action_name == "CacheExpiration":
        return DeliveryRuleCacheExpirationAction(
            parameters=CacheExpirationActionParameters(
                cache_behavior=cache_behavior,
                cache_duration=cache_duration,
                cache_type=CacheType.ALL
            ))
    if action_name in ('RequestHeader', 'ModifyRequestHeader'):
        return DeliveryRuleRequestHeaderAction(
            parameters=HeaderActionParameters(
                header_action=header_action,
                header_name=header_name,
                value=header_value
            ))
    if action_name in ('ResponseHeader', 'ModifyResponseHeader'):
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
    if action_name == 'OriginGroupOverride':
        if not is_valid_resource_id(origin_group):
            # Ideally we should use resource_id but Auzre FrontDoor portal extension has some case-sensitive issues
            # that prevent it from displaying correctly in portal.
            origin_group = f'/subscriptions/{get_subscription_id(cmd.cli_ctx)}/resourcegroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/endpoints/{endpoint_name}' \
                           f'/origingroups/{origin_group.lower()}'

        return OriginGroupOverrideAction(
            parameters=OriginGroupOverrideActionParameters(
                origin_group=ResourceReference(id=origin_group)
            ))

    return DeliveryRuleAction()


# pylint: disable=too-many-locals
def add_rule(cmd, client, resource_group_name, profile_name, endpoint_name,
             order, action_name, match_variable=None, operator=None,
             match_values=None, selector=None, negate_condition=None, transform=None,
             cache_behavior=None, cache_duration=None, header_action=None,
             header_name=None, header_value=None, query_string_behavior=None, query_parameters=None,
             redirect_type=None, redirect_protocol=None, custom_hostname=None, custom_path=None,
             custom_querystring=None, custom_fragment=None, source_pattern=None,
             destination=None, preserve_unmatched_path=None, rule_name=None, origin_group=None):

    partner_skus = [SkuName.PREMIUM_VERIZON, SkuName.CUSTOM_VERIZON, SkuName.STANDARD_AKAMAI, SkuName.STANDARD_VERIZON]
    profile = client.profiles.get(resource_group_name, profile_name)
    if rule_name is None and profile.sku.name not in partner_skus:
        raise CLIError("--rule-name is required for Microsoft SKU")

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)

    policy = endpoint.delivery_policy
    if policy is None:
        policy = EndpointPropertiesUpdateParametersDeliveryPolicy(
            description='delivery_policy',
            rules=[])

    _convert_to_unified_delivery_rules(policy)

    conditions = []
    condition = create_condition(match_variable, operator, match_values, selector, negate_condition, transform)
    if condition is not None:
        conditions.append(condition)
    actions = []
    action = create_action(action_name, cache_behavior, cache_duration, header_action, header_name,
                           header_value, query_string_behavior, query_parameters, redirect_type,
                           redirect_protocol, custom_hostname, custom_path, custom_querystring,
                           custom_fragment, source_pattern, destination, preserve_unmatched_path,
                           cmd, resource_group_name, profile_name, endpoint_name, origin_group)
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

    return client.endpoints.begin_update(resource_group_name, profile_name, endpoint_name, params)


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

    return client.endpoints.begin_update(resource_group_name, profile_name, endpoint_name, params)


def add_action(cmd, client, resource_group_name, profile_name, endpoint_name,
               rule_name, action_name, cache_behavior=None, cache_duration=None,
               header_action=None, header_name=None, header_value=None, query_string_behavior=None,
               query_parameters=None, redirect_type=None, redirect_protocol=None, custom_hostname=None,
               custom_path=None, custom_querystring=None, custom_fragment=None, source_pattern=None,
               destination=None, preserve_unmatched_path=None, origin_group=None):

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    action = create_action(action_name, cache_behavior, cache_duration, header_action, header_name,
                           header_value, query_string_behavior, query_parameters, redirect_type,
                           redirect_protocol, custom_hostname, custom_path, custom_querystring,
                           custom_fragment, source_pattern, destination, preserve_unmatched_path,
                           cmd, resource_group_name, profile_name, endpoint_name, origin_group)
    for i in range(0, len(policy.rules)):
        if policy.rules[i].name == rule_name:
            policy.rules[i].actions.append(action)

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.begin_update(resource_group_name, profile_name, endpoint_name, params)


def remove_rule(client, resource_group_name, profile_name, endpoint_name, rule_name=None, order: int = None):

    if rule_name is None and order is None:
        raise CLIError("Either --rule-name or --order must be specified")

    if order is not None and order < 0:
        raise CLIError("Order should be non-negative.")

    endpoint = client.endpoints.get(resource_group_name, profile_name, endpoint_name)
    policy = endpoint.delivery_policy
    if policy is not None:
        _convert_to_unified_delivery_rules(policy)
        pop_index = -1
        for idx, rule in enumerate(policy.rules):
            if rule_name is not None and rule.name == rule_name:
                pop_index = idx
                break
            if order is not None and rule.order == order:
                pop_index = idx
                break

        # To guarantee the consecutive rule order, we need to make sure the rule with order larger than the deleted one
        # to decrease its order by one. Rule with order 0 is special and no rule order adjustment is required.
        if pop_index != -1:
            pop_order = policy.rules[pop_index].order
            policy.rules.pop(pop_index)
            for rule in policy.rules:
                if rule.order > pop_order and pop_order != 0:
                    rule.order -= 1

    else:
        logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")

    params = EndpointUpdateParameters(
        delivery_policy=policy
    )

    return client.endpoints.begin_update(resource_group_name, profile_name, endpoint_name, params)


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

    return client.endpoints.begin_update(resource_group_name, profile_name, endpoint_name, params)


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

    return client.endpoints.begin_update(resource_group_name, profile_name, endpoint_name, params)


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

    return sdk_no_wait(no_wait, client.endpoints.begin_create, resource_group_name, profile_name, name, endpoint)


def purge_endpoint_content(client, resource_group_name, profile_name, endpoint_name,
                           content_paths, no_wait=None):
    purge_paramters = PurgeParameters(content_paths=content_paths)

    return sdk_no_wait(no_wait, client.endpoints.begin_purge_content, resource_group_name,
                       profile_name, endpoint_name, purge_paramters)


def load_endpoint_content(client, resource_group_name, profile_name, endpoint_name,
                          content_paths, no_wait=None):
    load_paramters = LoadParameters(content_paths=content_paths)

    return sdk_no_wait(no_wait, client.endpoints.begin_load_content, resource_group_name, profile_name,
                       endpoint_name, load_paramters)


# pylint: disable=unused-argument
def create_custom_domain(client, resource_group_name, profile_name, endpoint_name, custom_domain_name,
                         hostname, location=None, tags=None):

    return client.custom_domains.begin_create(resource_group_name,
                                              profile_name,
                                              endpoint_name,
                                              custom_domain_name,
                                              CustomDomainParameters(host_name=hostname))


def enable_custom_https(cmd, client, resource_group_name, profile_name, endpoint_name,
                        custom_domain_name, user_cert_subscription_id=None, user_cert_group_name=None,
                        user_cert_vault_name=None, user_cert_secret_name=None, user_cert_secret_version=None,
                        user_cert_protocol_type=None, min_tls_version=None):

    from azure.mgmt.cdn.models import (CdnCertificateSourceParameters,
                                       UserManagedHttpsParameters,
                                       CdnManagedHttpsParameters,
                                       KeyVaultCertificateSourceParameters,
                                       CertificateType,
                                       Profile,
                                       ProtocolType,
                                       UpdateRule,
                                       DeleteRule)

    profile: Profile = client.profiles.get(resource_group_name, profile_name)

    if min_tls_version is not None and min_tls_version.casefold() == 'none'.casefold():
        min_tls_version = MinimumTlsVersion.none
    elif min_tls_version == '1.0':
        min_tls_version = MinimumTlsVersion.tls10
    elif min_tls_version == '1.2':
        min_tls_version = MinimumTlsVersion.tls12

    # Are we using BYOC?
    if any(x is not None for x in [user_cert_subscription_id,
                                   user_cert_group_name,
                                   user_cert_vault_name,
                                   user_cert_secret_name,
                                   user_cert_secret_version,
                                   user_cert_protocol_type]):

        # If any BYOC flags are set, make sure they all are (except secret version).
        if any(x is None for x in [user_cert_group_name,
                                   user_cert_vault_name,
                                   user_cert_secret_name,
                                   user_cert_protocol_type]):
            raise CLIError("--user-cert-group-name, --user-cert-vault-name, --user-cert-secret-name, "
                           "and --user-cert-protocol-type are all required for user managed certificates.")

        if user_cert_subscription_id is None:
            user_cert_subscription_id = get_subscription_id(cmd.cli_ctx)

        # All BYOC params are set, let's create the https parameters
        if user_cert_protocol_type is None or user_cert_protocol_type.lower() == 'sni':
            user_cert_protocol_type = ProtocolType.server_name_indication
        elif user_cert_protocol_type.lower() == 'ip':
            user_cert_protocol_type = ProtocolType.ip_based
        else:
            raise CLIError("--user-cert-protocol-type is invalid")

        cert_source_params = KeyVaultCertificateSourceParameters(subscription_id=user_cert_subscription_id,
                                                                 resource_group_name=user_cert_group_name,
                                                                 vault_name=user_cert_vault_name,
                                                                 secret_name=user_cert_secret_name,
                                                                 secret_version=user_cert_secret_version,
                                                                 update_rule=UpdateRule.NO_ACTION,
                                                                 delete_rule=DeleteRule.NO_ACTION)

        https_params = UserManagedHttpsParameters(protocol_type=user_cert_protocol_type,
                                                  certificate_source_parameters=cert_source_params,
                                                  minimum_tls_version=min_tls_version)

    else:
        # We're using a CDN-managed certificate, let's create the right https
        # parameters for the profile SKU

        # Microsoft parameters
        if profile.sku.name == SkuName.standard_microsoft:
            cert_source_params = CdnCertificateSourceParameters(certificate_type=CertificateType.dedicated)
            https_params = CdnManagedHttpsParameters(protocol_type=ProtocolType.server_name_indication,
                                                     certificate_source_parameters=cert_source_params,
                                                     minimum_tls_version=min_tls_version)
        # Akamai parameters
        elif profile.sku.name == SkuName.standard_akamai:
            cert_source_params = CdnCertificateSourceParameters(certificate_type=CertificateType.shared)
            https_params = CdnManagedHttpsParameters(protocol_type=ProtocolType.server_name_indication,
                                                     certificate_source_parameters=cert_source_params,
                                                     minimum_tls_version=min_tls_version)
        # Verizon parameters
        else:
            cert_source_params = CdnCertificateSourceParameters(certificate_type=CertificateType.shared)
            https_params = CdnManagedHttpsParameters(protocol_type=ProtocolType.ip_based,
                                                     certificate_source_parameters=cert_source_params,
                                                     minimum_tls_version=min_tls_version)

    client.custom_domains.enable_custom_https(resource_group_name,
                                              profile_name,
                                              endpoint_name,
                                              custom_domain_name,
                                              https_params)

    updated = client.custom_domains.get(resource_group_name,
                                        profile_name,
                                        endpoint_name,
                                        custom_domain_name)

    return updated


def update_origin(client: OriginsOperations,
                  resource_group_name: str,
                  profile_name: str,
                  endpoint_name: str,
                  origin_name: str,
                  host_name: Optional[str] = None,
                  http_port: Optional[int] = None,
                  https_port: Optional[int] = None,
                  disabled: Optional[bool] = None,
                  origin_host_header: Optional[str] = None,
                  priority: Optional[int] = None,
                  weight: Optional[int] = None,
                  private_link_resource_id: Optional[str] = None,
                  private_link_location: Optional[str] = None,
                  private_link_approval_message: Optional[str] = None):
    from azure.mgmt.cdn.models import OriginUpdateParameters

    return client.begin_update(resource_group_name,
                               profile_name,
                               endpoint_name,
                               origin_name,
                               OriginUpdateParameters(
                                   host_name=host_name,
                                   http_port=http_port,
                                   https_port=https_port,
                                   enabled=not disabled,
                                   origin_host_header=origin_host_header,
                                   priority=priority,
                                   weight=weight,
                                   private_link_resource_id=private_link_resource_id,
                                   private_link_location=private_link_location,
                                   private_link_approval_message=private_link_approval_message))


def create_origin(client: OriginsOperations,
                  resource_group_name: str,
                  profile_name: str,
                  endpoint_name: str,
                  origin_name: str,
                  host_name: str,
                  disabled: bool = False,
                  http_port: int = 80,
                  https_port: int = 443,
                  origin_host_header: Optional[str] = None,
                  priority: int = 1,
                  weight: int = 1000,
                  private_link_resource_id: Optional[str] = None,
                  private_link_location: Optional[str] = None,
                  private_link_approval_message: Optional[str] = None):
    from azure.mgmt.cdn.models import Origin

    return client.begin_create(resource_group_name,
                               profile_name,
                               endpoint_name,
                               origin_name,
                               Origin(
                                   host_name=host_name,
                                   http_port=http_port,
                                   https_port=https_port,
                                   enabled=not disabled,
                                   origin_host_header=origin_host_header,
                                   priority=priority,
                                   weight=weight,
                                   private_link_resource_id=private_link_resource_id,
                                   private_link_location=private_link_location,
                                   private_link_approval_message=private_link_approval_message))


def update_profile(instance, tags=None):
    if instance.sku.name in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
        logger.warning('Standard_AzureFrontDoor and Premium_AzureFrontDoor are only supported for AFD profiles')
        raise ResourceNotFoundError("Operation returned an invalid status code 'Not Found'")

    params = ProfileUpdateParameters(tags=tags)
    _update_mapper(instance, params, ['tags'])
    return params


def create_profile(client, resource_group_name, name,
                   sku=SkuName.standard_akamai.value,
                   location=None, tags=None):
    from azure.mgmt.cdn.models import (Profile, Sku)
    profile = Profile(location=location, sku=Sku(name=sku), tags=tags)
    return client.profiles.begin_create(resource_group_name, name, profile)


def _parse_ranges(ranges: str):
    if ranges is None:
        return []

    from azure.mgmt.cdn.models import HttpErrorRangeParameters

    def parse_range(error_range: str):
        split = error_range.split('-')
        if not split or len(split) > 2:
            raise CLIError(f'range "{error_range}" is invalid')

        try:
            begin = split[0]
            end = split[1] if len(split) == 2 else begin
        except ValueError:
            raise CLIError(f'range "{error_range}" is invalid')

        return HttpErrorRangeParameters(being=begin, end=end)

    return [parse_range(error_range) for error_range in ranges.split(',')]


def create_origin_group(cmd,
                        client: OriginGroupsOperations,
                        resource_group_name: str,
                        profile_name: str,
                        endpoint_name: str,
                        name: str,
                        probe_path: Optional[str] = None,
                        probe_method: str = "HEAD",
                        probe_protocol: str = "HTTP",
                        probe_interval: int = 240,
                        origins: Optional[str] = None):

    # Move these to the parameters list once support is added in RP:
    response_error_detection_error_types: Optional[str] = None
    response_error_detection_failover_threshold: Optional[int] = None
    response_error_detection_status_code_ranges: Optional[str] = None

    from azure.mgmt.cdn.models import (OriginGroup,
                                       HealthProbeParameters,
                                       ResponseBasedOriginErrorDetectionParameters)

    health_probe_settings = HealthProbeParameters(probe_path=probe_path,
                                                  probe_request_type=HealthProbeRequestType[probe_method.upper()],
                                                  probe_protocol=ProbeProtocol[probe_protocol.upper()],
                                                  probe_interval_in_seconds=probe_interval)

    error_types = None
    if response_error_detection_error_types:
        error_types = response_error_detection_error_types.split(',')

    error_detection_settings = None
    if response_error_detection_error_types or \
       response_error_detection_failover_threshold or \
       response_error_detection_status_code_ranges:
        error_detection_settings = ResponseBasedOriginErrorDetectionParameters(
            response_based_detected_error_types=error_types,
            response_based_failover_threshold_percentage=response_error_detection_failover_threshold,
            http_error_ranges=_parse_ranges(response_error_detection_status_code_ranges))

    formatted_origins = []
    subscription_id = get_subscription_id(cmd.cli_ctx)
    if origins:
        for origin in origins.split(','):
            # If the origin is not an ID, assume it's a name and format it as an ID.
            if '/' not in origin:
                origin = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                         f'/providers/Microsoft.Cdn/profiles/{profile_name}/endpoints/{endpoint_name}' \
                         f'/origins/{origin}'
            formatted_origins.append(ResourceReference(id=origin))

    origin_group = OriginGroup(origins=formatted_origins,
                               health_probe_settings=health_probe_settings,
                               response_based_origin_error_detection_settings=error_detection_settings)

    return client.begin_create(resource_group_name,
                               profile_name,
                               endpoint_name,
                               name,
                               origin_group).result()


def update_origin_group(cmd,
                        client: OriginGroupsOperations,
                        resource_group_name: str,
                        profile_name: str,
                        endpoint_name: str,
                        name: str,
                        probe_path: str = None,
                        probe_method: str = None,
                        probe_protocol: str = None,
                        probe_interval: int = None,
                        origins: str = None):

    # Move these to the parameters list once support is added in RP:
    error_types: Optional[str] = None
    failover_threshold: Optional[int] = None
    status_code_ranges: Optional[str] = None

    from azure.mgmt.cdn.models import (OriginGroupUpdateParameters,
                                       HealthProbeParameters,
                                       ResponseBasedOriginErrorDetectionParameters)

    if probe_method is not None:
        probe_method = HealthProbeRequestType[probe_method.upper()]

    if probe_protocol is not None:
        probe_protocol = ProbeProtocol[probe_protocol.upper()]

    # Get existing health probe settings:
    existing = client.get(resource_group_name,
                          profile_name,
                          endpoint_name,
                          name)
    # Allow removing properties explicitly by specifying as empty string, or
    # update without modifying by not specifying (value is None).
    if probe_path == '':
        probe_path = None
    elif probe_path is None:
        probe_path = existing.health_probe_settings.probe_path
    if probe_method == '':
        probe_method = None
    elif probe_method is None:
        probe_method = existing.health_probe_settings.probe_request_type
    if probe_protocol == '':
        probe_protocol = None
    elif probe_protocol is None:
        probe_protocol = existing.health_probe_settings.probe_protocol
    if probe_interval == '':
        probe_interval = None
    elif probe_interval is None:
        probe_interval = existing.health_probe_settings.probe_interval_in_seconds
    origins = origins or existing.origins

    health_probe_settings = HealthProbeParameters(probe_path=probe_path,
                                                  probe_request_type=probe_method,
                                                  probe_protocol=probe_protocol,
                                                  probe_interval_in_seconds=probe_interval)

    if error_types is not None:
        error_types = error_types.split(',')
    if status_code_ranges is not None:
        status_code_ranges = _parse_ranges(status_code_ranges)

    error_detection_settings = None
    if error_types or \
       failover_threshold or \
       status_code_ranges:
        error_detection_settings = ResponseBasedOriginErrorDetectionParameters(
            response_based_detected_error_types=error_types,
            response_based_failover_threshold_percentage=failover_threshold,
            http_error_ranges=status_code_ranges)

    formatted_origins = []
    subscription_id = get_subscription_id(cmd.cli_ctx)
    for origin in origins.split(','):
        # If the origin is not an ID, assume it's a name and format it as an ID.
        if '/' not in origin:
            origin = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                     f'/providers/Microsoft.Cdn/profiles/{profile_name}/endpoints/{endpoint_name}' \
                     f'/origins/{origin}'
        formatted_origins.append(ResourceReference(id=origin))

    origin_group = OriginGroupUpdateParameters(
        origins=formatted_origins,
        health_probe_settings=health_probe_settings,
        response_based_origin_error_detection_settings=error_detection_settings)

    # client.begin_create isn't really a create, it's a PUT which is create or update,
    # client.begin_update doesn't allow unsetting fields.
    return client.begin_create(resource_group_name,
                               profile_name,
                               endpoint_name,
                               name,
                               origin_group)
# endregion
