# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Publisher(Model):
    """Publisher.

    :param display_name:
    :type display_name: str
    :param email_address:
    :type email_address: list of str
    :param extensions:
    :type extensions: list of :class:`PublishedExtension <gallery.v4_0.models.PublishedExtension>`
    :param flags:
    :type flags: object
    :param last_updated:
    :type last_updated: datetime
    :param long_description:
    :type long_description: str
    :param publisher_id:
    :type publisher_id: str
    :param publisher_name:
    :type publisher_name: str
    :param short_description:
    :type short_description: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'email_address': {'key': 'emailAddress', 'type': '[str]'},
        'extensions': {'key': 'extensions', 'type': '[PublishedExtension]'},
        'flags': {'key': 'flags', 'type': 'object'},
        'last_updated': {'key': 'lastUpdated', 'type': 'iso-8601'},
        'long_description': {'key': 'longDescription', 'type': 'str'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'short_description': {'key': 'shortDescription', 'type': 'str'}
    }

    def __init__(self, display_name=None, email_address=None, extensions=None, flags=None, last_updated=None, long_description=None, publisher_id=None, publisher_name=None, short_description=None):
        super(Publisher, self).__init__()
        self.display_name = display_name
        self.email_address = email_address
        self.extensions = extensions
        self.flags = flags
        self.last_updated = last_updated
        self.long_description = long_description
        self.publisher_id = publisher_id
        self.publisher_name = publisher_name
        self.short_description = short_description
