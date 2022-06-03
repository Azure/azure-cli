# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from azure.cli.core.commands import LongRunningOperation
from ._utils import validate_premium_registry, get_registry_by_name

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
        Policy = cmd.get_models('Policies')
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
        'Policies', 'RetentionPolicy', 'RegistryUpdateParameters')

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

def acr_config_soft_delete_show(cmd,
                              registry_name):
    registry, _ = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)
    policies = registry.policies
    soft_delete_policy = policies.soft_delete_policy if policies else None
    return soft_delete_policy

def acr_config_soft_delete_update(cmd,
                                client,
                                registry_name,
                                status=None,
                                days=None):
    registry, resource_group_name = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    Policy, SoftDeletePolicy, RegistryUpdateParameters = cmd.get_models(
        'Policies','SoftDeletePolicy', 'RegistryUpdateParameters')

    policies = registry.policies
    if policies is None:
        policies = Policy()

    policies.soft_delete_policy = policies.soft_delete_policy if policies.soft_delete_policy else SoftDeletePolicy()

    if status:
        policies.soft_delete_policy.status = status

    if days is not None:
        policies.soft_delete_policy.retention_days = days

    parameters = RegistryUpdateParameters(policies=policies)

    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.begin_update(resource_group_name, registry_name, parameters)
    )
    return updated_policies.policies.soft_delete_policy