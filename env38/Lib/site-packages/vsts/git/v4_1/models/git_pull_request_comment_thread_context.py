# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestCommentThreadContext(Model):
    """GitPullRequestCommentThreadContext.

    :param change_tracking_id: Used to track a comment across iterations. This value can be found by looking at the iteration's changes list. Must be set for pull requests with iteration support. Otherwise, it's not required for 'legacy' pull requests.
    :type change_tracking_id: int
    :param iteration_context: The iteration context being viewed when the thread was created.
    :type iteration_context: :class:`CommentIterationContext <git.v4_1.models.CommentIterationContext>`
    :param tracking_criteria: The criteria used to track this thread. If this property is filled out when the thread is returned, then the thread has been tracked from its original location using the given criteria.
    :type tracking_criteria: :class:`CommentTrackingCriteria <git.v4_1.models.CommentTrackingCriteria>`
    """

    _attribute_map = {
        'change_tracking_id': {'key': 'changeTrackingId', 'type': 'int'},
        'iteration_context': {'key': 'iterationContext', 'type': 'CommentIterationContext'},
        'tracking_criteria': {'key': 'trackingCriteria', 'type': 'CommentTrackingCriteria'}
    }

    def __init__(self, change_tracking_id=None, iteration_context=None, tracking_criteria=None):
        super(GitPullRequestCommentThreadContext, self).__init__()
        self.change_tracking_id = change_tracking_id
        self.iteration_context = iteration_context
        self.tracking_criteria = tracking_criteria
