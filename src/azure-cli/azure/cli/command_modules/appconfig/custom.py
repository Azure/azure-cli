# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from knack.util import CLIError
from knack.log import get_logger
from azure.mgmt.appconfiguration.models import (ConfigurationStoreUpdateParameters,
                                                ConfigurationStore,
                                                Sku,
                                                ResourceIdentity,
                                                UserIdentity,
                                                EncryptionProperties,
                                                KeyVaultProperties)

from ._utils import resolve_resource_group, user_confirmation


logger = get_logger(__name__)

SYSTEM_ASSIGNED = 'SystemAssigned'
USER_ASSIGNED = 'UserAssigned'
SYSTEM_USER_ASSIGNED = 'SystemAssigned, UserAssigned'
SYSTEM_ASSIGNED_IDENTITY = '[system]'


def create_configstore(client, resource_group_name, name, location, sku="Standard", assign_identity=None):
    if assign_identity is not None and not assign_identity:
        assign_identity = [SYSTEM_ASSIGNED_IDENTITY]

    configstore_params = ConfigurationStore(location=location.lower(),
                                            identity=__get_resource_identity(assign_identity) if assign_identity else None,
                                            sku=Sku(name=sku))

    return client.create(resource_group_name, name, configstore_params)


def delete_configstore(cmd, client, name, resource_group_name=None, yes=False):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)
    confirmation_message = "Are you sure you want to delete the App Configuration: {}".format(
        name)
    user_confirmation(confirmation_message, yes)
    return client.delete(resource_group_name, name)


def list_configstore(client, resource_group_name=None):
    response = client.list() if resource_group_name is None else client.list_by_resource_group(
        resource_group_name)
    return response


def show_configstore(cmd, client, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)
    return client.get(resource_group_name, name)


def update_configstore(cmd,
                       client,
                       name,
                       resource_group_name=None,
                       tags=None,
                       sku=None,
                       encryption_key_name=None,
                       encryption_key_vault=None,
                       encryption_key_version=None,
                       identity_client_id=None):
    __validate_cmk(encryption_key_name, encryption_key_vault, encryption_key_version, identity_client_id)
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)

    update_params = ConfigurationStoreUpdateParameters(tags=tags if tags else None,
                                                       sku=Sku(name=sku) if sku else None)

    if encryption_key_name is not None:
        key_vault_properties = KeyVaultProperties()
        if encryption_key_name:
            # key identifier schema https://keyvaultname.vault-int.azure-int.net/keys/keyname/keyversion
            key_identifier = "{}/keys/{}/{}".format(encryption_key_vault.strip('/'), encryption_key_name, encryption_key_version if encryption_key_version else "")
            key_vault_properties = KeyVaultProperties(key_identifier=key_identifier, identity_client_id=identity_client_id)

        update_params.encryption = EncryptionProperties(key_vault_properties=key_vault_properties)

    return client.update(resource_group_name=resource_group_name,
                         config_store_name=name,
                         config_store_update_parameters=update_params)


def assign_managed_identity(cmd, client, name, resource_group_name=None, identities=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)

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

    client.update(resource_group_name=resource_group_name,
                  config_store_name=name,
                  config_store_update_parameters=ConfigurationStoreUpdateParameters(identity=managed_identities))

    # Due to a bug in RP https://msazure.visualstudio.com/Azure%20AppConfig/_workitems/edit/6017040
    # It client.update does not return the updated identities.
    return show_managed_identity(cmd, client, name, resource_group_name)


def remove_managed_identity(cmd, client, name, resource_group_name=None, identities=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)

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

    client.update(resource_group_name=resource_group_name,
                  config_store_name=name,
                  config_store_update_parameters=ConfigurationStoreUpdateParameters(identity=managed_identities))


def show_managed_identity(cmd, client, name, resource_group_name=None):
    config_store = show_configstore(cmd, client, name, resource_group_name)

    return config_store.identity if config_store.identity else {}


def list_credential(cmd, client, name, resource_group_name=None):
    resource_group_name, endpoint = resolve_resource_group(cmd, name)
    credentials = client.list_keys(resource_group_name, name)
    augmented_credentials = []

    for credentail in credentials:
        augmented_credential = __convert_api_key_to_json(credentail, endpoint)
        augmented_credentials.append(augmented_credential)
    return augmented_credentials


def regenerate_credential(cmd, client, name, id_, resource_group_name=None):
    resource_group_name, endpoint = resolve_resource_group(cmd, name)
    credentail = client.regenerate_key(resource_group_name, name, id_)
    return __convert_api_key_to_json(credentail, endpoint)


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


def __convert_api_key_to_json(credentail, endpoint):
    augmented_credential = {}
    augmented_credential['id'] = credentail.id
    augmented_credential['name'] = credentail.name
    augmented_credential['value'] = credentail.value
    augmented_credential['lastModified'] = credentail.last_modified
    augmented_credential['readOnly'] = credentail.read_only
    augmented_credential['connectionString'] = 'Endpoint=' + \
        endpoint + ';Id=' + credentail.id + ';Secret=' + credentail.value
    return augmented_credential
