# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import (Optional, List)
from azure.mgmt.cdn.models import (AFDEndpoint, HealthProbeRequestType, EnabledState, Route, LinkToDefaultDomain,
                                   ResourceReference, AFDEndpointProtocols, HttpsRedirect, ForwardingProtocol,
                                   QueryStringCachingBehavior, HealthProbeParameters, MatchProcessingBehavior,
                                   AFDOrigin, AFDOriginGroup, SharedPrivateLinkResourceProperties, CompressionSettings,
                                   LoadBalancingSettingsParameters, SecurityPolicyWebApplicationFirewallParameters,
                                   SecurityPolicyWebApplicationFirewallAssociation, CustomerCertificateParameters,
                                   AFDDomain, AFDDomainHttpsParameters, AfdCertificateType, AfdMinimumTlsVersion,
                                   AFDEndpointUpdateParameters, SkuName, AfdPurgeParameters, Secret,
                                   SecurityPolicy, ProfileUpdateParameters)

from azure.mgmt.cdn.operations import (AFDOriginGroupsOperations, AFDOriginsOperations, AFDProfilesOperations,
                                       SecretsOperations, AFDEndpointsOperations, RoutesOperations, RuleSetsOperations,
                                       RulesOperations, SecurityPoliciesOperations, AFDCustomDomainsOperations,
                                       ProfilesOperations)

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import (sdk_no_wait)
from azure.cli.core.azclierror import (InvalidArgumentValueError)
from azure.core.exceptions import (ResourceNotFoundError)

from knack.log import get_logger
from msrest.polling import LROPoller, NoPolling

from .custom import _update_mapper

logger = get_logger(__name__)


def default_content_types():
    return ["application/eot",
            "application/font",
            "application/font-sfnt",
            "application/javascript",
            "application/json",
            "application/opentype",
            "application/otf",
            "application/pkcs7-mime",
            "application/truetype",
            "application/ttf",
            "application/vnd.ms-fontobject",
            "application/xhtml+xml",
            "application/xml",
            "application/xml+rss",
            "application/x-font-opentype",
            "application/x-font-truetype",
            "application/x-font-ttf",
            "application/x-httpd-cgi",
            "application/x-javascript",
            "application/x-mpegurl",
            "application/x-opentype",
            "application/x-otf",
            "application/x-perl",
            "application/x-ttf",
            "font/eot",
            "font/ttf",
            "font/otf",
            "font/opentype",
            "image/svg+xml",
            "text/css",
            "text/csv",
            "text/html",
            "text/javascript",
            "text/js",
            "text/plain",
            "text/richtext",
            "text/tab-separated-values",
            "text/xml",
            "text/x-script",
            "text/x-component",
            "text/x-java-source"]


def create_afd_profile(client: ProfilesOperations, resource_group_name, profile_name,
                       sku: SkuName,
                       tags=None):
    from azure.mgmt.cdn.models import (Profile, Sku)

    # Force location to global
    profile = Profile(location="global", sku=Sku(name=sku), tags=tags)
    return client.begin_create(resource_group_name, profile_name, profile)


def delete_afd_profile(client: ProfilesOperations, resource_group_name, profile_name):
    profile = None
    try:
        profile = client.get(resource_group_name, profile_name)
    except ResourceNotFoundError:
        pass

    if profile is None or profile.sku.name not in (SkuName.premium_azure_front_door,
                                                   SkuName.standard_azure_front_door):
        def get_long_running_output(_):
            return None

        logger.warning("Unexpected SKU type, only Standard_AzureFrontDoor and Premium_AzureFrontDoor are supported.")
        return LROPoller(client, None, get_long_running_output, NoPolling())

    return client.begin_delete(resource_group_name, profile_name)


def update_afd_profile(client: ProfilesOperations, resource_group_name, profile_name, tags):
    profile = client.get(resource_group_name, profile_name)
    if profile.sku.name not in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
        logger.warning('Unexpected SKU type, only Standard_AzureFrontDoor and Premium_AzureFrontDoor are supported')
        raise ResourceNotFoundError("Operation returned an invalid status code 'Not Found'")

    return client.begin_update(resource_group_name, profile_name, ProfileUpdateParameters(tags=tags))


