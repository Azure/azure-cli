# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_key_for_storage_account(cmd, storage_blob_endpoint, rg=None):  # pylint: disable=unused-argument
    from ._client_factory import cf_storage
    storage_account_name = _extract_storage_account_name_from_endpoint(storage_blob_endpoint)

    # The storage account's resource group might not necessarily be the cluster's resource group
    storage_client = cf_storage(cmd.cli_ctx)
    storage_account_rg = None
    if rg:
        # Check the storage accounts in the specified resource group first
        storage_accounts = storage_client.storage_accounts.list_by_resource_group(rg)
        for sa in storage_accounts:
            if _parse_resource_name_from_id(sa.id) == storage_account_name:
                storage_account_rg = _parse_resource_group_from_id(sa.id)
                break

    if not storage_account_rg:
        storage_accounts = storage_client.storage_accounts.list()
        for sa in storage_accounts:
            if _parse_resource_name_from_id(sa.id) == storage_account_name:
                storage_account_rg = _parse_resource_group_from_id(sa.id)
                break

    if not storage_account_rg:
        return None

    keys = storage_client.storage_accounts.list_keys(storage_account_rg, storage_account_name).keys
    return keys and keys[0] and keys[0].value


def _extract_storage_account_name_from_endpoint(storage_blob_endpoint):
    return storage_blob_endpoint.split('.')[0]


def _parse_resource_group_from_id(resource_id):
    import re
    return re.search('subscriptions/[^/]+/resourceGroups/([^/]+)/', resource_id).groups()[0]


def _parse_resource_name_from_id(resource_id):
    return resource_id.split('/')[-1]
