# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import time

from azure.cli.command_modules.appconfig._client_factory import cf_configstore, cf_replicas
from azure.cli.core.commands.progress import IndeterminateStandardOut
from azure.cli.core.util import user_confirmation
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.mgmt.appconfiguration.models import (ConfigurationStoreUpdateParameters,
                                                ConfigurationStore,
                                                Sku,
                                                ResourceIdentity,
                                                UserIdentity,
                                                EncryptionProperties,
                                                KeyVaultProperties,
                                                RegenerateKeyParameters,
                                                CreateMode,
                                                Replica,
                                                AuthenticationMode,
                                                PublicNetworkAccess,
                                                PrivateLinkDelegation,
                                                DataPlaneProxyProperties)
from knack.log import get_logger
from ._utils import resolve_store_metadata, resolve_deleted_store_metadata
from ._constants import ARMAuthenticationMode, ProvisioningStatus

logger = get_logger(__name__)

SYSTEM_ASSIGNED = 'SystemAssigned'
USER_ASSIGNED = 'UserAssigned'
SYSTEM_USER_ASSIGNED = 'SystemAssigned, UserAssigned'
SYSTEM_ASSIGNED_IDENTITY = '[system]'


def create_configstore(cmd,  # pylint: disable=too-many-locals
                       client,
                       resource_group_name,
                       name,
                       location,
                       sku="Standard",
                       tags=None,
                       assign_identity=None,
                       enable_public_network=None,
                       disable_local_auth=None,
                       retention_days=None,
                       enable_purge_protection=None,
                       replica_name=None,
                       replica_location=None,
                       no_replica=None,  # pylint: disable=unused-argument
                       arm_auth_mode=None,
                       enable_arm_private_network_access=None,
                       kv_revision_retention_period=None):
    if assign_identity is not None and not assign_identity:
        assign_identity = [SYSTEM_ASSIGNED_IDENTITY]

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = PublicNetworkAccess.ENABLED if enable_public_network else PublicNetworkAccess.DISABLED

    arm_private_link_delegation = None
    if enable_arm_private_network_access is not None:
        arm_private_link_delegation = PrivateLinkDelegation.ENABLED if enable_arm_private_network_access else PrivateLinkDelegation.DISABLED

    arm_authentication_mode = None
    if arm_auth_mode is not None:
        arm_authentication_mode = AuthenticationMode.LOCAL if arm_auth_mode == ARMAuthenticationMode.LOCAL else AuthenticationMode.PASS_THROUGH

    configstore_params = ConfigurationStore(location=location.lower(),
                                            identity=__get_resource_identity(assign_identity) if assign_identity else None,
                                            sku=Sku(name=sku),
                                            tags=tags,
                                            public_network_access=public_network_access,
                                            disable_local_auth=disable_local_auth,
                                            soft_delete_retention_in_days=retention_days,
                                            enable_purge_protection=enable_purge_protection,
                                            create_mode=CreateMode.DEFAULT,
                                            default_key_value_revision_retention_period_in_seconds=kv_revision_retention_period,
                                            data_plane_proxy=DataPlaneProxyProperties(
                                                authentication_mode=arm_authentication_mode,
                                                private_link_delegation=arm_private_link_delegation))

    progress = IndeterminateStandardOut()

    progress.write({"message": "Starting"})
    config_store = client.begin_create(resource_group_name, name, configstore_params)

    # # Poll request and create replica after store is created
    while config_store.status() != ProvisioningStatus.SUCCEEDED:
        progress.spinner.step(label="Creating store")
        config_store.wait(1)

    progress.write({"message": "Store created"})
    time.sleep(1)

    if replica_name is not None:
        replica_client = cf_replicas(cmd.cli_ctx)
        store_replica = create_replica(cmd, replica_client, name, replica_name, replica_location, resource_group_name)

        while store_replica.status() != ProvisioningStatus.SUCCEEDED:
            progress.spinner.step(label="Creating replica")
            store_replica.wait(1)

        if store_replica.status() == ProvisioningStatus.SUCCEEDED:
            progress.write({"message": "Replica created"})
            time.sleep(1)
        else:
            progress.write({"message": "Replica creation failed"})

    progress.clear()

    return config_store


def recover_deleted_configstore(cmd, client, name, resource_group_name=None, location=None):
    if resource_group_name is None or location is None:
        metadata_resource_group, metadata_location = resolve_deleted_store_metadata(cmd, name, resource_group_name, location)

        if resource_group_name is None:
            resource_group_name = metadata_resource_group
        if location is None:
            location = metadata_location

    configstore_params = ConfigurationStore(location=location.lower(),
                                            sku=Sku(name="Standard"),  # Only Standard SKU stores can be recovered!
                                            create_mode=CreateMode.RECOVER)

    return client.begin_create(resource_group_name, name, configstore_params)


