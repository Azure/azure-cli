# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long


from azure.mgmt.signalr.models import RegenerateKeyParameters


def signalr_key_list(client, resource_group_name, signalr_name):
    return client.list_keys(resource_group_name, signalr_name)


def signalr_key_renew(client, resource_group_name, signalr_name, key_type):
    return client.begin_regenerate_key(resource_group_name, signalr_name, RegenerateKeyParameters(key_type=key_type), polling=False)
