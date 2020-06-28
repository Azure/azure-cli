# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ClientCertificate(Model):
    """ClientCertificate.

    :param value: Gets or sets the value of client certificate.
    :type value: str
    """

    _attribute_map = {
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, value=None):
        super(ClientCertificate, self).__init__()
        self.value = value
