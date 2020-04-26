# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def add_log_analytics_workspace_linked_storage_accounts(client, resource_group_name, workspace_name,
                                                        data_source_type, storage_account_ids):
    linked_storage_accounts = client.get(resource_group_name=resource_group_name,
                                         workspace_name=workspace_name,
                                         data_source_type=data_source_type)
    linked_storage_accounts.storage_account_ids.extend(storage_account_ids)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   workspace_name=workspace_name,
                                   data_source_type=data_source_type,
                                   storage_account_ids=linked_storage_accounts.storage_account_ids)


def remove_log_analytics_workspace_linked_storage_accounts(client, resource_group_name, workspace_name,
                                                           data_source_type, storage_account_ids):
    linked_storage_accounts = client.get(resource_group_name=resource_group_name,
                                         workspace_name=workspace_name,
                                         data_source_type=data_source_type)
    existed_storage_account_ids_set = set(linked_storage_accounts.storage_account_ids)
    storage_account_ids_set = set()
    for storage_account_id in storage_account_ids:
        storage_account_ids_set.add(str.lower(storage_account_id))
    for existed_storage_account_id in existed_storage_account_ids_set:
        if str.lower(existed_storage_account_id) in storage_account_ids_set:
            linked_storage_accounts.storage_account_ids.remove(existed_storage_account_id)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   workspace_name=workspace_name,
                                   data_source_type=data_source_type,
                                   storage_account_ids=linked_storage_accounts.storage_account_ids)
