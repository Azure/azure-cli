# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.util import CLIError
from knack.log import get_logger
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.appconfiguration.models import (ConfigurationStoreUpdateParameters,
                                                ConfigurationStore,
                                                Sku,
                                                ResourceIdentity,
                                                UserIdentity,
                                                EncryptionProperties,
                                                KeyVaultProperties,
                                                RegenerateKeyParameters, CreateMode, Replica)
from azure.cli.core.util import user_confirmation

from ._utils import resolve_store_metadata, resolve_deleted_store_metadata

logger = get_logger(__name__)

SYSTEM_ASSIGNED = 'SystemAssigned'
USER_ASSIGNED = 'UserAssigned'
SYSTEM_USER_ASSIGNED = 'SystemAssigned, UserAssigned'
SYSTEM_ASSIGNED_IDENTITY = '[system]'


def create_configstore(client,
                       resource_group_name,
                       name,
                       location,
                       sku="Standard",
                       tags=None,
                       assign_identity=None,
                       enable_public_network=None,
                       disable_local_auth=None,
                       retention_days=None,
                       enable_purge_protection=None):
    if assign_identity is not None and not assign_identity:
        assign_identity = [SYSTEM_ASSIGNED_IDENTITY]

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = 'Enabled' if enable_public_network else 'Disabled'

    if sku.lower() == 'free' and (enable_purge_protection or retention_days):
        logger.warning("Options '--enable-purge-protection' and '--retention-days' will be ignored when creating a free store.")
        retention_days = None
        enable_purge_protection = None

    configstore_params = ConfigurationStore(location=location.lower(),
                                            identity=__get_resource_identity(assign_identity) if assign_identity else None,
                                            sku=Sku(name=sku),
                                            tags=tags,
                                            public_network_access=public_network_access,
                                            disable_local_auth=disable_local_auth,
                                            soft_delete_retention_in_days=retention_days,
                                            enable_purge_protection=enable_purge_protection,
                                            create_mode=CreateMode.DEFAULT)

    return client.begin_create(resource_group_name, name, configstore_params)


def recover_deleted_configstore(cmd, client, name, resource_group_name=None, location=None, yes=False):
    if resource_group_name is None or location is None:
        metadata_resource_group, metadata_location = resolve_deleted_store_metadata(cmd, name, resource_group_name, location)

        if resource_group_name is None:
            resource_group_name = metadata_resource_group
        if location is None:
            location = metadata_location

    configstore_params = ConfigurationStore(location=location.lower(),
                                            sku=Sku(name="Standard"),  # Only Standard SKU stores can be recovered!
                                            create_mode=CreateMode.RECOVER)
    user_confirmation("Are you sure you want to recover the App Configuration: {}".format(name), yes)
    return client.begin_create(resource_group_name, name, configstore_params)


def delete_configstore(cmd, client, name, resource_group_name=None, yes=False):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)
    confirmation_message = "Are you sure you want to delete the App Configuration: {}".format(name)
    user_confirmation(confirmation_message, yes)
    return client.begin_delete(resource_group_name, name)


def purge_deleted_configstore(cmd, client, name, location=None, yes=False):
    if location is None:
        _, location = resolve_deleted_store_metadata(cmd, name)
    confirmation_message = "This operation will permanently delete App Configuration and it's contents.\nAre you sure you want to purge the App Configuration: {}".format(name)
    user_confirmation(confirmation_message, yes)
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


def update_configstore(cmd,
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
                       enable_purge_protection=None):
    __validate_cmk(encryption_key_name, encryption_key_vault, encryption_key_version, identity_client_id)
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, name)

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = 'Enabled' if enable_public_network else 'Disabled'
    update_params = ConfigurationStoreUpdateParameters(tags=tags,
                                                       sku=Sku(name=sku) if sku else None,
                                                       public_network_access=public_network_access,
                                                       disable_local_auth=disable_local_auth,
                                                       enable_purge_protection=enable_purge_protection)

    if encryption_key_name is not None:
        key_vault_properties = KeyVaultProperties()
        if encryption_key_name:
            # key identifier schema https://keyvaultname.vault-int.azure-int.net/keys/keyname/keyversion
            key_identifier = "{}/keys/{}/{}".format(encryption_key_vault.strip('/'), encryption_key_name, encryption_key_version if encryption_key_version else "")
            key_vault_properties = KeyVaultProperties(key_identifier=key_identifier, identity_client_id=identity_client_id)

        update_params.encryption = EncryptionProperties(key_vault_properties=key_vault_properties)

    return client.begin_update(resource_group_name=resource_group_name,
                               config_store_name=name,
                               config_store_update_parameters=update_params)


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
        # Show a meaningful error message than the one coming from the server.
        raise ResourceNotFoundError("The replica '{}' for App Configuration '{}' not found.".format(name, store_name))


def create_replica(cmd, client, store_name, name, location, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)

    replica_creation_params = Replica(location=location)
    return client.begin_create(resource_group_name=resource_group_name,
                               config_store_name=store_name,
                               replica_name=name,
                               replica_creation_parameters=replica_creation_params)


def delete_replica(cmd, client, store_name, name, resource_group_name=None, yes=False):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)

    user_confirmation("Are you sure you want to delete the replica '{}' for the App Configuration '{}'".format(name, store_name), yes)
    return client.begin_delete(resource_group_name=resource_group_name,
                               config_store_name=store_name,
                               replica_name=name)


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
            raise CLIError("To modify customer encryption key --encryption-key-name is required")
    else:
        if encryption_key_name:
            if encryption_key_vault is None:
                raise CLIError("To modify customer encryption key --encryption-key-vault is required")
        else:
            if any(arg is not None for arg in [encryption_key_vault, encryption_key_version, identity_client_id]):
                logger.warning("Removing the customer encryption key. Key vault related arguments are ignored.")
