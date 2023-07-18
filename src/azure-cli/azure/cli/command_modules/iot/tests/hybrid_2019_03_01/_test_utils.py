# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
from os.path import exists
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def _create_test_cert(cert_file, key_file, subject, valid_days, serial_number):
    # create a key pair
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # create a self-signed cert
    subject_name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, subject),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject_name)
        .issuer_name(subject_name)
        .public_key(key.public_key())
        .serial_number(serial_number)
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=valid_days)
        )
        .sign(key, hashes.SHA256())
    )

    key_dump = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    cert_dump = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    with open(cert_file, "wt", encoding="utf-8") as f:
        f.write(cert_dump)

    with open(key_file, "wt", encoding="utf-8") as f:
        f.write(key_dump)


def _delete_test_cert(cert_file, key_file, verification_file):
    if exists(cert_file) and exists(key_file):
        os.remove(cert_file)
        os.remove(key_file)
    if exists(verification_file):
        os.remove(verification_file)


def _create_verification_cert(cert_file, key_file, verification_file, nonce, valid_days, serial_number):
    if exists(cert_file) and exists(key_file):
        # create a key pair
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        # open the root cert and key
        signing_cert = x509.load_pem_x509_certificate(open(cert_file, "rb").read())
        k = load_pem_private_key(open(key_file, "rb").read(), None)


        subject_name = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, nonce),
            ]
        )

        # create a cert signed by the root
        verification_cert = (
            x509.CertificateBuilder()
            .subject_name(subject_name)
            .issuer_name(signing_cert.subject)
            .public_key(key.public_key())
            .serial_number(serial_number)
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=valid_days)
            )
            .sign(k, hashes.SHA256())
        )

        verification_cert_str = verification_cert.public_bytes(serialization.Encoding.PEM).decode('ascii')

        open(verification_file, 'w').write(verification_cert_str)
