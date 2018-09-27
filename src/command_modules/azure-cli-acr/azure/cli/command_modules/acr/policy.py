# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
from ._utils import validate_managed_registry


POLICIES_NOT_SUPPORTED = 'Policies are only supported for managed registries.'


def acr_config_content_trust_show(cmd,
                                  client,
                                  registry_name,
                                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, POLICIES_NOT_SUPPORTED)
    return client.list_policies(resource_group_name, registry_name).trust_policy


def acr_config_content_trust_update(cmd,
                                    client,
                                    registry_name,
                                    status=None,
                                    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, POLICIES_NOT_SUPPORTED)

    trust_policy = client.list_policies(resource_group_name, registry_name).trust_policy

    if status is not None:
        trust_policy.status = status

    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.update_policies(resource_group_name, registry_name, None, trust_policy)
    )
    return updated_policies.trust_policy
