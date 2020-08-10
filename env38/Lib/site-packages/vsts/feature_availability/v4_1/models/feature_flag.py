# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeatureFlag(Model):
    """FeatureFlag.

    :param description:
    :type description: str
    :param effective_state:
    :type effective_state: str
    :param explicit_state:
    :type explicit_state: str
    :param name:
    :type name: str
    :param uri:
    :type uri: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'effective_state': {'key': 'effectiveState', 'type': 'str'},
        'explicit_state': {'key': 'explicitState', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'uri': {'key': 'uri', 'type': 'str'}
    }

    def __init__(self, description=None, effective_state=None, explicit_state=None, name=None, uri=None):
        super(FeatureFlag, self).__init__()
        self.description = description
        self.effective_state = effective_state
        self.explicit_state = explicit_state
        self.name = name
        self.uri = uri
