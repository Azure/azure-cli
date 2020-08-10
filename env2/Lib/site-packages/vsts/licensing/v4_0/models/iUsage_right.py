# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IUsageRight(Model):
    """IUsageRight.

    :param attributes: Rights data
    :type attributes: dict
    :param expiration_date: Rights expiration
    :type expiration_date: datetime
    :param name: Name, uniquely identifying a usage right
    :type name: str
    :param version: Version
    :type version: str
    """

    _attribute_map = {
        'attributes': {'key': 'attributes', 'type': '{object}'},
        'expiration_date': {'key': 'expirationDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, attributes=None, expiration_date=None, name=None, version=None):
        super(IUsageRight, self).__init__()
        self.attributes = attributes
        self.expiration_date = expiration_date
        self.name = name
        self.version = version