def list_afd_profiles(client: ProfilesOperations, resource_group_name=None):
    profile_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()

    profile_list = [profile for profile in profile_list if profile.sku.name in
                    (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door)]

    return list(profile_list)


def get_afd_profile(client: ProfilesOperations, resource_group_name, profile_name):
    profile = client.get(resource_group_name, profile_name)
    if profile.sku.name not in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
        # Workaround to make the behavior consist with true "Not Found"
        logger.warning('Unexpected SKU type, only Standard_AzureFrontDoor and Premium_AzureFrontDoor are supported')
        raise ResourceNotFoundError("Operation returned an invalid status code 'Not Found'")

    return profile


def list_resource_usage(client: AFDProfilesOperations, resource_group_name, profile_name):
    return client.list_resource_usage(resource_group_name, profile_name)


def create_afd_endpoint(client: AFDEndpointsOperations, resource_group_name, profile_name, endpoint_name,
                        origin_response_timeout_seconds,
                        enabled_state, tags=None, no_wait=None):

    # Force location to global
    endpoint = AFDEndpoint(location="global",
                           origin_response_timeout_seconds=origin_response_timeout_seconds,
                           enabled_state=enabled_state,
                           tags=tags)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, profile_name, endpoint_name, endpoint)


def purge_afd_endpoint_content(client: AFDEndpointsOperations, resource_group_name, profile_name, endpoint_name,
                               content_paths, domains=None, no_wait=None):
    endpoint = AfdPurgeParameters(content_paths=content_paths,
                                  domains=domains)

    return sdk_no_wait(no_wait, client.begin_purge_content, resource_group_name, profile_name, endpoint_name, endpoint)


def update_afd_endpoint(client: AFDEndpointsOperations, resource_group_name, profile_name, endpoint_name,
                        origin_response_timeout_seconds=None, enabled_state=None, tags=None):
    update_properties = AFDEndpointUpdateParameters(
        origin_response_timeout_seconds=origin_response_timeout_seconds,
        enabled_state=enabled_state,
        tags=tags
    )

    return client.begin_update(resource_group_name, profile_name, endpoint_name, update_properties)


def create_afd_origin_group(client: AFDOriginGroupsOperations,
                            resource_group_name: str,
                            profile_name: str,
                            origin_group_name: str,
                            load_balancing_sample_size: int,
                            load_balancing_successful_samples_required: int,
                            load_balancing_additional_latency_in_milliseconds: int,
                            probe_request_type: HealthProbeRequestType,
                            probe_protocol: str,
                            probe_path: str,
                            probe_interval_in_seconds: int = 240):

    # Add response error detection support once RP support it.
    health_probe_parameters = HealthProbeParameters(probe_path=probe_path,
                                                    probe_request_type=probe_request_type,
                                                    probe_protocol=probe_protocol,
                                                    probe_interval_in_seconds=probe_interval_in_seconds)

    load_balancing_settings_parameters = LoadBalancingSettingsParameters(
        sample_size=load_balancing_sample_size,
        successful_samples_required=load_balancing_successful_samples_required,
        additional_latency_in_milliseconds=load_balancing_additional_latency_in_milliseconds)

    afd_origin_group = AFDOriginGroup(load_balancing_settings=load_balancing_settings_parameters,
                                      health_probe_settings=health_probe_parameters)

    return client.begin_create(resource_group_name,
                               profile_name,
                               origin_group_name,
                               afd_origin_group).result()


