# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.mgmt.signalr.models import (
    SignalRResource)


# pylint: disable=dangerous-default-value
def update_network_rules(client, signalr_name, resource_group_name, public_network, connection_name=[], allow=[], deny=[]):
    resource = client.get(resource_group_name, signalr_name)
    network_acl = resource.network_ac_ls
    if public_network:
        network_acl.public_network.allow = allow
        network_acl.public_network.deny = deny

    if network_acl.private_endpoints:
        for x in network_acl.private_endpoints:
            if x.name in connection_name:
                x.allow = allow
                x.deny = deny

    return client.begin_update(resource_group_name, signalr_name, SignalRResource(network_ac_ls=network_acl))


def list_network_rules(client, signalr_name, resource_group_name):
    resource = client.get(resource_group_name, signalr_name)
    return resource.network_ac_ls
