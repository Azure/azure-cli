# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
from ._utils import validate_premium_registry


POLICIES_NOT_SUPPORTED = 'Policies are only supported for managed registries in Premium SKU.'


def acr_config_content_trust_show(cmd,
                                  registry_name,
                                  resource_group_name=None):
    registry, _ = validate_premium_registry(
        cmd, registry_name, resource_group_name, POLICIES_NOT_SUPPORTED)
    policies = registry.policies
    trust_policy = policies.trust_policy if policies else {}
    return trust_policy


def acr_config_content_trust_update(cmd,
                                    client,
                                    registry_name,
                                    status=None,
                                    resource_group_name=None):
    registry, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, POLICIES_NOT_SUPPORTED)

    policies = registry.policies

    if status is not None:
        Policy = cmd.get_models('Policy')
        policies = policies if policies else Policy()
        TrustPolicy = cmd.get_models('TrustPolicy')
        policies.trust_policy = policies.trust_policy if policies.trust_policy else TrustPolicy()
        policies.trust_policy.status = status

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(policies=policies)
    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.update(resource_group_name, registry_name, parameters)
    )
    return updated_policies.policies.trust_policy
