# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class Key:  # pylint: disable=too-few-public-methods
    def __init__(self, enc_key=None, x5t_256=None):
        self.enc_key = enc_key
        self.x5t_256 = x5t_256

    def to_json(self):
        return {
            'enc_key': self.enc_key if self.enc_key else '',
            'x5t_256': self.x5t_256 if self.x5t_256 else ''
        }


class EncData:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.data = []
        self.kdf = None

    def to_json(self):
        return {
            'data': [x.to_json() for x in self.data],
            'kdf': self.kdf if self.kdf else ''
        }


class Datum:  # pylint: disable=too-few-public-methods
    def __init__(self, compact_jwe=None, tag=None):
        self.compact_jwe = compact_jwe
        self.tag = tag

    def to_json(self):
        return {
            'compact_jwe': self.compact_jwe if self.compact_jwe else '',
            'tag': self.tag if self.tag else ''
        }


class SecurityDomainRestoreData:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.enc_data = EncData()
        self.wrapped_key = Key()

    def to_json(self):
        return {
            'EncData': self.enc_data.to_json(),
            'WrappedKey': self.wrapped_key.to_json()
        }