def delete_configstore(cmd, client, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)

    return client.begin_delete(resource_group_name, name)


def purge_deleted_configstore(cmd, client, name, location=None):
    if location is None:
        _, location = resolve_deleted_store_metadata(cmd, name)

    return client.begin_purge_deleted(config_store_name=name, location=location)


def list_configstore(client, resource_group_name=None):
    response = client.list() if resource_group_name is None else client.list_by_resource_group(resource_group_name)
    return response


def list_deleted_configstore(client):
    response = client.list_deleted()
    return response


def show_configstore(cmd, client, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)
    return client.get(resource_group_name, name)


def show_deleted_configstore(cmd, client, name, location=None):
    if location is None:
        _, location = resolve_deleted_store_metadata(cmd, name)
    return client.get_deleted(config_store_name=name, location=location)


def update_configstore(cmd,  # pylint: disable=too-many-locals
                       client,
                       name,
                       resource_group_name=None,
                       tags=None,
                       sku=None,
                       encryption_key_name=None,
                       encryption_key_vault=None,
                       encryption_key_version=None,
                       identity_client_id=None,
                       enable_public_network=None,
                       disable_local_auth=None,
                       enable_purge_protection=None,
                       arm_auth_mode=None,
                       enable_arm_private_network_access=None,
                       kv_revision_retention_period=None):
    __validate_cmk(encryption_key_name, encryption_key_vault, encryption_key_version, identity_client_id)
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = PublicNetworkAccess.ENABLED if enable_public_network else PublicNetworkAccess.DISABLED

    arm_private_link_delegation = None
    if enable_arm_private_network_access is not None:
        arm_private_link_delegation = PrivateLinkDelegation.ENABLED if enable_arm_private_network_access else PrivateLinkDelegation.DISABLED

    arm_authentication_mode = None
    if arm_auth_mode is not None:
        arm_authentication_mode = AuthenticationMode.LOCAL if arm_auth_mode == ARMAuthenticationMode.LOCAL else AuthenticationMode.PASS_THROUGH

    update_params = ConfigurationStoreUpdateParameters(tags=tags,
                                                       sku=Sku(name=sku) if sku else None,
                                                       public_network_access=public_network_access,
                                                       disable_local_auth=disable_local_auth,
                                                       enable_purge_protection=enable_purge_protection,
                                                       default_key_value_revision_retention_period_in_seconds=kv_revision_retention_period,
                                                       data_plane_proxy=DataPlaneProxyProperties(
                                                           authentication_mode=arm_authentication_mode,
                                                           private_link_delegation=arm_private_link_delegation))

    if encryption_key_name is not None:
        key_vault_properties = KeyVaultProperties()
        if encryption_key_name:
            # key identifier schema https://keyvaultname.vault-int.azure-int.net/keys/keyname/keyversion
            key_identifier = "{}/keys/{}/{}".format(encryption_key_vault.strip('/'), encryption_key_name, encryption_key_version if encryption_key_version else "")
            key_vault_properties = KeyVaultProperties(key_identifier=key_identifier, identity_client_id=identity_client_id)

        update_params.encryption = EncryptionProperties(key_vault_properties=key_vault_properties)

    return client.begin_update(
        resource_group_name=resource_group_name,
        config_store_name=name,
        config_store_update_parameters=update_params,
    )


def assign_managed_identity(cmd, client, name, resource_group_name=None, identities=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)

    if not identities:
        identities = [SYSTEM_ASSIGNED_IDENTITY]

    current_identities = show_managed_identity(cmd, client, name, resource_group_name)
    user_assigned_identities = {}
    identity_types = set()

    if current_identities:
        identity_types = identity_types if current_identities.type == 'None' else {identity_type.strip() for identity_type in current_identities.type.split(',')}
        user_assigned_identities = current_identities.user_assigned_identities if current_identities.user_assigned_identities else {}

    if SYSTEM_ASSIGNED_IDENTITY in identities:
        identities.remove(SYSTEM_ASSIGNED_IDENTITY)
        identity_types.add(SYSTEM_ASSIGNED)

    user_assigned_identities.update({identity: UserIdentity() for identity in identities})
    if user_assigned_identities:
        identity_types.add(USER_ASSIGNED)

    managed_identities = ResourceIdentity(type=','.join(identity_types) if identity_types else 'None',
                                          user_assigned_identities=user_assigned_identities if user_assigned_identities else None)

    client.begin_update(resource_group_name=resource_group_name,
                        config_store_name=name,
                        config_store_update_parameters=ConfigurationStoreUpdateParameters(identity=managed_identities))

    # Due to a bug in RP https://msazure.visualstudio.com/Azure%20AppConfig/_workitems/edit/6017040
    # It client.update does not return the updated identities.
    return show_managed_identity(cmd, client, name, resource_group_name)


