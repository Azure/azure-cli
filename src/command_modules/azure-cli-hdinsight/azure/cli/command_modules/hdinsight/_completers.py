# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_resources_in_resource_group, get_resources_in_subscription
from azure.cli.core.decorators import Completer


@Completer
def storage_account_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    resource_type = 'Microsoft.Storage/storageaccounts'
    rg = getattr(namespace, 'resource_group_name', None)
    if rg:
        return [r.primary_endpoints.blob for r in get_resources_in_resource_group(cmd.cli_ctx, rg, resource_type=resource_type)]
    return [r.primary_endpoints.blob for r in get_resources_in_subscription(cmd.cli_ctx, resource_type)]
