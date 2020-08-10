# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReviewSummary(Model):
    """ReviewSummary.

    :param average_rating: Average Rating
    :type average_rating: int
    :param rating_count: Count of total ratings
    :type rating_count: long
    :param rating_split: Split of count accross rating
    :type rating_split: list of :class:`RatingCountPerRating <gallery.v4_1.models.RatingCountPerRating>`
    """

    _attribute_map = {
        'average_rating': {'key': 'averageRating', 'type': 'int'},
        'rating_count': {'key': 'ratingCount', 'type': 'long'},
        'rating_split': {'key': 'ratingSplit', 'type': '[RatingCountPerRating]'}
    }

    def __init__(self, average_rating=None, rating_count=None, rating_split=None):
        super(ReviewSummary, self).__init__()
        self.average_rating = average_rating
        self.rating_count = rating_count
        self.rating_split = rating_split
