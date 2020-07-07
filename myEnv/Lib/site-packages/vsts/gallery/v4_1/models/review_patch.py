# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReviewPatch(Model):
    """ReviewPatch.

    :param operation: Denotes the patch operation type
    :type operation: object
    :param reported_concern: Use when patch operation is FlagReview
    :type reported_concern: :class:`UserReportedConcern <gallery.v4_1.models.UserReportedConcern>`
    :param review_item: Use when patch operation is EditReview
    :type review_item: :class:`Review <gallery.v4_1.models.Review>`
    """

    _attribute_map = {
        'operation': {'key': 'operation', 'type': 'object'},
        'reported_concern': {'key': 'reportedConcern', 'type': 'UserReportedConcern'},
        'review_item': {'key': 'reviewItem', 'type': 'Review'}
    }

    def __init__(self, operation=None, reported_concern=None, review_item=None):
        super(ReviewPatch, self).__init__()
        self.operation = operation
        self.reported_concern = reported_concern
        self.review_item = review_item
