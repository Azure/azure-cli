# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .publisher_base import PublisherBase


class Publisher(PublisherBase):
    """Publisher.

    :param display_name:
    :type display_name: str
    :param email_address:
    :type email_address: list of str
    :param extensions:
    :type extensions: list of :class:`PublishedExtension <gallery.v4_1.models.PublishedExtension>`
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
    :param _links:
    :type _links: :class:`ReferenceLinks <gallery.v4_1.models.ReferenceLinks>`
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
        'short_description': {'key': 'shortDescription', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'}
    }

    def __init__(self, display_name=None, email_address=None, extensions=None, flags=None, last_updated=None, long_description=None, publisher_id=None, publisher_name=None, short_description=None, _links=None):
        super(Publisher, self).__init__(display_name=display_name, email_address=email_address, extensions=extensions, flags=flags, last_updated=last_updated, long_description=long_description, publisher_id=publisher_id, publisher_name=publisher_name, short_description=short_description)
        self._links = _links
