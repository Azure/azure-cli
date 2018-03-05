# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# from ._client_factory import get_mediaservices_client

def create_mediaservice(
        client, resource_group_name, account_name, storage_account, location=None, tags=None):

    storage_account_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Storage/storageAccounts/{2}".format(client.config.subscription_id, resource_group_name, storage_account)

    from azure.mgmt.media.models import StorageAccount
    storage_account = StorageAccount("Primary", storage_account_id)

    from azure.mgmt.media.models import MediaService
    media_service = MediaService(location=location, storage_accounts=[storage_account], tags=tags)

    #return 0

    return client.create_or_update(resource_group_name, account_name, media_service)