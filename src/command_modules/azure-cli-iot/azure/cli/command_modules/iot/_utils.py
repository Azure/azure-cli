# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from os.path import exists, join
import base64
from OpenSSL import crypto


def create_self_signed_certificate(device_id, valid_days, cert_output_dir):
    cert_file = device_id + '-cert.pem'
    key_file = device_id + '-key.pem'

    # create a key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().CN = device_id
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(valid_days * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    cert_dump = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')
    key_dump = crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode('utf-8')
    thumbprint = cert.digest('sha1').replace(b':', b'').decode('utf-8')

    if cert_output_dir is not None and exists(cert_output_dir):
        open(join(cert_output_dir, cert_file), "wt").write(cert_dump)
        open(join(cert_output_dir, key_file), "wt").write(key_dump)

    return {
        'certificate': cert_dump,
        'privateKey': key_dump,
        'thumbprint': thumbprint
    }


def open_certificate(certificate_path):
    certificate = ""
    if certificate_path.endswith('.pem') or certificate_path.endswith('.cer'):
        with open(certificate_path, "rb") as cert_file:
            certificate = cert_file.read()
            try:
                certificate = certificate.decode("utf-8")
            except UnicodeError:
                certificate = base64.b64encode(certificate).decode("utf-8")
    return certificate
