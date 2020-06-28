# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiUpdate(Model):
    """WikiUpdate.

    :param associated_git_push: Git push object associated with this wiki update object. This is populated only in the response of the wiki updates POST API.
    :type associated_git_push: :class:`GitPush <wiki.v4_0.models.GitPush>`
    :param attachment_changes: List of attachment change objects that is to be associated with this update.
    :type attachment_changes: list of :class:`WikiAttachmentChange <wiki.v4_0.models.WikiAttachmentChange>`
    :param comment: Comment to be associated with this update.
    :type comment: str
    :param head_commit: Headcommit of the of the repository.
    :type head_commit: str
    :param page_change: Page change object associated with this update.
    :type page_change: :class:`WikiPageChange <wiki.v4_0.models.WikiPageChange>`
    """

    _attribute_map = {
        'associated_git_push': {'key': 'associatedGitPush', 'type': 'GitPush'},
        'attachment_changes': {'key': 'attachmentChanges', 'type': '[WikiAttachmentChange]'},
        'comment': {'key': 'comment', 'type': 'str'},
        'head_commit': {'key': 'headCommit', 'type': 'str'},
        'page_change': {'key': 'pageChange', 'type': 'WikiPageChange'}
    }

    def __init__(self, associated_git_push=None, attachment_changes=None, comment=None, head_commit=None, page_change=None):
        super(WikiUpdate, self).__init__()
        self.associated_git_push = associated_git_push
        self.attachment_changes = attachment_changes
        self.comment = comment
        self.head_commit = head_commit
        self.page_change = page_change
