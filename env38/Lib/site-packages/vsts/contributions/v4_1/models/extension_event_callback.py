# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionEventCallback(Model):
    """ExtensionEventCallback.

    :param uri: The uri of the endpoint that is hit when an event occurs
    :type uri: str
    """

    _attribute_map = {
        'uri': {'key': 'uri', 'type': 'str'}
    }

    def __init__(self, uri=None):
        super(ExtensionEventCallback, self).__init__()
        self.uri = uri
