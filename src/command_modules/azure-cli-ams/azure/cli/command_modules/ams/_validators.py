# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def storage_account_id(cmd, namespace):
    """Validate storage account name"""
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    if (namespace.storage_account and not
            ('/providers/Microsoft.ClassicStorage/storageAccounts/' in namespace.storage_account or
             '/providers/Microsoft.Storage/storageAccounts/' in namespace.storage_account)):
        storage_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_STORAGE)
        acc = storage_client.storage_accounts.get_properties(namespace.resource_group_name,
                                                             namespace.storage_account)
        if not acc:
            raise ValueError("Storage account named '{}' not found in the resource group '{}'.".
                             format(namespace.storage_account, namespace.resource_group_name))
        namespace.storage_account = acc.id  # pylint: disable=no-member
