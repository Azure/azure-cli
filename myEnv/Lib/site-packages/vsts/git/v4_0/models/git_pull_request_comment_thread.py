# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .comment_thread import CommentThread


class GitPullRequestCommentThread(CommentThread):
    """GitPullRequestCommentThread.

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
    :param pull_request_thread_context: Extended context information unique to pull requests
    :type pull_request_thread_context: :class:`GitPullRequestCommentThreadContext <git.v4_0.models.GitPullRequestCommentThreadContext>`
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
        'thread_context': {'key': 'threadContext', 'type': 'CommentThreadContext'},
        'pull_request_thread_context': {'key': 'pullRequestThreadContext', 'type': 'GitPullRequestCommentThreadContext'}
    }

    def __init__(self, _links=None, comments=None, id=None, is_deleted=None, last_updated_date=None, properties=None, published_date=None, status=None, thread_context=None, pull_request_thread_context=None):
        super(GitPullRequestCommentThread, self).__init__(_links=_links, comments=comments, id=id, is_deleted=is_deleted, last_updated_date=last_updated_date, properties=properties, published_date=published_date, status=status, thread_context=thread_context)
        self.pull_request_thread_context = pull_request_thread_context
