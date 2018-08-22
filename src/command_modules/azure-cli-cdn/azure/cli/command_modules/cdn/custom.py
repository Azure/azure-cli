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


def _update_mapper(existing, new, keys):
    for key in keys:
        existing_value = getattr(existing, key)
        new_value = getattr(new, key)
        setattr(new, key, new_value if new_value is not None else existing_value)


# region Custom Commands
# pylint: disable=unused-argument
def list_profiles(cmd, client, resource_group_name=None):
    profiles = client.profiles
    profile_list = profiles.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else profiles.list()
    return list(profile_list)


# pylint: disable=unused-argument
def update_endpoint(cmd, instance,
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


# pylint: disable=unused-argument
def create_endpoint(cmd, client, resource_group_name, profile_name, name, origins, location=None,
                    origin_host_header=None, origin_path=None, content_types_to_compress=None,
                    is_compression_enabled=None, is_http_allowed=None, is_https_allowed=None,
                    query_string_caching_behavior=QueryStringCachingBehavior.ignore_query_string.
                    value, tags=None):
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

    return client.endpoints.create(resource_group_name, profile_name, name, endpoint)


# pylint: disable=unused-argument
def create_custom_domain(cmd, client, resource_group_name, profile_name, endpoint_name, custom_domain_name,
                         hostname, location=None, tags=None):
    return client.custom_domains.create(resource_group_name,
                                        profile_name,
                                        endpoint_name,
                                        custom_domain_name,
                                        hostname)


# pylint: disable=unused-argument
def update_profile(cmd, instance, tags=None):
    params = ProfileUpdateParameters(tags=tags)
    _update_mapper(instance, params, ['tags'])
    return params


# pylint: disable=unused-argument
def create_profile(cmd, client, resource_group_name, name,
                   sku=SkuName.standard_akamai.value,
                   location=None, tags=None):
    from azure.mgmt.cdn.models import (Profile, Sku)
    profile = Profile(location=location, sku=Sku(name=sku), tags=tags)
    return client.profiles.create(resource_group_name, name, profile)

# endregion
