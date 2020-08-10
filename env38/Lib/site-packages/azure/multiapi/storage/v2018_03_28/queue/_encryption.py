# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
from json import (
    dumps,
    loads,
)

from azure.common import (
    AzureException,
)
from cryptography.hazmat.primitives.padding import PKCS7

from ..common._common_conversion import (
    _encode_base64,
    _decode_base64_to_bytes
)
from ..common._encryption import (
    _generate_encryption_data_dict,
    _dict_to_encryption_data,
    _generate_AES_CBC_cipher,
    _validate_and_unwrap_cek,
    _EncryptionAlgorithm,
)
from ..common._error import (
    _ERROR_DECRYPTION_FAILURE,
    _ERROR_UNSUPPORTED_ENCRYPTION_ALGORITHM,
    _validate_not_none,
    _validate_key_encryption_key_wrap,
)
from ._error import (
    _ERROR_MESSAGE_NOT_ENCRYPTED
)


def _encrypt_queue_message(message, key_encryption_key):
    '''
    Encrypts the given plain text message using AES256 in CBC mode with 128 bit padding.
    Wraps the generated content-encryption-key using the user-provided key-encryption-key (kek). 
    Returns a json-formatted string containing the encrypted message and the encryption metadata.

    :param object message:
        The plain text messge to be encrypted.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        wrap_key(key)--wraps the specified key using an algorithm of the user's choice.
        get_key_wrap_algorithm()--returns the algorithm used to wrap the specified symmetric key.
        get_kid()--returns a string key id for this key-encryption-key.
    :return: A json-formatted string containing the encrypted message and the encryption metadata.
    :rtype: str
    '''

    _validate_not_none('message', message)
    _validate_not_none('key_encryption_key', key_encryption_key)
    _validate_key_encryption_key_wrap(key_encryption_key)

    # AES256 uses 256 bit (32 byte) keys and always with 16 byte blocks
    content_encryption_key = os.urandom(32)
    initialization_vector = os.urandom(16)

    # Queue encoding functions all return unicode strings, and encryption should 
    # operate on binary strings.
    message = message.encode('utf-8')

    cipher = _generate_AES_CBC_cipher(content_encryption_key, initialization_vector)

    # PKCS7 with 16 byte blocks ensures compatibility with AES.
    padder = PKCS7(128).padder()
    padded_data = padder.update(message) + padder.finalize()

    # Encrypt the data.
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Build the dictionary structure.
    queue_message = {'EncryptedMessageContents': _encode_base64(encrypted_data),
                     'EncryptionData': _generate_encryption_data_dict(key_encryption_key,
                                                                      content_encryption_key,
                                                                      initialization_vector)}

    return dumps(queue_message)


def _decrypt_queue_message(message, require_encryption, key_encryption_key, resolver):
    '''
    Returns the decrypted message contents from an EncryptedQueueMessage.
    If no encryption metadata is present, will return the unaltered message.
    :param str message:
        The JSON formatted QueueEncryptedMessage contents with all associated metadata.
    :param bool require_encryption:
        If set, will enforce that the retrieved messages are encrypted and decrypt them.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        unwrap_key(key, algorithm)--returns the unwrapped form of the specified symmetric key using the string-specified algorithm.
        get_kid()--returns a string key id for this key-encryption-key.
    :param function resolver(kid):
        The user-provided key resolver. Uses the kid string to return a key-encryption-key implementing the interface defined above.
    :return: The plain text message from the queue message.
    :rtype: str
    '''

    try:
        message = loads(message)

        encryption_data = _dict_to_encryption_data(message['EncryptionData'])
        decoded_data = _decode_base64_to_bytes(message['EncryptedMessageContents'])
    except (KeyError, ValueError):
        # Message was not json formatted and so was not encrypted
        # or the user provided a json formatted message.
        if require_encryption:
            raise ValueError(_ERROR_MESSAGE_NOT_ENCRYPTED)
        else:
            return message
    try:
        return _decrypt(decoded_data, encryption_data, key_encryption_key, resolver).decode('utf-8')
    except Exception:
        raise AzureException(_ERROR_DECRYPTION_FAILURE)


def _decrypt(message, encryption_data, key_encryption_key=None, resolver=None):
    '''
    Decrypts the given ciphertext using AES256 in CBC mode with 128 bit padding.
    Unwraps the content-encryption-key using the user-provided or resolved key-encryption-key (kek). Returns the original plaintex.

    :param str message:
        The ciphertext to be decrypted.
    :param _EncryptionData encryption_data:
        The metadata associated with this ciphertext.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        unwrap_key(key, algorithm)--returns the unwrapped form of the specified symmetric key using the string-specified algorithm.
        get_kid()--returns a string key id for this key-encryption-key.
    :param function resolver(kid):
        The user-provided key resolver. Uses the kid string to return a key-encryption-key implementing the interface defined above.
    :return: The decrypted plaintext.
    :rtype: str
    '''
    _validate_not_none('message', message)
    content_encryption_key = _validate_and_unwrap_cek(encryption_data, key_encryption_key, resolver)

    if not (_EncryptionAlgorithm.AES_CBC_256 == encryption_data.encryption_agent.encryption_algorithm):
        raise ValueError(_ERROR_UNSUPPORTED_ENCRYPTION_ALGORITHM)

    cipher = _generate_AES_CBC_cipher(content_encryption_key, encryption_data.content_encryption_IV)

    # decrypt data
    decrypted_data = message
    decryptor = cipher.decryptor()
    decrypted_data = (decryptor.update(decrypted_data) + decryptor.finalize())

    # unpad data
    unpadder = PKCS7(128).unpadder()
    decrypted_data = (unpadder.update(decrypted_data) + unpadder.finalize())

    return decrypted_data
