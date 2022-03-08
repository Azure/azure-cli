# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from os.path import exists
import os
from OpenSSL import crypto


def _create_test_cert(cert_file, key_file, subject, valid_days, serial_number):
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2046)

    # create a self-signed cert with some basic constraints
    cert = crypto.X509()
    cert.get_subject().CN = subject
    cert.gmtime_adj_notBefore(-1 * 24 * 60 * 60)
    cert.gmtime_adj_notAfter(valid_days * 24 * 60 * 60)
    cert.set_version(2)
    cert.set_serial_number(serial_number)
    cert.add_extensions([
        crypto.X509Extension(b"basicConstraints", True, b"CA:TRUE, pathlen:1"),
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash",
                             subject=cert),
    ])
    cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always",
                             issuer=cert)
    ])
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    cert_str = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')
    key_str = crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode('utf-8')

    open(cert_file, 'w').write(cert_str)
    open(key_file, 'w').write(key_str)


def _delete_test_cert(cert_file, key_file, verification_file):
    if exists(cert_file) and exists(key_file):
        os.remove(cert_file)
        os.remove(key_file)

    if exists(verification_file):
        os.remove(verification_file)


def _create_verification_cert(cert_file, key_file, verification_file, nonce, valid_days, serial_number):
    if exists(cert_file) and exists(key_file):
        # create a key pair
        public_key = crypto.PKey()
        public_key.generate_key(crypto.TYPE_RSA, 2046)

        # open the root cert and key
        signing_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cert_file).read())
        k = crypto.load_privatekey(crypto.FILETYPE_PEM, open(key_file).read())

        # create a cert signed by the root
        verification_cert = crypto.X509()
        verification_cert.get_subject().CN = nonce
        verification_cert.gmtime_adj_notBefore(-1 * 24 * 60 * 60)
        verification_cert.gmtime_adj_notAfter(valid_days * 24 * 60 * 60)
        verification_cert.set_version(2)
        verification_cert.set_serial_number(serial_number)

        verification_cert.set_pubkey(public_key)
        verification_cert.set_issuer(signing_cert.get_subject())
        verification_cert.add_extensions([
            crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always",
                                 issuer=signing_cert)
        ])
        verification_cert.sign(k, 'sha256')

        verification_cert_str = crypto.dump_certificate(crypto.FILETYPE_PEM, verification_cert).decode('ascii')

        open(verification_file, 'w').write(verification_cert_str)
