# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublisherFacts(Model):
    """PublisherFacts.

    :param display_name:
    :type display_name: str
    :param flags:
    :type flags: object
    :param publisher_id:
    :type publisher_id: str
    :param publisher_name:
    :type publisher_name: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'flags': {'key': 'flags', 'type': 'object'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'}
    }

    def __init__(self, display_name=None, flags=None, publisher_id=None, publisher_name=None):
        super(PublisherFacts, self).__init__()
        self.display_name = display_name
        self.flags = flags
        self.publisher_id = publisher_id
        self.publisher_name = publisher_name
