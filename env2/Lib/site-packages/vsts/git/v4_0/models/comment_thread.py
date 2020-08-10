# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CommentThread(Model):
    """CommentThread.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param comments: A list of the comments.
    :type comments: list of :class:`Comment <git.v4_0.models.Comment>`
    :param id: The comment thread id.
    :type id: int
    :param is_deleted: Specify if the thread is deleted which happens when all comments are deleted
    :type is_deleted: bool
    :param last_updated_date: The time this thread was last updated.
    :type last_updated_date: datetime
    :param properties: A list of (optional) thread properties.
    :type properties: :class:`object <git.v4_0.models.object>`
    :param published_date: The time this thread was published.
    :type published_date: datetime
    :param status: The status of the comment thread.
    :type status: object
    :param thread_context: Specify thread context such as position in left/right file.
    :type thread_context: :class:`CommentThreadContext <git.v4_0.models.CommentThreadContext>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'comments': {'key': 'comments', 'type': '[Comment]'},
        'id': {'key': 'id', 'type': 'int'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'properties': {'key': 'properties', 'type': 'object'},
        'published_date': {'key': 'publishedDate', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'object'},
        'thread_context': {'key': 'threadContext', 'type': 'CommentThreadContext'}
    }

    def __init__(self, _links=None, comments=None, id=None, is_deleted=None, last_updated_date=None, properties=None, published_date=None, status=None, thread_context=None):
        super(CommentThread, self).__init__()
        self._links = _links
        self.comments = comments
        self.id = id
        self.is_deleted = is_deleted
        self.last_updated_date = last_updated_date
        self.properties = properties
        self.published_date = published_date
        self.status = status
        self.thread_context = thread_context
