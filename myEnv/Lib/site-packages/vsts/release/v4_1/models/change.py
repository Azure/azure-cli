# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Change(Model):
    """Change.

    :param author: The author of the change.
    :type author: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param change_type: The type of change. "commit", "changeset", etc.
    :type change_type: str
    :param display_uri: The location of a user-friendly representation of the resource.
    :type display_uri: str
    :param id: Something that identifies the change. For a commit, this would be the SHA1. For a TFVC changeset, this would be the changeset id.
    :type id: str
    :param location: The location of the full representation of the resource.
    :type location: str
    :param message: A description of the change. This might be a commit message or changeset description.
    :type message: str
    :param pusher: The person or process that pushed the change.
    :type pusher: str
    :param timestamp: A timestamp for the change.
    :type timestamp: datetime
    """

    _attribute_map = {
        'author': {'key': 'author', 'type': 'IdentityRef'},
        'change_type': {'key': 'changeType', 'type': 'str'},
        'display_uri': {'key': 'displayUri', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'message': {'key': 'message', 'type': 'str'},
        'pusher': {'key': 'pusher', 'type': 'str'},
        'timestamp': {'key': 'timestamp', 'type': 'iso-8601'}
    }

    def __init__(self, author=None, change_type=None, display_uri=None, id=None, location=None, message=None, pusher=None, timestamp=None):
        super(Change, self).__init__()
        self.author = author
        self.change_type = change_type
        self.display_uri = display_uri
        self.id = id
        self.location = location
        self.message = message
        self.pusher = pusher
        self.timestamp = timestamp
