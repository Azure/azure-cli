# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UserReportedConcern(Model):
    """UserReportedConcern.

    :param category: Category of the concern
    :type category: object
    :param concern_text: User comment associated with the report
    :type concern_text: str
    :param review_id: Id of the review which was reported
    :type review_id: long
    :param submitted_date: Date the report was submitted
    :type submitted_date: datetime
    :param user_id: Id of the user who reported a review
    :type user_id: str
    """

    _attribute_map = {
        'category': {'key': 'category', 'type': 'object'},
        'concern_text': {'key': 'concernText', 'type': 'str'},
        'review_id': {'key': 'reviewId', 'type': 'long'},
        'submitted_date': {'key': 'submittedDate', 'type': 'iso-8601'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, category=None, concern_text=None, review_id=None, submitted_date=None, user_id=None):
        super(UserReportedConcern, self).__init__()
        self.category = category
        self.concern_text = concern_text
        self.review_id = review_id
        self.submitted_date = submitted_date
        self.user_id = user_id
