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
        certificate = base64.b64encode(certificate).decode("utf-8")
    return certificate


def generate_key(byte_length=32):
    """
    Generate cryptographically secure device key.
    """
    import secrets

    token_bytes = secrets.token_bytes(byte_length)
    return base64.b64encode(token_bytes).decode("utf8")


def _dps_certificate_response_transform(certificate_response):
    from azure.mgmt.iothubprovisioningservices.models import (CertificateListDescription,
                                                              CertificateResponse,
                                                              VerificationCodeResponse)
    if isinstance(certificate_response, CertificateListDescription) and certificate_response.value:
        for cert in certificate_response.value:
            cert = _replace_certificate_bytes(cert)
    if isinstance(certificate_response, (CertificateResponse, VerificationCodeResponse)):
        certificate_response = _replace_certificate_bytes(certificate_response)
    return certificate_response


def _replace_certificate_bytes(cert_object):
    properties = getattr(cert_object, 'properties', {})
    body = getattr(properties, 'certificate', None)
    if body:
        cert_bytes = _safe_decode(body)
        if not cert_bytes:
            from knack.log import get_logger
            logger = get_logger(__name__)
            logger.warning('Certificate `%s` contains invalid unicode characters; its body was omitted from output.',
                           cert_object.name)
        cert_object.properties.certificate = cert_bytes
    return cert_object


def _safe_decode(cert_bytes):
    if isinstance(cert_bytes, str):
        return cert_bytes
    if isinstance(cert_bytes, (bytearray, bytes)):
        try:
            return cert_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return None
    return None
