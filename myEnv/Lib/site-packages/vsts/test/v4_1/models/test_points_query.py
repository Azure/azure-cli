# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestPointsQuery(Model):
    """TestPointsQuery.

    :param order_by:
    :type order_by: str
    :param points:
    :type points: list of :class:`TestPoint <test.v4_1.models.TestPoint>`
    :param points_filter:
    :type points_filter: :class:`PointsFilter <test.v4_1.models.PointsFilter>`
    :param wit_fields:
    :type wit_fields: list of str
    """

    _attribute_map = {
        'order_by': {'key': 'orderBy', 'type': 'str'},
        'points': {'key': 'points', 'type': '[TestPoint]'},
        'points_filter': {'key': 'pointsFilter', 'type': 'PointsFilter'},
        'wit_fields': {'key': 'witFields', 'type': '[str]'}
    }

    def __init__(self, order_by=None, points=None, points_filter=None, wit_fields=None):
        super(TestPointsQuery, self).__init__()
        self.order_by = order_by
        self.points = points
        self.points_filter = points_filter
        self.wit_fields = wit_fields