def update_afd_origin_group(client: AFDOriginGroupsOperations,
                            resource_group_name: str,
                            profile_name: str,
                            origin_group_name: str,
                            load_balancing_sample_size: int = None,
                            load_balancing_successful_samples_required: int = None,
                            load_balancing_additional_latency_in_milliseconds: int = None,
                            probe_request_type: HealthProbeRequestType = None,
                            probe_protocol: str = None,
                            probe_path: str = None,
                            probe_interval_in_seconds: int = None):

    # Move these to the parameters list once support is added in RP.
    existing = client.get(resource_group_name, profile_name, origin_group_name)

    health_probe_parameters = HealthProbeParameters(probe_path=probe_path,
                                                    probe_request_type=probe_request_type,
                                                    probe_protocol=probe_protocol,
                                                    probe_interval_in_seconds=probe_interval_in_seconds)

    _update_mapper(existing.health_probe_settings,
                   health_probe_parameters,
                   ["probe_path", "probe_request_type", "probe_protocol", "probe_interval_in_seconds"])

    load_balancing_settings_parameters = LoadBalancingSettingsParameters(
        sample_size=load_balancing_sample_size,
        successful_samples_required=load_balancing_successful_samples_required,
        additional_latency_in_milliseconds=load_balancing_additional_latency_in_milliseconds)
    _update_mapper(existing.load_balancing_settings,
                   load_balancing_settings_parameters,
                   ["sample_size", "successful_samples_required", "additional_latency_in_milliseconds"])

    afd_origin_group = AFDOriginGroup(load_balancing_settings=load_balancing_settings_parameters,
                                      health_probe_settings=health_probe_parameters)

    return client.begin_create(resource_group_name,
                               profile_name,
                               origin_group_name,
                               afd_origin_group).result()


def create_afd_origin(client: AFDOriginsOperations,
                      resource_group_name: str,
                      profile_name: str,
                      origin_group_name: str,
                      origin_name: str,
                      host_name: str,
                      enabled_state: EnabledState,
                      enable_private_link: bool = None,
                      private_link_resource: str = None,
                      private_link_location: str = None,
                      private_link_sub_resource_type: str = None,
                      private_link_request_message: str = None,
                      http_port: int = 80,
                      https_port: int = 443,
                      origin_host_header: Optional[str] = None,
                      priority: int = 1,
                      weight: int = 1000):

    shared_private_link_resource = None
    if enable_private_link:
        shared_private_link_resource = SharedPrivateLinkResourceProperties(
            private_link=ResourceReference(id=private_link_resource),
            private_link_location=private_link_location,
            group_id=private_link_sub_resource_type,
            request_message=private_link_request_message)

    return client.begin_create(resource_group_name,
                               profile_name,
                               origin_group_name,
                               origin_name,
                               AFDOrigin(
                                   host_name=host_name,
                                   http_port=http_port,
                                   https_port=https_port,
                                   origin_host_header=origin_host_header,
                                   priority=priority,
                                   weight=weight,
                                   shared_private_link_resource=shared_private_link_resource,
                                   enabled_state=enabled_state))


