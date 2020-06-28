# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ClientRightsContainer(Model):
    """ClientRightsContainer.

    :param certificate_bytes:
    :type certificate_bytes: str
    :param token:
    :type token: str
    """

    _attribute_map = {
        'certificate_bytes': {'key': 'certificateBytes', 'type': 'str'},
        'token': {'key': 'token', 'type': 'str'}
    }

    def __init__(self, certificate_bytes=None, token=None):
        super(ClientRightsContainer, self).__init__()
        self.certificate_bytes = certificate_bytes
        self.token = token
