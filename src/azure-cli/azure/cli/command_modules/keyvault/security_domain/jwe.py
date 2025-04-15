# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import base64
import hashlib
import hmac
import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from knack.util import CLIError

from azure.cli.command_modules.keyvault.security_domain.sp800_108 import KDF
from azure.cli.command_modules.keyvault.security_domain.utils import Utils


class JWEHeader:  # pylint: disable=too-many-instance-attributes
    _fields = ['alg', 'enc', 'zip', 'jku', 'jwk', 'kid', 'x5u', 'x5c', 'x5t', 'x5t_S256', 'typ', 'cty', 'crit']

    def __init__(self, alg=None, enc=None, zip=None,  # pylint: disable=redefined-builtin
                 jku=None, jwk=None, kid=None, x5u=None, x5c=None, x5t=None,
                 x5t_S256=None, typ=None, cty=None, crit=None):
        """
            JWE header
        :param alg: algorithm
        :param enc: encryption algorithm
        :param zip: compression algorithm
        :param jku: JWK set URL
        :param jwk: JSON Web key
        :param kid: Key ID
        :param x5u: X.509 certificate URL
        :param x5c: X.509 certificate chain
        :param x5t: X.509 certificate SHA-1 Thumbprint
        :param x5t_S256: X.509 certificate SHA-256 Thumbprint
        :param typ: type
        :param cty: content type
        :param crit: critical
        """
        self.alg = alg
        self.enc = enc
        self.zip = zip
        self.jku = jku
        self.jwk = jwk
        self.kid = kid
        self.x5u = x5u
        self.x5c = x5c
        self.x5t = x5t
        self.x5t_S256 = x5t_S256
        self.typ = typ
        self.cty = cty
        self.crit = crit

    @staticmethod
    def from_json_str(json_str):
        json_dict = json.loads(json_str)
        jwe_header = JWEHeader()
        for k in jwe_header._fields:
            if k == 'x5t_S256':
                v = json_dict.get('x5t#S256', None)
            else:
                v = json_dict.get(k, None)
            if v is not None:
                setattr(jwe_header, k, v)
        return jwe_header

    def to_json_str(self):
        json_dict = {}
        for k in self._fields:
            v = getattr(self, k, None)
            if v is not None:
                if k == 'x5t_S256':
                    json_dict['x5t#S256'] = v
                else:
                    json_dict[k] = v
        return json.dumps(json_dict)


class JWEDecode:
    def __init__(self, compact_jwe=None):
        if compact_jwe is None:
            self.encoded_header = ''
            self.encrypted_key = None
            self.init_vector = None
            self.ciphertext = None
            self.auth_tag = None
            self.protected_header = JWEHeader()
        else:
            parts = compact_jwe.split('.')
            if len(parts) != 5:
                raise CLIError('Malformed input.')

            self.encoded_header = parts[0]
            header = base64.urlsafe_b64decode(self.encoded_header + '===').decode('ascii')  # Fix incorrect padding
            self.protected_header = JWEHeader.from_json_str(header)
            self.encrypted_key = base64.urlsafe_b64decode(parts[1] + '===')
            self.init_vector = base64.urlsafe_b64decode(parts[2] + '===')
            self.ciphertext = base64.urlsafe_b64decode(parts[3] + '===')
            self.auth_tag = base64.urlsafe_b64decode(parts[4] + '===')

    def encode_header(self):
        header_json = self.protected_header.to_json_str().replace('": ', '":').replace('", ', '",')
        self.encoded_header = Utils.security_domain_b64_url_encode(header_json.encode('ascii'))

    def encode_compact(self):
        ret = [self.encoded_header + '.']

        if self.encrypted_key is not None:
            ret.append(Utils.security_domain_b64_url_encode(self.encrypted_key))
        ret.append('.')

        if self.init_vector is not None:
            ret.append(Utils.security_domain_b64_url_encode(self.init_vector))
        ret.append('.')

        if self.ciphertext is not None:
            ret.append(Utils.security_domain_b64_url_encode(self.ciphertext))
        ret.append('.')

        if self.auth_tag is not None:
            ret.append(Utils.security_domain_b64_url_encode(self.auth_tag))

        return ''.join(ret)