def update_afd_origin(client: AFDOriginsOperations,
                      resource_group_name: str,
                      profile_name: str,
                      origin_group_name: str,
                      origin_name: str,
                      host_name: str = None,
                      enabled_state: EnabledState = None,
                      http_port: int = None,
                      https_port: int = None,
                      origin_host_header: Optional[str] = None,
                      priority: int = None,
                      weight: int = None,
                      enable_private_link: bool = None,
                      private_link_resource: str = None,
                      private_link_location: str = None,
                      private_link_sub_resource_type: str = None,
                      private_link_request_message: str = None):

    existing = client.get(resource_group_name, profile_name, origin_group_name, origin_name)
    origin = AFDOrigin(
        host_name=host_name,
        http_port=http_port,
        https_port=https_port,
        origin_host_header=origin_host_header,
        priority=priority,
        weight=weight,
        enabled_state=enabled_state)

    _update_mapper(
        existing,
        origin,
        ["host_name", "http_port", "https_port", "origin_host_header", "priority", "weight", "enabled_state"])

    if enable_private_link is not None and not enable_private_link:
        origin.shared_private_link_resource = None
    elif (private_link_resource is not None or
          private_link_location is not None or
          private_link_sub_resource_type is not None or
          private_link_request_message is not None):
        shared_private_link_resource = SharedPrivateLinkResourceProperties(
            private_link=ResourceReference(id=private_link_resource) if private_link_resource is not None else None,
            private_link_location=private_link_location,
            group_id=private_link_sub_resource_type,
            request_message=private_link_request_message)

        if existing.shared_private_link_resource is not None:
            existing_shared_private_link_resource = SharedPrivateLinkResourceProperties(
                private_link=ResourceReference(id=existing.shared_private_link_resource["privateLink"]['id']),
                private_link_location=existing.shared_private_link_resource["privateLinkLocation"],
                group_id=existing.shared_private_link_resource["groupId"],
                request_message=existing.shared_private_link_resource["requestMessage"])

            _update_mapper(
                existing_shared_private_link_resource,
                shared_private_link_resource,
                ["private_link", "private_link_location", "group_id", "request_message"])

        origin.shared_private_link_resource = shared_private_link_resource
    else:
        origin.shared_private_link_resource = existing.shared_private_link_resource

    # client.update does not allow unset field
    return client.begin_create(resource_group_name,
                               profile_name,
                               origin_group_name,
                               origin_name,
                               origin)


def create_afd_route(cmd,
                     client: RoutesOperations,
                     resource_group_name: str,
                     profile_name: str,
                     endpoint_name: str,
                     route_name: str,
                     https_redirect: HttpsRedirect,
                     supported_protocols: List[AFDEndpointProtocols],
                     origin_group: str,
                     forwarding_protocol: ForwardingProtocol,
                     link_to_default_domain: LinkToDefaultDomain = None,
                     is_compression_enabled: bool = False,
                     content_types_to_compress: List[str] = None,
                     query_string_caching_behavior: QueryStringCachingBehavior = None,
                     custom_domains: List[str] = None,
                     origin_path: Optional[str] = None,
                     patterns_to_match: List[str] = None,
                     rule_sets: List[str] = None):

    subscription_id = get_subscription_id(cmd.cli_ctx)
    formatted_custom_domains = []
    if custom_domains is not None:
        for custom_domain in custom_domains:
            if '/customdomains/' not in custom_domain.lower():
                custom_domain = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                                f'/providers/Microsoft.Cdn/profiles/{profile_name}/customDomains/{custom_domain}'

            # If the origin is not an ID, assume it's a name and format it as an ID.
            formatted_custom_domains.append(ResourceReference(id=custom_domain))

    if '/origingroups/' not in origin_group.lower():
        origin_group = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                       f'/providers/Microsoft.Cdn/profiles/{profile_name}/originGroups/{origin_group}'

    compression_settings = CompressionSettings(
        content_types_to_compress=content_types_to_compress,
        is_compression_enabled=is_compression_enabled
    )

    if is_compression_enabled and content_types_to_compress is None:
        compression_settings.content_types_to_compress = default_content_types()

    if not compression_settings.is_compression_enabled:
        compression_settings.content_types_to_compress = []

    formatted_rule_sets = []
    if rule_sets is not None:
        for rule_set in rule_sets:
            if '/rulesets/' not in rule_set.lower():
                rule_set = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/ruleSets/{rule_set}'

            formatted_rule_sets.append(ResourceReference(id=rule_set))

    return client.begin_create(resource_group_name,
                               profile_name,
                               endpoint_name,
                               route_name,
                               Route(
                                   custom_domains=formatted_custom_domains,
                                   origin_path=origin_path,
                                   patterns_to_match=patterns_to_match if patterns_to_match is not None else ['/*'],
                                   supported_protocols=supported_protocols,
                                   https_redirect=https_redirect,
                                   origin_group=ResourceReference(id=origin_group),
                                   forwarding_protocol=forwarding_protocol,
                                   rule_sets=formatted_rule_sets,
                                   query_string_caching_behavior=query_string_caching_behavior,
                                   compression_settings=compression_settings,
                                   link_to_default_domain=LinkToDefaultDomain.enabled if link_to_default_domain else
                                   LinkToDefaultDomain.disabled))


