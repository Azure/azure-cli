# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitAnnotatedTag(Model):
    """GitAnnotatedTag.

    :param message: The tagging Message
    :type message: str
    :param name: The name of the annotated tag.
    :type name: str
    :param object_id: The objectId (Sha1Id) of the tag.
    :type object_id: str
    :param tagged_by: User info and date of tagging.
    :type tagged_by: :class:`GitUserDate <git.v4_1.models.GitUserDate>`
    :param tagged_object: Tagged git object.
    :type tagged_object: :class:`GitObject <git.v4_1.models.GitObject>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'object_id': {'key': 'objectId', 'type': 'str'},
        'tagged_by': {'key': 'taggedBy', 'type': 'GitUserDate'},
        'tagged_object': {'key': 'taggedObject', 'type': 'GitObject'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, message=None, name=None, object_id=None, tagged_by=None, tagged_object=None, url=None):
        super(GitAnnotatedTag, self).__init__()
        self.message = message
        self.name = name
        self.object_id = object_id
        self.tagged_by = tagged_by
        self.tagged_object = tagged_object
        self.url = url
