# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.mgmt.signalr.models import KeyType


def signalr_cors_list(client, resource_group_name, signalr_name):
    return client.list_keys(resource_group_name, signalr_name)


def signalr_cors_add(client, resource_group_name, signalr_name, key_type):
    if key_type == 'primary':
        key_type = KeyType.primary
    else:
        key_type = KeyType.secondary
    return client.regenerate_key(resource_group_name, signalr_name, key_type, polling=False)

def signalr_cors_remove(client, resource_group_name, signalr_name, key_type):