def update_afd_route(cmd,
                     client: RoutesOperations,
                     resource_group_name: str,
                     profile_name: str,
                     endpoint_name: str,
                     route_name: str,
                     https_redirect: HttpsRedirect = None,
                     supported_protocols: List[AFDEndpointProtocols] = None,
                     origin_group: str = None,
                     forwarding_protocol: ForwardingProtocol = None,
                     link_to_default_domain: LinkToDefaultDomain = None,
                     is_compression_enabled: bool = None,
                     content_types_to_compress: List[str] = None,
                     query_string_caching_behavior: QueryStringCachingBehavior = None,
                     custom_domains: List[str] = None,
                     origin_path: Optional[str] = None,
                     patterns_to_match: List[str] = None,
                     rule_sets: List[str] = None):

    existing = client.get(resource_group_name, profile_name, endpoint_name, route_name)
    route = Route(
        origin_path=origin_path,
        origin_group=existing.origin_group,
        patterns_to_match=patterns_to_match,
        supported_protocols=supported_protocols,
        https_redirect=https_redirect,
        forwarding_protocol=forwarding_protocol,
        query_string_caching_behavior=query_string_caching_behavior,
        link_to_default_domain=link_to_default_domain)

    subscription_id = get_subscription_id(cmd.cli_ctx)
    if custom_domains is not None:
        formatted_custom_domains = []
        for custom_domain in custom_domains:
            if '/customdomains/' not in custom_domain.lower():
                custom_domain = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                                f'/providers/Microsoft.Cdn/profiles/{profile_name}/customDomains/{custom_domain}'

            # If the origin is not an ID, assume it's a name and format it as an ID.
            formatted_custom_domains.append(ResourceReference(id=custom_domain))

        route.custom_domains = formatted_custom_domains

    if origin_group is not None:
        if '/origingroups/' not in origin_group.lower():
            origin_group = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/originGroups/{origin_group}'

        route.origin_group = origin_group

    if rule_sets is not None:
        formatted_rule_sets = []
        for rule_set in rule_sets:
            if '/rulesets/' not in rule_set.lower():
                rule_set = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                           f'/providers/Microsoft.Cdn/profiles/{profile_name}/ruleSets/{rule_set}'

            # If the origin is not an ID, assume it's a name and format it as an ID.
            formatted_rule_sets.append(ResourceReference(id=rule_set))

        route.rule_sets = formatted_rule_sets

    _update_mapper(existing, route,
                   ["custom_domains", "origin_path", "patterns_to_match",
                    "supported_protocols", "https_redirect", "origin_group",
                    "forwarding_protocol", "rule_sets", "query_string_caching_behavior",
                    "link_to_default_domain", "compression_settings"])

    if is_compression_enabled:
        if existing.compression_settings is None:
            route.compression_settings = CompressionSettings(
                content_types_to_compress=content_types_to_compress if content_types_to_compress is not None else
                default_content_types(),
                is_compression_enabled=is_compression_enabled
            )
        else:
            route.compression_settings = CompressionSettings(
                content_types_to_compress=content_types_to_compress if content_types_to_compress is not None else
                existing.compression_settings.content_types_to_compress,
                is_compression_enabled=is_compression_enabled
            )
    elif is_compression_enabled is None:
        if content_types_to_compress is not None and existing.compression_settings is not None:
            route.compression_settings = CompressionSettings(
                content_types_to_compress=content_types_to_compress,
                is_compression_enabled=existing.compression_settings["isCompressionEnabled"]
            )
    else:
        route.compression_settings = CompressionSettings(
            content_types_to_compress=[],
            is_compression_enabled=False
        )

    return client.begin_create(resource_group_name,
                               profile_name,
                               endpoint_name,
                               route_name,
                               route)


