# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=redefined-builtin

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import BadRequestError
from azure.mgmt.media.models import (MediaService, AccountEncryption, KeyVaultProperties, ResourceIdentity, AccountEncryptionKeyType,
                                     MediaServiceUpdate)


def get_encryption(client, resource_group_name, account_name):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)
    return account_info.encryption


def set_encryption(client, resource_group_name, account_name, key_type=None,
                   current_key_id=None, key_identifier=None, system_assigned=None, user_assigned=None):
    try:
        account_info: MediaService = client.get(resource_group_name, account_name) if resource_group_name else client.get_by_subscription(account_name)
        if key_type == AccountEncryptionKeyType.CUSTOMER_KEY:
            key_vault_props = KeyVaultProperties(key_identifier=key_identifier,
                                                 current_key_identifier=current_key_id)

            if user_assigned:
                identity = ResourceIdentity(use_system_assigned_identity=False,
                                            user_assigned_identity=user_assigned)
            elif system_assigned:
                identity = ResourceIdentity(use_system_assigned_identity=True,
                                            user_assigned_identity=None)
            else:
                identity = None

            encryption = AccountEncryption(type=key_type, key_vault_properties=key_vault_props, identity=identity)
        else:
            encryption = AccountEncryption(type=key_type, key_vault_properties=None, identity=None)

        media_service: MediaService = MediaService(location=account_info.location, storage_accounts=account_info.storage_accounts,
                                                   key_delivery=account_info.key_delivery, identity=account_info.identity,
                                                   encryption=encryption,storage_authentication=account_info.storage_authentication, 
                                                   name=account_info.name, public_network_access=account_info.public_network_access)
        print(encryption)
        return client.create_or_update(resource_group_name, account_name, media_service)
    except HttpResponseError as ex:
        recommendation = ''
        if ex.message == '(BadRequest) Access to the Customer Key was forbidden.':
            recommendation = 'Please use the Azure Portal to grant the key vault access to the media account.'\
                             'For more information please visit https://aka.ms/keyvaultaccess'
        raise BadRequestError(ex, recommendation)
