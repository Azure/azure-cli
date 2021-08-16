# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.core.exceptions import HttpResponseError

from azure.mgmt.media.models import (MediaService, MediaServiceIdentity, StorageAccount,
                                     CheckNameAvailabilityInput, SyncStorageKeysInput)


def get_mediaservice(client, account_name, resource_group_name=None):
    return client.get(resource_group_name,
                      account_name) if resource_group_name else client.get_by_subscription(account_name)


def list_mediaservices(client, resource_group_name=None):
    return client.list(resource_group_name) if resource_group_name else client.list_by_subscription()


def create_mediaservice(client, resource_group_name, account_name, storage_account, location=None,
                        assign_identity=False, tags=None):
    storage_account_primary = StorageAccount(type='Primary', id=storage_account)

    return create_or_update_mediaservice(client, resource_group_name, account_name, [storage_account_primary],
                                         location, assign_identity,
                                         tags)


def add_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account in s.id, ams.storage_accounts))

    storage_account_secondary = StorageAccount(type='Secondary', id=storage_account)

    if not storage_accounts_filtered:
        ams.storage_accounts.append(storage_account_secondary)

    return create_or_update_mediaservice(client, resource_group_name, account_name,
                                         ams.storage_accounts,
                                         ams.location,
                                         ams.tags)


def remove_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account not in s.id and 'Secondary' in s.type,
                                            ams.storage_accounts))

    primary_storage_account = list(filter(lambda s: 'Primary' in s.type, ams.storage_accounts))[0]
    storage_accounts_filtered.append(primary_storage_account)

    return create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts_filtered,
                                         ams.location,
                                         ams.tags)


def sync_storage_keys(client, resource_group_name, account_name, storage_account_id):
    parameters = SyncStorageKeysInput(id=storage_account_id)
    return client.sync_storage_keys(resource_group_name, account_name, parameters)


def set_mediaservice_trusted_storage(client, resource_group_name, account_name,
                                     storage_auth):
    ams = client.get(resource_group_name, account_name)
    media_service = MediaService(location=ams.location, storage_accounts=ams.storage_accounts,
                                 storage_authentication=storage_auth)

    return client.create_or_update(resource_group_name, account_name, media_service)


def create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts=None,
                                  location=None, assign_identity=False,
                                  tags=None):
    identity = 'SystemAssigned' if assign_identity else 'None'
    media_service = MediaService(location=location, storage_accounts=storage_accounts,
                                 identity=MediaServiceIdentity(type=identity), tags=tags)

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
