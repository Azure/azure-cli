# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import user_confirmation
from knack.log import get_logger, CLIError

from ._utils import validate_premium_registry, get_registry_by_name


POLICIES_NOT_SUPPORTED = 'Policies are only supported for managed registries in Premium SKU.'
logger = get_logger(__name__)


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
                                  days=None,
                                  yes=False):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, None)

    Policy, SoftDeletePolicy, RegistryUpdateParameters = cmd.get_models(
        'Policies', 'SoftDeletePolicy', 'RegistryUpdateParameters')

    policies = registry.policies
    if policies is None:
        policies = Policy()

    policies.soft_delete_policy = policies.soft_delete_policy if policies.soft_delete_policy else SoftDeletePolicy()

    if status:
        if (policies.soft_delete_policy.status == 'enabled' and status == 'disabled'):
            logger.warning("Disabling soft-delete does not affect purge behavior for previously deleted artifacts."
                           " Artifacts currently in a soft-deleted state will continue to be purged in accordance"
                           " with the current soft-delete retention days policy.")
        policies.soft_delete_policy.status = status

    if days is not None:
        if policies.soft_delete_policy.retention_days > days:
            user_confirmation("Soft-delete purge scheduling is determined by a registry's current soft-delete retention"
                              " days policy at the time of purge. By reducing the retention days policy, you are"
                              " changing the scheduled purge date of previously deleted artifacts. In doing so, you may"
                              " be scheduling some artifacts in a soft-deleted state for immediate purge. Do you wish"
                              " to proceed?", yes)

        policies.soft_delete_policy.retention_days = days

    parameters = RegistryUpdateParameters(policies=policies)

    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.begin_update(resource_group_name, registry_name, parameters)
    )
    return updated_policies.policies.soft_delete_policy


def acr_config_authentication_as_arm_show(cmd,
                                          registry_name,
                                          resource_group_name=None):

    AzureADAuthenticationAsArmPolicy = cmd.get_models('AzureADAuthenticationAsArmPolicy')

    try:
        registry, _ = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)
    except CLIError:
        return AzureADAuthenticationAsArmPolicy()

    AzureADAuthenticationAsArmPolicy = cmd.get_models('AzureADAuthenticationAsArmPolicy')
    policies = registry.policies

    # On AzureStackHub, the 2019-05-01 API version is still in use, so we need to check if the
    # 'azure_ad_authentication_as_arm_policy' attribute exists before we invoke it
    if policies and hasattr(policies, 'azure_ad_authentication_as_arm_policy'):
        return policies.azure_ad_authentication_as_arm_policy

    return AzureADAuthenticationAsArmPolicy


def acr_config_authentication_as_arm_update(cmd,
                                            client,
                                            registry_name,
                                            status=None,
                                            resource_group_name=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)
    policies = registry.policies
    if status:
        Policy = cmd.get_models('Policy')
        policies = policies if policies else Policy()
        AzureADAuthenticationAsArmPolicy = cmd.get_models('AzureADAuthenticationAsArmPolicy')
        policies.azure_ad_authentication_as_arm_policy = policies.azure_ad_authentication_as_arm_policy \
            if policies.azure_ad_authentication_as_arm_policy else AzureADAuthenticationAsArmPolicy()
        policies.azure_ad_authentication_as_arm_policy.status = status

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(policies=policies)
    updated_policies = LongRunningOperation(cmd.cli_ctx)(
        client.begin_update(resource_group_name, registry_name, parameters)
    )

    return updated_policies.policies.azure_ad_authentication_as_arm_policy
