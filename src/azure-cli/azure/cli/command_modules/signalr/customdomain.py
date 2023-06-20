# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long


from azure.mgmt.signalr.models import (
    CustomDomain,
    ResourceReference
)

from azure.mgmt.signalr._signal_rmanagement_client import (
    SignalRCustomDomainsOperations
)


def custom_domain_create(client: SignalRCustomDomainsOperations, resource_group_name, signalr_name, name, domain_name, certificate_resource_id):
    resource_reference = ResourceReference(id=certificate_resource_id)
    custom_domain = CustomDomain(domain_name=domain_name, custom_certificate=resource_reference)

    return client.begin_create_or_update(resource_group_name, signalr_name, name, custom_domain)


def custom_domain_delete(client: SignalRCustomDomainsOperations, resource_group_name, signalr_name, name):
    return client.begin_delete(resource_group_name, signalr_name, name)


def custom_domain_show(client: SignalRCustomDomainsOperations, resource_group_name, signalr_name, name):
    return client.get(resource_group_name, signalr_name, name)


def custom_domain_list(client: SignalRCustomDomainsOperations, resource_group_name, signalr_name):
    return client.list(resource_group_name, signalr_name)


def get_custom_domain(client: SignalRCustomDomainsOperations, resource_group_name, signalr_name, name):
    return client.get(resource_group_name, signalr_name, name)


def set_custom_domain(client: SignalRCustomDomainsOperations, resource_group_name, signalr_name, name, parameters):
    return client.begin_create_or_update(resource_group_name, signalr_name, name, parameters)


def update(instance: CustomDomain, domain_name=None, certificate_resource_id=None):
    if domain_name is not None:
        instance.domain_name = domain_name
    if certificate_resource_id is not None:
        instance.custom_certificate = ResourceReference(id=certificate_resource_id)
    return instance
