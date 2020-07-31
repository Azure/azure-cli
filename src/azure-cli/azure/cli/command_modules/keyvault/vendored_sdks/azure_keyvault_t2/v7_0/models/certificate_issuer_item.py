# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CertificateIssuerItem(Model):
    """The certificate issuer item containing certificate issuer metadata.

    :param id: Certificate Identifier.
    :type id: str
    :param provider: The issuer provider.
    :type provider: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'provider': {'key': 'provider', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(CertificateIssuerItem, self).__init__(**kwargs)
        self.id = kwargs.get('id', None)
        self.provider = kwargs.get('provider', None)
