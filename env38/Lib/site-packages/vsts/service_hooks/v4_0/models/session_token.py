# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SessionToken(Model):
    """SessionToken.

    :param error: The error message in case of error
    :type error: str
    :param token: The access token
    :type token: str
    :param valid_to: The expiration date in UTC
    :type valid_to: datetime
    """

    _attribute_map = {
        'error': {'key': 'error', 'type': 'str'},
        'token': {'key': 'token', 'type': 'str'},
        'valid_to': {'key': 'validTo', 'type': 'iso-8601'}
    }

    def __init__(self, error=None, token=None, valid_to=None):
        super(SessionToken, self).__init__()
        self.error = error
        self.token = token
        self.valid_to = valid_to