def create_afd_rule_set(client: RuleSetsOperations,
                        resource_group_name: str,
                        profile_name: str,
                        rule_set_name: str):

    return client.begin_create(resource_group_name, profile_name, rule_set_name)


# pylint: disable=too-many-locals
def create_afd_rule(client: RulesOperations, resource_group_name, profile_name, rule_set_name,
                    order, rule_name, action_name, match_variable=None, operator=None,
                    match_values=None, selector=None, negate_condition=None, transform=None,
                    cache_behavior=None, cache_duration=None, header_action=None,
                    header_name=None, header_value=None, query_string_behavior=None, query_parameters=None,
                    redirect_type=None, redirect_protocol=None, custom_hostname=None, custom_path=None,
                    custom_querystring=None, custom_fragment=None, source_pattern=None,
                    destination=None, preserve_unmatched_path=None,
                    match_processing_behavior: MatchProcessingBehavior = None):
    from azure.mgmt.cdn.models import Rule
    from .custom import create_condition
    from .custom import create_action

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

    rule = Rule(
        name=rule_name,
        order=order,
        conditions=conditions,
        actions=actions,
        match_processing_behavior=match_processing_behavior
    )

    return client.begin_create(resource_group_name,
                               profile_name,
                               rule_set_name,
                               rule_name,
                               rule=rule)


def add_afd_rule_condition(client: RulesOperations, resource_group_name, profile_name, rule_set_name,
                           rule_name, match_variable, operator, match_values=None, selector=None,
                           negate_condition=None, transform=None):
    from .custom import create_condition

    existing_rule = client.get(resource_group_name, profile_name, rule_set_name, rule_name)
    condition = create_condition(match_variable, operator, match_values, selector, negate_condition, transform)
    existing_rule.conditions.append(condition)

    return client.begin_create(resource_group_name,
                               profile_name,
                               rule_set_name,
                               rule_name,
                               rule=existing_rule)


def add_afd_rule_action(client: RulesOperations, resource_group_name, profile_name, rule_set_name,
                        rule_name, action_name, cache_behavior=None, cache_duration=None,
                        header_action=None, header_name=None, header_value=None, query_string_behavior=None,
                        query_parameters=None, redirect_type=None, redirect_protocol=None, custom_hostname=None,
                        custom_path=None, custom_querystring=None, custom_fragment=None, source_pattern=None,
                        destination=None, preserve_unmatched_path=None):
    from .custom import create_action

    existing_rule = client.get(resource_group_name, profile_name, rule_set_name, rule_name)
    action = create_action(action_name, cache_behavior, cache_duration, header_action, header_name,
                           header_value, query_string_behavior, query_parameters, redirect_type,
                           redirect_protocol, custom_hostname, custom_path, custom_querystring,
                           custom_fragment, source_pattern, destination, preserve_unmatched_path)

    existing_rule.actions.append(action)
    return client.begin_create(resource_group_name,
                               profile_name,
                               rule_set_name,
                               rule_name,
                               rule=existing_rule)


def remove_afd_rule_condition(client: RulesOperations, resource_group_name, profile_name,
                              rule_set_name, rule_name, index):
    existing_rule = client.get(resource_group_name, profile_name, rule_set_name, rule_name)
    if len(existing_rule.conditions) > 1 and index < len(existing_rule.conditions):
        existing_rule.conditions.pop(index)
    else:
        logger.warning("Invalid condition index found. This command will be skipped. Please check the rule.")

    return client.begin_create(resource_group_name,
                               profile_name,
                               rule_set_name,
                               rule_name,
                               rule=existing_rule)


def remove_afd_rule_action(client: RulesOperations, resource_group_name, profile_name, rule_set_name, rule_name, index):
    existing_rule = client.get(resource_group_name, profile_name, rule_set_name, rule_name)
    if len(existing_rule.actions) > 1 and index < len(existing_rule.actions):
        existing_rule.actions.pop(index)
    else:
        logger.warning("Invalid condition index found. This command will be skipped. Please check the rule.")

    return client.begin_create(resource_group_name,
                               profile_name,
                               rule_set_name,
                               rule_name,
                               rule=existing_rule)


