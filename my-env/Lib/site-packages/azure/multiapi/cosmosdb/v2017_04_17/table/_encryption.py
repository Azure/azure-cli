# -------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------------------------

import os
from copy import deepcopy
from json import (
    dumps,
    loads,
)

from azure.common import AzureException
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import (
    Hash,
    SHA256,
)
from cryptography.hazmat.primitives.padding import PKCS7

from ..common._common_conversion import (
    _decode_base64_to_bytes,
)
from ..common._constants import (
    _ENCRYPTION_PROTOCOL_V1,
)
from ..common._encryption import (
    _generate_encryption_data_dict,
    _dict_to_encryption_data,
    _generate_AES_CBC_cipher,
    _validate_and_unwrap_cek,
    _EncryptionAlgorithm
)
from ..common._error import (
    _ERROR_DECRYPTION_FAILURE,
    _ERROR_UNSUPPORTED_ENCRYPTION_ALGORITHM,
    _validate_not_none,
    _validate_key_encryption_key_wrap,
)
from ._error import (
    _ERROR_UNSUPPORTED_TYPE_FOR_ENCRYPTION,
    _ERROR_ENTITY_NOT_ENCRYPTED
)
from .models import (
    Entity,
    EntityProperty,
    EdmType,
)


def _encrypt_entity(entity, key_encryption_key, encryption_resolver):
    '''
    Encrypts the given entity using AES256 in CBC mode with 128 bit padding.
    Will generate a content-encryption-key (cek) to encrypt the properties either
    stored in an EntityProperty with the 'encrypt' flag set or those
    specified by the encryption resolver. This cek is then wrapped using the 
    provided key_encryption_key (kek). Only strings may be encrypted and the
    result is stored as binary on the service. 

    :param entity:
        The entity to insert. Could be a dict or an entity object.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        wrap_key(key)--wraps the specified key using an algorithm of the user's choice.
        get_key_wrap_algorithm()--returns the algorithm used to wrap the specified symmetric key.
        get_kid()--returns a string key id for this key-encryption-key.
    :param function(partition_key, row_key, property_name) encryption_resolver:
        A function that takes in an entities partition key, row key, and property name and returns 
        a boolean that indicates whether that property should be encrypted.
    :return: An entity with both the appropriate properties encrypted and the 
        encryption data.
    :rtype: object
    '''

    _validate_not_none('entity', entity)
    _validate_not_none('key_encryption_key', key_encryption_key)
    _validate_key_encryption_key_wrap(key_encryption_key)

    # AES256 uses 256 bit (32 byte) keys and always with 16 byte blocks
    content_encryption_key = os.urandom(32)
    entity_initialization_vector = os.urandom(16)

    encrypted_properties = []
    encrypted_entity = Entity()
    for key, value in entity.items():
        # If the property resolver says it should be encrypted
        # or it is an EntityProperty with the 'encrypt' property set.
        if (isinstance(value, EntityProperty) and value.encrypt) or \
                (encryption_resolver is not None \
                         and encryption_resolver(entity['PartitionKey'], entity['RowKey'], key)):

            # Only strings can be encrypted and None is not an instance of str.
            if isinstance(value, EntityProperty):
                if value.type == EdmType.STRING:
                    value = value.value
                else:
                    raise ValueError(_ERROR_UNSUPPORTED_TYPE_FOR_ENCRYPTION)
            if not isinstance(value, str):
                raise ValueError(_ERROR_UNSUPPORTED_TYPE_FOR_ENCRYPTION)

                # Value is now confirmed to hold a valid string value to be encrypted
            # and should be added to the list of encrypted properties.
            encrypted_properties.append(key)

            propertyIV = _generate_property_iv(entity_initialization_vector,
                                               entity['PartitionKey'], entity['RowKey'],
                                               key, False)

            # Encode the strings for encryption.
            value = value.encode('utf-8')

            cipher = _generate_AES_CBC_cipher(content_encryption_key, propertyIV)

            # PKCS7 with 16 byte blocks ensures compatibility with AES.
            padder = PKCS7(128).padder()
            padded_data = padder.update(value) + padder.finalize()

            # Encrypt the data.
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

            # Set the new value of this key to be a binary EntityProperty for proper serialization.
            value = EntityProperty(EdmType.BINARY, encrypted_data)

        encrypted_entity[key] = value

    encrypted_properties = dumps(encrypted_properties)

    # Generate the metadata iv.
    metadataIV = _generate_property_iv(entity_initialization_vector,
                                       entity['PartitionKey'], entity['RowKey'],
                                       '_ClientEncryptionMetadata2', False)

    encrypted_properties = encrypted_properties.encode('utf-8')

    cipher = _generate_AES_CBC_cipher(content_encryption_key, metadataIV)

    padder = PKCS7(128).padder()
    padded_data = padder.update(encrypted_properties) + padder.finalize()

    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    encrypted_entity['_ClientEncryptionMetadata2'] = EntityProperty(EdmType.BINARY, encrypted_data)

    encryption_data = _generate_encryption_data_dict(key_encryption_key, content_encryption_key,
                                                     entity_initialization_vector)

    encrypted_entity['_ClientEncryptionMetadata1'] = dumps(encryption_data)
    return encrypted_entity


