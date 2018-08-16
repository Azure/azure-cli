# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_streaming_endpoint(client, resource_group_name, account_name, streaming_endpoint_name, location,  # pylint: disable=too-many-locals
                              auto_start=None, tags=None, cross_domain_policy=None, ips=None,
                              description=None, scale_units=None, availability_set_name=None, max_cache_age=None,
                              cdn_provider=None, cdn_profile=None, custom_host_names=None, client_access_policy=None):
    from azure.mgmt.media.models import (StreamingEndpoint, IPAccessControl, StreamingEndpointAccessControl)

    allow_list = []
    if ips is not None:
        for ip in ips:
            allow_list.append(create_ip_range(streaming_endpoint_name, ip))

    streaming_endpoint_access_control = None
    if ips is not None:
        streaming_endpoint_access_control = StreamingEndpointAccessControl(ip=IPAccessControl(allow=allow_list))

    policies = create_cross_site_access_policies(client_access_policy, cross_domain_policy)

    cdn_enabled = cdn_profile is not None or cdn_provider is not None

    streaming_endpoint = StreamingEndpoint(max_cache_age=max_cache_age, tags=tags, location=location,
                                           description=description, custom_host_names=custom_host_names,
                                           scale_units=scale_units, cdn_profile=cdn_profile,
                                           availability_set_name=availability_set_name, cdn_enabled=cdn_enabled,
                                           cdn_provider=cdn_provider, cross_site_access_policies=policies,
                                           access_control=streaming_endpoint_access_control)

    return client.create(resource_group_name=resource_group_name, account_name=account_name, auto_start=auto_start,
                         streaming_endpoint_name=streaming_endpoint_name, parameters=streaming_endpoint)


def add_akamai_access_control(client, account_name, resource_group_name, streaming_endpoint_name,
                              identifier=None, base64_key=None, expiration=None):
    from azure.mgmt.media.models import (AkamaiAccessControl, AkamaiSignatureHeaderAuthenticationKey)

    streaming_endpoint = client.get(resource_group_name, account_name, streaming_endpoint_name)

    auth_key = AkamaiSignatureHeaderAuthenticationKey(identifier=identifier,
                                                      base64_key=base64_key, expiration=expiration)

    if streaming_endpoint.access_control is not None:
        if streaming_endpoint.access_control.akamai is None:
            akamai_control = AkamaiAccessControl(akamai_signature_header_authentication_key_list=[])
            streaming_endpoint.access_control.akamai = akamai_control

        streaming_endpoint.access_control.akamai.akamai_signature_header_authentication_key_list.append(auth_key)

    return client.update(resource_group_name, account_name, streaming_endpoint_name, streaming_endpoint)


def remove_akamai_access_control(client, account_name, resource_group_name, streaming_endpoint_name, identifier):

    streaming_endpoint = client.get(resource_group_name, account_name, streaming_endpoint_name)

    if streaming_endpoint.access_control is not None:
        if streaming_endpoint.access_control.akamai is not None:
            streaming_endpoint.access_control.akamai.akamai_signature_header_authentication_key_list = list(filter(lambda x: x.identifier != identifier, streaming_endpoint.access_control.akamai.akamai_signature_header_authentication_key_list))  # pylint: disable=line-too-long

    return client.update(resource_group_name, account_name, streaming_endpoint_name, streaming_endpoint)


def create_cross_site_access_policies(client_access_policy, cross_domain_policy):
    from azure.mgmt.media.models import CrossSiteAccessPolicies

    policies = CrossSiteAccessPolicies()

    if client_access_policy:
        policies.client_access_policy = read_xml_policy(client_access_policy)

    if cross_domain_policy:
        policies.cross_domain_policy = read_xml_policy(cross_domain_policy)

    return policies


def read_xml_policy(xml_policy_path):
    with open(xml_policy_path, 'r') as file:
        return file.read()


def create_ip_range(streaming_endpoint_name, ip):
    from azure.mgmt.media.models import (IPRange)
    return IPRange(name=("{}_{}".format(streaming_endpoint_name, ip)), address=ip, subnet_prefix_length=0)
