# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def is_valid_ssh_rsa_public_key(openssh_pubkey):
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression # pylint: disable=line-too-long
    # A "good enough" check is to see if the key starts with the correct header.
    import struct
    import base64

    parts = openssh_pubkey.split()
    if len(parts) < 2:
        return False
    key_type = parts[0]
    key_string = parts[1]

    data = base64.b64decode(key_string)
    int_len = 4
    str_len = struct.unpack('>I', data[:int_len])[0]  # this should return 7
    return data[int_len:int_len + str_len] == key_type.encode()


def generate_ssh_keys(private_key_filepath, public_key_filepath):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    if os.path.isfile(public_key_filepath):
        try:
            with open(public_key_filepath, 'r') as public_key_file:
                public_key = public_key_file.read()
                pub_ssh_dir = os.path.dirname(public_key_filepath)
                logger.warning("Public SSH key file '%s' already exists in the directory: '%s'. "
                               "New SSH key files will not be generated.",
                               public_key_filepath, pub_ssh_dir)

                return public_key
        except OSError as e:
            raise CLIError(e)

    ssh_dir = os.path.dirname(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        os.chmod(ssh_dir, 0o700)

    if os.path.isfile(private_key_filepath):
        # Try to use existing private key if it exists.
        # https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#key-loading
        with open(private_key_filepath, "rb") as f:
            private_bytes = f.read()
        private_key = serialization.load_pem_private_key(private_bytes, password=None)
        logger.warning("Private SSH key file '%s' was found in the directory: '%s'. "
                       "A paired public key file '%s' will be generated.",
                       private_key_filepath, ssh_dir, public_key_filepath)
    else:
        # Otherwise generate new private key.
        # https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#generation
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#key-serialization
        # The private key will look like:
        # -----BEGIN RSA PRIVATE KEY-----
        # ...
        # -----END RSA PRIVATE KEY-----
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Creating the private key file with 600 permission makes sure only the current user can access it.
        # Reference: paramiko.pkey.PKey._write_private_key_file
        with os.fdopen(_open(private_key_filepath, 0o600), "wb") as f:
            f.write(private_bytes)

    # Write public key
    # The public key will look like:
    # ssh-rsa ...
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    with os.fdopen(_open(public_key_filepath, 0o644), 'wb') as f:
        f.write(public_bytes)

    return public_bytes.decode()


def _open(filename, mode):
    return os.open(filename, flags=os.O_WRONLY | os.O_TRUNC | os.O_CREAT, mode=mode)
