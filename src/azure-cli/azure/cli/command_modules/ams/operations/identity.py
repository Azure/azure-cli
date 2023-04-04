# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=redefined-builtin

from azure.mgmt.media.models import (MediaService, MediaServiceUpdate, MediaServiceIdentity)
from azure.cli.core.azclierror import ValidationError


def assign_identity(client, resource_group_name, account_name, system_assigned=False, user_assigned=None):
    if system_assigned is False and user_assigned is None:
        error_msg = 'Please specify either system assigned identity or a user assigned identity'
        raise ValidationError(error_msg)

    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)
    if account_info.identity is None:
        current_identity_types = []
    else:
        current_identity_types = account_info.identity.type.split(',')
        if 'None' in current_identity_types:
            current_identity_types = []

    media_service = MediaServiceUpdate(identity=MediaServiceIdentity(type=''))

    if system_assigned and 'SystemAssigned' not in current_identity_types:
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
    if (system_assigned is False and user_assigned is None):
        error_msg = 'Please specify either system assigned identity or a user assigned identity'
        raise ValidationError(error_msg)

    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)

    current_identity_types = account_info.identity.type.split(',')

    media_service = MediaService(name=account_info.name, location=account_info.location,
                                 key_delivery=account_info.key_delivery,
                                 identity=MediaServiceIdentity(
                                     type='',
                                     user_assigned_identities=account_info.identity.user_assigned_identities),
                                 encryption=account_info.encryption, storage_accounts=account_info.storage_accounts,
                                 storage_authentication=account_info.storage_authentication,
                                 public_network_access=account_info.public_network_access)

    if system_assigned and 'SystemAssigned' in current_identity_types:
        current_identity_types.remove('SystemAssigned')
    user_id_dict = {}
    if user_assigned:
        for user_id in user_assigned:
            user_id_dict[user_id] = None
        media_service.identity.user_assigned_identities = user_id_dict

    identity_type = ','.join(current_identity_types) if current_identity_types else 'None'
    media_service.identity.type = identity_type

    if user_assigned and identity_type != 'None':
        return client.update(resource_group_name, account_name, media_service)

    return client.create_or_update(resource_group_name, account_name, media_service)


def show_identity(client, resource_group_name, account_name):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)
    return account_info.identity
