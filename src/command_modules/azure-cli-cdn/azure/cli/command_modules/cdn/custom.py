# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging
from azure.mgmt.cdn.models import (Endpoint, QueryStringCachingBehavior, SkuName,
                                   EndpointUpdateParameters)


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
                    query_string_caching_behavior=None):
    params = EndpointUpdateParameters(
                        origin_host_header=origin_host_header,
                        origin_path=origin_path,
                        content_types_to_compress=content_types_to_compress,
                        is_compression_enabled=is_compression_enabled,
                        is_http_allowed=is_http_allowed,
                        is_https_allowed=is_https_allowed,
                        query_string_caching_behavior=query_string_caching_behavior)
    _update_mapper(instance, params, [
        'origin_host_header',
        'origin_path',
        'content_types_to_compress',
        'is_compression_enabled',
        'is_http_allowed',
        'is_https_allowed',
        'query_string_caching_behavior'
    ])
    return params
update_endpoint.__doc__ = EndpointUpdateParameters.__doc__


def create_endpoint(client, resource_group_name, profile_name, name, origins, location=None,
                    origin_host_header=None, origin_path=None, content_types_to_compress=None,
                    is_compression_enabled=None, is_http_allowed=None, is_https_allowed=None,
                    query_string_caching_behavior=QueryStringCachingBehavior.ignore_query_string.
                    value):
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
                        query_string_caching_behavior=query_string_caching_behavior)
    return client.endpoints.create(resource_group_name, profile_name, name, endpoint)
create_endpoint.__doc__ = Endpoint.__doc__


def create_custom_domain(client, resource_group_name, profile_name, endpoint_name, name, hostname,
                         location=None):
    """
    Creates a new custom domain within an endpoint.
    :param client: CdnManagementClint
    :param resource_group_name: Name of resource group.
    :param profile_name: Name of the CDN profile which is unique within the resource group.
    :param endpoint_name: Name of the endpoint under the profile which is unique globally.
    :param name: Name of the custom domain within an endpoint.
    :param hostname: The host name of the custom domain. Must be a domain name.
    :param location: Location of the profile. Defaults to the location of the resource group.
    :return: The newly created CDN profile
    :rtype: Profile
    """
    from azure.mgmt.cdn.models import (CustomDomain)
    custom_domain = CustomDomain(location, hostname)
    return client.custom_domains.create(resource_group_name,
                                        profile_name,
                                        endpoint_name,
                                        name,
                                        hostname,
                                        custom_domain)


def create_profile(client, resource_group_name, name,
                   sku=SkuName.standard_akamai.value,
                   location=None):
    """
    Creates a new CDN profile with a profile name under the specified resource group.
    :param client: CdnManagementClint
    :param resource_group_name: Name of resource group.
    :param name: The name of the CDN profile
    :param sku: The pricing tier (defines a CDN provider, feature list and rate) of the CDN profile.
        Defaults to Standard_Akamai.
    :param location: Location of the profile. Defaults to the location of the resource group.
    :return: The newly created CDN profile
    :rtype: Profile
    """
    from azure.mgmt.cdn.models import (Profile, Sku)
    profile = Profile(location, Sku(name=sku))
    return client.profiles.create(resource_group_name, name, profile)