def _decrypt_entity(entity, encrypted_properties_list, content_encryption_key, entityIV, isJavaV1):
    '''
    Decrypts the specified entity using AES256 in CBC mode with 128 bit padding. Unwraps the CEK 
    using either the specified KEK or the key returned by the key_resolver. Properties 
    specified in the encrypted_properties_list, will be decrypted and decoded to utf-8 strings.

    :param entity:
        The entity being retrieved and decrypted. Could be a dict or an entity object.
    :param list encrypted_properties_list:
        The encrypted list of all the properties that are encrypted.
    :param bytes[] content_encryption_key:
        The key used internally to encrypt the entity. Extrated from the entity metadata.
    :param bytes[] entityIV:
        The intialization vector used to seed the encryption algorithm. Extracted from the
        entity metadata.
    :return: The decrypted entity
    :rtype: Entity
    '''

    _validate_not_none('entity', entity)

    decrypted_entity = deepcopy(entity)
    try:
        for property in entity.keys():
            if property in encrypted_properties_list:
                value = entity[property]

                propertyIV = _generate_property_iv(entityIV,
                                                   entity['PartitionKey'], entity['RowKey'],
                                                   property, isJavaV1)
                cipher = _generate_AES_CBC_cipher(content_encryption_key,
                                                  propertyIV)

                # Decrypt the property.
                decryptor = cipher.decryptor()
                decrypted_data = (decryptor.update(value.value) + decryptor.finalize())

                # Unpad the data.
                unpadder = PKCS7(128).unpadder()
                decrypted_data = (unpadder.update(decrypted_data) + unpadder.finalize())

                decrypted_data = decrypted_data.decode('utf-8')

                decrypted_entity[property] = decrypted_data

        decrypted_entity.pop('_ClientEncryptionMetadata1')
        decrypted_entity.pop('_ClientEncryptionMetadata2')
        return decrypted_entity
    except:
        raise AzureException(_ERROR_DECRYPTION_FAILURE)


def _extract_encryption_metadata(entity, require_encryption, key_encryption_key, key_resolver):
    '''
    Extracts the encryption metadata from the given entity, setting them to be utf-8 strings.
    If no encryption metadata is present, will return None for all return values unless
    require_encryption is true, in which case the method will throw.

    :param entity:
        The entity being retrieved and decrypted. Could be a dict or an entity object.
    :param bool require_encryption:
        If set, will enforce that the retrieved entity is encrypted and decrypt it.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        unwrap_key(key, algorithm)--returns the unwrapped form of the specified symmetric key using the 
        string-specified algorithm.
        get_kid()--returns a string key id for this key-encryption-key.
    :param function key_resolver(kid):
        The user-provided key resolver. Uses the kid string to return a key-encryption-key implementing
        the interface defined above.
    :returns: a tuple containing the entity iv, the list of encrypted properties, the entity cek,
        and whether the entity was encrypted using JavaV1.
    :rtype: tuple (bytes[], list, bytes[], bool)
    '''
    _validate_not_none('entity', entity)

    try:
        encrypted_properties_list = _decode_base64_to_bytes(entity['_ClientEncryptionMetadata2'])
        encryption_data = entity['_ClientEncryptionMetadata1']
        encryption_data = _dict_to_encryption_data(loads(encryption_data))
    except Exception:
        # Message did not have properly formatted encryption metadata.
        if require_encryption:
            raise ValueError(_ERROR_ENTITY_NOT_ENCRYPTED)
        else:
            return None, None, None, None

    if not (encryption_data.encryption_agent.encryption_algorithm == _EncryptionAlgorithm.AES_CBC_256):
        raise ValueError(_ERROR_UNSUPPORTED_ENCRYPTION_ALGORITHM)

    content_encryption_key = _validate_and_unwrap_cek(encryption_data, key_encryption_key, key_resolver)

    # Special check for compatibility with Java V1 encryption protocol.
    isJavaV1 = (encryption_data.key_wrapping_metadata is None) or \
               ((encryption_data.encryption_agent.protocol == _ENCRYPTION_PROTOCOL_V1) and
                'EncryptionLibrary' in encryption_data.key_wrapping_metadata and
                'Java' in encryption_data.key_wrapping_metadata['EncryptionLibrary'])

    metadataIV = _generate_property_iv(encryption_data.content_encryption_IV,
                                       entity['PartitionKey'], entity['RowKey'],
                                       '_ClientEncryptionMetadata2', isJavaV1)

    cipher = _generate_AES_CBC_cipher(content_encryption_key, metadataIV)

    # Decrypt the data.
    decryptor = cipher.decryptor()
    encrypted_properties_list = decryptor.update(encrypted_properties_list) + decryptor.finalize()

    # Unpad the data.
    unpadder = PKCS7(128).unpadder()
    encrypted_properties_list = unpadder.update(encrypted_properties_list) + unpadder.finalize()

    encrypted_properties_list = encrypted_properties_list.decode('utf-8')

    if isJavaV1:
        # Strip the square braces from the ends and split string into list.
        encrypted_properties_list = encrypted_properties_list[1:-1]
        encrypted_properties_list = encrypted_properties_list.split(', ')
    else:
        encrypted_properties_list = loads(encrypted_properties_list)

    return encryption_data.content_encryption_IV, encrypted_properties_list, content_encryption_key, isJavaV1


def _generate_property_iv(entity_iv, pk, rk, property_name, isJavaV1):
    '''
    Uses the entity_iv, partition key, and row key to generate and return
    the iv for the specified property.
    '''
    digest = Hash(SHA256(), default_backend())
    if not isJavaV1:
        digest.update(entity_iv +
                      (rk + pk + property_name).encode('utf-8'))
    else:
        digest.update(entity_iv +
                      (pk + rk + property_name).encode('utf-8'))
    propertyIV = digest.finalize()
    return propertyIV[:16]
