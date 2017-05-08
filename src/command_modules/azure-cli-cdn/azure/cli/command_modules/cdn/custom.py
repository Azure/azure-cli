# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.cdn.models import (Endpoint, QueryStringCachingBehavior, SkuName,
                                   EndpointUpdateParameters, ProfileUpdateParameters)


def default_content_types():
    return ["text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/x-javascript",
            "application/javascript",
            "application/json",
            "application/xml"]


def list_profiles(client, resource_group_name=None):
    profiles = client.profiles
    profile_list = profiles.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else profiles.list()
    return list(profile_list)


def _update_mapper(existing, new, keys):
    for key in keys:
        existing_value = getattr(existing, key)
        new_value = getattr(new, key)
        setattr(new, key, new_value if new_value is not None else existing_value)


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


update_endpoint.__doc__ = EndpointUpdateParameters.__doc__


def create_endpoint(client, resource_group_name, profile_name, name, origins, location=None,
                    origin_host_header=None, origin_path=None, content_types_to_compress=None,
                    is_compression_enabled=None, is_http_allowed=None, is_https_allowed=None,
                    query_string_caching_behavior=QueryStringCachingBehavior.ignore_query_string.
                    value, tags=None):
    is_compression_enabled = False if is_compression_enabled is None else is_compression_enabled
    is_http_allowed = True if is_http_allowed is None else is_http_allowed
    is_https_allowed = True if is_https_allowed is None else is_https_allowed
    endpoint = Endpoint(location,
                        origins,
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

    return client.endpoints.create(resource_group_name, profile_name, name, endpoint)


create_endpoint.__doc__ = Endpoint.__doc__


def create_custom_domain(client, resource_group_name, profile_name, endpoint_name, name, hostname,
                         location=None, tags=None):
    from azure.mgmt.cdn.models import (CustomDomain)
    custom_domain = CustomDomain(location, hostname, tags=tags)
    return client.custom_domains.create(resource_group_name,
                                        profile_name,
                                        endpoint_name,
                                        name,
                                        hostname,
                                        custom_domain)


def update_profile(instance, tags=None):
    params = ProfileUpdateParameters(tags=tags)
    _update_mapper(instance, params, ['tags'])
    return params


update_profile.__doc__ = ProfileUpdateParameters.__doc__


def create_profile(client, resource_group_name, name,
                   sku=SkuName.standard_akamai.value,
                   location=None, tags=None):
    from azure.mgmt.cdn.models import (Profile, Sku)
    profile = Profile(location, Sku(name=sku), tags=tags)
    return client.profiles.create(resource_group_name, name, profile)
