# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.batch import BatchManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client

# COMMAND NAMESPACE VALIDATORS

def application_enabled(namespace):
    """ Validates account has auto-storage enabled"""

    client = get_mgmt_service_client(BatchManagementClient)
    acc = client.batch_account.get(namespace.resource_group_name, namespace.account_name)
    if not acc:
        raise ValueError("Batch account '{}' not found.".format(namespace.account_name))
    if not acc.auto_storage or not acc.auto_storage.storage_account_id: #pylint: disable=no-member
        raise ValueError("Batch account '{}' needs auto-storage enabled.".
                         format(namespace.account_name))

