# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from azure.cli.core.commands import LongRunningOperation
from ._utils import validate_premium_registry

POLICIES_NOT_SUPPORTED = 'Policies are only supported for managed registries in Premium SKU.'


# temporary place holder enum for retention type
class RetentionType(str, Enum):
    UntaggedManifests = "UntaggedManifests"


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

    if status:
        Policy = cmd.get_models('Policy')
        policies = policies if policies else Policy()
        TrustPolicy = cmd.get_models('TrustPolicy')
        policies.trust_policy = policies.trust_policy if policies.trust_policy else TrustPolicy()
        policies.trust_policy.status = status

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(policies=policies)
    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.begin_update(resource_group_name, registry_name, parameters)
    )
    return updated_policies.policies.trust_policy


def acr_config_retention_show(cmd,
                              registry_name,
                              resource_group_name=None):
    registry, _ = validate_premium_registry(
        cmd, registry_name, resource_group_name, POLICIES_NOT_SUPPORTED)
    policies = registry.policies
    retention_policy = policies.retention_policy if policies else None
    return retention_policy


def acr_config_retention_update(cmd,
                                client,
                                registry_name,
                                policy_type,  # pylint: disable=unused-argument
                                status=None,
                                days=None,
                                resource_group_name=None):
    registry, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, POLICIES_NOT_SUPPORTED)

    Policy, RetentionPolicy, RegistryUpdateParameters = cmd.get_models(
        'Policy', 'RetentionPolicy', 'RegistryUpdateParameters')

    policies = registry.policies
    if policies is None:
        policies = Policy()

    policies.retention_policy = policies.retention_policy if policies.retention_policy else RetentionPolicy()

    if status:
        policies.retention_policy.status = status

    if days is not None:
        policies.retention_policy.days = days

    parameters = RegistryUpdateParameters(policies=policies)
    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.begin_update(resource_group_name, registry_name, parameters)
    )
    return updated_policies.policies.retention_policy
