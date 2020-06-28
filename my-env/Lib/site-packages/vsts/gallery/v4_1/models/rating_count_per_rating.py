# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RatingCountPerRating(Model):
    """RatingCountPerRating.

    :param rating: Rating value
    :type rating: str
    :param rating_count: Count of total ratings
    :type rating_count: long
    """

    _attribute_map = {
        'rating': {'key': 'rating', 'type': 'str'},
        'rating_count': {'key': 'ratingCount', 'type': 'long'}
    }

    def __init__(self, rating=None, rating_count=None):
        super(RatingCountPerRating, self).__init__()
        self.rating = rating
        self.rating_count = rating_count