def remove_managed_identity(cmd, client, name, resource_group_name=None, identities=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)

    current_identities = show_managed_identity(cmd, client, name, resource_group_name)
    if not current_identities or current_identities.type == 'None':
        logger.warning("No identity associated with this App Configuration.")
        return

    if not identities:
        identities = [SYSTEM_ASSIGNED_IDENTITY]

    user_assigned_identities = {}
    if '[all]' in identities:
        identity_types = None
    else:
        identity_types = {identity_type.strip() for identity_type in current_identities.type.split(',')}

        if current_identities.user_assigned_identities:
            for identity in current_identities.user_assigned_identities:
                if identity not in identities:
                    user_assigned_identities[identity] = current_identities.user_assigned_identities[identity]

        if SYSTEM_ASSIGNED_IDENTITY in identities:
            identity_types.discard(SYSTEM_ASSIGNED)

        if not user_assigned_identities:
            identity_types.discard(USER_ASSIGNED)

    managed_identities = ResourceIdentity(type=','.join(identity_types) if identity_types else 'None',
                                          user_assigned_identities=user_assigned_identities if user_assigned_identities else None)

    client.begin_update(resource_group_name=resource_group_name,
                        config_store_name=name,
                        config_store_update_parameters=ConfigurationStoreUpdateParameters(identity=managed_identities))


def show_managed_identity(cmd, client, name, resource_group_name=None):
    config_store = show_configstore(cmd, client, name, resource_group_name)
    return config_store.identity if config_store.identity else {}


def list_credential(cmd, client, name, resource_group_name=None):
    resource_group_name, _ = resolve_store_metadata(cmd, name)
    return client.list_keys(resource_group_name, name)


def regenerate_credential(cmd, client, name, id_, resource_group_name=None):
    resource_group_name, _ = resolve_store_metadata(cmd, name)
    return client.regenerate_key(resource_group_name, name, RegenerateKeyParameters(id=id_))


def list_replica(cmd, client, store_name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)

    return client.list_by_configuration_store(resource_group_name=resource_group_name, config_store_name=store_name)


def show_replica(cmd, client, store_name, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)
    try:
        return client.get(resource_group_name=resource_group_name, config_store_name=store_name, replica_name=name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError("The replica '{}' for App Configuration '{}' not found.".format(name, store_name))


def create_replica(cmd, client, store_name, name, location, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)

    replica_creation_params = Replica(location=location)
    return client.begin_create(resource_group_name=resource_group_name,
                               config_store_name=store_name,
                               replica_name=name,
                               replica_creation_parameters=replica_creation_params)


def delete_replica(cmd, client, store_name, name, yes=False, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)

    if not yes:
        config_store_client = cf_configstore(cmd.cli_ctx)
        config_store = show_configstore(
            cmd, config_store_client, store_name, resource_group_name
        )
        replicas = list_replica(cmd, client, store_name, resource_group_name)

        if config_store.sku.name.lower() == "premium" and len(list(replicas)) == 1:
            user_confirmation(
                "Deleting the last replica will disable geo-replication. It is recommended that a premium tier store have geo-replication enabled to take advantage of the improved SLA. The first replica for a premium tier store comes at no additional cost. Do you want to continue?"
            )
        else:
            user_confirmation("Are you sure you want to continue with this operation?")

    return client.begin_delete(
        resource_group_name=resource_group_name,
        config_store_name=store_name,
        replica_name=name,
    )


def __get_resource_identity(assign_identity):
    system_assigned = False
    user_assigned = {}
    for identity in assign_identity:
        if identity == SYSTEM_ASSIGNED_IDENTITY:
            system_assigned = True
        else:
            user_assigned[identity] = UserIdentity()

    if system_assigned and user_assigned:
        identity_type = SYSTEM_USER_ASSIGNED
    elif system_assigned:
        identity_type = SYSTEM_ASSIGNED
    elif user_assigned:
        identity_type = USER_ASSIGNED
    else:
        identity_type = "None"

    return ResourceIdentity(type=identity_type,
                            user_assigned_identities=user_assigned if user_assigned else None)


def __validate_cmk(encryption_key_name=None,
                   encryption_key_vault=None,
                   encryption_key_version=None,
                   identity_client_id=None):
    if encryption_key_name is None:
        if any(arg is not None for arg in [encryption_key_vault, encryption_key_version, identity_client_id]):
            raise RequiredArgumentMissingError("To modify customer encryption key --encryption-key-name is required")
    else:
        if encryption_key_name:
            if encryption_key_vault is None:
                raise RequiredArgumentMissingError("To modify customer encryption key --encryption-key-vault is required")
        else:
            if any(arg is not None for arg in [encryption_key_vault, encryption_key_version, identity_client_id]):
                logger.warning("Removing the customer encryption key. Key vault related arguments are ignored.")