class JWE:
    def __init__(self, compact_jwe=None):
        self.jwe_decode = JWEDecode(compact_jwe=compact_jwe)

    def encode_compact(self):
        return self.jwe_decode.encode_compact()

    def get_padding_mode(self):
        alg = self.jwe_decode.protected_header.alg

        if alg == 'RSA-OAEP-256':
            algorithm = hashes.SHA256()
            return asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=algorithm), algorithm=algorithm, label=None)

        if alg == 'RSA-OAEP':
            algorithm = hashes.SHA1()
            return asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=algorithm), algorithm=algorithm, label=None)

        if alg == 'RSA1_5':
            return asymmetric_padding.PKCS1v15()

        return None

    def get_cek(self, private_key):
        return private_key.decrypt(
            self.jwe_decode.encrypted_key,
            self.get_padding_mode()
        )

    def set_cek(self, cert, cek):
        public_key = cert.public_key()
        self.jwe_decode.encrypted_key = public_key.encrypt(bytes(cek), self.get_padding_mode())

    @staticmethod
    def dek_from_cek(cek):
        dek = bytearray()
        for i in range(32):
            dek.append(cek[i + 32])
        return dek

    @staticmethod
    def hmac_key_from_cek(cek):
        hk = bytearray()
        for i in range(32):
            hk.append(cek[i])
        return hk

    def get_mac(self, hk):
        header_bytes = bytearray()
        header_bytes.extend(self.jwe_decode.encoded_header.encode('ascii'))
        auth_bits = len(header_bytes) * 8

        hash_data = bytearray()
        hash_data.extend(header_bytes)
        hash_data.extend(self.jwe_decode.init_vector)
        hash_data.extend(self.jwe_decode.ciphertext)
        hash_data.extend(KDF.to_big_endian_64bits(auth_bits))

        hMAC = hmac.HMAC(hk, msg=hash_data, digestmod=hashlib.sha512)
        return hMAC.digest()

    def Aes256HmacSha512Encrypt(self, cek, plaintext):
        dek = JWE.dek_from_cek(cek)
        hk = JWE.hmac_key_from_cek(cek)

        padder = padding.PKCS7(128).padder()
        plaintext = padder.update(bytes(plaintext)) + padder.finalize()

        aes_key = dek
        aes_iv = Utils.get_random(16)
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv), backend=default_backend())
        encryptor = cipher.encryptor()
        self.jwe_decode.ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        self.jwe_decode.init_vector = aes_iv

        mac_value = self.get_mac(hk)
        self.jwe_decode.auth_tag = bytearray()
        for i in range(32):
            self.jwe_decode.auth_tag.append(mac_value[i])

    def Aes256HmacSha512Decrypt(self, cek):
        dek = JWE.dek_from_cek(cek)
        hk = JWE.hmac_key_from_cek(cek)
        mac_value = self.get_mac(hk)

        test = 0
        i = 0
        while i < len(self.jwe_decode.auth_tag) == 32:
            test |= (self.jwe_decode.auth_tag[i] ^ mac_value[i])
            i += 1

        if test != 0:
            return None

        aes_key = dek
        aes_iv = self.jwe_decode.init_vector
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(self.jwe_decode.ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(bytes(plaintext)) + unpadder.finalize()

        return plaintext

    def decrypt_using_bytes(self, cek):
        if self.jwe_decode.protected_header.enc == 'A256CBC-HS512':
            return self.Aes256HmacSha512Decrypt(cek)
        return None

    def get_cek_from_private_key(self, private_key):
        return private_key.decrypt(self.jwe_decode.encrypted_key, self.get_padding_mode())

    def decrypt_using_private_key(self, private_key):
        cek = self.get_cek_from_private_key(private_key)
        return self.decrypt_using_bytes(cek)

    def encrypt_using_bytes(self, cek, plaintext, alg_id, kid=None):
        if kid is not None:
            self.jwe_decode.protected_header.alg = 'dir'
            self.jwe_decode.protected_header.kid = kid

        if alg_id == 'A256CBC-HS512':
            self.jwe_decode.protected_header.enc = alg_id
            self.jwe_decode.encode_header()
            self.Aes256HmacSha512Encrypt(cek, plaintext)

    def encrypt_using_cert(self, cert, plaintext):
        self.jwe_decode.protected_header.alg = 'RSA-OAEP-256'
        self.jwe_decode.protected_header.kid = 'not used'
        cek = Utils.get_random(64)
        self.set_cek(cert, cek)
        self.encrypt_using_bytes(cek, plaintext, alg_id='A256CBC-HS512')
