# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=redefined-builtin

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import BadRequestError
from azure.mgmt.media.models import (MediaService, AccountEncryption, KeyVaultProperties, ResourceIdentity, AccountEncryptionKeyType,
                                     MediaServiceUpdate, MediaServiceIdentity)


def assign_identity(client, resource_group_name, account_name, system_assigned=False, user_assigned=None):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)

    current_identity_types = account_info.identity.type.split(',')

    media_service = MediaServiceUpdate(identity=MediaServiceIdentity(type=''))

    if (system_assigned and 'SystemAssigned' not in current_identity_types):
        current_identity_types.append('SystemAssigned')
    user_id_dict = {}
    if user_assigned:
        if 'UserAssigned' not in current_identity_types:
            current_identity_types.append('UserAssigned')
        for user_id in user_assigned:
            user_id_dict[user_id] = {}
        media_service.identity.user_assigned_identities = user_id_dict

    identity_type = ','.join(current_identity_types)
    media_service.identity.type = identity_type

    return client.update(resource_group_name, account_name, media_service)


def remove_identity(client, resource_group_name, account_name, system_assigned=False, user_assigned=None):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)

    current_identity_types = account_info.identity.type.split(',')

    media_service = MediaServiceUpdate(identity=MediaServiceIdentity(type=''))

    if (system_assigned and 'SystemAssigned' in current_identity_types):
        current_identity_types.remove('SystemAssigned')
    user_id_dict = {}
    if user_assigned:
        for user_id in user_assigned:
            user_id_dict[user_id] = None
        media_service.identity.user_assigned_identities = user_id_dict

    identity_type = ','.join(current_identity_types) if current_identity_types else 'None'
    media_service.identity.type = identity_type

    return client.update(resource_group_name, account_name, media_service)

def show_identity(client, resource_group_name, account_name):
    account_info = client.get(resource_group_name,
                      account_name) if resource_group_name else client.get_by_subscription(account_name)
    return account_info.identity