# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .board_chart_reference import BoardChartReference


class BoardChart(BoardChartReference):
    """BoardChart.

    :param name: Name of the resource
    :type name: str
    :param url: Full http link to the resource
    :type url: str
    :param _links: The links for the resource
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param settings: The settings for the resource
    :type settings: dict
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'settings': {'key': 'settings', 'type': '{object}'}
    }

    def __init__(self, name=None, url=None, _links=None, settings=None):
        super(BoardChart, self).__init__(name=name, url=url)
        self._links = _links
        self.settings = settings
