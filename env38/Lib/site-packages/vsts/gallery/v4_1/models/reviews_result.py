# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReviewsResult(Model):
    """ReviewsResult.

    :param has_more_reviews: Flag indicating if there are more reviews to be shown (for paging)
    :type has_more_reviews: bool
    :param reviews: List of reviews
    :type reviews: list of :class:`Review <gallery.v4_1.models.Review>`
    :param total_review_count: Count of total review items
    :type total_review_count: long
    """

    _attribute_map = {
        'has_more_reviews': {'key': 'hasMoreReviews', 'type': 'bool'},
        'reviews': {'key': 'reviews', 'type': '[Review]'},
        'total_review_count': {'key': 'totalReviewCount', 'type': 'long'}
    }

    def __init__(self, has_more_reviews=None, reviews=None, total_review_count=None):
        super(ReviewsResult, self).__init__()
        self.has_more_reviews = has_more_reviews
        self.reviews = reviews
        self.total_review_count = total_review_count
