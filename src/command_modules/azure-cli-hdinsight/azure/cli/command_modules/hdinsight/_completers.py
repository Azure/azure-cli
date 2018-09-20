# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from ._client_factory import cf_storage


@Completer
def storage_account_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    storage_client = cf_storage(cmd.cli_ctx)
    rg = getattr(namespace, 'resource_group_name', None)
    if rg:
        storage_accounts = storage_client.storage_accounts.list_by_resource_group(rg)
    else:
        storage_accounts = storage_client.storage_accounts.list()

    def extract_blob_endpoint(storage_account):
        return storage_account and storage_account.primary_endpoints and storage_account.primary_endpoints.blob

    def extract_host(uri):
        import re
        return re.search('//(.*)/', uri).groups()[0]

    return [extract_host(extract_blob_endpoint(s)) for s in storage_accounts]
