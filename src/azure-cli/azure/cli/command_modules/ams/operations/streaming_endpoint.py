# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import (sdk_no_wait, CLIError)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.command_modules.ams._utils import (create_ip_range, show_resource_not_found_message)

from azure.mgmt.media.models import (AkamaiAccessControl, AkamaiSignatureHeaderAuthenticationKey,
                                     CrossSiteAccessPolicies, IPAccessControl,
                                     StreamingEndpoint, StreamingEndpointAccessControl,
                                     StreamingEntityScaleUnit)


def create_streaming_endpoint(cmd, client, resource_group_name, account_name, streaming_endpoint_name,  # pylint: disable=too-many-locals
                              scale_units, auto_start=None, tags=None, cross_domain_policy=None, ips=None,
                              description=None, availability_set_name=None, max_cache_age=None, cdn_provider=None,
                              cdn_profile=None, custom_host_names=None, client_access_policy=None, no_wait=False):
    from azure.cli.command_modules.ams._client_factory import (get_mediaservices_client)

    allow_list = []
    if ips is not None:
        for ip in ips:
            allow_list.append(create_ip_range(streaming_endpoint_name, ip))

    ams_client = get_mediaservices_client(cmd.cli_ctx)
    ams = ams_client.get(resource_group_name, account_name)
    location = ams.location

    streaming_endpoint_access_control = StreamingEndpointAccessControl()

    if ips is not None:
        streaming_endpoint_access_control.ip = IPAccessControl(allow=allow_list)

    policies = create_cross_site_access_policies(client_access_policy, cross_domain_policy)

    cdn_enabled = cdn_profile is not None or cdn_provider is not None

    streaming_endpoint = StreamingEndpoint(max_cache_age=max_cache_age, tags=tags, location=location,
                                           description=description, custom_host_names=custom_host_names,
                                           scale_units=scale_units, cdn_profile=cdn_profile,
                                           availability_set_name=availability_set_name, cdn_enabled=cdn_enabled,
                                           cdn_provider=cdn_provider, cross_site_access_policies=policies,
                                           access_control=streaming_endpoint_access_control)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name=resource_group_name, account_name=account_name,
                       auto_start=auto_start, streaming_endpoint_name=streaming_endpoint_name,
                       parameters=streaming_endpoint)


def add_akamai_access_control(client, account_name, resource_group_name, streaming_endpoint_name,
                              identifier=None, base64_key=None, expiration=None):

    streaming_endpoint = client.get(resource_group_name, account_name, streaming_endpoint_name)

    auth_key = AkamaiSignatureHeaderAuthenticationKey(identifier=identifier,
                                                      base64_key=base64_key, expiration=expiration)

    if streaming_endpoint.access_control is None:
        streaming_endpoint.access_control = StreamingEndpointAccessControl()

    if streaming_endpoint.access_control.akamai is None:
        streaming_endpoint.access_control.akamai = AkamaiAccessControl(
            akamai_signature_header_authentication_key_list=[])

    streaming_endpoint.access_control.akamai.akamai_signature_header_authentication_key_list.append(auth_key)

    return client.begin_update(resource_group_name, account_name, streaming_endpoint_name, streaming_endpoint)


def remove_akamai_access_control(client, account_name, resource_group_name, streaming_endpoint_name, identifier):

    streaming_endpoint = client.get(resource_group_name, account_name, streaming_endpoint_name)

    if streaming_endpoint.access_control is not None:
        if streaming_endpoint.access_control.akamai is not None:
            streaming_endpoint.access_control.akamai.akamai_signature_header_authentication_key_list = list(
                filter(lambda x: x.identifier != identifier,
                       streaming_endpoint.access_control.akamai.akamai_signature_header_authentication_key_list))

    return client.begin_update(resource_group_name, account_name, streaming_endpoint_name, streaming_endpoint)


def update_streaming_endpoint_setter(client, resource_group_name, account_name, streaming_endpoint_name,
                                     parameters, no_wait):
    if (parameters.access_control is not None and
            parameters.access_control.ip is not None and
            parameters.access_control.ip.allow):
        ips = list(map(lambda x: create_ip_range(streaming_endpoint_name, x) if isinstance(x, str) else x,
                       parameters.access_control.ip.allow))
        parameters.access_control.ip.allow = ips

    return sdk_no_wait(no_wait, client.begin_update, resource_group_name=resource_group_name,
                       account_name=account_name, streaming_endpoint_name=streaming_endpoint_name,
                       parameters=parameters)


