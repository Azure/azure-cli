# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Attachment(Model):
    """Attachment.

    :param _links: Links to other related objects.
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param author: The person that uploaded this attachment.
    :type author: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param content_hash: Content hash of on-disk representation of file content. Its calculated by the server by using SHA1 hash function.
    :type content_hash: str
    :param created_date: The time the attachment was uploaded.
    :type created_date: datetime
    :param description: The description of the attachment.
    :type description: str
    :param display_name: The display name of the attachment. Can't be null or empty.
    :type display_name: str
    :param id: Id of the attachment.
    :type id: int
    :param properties: Extended properties.
    :type properties: :class:`object <git.v4_1.models.object>`
    :param url: The url to download the content of the attachment.
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'IdentityRef'},
        'content_hash': {'key': 'contentHash', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'properties': {'key': 'properties', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, author=None, content_hash=None, created_date=None, description=None, display_name=None, id=None, properties=None, url=None):
        super(Attachment, self).__init__()
        self._links = _links
        self.author = author
        self.content_hash = content_hash
        self.created_date = created_date
        self.description = description
        self.display_name = display_name
        self.id = id
        self.properties = properties
        self.url = url
