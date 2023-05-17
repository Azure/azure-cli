# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=too-many-locals

from azure.cli.core.profiles import ResourceType
from knack.log import get_logger

logger = get_logger(__name__)


# Namespace Region
def cli_namespace_create(cmd, client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard', capacity=None,
                         is_auto_inflate_enabled=None, maximum_throughput_units=None, is_kafka_enabled=None, zone_redundant=None, cluster_arm_id=None,
                         disable_local_auth=None, mi_system_assigned=None, mi_user_assigned=None, encryption_config=None, minimum_tls_version=None, require_infrastructure_encryption=None):
    EHNamespace = cmd.get_models('EHNamespace', resource_type=ResourceType.MGMT_EVENTHUB)
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_EVENTHUB)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_EVENTHUB)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_EVENTHUB)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_EVENTHUB)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2018-01-01-preview'):
        ehparam = EHNamespace()
        ehparam.location = location
        ehparam.tags = tags
        ehparam.sku = Sku(name=sku, tier=sku, capacity=capacity)
        ehparam.is_auto_inflate_enabled = is_auto_inflate_enabled
        ehparam.maximum_throughput_units = maximum_throughput_units
        ehparam.kafka_enabled = is_kafka_enabled
        ehparam.zone_redundant = zone_redundant
        ehparam.disable_local_auth = disable_local_auth
        ehparam.cluster_arm_id = cluster_arm_id
        ehparam.minimum_tls_version = minimum_tls_version

        if mi_system_assigned:
            ehparam.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)

        if mi_user_assigned:
            if ehparam.identity:
                if ehparam.identity.type == IdentityType.SYSTEM_ASSIGNED:
                    ehparam.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED
                else:
                    ehparam.identity.type = IdentityType.USER_ASSIGNED
            else:
                ehparam.identity = Identity(type=IdentityType.USER_ASSIGNED)

            default_user_identity = UserAssignedIdentity()
            ehparam.identity.user_assigned_identities = dict.fromkeys(mi_user_assigned, default_user_identity)

        if encryption_config:
            ehparam.encryption = Encryption()
            ehparam.encryption.key_vault_properties = encryption_config

        if require_infrastructure_encryption is not None:
            if ehparam.encryption is None:
                ehparam.encryption = Encryption()
            ehparam.encryption.require_infrastructure_encryption = require_infrastructure_encryption

        client.begin_create_or_update(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            parameters=ehparam).result()

    return client.get(resource_group_name, namespace_name)


def cli_namespace_update(cmd, instance, tags=None, sku=None, capacity=None, is_auto_inflate_enabled=None,
                         maximum_throughput_units=None, is_kafka_enabled=None,
                         disable_local_auth=None, require_infrastructure_encryption=None, minimum_tls_version=None):
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_EVENTHUB)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2021-06-01-preview'):
        if tags:
            instance.tags = tags

        if sku:
            instance.sku.name = sku
            instance.sku.tier = sku

        if capacity:
            instance.sku.capacity = capacity

        if is_auto_inflate_enabled is not None:
            instance.is_auto_inflate_enabled = is_auto_inflate_enabled

        if maximum_throughput_units is not None:
            instance.maximum_throughput_units = maximum_throughput_units

        if is_kafka_enabled is not None:
            instance.kafka_enabled = is_kafka_enabled

        if minimum_tls_version:
            instance.minimum_tls_version = minimum_tls_version

        if require_infrastructure_encryption is not None:
            if instance.encryption is None:
                instance.encryption = Encryption()
            instance.encryption.require_infrastructure_encryption = require_infrastructure_encryption

        if disable_local_auth is not None:
            instance.disable_local_auth = disable_local_auth

    return instance


def cli_namespace_list(cmd, client, resource_group_name=None):
    if cmd.supported_api_version(min_api='2021-06-01-preview'):
        if resource_group_name:
            return client.list_by_resource_group(resource_group_name=resource_group_name)
    return client.list()


