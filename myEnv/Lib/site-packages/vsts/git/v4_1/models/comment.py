# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Comment(Model):
    """Comment.

    :param _links: Links to other related objects.
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param author: The author of the comment.
    :type author: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param comment_type: The comment type at the time of creation.
    :type comment_type: object
    :param content: The comment content.
    :type content: str
    :param id: The comment ID. IDs start at 1 and are unique to a pull request.
    :type id: int
    :param is_deleted: Whether or not this comment was soft-deleted.
    :type is_deleted: bool
    :param last_content_updated_date: The date the comment's content was last updated.
    :type last_content_updated_date: datetime
    :param last_updated_date: The date the comment was last updated.
    :type last_updated_date: datetime
    :param parent_comment_id: The ID of the parent comment. This is used for replies.
    :type parent_comment_id: int
    :param published_date: The date the comment was first published.
    :type published_date: datetime
    :param users_liked: A list of the users who have liked this comment.
    :type users_liked: list of :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'IdentityRef'},
        'comment_type': {'key': 'commentType', 'type': 'object'},
        'content': {'key': 'content', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'last_content_updated_date': {'key': 'lastContentUpdatedDate', 'type': 'iso-8601'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'parent_comment_id': {'key': 'parentCommentId', 'type': 'int'},
        'published_date': {'key': 'publishedDate', 'type': 'iso-8601'},
        'users_liked': {'key': 'usersLiked', 'type': '[IdentityRef]'}
    }

    def __init__(self, _links=None, author=None, comment_type=None, content=None, id=None, is_deleted=None, last_content_updated_date=None, last_updated_date=None, parent_comment_id=None, published_date=None, users_liked=None):
        super(Comment, self).__init__()
        self._links = _links
        self.author = author
        self.comment_type = comment_type
        self.content = content
        self.id = id
        self.is_deleted = is_deleted
        self.last_content_updated_date = last_content_updated_date
        self.last_updated_date = last_updated_date
        self.parent_comment_id = parent_comment_id
        self.published_date = published_date
        self.users_liked = users_liked
