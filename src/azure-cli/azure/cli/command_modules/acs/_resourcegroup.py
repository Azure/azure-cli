# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import AzCLIError

from ._client_factory import cf_resource_groups


def get_rg_location(ctx, resource_group_name, subscription_id=None):
    groups = cf_resource_groups(ctx, subscription_id=subscription_id)
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    if rg is None:
        raise AzCLIError(f"Resource group {resource_group_name} not found.")
    return rg.location
