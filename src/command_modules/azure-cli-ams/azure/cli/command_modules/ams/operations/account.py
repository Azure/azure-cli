# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def list_mediaservices(client, resource_group_name=None):
    return client.list(resource_group_name) if resource_group_name else client.list_by_subscription()


def create_mediaservice(client, resource_group_name, account_name, storage_account, location=None, tags=None):
    from azure.mediav3.models import StorageAccount
    storage_account_primary = StorageAccount('Primary', storage_account)

    return create_or_update_mediaservice(client, resource_group_name, account_name, [storage_account_primary],
                                         location,
                                         tags)


def add_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account in s.id, ams.storage_accounts))

    from azure.mediav3.models import StorageAccount
    storage_account_secondary = StorageAccount('Secondary', storage_account)

    if not storage_accounts_filtered:
        ams.storage_accounts.append(storage_account_secondary)

    return create_or_update_mediaservice(client, resource_group_name, account_name,
                                         ams.storage_accounts,
                                         ams.location,
                                         ams.tags)


def remove_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account not in s.id and 'Secondary' in s.type.value,
                                            ams.storage_accounts))

    primary_storage_account = list(filter(lambda s: 'Primary' in s.type.value, ams.storage_accounts))[0]
    storage_accounts_filtered.append(primary_storage_account)

    return create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts_filtered,
                                         ams.location,
                                         ams.tags)


def create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts=None,
                                  location=None,
                                  tags=None):

    from azure.mediav3.models import MediaService
    media_service = MediaService(location=location, storage_accounts=storage_accounts, tags=tags)

    return client.create_or_update(resource_group_name, account_name, media_service)
