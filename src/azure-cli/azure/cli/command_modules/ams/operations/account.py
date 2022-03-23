# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import ValidationError

from azure.mgmt.media.models import (MediaService, MediaServiceIdentity, StorageAccount, MediaServiceUpdate,
                                     CheckNameAvailabilityInput, SyncStorageKeysInput, ResourceIdentity, KeyDelivery,
                                     AccessControl)


def get_mediaservice(client, account_name, resource_group_name=None):
    return client.get(resource_group_name,
                      account_name) if resource_group_name else client.get_by_subscription(account_name)


def list_mediaservices(client, resource_group_name=None):
    return client.list(resource_group_name) if resource_group_name else client.list_by_subscription()


def create_mediaservice(client, resource_group_name, account_name, storage_account, location=None,
                        mi_system_assigned=False, mi_user_assigned=None, public_network_access=False,
                        default_action=None, ip_allow_list=None, tags=None):
    storage_account_primary = StorageAccount(type='Primary', id=storage_account)
    return create_or_update_mediaservice(client, resource_group_name, account_name, [storage_account_primary],
                                         location, mi_system_assigned, mi_user_assigned, public_network_access,
                                         default_action, ip_allow_list, tags)


def add_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account,
                                       system_assigned=False, user_assigned=None):
    ams = client.get(resource_group_name, account_name)
    if (system_assigned == False and user_assigned is None and ams.storage_authentication == 'ManagedIdentity'):
        error_msg = 'Please specify either a system assigned identity or a user assigned identity'
        raise ValidationError(error_msg)

    storage_accounts_filtered = list(filter(lambda s: storage_account in s.id, ams.storage_accounts))

    storage_account_secondary = StorageAccount(type='Secondary', id=storage_account, identity=ResourceIdentity(
        use_system_assigned_identity=system_assigned, user_assigned_identity=user_assigned))
    if not storage_accounts_filtered:
        ams.storage_accounts.append(storage_account_secondary)

    media_service = MediaService(name=ams.name, location=ams.location, key_delivery=ams.key_delivery,
                                 identity=ams.identity, encryption=ams.encryption,
                                 storage_accounts=ams.storage_accounts, storage_authentication=ams.storage_authentication,
                                 public_network_access=ams.public_network_access)

    return client.create_or_update(resource_group_name, account_name, media_service)


def remove_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account not in s.id and 'Secondary' in s.type,
                                            ams.storage_accounts))

    primary_storage_account = list(filter(lambda s: 'Primary' in s.type, ams.storage_accounts))[0]
    storage_accounts_filtered.append(primary_storage_account)

    media_service = MediaService(name=ams.name, location=ams.location, key_delivery=ams.key_delivery,
                                 identity=ams.identity, encryption=ams.encryption,
                                 storage_accounts=storage_accounts_filtered,
                                 storage_authentication=ams.storage_authentication,
                                 public_network_access=ams.public_network_access)

    return client.create_or_update(resource_group_name, account_name, media_service)


def sync_storage_keys(client, resource_group_name, account_name, storage_account_id):
    parameters = SyncStorageKeysInput(id=storage_account_id)
    return client.sync_storage_keys(resource_group_name, account_name, parameters)


def set_mediaservice_trusted_storage(client, resource_group_name, account_name, storage_auth, storage_account_id=None,
                                     system_assigned=False, user_assigned=None):
    ams: MediaService = client.get(resource_group_name, account_name) if resource_group_name else client.get_by_subscription(account_name)
    if storage_auth == 'ManagedIdentity' and storage_account_id == None:
        error_msg = 'Please specify a storage account id for the storage account whose identity you would like to set'
        raise ValidationError(error_msg)

    for storage_account in ams.storage_accounts:
        if storage_auth == 'ManagedIdentity':
            if storage_account.id.lower() == storage_account_id.lower():
                storage_account.identity = ResourceIdentity(use_system_assigned_identity=system_assigned,
                                                            user_assigned_identity=user_assigned)
        else:
            storage_account.identity = None


    media_service = MediaService(name=ams.name,location=ams.location, key_delivery=ams.key_delivery,
                                 identity=ams.identity, encryption=ams.encryption,
                                 storage_accounts=ams.storage_accounts, storage_authentication=storage_auth,
                                 public_network_access=ams.public_network_access)

    return client.create_or_update(resource_group_name, account_name, media_service)


def create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts=None,
                                  location=None, mi_system_assigned=False, mi_user_assigned=None,
                                  public_network_access=False, default_action=None, ip_allow_list=None, tags=None):
    identity = MediaServiceIdentity(type='')
    identity.type = 'SystemAssigned' if mi_system_assigned else ''
    user_id_dict = {}
    if mi_user_assigned:
        identity.type = ','.join([identity.type, 'UserAssigned']) if identity.type else 'UserAssigned'
        for user_id in mi_user_assigned:
            user_id_dict[user_id] = {}
        identity.user_assigned_identities = user_id_dict

    media_service = MediaService(location=location, storage_accounts=storage_accounts,
                                 identity=identity,
                                 tags=tags, public_network_access='Enabled' if public_network_access else 'Disabled')

    media_service.key_delivery = KeyDelivery(access_control=AccessControl(default_action=default_action, ip_allow_list=ip_allow_list if default_action == 'Deny' else []))
    return client.create_or_update(resource_group_name, account_name, media_service)


def mediaservice_update_getter(client, resource_group_name, account_name):

    try:
        return client.get(resource_group_name, account_name)
    except HttpResponseError as ex:
        raise CLIError(ex.message)


def update_mediaservice(instance, tags=None):
    if not instance:
        raise CLIError('The account resource was not found.')

    if tags:
        instance.tags = tags

    return instance


def check_name_availability(client, location, account_name):
    parameters = CheckNameAvailabilityInput(name=account_name, type='MICROSOFT.MEDIA/MEDIASERVICES')
    availability = client.check_name_availability(location_name=location, parameters=parameters)

    if availability.name_available:
        return 'Name available.'

    return availability.message