# pylint: disable=too-many-branches
def update_streaming_endpoint(instance, tags=None, cross_domain_policy=None, client_access_policy=None,
                              description=None, max_cache_age=None, ips=None, disable_cdn=None,
                              cdn_provider=None, cdn_profile=None, custom_host_names=None):

    if not instance:
        raise CLIError('The streaming endpoint resource was not found.')

    if ips is not None:
        is_ips_argument_empty = len(ips) == 1 and ips[0] == ""
        if is_ips_argument_empty:
            if instance.access_control is not None and instance.access_control.ip is not None:
                instance.access_control.ip = None
        else:
            if instance.access_control is None:
                instance.access_control = StreamingEndpointAccessControl()
            if instance.access_control.ip is None:
                instance.access_control.ip = IPAccessControl(allow=[])
            for ip in ips:
                instance.access_control.ip.allow.append(create_ip_range(instance.name, ip))

    if instance.cross_site_access_policies is None:
        instance.cross_site_access_policies = CrossSiteAccessPolicies()

    if client_access_policy is not None:
        if not client_access_policy:
            instance.cross_site_access_policies.client_access_policy = None
        else:
            instance.cross_site_access_policies.client_access_policy = client_access_policy

    if cross_domain_policy is not None:
        if not cross_domain_policy:
            instance.cross_site_access_policies.cross_domain_policy = None
        else:
            instance.cross_site_access_policies.cross_domain_policy = cross_domain_policy

    if max_cache_age is not None:
        instance.max_cache_age = max_cache_age
    if tags is not None:
        instance.tags = tags
    if description is not None:
        instance.description = description
    if custom_host_names is not None:
        is_custom_host_names_argument_empty = len(custom_host_names) == 1 and custom_host_names[0] == ""
        if is_custom_host_names_argument_empty:
            instance.custom_host_names = []
        else:
            instance.custom_host_names = custom_host_names
    if cdn_provider is not None:
        instance.cdn_provider = cdn_provider
    if cdn_profile is not None:
        instance.cdn_profile = cdn_profile
    if cdn_provider is not None or cdn_profile is not None:
        if ips is None and instance.access_control is not None:
            instance.access_control = None
        instance.cdn_enabled = True

    if disable_cdn is not None:
        instance.cdn_enabled = not disable_cdn

    return instance


def create_cross_site_access_policies(client_access_policy, cross_domain_policy):

    policies = CrossSiteAccessPolicies()

    if client_access_policy:
        policies.client_access_policy = client_access_policy

    if cross_domain_policy:
        policies.cross_domain_policy = cross_domain_policy

    return policies


def scale(client, resource_group_name, account_name, streaming_endpoint_name, scale_units):
    parameters = StreamingEntityScaleUnit(scale_unit=scale_units)

    return client.begin_scale(resource_group_name, account_name, streaming_endpoint_name, parameters)


def start(cmd, client, resource_group_name, account_name, streaming_endpoint_name,
          no_wait=False):
    if no_wait:
        return sdk_no_wait(no_wait, client.begin_start, resource_group_name, account_name,
                           streaming_endpoint_name)

    LongRunningOperation(cmd.cli_ctx)(client.begin_start(resource_group_name, account_name,
                                                         streaming_endpoint_name))

    return client.get(resource_group_name, account_name, streaming_endpoint_name)


def stop(cmd, client, resource_group_name, account_name,
         streaming_endpoint_name, no_wait=False):
    if no_wait:
        return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, account_name,
                           streaming_endpoint_name)

    LongRunningOperation(cmd.cli_ctx)(client.begin_stop(resource_group_name, account_name,
                                                        streaming_endpoint_name))

    return client.get(resource_group_name, account_name, streaming_endpoint_name)


def get_streaming_endpoint(client, resource_group_name, account_name,
                           streaming_endpoint_name):
    streaming_endpoint = client.get(resource_group_name, account_name, streaming_endpoint_name)
    if not streaming_endpoint:
        show_resource_not_found_message(
            resource_group_name,
            account_name,
            'streamingEndpoints',
            streaming_endpoint_name)

    return streaming_endpoint