def list_afd_rule_condition(client: RulesOperations, resource_group_name,
                            profile_name, rule_set_name,
                            rule_name):
    rule = client.get(resource_group_name, profile_name, rule_set_name, rule_name)
    return rule.conditions


def list_afd_rule_action(client: RulesOperations, resource_group_name,
                         profile_name, rule_set_name,
                         rule_name):
    rule = client.get(resource_group_name, profile_name, rule_set_name, rule_name)
    return rule.actions


def create_afd_security_policy(client: SecurityPoliciesOperations,
                               resource_group_name,
                               profile_name,
                               security_policy_name,
                               domains: List[str],
                               waf_policy: str):

    if any(("/afdendpoints/" not in domain.lower() and
            "/customdomains/" not in domain.lower()) for domain in domains):
        raise InvalidArgumentValueError('Domain should either be endpoint ID or custom domain ID.')

    if "/frontdoorwebapplicationfirewallpolicies/" not in waf_policy.lower():
        raise InvalidArgumentValueError('waf_policy should be valid Front Door WAF policy ID.')

    # Add patterns and multiple domains support in the feature
    parameters = SecurityPolicyWebApplicationFirewallParameters(
        waf_policy=ResourceReference(id=waf_policy),
        associations=[SecurityPolicyWebApplicationFirewallAssociation(
            domains=[ResourceReference(id=domain) for domain in domains],
            patterns_to_match=["/*"])])

    return client.begin_create(resource_group_name,
                               profile_name,
                               security_policy_name,
                               SecurityPolicy(parameters=parameters))


def update_afd_security_policy(client: SecurityPoliciesOperations,
                               resource_group_name,
                               profile_name,
                               security_policy_name,
                               domains: List[str] = None,
                               waf_policy: str = None):

    if domains is not None and any(("/afdendpoints/" not in domain.lower() and
                                    "/customdomains/" not in domain.lower()) for domain in domains):
        raise InvalidArgumentValueError('Domain should be either endpoint ID or custom domain ID.')

    if waf_policy is not None and "/frontdoorwebapplicationfirewallpolicies/" not in waf_policy:
        raise InvalidArgumentValueError('waf_policy should be Front Door WAF policy ID.')

    existing = client.get(resource_group_name, profile_name, security_policy_name)

    # Add patterns and multiple domains support in the future
    parameters = SecurityPolicyWebApplicationFirewallParameters(
        waf_policy=ResourceReference(id=waf_policy) if waf_policy is not None else existing.parameters.waf_policy,
        associations=[SecurityPolicyWebApplicationFirewallAssociation(
            domains=[ResourceReference(id=domain) for domain in domains],
            patterns_to_match=["/*"])] if domains is not None else existing.parameters.associations)

    return client.begin_create(resource_group_name,
                               profile_name,
                               security_policy_name,
                               SecurityPolicy(parameters=parameters))


def create_afd_secret(client: SecretsOperations,
                      resource_group_name,
                      profile_name,
                      secret_name,
                      secret_source,
                      secret_version: str = None,
                      use_latest_version: bool = None):

    if "/certificates/" not in secret_source.lower():
        raise InvalidArgumentValueError('secret_source should be valid Azure key vault certificate ID.')

    if secret_version is None and not use_latest_version:
        raise InvalidArgumentValueError('Either specify secret_version or enable use_latest_version.')

    # Only support CustomerCertificate for the moment
    parameters = None
    if use_latest_version:
        parameters = CustomerCertificateParameters(
            secret_source=ResourceReference(id=secret_source),
            secret_version=None,
            use_latest_version=True
        )
    else:
        parameters = CustomerCertificateParameters(
            secret_source=ResourceReference(id=f'{secret_source}/{secret_version}'),
            secret_version=secret_version,
            use_latest_version=False
        )

    return client.begin_create(resource_group_name,
                               profile_name,
                               secret_name,
                               Secret(parameters=parameters))


