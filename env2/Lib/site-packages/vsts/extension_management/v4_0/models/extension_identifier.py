# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionIdentifier(Model):
    """ExtensionIdentifier.

    :param extension_name: The ExtensionName component part of the fully qualified ExtensionIdentifier
    :type extension_name: str
    :param publisher_name: The PublisherName component part of the fully qualified ExtensionIdentifier
    :type publisher_name: str
    """

    _attribute_map = {
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'}
    }

    def __init__(self, extension_name=None, publisher_name=None):
        super(ExtensionIdentifier, self).__init__()
        self.extension_name = extension_name
        self.publisher_name = publisher_name