def cli_add_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_EVENTHUB)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_EVENTHUB)

    identity_id = {}

    if namespace.identity is None:
        namespace.identity = Identity()

    if system_assigned:
        if namespace.identity.type == IdentityType.USER_ASSIGNED:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED

        elif namespace.identity.type == IdentityType.NONE or namespace.identity.type is None:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED

    if user_assigned:
        default_user_identity = UserAssignedIdentity()
        identity_id.update(dict.fromkeys(user_assigned, default_user_identity))

        if namespace.identity.user_assigned_identities is None:
            namespace.identity.user_assigned_identities = identity_id
        else:
            namespace.identity.user_assigned_identities.update(identity_id)

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED

        elif namespace.identity.type == IdentityType.NONE or namespace.identity.type is None:
            namespace.identity.type = IdentityType.USER_ASSIGNED

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_remove_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)

    from azure.cli.core import CLIError

    if namespace.identity is None:
        raise CLIError('The namespace does not have identity enabled')

    if system_assigned:
        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED:
            namespace.identity.type = IdentityType.NONE

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            namespace.identity.type = IdentityType.USER_ASSIGNED

    if user_assigned:
        if namespace.identity.type == IdentityType.USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities) == 0:
                    namespace.identity.type = IdentityType.NONE
                    namespace.identity.user_assigned_identities = None

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities) == 0:
                    namespace.identity.type = IdentityType.SYSTEM_ASSIGNED
                    namespace.identity.user_assigned_identities = None

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_add_encryption(cmd, client, resource_group_name, namespace_name, encryption_config, require_infrastructure_encryption=None):
    namespace = client.get(resource_group_name, namespace_name)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_EVENTHUB)

    if namespace.encryption:
        if namespace.encryption.key_vault_properties:
            namespace.encryption.key_vault_properties.extend(encryption_config)
        else:
            namespace.encryption.key_vault_properties = encryption_config

    else:
        namespace.encryption = Encryption()
        namespace.encryption.key_vault_properties = encryption_config

    if require_infrastructure_encryption is not None:
        namespace.encryption.require_infrastructure_encryption = require_infrastructure_encryption

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_remove_encryption(client, resource_group_name, namespace_name, encryption_config):
    namespace = client.get(resource_group_name, namespace_name)

    from azure.cli.core import CLIError

    if namespace.encryption is None:
        raise CLIError('The namespace does not have encryption enabled')

    if namespace.encryption.key_vault_properties:
        for encryption_property in encryption_config:
            if encryption_property in namespace.encryption.key_vault_properties:
                namespace.encryption.key_vault_properties.remove(encryption_property)

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_appgroup_create(cmd, client, resource_group_name, namespace_name, application_group_name, client_app_group_identifier,
                        throttling_policy_config, is_enabled=None):
    ApplicationGroup = cmd.get_models('ApplicationGroup', resource_type=ResourceType.MGMT_EVENTHUB)
    appGroup = ApplicationGroup(policies=throttling_policy_config, client_app_group_identifier=client_app_group_identifier)

    if is_enabled is not None:
        ApplicationGroup.is_enabled = is_enabled

    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)


def cli_appgroup_update(client, resource_group_name, namespace_name, application_group_name, is_enabled=None):
    appGroup = client.get(resource_group_name, namespace_name, application_group_name)

    if is_enabled is not None:
        appGroup.is_enabled = is_enabled

    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)


def cli_add_appgroup_policy(client, resource_group_name, namespace_name, application_group_name, throttling_policy_config):
    appGroup = client.get(resource_group_name, namespace_name, application_group_name)
    appGroup.policies.extend(throttling_policy_config)
    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)


def cli_remove_appgroup_policy(client, resource_group_name, namespace_name, application_group_name, throttling_policy_config):
    from azure.cli.core import CLIError

    appGroup = client.get(resource_group_name, namespace_name, application_group_name)
    logger.warning(
        'This operation will do removals based on policy name. Will not accept metric-id,rate-limit-threshold in the future in future release.'
        'Also throttling_policy_config parameter will replace with "policy" in same future release.')
    if appGroup.policies:
        for policy_object in throttling_policy_config:
            if policy_object in appGroup.policies:
                appGroup.policies.remove(policy_object)
            else:
                raise CLIError('The following policy was not found: Name: ' + policy_object.name + ', RateLimitThreshold: ' + str(policy_object.rate_limit_threshold) + ', MetricId: ' + policy_object.metric_id)

    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)