def update_afd_secret(client: SecretsOperations,
                      resource_group_name,
                      profile_name,
                      secret_name,
                      secret_source: str = None,
                      secret_version: str = None,
                      use_latest_version: bool = None):
    existing = client.get(resource_group_name, profile_name, secret_name)

    secret_source_id = secret_source if secret_source is not None else existing.parameters.secret_source.id
    if existing.parameters.secret_version is not None and existing.parameters.secret_version in secret_source_id:
        version_start = secret_source_id.lower().rindex(f'/{existing.parameters.secret_version}')
        secret_source_id = secret_source_id[0:version_start]

    secret_version = (secret_version if secret_version is not None
                      else existing.parameters.secret_version)

    use_latest_version = (use_latest_version if use_latest_version is not None
                          else existing.parameters.use_latest_version)

    return create_afd_secret(client,
                             resource_group_name,
                             profile_name,
                             secret_name,
                             secret_source_id,
                             secret_version,
                             use_latest_version)


def create_afd_custom_domain(cmd,
                             client: AFDCustomDomainsOperations,
                             resource_group_name: str,
                             profile_name: str,
                             custom_domain_name: str,
                             host_name: str,
                             certificate_type: AfdCertificateType,
                             minimum_tls_version: AfdMinimumTlsVersion,
                             azure_dns_zone: str = None,
                             secret: str = None,
                             no_wait: bool = None):

    if azure_dns_zone is not None and "/dnszones/" not in azure_dns_zone.lower():
        raise InvalidArgumentValueError('azure_dns_zone should be valid Azure dns zone ID.')

    subscription_id = get_subscription_id(cmd.cli_ctx)
    if secret is not None and "/secrets/" not in secret.lower():
        secret = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                 f'/providers/Microsoft.Cdn/profiles/{profile_name}/secrets/{secret}'

    tls_settings = AFDDomainHttpsParameters(certificate_type=certificate_type,
                                            minimum_tls_version=minimum_tls_version,
                                            secret=ResourceReference(id=secret) if secret is not None else None)

    afd_domain = AFDDomain(host_name=host_name,
                           tls_settings=tls_settings,
                           azure_dns_zone=ResourceReference(id=azure_dns_zone) if azure_dns_zone is not None else None)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, profile_name, custom_domain_name, afd_domain)


def update_afd_custom_domain(cmd,
                             client: AFDCustomDomainsOperations,
                             resource_group_name: str,
                             profile_name: str,
                             custom_domain_name: str,
                             certificate_type: AfdCertificateType = None,
                             minimum_tls_version: AfdMinimumTlsVersion = None,
                             azure_dns_zone: str = None,
                             secret: str = None):

    if azure_dns_zone is not None and "/dnszones/" not in azure_dns_zone.lower():
        raise InvalidArgumentValueError('azure_dns_zone should be valid Azure dns zone ID.')

    subscription_id = get_subscription_id(cmd.cli_ctx)
    if secret is not None and "/secrets/" not in secret.lower():
        secret = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}' \
                 f'/providers/Microsoft.Cdn/profiles/{profile_name}/secrets/{secret}'

    existing = client.get(resource_group_name, profile_name, custom_domain_name)

    tls_settings = AFDDomainHttpsParameters(certificate_type=certificate_type,
                                            minimum_tls_version=minimum_tls_version,
                                            secret=ResourceReference(id=secret) if secret is not None else None)

    _update_mapper(existing.tls_settings, tls_settings, ["certificate_type", "minimum_tls_version", "secret"])

    if certificate_type == AfdCertificateType.managed_certificate:
        tls_settings.secret = None

    afd_domain = AFDDomain(
        host_name=existing.host_name,
        tls_settings=tls_settings,
        azure_dns_zone=ResourceReference(id=azure_dns_zone) if azure_dns_zone is not None else existing.azure_dns_zone)

    return client.begin_create(resource_group_name,
                               profile_name,
                               custom_domain_name,
                               afd_domain).result()

# endregion
